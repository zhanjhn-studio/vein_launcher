"""Domain 仓储接口定义 - Infrastructure 层负责实现"""

from .file_repo import (
    AbstractFileRepository,
    AssetsRepository,
    LibraryRepository,
    ModRepository
)

from .network_repo import (
    AbstractNetworkRepository,
    MojangAPIRepository,
    FabricAPIRepository,
    ForgeAPIRepository,
    ModrinthAPIRepository,
    CurseForgeAPIRepository
)

__all__ = [
    # File storage interfaces
    "AbstractFileRepository",
    "AssetsRepository",
    "LibraryRepository",
    "ModRepository",
    # Network API interfaces  
    "AbstractNetworkRepository",
    "MojangAPIRepository",
    "FabricAPIRepository",
    "ForgeAPIRepository",
    "ModrinthAPIRepository",
    "CurseForgeAPIRepository"
]
