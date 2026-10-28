"""插件宿主能力注册表 —— 权限校验 + 路径沙箱双重防护

设计：
- 每个能力（capability）绑定一个权限标识，插件必须在 manifest 中声明，运行时再校验。
- 文件类能力必须落在允许的根目录内（插件自身 data 目录等），防止越权读写。
- 能力实现由 Application 层注入，基础设施层保持可测试。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Iterable, List, Optional

from vein_launcher.common.exceptions import VeinError

logger = logging.getLogger(__name__)


class PluginPermissionError(VeinError):
    """插件未声明/未授予某项权限"""


class CapabilityNotFoundError(VeinError):
    """未知能力"""


@dataclass(slots=True)
class Capability:
    """一项可被插件调用的宿主能力"""

    name: str
    permission: str
    handler: Callable[..., Awaitable[Any]]
    description: str = ""


class CapabilityRegistry:
    """能力注册与执行"""

    def __init__(self, allowed_roots: Optional[Iterable[Path]] = None):
        self._capabilities: Dict[str, Capability] = {}
        self._allowed_roots: List[Path] = [
            Path(p).resolve() for p in (allowed_roots or [])
        ]

    # -------------------------- 注册 --------------------------
    def register(
        self,
        name: str,
        permission: str,
        handler: Callable[..., Awaitable[Any]],
        description: str = "",
    ) -> None:
        if name in self._capabilities:
            logger.warning("能力重复注册，后注册者覆盖：%s", name)
        self._capabilities[name] = Capability(name, permission, handler, description)

    def add_allowed_root(self, root: Path) -> None:
        """追加可访问目录（插件沙箱）"""
        resolved = Path(root).resolve()
        if resolved not in self._allowed_roots:
            self._allowed_roots.append(resolved)

    def names(self) -> List[str]:
        return sorted(self._capabilities)

    def describe(self) -> List[Dict[str, str]]:
        return [
            {"name": c.name, "permission": c.permission, "description": c.description}
            for c in self._capabilities.values()
        ]

    # -------------------------- 执行 --------------------------
    async def execute(
        self,
        plugin_id: str,
        declared_permissions: Iterable[str],
        api_name: str,
        args: List[Any],
    ) -> Any:
        """执行能力调用

        Raises:
            CapabilityNotFoundError: 能力不存在
            PluginPermissionError: 权限不足
            VeinError: 处理器内部业务错误
        """
        cap = self._capabilities.get(api_name)
        if cap is None:
            raise CapabilityNotFoundError(f"未知能力：{api_name}")

        granted = set(declared_permissions)
        if cap.permission not in granted:
            logger.warning(
                "插件 %s 尝试调用未授权能力 %s（需要 %s）",
                plugin_id, api_name, cap.permission,
            )
            raise PluginPermissionError(
                f"插件 {plugin_id} 缺少权限 {cap.permission}，拒绝调用 {api_name}"
            )

        try:
            return await cap.handler(*args)
        except (CapabilityNotFoundError, PluginPermissionError):
            raise
        except Exception as exc:
            logger.error("能力 %s 执行失败（插件 %s）：%s", api_name, plugin_id, exc)
            raise VeinError(f"{api_name} 执行失败：{exc}") from exc

    # -------------------------- 路径沙箱 --------------------------
    def check_path(self, raw_path: str) -> Path:
        """校验路径是否在允许的根目录内，返回绝对路径

        Raises:
            PluginPermissionError: 越权访问
        """
        if not self._allowed_roots:
            raise PluginPermissionError("未配置插件可访问目录")

        candidate = Path(raw_path)
        if not candidate.is_absolute():
            candidate = self._allowed_roots[0] / candidate
        resolved = candidate.resolve()

        for root in self._allowed_roots:
            try:
                resolved.relative_to(root)
                return resolved
            except ValueError:
                continue
        raise PluginPermissionError(f"越权路径访问被拒绝：{resolved}")
