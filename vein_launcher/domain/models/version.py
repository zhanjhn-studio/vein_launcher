"""Minecraft 版本模型 - Mojang 版本 JSON 解析"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class VersionInfo(BaseModel):
    """版本基础信息"""
    version_id: str = Field(..., description="版本 ID，如 '1.20.4'")
    type_: str = Field(..., alias="type", description="类型：release/snapshot")
    url: str = Field(..., description="版本 JSON 下载地址")
    release_time: datetime = Field(..., description="发布时间")
    
    class Config:
        populate_by_name = True


class LibraryRules(BaseModel):
    """库规则（条件性加载）"""
    allows: Optional[List[str]] = None
    excludes: Optional[List[str]] = None


class LibraryFeatureRules(BaseModel):
    """特性规则（MC 版本范围过滤）"""
    features: Optional[Dict[str, List[str]]] = None


class LibraryOS(BaseModel):
    """操作系统过滤规则"""
    name: str
    rules: Optional[List[LibraryRules]] = None


class LibraryNativeDependencies(BaseModel):
    """原生库依赖链"""
    id_: str = Field(..., alias="id")
    
    class Config:
        populate_by_name = True


class LibraryArtifact(BaseModel):
    """库工件定义"""
    path: str = Field(..., description="相对路径，如 'net/minecraft/client/main.jar'")
    url: str = Field(..., description="下载地址")
    size: int = Field(..., description="文件大小 (字节)")
    sha1: str = Field(..., description="SHA-1 校验和")


class LibraryNatives(BaseModel):
    """平台相关原生库"""
    linux64: Optional[str] = None
    osx64: Optional[str] = None
    windows64: Optional[str] = Field(None, alias="win64")
    
    class Config:
        populate_by_name = True


class Library(BaseModel):
    """库/依赖项模型 - Mojang libraries[] 对象"""
    
    name: str = Field(..., description="库名称，如 'net.minecrell:terminalconsoleappender'")
    downloads: Optional[Dict[str, Any]] = None  # 包含 artifact/classifiers
    
    # 提取规则
    extract: Optional[Union[bool, List[str]]] = Field(
        default=None, 
        description="是否需要解压：true=全提取，false=不解压（作为 JAR），['*'] 或 ['特定文件']=部分提取"
    )
    
    # 平台过滤
    native_systems: Optional[LibraryNatives] = None
    
    # 下载分类器（多版本下载：classifier=win64 对应 natives.win64）
    classifiers: Optional[Dict[str, LibraryArtifact]] = None
    
    # 规则过滤系统
    rules: Optional[List[Dict[str, Any]]] = None  # os/rule/feature 等
    
    # 依赖项
    depends: Optional[List["Library"]] = Field(default=None, alias="dependencies")
    
    class Config:
        populate_by_name = True


class AssetsIndex(BaseModel):
    """资源索引定义"""
    id_: str = Field(..., alias="id", description="版本号，如 '12'")
    url: str = Field(..., description="objects.json 下载地址")


class VersionJSON(VersionInfo):
    """完整的 Minecraft 版本 JSON 模型
    
    参考：https://launchermeta.mojang.com/mc/version/1.20.4/1.20.4.json
    """
    
    # 继承关系
    inherits_from: Optional[str] = Field(
        default=None, 
        description="父版本 ID（版本继承机制，合并 assets/libraries）"
    )
    
    # 资源索引
    assets: str = Field(..., description="legacy/old_assets/或数字版本（索引 ID）")
    
    # 显式 assets 对象（新版本格式）
    asset_index: Optional[AssetsIndex] = None
    
    # 库列表
    libraries: List[Library] = Field(default_factory=list)
    
    # 启动相关
    main_class: str = Field(..., description="主类完整名，如 'net.minecraft.client.main.Main'")
    minecraft_arguments: Optional[str] = Field(
        default=None, 
        description="旧格式参数模板（新版已废弃）"
    )
    
    # 命令行参数数组（新版推荐）
    argument_override: Optional[List[Dict[str, Any]]] = None
    
    # 服务端支持
    server_assets_index: Optional[AssetsIndex] = Field(
        default=None, 
        alias="server-assets"
    )
    server_main_class: Optional[str] = None
    
    # 兼容性标记
    minimum_java_version: Dict[str, int] = Field(
        default={"major": 17}, 
        description="最低 Java 版本要求"
    )
    
    changes: Optional[Dict[str, Any]] = None  # 变更说明
    
    class Config:
        populate_by_name = True


class ParsedVersion(BaseModel):
    """解析后的版本对象（已合并继承链）"""
    
    version_id: str
    type_: str = Field(..., alias="type")
    
    # 完整信息
    assets_index: AssetsIndex
    libraries: List[Library]
    main_class: str
    
    # Java 要求
    java_version_requirement: int = Field(default=17)
    
    # 继承链（用于调试）
    inheritance_chain: List[str] = Field(default_factory=list)
    
    class Config:
        populate_by_name = True
