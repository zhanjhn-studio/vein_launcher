"""日志系统配置 - 文件 + 控制台双输出"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logger(name: str = "vein_launcher", log_level: int = logging.INFO) -> logging.Logger:
    """
    配置并返回 Logger
    
    Args:
        name: logger 名称
        log_level: 日志级别
        
    Returns:
        配置好的 Logger 实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # 防止重复添加 handler
    if logger.handlers:
        return logger
    
    # 创建日志目录
    log_dir = Path(__import__("os").path.expandvars("~\\AppData\\Roaming\\VeinLauncher\\logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 日期标记的日志文件
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = log_dir / f"{today}.log"
    
    # 1. 控制台 handler（stdout）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_format = logging.Formatter(
        "[%(levelname)-8s] %(name)s | %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # 2. 文件 handler（详细日志）
    file_handler = logging.FileHandler(
        log_file, 
        mode="a", 
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)  # 文件记录更详细的日志
    file_format = logging.Formatter(
        "[%(asctime)s] [%(levelname)-8s] %(name)s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    # 3. 错误日志单独文件（仅 ERROR+）
    error_log_file = log_dir / "error.log"
    error_handler = logging.FileHandler(
        error_log_file,
        mode="a",
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_format)
    logger.addHandler(error_handler)
    
    return logger


# 全局默认 logger
logger = setup_logger()
