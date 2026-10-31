"""插件宿主能力注册表：权限校验 + 路径沙箱"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Iterable, List, Optional

from vein_launcher.common.exceptions import VeinError

logger = logging.getLogger(__name__)


class PluginPermissionError(VeinError):
    """插件未声明该权限"""


class CapabilityNotFoundError(VeinError):
    """未知能力"""


@dataclass(slots=True)
class Capability:
    name: str
    permission: str
    handler: Callable[..., Awaitable[Any]]


class CapabilityRegistry:
    """能力注册与执行"""

    def __init__(self, allowed_roots: Optional[Iterable[Path]] = None):
        self._caps: Dict[str, Capability] = {}
        self._roots: List[Path] = [Path(p).resolve() for p in (allowed_roots or [])]

    def register(self, name: str, permission: str, handler: Callable[..., Awaitable[Any]]) -> None:
        self._caps[name] = Capability(name, permission, handler)

    def add_root(self, root: Path) -> None:
        resolved = Path(root).resolve()
        if resolved not in self._roots:
            self._roots.append(resolved)

    def names(self) -> List[str]:
        return sorted(self._caps)

    async def execute(self, plugin_id: str, permissions: Iterable[str], api: str, args: List[Any]) -> Any:
        cap = self._caps.get(api)
        if cap is None:
            raise CapabilityNotFoundError(f"未知能力：{api}")
        if cap.permission not in set(permissions):
            raise PluginPermissionError(f"插件 {plugin_id} 缺少权限 {cap.permission}")
        return await cap.handler(plugin_id, *args)

    def check_path(self, raw: str) -> Path:
        """把插件传入的路径限制在允许的根目录内"""
        if not self._roots:
            raise PluginPermissionError("未配置插件目录")
        candidate = Path(raw)
        if not candidate.is_absolute():
            candidate = self._roots[0] / candidate
        resolved = candidate.resolve()
        for root in self._roots:
            try:
                resolved.relative_to(root)
                return resolved
            except ValueError:
                continue
        raise PluginPermissionError(f"越权路径：{resolved}")


__all__ = ["CapabilityRegistry", "PluginPermissionError", "CapabilityNotFoundError"]
