"""Domain 领域层 - Minecraft 核心业务逻辑与规则

职责：
- 版本解析（继承链合并）
- 账号验证（离线/微软OAuth） 
- 加载器规则（Fabric/Forge/Quilt）
- 模组市场适配（Modrinth/CurseForge抽象接口）
- 插件系统规范（Node.js RPC API定义）

依赖：Common Layer (event_bus, exceptions)
被依赖：Infrastructure, Application Layers
"""

from .models import (
    # Version models
    VersionJSON,
    ParsedVersion, 
    Library,
    AssetsIndex,
    # Account
    AccountBase,
    OfflineAccount,
    MicrosoftAccount,
    AccountManager,
    # Loader
    LoaderType,
    LoaderVersion,
    LoaderSpec,
    LoaderFactory,
    # Mod system (NEW)
    ModInfo,
    ModFile,
    ModrinthMod,
    CurseForgeMod,
    PluginMod,
    # Plugin system (NEW) 
    PluginManifest,
    PluginInstance,
    PluginPermissions,
    VRPC_GLOBAL_EXPORTS
)

from .services import (
    version_resolver  # Will be imported when implemented
)

from .repositories import (
    AbstractFileRepository,
    AssetsRepository,
    LibraryRepository,
    ModRepository,
    AbstractNetworkRepository,
    MojangAPIRepository,
    FabricAPIRepository,  
    ForgeAPIRepository,
    ModrinthAPIRepository,
    CurseForgeAPIRepository
)

__all__ = [
    # Domain Models
    "VersionJSON",
    "ParsedVersion",
    "Library", 
    "AssetsIndex",
    "AccountBase",
    "OfflineAccount",
    "MicrosoftAccount", 
    "AccountManager",
    "LoaderType",
    "LoaderVersion",
    "LoaderSpec",
    "LoaderFactory",
    # Mod System Models (NEW)
    "ModInfo",
    "ModFile",
    "ModrinthMod",
    "CurseForgeMod", 
    "PluginMod",
    # Plugin System Models (NEW)
    "PluginManifest",
    "PluginInstance",
    "PluginPermissions",
    "VRPC_GLOBAL_EXPORTS",
    # Domain Services
    "version_resolver",
    # Repository Interfaces
    "AbstractFileRepository",
    "AssetsRepository",
    "LibraryRepository",
    "ModRepository",
    "AbstractNetworkRepository",
    "MojangAPIRepository",
    "FabricAPIRepository",
    "ForgeAPIRepository",
    "ModrinthAPIRepository",
    "CurseForgeAPIRepository"
]
