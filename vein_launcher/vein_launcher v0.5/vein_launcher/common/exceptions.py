"""Vein Launcher 全局异常定义"""


class VeinError(Exception):
    """所有业务异常的基类"""
    pass


# ========== 下载相关错误 ==========

class DownloadError(VeinError):
    """下载失败"""
    
    def __init__(self, message: str, url: str = "", retry_count: int = 0):
        super().__init__(message)
        self.url = url
        self.retry_count = retry_count


class SHA1MismatchError(DownloadError):
    """SHA-1 校验失败"""
    
    def __init__(self, message: str, expected: str, actual: str, file_path: str = ""):
        super().__init__(message)
        self.expected = expected
        self.actual = actual
        self.file_path = file_path


# ========== 版本相关错误 ==========

class VersionNotFoundError(VeinError):
    """未找到指定版本"""
    
    def __init__(self, version_id: str):
        super().__init__(f"版本不存在：{version_id}")
        self.version_id = version_id


class VersionDownloadIncompleteError(VeinError):
    """版本下载不完整，缺少必要文件"""
    
    def __init__(self, version_id: str, missing_files: list[str]):
        super().__init__(f"版本 {version_id} 缺少文件：{', '.join(missing_files)}")
        self.version_id = version_id
        self.missing_files = missing_files


# ========== Java 相关错误 ==========

class JavaNotFoundError(VeinError):
    """未找到可用的 Java 环境"""
    
    def __init__(self, message: str = "未在系统中找到可用的 Java 环境"):
        super().__init__(message)


class JavaVersionUnsupportedError(VeinError):
    """Java 版本不满足要求"""
    
    def __init__(self, required_version: int, actual_version: int):
        super().__init__(f"需要 Java {required_version}，当前版本为 {actual_version}")
        self.required = required_version
        self.actual = actual_version


# ========== 账号相关错误 ==========

class AccountError(VeinError):
    """账号验证失败"""
    
    def __init__(self, message: str, account_id: str = ""):
        super().__init__(message)
        self.account_id = account_id


class AuthenticationError(AccountError):
    """认证失败（微软/离线）"""


# ========== 进程相关错误 ==========

class GameLaunchError(VeinError):
    """游戏启动失败"""
    
    def __init__(self, message: str, error_log: str = ""):
        super().__init__(message)
        self.error_log = error_log


class ProcessTimeoutError(VeinError):
    """进程操作超时"""


# ========== 配置相关错误 ==========

class ConfigError(VeinError):
    """配置读取/保存失败"""
    
    def __init__(self, message: str, file_path: str = ""):
        super().__init__(message)
        self.file_path = file_path
