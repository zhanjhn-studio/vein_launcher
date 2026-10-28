"""表现层 - Qt 与 asyncio 的桥接

UI 线程只处理绘制；所有 IO 协程在后台事件循环线程执行，
结果通过 Qt 信号回到主线程，避免阻塞界面。
"""

from __future__ import annotations

import asyncio
import logging
import threading
from typing import Any, Awaitable, Callable, Dict, Optional

from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class AsyncBridge(QObject):
    """后台 asyncio 事件循环 + 回调派发"""

    _finished = Signal(object, object, object)  # token, result, error

    def __init__(self) -> None:
        super().__init__()
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._run_loop, name="vein-async", daemon=True
        )
        self._callbacks: Dict[int, Optional[Callable[[Any, Optional[BaseException]], None]]] = {}
        self._finished.connect(self._dispatch)
        self._thread.start()

    # ------------------------------------------------------------------
    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return self._loop

    # ------------------------------------------------------------------
    def submit(
        self,
        coro: Awaitable[Any],
        callback: Optional[Callable[[Any, Optional[BaseException]], None]] = None,
    ) -> int:
        """提交协程；callback(result, error) 会在 UI 线程被调用"""
        token = id(coro)
        self._callbacks[token] = callback
        self._loop.call_soon_threadsafe(self._spawn, coro, token)
        return token

    def _spawn(self, coro: Awaitable[Any], token: int) -> None:
        task = self._loop.create_task(coro)  # type: ignore[arg-type]
        task.add_done_callback(lambda t: self._on_done(token, t))

    def _on_done(self, token: int, task: "asyncio.Task[Any]") -> None:
        try:
            error = task.exception()
        except asyncio.CancelledError:
            error = asyncio.CancelledError()
        result = None if error else task.result()
        self._finished.emit(token, result, error)

    def _dispatch(self, token: int, result: Any, error: Any) -> None:
        callback = self._callbacks.pop(token, None)
        if callback:
            try:
                callback(result, error)
            except Exception:  # UI 回调异常不应打断事件循环
                logger.exception("异步回调执行失败")

    # ------------------------------------------------------------------
    def shutdown(self) -> None:
        """停止事件循环（应用退出时调用）"""
        def _stop() -> None:
            for task in asyncio.all_tasks(self._loop):
                task.cancel()
            self._loop.stop()

        try:
            self._loop.call_soon_threadsafe(_stop)
        except RuntimeError:
            pass


__all__ = ["AsyncBridge"]
