"""基础设施层 - 游戏进程管理

职责：启动子进程、实时转发 stdout/stderr、上报退出码。
命令构建在 Application 层完成，这里只负责「执行与观测」。
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Optional

from vein_launcher.common.events.event_bus import event_bus
from vein_launcher.common.events.events import EventNames
from vein_launcher.common.exceptions import GameLaunchError

logger = logging.getLogger(__name__)


class GameProcess:
    """Minecraft 进程包装器"""

    def __init__(self):
        self._process: Optional[asyncio.subprocess.Process] = None
        self._reader_task: Optional[asyncio.Task] = None
        self._log_lines: List[str] = []
        self._max_log_lines = 5000

    # ------------------------------------------------------------------
    # 状态
    # ------------------------------------------------------------------
    @property
    def pid(self) -> Optional[int]:
        return self._process.pid if self._process else None

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.returncode is None

    @property
    def exit_code(self) -> Optional[int]:
        return self._process.returncode if self._process else None

    # ------------------------------------------------------------------
    # 启动 / 停止
    # ------------------------------------------------------------------
    async def launch(
        self,
        command: List[str],
        cwd: Path,
        env: Optional[dict] = None,
    ) -> int:
        """启动游戏并返回 PID；日志会在后台异步转发到事件总线"""
        if self.is_running:
            raise GameLaunchError("已有游戏进程在运行")
        if not command:
            raise GameLaunchError("启动命令为空")

        exe = Path(command[0])
        if not exe.exists():
            raise GameLaunchError(f"Java 可执行文件不存在：{exe}")

        logger.info("启动游戏：%s", " ".join(command))
        event_bus.publish(EventNames.GAME_LAUNCH_START, command=command, cwd=str(cwd))

        try:
            self._process = await asyncio.create_subprocess_exec(
                *command,
                cwd=str(cwd),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=env,
                creationflags=self._creation_flags(),
            )
        except OSError as exc:
            raise GameLaunchError(f"进程创建失败：{exc}") from exc

        self._log_lines.clear()
        self._reader_task = asyncio.create_task(self._pump_output())
        event_bus.publish(EventNames.GAME_RUNNING, pid=self._process.pid)
        logger.info("游戏进程已启动 PID=%s", self._process.pid)
        return self._process.pid

    @staticmethod
    def _creation_flags() -> int:
        """Windows 上避免弹出黑框"""
        if sys.platform == "win32":
            return getattr(asyncio.subprocess, "CREATE_NO_WINDOW", 0x08000000)
        return 0

    async def _pump_output(self) -> None:
        """逐行读取 stdout 并广播"""
        assert self._process is not None and self._process.stdout is not None
        stream = self._process.stdout
        while True:
            try:
                raw = await stream.readline()
            except (asyncio.CancelledError, asyncio.LimitOverrunError):
                break
            if not raw:
                break
            line = raw.decode("utf-8", errors="replace").rstrip()
            if not line:
                continue
            self._log_lines.append(line)
            if len(self._log_lines) > self._max_log_lines:
                del self._log_lines[: len(self._log_lines) - self._max_log_lines]
            event_bus.publish(EventNames.GAME_LOG_UPDATE, line=line)

    async def wait(self) -> int:
        """等待进程退出，返回退出码"""
        if self._process is None:
            return -1
        code = await self._process.wait()
        if self._reader_task:
            try:
                await asyncio.wait_for(self._reader_task, timeout=5)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                self._reader_task.cancel()
        event_bus.publish(EventNames.GAME_EXITED, exit_code=code, pid=self._process.pid)
        if code != 0:
            event_bus.publish(EventNames.Game_CRASHED, exit_code=code)
            logger.warning("游戏异常退出，退出码 %s", code)
        else:
            logger.info("游戏正常退出")
        return code

    async def kill(self, timeout: float = 10.0) -> bool:
        """先 terminate，超时后 kill"""
        if not self.is_running:
            return False
        assert self._process is not None
        self._process.terminate()
        try:
            await asyncio.wait_for(self._process.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            self._process.kill()
            await self._process.wait()
        event_bus.publish(EventNames.GAME_EXITED, exit_code=self._process.returncode, pid=self._process.pid)
        return True

    def recent_log(self, limit: int = 200) -> List[str]:
        """最近 N 行日志"""
        return self._log_lines[-limit:]


__all__ = ["GameProcess"]
