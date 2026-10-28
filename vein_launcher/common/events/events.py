"""所有业务事件的常量定义 - 统一事件命名规范"""


class EventNames:
    """事件名称常量类"""
    
    # ========== 版本相关事件 ==========
    VERSION_LIST_UPDATED = "version.list.updated"        # 版本列表刷新
    VERSION_SELECTED = "version.selected"                # 用户选择版本
    VERSION_DOWNLOAD_START = "version.download.start"    # 开始下载版本
    VERSION_DOWNLOAD_PROGRESS = "version.download.progress"  # 下载进度更新
    VERSION_DOWNLOAD_COMPLETE = "version.download.complete"  # 版本下载完成
    VERSION_DOWNLOAD_ERROR = "version.download.error"      # 下载失败
    VERSION_DELETED = "version.deleted"                  # 版本被删除
    
    # ========== 下载任务事件 ==========
    DOWNLOAD_QUEUE_UPDATED = "download.queue.updated"        # 下载队列变更
    DOWNLOAD_TASK_START = "download.task.start"              # 单个下载任务开始
    DOWNLOAD_TASK_PROGRESS = "download.task.progress"        # 任务进度（文件级）
    DOWNLOAD_TASK_COMPLETE = "download.task.complete"        # 任务完成
    DOWNLOAD_TASK_ERROR = "download.task.error"             # 任务失败
    
    # ========== 游戏启动事件 ==========
    GAME_LAUNCH_START = "game.launch.start"              # 开始启动游戏
    GAME_LOG_UPDATE = "game.log.update"                  # 游戏日志更新（实时）
    GAME_RUNNING = "game.running"                        # 游戏正在运行
    GAME_EXITED = "game.exited"                          # 游戏退出
    Game_CRASHED = "game.crashed"                         # 游戏崩溃
    
    # ========== 账号事件 ==========
    ACCOUNT_ADDED = "account.added"                      # 添加新账号
    ACCOUNT_REMOVED = "account.removed"                  # 删除账号
    ACCOUNT_SELECTED = "account.selected"                # 切换当前账号
    ACCOUNT_LOGIN_SUCCESS = "account.login.success"      # 登录成功
    ACCOUNT_LOGIN_FAILED = "account.login.failed"        # 登录失败
    
    # ========== 加载器事件（Fabric/Forge/Quilt）==========
    LOADER_INSTALL_START = "loader.install.start"        # 开始安装加载器
    LOADER_INSTALL_COMPLETE = "loader.install.complete"   # 加载器安装完成
    LOADER_INSTALL_ERROR = "loader.install.error"         # 加载器安装失败
    
    # ========== 模组事件 ==========
    MODS_UPDATED = "mods.updated"                        # 模组列表更新
    MOD_TOGGLE = "mod.toggle"                             # 模组启用/禁用
    
    # ========== 设置事件 ==========
    THEME_CHANGED = "theme.changed"                      # 主题切换（深色/浅色）
    SETTINGS_UPDATED = "settings.updated"                # 设置保存成功
    JAVA_PATH_CHANGED = "java.path.changed"              # Java 路径变更
    
    # ========== UI 交互事件 ==========
    PAGE_CHANGED = "page.changed"                        # 页面切换
    SHOW_LOG_PANEL = "ui.show.log_panel"                 # 显示日志面板
    HIDE_LOG_PANEL = "ui.hide.log_panel"                 # 隐藏日志面板
    
    # ========== 系统事件 ==========
    APP_STARTUP = "app.startup"                          # 应用启动完成
    APP_SHUTDOWN = "app.shutdown"                        # 应用即将关闭
