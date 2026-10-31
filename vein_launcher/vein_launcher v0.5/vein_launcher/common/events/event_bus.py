"""全局事件总线 - 所有跨层通信的唯一通道"""

from typing import Callable, Any, Dict, List
from collections import defaultdict
import threading
import logging

logger = logging.getLogger(__name__)


class EventBus:
    """
    全局事件总线（单例模式）
    
    职责：
    - 发布/订阅模式实现跨层通信  
    - 所有层之间的数据流转必须通过事件总线
    - 禁止直接调用其他层的 API
    
    使用示例：
        # 订阅事件
        event_bus.subscribe("version.download.complete", callback)
        
        # 发布事件
        event_bus.publish("version.download.complete", version_id="1.20.4")
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # 事件 -> [回调函数列表]
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._lock = threading.RLock()
        self._initialized = True
        
        logger.info("EventBus 初始化完成")
    
    def subscribe(self, event_name: str, callback: Callable) -> None:
        """
        订阅事件
        
        Args:
            event_name: 事件名称，格式 "模块。动作。状态" 如 "version.download.complete"
            callback: 回调函数，接收 **kwargs 参数
        """
        with self._lock:
            if event_name not in self._subscribers:
                self._subscribers[event_name] = []
            self._subscribers[event_name].append(callback)
            logger.debug(f"订阅事件：{event_name}")
    
    def unsubscribe(self, event_name: str, callback: Callable) -> None:
        """取消订阅"""
        with self._lock:
            if event_name in self._subscribers and callback in self._subscribers[event_name]:
                self._subscribers[event_name].remove(callback)
                logger.debug(f"取消订阅：{event_name}")
    
    def publish(self, event_name: str, **data) -> None:
        """
        发布事件
        
        Args:
            event_name: 事件名称
            **data: 传递给所有订阅者的数据
        """
        with self._lock:
            callbacks = list(self._subscribers.get(event_name, []))
        
        # 在锁外执行回调，避免死锁
        for callback in callbacks:
            try:
                callback(**data)
            except Exception as e:
                logger.error(f"事件处理错误 [{event_name}]: {e}")
    
    def publish_once(self, event_name: str, **data) -> None:
        """发布与取消订阅（一次性事件）"""
        def one_shot_callback(**kwargs):
            self.unsubscribe(event_name, one_shot_callback)
            # 执行实际回调逻辑，由调用者决定
        
        self.subscribe(event_name, one_shot_callback)
        self.publish(event_name, **data)
    
    def clear(self) -> None:
        """清除所有订阅（用于程序退出）"""
        with self._lock:
            self._subscribers.clear()


# 全局单例实例
event_bus = EventBus()
