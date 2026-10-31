"""加载器模型 - Fabric / Forge / Quilt 规则定义"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class LoaderType(Enum):
    """加载器类型枚举"""
    VANILLA = "vanilla"      # 原版（无加载器）
    FABRIC = "fabric"        
    FORGE = "forge"          
    QUILT = "quilt"           # Fabric 兼容但独立


class LoaderVersion(BaseModel):
    """加载器版本信息"""
    
    loader_type: LoaderType
    version_id: str          # 加载器自身版本号，如 fabric-loader-0.14.21
    
    # 对应 MC 主版本
    mc_version: str          # "1.20.4"
    recommended_for_version: Optional[str] = None  # Forge 的"recommended for"字段
    
    # 安装位置（相对路径）
    installation_path: str   # "versions/fabric-1.20.4/"
    
    # Fabric/Quilt 特有
    loader_version: Optional[str] = None      # Loader 本身的版本（fabric-loader-x.y.z）
    server_mods_version: Optional[str] = None # fabric-api-server-mods x.y.z
    
    # Forge 特有  
    installer_profile: Optional[Dict[str, Any]] = None  # ForgeInstallerProfile JSON


class LoaderSpec(BaseModel):
    """加载器安装规范 - 指导如何自动安装"""
    
    loader_type: LoaderType
    target_mc_version: str     # "1.20.4"
    
    # 版本检索 API 端点
    api_url: Optional[str] = None  # 如 https://meta.fabricmc.net/v2/versions/loader
    
    # 已选定的加载器版本（从 API 返回）
    selected_version: Optional[LoaderVersion] = None
    
    # 安装命令/JAVAW 参数模板
    install_command_template: Optional[str] = None


class LoaderInstallerSpec(BaseModel):
    """加载器安装详情"""
    
    target_version_dir: str       # 目标安装目录（绝对路径）
    loader_files: List[Dict[str, Any]]  # 需要下载的库列表
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.loader_files:
            self.loader_files = []


class LoaderRegistry(BaseModel):
    """全局加载器注册表（缓存用）"""
    
    loaded_loaders: List[LoaderVersion] = Field(default_factory=list)
    
    def get_later_versions(self, version_id: str) -> List[LoaderVersion]:
        """获取已安装的同类型加载器版本列表"""
        # 筛选同主版本的加载器
        parts = version_id.split("-")
        if len(parts) < 2:
            return []
        
        main_version = parts[-1]  # "1.20.4"
        typ = parts[0] if "-" in version_id else "vanilla"
        
        result = [v for v in self.loaded_loaders 
                  if v.mc_version == main_version and v.loader_type.value == typ]
        return sorted(result, key=lambda x: x.version_id, reverse=True)


class LoaderFactory(BaseModel):
    """加载器工厂 - 创建新版本的逻辑"""
    
    @staticmethod
    def create_fabric_spec(mc_version: str) -> LoaderSpec:
        """创建 Fabric 安装规范"""
        return LoaderSpec(
            loader_type=LoaderType.FABRIC,
            target_mc_version=mc_version,
            api_url="https://meta.fabricmc.net/v2/versions/loader"
        )
    
    @staticmethod
    def create_forge_spec(mc_version: str) -> LoaderSpec:
        """创建 Forge 安装规范"""
        return LoaderSpec(
            loader_type=LoaderType.FORGE,
            target_mc_version=mc_version,
            api_url=f"https://files.minecraftforge.net/maven/net/minecraftforge/forge/maven-metadata-{mc_version}.xml"
        )
    
    @staticmethod
    def create_quilt_spec(mc_version: str) -> LoaderSpec:
        """创建 Quilt 安装规范"""
        return LoaderSpec(
            loader_type=LoaderType.QUILT,
            target_mc_version=mc_version,
            api_url="https://meta.quiltmc.org/v3/"
        )
