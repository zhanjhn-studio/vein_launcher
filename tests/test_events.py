"""事件总线测试 —— 验证跨层通信的唯一通道行为"""

from __future__ import annotations

import unittest

from vein_launcher.common.events.event_bus import EventBus
from vein_launcher.common.events.events import EventNames


class EventBusTest(unittest.TestCase):
    def setUp(self):
        self.bus = EventBus()
        self.bus.clear()

    def tearDown(self):
        self.bus.clear()

    def test_publish_subscribe(self):
        received = []
        self.bus.subscribe("demo.event", lambda **kw: received.append(kw))
        self.bus.publish("demo.event", value=42)
        self.assertEqual(received, [{"value": 42}])

    def test_unsubscribe(self):
        received = []
        handler = lambda **kw: received.append(kw)  # noqa: E731
        self.bus.subscribe("demo.event", handler)
        self.bus.unsubscribe("demo.event", handler)
        self.bus.publish("demo.event", value=1)
        self.assertEqual(received, [])

    def test_handler_exception_isolated(self):
        received = []

        def boom(**_):
            raise RuntimeError("handler failed")

        self.bus.subscribe("demo.event", boom)
        self.bus.subscribe("demo.event", lambda **kw: received.append(kw))
        self.bus.publish("demo.event", value=7)  # 不应抛出
        self.assertEqual(received, [{"value": 7}])

    def test_singleton(self):
        self.assertIs(EventBus(), EventBus())

    def test_event_names_unique(self):
        values = [
            v for k, v in vars(EventNames).items()
            if not k.startswith("_") and isinstance(v, str)
        ]
        self.assertEqual(len(values), len(set(values)), "事件名存在重复")
        self.assertIn(EventNames.PLUGIN_LOADED, values)


if __name__ == "__main__":
    unittest.main()
