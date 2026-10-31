"""Domain 领域模型包 - MC 核心业务对象 + Mod/Plugin新需求扩展"""

from .version import VersionJSON, ParsedVersion, Library, AssetsIndex
from .account import AccountBase, OfflineAccount, MicrosoftAccount, AccountManager
from .launcher import LoaderType, LoaderVersion, LoaderSpec, LoaderFactory

# === New: Mod Marketplace System ===
from .mod import (
    ModInfo,
    ModFile, 
    ModrinthMod,
    CurseForgeMod,
    PluginMod,
    ModInstallationSpec,
    ModDependencyGraph
)

# === New: Node.js Plugin System ===  
from .plugin import (
    PluginManifest,
    PluginInstance,
    PluginPermissions,
    PluginRPCError,
    VRPC_GLOBAL_EXPORTS
)

__all__ = [
    # Original Domain Models
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
    # Mod System (NEW)
    "ModInfo",
    "ModFile",
    "ModrinthMod",
    "CurseForgeMod", 
    "PluginMod",
    "ModInstallationSpec",
    "ModDependencyGraph",
    # Plugin System (NEW)  
    "PluginManifest",
    "PluginInstance",
    "PluginPermissions",
    "PluginRPCError",
    "VRPC_GLOBAL_EXPORTS"
]
