"""文件仓储接口定义 - Domain 层不实现具体 IO 逻辑

Infrastructure layer 负责实现此接口的具体存储逻辑。
Domain 只定义抽象方法签名，保证业务逻辑与技术细节分离。
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any


class AbstractFileRepository(ABC):
    """文件仓储抽象接口
    
    实现者：infrastructure.storage.file_storage.FileStorageImpl
    
    职责：
    - assets/ objects（资源包）存取
    - libraries/*.jar（依赖库）管理  
    - mods/ config/目录操作
    - SHA-1 校验辅助
    """
    
    @abstractmethod
    async def save_file(
        self, 
        file_path: Path, 
        content_bytes: bytes,
        expected_sha1: Optional[str] = None
    ) -> bool:
        """
        保存文件（Infrastructure 层实现断点续传 + SHA 校验）
        
        Args:
            file_path: 目标文件绝对路径
            content_bytes: 二进制内容
            expected_sha1: 期望的 SHA-1 值（可选，用于校验）
            
        Returns:
            bool - True=成功（已写入磁盘），False=失败
            
        Raises:
            - IOError: 磁盘满/权限拒绝
            - SHAMismatchError: 如果提供了 expected_sha1 但校验失败
        """
        pass
    
    @abstractmethod
    async def load_file(self, file_path: Path) -> Optional[bytes]:
        """读取文件二进制内容"""
        pass
    
    @abstractmethod
    async def exists(self, file_path: Path) -> bool:
        """检查文件是否存在（不读入内存）"""
        pass
    
    @abstractmethod
    async def sha1_hash(self, file_path: Path) -> Optional[str]:
        """
        计算文件的 SHA-1 hash
        
        实现建议：使用 hashlib.sha1()，分块读取大文件避免内存溢出
        """
        pass
    
    @abstractmethod  
    async def delete_file(self, file_path: Path) -> bool:
        """删除单个文件"""
        pass
    
    @abstractmethod
    async def ensure_dir(self, dir_path: Path) -> None:
        """确保目录存在（mkdir -p）"""
        pass


class AssetsRepository(AbstractFileRepository):
    """Assets 资源仓储接口（特殊处理：objects.json + 子文件管理）"""
    
    @abstractmethod
    async def download_assets_index(
        self, 
        index_id: str, 
        url: str  
    ) -> Dict[str, Any]:
        """下载 assets/indexes/{index_id}.json，返回 objects 字典"""
        pass
    
    @abstractmethod
    async def get_asset_file_path(self, hash_name: str) -> Path:
        """
        根据哈希值返回本地文件路径
        
        Assets 存储逻辑：
        - Objects/xx/hash[0-2]/hash
        
        示例："abc123..." → "objects/ab/c123.../abc123"
        """
        pass


class LibraryRepository(AbstractFileRepository):
    """Libraries 依赖库仓储接口
    
    特殊规则：
    1. 存储路径格式：
       - maven.group/artifact/version.jar → "libraries/net/minecraftforge/forge/1.20.4-xxxx.jar"
       
    2. extract 处理的 natives（解压到临时目录，供 JVM 加载）
    
    3. 全局共享机制（多版本复用同一 jar）
    """
    
    @abstractmethod
    async def get_library_cache_path(self, maven_coord: str) -> Path:
        """根据 Maven 坐标返回缓存路径"""
        pass
    
    @abstractmethod
    async def extract_natives(
        self, 
        jar_path: Path,
        target_dir: Path,
        exclude_patterns: list[str] = None  # ["META-INF/*"]
    ) -> bool:
        """解压 JAR 到 natives 目录（LWJGL/opengl/d3d 等本地库）"""
        pass


class ModRepository(AbstractFileRepository):
    """Mods 模组文件仓储接口
    
    每个版本独享一个 mods/ 子目录：
    instances/<version_id>/mods/*.jar
    """
    
    @abstractmethod
    async def get_version_mods_dir(self, version_id: str) -> Path:
        """获取指定版本的 mods 目录"""
        pass
    
    @abstractmethod
    async def list_enabled_mods(self, version_id: str) -> list[str]:
        """列出启用的模组文件（.jar 扩展）"""
        pass
    
    @abstractmethod
    async def disable_mod(
        self, 
        version_id: str,
        mod_file_name: str
    ) -> bool:
        """禁用模组（重命名为 .disabled.jar，不移除）"""
        pass
