"""插件宿主：Node.js 子进程 + JSON-RPC 2.0（stdio）

协议（逐行 JSON）：
    Python → Node : {"jsonrpc":"2.0","id":n,"method":"plugin.load",...}
    Node  → Python: {"jsonrpc":"2.0","id":n,"method":"host.call",...}
    Python → Node : {"jsonrpc":"2.0","method":"event.emit",...}
"""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from vein_launcher.infrastructure.plugin_host.capabilities import (
    CapabilityRegistry,
    PluginPermissionError,
)
from vein_launcher.infrastructure.plugin_host.loader import InstalledPlugin, PluginManifest

logger = logging.getLogger(__name__)

RUNTIME = Path(__file__).parent / "runtime" / "node_host.js"
MAX_LINE = 4 * 1024 * 1024


class PluginHostError(Exception):
    """宿主生命周期错误"""


class PluginHost:
    """管理 Node 宿主进程"""

    def __init__(self, capabilities: CapabilityRegistry, node: Optional[str] = None):
        self._capabilities = capabilities
        self._node = node or shutil.which("node")
        self._proc: Optional[asyncio.subprocess.Process] = None
        self._reader: Optional[asyncio.Task] = None
        self._errors: Optional[asyncio.Task] = None
        self._pending: Dict[int, asyncio.Future] = {}
        self._next_id = 0
        self._plugins: Dict[str, InstalledPlugin] = {}
        self._logs: List[str] = []

    @property
    def running(self) -> bool:
        return self._proc is not None and self._proc.returncode is None

    @property
    def pid(self) -> Optional[int]:
        return self._proc.pid if self._proc else None

    def recent_logs(self, limit: int = 50) -> List[str]:
        return self._logs[-limit:]

    # ------------------------------------------------------------------
    async def start(self) -> None:
        if self.running:
            return
        if not self._node:
            raise PluginHostError("未找到 Node.js")
        if not RUNTIME.is_file():
            raise PluginHostError(f"宿主脚本缺失：{RUNTIME}")

        self._proc = await asyncio.create_subprocess_exec(
            self._node, str(RUNTIME),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            limit=MAX_LINE,
        )
        self._reader = asyncio.create_task(self._read_stdout())
        self._errors = asyncio.create_task(self._read_stderr())
        info = await self._request("host.ping", {}, timeout=10)
        logger.info("插件宿主就绪 pid=%s node=%s", self.pid, (info or {}).get("node"))

    async def stop(self) -> None:
        if self._proc is None:
            return
        try:
            await self._request("host.shutdown", {}, timeout=3)
        except Exception:
            pass
        if self._proc.returncode is None:
            self._proc.terminate()
            try:
                await asyncio.wait_for(self._proc.wait(), timeout=5)
            except asyncio.TimeoutError:
                self._proc.kill()
                await self._proc.wait()
        for task in (self._reader, self._errors):
            if task:
                task.cancel()
        self._proc = None
        self._plugins.clear()

    # ------------------------------------------------------------------
    async def load(self, plugin: InstalledPlugin) -> None:
        await self.start()
        entry = plugin.path / plugin.manifest.main
        if not entry.is_file():
            raise PluginHostError(f"插件入口不存在：{entry}")

        self._plugins[plugin.manifest.name] = plugin
        try:
            await self._request(
                "plugin.load",
                {
                    "pluginId": plugin.manifest.name,
                    "entry": str(entry.resolve()),
                    "manifest": {
                        "name": plugin.manifest.name,
                        "version": plugin.manifest.version,
                        "displayName": plugin.manifest.display_name,
                        "permissions": plugin.manifest.permissions,
                    },
                    "dataDir": str(plugin.data_dir),
                },
                timeout=20,
            )
        except Exception:
            self._plugins.pop(plugin.manifest.name, None)
            raise

    async def unload(self, plugin_id: str) -> None:
        if plugin_id in self._plugins and self.running:
            try:
                await self._request("plugin.unload", {"pluginId": plugin_id}, timeout=5)
            except Exception as exc:
                logger.warning("卸载插件失败 %s：%s", plugin_id, exc)
        self._plugins.pop(plugin_id, None)

    async def emit(self, topic: str, payload: Optional[Dict[str, Any]] = None) -> None:
        if not self.running:
            return
        self._send({"jsonrpc": "2.0", "method": "event.emit",
                    "params": {"topic": topic, "payload": payload or {}}})

    # ------------------------------------------------------------------
    def _send(self, message: Dict[str, Any]) -> None:
        assert self._proc is not None and self._proc.stdin is not None
        self._proc.stdin.write((json.dumps(message, ensure_ascii=False) + "\n").encode("utf-8"))

    async def _request(self, method: str, params: Dict[str, Any], timeout: float) -> Any:
        if not self.running:
            raise PluginHostError("宿主未运行")
        self._next_id += 1
        req_id = self._next_id
        future: asyncio.Future = asyncio.get_running_loop().create_future()
        self._pending[req_id] = future
        self._send({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params})
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        finally:
            self._pending.pop(req_id, None)

    async def _read_stdout(self) -> None:
        assert self._proc is not None and self._proc.stdout is not None
        stream = self._proc.stdout
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
                continue
            await self._dispatch(message)

    async def _read_stderr(self) -> None:
        assert self._proc is not None and self._proc.stderr is not None
        while True:
            raw = await self._proc.stderr.readline()
            if not raw:
                break
            text = raw.decode("utf-8", errors="replace").rstrip()
            if text:
                self._logs.append(text)

    async def _dispatch(self, message: Dict[str, Any]) -> None:
        # 响应
        if "id" in message and ("result" in message or "error" in message):
            future = self._pending.get(message["id"])
            if future and not future.done():
                if message.get("error"):
                    future.set_exception(PluginHostError(message["error"].get("message", "")))
                else:
                    future.set_result(message.get("result"))
            return

        method = message.get("method", "")
        params = message.get("params") or {}

        # 请求（需要回应）
        if "id" in message:
            try:
                result = await self._handle(method, params)
                self._send({"jsonrpc": "2.0", "id": message["id"], "result": result})
            except PluginPermissionError as exc:
                self._logs.append(f"DENIED: {exc}")
                self._send({"jsonrpc": "2.0", "id": message["id"],
                            "error": {"code": -32003, "message": str(exc)}})
            except Exception as exc:
                self._send({"jsonrpc": "2.0", "id": message["id"],
                            "error": {"code": -32603, "message": str(exc)}})
            return

        # 通知
        if method == "plugin.log":
            text = f"[{params.get('pluginId','?')}] {params.get('message','')}"
            self._logs.append(text)
            logger.debug(text)
        elif method == "plugin.error":
            text = f"[{params.get('pluginId','?')}] ERROR {params.get('error','')}"
            self._logs.append(text)
            logger.error(text)

    async def _handle(self, method: str, params: Dict[str, Any]) -> Any:
        if method != "host.call":
            raise PluginHostError(f"未知方法：{method}")

        plugin_id = str(params.get("pluginId", ""))
        api = str(params.get("api", ""))
        args = list(params.get("args") or [])

        plugin = self._plugins.get(plugin_id)
        if plugin is None:
            raise PluginHostError(f"未加载插件：{plugin_id}")

        return await self._capabilities.execute(
            plugin_id, plugin.manifest.permissions, api, args
        )


__all__ = ["PluginHost", "PluginHostError"]
