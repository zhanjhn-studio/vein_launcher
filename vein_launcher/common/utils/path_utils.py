"""路径工具 - Windows pathlib 优先"""

from pathlib import Path
import os


def get_app_data_dir() -> Path:
    """获取应用程序数据目录 (AppData\\Roaming)"""
    return Path(os.path.expandvars("~\\AppData\\Roaming\\VeinLauncher"))


def get_instance_root() -> Path:
    """
    获取 Minecraft 实例根目录
    默认：AppData\\Roaming\\.vein_launcher\\instances
    """
    return get_app_data_dir() / "instances"


def get_version_dir(version_id: str) -> Path:
    """
    获取指定版本的目录
    
    Args:
        version_id: 版本 ID，如 "1.20.4", "fabric-1.20.4"
        
    Returns:
        版本目录路径
    """
    return get_instance_root() / version_id


def get_assets_dir() -> Path:
    """获取全局 assets 目录（多版本共享）"""
    return get_app_data_dir() / "assets"


def get_plugins_dir() -> Path:
    """获取插件安装根目录（每个插件一个子目录）"""
    return get_app_data_dir() / "plugins"


def sanitize_plugin_id(plugin_id: str) -> str:
    """把 NPM 包名转成安全的目录名（@scope/name -> @scope__name）"""
    return plugin_id.replace("/", "__").replace("\\", "__").strip()


def get_plugin_sandbox_dir(plugin_id: str) -> Path:
    """获取单个插件的数据沙箱目录（插件只能读写这里 + 自身目录）"""
    return get_plugins_dir() / sanitize_plugin_id(plugin_id) / "data"


def get_libraries_dir() -> Path:
    """获取全局 libraries 目录（多版本共享）"""
    return get_app_data_dir() / "libraries"


def ensure_dir(path: Path) -> Path:
    """
    确保目录存在，不存在则创建
    
    Args:
        path: 目标路径
        
    Returns:
        路径对象
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_join(base: Path, *paths: str) -> Path:
    """
    安全地拼接路径，防止路径穿越
    
    Args:
        base: 基础路径
        *paths: 要拼接的路径片段
        
    Returns:
        绝对路径
    """
    full_path = base.joinpath(*paths).resolve()
    
    # 安全检查：确保最终路径在基础路径下
    try:
        full_path.relative_to(base)
        return full_path
    except ValueError:
        raise ValueError(f"路径穿越检测失败：{full_path}")


def get_relative_path(full_path: Path, base: Path) -> str:
    """获取相对路径"""
    try:
        return str(full_path.relative_to(base))
    except ValueError:
        return str(full_path)
