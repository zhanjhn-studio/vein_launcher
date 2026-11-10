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
from vein_launcher.common.utils.console import hidden_kwargs, hidden_popen_kwargs
from vein_launcher.presentation.context import AppContext

logger = logging.getLogger(__name__)


def _is_older(current: str, minimum: str) -> bool:
    import re

    def parse(v: str):
        return [int(x) for x in re.findall(r"\d+", v)[:3]] or [0, 0, 0]

    return parse(current) < parse(minimum)


# ----------------------------------------------------------------------
# 界面偏好：自定义壁纸的媒体类型判定与前端载荷
# ----------------------------------------------------------------------
WALLPAPER_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".avif"}
WALLPAPER_VIDEO_EXT = {".mp4", ".webm", ".mov", ".m4v", ".ogv"}


def _wallpaper_kind(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in WALLPAPER_VIDEO_EXT:
        return "video"
    if ext in WALLPAPER_IMAGE_EXT:
        return "image"
    return ""


def _wallpaper_payload(raw: str) -> Optional[dict]:
    """把配置里的壁纸路径转成前端可直接用的 file:// URL；无效/已删除时返回 None"""
    if not raw:
        return None
    try:
        path = Path(raw).expanduser().resolve()
    except OSError:
        return None
    if not path.is_file():
        return None
    kind = _wallpaper_kind(path)
    if not kind:
        return None
    return {"url": path.as_uri(), "kind": kind, "name": path.name, "path": str(path)}


def _normalize_hex(raw: str) -> str:
    """把用户输入的主色收敛成 #rrggbb；空串 / 非法值返回 ""（回退内置配色）"""
    value = (raw or "").strip().lower()
    if not value:
        return ""
    if not value.startswith("#"):
        value = "#" + value
    if len(value) == 4:  # #abc → #aabbcc
        value = "#" + "".join(ch * 2 for ch in value[1:])
    if len(value) != 7:
        return ""
    try:
        int(value[1:], 16)
    except ValueError:
        return ""
    return value


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
    _clip_request = Signal(str, object)
    _hotkey_request = Signal(object)

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
        # 指令速查窗的数据源（前端 tools.syncPalette 推过来）
        self.palette_entries: list[dict] = []
        self.palette_nodes: list[str] = []
        self._js_request.connect(self._execute_js)
        page.loadFinished.connect(self._on_page_loaded)
        self._handlers: dict[str, Callable[..., Any]] = {
            "app.info": self._app_info,
            "versions.remote": self._versions_remote,
            "versions.info": self._versions_installed,
            "versions.install": self._versions_install,
            "versions.delete": self._versions_delete,
            "versions.files": self._versions_files,
            "versions.fileDelete": self._versions_file_delete,
            "versions.openFolder": self._versions_open_folder,
            "launch": self._launch,
            "game.running": self._game_running,
            "game.kill": self._game_kill,
            "game.windows": self._game_windows,
            "game.focus": self._game_focus,
            "game.command": self._game_command,
            "accounts.list": self._accounts_list,
            "accounts.add": self._accounts_add,
            "accounts.select": self._accounts_select,
            "mods.search": self._mods_search,
            "mods.featured": self._mods_featured,
            "mods.versions": self._mods_versions,
            "mods.install": self._mods_install,
            "java.detect": self._java_detect,
            "java.ensure": self._java_ensure,
            "java.resolve": self._java_resolve,
            "downloads.list": self._downloads_list,
            "downloads.remove": self._downloads_remove,
            "mlc.worlds": self._mlc_worlds,
            "app.openDataDir": self._open_data_dir,
            "i18n.get": self._i18n_get,
            "i18n.set": self._i18n_set,
            "announcements.get": self._announcements_get,
            "update.check": self._update_check,
            "mc2.worlds": self._mc2_worlds,
            "mc2.refresh": self._mc2_worlds,
            "mc2.scan": self._mc2_scan,
            "app.openUrl": self._open_url,
            "app.pickDirectory": self._pick_directory,
            "app.pickFile": self._pick_file,
            "optifine.install": self._optifine_install,
            "accounts.remove": self._accounts_remove,
            "accounts.msClientId": self._ms_client_id,
            "accounts.msAuthority": self._ms_authority,
            "accounts.msStart": self._ms_start,
            "accounts.msLogin": self._ms_login,
            "accounts.littleSkin": self._littleskin_login,
            "onboarding.complete": self._onboarding_complete,
            "skins.list": self._skins_list,
            "skins.import": self._skins_import,
            "skins.clear": self._skins_clear,
            "skins.remote": self._skins_remote,
            "skins.library": self._skins_library,
            "skins.download": self._skins_download,
            "instances.contents": self._instance_contents,
            "instances.toggle": self._instance_toggle,
            "instances.deleteFile": self._instance_delete_file,
            "instances.worlds": self._instance_worlds,
            "instances.deleteWorld": self._instance_delete_world,
            "update.latest": self._update_latest,
            "update.download": self._update_download,
            "update.install": self._update_install,
            "ui.prefs": self._ui_prefs,
            "ui.setPrefs": self._ui_set_prefs,
            "ui.importWallpaper": self._ui_import_wallpaper,
            "tools.copy": self._tools_copy,
            "tools.bindHotkeys": self._tools_bind_hotkeys,
            "tools.syncPalette": self._tools_sync_palette,
            "tools.config": self._tools_config,
            "tools.saveConfig": self._tools_save_config,
            "minecraft.getDir": self._minecraft_get_dir,
            "minecraft.setDir": self._minecraft_set_dir,
            "mlc.state": self._mlc_state,
            "mlc.setEnabled": self._mlc_set_enabled,
            "mlc.agentState": self._mlc_agent_state,
            "mlc.agentChat": self._mlc_agent_chat,
            "mlc.watchStart": self._mlc_watch_start,
            "mlc.watchStop": self._mlc_watch_stop,
            "mlc.player": self._mlc_player,
            "mlc.worldDetail": self._mlc_world_detail,
            "mlc.modLoad": self._mlc_mod_load,
            "plugins.state": self._plugins_state,
            "plugins.setEnabled": self._plugins_set_enabled,
            "plugins.reload": self._plugins_reload,
            "plugins.logs": self._plugins_logs,
            "plugins.uiAction": self._plugins_ui_action,
            "plugins.installExample": self._plugins_install_example,
            "plugins.nodeStatus": self._plugins_node_status,
            "plugins.installNode": self._plugins_install_node,
            "logs.openDir": self._open_log_dir,
        }

        event_bus.subscribe(EventNames.GAME_LOG_UPDATE, self._on_game_log)
        event_bus.subscribe("ui.notify", self._on_ui_notify)
        event_bus.subscribe(EventNames.GAME_RUNNING, self._on_game_running)
        event_bus.subscribe(EventNames.GAME_EXITED, self._on_game_exited)
        event_bus.subscribe("plugin.ui", self._on_plugin_ui)
        for agent_event in ("game.enter", "game.leave", "player.dimension", "player.death"):
            event_bus.subscribe(f"mlc.agent.{agent_event}", self._make_mlc_agent_handler(agent_event))

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
        accounts = self._ctx.accounts.list()
        return {
            "version": self._ctx.version,
            "dataDir": str(self._ctx.data_dir),
            "accountCount": len(accounts),
            "firstRun": not accounts and not self._onboarding_done(),
        }

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

    async def _versions_files(self, instance: str, sub: str = "") -> list:
        return self._ctx.versions.list_files(str(instance), str(sub or ""))

    async def _versions_file_delete(self, instance: str, rel: str) -> dict:
        return {"deleted": self._ctx.versions.delete_file(str(instance), str(rel))}

    async def _versions_open_folder(self, instance: str) -> dict:
        import subprocess

        from vein_launcher.common.utils.path_utils import get_version_dir

        path = str(get_version_dir(str(instance)))
        subprocess.Popen(["explorer", path], **hidden_popen_kwargs())
        return {"path": path}

    async def _versions_install(
        self, version_id: str, loader: str = "", loader_version: str = "",
        custom_name: str = "",
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
                    result = await self._ctx.loaders.install(
                        str(loader),
                        str(version_id),
                        str(loader_version) or None,
                        progress=lambda phase, done, total: self._progress(
                            task_id, done, total
                        ),
                    )
                    source = result.get("version_id", f"{loader}-{version_id}")
                else:
                    result = await self._ctx.versions.install(
                        str(version_id),
                        progress=lambda phase, done, total: self._progress(
                            str(version_id), done, total
                        ),
                    )
                    source = str(version_id)

                self._run_js("window.__veinInstalled && window.__veinInstalled()")
                if custom_name:
                    target = await self._ctx.versions.copy_instance(source, str(custom_name))
                    result = {**result, "version_id": target, "custom": True}
                return result
        except BaseException as exc:
            entry = self._downloads.get(task_id)
            if entry:
                message = "已取消" if isinstance(exc, asyncio.CancelledError) else str(exc)
                entry.update(active=False, error=message)
            raise
        finally:
            entry = self._downloads.get(task_id)
            if entry and entry.get("error") is None:
                entry["done"] = max(int(entry.get("done") or 0), int(entry.get("total") or 1))
                entry["total"] = entry["done"]
            if entry and entry.get("error") is None:
                entry["active"] = False

    async def _versions_delete(self, version_id: str) -> dict:
        return {"deleted": self._ctx.versions.delete(str(version_id))}

    async def _java_ensure(self, major: int = 17) -> dict:
        return await self._ctx.java.ensure(int(major), progress=lambda phase, done, total: None)

    async def _java_resolve(self, major: int = 17) -> dict:
        return await self._ctx.java.ensure(int(major), download=False)

    async def _launch(self, version_id: str, username: str = "Player") -> dict:
        merged = await self._ctx.versions.merged(str(version_id))
        major = int((merged.get("javaVersion") or {}).get("majorVersion", 8))
        java_path = None
        try:
            ensured = await self._ctx.java.ensure(major)
            java_path = ensured.get("path")
            logger.info("启动使用 Java %s：%s", major, java_path)
        except Exception as exc:
            logger.warning("Java 自动匹配失败，回退系统探测：%s", exc)
        access_token = None
        auth_uuid = None
        user_type = "legacy"
        extra_jvm: list[str] = []
        selected = self._ctx.accounts.current()
        if selected is not None:
            kind = getattr(selected, "account_type", "offline")
            if kind == "microsoft":
                token = await self._ms_ensure_token(selected)
                if token and token.get("access_token"):
                    access_token = token["access_token"]
                    auth_uuid = token.get("uuid") or None
                    user_type = "msa"
                    logger.info("使用正版账号启动：%s", selected.username)
            elif kind == "littleskin":
                access_token = getattr(selected, "access_token", None) or None
                auth_uuid = getattr(selected, "uuid", None) or None
                user_type = "mojang"
                server = getattr(selected, "server", "") or ""
                jar = await self._ensure_authlib_injector()
                if jar:
                    extra_jvm = [f"-javaagent:{jar}={server}"]
                logger.info("使用 LittleSkin 账号启动：%s（%s）", selected.username, server)
            else:
                logger.info("使用离线账号启动：%s", selected.username)

        pid = await self._ctx.launcher.launch(
            str(version_id),
            str(username),
            java_path=java_path,
            access_token=access_token,
            auth_uuid=auth_uuid,
            user_type=user_type,
            extra_jvm=extra_jvm,
        )
        return {
            "pid": pid,
            "java": java_path,
            "online": bool(access_token),
            "user_type": user_type,
        }

    async def _accounts_list(self) -> list:
        return self._ctx.accounts.list()

    async def _accounts_add(self, username: str) -> dict:
        return self._ctx.accounts.add_offline(str(username))

    async def _accounts_select(self, account_id: str) -> dict:
        ok = self._ctx.accounts.select(str(account_id))
        self._run_js("window.__veinAccountsChanged && window.__veinAccountsChanged()")
        return {"ok": ok}

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

    async def _mods_versions(self, slug: str, mc_version: str = "", loader: str = "") -> list:
        versions = await self._ctx.modrinth.versions(
            str(slug), game_version=str(mc_version) or None, loader=str(loader) or None
        )
        rows = []
        for item in versions:
            file = self._ctx.modrinth.file_of(item)
            if not file:
                continue
            rows.append(
                {
                    "id": item.get("id", ""),
                    "name": item.get("name", ""),
                    "version_number": item.get("version_number", ""),
                    "game_versions": item.get("game_versions", []),
                    "loaders": item.get("loaders", []),
                    "date": item.get("date_published", ""),
                    "downloads": item.get("downloads", 0),
                    "file": file,
                }
            )
        return rows

    async def _mods_install(self, slug: str, instance: str, project_type: str, loader: str, version_id: str = "") -> dict:
        import re as _re

        instance_id = str(instance)
        has_loader = any(k in instance_id.lower() for k in ("fabric", "forge", "quilt", "neoforge"))
        if str(project_type) == "mod" and not has_loader:
            mc_version = _re.sub(r"^(fabric|forge|quilt|neoforge)-", "", instance_id, flags=_re.I)
            return {
                "needsLoader": True,
                "instance": instance_id,
                "mcVersion": mc_version,
                "suggestedLoader": "fabric",
            }

        instance_loader = ""
        for key in ("fabric", "quilt", "neoforge", "forge"):
            if key in instance_id.lower():
                instance_loader = key
                break
        effective_loader = instance_loader or str(loader) or None
        versions = await self._ctx.modrinth.versions(str(slug), loader=effective_loader)
        if version_id:
            picked = next((v for v in versions if str(v.get("id")) == str(version_id)), None)
            versions = [picked] if picked else []
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
            task_id = f"pack-{slug}"
            self._downloads[task_id] = {
                "id": task_id, "name": str(slug), "done": 0, "total": 0, "active": True, "error": None,
            }
            try:
                await self._ctx.modrinth_download(
                    file["url"], archive, file.get("sha1"),
                    progress=lambda done, total: self._progress(task_id, done, total),
                )
                return await self._ctx.modpacks.install(
                    archive,
                    str(instance),
                    progress=lambda done, total: self._progress(task_id, done, total),
                )
            except Exception as exc:
                entry = self._downloads.get(task_id)
                if entry:
                    entry.update(active=False, error=str(exc))
                raise
            finally:
                entry = self._downloads.get(task_id)
                if entry and entry.get("error") is None:
                    entry.update(active=False)
                shutil.rmtree(workdir, ignore_errors=True)

        target_dir = self._ctx.instance_sub_dir(str(instance), str(project_type))
        target_dir.mkdir(parents=True, exist_ok=True)
        task_id = f"mod-{slug}"
        self._downloads[task_id] = {
            "id": task_id,
            "name": str(slug),
            "done": 0,
            "total": 0,
            "active": True,
            "error": None,
        }
        try:
            await self._ctx.modrinth_download(
                file["url"],
                target_dir / file["name"],
                file.get("sha1"),
                progress=lambda done, total: self._progress(task_id, done, total),
            )
        finally:
            entry = self._downloads.get(task_id)
            if entry:
                entry.update(active=False)
        return {"installed": 1, "path": str(target_dir / file["name"])}

    async def _java_detect(self, refresh: bool = False) -> list:
        # 启动时已预热过检测结果；一分钟内直接复用，避免每次开设置页都扫一遍磁盘
        cached = self._ctx.java_runtimes
        fresh = time.time() - getattr(self._ctx, "java_checked_at", 0) < 60
        if refresh or not cached or not fresh:
            runtimes = await self._ctx.detector.detect()
            self._ctx.java_runtimes = runtimes
            self._ctx.java_checked_at = time.time()
        else:
            runtimes = cached
        return [
            {"path": str(rt.path), "major": rt.major, "version": rt.version, "vendor": rt.vendor}
            for rt in runtimes
        ]

    # ------------------------------------------------------------------ 运行中的游戏
    async def _game_running(self) -> dict:
        from vein_launcher.application.services.game_registry import game_registry

        games = await asyncio.to_thread(game_registry.list)
        return {"games": games, "count": len(games)}

    async def _game_windows(self) -> dict:
        from vein_launcher.infrastructure.process.game_input import list_windows

        return {"windows": await asyncio.to_thread(list_windows, "Minecraft")}

    async def _game_focus(self, pid: int = 0) -> dict:
        from vein_launcher.infrastructure.process import game_input

        def run() -> dict:
            windows = game_input.list_windows("Minecraft")
            target = next((w for w in windows if int(pid) == w["pid"]), None) if pid else (windows[0] if windows else None)
            if not target:
                return {"focused": False, "reason": "no minecraft window"}
            return {"focused": game_input.focus_window(int(target["hwnd"])), "hwnd": int(target["hwnd"])}

        return await asyncio.to_thread(run)

    async def _game_command(self, command: str = "", pid: int = 0) -> dict:
        """原版通道：切到游戏窗口，用键盘输入一条聊天指令（受 MLC 总开关控制）"""
        if not self._ctx.mlc.enabled:
            raise RuntimeError("MLC 总开关未开启：请先到 MLC 页打开总开关（MLC is turned off）")
        from vein_launcher.infrastructure.process import game_input

        def run() -> dict:
            windows = game_input.list_windows("Minecraft")
            if not windows:
                raise RuntimeError("没有找到 Minecraft 窗口，请先在游戏里进入世界")
            target = next((w for w in windows if int(pid) == w["pid"]), None) if pid else windows[0]
            return game_input.send_chat_command(str(command), int(target["hwnd"]))

        return await asyncio.to_thread(run)

    async def _game_kill(self, pid: int = 0) -> dict:
        from vein_launcher.application.services.game_registry import game_registry

        return await asyncio.to_thread(game_registry.kill, int(pid))

    # ------------------------------------------------------------------
    async def _plugins_node_status(self) -> dict:
        return self._ctx.plugins.node_status()

    async def _plugins_install_node(self) -> dict:
        self._downloads["node-install"] = {
            "id": "node-install", "name": "Node.js", "done": 0, "total": 0, "active": True, "error": None,
        }
        try:
            result = await self._ctx.plugins.install_node(
                progress=lambda done, total: self._progress("node-install", done, total)
            )
        finally:
            entry = self._downloads.get("node-install")
            if entry:
                entry.update(active=False)
        return result

    async def _plugins_state(self) -> dict:
        return self._ctx.plugins.state()

    async def _plugins_set_enabled(self, name: str, enabled: bool = True) -> dict:
        return await self._ctx.plugins.set_enabled(str(name), bool(enabled))

    async def _plugins_reload(self, name: str) -> dict:
        return await self._ctx.plugins.reload(str(name))

    async def _plugins_ui_action(self, plugin_id: str, action: str, payload: Any = None) -> dict:
        if self._ctx.plugins.host.running:
            await self._ctx.plugins.host.emit(
                "plugin.action",
                {"pluginId": str(plugin_id), "action": str(action), "payload": payload},
            )
        return {"ok": True}

    async def _plugins_logs(self, limit: int = 200) -> list:
        return self._ctx.plugins.logs(int(limit))

    async def _plugins_install_example(self, name: str) -> dict:
        return self._ctx.plugins.install_example(str(name))

    async def _downloads_remove(self, task_id: str) -> dict:
        removed = self._downloads.pop(str(task_id), None)
        return {"removed": bool(removed), "id": str(task_id)}

    async def _downloads_list(self) -> list:
        # 只保留最近 20 条，避免长期使用后列表无限增长
        items = list(self._downloads.values())
        return items[-20:]

    async def _i18n_get(self) -> dict:
        from vein_launcher.common.i18n.translator import translator

        return {"lang": translator.current_lang, "languages": translator.languages}

    async def _i18n_set(self, lang: str) -> dict:
        from vein_launcher.common.config.settings import settings_manager
        from vein_launcher.common.i18n.translator import translator

        ok = translator.set_language(str(lang))
        translator.save_choice()
        # 同步写回 config.json，避免 language.json 与 ui.language 各说各话
        try:
            ui = settings_manager.get().ui
            if getattr(ui, "language", "") != translator.current_lang:
                ui.language = translator.current_lang
                settings_manager.save()
        except Exception:  # noqa: BLE001
            pass
        return {"ok": ok, "lang": translator.current_lang}

    async def _pick_directory(self, title: str = "Select folder") -> dict:
        import threading

        holder = {"title": str(title), "result": "", "event": threading.Event()}
        self._pick_request.emit(holder)
        await asyncio.to_thread(holder["event"].wait, 60)
        return {"path": holder.get("result", "")}

    async def _pick_file(self, title: str = "Select file", filters: str = "") -> dict:
        import threading

        holder = {
            "title": str(title),
            "result": "",
            "event": threading.Event(),
            "mode": "file",
            "filters": filters or "All files (*.*)",
        }
        self._pick_request.emit(holder)
        await asyncio.to_thread(holder["event"].wait, 120)
        return {"path": holder.get("result", "")}

    async def _optifine_install(self, installer: str) -> dict:
        import asyncio as _asyncio

        from vein_launcher.common.utils.path_utils import get_minecraft_dir

        jar = Path(str(installer))
        if not jar.is_file():
            raise ValueError("Installer not found")
        ensured = await self._ctx.java.ensure(17)
        java = ensured.get("path")
        if not java:
            raise RuntimeError("Java not available")
        proc = await _asyncio.create_subprocess_exec(
            java,
            "-jar",
            str(jar),
            cwd=str(get_minecraft_dir()),
            stdout=_asyncio.subprocess.DEVNULL,
            stderr=_asyncio.subprocess.PIPE,
            **hidden_kwargs(),
        )
        _, err = await proc.communicate()
        logger.info("OptiFine installer exit=%s", proc.returncode)
        if proc.returncode != 0:
            message = (err or b"").decode("utf-8", "replace")[-400:]
            raise RuntimeError(f"OptiFine installer failed: {message}")
        return {"ok": True, "versions": self._ctx.versions.list_installed()}

    async def _accounts_remove(self, account_id: str) -> dict:
        return {"ok": self._ctx.accounts.remove(str(account_id))}

    def _ms_config(self) -> Path:
        from vein_launcher.common.utils.path_utils import get_config_dir

        return get_config_dir() / "ms_client_id.json"

    def _ms_read_config(self) -> dict:
        import json as _json

        try:
            data = _json.loads(self._ms_config().read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _ms_read_client_id(self) -> str:
        return str(self._ms_read_config().get("client_id", ""))

    def _ms_apply_authority(self) -> str:
        from vein_launcher.infrastructure.network import microsoft_auth

        authority = str(self._ms_read_config().get("authority", "") or "common")
        microsoft_auth.AUTHORITY = authority
        return authority

    async def _ms_client_id(self, client_id: str = "") -> dict:
        import json as _json

        if client_id:
            self._ms_config().parent.mkdir(parents=True, exist_ok=True)
            self._ms_config().write_text(
                _json.dumps({"client_id": str(client_id)}, indent=2), encoding="utf-8"
            )
        return {"client_id": self._ms_read_client_id()}

    async def _ms_authority(self, authority: str = "") -> dict:
        import json as _json

        from vein_launcher.infrastructure.network import microsoft_auth

        if authority:
            data = self._ms_read_config()
            data["authority"] = str(authority).strip() or "common"
            self._ms_config().parent.mkdir(parents=True, exist_ok=True)
            self._ms_config().write_text(
                _json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        return {"authority": self._ms_apply_authority()}

    async def _ms_start(self) -> dict:
        from vein_launcher.infrastructure.network import microsoft_auth

        self._ms_apply_authority()
        info = await microsoft_auth.start_device_code(self._ms_read_client_id())
        return {
            "device_code": info.get("device_code", ""),
            "user_code": info.get("user_code", ""),
            "verification_uri": info.get("verification_uri", ""),
            "expires_in": info.get("expires_in", 0),
        }

    async def _ms_login(self, device_code: str) -> dict:
        from vein_launcher.infrastructure.network import microsoft_auth

        self._ms_apply_authority()
        profile = await microsoft_auth.login_with_device_code(
            self._ms_read_client_id(), str(device_code)
        )
        return self._ctx.accounts.add_microsoft(profile)

    async def _littleskin_login(self, server: str = "", email: str = "", password: str = "") -> dict:
        """LittleSkin / 通用 Yggdrasil 皮肤站登录"""
        from vein_launcher.infrastructure.network import littleskin

        session = await littleskin.authenticate(
            server or littleskin.DEFAULT_SERVER, str(email), str(password)
        )
        profile = await littleskin.profile(session["server"], session["access_token"])
        skins = (profile or {}).get("skins") or []
        if skins and isinstance(skins[0], dict):
            variant = str(skins[0].get("variant") or "").lower()
            if variant:
                session["skin_model"] = variant
        return self._ctx.accounts.add_littleskin(session)

    def _onboarding_file(self) -> Path:
        from vein_launcher.common.utils.path_utils import get_config_dir

        return get_config_dir() / "onboarding.json"

    def _onboarding_done(self) -> bool:
        try:
            data = json.loads(self._onboarding_file().read_text(encoding="utf-8"))
            return bool(data.get("completed"))
        except Exception:
            return False

    async def _onboarding_complete(self, consent: bool = False) -> dict:
        path = self._onboarding_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {"completed": True, "consent": bool(consent), "at": int(time.time())},
                indent=2,
            ),
            encoding="utf-8",
        )
        return {"ok": True}

    async def _ms_ensure_token(self, account) -> Optional[dict]:
        """返回可用的 Minecraft 会话令牌；过期前用 refresh_token 自动续期"""
        from vein_launcher.domain.models.account import token_needs_refresh
        from vein_launcher.infrastructure.network import microsoft_auth

        cached = (
            {"access_token": account.mc_access_token, "uuid": account.uuid or ""}
            if getattr(account, "mc_access_token", None)
            else None
        )
        if cached and not token_needs_refresh(getattr(account, "mc_expires_at", None)):
            return cached

        refresh_token = getattr(account, "refresh_token", "") or ""
        if not refresh_token:
            logger.warning("正版账号缺少 refresh token，只能使用现有令牌")
            return cached
        try:
            self._ms_apply_authority()
            session = await microsoft_auth.refresh_session(
                self._ms_read_client_id(), refresh_token
            )
            self._ctx.accounts.update_ms_session(account.account_id, session)
            logger.info("正版令牌已续期：%s", account.username)
            return {
                "access_token": session.get("access_token", ""),
                "uuid": session.get("uuid") or account.uuid or "",
            }
        except Exception as exc:
            logger.warning("正版令牌续期失败（继续尝试现有令牌）：%s", exc)
            return cached

    async def _ensure_authlib_injector(self) -> Optional[str]:
        """确保 authlib-injector.jar 存在：皮肤站账号进游戏必需"""
        from vein_launcher.infrastructure.network.authlib import ensure_authlib_injector

        jar = await ensure_authlib_injector()
        return str(jar) if jar else None

    async def _skins_library(self, page: int = 1, keyword: str = "") -> dict:
        """LittleSkin 公开皮肤库列表"""
        from vein_launcher.infrastructure.network import littleskin

        try:
            return await littleskin.skin_library(int(page), str(keyword))
        except Exception as exc:
            logger.warning("皮肤库获取失败：%s", exc)
            return {"page": int(page), "items": [], "has_more": False, "error": str(exc)}

    async def _skins_download(self, account_id: str, tid: int, model: str = "classic") -> dict:
        """从皮肤库下载一张皮肤并保存到指定账号"""
        from vein_launcher.infrastructure.network import littleskin

        try:
            data = await littleskin.download_skin(int(tid))
            state = self._ctx.skins.apply_bytes(
                str(account_id), data, model=str(model), source=f"littleskin:{tid}"
            )
            return {"ok": True, "skin": state}
        except Exception as exc:
            logger.warning("皮肤下载失败 tid=%s：%s", tid, exc)
            return {"ok": False, "error": str(exc)}

    async def _instance_contents(self, version_id: str) -> dict:
        return self._ctx.instances.list_contents(str(version_id))

    async def _update_latest(self) -> dict:
        try:
            return await self._ctx.update.latest()
        except Exception as exc:
            logger.warning("检查更新失败：%s", exc)
            return {"available": False, "current": self._ctx.version, "error": str(exc)}

    async def _update_download(self, url: str, name: str) -> dict:
        path = await self._ctx.update.download(
            str(url), str(name), progress=lambda done, total: self._progress("update", done, total)
        )
        return {"path": str(path), "size": path.stat().st_size}

    async def _update_install(self, path: str) -> dict:
        return await asyncio.to_thread(self._ctx.update.install, str(path))

    @staticmethod
    def _ui_config():
        from vein_launcher.common.config.settings import settings_manager

        return settings_manager.get().ui

    async def _ui_prefs(self) -> dict:
        ui = self._ui_config()
        return {
            "compactMode": bool(getattr(ui, "compact_mode", False)),
            "idleSeconds": int(getattr(ui, "idle_seconds", 60) or 0),
            "wallpaper": _wallpaper_payload(getattr(ui, "wallpaper", "")),
            "accent": str(getattr(ui, "accent", "") or ""),
        }

    async def _ui_set_prefs(
        self,
        compact_mode: Any = None,
        idle_seconds: Any = None,
        clear_wallpaper: bool = False,
        wallpaper: str = "",
        accent: Any = None,
    ) -> dict:
        from vein_launcher.common.config.settings import settings_manager

        manager = settings_manager
        ui = manager.get().ui
        if compact_mode is not None:
            ui.compact_mode = bool(compact_mode)
        if idle_seconds is not None:
            try:
                seconds = int(idle_seconds)
            except (TypeError, ValueError):
                seconds = 60
            ui.idle_seconds = 0 if seconds <= 0 else max(5, min(3600, seconds))
        if accent is not None:
            ui.accent = _normalize_hex(str(accent))
        if clear_wallpaper:
            ui.wallpaper = ""
        elif wallpaper:
            ui.wallpaper = str(Path(str(wallpaper)).expanduser())
        manager.save()
        return await self._ui_prefs()

    async def _ui_import_wallpaper(self) -> dict:
        """弹出文件选择框，把壁纸复制进数据目录后持久化"""
        import shutil

        from vein_launcher.common.config.settings import settings_manager
        from vein_launcher.common.utils.path_utils import get_config_dir

        picked = await self._pick_file(
            "Select wallpaper",
            "Media (*.png *.jpg *.jpeg *.webp *.gif *.bmp *.avif *.mp4 *.webm *.mov *.m4v);;"
            "Images (*.png *.jpg *.jpeg *.webp *.gif *.bmp *.avif);;"
            "Videos (*.mp4 *.webm *.mov *.m4v);;All files (*.*)",
        )
        source = str(picked.get("path") or "")
        if not source:
            prefs = await self._ui_prefs()
            prefs["cancelled"] = True
            return prefs

        src = Path(source)
        kind = _wallpaper_kind(src)
        if not kind:
            raise ValueError("Unsupported wallpaper type")

        target_dir = get_config_dir() / "wallpapers"
        target_dir.mkdir(parents=True, exist_ok=True)
        for stale in target_dir.glob("wallpaper.*"):
            try:
                stale.unlink()
            except OSError:
                logger.warning("旧壁纸清理失败：%s", stale)
        target = target_dir / f"wallpaper{src.suffix.lower()}"
        shutil.copy2(src, target)

        settings_manager.get().ui.wallpaper = str(target)
        settings_manager.save()
        logger.info("自定义壁纸已导入：%s", target)
        return await self._ui_prefs()

    # ------------------------------------------------------------------
    # 工具页：复制指令 / 绑定全局热键
    # ------------------------------------------------------------------
    async def _tools_copy(self, text: str = "") -> dict:
        """把指令写进系统剪贴板（Qt 剪贴板只能在 UI 线程操作，这里转发过去）"""
        payload = str(text or "")
        if not payload:
            raise ValueError("要复制的内容为空")
        holder = {"text": payload, "ok": False, "event": threading.Event()}
        self._clip_request.emit(payload, holder)
        if not holder["event"].wait(2.0):
            raise RuntimeError("剪贴板操作超时")
        if not holder["ok"]:
            raise RuntimeError("写入剪贴板失败")
        return {"ok": True, "length": len(payload), "text": payload}

    async def _tools_bind_hotkeys(
        self, entries: Any = None, palette_key: Any = None
    ) -> dict:
        """把 [{slot, text, title}] 注册成 Ctrl+Alt+<slot> 全局热键，同时应用小窗热键"""
        payload = entries if isinstance(entries, list) else []
        holder: dict = {
            "entries": payload,
            "palette_key": palette_key,
            "result": None,
            "event": threading.Event(),
        }
        self._hotkey_request.emit(holder)
        if not holder["event"].wait(3.0):
            return {"ok": False, "error": "热键注册超时", "bound": [], "failed": []}
        return holder["result"] or {
            "ok": False,
            "error": "热键注册失败",
            "bound": [],
            "failed": [],
        }

    # ------------------------------------------------------------------
    # 工具页：常用指令配置（自定义指令 + 小窗热键）
    # ------------------------------------------------------------------
    @staticmethod
    def _tools_config_path():
        from vein_launcher.common.utils.path_utils import get_config_dir

        return get_config_dir() / "tools.json"

    def _read_tools_config(self) -> dict:
        data: dict = {"favorites": [], "paletteKey": "Q"}
        try:
            raw = json.loads(self._tools_config_path().read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            return data
        if not isinstance(raw, dict):
            return data

        favorites = []
        for item in raw.get("favorites") or []:
            if not isinstance(item, dict):
                continue
            cmd = str(item.get("cmd") or "").strip()
            if not cmd:
                continue
            if not cmd.startswith("/"):
                cmd = "/" + cmd
            try:
                slot = int(item.get("slot"))
            except (TypeError, ValueError):
                slot = None
            favorites.append(
                {
                    "id": str(item.get("id") or f"fav-{len(favorites) + 1}"),
                    "title": str(item.get("title") or cmd),
                    "cmd": cmd,
                    "slot": slot if slot in range(0, 10) else None,
                }
            )
        data["favorites"] = favorites
        key = str(raw.get("paletteKey") or "Q").upper()
        data["paletteKey"] = key
        return data

    async def _tools_config(self) -> dict:
        return self._read_tools_config()

    async def _tools_save_config(
        self, favorites: Any = None, palette_key: Any = None
    ) -> dict:
        import uuid

        rows: list[dict] = []
        for item in favorites or []:
            if not isinstance(item, dict):
                continue
            cmd = str(item.get("cmd") or "").strip()
            if not cmd:
                continue
            if not cmd.startswith("/"):
                cmd = "/" + cmd
            try:
                slot = int(item.get("slot"))
            except (TypeError, ValueError):
                slot = None
            rows.append(
                {
                    "id": str(item.get("id") or uuid.uuid4().hex[:8]),
                    "title": str(item.get("title") or cmd).strip() or cmd,
                    "cmd": cmd,
                    "slot": slot if slot in range(0, 10) else None,
                }
            )

        key = str(palette_key or "Q").upper()
        data = {"favorites": rows, "paletteKey": key}
        path = self._tools_config_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError as exc:
            raise RuntimeError(f"保存失败：{exc}") from exc
        logger.info("常用指令已保存：%d 条，小窗热键 Ctrl+Alt+%s", len(rows), key)
        return {"ok": True, "config": data}

    async def _tools_sync_palette(self, payload: Any = None) -> dict:
        """前端把全量候选 + 合法前缀推给 Python，供 Ctrl+Alt+Q 速查窗检索/构建"""
        entries: Any = payload
        nodes: Any = []
        if isinstance(payload, dict):
            entries = payload.get("entries") or []
            nodes = payload.get("nodes") or []

        rows: list[dict] = []
        seen: set[str] = set()
        for item in entries or []:
            if not isinstance(item, dict):
                continue
            token = str(item.get("token") or "").strip()
            parent = str(item.get("parent") or "").strip()
            if not token:
                continue
            command = f"{parent} {token}".strip()
            if command in seen:
                continue
            seen.add(command)
            rows.append(
                {
                    "token": token,
                    "hint": str(item.get("hint") or ""),
                    "parent": parent,
                    "command": command,
                }
            )
        self.palette_entries = rows
        self.palette_nodes = [str(n).strip() for n in nodes if str(n).strip()]
        logger.info("指令速查表已同步：%d 条候选 / %d 个前缀", len(rows), len(self.palette_nodes))
        return {"ok": True, "count": len(rows), "nodes": len(self.palette_nodes)}

    def push_hotkey(self, slot: int, text: str, title: str, mode: str = "copy") -> None:
        """热键触发后通知前端弹提示（mode: sent / copy）"""
        self._run_js(
            "window.__veinHotkey && window.__veinHotkey("
            f"{int(slot)},{json.dumps(text, ensure_ascii=False)},"
            f"{json.dumps(title, ensure_ascii=False)},"
            f"{json.dumps(mode, ensure_ascii=False)})"
        )

    async def _instance_toggle(self, version_id: str, kind: str, name: str, enabled: bool) -> dict:
        return self._ctx.instances.set_enabled(str(version_id), str(kind), str(name), bool(enabled))

    async def _instance_delete_file(self, version_id: str, kind: str, name: str) -> dict:
        return self._ctx.instances.delete(str(version_id), str(kind), str(name))

    async def _instance_worlds(self, version_id: str) -> list:
        return self._ctx.instances.list_worlds(str(version_id))

    async def _instance_delete_world(self, version_id: str, folder: str) -> dict:
        return self._ctx.instances.delete_world(str(version_id), str(folder))

    async def _skins_list(self) -> list:
        rows = []
        for account in self._ctx.accounts.list():
            state = self._ctx.skins.state(account["id"])
            rows.append({**account, "skin": state})
        return rows

    async def _skins_import(self, account_id: str, path: str, model: str = "classic") -> dict:
        return self._ctx.skins.apply_file(str(account_id), str(path), str(model))

    async def _skins_clear(self, account_id: str) -> dict:
        return self._ctx.skins.clear(str(account_id))

    async def _skins_remote(self, account_id: str) -> dict:
        """读取 LittleSkin 角色当前的皮肤（只读预览，不写回）"""
        import base64

        from vein_launcher.application.services.skin_service import SkinError, validate_skin
        from vein_launcher.infrastructure.network import littleskin

        account = self._ctx.accounts.get(str(account_id))
        if account is None:
            return {"ok": False, "error": "Account not found"}
        if getattr(account, "account_type", "") != "littleskin":
            return {"ok": False, "error": "Only LittleSkin accounts have a remote skin"}
        try:
            profile = await littleskin.profile_by_uuid(
                getattr(account, "server", ""), getattr(account, "uuid", "") or ""
            )
            skin = littleskin.extract_skin(profile)
            if not skin:
                return {"ok": False, "error": "This LittleSkin player has no skin yet"}
            data = await littleskin.fetch_texture(skin["url"])
            validate_skin(data)
        except (littleskin.LittleSkinError, SkinError) as exc:
            logger.warning("读取 LittleSkin 皮肤失败：%s", exc)
            return {"ok": False, "error": str(exc)}
        return {
            "ok": True,
            "model": skin["model"],
            "url": skin["url"],
            "data_url": "data:image/png;base64," + base64.b64encode(data).decode(),
        }

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

    async def _mc2_scan(self, instance: str, folder: str) -> dict:
        return await asyncio.to_thread(self._ctx.mc2.scan, str(instance), str(folder))

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
        state = dict(self._ctx.mlc.state())
        # connected 保留旧字段语义：游戏进程是否仍然连着
        state["connected"] = bool(state.get("running"))
        state["pid"] = state.get("pid") or self._mlc_pid
        return state

    async def _mlc_player(self, version_id: str = "", world: str = "") -> dict:
        return self._ctx.mlc.player_info(str(version_id), str(world))

    async def _mlc_world_detail(self, version_id: str = "", world: str = "") -> dict:
        return self._ctx.mlc.world_detail(str(version_id), str(world))

    async def _mlc_set_enabled(self, enabled: bool = False) -> dict:
        return self._ctx.mlc.set_enabled(bool(enabled))

    async def _mlc_agent_state(self, port: int = 0) -> dict:
        return await self._ctx.mlc.agent_state(int(port or 0))

    async def _mlc_agent_chat(self, text: str = "", port: int = 0) -> dict:
        return await self._ctx.mlc.agent_chat(str(text), int(port or 0))

    async def _mlc_watch_start(self, interval: float = 1.0) -> dict:
        self._ctx.mlc.start_agent_watch(float(interval or 1.0))
        return {"watching": True}

    async def _mlc_watch_stop(self) -> dict:
        self._ctx.mlc.stop_agent_watch()
        return {"watching": False}

    async def _mlc_mod_load(self, version_id: str = "", path: str = "") -> dict:
        return self._ctx.mlc.mod_load(str(version_id), str(path))

    def _make_mlc_agent_handler(self, name: str):
        def handle(state: Any = None, **_ignored) -> None:
            payload = json.dumps({"event": name, "state": state}, ensure_ascii=False)
            self._run_js(f"window.__veinMlcEvent && window.__veinMlcEvent({payload})")

        return handle

    def _on_plugin_ui(self, plugin_id: str = "", tree: Any = None) -> None:
        payload = json.dumps({"pluginId": plugin_id, "tree": tree}, ensure_ascii=False)
        self._run_js(f"window.__veinUi && window.__veinUi({payload})")

    def _on_game_running(self, pid: int = 0, **_) -> None:
        self._mlc_connected = True
        self._mlc_pid = int(pid) or None

    def _on_game_exited(self, exit_code: int = 0, **_) -> None:
        self._mlc_connected = False
        self._mlc_pid = None
        self._run_js(f"window.__veinGameExited && window.__veinGameExited({int(exit_code or 0)})")

    async def _open_log_dir(self) -> dict:
        import subprocess

        from vein_launcher.common.logging.logger import log_dir

        path = log_dir()
        subprocess.Popen(["explorer", str(path)], **hidden_popen_kwargs())
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
