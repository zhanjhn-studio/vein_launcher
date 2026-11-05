"""Minecraft 版本模型 - Mojang 版本 JSON 解析

字段命名对齐 launchermeta 的真实 JSON（camelCase），Python 侧一律 snake_case，
靠 pydantic 的 alias + populate_by_name 双向兼容：

    {"id": "1.20.4", "releaseTime": "...", "mainClass": "...", "assetIndex": {...}}

两条来自真实数据的容错约定：

1. 单版本 JSON（piston-meta 上的 `1.20.4.json`）**没有** `url` 字段，
   `url` 只出现在 version_manifest 的条目里；因此 `url` 可选。
2. Fabric/Forge 生成的子版本 JSON（`inheritsFrom` 指向父版本）通常**完全没有**
   `assets` / `assetIndex` / `javaVersion`，全部从父版本继承；因此这些字段可选，
   避免一份合法 JSON 因为缺一个非关键字段就整体解析失败。

未声明的字段按 pydantic 默认策略忽略（extra=ignore），故这里显式保留后续启动
链路（类路径、资源索引、日志配置）真正需要的 `downloads` / `logging`。
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, ConfigDict, Field


class VersionInfo(BaseModel):
    """版本基础信息（单版本 JSON 与 manifest 条目共用）"""

    version_id: str = Field(..., alias="id", description="版本 ID，如 '1.20.4'")
    type_: str = Field(..., alias="type", description="类型：release/snapshot/old_beta/old_alpha")
    url: Optional[str] = Field(
        default=None,
        description="版本 JSON 下载地址；仅 version_manifest 条目提供，单版本 JSON 内没有此字段",
    )
    release_time: Optional[datetime] = Field(
        default=None, alias="releaseTime", description="发布时间（ISO 8601）"
    )

    model_config = ConfigDict(populate_by_name=True)


class JavaVersion(BaseModel):
    """`javaVersion` 对象 - Mojang 声明的 Java 运行时要求"""

    component: Optional[str] = Field(default=None, description="如 'java-runtime-gamma'")
    major_version: int = Field(
        default=17, alias="majorVersion", description="所需 Java 大版本，如 17 / 21 / 8"
    )

    model_config = ConfigDict(populate_by_name=True)


class AssetsIndex(BaseModel):
    """资源索引定义（`assetIndex` 对象，或退化为索引 ID 字符串）"""

    id_: str = Field(..., alias="id", description="版本号，如 '12'")
    url: Optional[str] = Field(default=None, description="objects 索引 JSON 下载地址")
    sha1: Optional[str] = Field(default=None, description="objects 索引校验和")
    size: Optional[int] = None
    total_size: Optional[int] = Field(default=None, alias="totalSize")

    model_config = ConfigDict(populate_by_name=True)


class LibraryRules(BaseModel):
    """库规则（条件性加载，旧格式占位）"""

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

    model_config = ConfigDict(populate_by_name=True)


class LibraryArtifact(BaseModel):
    """库工件定义"""

    path: str = Field(..., description="相对路径，如 'net/minecraft/client/main.jar'")
    url: str = Field(..., description="下载地址")
    size: Optional[int] = Field(default=None, description="文件大小 (字节)")
    sha1: Optional[str] = Field(default=None, description="SHA-1 校验和")


class LibraryNatives(BaseModel):
    """平台相关原生库"""

    linux64: Optional[str] = None
    osx64: Optional[str] = None
    windows64: Optional[str] = Field(None, alias="win64")

    model_config = ConfigDict(populate_by_name=True)


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
    native_systems: Optional[LibraryNatives] = Field(default=None, alias="natives")

    # 下载分类器（多版本下载：classifier=win64 对应 natives.win64）
    classifiers: Optional[Dict[str, LibraryArtifact]] = None

    # 规则过滤系统：os.name / os.arch / os.version / features
    rules: Optional[List[Dict[str, Any]]] = None

    # 依赖项
    depends: Optional[List["Library"]] = Field(default=None, alias="dependencies")

    model_config = ConfigDict(populate_by_name=True)


class VersionJSON(VersionInfo):
    """完整的 Minecraft 版本 JSON 模型

    参考：https://piston-meta.mojang.com/v1/packages/.../1.20.4.json
    """

    # 继承关系
    inherits_from: Optional[str] = Field(
        default=None,
        alias="inheritsFrom",
        description="父版本 ID（版本继承机制，合并 assets/libraries）",
    )

    # 资源索引：旧字段 assets 是索引名字符串，新字段 assetIndex 是完整对象
    assets: Optional[str] = Field(
        default=None, description="索引 ID（legacy/old_assets/数字）；子版本 JSON 常缺省"
    )
    asset_index: Optional[AssetsIndex] = Field(
        default=None, alias="assetIndex", description="显式 assets 对象（新版本格式）"
    )

    # 库列表
    libraries: List[Library] = Field(default_factory=list)

    # 启动相关
    main_class: Optional[str] = Field(
        default=None,
        alias="mainClass",
        description="主类完整名，如 'net.minecraft.client.main.Main'；子版本 JSON 会覆盖父版本",
    )
    minecraft_arguments: Optional[str] = Field(
        default=None,
        alias="minecraftArguments",
        description="旧格式参数模板字符串（新版已废弃，改用 arguments）",
    )
    argument_override: Optional[Union[Dict[str, List[Any]], List[Any]]] = Field(
        default=None, alias="arguments", description="命令行参数（game/jvm 两个列表）"
    )

    # Java 运行时要求（对齐真实 JSON 的 javaVersion.majorVersion）
    java_version: Optional[JavaVersion] = Field(
        default=None, alias="javaVersion", description="Mojang 声明的 Java 要求"
    )

    # 启动链路需要透传、但不参与领域规则的原始配置
    downloads: Optional[Dict[str, Any]] = Field(
        default=None, description="client/server 工件下载信息（启动前补齐 client.jar 用）"
    )
    logging: Optional[Dict[str, Any]] = Field(
        default=None, description="日志配置客户端（log4j 启动参数用）"
    )
    minimum_launcher_version: Optional[int] = Field(default=None, alias="minimumLauncherVersion")

    # 服务端支持
    server_assets_index: Optional[AssetsIndex] = Field(default=None, alias="server-assets")
    server_main_class: Optional[str] = Field(default=None, alias="serverMainClass")

    changes: Optional[Dict[str, Any]] = None  # 变更说明

    model_config = ConfigDict(populate_by_name=True)

    @property
    def java_requirement(self) -> int:
        """所需 Java 大版本；缺 `javaVersion` 时按 17 兜底（解析器再做版本启发式）"""
        return self.java_version.major_version if self.java_version else 17


class ParsedVersion(BaseModel):
    """解析后的版本对象（已合并继承链）"""

    version_id: str
    type_: str = Field(..., alias="type")

    # 完整信息；assets_index 允许为字符串（只拿得到索引名、没有对象时）
    assets_index: Union[AssetsIndex, str]
    libraries: List[Library]
    main_class: str

    # Java 要求
    java_version_requirement: int = Field(default=17)

    # 继承链（用于调试）：leaf → root 顺序
    inheritance_chain: List[str] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)
