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

from PySide6.QtCore import QObject, QTimer, Signal, Slot

from vein_launcher.common.events.event_bus import event_bus
from vein_launcher.common.events.events import EventNames
from vein_launcher.presentation.context import AppContext

logger = logging.getLogger(__name__)


def _is_older(current: str, minimum: str) -> bool:
    import re

    def parse(v: str):
        return [int(x) for x in re.findall(r"\d+", v)[:3]] or [0, 0, 0]

    return parse(current) < parse(minimum)



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
    _pick_request = Signal(object)

    def __init__(self, context: AppContext, page, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._ctx = context
        self._page = page
        self._runner = AsyncRunner()
        self._page_ready = False
        self._js_queue: list[str] = []
        self._install_lock = asyncio.Lock()
        self._downloads: dict[str, dict] = {}
        self._mlc_connected = False
        self._mlc_pid: Optional[int] = None
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
            "mods.featured": self._mods_featured,
            "mods.install": self._mods_install,
            "java.detect": self._java_detect,
            "downloads.list": self._downloads_list,
            "mlc.worlds": self._mlc_worlds,
            "app.openDataDir": self._open_data_dir,
            "i18n.get": self._i18n_get,
            "i18n.set": self._i18n_set,
            "announcements.get": self._announcements_get,
            "update.check": self._update_check,
            "mc2.worlds": self._mc2_worlds,
            "mc2.refresh": self._mc2_worlds,
            "app.openUrl": self._open_url,
            "app.pickDirectory": self._pick_directory,
            "minecraft.getDir": self._minecraft_get_dir,
            "minecraft.setDir": self._minecraft_set_dir,
            "mlc.state": self._mlc_state,
            "plugins.state": self._plugins_state,
            "plugins.setEnabled": self._plugins_set_enabled,
            "plugins.reload": self._plugins_reload,
            "plugins.logs": self._plugins_logs,
            "plugins.installExample": self._plugins_install_example,
            "logs.openDir": self._open_log_dir,
        }

        event_bus.subscribe(EventNames.GAME_LOG_UPDATE, self._on_game_log)
        event_bus.subscribe("ui.notify", self._on_ui_notify)
        event_bus.subscribe(EventNames.GAME_RUNNING, self._on_game_running)
        event_bus.subscribe(EventNames.GAME_EXITED, self._on_game_exited)

    # ------------------------------------------------------------------
    def start(self) -> None:
        """启动后台服务（插件宿主等）"""
        self._runner.submit(self._ctx.startup())

    def navigate(self, page: str) -> None:
        """让前端切换到指定页面"""
        self._run_js(f"window.__veinNavigate && window.__veinNavigate({json.dumps(page)})")

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
            params = data.get("params") or {}
            if isinstance(params, dict):
                args = list(params.get("args") or [])
            else:
                args = list(params)
            if not args:
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
        entry = self._downloads.get(task_id)
        if entry is not None:
            entry["done"] = done
            entry["total"] = total
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
        # 延后到事件循环下一拍执行：避免在 QWebChannel 的输入同步调用栈里直接调 WebEngine
        QTimer.singleShot(0, lambda: self._run_js_now(script))

    def _run_js_now(self, script: str) -> None:
        try:
            self._page.runJavaScript(script)
        except RuntimeError:
            logger.debug("页面已销毁，丢弃脚本：%s", script[:80])

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
        task_id = f"{loader}-{version_id}" if loader else str(version_id)
        self._downloads[task_id] = {
            "id": task_id,
            "name": task_id,
            "done": 0,
            "total": 0,
            "active": True,
            "error": None,
        }
        try:
            async with self._install_lock:
                if loader:
                    return await self._ctx.loaders.install(
                        str(loader), str(version_id), str(loader_version) or None
                    )
                return await self._ctx.versions.install(
                    str(version_id),
                    progress=lambda phase, done, total: self._progress(
                        str(version_id), done, total
                    ),
                )
        except Exception as exc:
            entry = self._downloads.get(task_id)
            if entry:
                entry.update(active=False, error=str(exc))
            raise
        finally:
            entry = self._downloads.get(task_id)
            if entry and entry.get("error") is None:
                entry["active"] = False

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

    async def _mods_featured(self, project_type: str = "mod", mc_version: str = "",
                             loader: str = "", limit: int = 24) -> list:
        hits = await self._ctx.modrinth.featured(
            project_type=str(project_type or "mod"),
            game_version=str(mc_version) or None,
            loader=str(loader) or None,
            limit=int(limit),
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
            import shutil
            import tempfile

            workdir = Path(tempfile.mkdtemp(prefix="vein_pack_"))
            archive = workdir / file["name"]
            try:
                await self._ctx.modrinth_download(file["url"], archive, file.get("sha1"))
                return await self._ctx.modpacks.install(archive, str(instance))
            finally:
                shutil.rmtree(workdir, ignore_errors=True)

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
    async def _plugins_state(self) -> dict:
        return self._ctx.plugins.state()

    async def _plugins_set_enabled(self, name: str, enabled: bool = True) -> dict:
        return await self._ctx.plugins.set_enabled(str(name), bool(enabled))

    async def _plugins_reload(self, name: str) -> dict:
        return await self._ctx.plugins.reload(str(name))

    async def _plugins_logs(self, limit: int = 200) -> list:
        return self._ctx.plugins.logs(int(limit))

    async def _plugins_install_example(self, name: str) -> dict:
        return self._ctx.plugins.install_example(str(name))

    async def _downloads_list(self) -> list:
        return list(self._downloads.values())

    async def _i18n_get(self) -> dict:
        from vein_launcher.common.i18n.translator import translator

        return {"lang": translator.current_lang, "languages": translator.languages}

    async def _i18n_set(self, lang: str) -> dict:
        from vein_launcher.common.i18n.translator import translator

        ok = translator.set_language(str(lang))
        translator.save_choice()
        return {"ok": ok, "lang": translator.current_lang}

    async def _pick_directory(self, title: str = "Select folder") -> dict:
        import threading

        holder = {"title": str(title), "result": "", "event": threading.Event()}
        self._pick_request.emit(holder)
        await asyncio.to_thread(holder["event"].wait, 60)
        return {"path": holder.get("result", "")}

    async def _minecraft_get_dir(self) -> dict:
        from vein_launcher.common.utils.path_utils import get_minecraft_dir

        return {"path": str(get_minecraft_dir())}

    async def _minecraft_set_dir(self, path: str = "") -> dict:
        from vein_launcher.common.utils.path_utils import (
            bootstrap_layout,
            get_minecraft_dir,
            set_minecraft_dir,
        )

        target = set_minecraft_dir(str(path) or None)
        bootstrap_layout()
        return {"path": str(get_minecraft_dir()), "ok": target.is_dir()}

    async def _announcements_get(self, force: bool = False) -> dict:
        data = await self._ctx.announcements.fetch(bool(force))
        current = self._ctx.version
        min_version = str(data.get("min_version") or "")
        heavy = [a for a in data.get("announcements", []) if a.get("level") == "heavy"]
        return {
            "version": data.get("version", ""),
            "current": current,
            "announcements": data.get("announcements", []),
            "update": data.get("update", {}),
            "force_update": bool(heavy) or bool(min_version and _is_older(current, min_version)),
            "min_version": min_version,
        }

    async def _update_check(self) -> dict:
        data = await self._ctx.announcements.fetch()
        update = data.get("update") or {}
        return {
            "current": self._ctx.version,
            "latest": update.get("version", ""),
            "url": update.get("url", ""),
            "notes": update.get("notes", ""),
        }

    async def _mc2_worlds(self, instance: str = "") -> list:
        return self._ctx.mc2.list_worlds(str(instance) or None)

    async def _open_url(self, url: str) -> dict:
        import webbrowser

        if not str(url).startswith(("http://", "https://")):
            raise ValueError("仅允许 http(s) 链接")
        webbrowser.open(str(url))
        return {"ok": True}

    async def _mlc_worlds(self, version_id: str = "") -> dict:
        return self._ctx.mlc.world_info(str(version_id))

    async def _open_data_dir(self) -> dict:
        import subprocess

        path = str(self._ctx.data_dir)
        subprocess.Popen(["explorer", path])
        return {"path": path}

    async def _mlc_state(self) -> dict:
        return {
            "connected": self._mlc_connected,
            "pid": self._mlc_pid,
        }

    def _on_game_running(self, pid: int = 0, **_) -> None:
        self._mlc_connected = True
        self._mlc_pid = int(pid) or None

    def _on_game_exited(self, exit_code: int = 0, **_) -> None:
        self._mlc_connected = False
        self._mlc_pid = None

    async def _open_log_dir(self) -> dict:
        import subprocess

        from vein_launcher.common.logging.logger import log_dir

        path = log_dir()
        subprocess.Popen(["explorer", str(path)])
        return {"path": str(path)}

    # ------------------------------------------------------------------
    def shutdown(self, context=None) -> None:
        """先异步释放资源，再停事件循环；避免插件宿主等子进程泄漏"""
        if context is not None:
            try:
                future = asyncio.run_coroutine_threadsafe(context.close(), self._runner.loop)
                future.result(timeout=8)
                logger.info("后端资源已释放")
            except Exception:
                logger.exception("关闭后端服务失败")
        self._runner.shutdown()
