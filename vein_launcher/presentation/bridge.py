"""表现层 - Python ↔ React 通信桥（QWebChannel）

JS 侧：
    window.__bridge.call(requestId, JSON.stringify({method, args}))
Python 完成后回调：
    window.__veinResult(requestId, ok, payload)
进度推送：
    window.__veinProgress(taskId, done, total)
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
from pathlib import Path
from typing import Any, Callable, Optional

from PySide6.QtCore import QObject, Signal, Slot

from vein_launcher.common.events.event_bus import event_bus
from vein_launcher.common.events.events import EventNames
from vein_launcher.presentation.context import AppContext

logger = logging.getLogger(__name__)


class AsyncRunner:
    """后台 asyncio 事件循环"""

    def __init__(self) -> None:
        self.loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run, name="vein-async", daemon=True)
        self._thread.start()

    def _run(self) -> None:
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def submit(self, coro) -> None:
        self.loop.call_soon_threadsafe(self.loop.create_task, coro)

    def shutdown(self) -> None:
        def _stop() -> None:
            for task in asyncio.all_tasks(self.loop):
                task.cancel()
            self.loop.stop()

        try:
            self.loop.call_soon_threadsafe(_stop)
        except RuntimeError:
            pass


class ApiBridge(QObject):
    """暴露给前端的接口"""

    # 线程安全的 JS 执行通道：后台线程 emit，UI 线程执行
    _js_request = Signal(str)

    def __init__(self, context: AppContext, page, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._ctx = context
        self._page = page
        self._runner = AsyncRunner()
        self._page_ready = False
        self._js_queue: list[str] = []
        self._js_request.connect(self._execute_js)
        page.loadFinished.connect(self._on_page_loaded)
        self._handlers: dict[str, Callable[..., Any]] = {
            "app.info": self._app_info,
            "versions.remote": self._versions_remote,
            "versions.info": self._versions_installed,
            "versions.install": self._versions_install,
            "versions.delete": self._versions_delete,
            "launch": self._launch,
            "accounts.list": self._accounts_list,
            "accounts.add": self._accounts_add,
            "accounts.select": self._accounts_select,
            "mods.search": self._mods_search,
            "mods.install": self._mods_install,
            "java.detect": self._java_detect,
        }

        event_bus.subscribe(EventNames.GAME_LOG_UPDATE, self._on_game_log)
        event_bus.subscribe("ui.notify", self._on_ui_notify)

    # ------------------------------------------------------------------
    def start(self) -> None:
        """启动后台服务（插件宿主等）"""
        self._runner.submit(self._ctx.startup())

    def _on_game_log(self, line: str = "", **_) -> None:
        self._run_js(f"window.__veinLog({json.dumps(line, ensure_ascii=False)})")

    def _on_ui_notify(self, title: str = "", message: str = "", **_) -> None:
        self._run_js(
            f"window.__veinNotify({json.dumps(title, ensure_ascii=False)},"
            f"{json.dumps(message, ensure_ascii=False)})"
        )

    # ------------------------------------------------------------------
    @Slot(str, str)
    def call(self, request_id: str, payload: str) -> None:
        try:
            data = json.loads(payload or "{}")
            method = data.get("method", "")
            args = list(data.get("args") or [])
        except json.JSONDecodeError as exc:
            self._fail(request_id, f"参数解析失败：{exc}")
            return

        handler = self._handlers.get(method)
        if handler is None:
            self._fail(request_id, f"未知方法：{method}")
            return

        self._runner.submit(self._run(request_id, handler, args))

    async def _run(self, request_id: str, handler: Callable[..., Any], args: list) -> None:
        method = getattr(handler, "__name__", "call")
        started = time.perf_counter()
        try:
            result = await handler(*args)
            elapsed = (time.perf_counter() - started) * 1000
            logger.debug("bridge %s ok (%.0f ms)", method, elapsed)
            self._ok(request_id, result)
        except Exception as exc:  # 任何异常都回到前端，不吞掉
            elapsed = (time.perf_counter() - started) * 1000
            logger.exception("bridge %s failed (%.0f ms)：%s", method, elapsed, exc)
            self._fail(request_id, str(exc))

    # ------------------------------------------------------------------
    def _ok(self, request_id: str, result: Any) -> None:
        self._run_js(f"window.__veinResult({json.dumps(request_id)}, true, {json.dumps(result, ensure_ascii=False)})")

    def _fail(self, request_id: str, message: str) -> None:
        self._run_js(f"window.__veinResult({json.dumps(request_id)}, false, {json.dumps(message, ensure_ascii=False)})")

    def _progress(self, task_id: str, done: int, total: int) -> None:
        self._run_js(f"window.__veinProgress({json.dumps(task_id)}, {done}, {total})")

    def _run_js(self, script: str) -> None:
        """任意线程可调用；未加载完成时先排队"""
        if not self._page_ready:
            self._js_queue.append(script)
            if len(self._js_queue) > 500:
                self._js_queue.pop(0)
            return
        self._js_request.emit(script)

    def _execute_js(self, script: str) -> None:
        self._page.runJavaScript(script)

    def _on_page_loaded(self, ok: bool) -> None:
        self._page_ready = bool(ok)
        if not ok:
            logger.warning("页面加载失败，JS 队列保留 %d 条", len(self._js_queue))
            return
        logger.info("前端就绪，冲刷 %d 条待执行脚本", len(self._js_queue))
        queued, self._js_queue = self._js_queue, []
        for script in queued:
            self._js_request.emit(script)

    # ------------------------------------------------------------------
    # 处理方法
    # ------------------------------------------------------------------
    async def _app_info(self) -> dict:
        return {"version": self._ctx.version, "dataDir": str(self._ctx.data_dir)}

    async def _versions_remote(self, limit: int = 80) -> list:
        items = await self._ctx.versions_api.fetch_version_list()
        releases = [v for v in items if v.get("type") == "release"]
        pool = releases or items
        return [
            {"id": v.get("id"), "type": v.get("type"), "release_time": (v.get("releaseTime") or "")[:10]}
            for v in pool[: int(limit)]
        ]

    async def _versions_installed(self) -> list:
        return self._ctx.versions.list_installed()

    async def _versions_install(
        self, version_id: str, loader: str = "", loader_version: str = ""
    ) -> dict:
        if loader:
            return await self._ctx.loaders.install(
                str(loader), str(version_id), str(loader_version) or None
            )
        return await self._ctx.versions.install(
            str(version_id),
            progress=lambda phase, done, total: self._progress(str(version_id), done, total),
        )

    async def _versions_delete(self, version_id: str) -> dict:
        return {"deleted": self._ctx.versions.delete(str(version_id))}

    async def _launch(self, version_id: str, username: str = "Player") -> dict:
        pid = await self._ctx.launcher.launch(str(version_id), str(username))
        return {"pid": pid}

    async def _accounts_list(self) -> list:
        return self._ctx.accounts.list()

    async def _accounts_add(self, username: str) -> dict:
        return self._ctx.accounts.add_offline(str(username))

    async def _accounts_select(self, account_id: str) -> dict:
        return {"ok": self._ctx.accounts.select(str(account_id))}

    async def _mods_search(self, query: str, project_type: str, mc_version: str, loader: str) -> list:
        hits = await self._ctx.modrinth.search(
            str(query),
            project_type=str(project_type or "mod"),
            game_version=str(mc_version) or None,
            loader=str(loader) or None,
        )
        return [self._ctx.modrinth.summary(hit) for hit in hits]

    async def _mods_install(self, slug: str, instance: str, project_type: str, loader: str) -> dict:
        versions = await self._ctx.modrinth.versions(str(slug), loader=str(loader) or None)
        if not versions:
            raise RuntimeError("没有可下载的文件")
        file = self._ctx.modrinth.file_of(versions[0])
        if not file:
            raise RuntimeError("文件信息缺失")

        if str(project_type) == "modpack":
            import tempfile

            archive = Path(tempfile.mkdtemp(prefix="vein_pack_")) / file["name"]
            await self._ctx.modrinth_download(file["url"], archive, file.get("sha1"))
            return await self._ctx.modpacks.install(archive, str(instance))

        target_dir = self._ctx.instance_sub_dir(str(instance), str(project_type))
        target_dir.mkdir(parents=True, exist_ok=True)
        await self._ctx.modrinth_download(
            file["url"], target_dir / file["name"], file.get("sha1")
        )
        return {"installed": 1, "path": str(target_dir / file["name"])}

    async def _java_detect(self) -> list:
        runtimes = await self._ctx.detector.detect()
        return [
            {"path": str(rt.path), "major": rt.major, "version": rt.version, "vendor": rt.vendor}
            for rt in runtimes
        ]

    # ------------------------------------------------------------------
    def shutdown(self) -> None:
        self._runner.shutdown()
