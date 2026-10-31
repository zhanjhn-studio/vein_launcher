"""网络 API 仓储接口定义 - Mojang / Fabric / Forge / Modrinth 客户端

Infrastructure layer 负责实现 requests/速率限制/代理设置等具体技术细节。
Domain 只定义业务方法签名（fetch_version, get_mod_info 等）。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class AbstractNetworkRepository(ABC):
    """网络请求抽象基类
    
    Infrastructure 实现者需支持：
    - HTTP / HTTPS 协议
    - GET/POST 方法
    - User-Agent/Mojang Authenticator header
    - 代理设置（全局代理 or API 特定）
    - 超时控制 / 重试机制
    """
    
    @abstractmethod
    async def get_json(self, url: str) -> Dict[str, Any]:
        """GET 请求并返回 JSON 字典"""
        pass
    
    @abstractmethod
    async def stream_download(
        self, 
        url: str,
        save_path: str,
        progress_callback=None  # def callback(downloaded_bytes, total_bytes)
    ) -> bool:
        """分块流式下载（防止大文件内存溢出）"""
        pass


class MojangAPIRepository(AbstractNetworkRepository):
    """Mojang Launcher API 仓储接口
    
    端点参考（https://github.com/LuckPerms/java-mojang-api/blob/main/src/main/kotlin/com/lukperms/java/util/mojang/MojangEndpoints.kt）:
    
    - Version List: https://launchermeta.mojang.com/mc/version.json
    - Single Version: https://launchermeta.mojang.com/mc/versions/{version_id}/{version_id}.json
    - Assets Index: https://launchermeta.mojang.com/v1/packages/{sha1}
    
    特殊注意：Mojang API 需要正确的 User-Agent，否则可能返回 403
    """
    
    @abstractmethod
    async def fetch_version_list(self) -> List[Dict[str, Any]]:
        """获取所有版本列表（带 type/releaseTime/versionId）"""
        pass
    
    @abstractmethod
    async def fetch_version(self, version_id: str) -> Dict[str, Any]:
        """下载单个版本的完整 JSON（含 inheritsFrom/languages/assets 等字段）"""
        pass
    
    @abstractmethod
    async def fetch_assets_index(self, index_id: str) -> Dict[str, Any]:
        """获取 assets/indexes/{index_id}.json（objects[]）"""
        pass


class FabricAPIRepository(AbstractNetworkRepository):
    """Fabric API 仓储接口
    
    Meta API: https://fabricmc.net/developers/docs/apis#meta-api
    
    - Loader Versions: https://meta.fabricmc.net/v2/versions/loader/{mc_version}
    - Fabric API Versions: https://meta.fabricmc.net/v2/versions/content/net/fabricmc/fabric-api
    """
    
    @abstractmethod
    async def get_latest_loader(self, mc_version: str) -> Dict[str, Any]:
        """获取指定 MC 版本的最新版 Fabric Loader"""
        pass
    
    @abstractmethod
    async def get_fabric_api_versions(
        self, 
        mc_version: str,
        loader_version: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取 Fabric API 模组版本列表"""
        pass


class ForgeAPIRepository(AbstractNetworkRepository):
    """Forge Installer API 仓储接口
    
    Maven Metadata: https://files.minecraftforge.net/maven/net/minecraftforge/forge/maven-metadata-{mc_version}.xml
    
    - Latest recommended 版本
    - latest 推荐候选
    """
    
    @abstractmethod
    async def get_recommended_versions(self, mc_version: str) -> Dict[str, Any]:
        """获取推荐的 Forge 版本号"""
        pass


class ModrinthAPIRepository(AbstractNetworkRepository):
    """Modrinth API 仓储接口 - 模组市场核心
    
    API Docs: https://modrinth.com/docs/api#section/Introduction
    
    - Search mods: GET /api/v2/mod/search?query={keyword}
    - Version query: GET /api/v2/version/{version_id}
    - File list: GET /api/v2/project/{slug}/version
    - Download URL: response.url (直接下载)
    
    分页限制：每页最多 100 项，支持 cursor-based pagination
    """
    
    @abstractmethod
    async def search_mods(
        self,
        query: str,                # 搜索关键词
        limit: int = 20,           # 返回数量（≤100）
        tags: List[str] = None,   # ["fabric", "quilt"] 筛选标签
        game_versions: List[str] = None  # ["1.20.4", "1.20.5"] 限定游戏版本
    ) -> List[Dict[str, Any]]:
        """搜索模组，返回项目信息数组"""
        pass
    
    @abstractmethod
    async def get_mod_versions(
        self,
        project_slug: str,         # Modrinth slug
        game_version: Optional[str] = None   # 指定 MC 版本过滤
    ) -> List[Dict[str, Any]]:
        """获取某个模组的所有文件列表（含 dependencies）"""
        pass


class CurseForgeAPIRepository(AbstractNetworkRepository):
    """CurseForge API 仓储接口 - 另一个主流模组市场
    
    API Docs: https://support.curseforge.com/hc/en-us/articles/259043648-Authorizing+for+the+CurseForge+API
    
    需要 API Key（CF 强制要求），在 headers 中携带 "x-api-key"
    """
    
    @abstractmethod  
    async def search_projects(
        self,
        query: str,
        api_key: str,              # CurseForge API Token
        limit: int = 25            # CF API 限制每页最大 25
    ) -> List[Dict[str, Any]]:
        """搜索模组项目"""
        pass
