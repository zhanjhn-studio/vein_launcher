"""基础设施层 - 游戏进程管理"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import List, Optional

from vein_launcher.common.events.event_bus import event_bus
from vein_launcher.common.events.events import EventNames
from vein_launcher.common.exceptions import GameLaunchError

logger = logging.getLogger(__name__)


class GameProcess:
    """启动 Minecraft 并转发 stdout"""

    def __init__(self) -> None:
        self._process: Optional[asyncio.subprocess.Process] = None
        self._reader: Optional[asyncio.Task] = None
        self._waiter: Optional[asyncio.Task] = None
        self._exit_code: Optional[int] = None
        self._exit_published = False

    @property
    def running(self) -> bool:
        return self._process is not None and self._process.returncode is None

    @property
    def pid(self) -> Optional[int]:
        return self._process.pid if self._process else None

    # ------------------------------------------------------------------
    async def launch(self, command: List[str], cwd: Path) -> int:
        if self.running:
            raise GameLaunchError("游戏已在运行")
        if not command:
            raise GameLaunchError("启动命令为空")
        if not Path(command[0]).is_file():
            raise GameLaunchError(f"Java 不存在：{command[0]}")

        logger.info("启动游戏：%s", " ".join(command))
        try:
            self._process = await asyncio.create_subprocess_exec(
                *command,
                cwd=str(cwd),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
        except OSError as exc:
            raise GameLaunchError(f"进程创建失败：{exc}") from exc

        self._exit_code = None
        self._exit_published = False
        self._reader = asyncio.create_task(self._pump())
        # 后台监听退出：调用方不等待 wait() 时也能复位 UI 的运行状态
        self._waiter = asyncio.create_task(self._watch_exit())
        event_bus.publish(EventNames.GAME_RUNNING, pid=self._process.pid)
        return self._process.pid

    async def _pump(self) -> None:
        assert self._process is not None and self._process.stdout is not None
        stream = self._process.stdout
        while True:
            line = await stream.readline()
            if not line:
                break
            text = line.decode("utf-8", errors="replace").rstrip()
            if text:
                event_bus.publish(EventNames.GAME_LOG_UPDATE, line=text)

    async def _watch_exit(self) -> None:
        """等待进程结束并发布 GAME_EXITED（只发布一次）"""
        process = self._process
        if process is None:
            return
        try:
            code = await process.wait()
        except asyncio.CancelledError:
            raise
        except Exception:  # 监听失败不应影响启动流程
            logger.exception("等待游戏进程结束失败")
            return
        self._publish_exit(code)

    def _publish_exit(self, code: int) -> None:
        self._exit_code = code
        if self._exit_published:
            return
        self._exit_published = True
        logger.info("游戏进程结束：exit_code=%s", code)
        event_bus.publish(EventNames.GAME_EXITED, exit_code=code)

    async def wait(self) -> int:
        """等待游戏结束（返回值与 GAME_EXITED 一致）"""
        if self._process is None:
            return -1
        if self._waiter is None:
            self._waiter = asyncio.create_task(self._watch_exit())
        try:
            await self._waiter
        except asyncio.CancelledError:
            self._waiter = None
            raise
        if self._reader is not None:
            try:
                await asyncio.wait_for(self._reader, timeout=3)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                self._reader.cancel()
        if self._exit_code is None:
            code = self._process.returncode if self._process.returncode is not None else -1
            self._publish_exit(code)
        return self._exit_code if self._exit_code is not None else -1

    async def kill(self) -> None:
        if not self.running:
            return
        assert self._process is not None
        self._process.terminate()
        try:
            await asyncio.wait_for(self._process.wait(), timeout=8)
        except asyncio.TimeoutError:
            self._process.kill()
            await self._process.wait()
        # 等后台监听收尾，保证事件只发一次且 exit code 正确
        if self._waiter is not None:
            try:
                await asyncio.wait_for(self._waiter, timeout=5)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                self._waiter.cancel()
        code = self._process.returncode if self._process.returncode is not None else -1
        self._publish_exit(code)


__all__ = ["GameProcess"]
