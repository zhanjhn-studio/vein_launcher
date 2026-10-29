"""MLC - Minecraft Launcher Control

Vein Launcher 自研的游戏控制层（替代传统 MCP 的角色）：
封装启动、世界信息、事件订阅等能力，供插件通过 Node 宿主安全调用。

当前为 **demo 阶段**：只实现真实可用的部分，
涉及游戏内数据（玩家坐标、按键输入）的能力返回明确的不支持状态。
"""

from vein_launcher.mlc.service import MlcService

__all__ = ["MlcService"]
