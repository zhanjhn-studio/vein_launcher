"""插件宿主 —— Node.js 子进程 + 双向 JSON-RPC 2.0（stdio 传输）

这是 Vein Launcher 的核心特色模块：
- Python 侧（本文件）负责：进程生命周期、能力分发、权限校验、事件广播。
- Node 侧（runtime/node_host.js）负责：加载 NPM 插件、注入 `vein` API、异常隔离。

协议（每行一个 JSON 对象）：
  Python → Node : {"jsonrpc":"2.0","id":1,"method":"plugin.load","params":{...}}
  Node  → Python: {"jsonrpc":"2.0","id":1,"result":{...}}
  Node  → Python: {"jsonrpc":"2.0","id":9,"method":"host.call","params":{pluginId,api,args}}
  Python → Node : {"jsonrpc":"2.0","method":"event.emit","params":{topic,payload}}
"""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
from collections import deque
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional

from vein_launcher.common.events.event_bus import event_bus
from vein_launcher.common.events.events import EventNames
from vein_launcher.common.exceptions import VeinError
from vein_launcher.common.utils.path_utils import get_plugins_dir, sanitize_plugin_id
from vein_launcher.domain.models.plugin import PluginManifest
from vein_launcher.infrastructure.plugin_host.capabilities import (
    CapabilityRegistry,
    PluginPermissionError,
)

logger = logging.getLogger(__name__)

DEFAULT_RUNTIME = Path(__file__).parent / "runtime" / "node_host.js"
RPC_TIMEOUT = 30.0
MAX_LINE_BYTES = 4 * 1024 * 1024


class PluginHostError(VeinError):
    """插件宿主生命周期或协议错误"""


class PluginHost:
    """管理 Node.js 插件宿主进程"""

    def __init__(
        self,
        node_exe: Optional[str] = None,
        runtime_script: Optional[Path] = None,
        plugins_root: Optional[Path] = None,
        capabilities: Optional[CapabilityRegistry] = None,
        rpc_timeout: float = RPC_TIMEOUT,
    ):
        self._node_exe = node_exe or shutil.which("node")
        self._runtime = Path(runtime_script) if runtime_script else DEFAULT_RUNTIME
        self._plugins_root = Path(plugins_root) if plugins_root else get_plugins_dir()
        self._capabilities = capabilities or CapabilityRegistry()
        self._rpc_timeout = rpc_timeout

        self._proc: Optional[asyncio.subprocess.Process] = None
        self._read_task: Optional[asyncio.Task] = None
        self._err_task: Optional[asyncio.Task] = None
        self._pending: Dict[int, asyncio.Future] = {}
        self._next_id = 0
        self._plugins: Dict[str, Dict[str, Any]] = {}
        self._logs: Deque[str] = deque(maxlen=2000)
        self._lock = asyncio.Lock()
        self._closing = False

    # ------------------------------------------------------------------
    # 状态
    # ------------------------------------------------------------------
    @property
    def running(self) -> bool:
        return self._proc is not None and self._proc.returncode is None

    @property
    def pid(self) -> Optional[int]:
        return self._proc.pid if self._proc else None

    def recent_logs(self, limit: int = 200) -> List[str]:
        return list(self._logs)[-limit:]

    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------
    async def start(self) -> None:
        """启动 Node 宿主进程（幂等）"""
        if self.running:
            return
        if not self._node_exe:
            raise PluginHostError("未找到 Node.js，请安装 Node.js 18+ 或配置路径")
        if not self._runtime.is_file():
            raise PluginHostError(f"插件宿主脚本缺失：{self._runtime}")

        self._plugins_root.mkdir(parents=True, exist_ok=True)
        self._capabilities.add_allowed_root(self._plugins_root)

        logger.info("启动插件宿主：%s %s", self._node_exe, self._runtime)
        self._proc = await asyncio.create_subprocess_exec(
            self._node_exe,
            str(self._runtime),
            "--plugins-root",
            str(self._plugins_root),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            limit=MAX_LINE_BYTES,
        )
        self._closing = False
        self._read_task = asyncio.create_task(self._read_stdout())
        self._err_task = asyncio.create_task(self._read_stderr())

        info = await self._request("host.ping", {}, timeout=15)
        event_bus.publish(EventNames.PLUGIN_HOST_STARTED, pid=self.pid, info=info)
        logger.info("插件宿主就绪 PID=%s node=%s", self.pid, (info or {}).get("node"))

    async def stop(self) -> None:
        """停止宿主：先请求优雅退出，超时再强杀"""
        if self._proc is None:
            return
        self._closing = True
        try:
            await self._request("host.shutdown", {}, timeout=5)
        except (PluginHostError, asyncio.TimeoutError):
            pass

        if self._proc.returncode is None:
            self._proc.terminate()
            try:
                await asyncio.wait_for(self._proc.wait(), timeout=5)
            except asyncio.TimeoutError:
                self._proc.kill()
                await self._proc.wait()

        for task in (self._read_task, self._err_task):
            if task:
                task.cancel()
        self._fail_pending(PluginHostError("宿主已停止"))
        self._proc = None
        self._plugins.clear()
        event_bus.publish(EventNames.PLUGIN_HOST_STOPPED, pid=None)
        logger.info("插件宿主已停止")

    async def restart(self) -> None:
        await self.stop()
        await self.start()

    # ------------------------------------------------------------------
    # 插件操作
    # ------------------------------------------------------------------
    async def load_plugin(self, manifest: PluginManifest, install_path: Path) -> None:
        """通知 Node 侧激活插件"""
        await self.start()
        plugin_id = manifest.name
        entry = install_path / manifest.main_entry
        if not entry.is_file():
            raise PluginHostError(f"插件入口不存在：{entry}")

        self._plugins[plugin_id] = {
            "manifest": manifest,
            "path": install_path.resolve(),
            "entry": entry.resolve(),
        }

        try:
            await self._request(
                "plugin.load",
                {
                    "pluginId": plugin_id,
                    "entry": str(entry.resolve()),
                    "manifest": {
                        "name": manifest.name,
                        "version": manifest.version,
                        "displayName": manifest.display_name,
                        "permissions": list(manifest.permissions),
                        "apiVersion": manifest.api_version,
                    },
                    "dataDir": str(
                        (self._plugins_root / sanitize_plugin_id(plugin_id) / "data").resolve()
                    ),
                },
                timeout=self._rpc_timeout,
            )
        except Exception:
            self._plugins.pop(plugin_id, None)
            raise

        event_bus.publish(
            EventNames.PLUGIN_LOADED, plugin_id=plugin_id, version=manifest.version
        )
        logger.info("插件已激活：%s@%s", plugin_id, manifest.version)

    async def unload_plugin(self, plugin_id: str) -> None:
        """停用插件（未加载也安全）"""
        if plugin_id in self._plugins and self.running:
            try:
                await self._request("plugin.unload", {"pluginId": plugin_id}, timeout=10)
            except (PluginHostError, asyncio.TimeoutError) as exc:
                logger.warning("插件卸载异常 %s: %s", plugin_id, exc)
        self._plugins.pop(plugin_id, None)
        event_bus.publish(EventNames.PLUGIN_UNLOADED, plugin_id=plugin_id)

    async def invoke(
        self, plugin_id: str, method: str, args: Optional[List[Any]] = None, timeout: Optional[float] = None
    ) -> Any:
        """Python → 插件 的主动调用（如 UI 按钮触发插件命令）"""
        if plugin_id not in self._plugins:
            raise PluginHostError(f"插件未加载：{plugin_id}")
        return await self._request(
            "plugin.invoke",
            {"pluginId": plugin_id, "method": method, "args": args or []},
            timeout=timeout or self._rpc_timeout,
        )

    async def emit_event(self, topic: str, payload: Optional[Dict[str, Any]] = None) -> None:
        """把启动器事件广播给所有已加载插件（通知，不等响应）"""
        if not self.running:
            return
        self._send(
            {"jsonrpc": "2.0", "method": "event.emit", "params": {"topic": topic, "payload": payload or {}}}
        )

    # ------------------------------------------------------------------
    # 协议底层
    # ------------------------------------------------------------------
    def _send(self, payload: Dict[str, Any]) -> None:
        assert self._proc is not None and self._proc.stdin is not None
        line = json.dumps(payload, ensure_ascii=False) + "\n"
        try:
            self._proc.stdin.write(line.encode("utf-8"))
        except (BrokenPipeError, ConnectionResetError) as exc:
            raise PluginHostError(f"写入宿主失败：{exc}") from exc

    async def _request(self, method: str, params: Dict[str, Any], timeout: float) -> Any:
        if not self.running:
            raise PluginHostError("插件宿主未运行")
        self._next_id += 1
        req_id = self._next_id
        future: asyncio.Future = asyncio.get_running_loop().create_future()
        self._pending[req_id] = future
        self._send({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params})
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        finally:
            self._pending.pop(req_id, None)

    def _fail_pending(self, exc: BaseException) -> None:
        for future in self._pending.values():
            if not future.done():
                future.set_exception(exc)
        self._pending.clear()

    async def _read_stdout(self) -> None:
        """逐行读取 Node 输出"""
        assert self._proc is not None and self._proc.stdout is not None
        stream = self._proc.stdout
        try:
            while True:
                raw = await stream.readline()
                if not raw:
                    break
                line = raw.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    message = json.loads(line)
                except json.JSONDecodeError:
                    self._logs.append(line)
                    logger.debug("[node] %s", line)
                    continue
                await self._handle_message(message)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # 读取线程异常不应静默
            logger.error("插件宿主输出读取异常：%s", exc)
        finally:
            self._fail_pending(PluginHostError("插件宿主连接已断开"))
            if not self._closing:
                event_bus.publish(EventNames.PLUGIN_ERROR, plugin_id="<host>", error="宿主进程意外退出")
                logger.warning("插件宿主进程退出，退出码=%s", self._proc.returncode if self._proc else None)

    async def _read_stderr(self) -> None:
        """Node 侧 console 输出统一走 stderr"""
        assert self._proc is not None and self._proc.stderr is not None
        try:
            while True:
                raw = await self._proc.stderr.readline()
                if not raw:
                    break
                line = raw.decode("utf-8", errors="replace").rstrip()
                if line:
                    self._logs.append(line)
                    logger.debug("[node:stderr] %s", line)
        except (asyncio.CancelledError, ValueError):
            return

    async def _handle_message(self, message: Dict[str, Any]) -> None:
        """分发：响应 / 请求 / 通知"""
        if "id" in message and ("result" in message or "error" in message):
            future = self._pending.get(message["id"])
            if future and not future.done():
                if message.get("error"):
                    err = message["error"]
                    future.set_exception(
                        PluginHostError(f"[{err.get('code')}] {err.get('message')}")
                    )
                else:
                    future.set_result(message.get("result"))
            return

        method = message.get("method", "")
        params = message.get("params") or {}

        if "id" in message:
            # Node 发起的请求，需要响应
            try:
                result = await self._handle_request(method, params)
                self._send({"jsonrpc": "2.0", "id": message["id"], "result": result})
            except PluginPermissionError as exc:
                self._logs.append(f"PERMISSION DENIED: {exc}")
                event_bus.publish(
                    EventNames.PLUGIN_PERMISSION_DENIED,
                    plugin_id=params.get("pluginId", "?"),
                    api=params.get("api", "?"),
                    error=str(exc),
                )
                self._send(
                    {
                        "jsonrpc": "2.0",
                        "id": message["id"],
                        "error": {"code": -32003, "message": str(exc)},
                    }
                )
            except Exception as exc:
                self._send(
                    {
                        "jsonrpc": "2.0",
                        "id": message["id"],
                        "error": {"code": -32603, "message": str(exc)},
                    }
                )
            return

        # 通知
        if method == "plugin.log":
            text = f"[{params.get('pluginId','?')}] {params.get('message','')}"
            self._logs.append(text)
            event_bus.publish(
                EventNames.PLUGIN_LOG,
                plugin_id=params.get("pluginId", "?"),
                level=params.get("level", "info"),
                message=params.get("message", ""),
            )
        elif method == "plugin.error":
            event_bus.publish(
                EventNames.PLUGIN_ERROR,
                plugin_id=params.get("pluginId", "?"),
                error=params.get("error", ""),
                stack=params.get("stack", ""),
            )
            logger.error("插件异常 %s: %s", params.get("pluginId"), params.get("error"))
        elif method == "plugin.ready":
            logger.debug("插件就绪：%s", params.get("pluginId"))

    async def _handle_request(self, method: str, params: Dict[str, Any]) -> Any:
        """处理 Node 侧请求"""
        if method == "host.call":
            plugin_id = str(params.get("pluginId", ""))
            api = str(params.get("api", ""))
            args = list(params.get("args") or [])

            plugin = self._plugins.get(plugin_id)
            if plugin is None:
                raise PluginHostError(f"未知插件：{plugin_id}")
            manifest: PluginManifest = plugin["manifest"]

            # 文件类能力强制收敛到插件目录内
            return await self._capabilities.execute(
                plugin_id, manifest.permissions, api, args
            )
        raise PluginHostError(f"未知宿主方法：{method}")


__all__ = ["PluginHost", "PluginHostError", "DEFAULT_RUNTIME"]
