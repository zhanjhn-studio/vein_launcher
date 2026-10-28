"""模组模型 - Modrinth / CurseForge / Plugin 适配基类

设计原则：
1. 抽象统一的 ModInfo 接口，不同源站实现具体适配器
2. 插件化设计，基座不写死特定资源站逻辑
3. 依赖解析由 Infrastructure 层下载后在 Application 层处理
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class ModFile:
    """模组文件定义（特定版本）"""
    
    file_id: str                 # 文件唯一 ID（源站返回）
    display_name: str            # 显示名称，如 "Fabric API 0.91.0"
    version: str                 # 模组版本号
    description: Optional[str]   # 简短描述
    
    # 版本元数据
    mc_versions: List[str]       # 支持的 MC 版本列表 ["1.20.4", "1.20.5"]
    release_type: str            # [release/beta/alpha]
    publish_time: datetime       # 发布时间
    
    # 下载信息
    download_url: str            # 直接下载地址
    file_size: int               # 文件大小 (字节)
    sha1_hash: str               # SHA-1 校验和（40 字符）
    
    # 前置依赖解析（关键！用于自动补全前置模组）
    depends_on: List[str] = None  # 依赖的模组 slug，如 ["fabric-api", "cloth-config"]
    conflicts_with: List[str] = None
    
    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []
        if self.conflicts_with is None:
            self.conflicts_with = []


class ModInfo(ABC):
    """模组信息抽象基类（统一不同源站的接口）"""
    
    def __init__(
        self,
        slug: str,                       # 唯一 ID，如 "fabric-api"
        name: str,                       # 显示名
        description: str,                # 长篇描述
        source: str,                     # [modrinth/curseforge/plugin]
        download_count: int = 0          # 总下载量统计
    ):
        self.slug = slug
        self.name = name
        self.description = description
        self.source = source
        self.download_count = download_count
    
    @abstractmethod
    def get_latest_version(self, mc_version: str) -> Optional[ModFile]:
        """获取指定 MC 版本的最新版
        
        Args:
            mc_version: 目标 Minecraft 版本
            
        Returns:
            ModFile 对象（存在）或 None（不存在）
        """
        pass
    
    @abstractmethod
    def search_versions(self, mc_version: str) -> List[ModFile]:
        """搜索某个模组的所有可用版本
        
        Args:
            mc_version: Minecraft 版本
            
        Returns:
            ModFile 列表（按发布时间降序）
        """
        pass
    
    @abstractmethod
    def get_dependencies(self, file_id: str) -> Dict[str, Any]:
        """获取某个文件的依赖信息
        
        Args:
            file_id: File 唯一标识
            
        Returns:
            依赖字典 { depends_on: [...], conflicts_with: [...] }
        """
        pass


class ModrinthMod(ModInfo):
    """Modrinth 资源站适配器（实际实现由 Infrastructure 层提供）"""
    
    def __init__(self, slug: str, name: str, description: str, download_count: int = 0):
        super().__init__(slug=slug, name=name, description=description, 
                        source="modrinth", download_count=download_count)
        
        # Modrinth 特有字段（API 返回的 slug）
        self.modrinth_id: Optional[str] = None  # API 生成的 UUID
    
    def get_latest_version(self, mc_version: str) -> Optional[ModFile]:
        """Modrinth API 查询：https://modrinth.com/api/v2/version?project={slug}&game_versions={mc_version}"""
        raise NotImplementedError("需要 Infrastructure layer 实现 HTTP 请求")
    
    def search_versions(self, mc_version: str) -> List[ModFile]:
        """分页拉取所有版本（API 限制每页 10 条，支持 cursor）"""
        raise NotImplementedError("需要 Infrastructure layer 实现")
    
    def get_dependencies(self, file_id: str) -> Dict[str, Any]:
        """Modrinth 的 dependencies 字段在 Version API 内"""
        raise NotImplementedError()


class CurseForgeMod(ModInfo):
    """CurseForge 资源站适配器
    
    CF 数据结构更复杂：
    - Modpack + Mod 双重入口
    - 文件分级（release/beta/alpha）
    - 依赖项通过 Relationships API
    """
    
    def __init__(self, slug: str, name: str, description: str, download_count: int = 0):
        super().__init__(slug=slug, name=name, description=description,
                        source="curseforge", download_count=download_count)
        
        # CurseForge 特有字段
        self.cf_project_id: Optional[int] = None  # 项目数字 ID
    
    def get_latest_version(self, mc_version: str) -> Optional[ModFile]:
        """CF API: https://api.curseforge.com/v1/file/index?q=project:...&gameVersion={mc}"""
        raise NotImplementedError("需要 Infrastructure layer 实现")
    
    def search_versions(self, mc_version: str) -> List[ModFile]:
        raise NotImplementedError()
    
    def get_dependencies(self, file_id: str) -> Dict[str, Any]:
        """CF 的 dependencies 在 File Details API 返回 relationships[]"""
        raise NotImplementedError()


class PluginMod(ModInfo):
    """本地插件模块适配器（通过 Node.js RPC 调用外部插件）"""
    
    def __init__(self, slug: str, name: str, description: str):
        super().__init__(slug=slug, name=name, description=description, source="plugin")
    
    def get_latest_version(self, mc_version: str) -> Optional[ModFile]:
        """RPC call → plugin_manager.get_file_list()"""
        raise NotImplementedError("需要 Plugin RPC interface")
    
    def search_versions(self, mc_version: str) -> List[ModFile]:
        raise NotImplementedError()
    
    def get_dependencies(self, file_id: str) -> Dict[str, Any]:
        """本地插件依赖在 package.json 定义"""
        raise NotImplementedError()


@dataclass
class ModInstallationSpec:
    """模组安装规范 - Application 层协调器调用 Infrastructure 下载器时使用
    
    示例：
    spec = ModInstallationSpec(
        mod=ModrinthMod("fabric-api", "Fabric API"),
        target_version="1.20.4",
        files=[file_0.91.0, file_0.90.5]  # Fabric API + Dependencies
    )
    
    infrastructure.download_service.batch_download(spec.files)
    """
    
    mod_info: ModInfo           # 核心模组 Info
    selected_files: List[ModFile]  # 待下载安装的文件列表（含自动解析的前置依赖）


@dataclass
class ModDependencyGraph:
    """模组依赖图构建器输出
    
    应用场景：
    - 安装 A 模组时，自动解析所有前置 B、C...
    - 冲突检测（A vs B 存在 conflicts_with[]）
    
    图遍历算法由 Application layer 负责实现
    """
    root_mod: ModInfo           # 用户请求的根节点
    dependents: List[ModFile]   # 依赖链中的所有文件
    resolution_order: List[ModFile]  # 按依赖层级排序后的安装顺序
