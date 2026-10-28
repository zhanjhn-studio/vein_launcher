"""全局配置管理 - Pydantic 模型 + JSON 存储"""

import json
import logging
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class JavaConfig(BaseModel):
    """Java 环境配置"""
    path: Optional[str] = None  # Java 执行路径
    auto_detect: bool = True    # 是否自动探测


class LaunchConfig(BaseModel):
    """游戏启动配置"""
    memory_min: int = 2048      # 最小内存 (MB)
    memory_max: int = 4096      # 最大内存 (MB)
    resolution_width: int = 1920  # 游戏分辨率宽
    resolution_height: int = 1080 # 游戏分辨率高
    full_screen: bool = False   # 是否全屏
    jvm_args: list[str] = Field(default_factory=list)  # 自定义 JVM 参数


class DownloadConfig(BaseModel):
    """下载配置"""
    max_speed_mbps: int = 0     # 限速 (0=不限速)
    max_concurrent: int = 4     # 最大并发数
    retry_count: int = 3        # 失败重试次数


class NetworkConfig(BaseModel):
    """网络配置"""
    proxy_enabled: bool = False
    proxy_type: str = "HTTP"    # HTTP / SOCKS5
    proxy_host: str = ""
    proxy_port: int = 0


class UIConfig(BaseModel):
    """界面配置"""
    theme: str = "dark"         # dark / light
    language: str = "zh_CN"     # zh_CN / en_US
    window_width: int = 1200
    window_height: int = 800


class Settings(BaseModel):
    """全局配置主模型"""
    java: JavaConfig = Field(default_factory=JavaConfig)
    launch: LaunchConfig = Field(default_factory=LaunchConfig)
    download: DownloadConfig = Field(default_factory=DownloadConfig)
    network: NetworkConfig = Field(default_factory=NetworkConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    
    # 版本管理根路径（默认在 APPDATA）
    instance_root: Optional[str] = None


class SettingsManager:
    """配置管理器（单例）"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._config_path = self._get_config_path()
        self._settings: Optional[Settings] = None
        self._initialized = True
        
        logger.info(f"配置管理器初始化，配置文件路径：{self._config_path}")
    
    def _get_config_path(self) -> Path:
        """获取配置文件路径"""
        # Windows: %APPDATA%\VeinLauncher\config.json
        from pathlib import Path
        config_dir = Path(__import__('os').path.expandvars("~\\AppData\\Roaming\\VeinLauncher"))
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.json"
    
    def load(self) -> Settings:
        """加载配置"""
        if self._config_path.exists():
            try:
                data = json.loads(self._config_path.read_text(encoding="utf-8"))
                self._settings = Settings(**data)
                logger.info("配置加载成功")
            except Exception as e:
                logger.warning(f"配置加载失败，使用默认配置：{e}")
                self._settings = Settings()
        else:
            self._settings = Settings()
            self.save()
        
        return self._settings
    
    def save(self) -> bool:
        """保存配置"""
        if not self._settings:
            return False
        
        try:
            # 确保目录存在
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # JSON 格式化输出
            json_str = self._settings.model_dump_json(indent=2, ensure_ascii=False)
            self._config_path.write_text(json_str, encoding="utf-8")
            logger.info("配置保存成功")
            return True
        except Exception as e:
            logger.error(f"配置保存失败：{e}")
            return False
    
    def get(self) -> Settings:
        """获取当前配置"""
        if not self._settings:
            return self.load()
        return self._settings


# 全局单例
settings_manager = SettingsManager()
