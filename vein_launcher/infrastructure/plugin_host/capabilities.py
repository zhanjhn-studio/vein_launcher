"""插件宿主能力注册表：权限校验 + 路径沙箱 + 调用超时"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Iterable, List, Optional

from vein_launcher.common.exceptions import VeinError

logger = logging.getLogger(__name__)

# 单次能力调用的默认超时（秒）。插件写法出 bug 时不会永久挂住宿主。
DEFAULT_TIMEOUT = 30.0


class PluginPermissionError(VeinError):
    """插件未声明该权限"""


class CapabilityNotFoundError(VeinError):
    """未知能力"""


class CapabilityTimeoutError(VeinError):
    """能力调用超时"""


@dataclass(slots=True)
class Capability:
    name: str
    permission: str
    handler: Callable[..., Awaitable[Any]]
    timeout: float = DEFAULT_TIMEOUT


class CapabilityRegistry:
    """能力注册与执行"""

    def __init__(self, allowed_roots: Optional[Iterable[Path]] = None):
        self._caps: Dict[str, Capability] = {}
        self._roots: List[Path] = [Path(p).resolve() for p in (allowed_roots or [])]

    def register(
        self,
        name: str,
        permission: str,
        handler: Callable[..., Awaitable[Any]],
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._caps[name] = Capability(name, permission, handler, timeout)

    def add_root(self, root: Path) -> None:
        resolved = Path(root).resolve()
        if resolved not in self._roots:
            self._roots.append(resolved)

    def names(self) -> List[str]:
        return sorted(self._caps)

    def describe(self) -> List[Dict[str, str]]:
        """供插件页展示：能力名 → 所需权限"""
        return [
            {"name": c.name, "permission": c.permission}
            for c in sorted(self._caps.values(), key=lambda c: c.name)
        ]

    async def execute(self, plugin_id: str, permissions: Iterable[str], api: str, args: List[Any]) -> Any:
        cap = self._caps.get(api)
        if cap is None:
            raise CapabilityNotFoundError(f"未知能力：{api}")
        if cap.permission not in set(permissions):
            raise PluginPermissionError(f"插件 {plugin_id} 缺少权限 {cap.permission}")
        try:
            return await asyncio.wait_for(cap.handler(plugin_id, *args), timeout=cap.timeout)
        except asyncio.TimeoutError as exc:
            logger.warning("插件 %s 调用 %s 超时（%.0fs）", plugin_id, api, cap.timeout)
            raise CapabilityTimeoutError(f"{api} 调用超时（{cap.timeout:.0f}s）") from exc

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


__all__ = [
    "CapabilityRegistry",
    "PluginPermissionError",
    "CapabilityNotFoundError",
    "CapabilityTimeoutError",
    "DEFAULT_TIMEOUT",
]
