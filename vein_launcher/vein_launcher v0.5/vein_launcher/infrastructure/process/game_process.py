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

        self._reader = asyncio.create_task(self._pump())
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

    async def wait(self) -> int:
        if self._process is None:
            return -1
        code = await self._process.wait()
        if self._reader:
            try:
                await asyncio.wait_for(self._reader, timeout=3)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                self._reader.cancel()
        event_bus.publish(EventNames.GAME_EXITED, exit_code=code)
        return code

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


__all__ = ["GameProcess"]
