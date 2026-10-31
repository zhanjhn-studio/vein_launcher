"""版本继承链解析器 - 递归合并父版本的 assets/libraries

工作流程：
User Version JSON → inherits_from="1.20"  
   ↓
fetch(Version "1.20") → inherits_from="1.19"
   ↓
...直到遇到根节点（无 inheritsFrom）
   ↓   
自底向上合并 libraries/assets/main_class
   ↓
返回完整的 ParsedVersion 对象

基于 vision-audit 提供的 Mojang Version Schema 文档优化实现
"""

from typing import Dict, List, Optional
from vein_launcher.domain.models.version import VersionJSON, ParsedVersion, Library
from vein_launcher.common.exceptions import VersionNotFoundError


class VersionResolutionError(Exception):
    """版本解析错误（循环继承、父版本不存在）"""
    pass


class VersionResolver:
    """版本解析器 - 领域服务核心
    
    使用场景：Application Layer 收到下载请求时，必须先通过本类解析完整依赖链。
    
    算法复杂度：O(N)，N=继承链长度（一般不超过 3-5 层）
    """
    
    def __init__(self):
        self._cache: Dict[str, ParsedVersion] = {}
    
    async def resolve(self, version_id: str, fetch_api_client) -> ParsedVersion:
        """
        递归解析版本至完整版
        
        Args:
            version_id: 目标版本 ID，如 "fabric-1.20.4"
            fetch_api_client: Infrastructure NetworkRepo（未实现占位）
            
        Returns:
            ParsedVersion 完整对象
            
        Raises:
            - VersionNotFoundError: 父版本不存在
            - VersionResolutionError: 循环继承检测失败
        """
        
        # 1. 检查本地缓存
        if version_id in self._cache:
            return self._cache[version_id]
        
        # 2. 获取 JSON（调用 Infrastructure Network API）
        raw_json = await fetch_api_client.fetch_version(version_id)  
        
        try:
            version_obj = VersionJSON.model_validate(raw_json)
        except Exception as e:
            raise ValueError(f"版本 JSON 格式校验失败：{e}")
        
        # 3. 开始递归解析继承链
        inheritance_chain = []  # type: List[str]
        all_libraries = []      # type: List[Library]
        final_assets_index_name = None
        
        current_obj = version_obj
        
        while current_obj:
            # 循环检测
            if current_obj.version_id in inheritance_chain:
                raise VersionResolutionError(
                    f"循环继承检测：{' → '.join(inheritance_chain) + ' → ' + current_obj.version_id}"
                )
            
            inheritance_chain.insert(0, current_obj.version_id)  # 头插法，子→父
            
            # Assets Index 处理（以最后遇到的为准）
            if version_obj.assets != "legacy":
                final_assets_index_name = version_obj.assets
            
            # Libraries 合并（父在前，子覆盖 - Mojang 标准）
            for lib in reversed(current_obj.libraries):
                if lib not in all_libraries:  
                    all_libraries.insert(0, lib)   # 头部追加，子在前
                        
            # 如果还有父版本，继续递归
            if current_obj.inherits_from:
                current_obj = await self._fetch_parent_version(
                    current_obj.inherits_from, fetch_api_client
                )
            else:
                break  # 到达根节点
        
        # 4. 构造 ParsedVersion
        parsed_version = ParsedVersion(
            version_id=version_obj.version_id,
            type_=version_obj.type_,
            assets_index=final_assets_index_name or "legacy",
            libraries=all_libraries,
            main_class=current_obj.main_class or "net.minecraft.client.main.Main",
            java_version_requirement=self._extract_java_req(current_obj),
            inheritance_chain=inheritance_chain
        )
        
        # 5. 存入缓存（加速后续访问）
        self._cache[version_id] = parsed_version
        
        return parsed_version
    
    async def _fetch_parent_version(self, parent_id: str, fetch_api_client) -> Optional[VersionJSON]:
        """获取父版本对象"""
        try:
            raw_json = await fetch_api_client.fetch_version(parent_id)
            return VersionJSON.model_validate(raw_json)
        except Exception as e:
            raise VersionNotFoundError(f"父版本不存在：{parent_id}")
    
    def _extract_java_req(self, version_obj: VersionJSON) -> int:
        """提取 Java 版本要求（兼容旧版）"""
        if version_obj.minimum_java_version:
            return version_obj.minimum_java_version.get("major", 17)
        
        # Heuristic: 基于版本的简单判断
        from vein_launcher.common.utils import compare_versions
        
        if compare_versions(version_obj.version_id, "1.17") >= 0:
            return 17
        elif compare_versions(version_obj.version_id, "1.12") >= 0:
            return 8
        
        return 8
    
    async def resolve_with_deps(
        self,
        version_id: str,
        fetch_api_client,
        include_loader_libs: bool = False
    ) -> List[Library]:
        """
        返回完整依赖库列表（过滤当前 OS）
        
        Args:
            version_id: 目标版本
            fetch_api_client: Network API client
            include_loader_libs: 是否包含 Fabric/Forge loaders
            
        Returns:
            过滤后且按顺序排列的 Library 对象列表
        """
        parsed = await self.resolve(version_id, fetch_api_client)
        
        # 过滤当前平台（Windows x64）
        from vein_launcher.common.utils import ensure_dir
        
        filtered_libs = []
        for lib in parsed.libraries:
            if self._should_include_for_platform(lib):
                filtered_libs.append(lib)
                
        return filtered_libs
    
    def _should_include_for_platform(self, library: Library) -> bool:
        """基于 rules/os 字段判断是否包含当前平台的库"""
        
        if not library.rules:
            return True
        
        current_os = "windows_x64"   # 简单处理，后续可扩展为动态获取
        
        allow_list = False
        disallow_found = False
        
        for rule in library.rules:
            action = rule.get("action", "allow")  # allow/disallow
            
            if "os" in rule:
                os_match = self._match_os(rule["os"], current_os)
                
                if os_match and action == "disallow":
                    disallow_found = True
                    break
                
                if os_match and action == "allow":
                    allow_list = True
            
            elif action == "allow":  # 无条件 allow（默认规则）
                allow_list = True
        
        # disallow 优先级高于 allow
        if disallow_found:
            return False
        
        return allow_list
    
    def _match_os(self, os_req: Dict[str, str], current_os: str) -> bool:
        """操作系统匹配逻辑"""
        required_name = os_req.get("name", "")
        
        if not required_name:
            return True
        
        # 简单字符串包含判断
        # 可扩展：版本比较、架构精确匹配（x64 vs arm64）
        return required_name in current_os
