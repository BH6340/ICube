import os
import sys
import logging

from loguru import logger
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 1. 定义拦截器：将标准 logging 日志转发至 Loguru
class InterceptHandler(logging.Handler):
    def emit(self, record):
        # 获取对应的 Loguru 级别
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 找到调用者的帧以记录正确的代码行号
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging():
    """
    配置 Loguru 日志并拦截标准 logging
    """
    # --- 配置参数 ---
    # 日志文件路径
    folder_ = os.path.join(BASE_DIR, "log/")
    # 文件前缀
    prefix_ = "cube-"
    # 超过10MB创建新的日志文件
    rotation_ = "10 MB"
    # 30天覆盖
    retention_ = "30 days"
    encoding_ = "utf-8"
    backtrace_ = True
    # 诊断
    diagnose_ = True

    # 格式定义：包含进程和线程 ID
    format_ = (
        '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | '
        '<level>{level: <8}</level> | '
        '<magenta>{process}</magenta>:<yellow>{thread}</yellow> | '
        '<cyan>{name}</cyan>:<cyan>{function}</cyan>:<yellow>{line}</yellow> - '
        '<level>{message}</level>'
    )

    # 确保日志目录存在
    if not os.path.exists(folder_):
        os.makedirs(folder_)

    # --- Loguru 配置 ---

    # 移除 Loguru 默认的 Handler（防止重复输出）
    logger.remove()

    # 添加分级日志文件（漏斗式记录）
    levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    for level_name in levels:
        logger.add(
            sink=f"{folder_}{prefix_}{level_name.lower()}.log",
            level=level_name,
            format=format_,
            rotation=rotation_,
            retention=retention_,
            encoding=encoding_,
            backtrace=backtrace_,
            diagnose=diagnose_,
            colorize=False,
            enqueue=True,  # 异步写入，多进程安全
        )

    # 添加控制台输出
    logger.add(
        sys.stderr,
        level="INFO",
        format=format_,
        colorize=True,
        backtrace=backtrace_,
        diagnose=diagnose_,
        enqueue=False
    )

    # --- 拦截 Django/标准库日志 ---

    # 所有的日志都会被重定向到 InterceptHandler
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # 特别针对一些常见的库，确保它们的记录器也使用拦截器
    # 这里可以根据需要添加更多的库名
    loggers = [
        "django",
        "django.server",
        "django.db.backends",
        "django.utils.autoreload",
        "gunicorn",
        "uvicorn",
    ]

    for name in loggers:
        _logger = logging.getLogger(name)
        _logger.handlers = [InterceptHandler()]
        _logger.propagate = False  # 防止向上抛给已经配置过的根记录器导致重复

    # logger.info(f"Log folder is: {folder_}")