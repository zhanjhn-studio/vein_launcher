"""Node.js 插件系统元数据模型

插件通过 NPM 包分发，package.json 声明元信息、权限、入口点。
主程序提供标准化 RPC 接口，开放文件操作/下载队列/JVM 进程/UI 通知能力。

参考 Node Package Manager 标准 + VS Code Extension API
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from enum import Enum


class PluginPermissions(Enum):
    """插件权限模型（沙箱级别）"""
    
    # 基本权限
    READ_CONFIG = "config.read"          # 读取配置
    WRITE_CONFIG = "config.write"        # 修改配置
    
    # 文件操作（需要用户授权特定路径）
    READ_FILE = "file.read"              # 读取指定目录
    WRITE_FILE = "file.write"            # 写入指定目录
    DELETE_FILE = "file.delete"          # 删除文件
    
    # 下载管理
    QUEUE_DOWNLOAD = "download.queue"    # 添加下载任务
    CANCEL_DOWNLOAD = "download.cancel"  # 取消任务
    GET_PROGRESS = "download.progress"   # 查询进度
    
    # 游戏进程控制
    LAUNCH_GAME = "game.launch"          # 启动游戏
    KILL_PROCESS = "game.kill"           # 强制关闭
    READ_LOGS = "game.logs"              # 读取日志
    
    # UI 能力
    SHOW_NOTIFY = "ui.notify"            # 显示通知
    OPEN_PAGE = "ui.open_page"           # 打开指定页面
    
    # 网络请求（需要用户确认）
    HTTP_REQUEST = "network.http"        # HTTP 请求代理
    WS_CONNECT = "network.websocket"     # WebSocket 连接
    
    # 高危权限
    EXECUTE_SYS_CMD = "sys.execute"      # 执行系统命令
    MODIFY_JVM_ARGS = "jvm.modify"       # 修改 JVM 参数


@dataclass
class PluginManifest:
    """插件元数据模型（从 package.json + vein_plugin.json 解析）"""
    
    # NPM 标准字段
    name: str                        # 包名，如 "@vein/plugin-mod-helper"
    version: str                     # SemVer 版本号
    description: str                 # 描述
    author: str                      # 作者
    license: Optional[str] = None    # 开源协议
    
    # Vein Launcher 专用扩展字段
    display_name: str                # UI 显示的中文名称
    icon_path: Optional[str] = None  # 图标路径（相对插件目录）
    homepage_url: Optional[str] = None
    repository_url: Optional[str] = None
    
    # 引擎要求（vein-labchurer >= x.y.z）
    vein_required_version: str = ">=0.1.0"
    
    # Entry 点（Node.js 入口文件路径，相对插件根目录）
    main_entry: str = "dist/main.js"
    
    # API 版本（定义使用的 Vein Launcher RPC API 版本）
    api_version: str = "1.0"
    
    # 请求权限列表
    permissions: List[str] = field(default_factory=list)
    
    # 插件类型标记
    plugin_type: Literal["mod_helper", "theme", "automation", "utility"] = "utility"
    
    # 国际化支持的语言文件
    i18n_locales: Dict[str, str] = field(default_factory=dict)
    # { "zh_CN": "locales/zh_CN.json", "en_US": "locales/en.json" }
    
    # 插件激活模式（启动时自启 / 按需加载）
    activate_on_startup: bool = False
    
    def has_permission(self, permission: str) -> bool:
        """检查是否有特定权限"""
        return permission in self.permissions or PluginPermissions[permission].value in self.permissions


@dataclass
class PluginInstance:
    """已安装插件实例对象（运行时信息）"""
    
    manifest: PluginManifest         # 解析后的元数据
    install_path: str                # 插件文件夹绝对路径
    installed_time: datetime         # 安装时间
    enabled: bool = True             # 是否启用
    
    # Node.js 进程状态（由 Infrastructure 层管理）
    process_pid: Optional[int] = None
    worker_count: int = 0            # Node Worker 线程数
    
    # 沙箱限制目录
    sandbox_paths: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if self.sandbox_paths is None:
            self.sandbox_paths = []


@dataclass
class PluginRPCError:
    """RPC 调用错误"""
    
    code: int                        # 错误代码（类似 HTTP）
    message: str                     # 错误信息
    permission_required: Optional[str] = None  # 缺失的权限声明


# ==================== RPC Protocol Definition ====================

class VeinRPCContext:
    """RPC 调用上下文（注入到每个 callback）"""
    
    def __init__(self, plugin_id: str):
        self.plugin_id = plugin_id
        self.call_stack: List[str] = []


# RPC 接口定义（Python 端提供给 Node.js 的 API）

class VRPCFileOps:
    """文件操作 API（沙箱模式：只在 sandbox_paths 内有效）"""
    
    @staticmethod
    async def read_text(path: str, ctx: VeinRPCContext) -> str:
        """读取文本文件"""
        raise NotImplementedError("Infrastructure layer")
    
    @staticmethod
    async def write_text(path: str, content: str, ctx: VeinRPCContext) -> bool:
        """写入文本文件"""
        raise NotImplementedError()
    
    @staticmethod
    async def list_dir(path: str, ctx: VeinRPCContext) -> List[Dict[str, Any]]:
        """列出目录内容（files/ dirs 分开）"""
        raise NotImplementedError()


class VRPCDownloadQueue:
    """下载队列管理 API"""
    
    @staticmethod
    async def add_task(
        url: str, 
        save_path: str, 
        ctx: VeinRPCContext
    ) -> int:
        """添加下载任务，返回 task_id"""
        raise NotImplementedError()
    
    @staticmethod
    async def cancel(task_id: int, ctx: VeinRPCContext) -> bool:
        raise NotImplementedError()


class VRPCGameControl:
    """游戏进程控制 API"""
    
    @staticmethod
    async def launch(
        version_id: str, 
        memory_mb: int = 4096, 
        ctx: VeinRPCContext
    ) -> Dict[str, Any]:
        return {
            "process_pid": ...,
            "java_path": ...,
            "vm_args": []
        }


class VRPCUIOps:
    """UI 操作 API"""
    
    @staticmethod
    async def notify(
        title: str, 
        message: str, 
        type_: Literal["info", "success", "warning", "error"] = "info",
        ctx: VeinRPCContext = None
    ) -> bool:
        raise NotImplementedError()


# 完整的 VRPC 接口暴露给插件的映射

VRPC_GLOBAL_EXPORTS = {
    # 文件操作
    "file": {
        "readText": VRPCFileOps.read_text,
        "writeText": VRPCFileOps.write_text,
        "listDir": VRPCFileOps.list_dir
    },
    # 下载管理  
    "download": {
        "queueTask": VRPCDownloadQueue.add_task,
        "cancel": VRPCDownloadQueue.cancel
    },
    # 游戏控制
    "game": {
        "launch": VRPCGameControl.launch
    },
    # UI 能力
    "ui": {
        "notify": VRPCUIOps.notify
    }
}
