"""Domain 领域服务模块 - 业务规则实现（无 IO）"""

from .version_resolver import VersionResolver, VersionResolutionError

__all__ = ["VersionResolver", "VersionResolutionError"]
