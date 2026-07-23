# -*- coding: utf-8 -*-
"""
Loguru 日志配置模块

该模块配置项目的日志系统，使用 Loguru 替代 Django 默认的 logging 模块。

设计背景：
    - Django 默认日志系统配置繁琐，使用不便
    - Loguru 提供更简洁的 API 和更强大的功能
    - 需要支持开发环境和生产环境的不同日志策略
    - 需要将 Django 和第三方库的日志也纳入 Loguru 管理

核心组件：
    - InterceptHandler: 将标准 logging 日志转发到 Loguru
    - _get_log_folder: 根据运行环境确定日志目录
    - setup_logging: 配置日志系统的主函数

日志策略：
    - 开发环境：按日志级别分别输出到不同文件，控制台输出 INFO 级别
    - 生产环境：统一输出到 all.log，ERROR 级别额外输出到 error.log，控制台输出 WARNING 级别
    - 日志文件大小达到 10MB 自动分割，保留 30 天
"""
import os
import sys
import logging
import json

from loguru import logger
from pathlib import Path
from datetime import datetime

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class InterceptHandler(logging.Handler):
    """
    标准 logging 到 Loguru 的桥接处理器

    将 Django、第三方库等使用标准 logging 模块的日志转发到 Loguru。
    这样整个项目的日志都统一由 Loguru 管理，便于配置和分析。

    工作原理：
        1. 继承 logging.Handler
        2. 重写 emit 方法，将 logging 的 LogRecord 转换为 Loguru 的日志调用
        3. 调整调用深度，确保日志显示的是原始调用位置而非本类
    """

    def emit(self, record):
        """
        将 logging 的日志记录转发到 Loguru

        Args:
            record: logging.LogRecord 对象
        """
        # 将 logging 的级别名称转换为 Loguru 的级别
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            # 如果级别名称无法识别，使用数值级别
            level = record.levelno

        # 调整调用深度，确保日志显示的是原始调用位置
        # 因为当前函数在调用链中，需要跳过本类和 logging 模块的栈帧
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        # 将日志转发到 Loguru，包含异常信息
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def _get_log_folder():
    """
    根据运行环境确定日志目录

    返回：
        Docker 环境返回 '/var/log/icube/'
        本地环境返回项目根目录下的 'log/' 目录
    """
    if os.getenv('RUNNING_IN_DOCKER', 'false').lower() == 'true':
        return '/var/log/icube/'
    return os.path.join(BASE_DIR, "log/")


def setup_logging():
    """
    配置日志系统的主函数

    根据环境变量 DJANGO_ENV 决定日志策略：
        - dev: 开发环境，按级别分文件，控制台输出详细信息
        - prod: 生产环境，统一输出，控制台仅输出警告及以上

    配置项说明：
        - rotation: 日志文件大小达到 10MB 自动分割
        - retention: 保留 30 天的日志
        - backtrace: 启用异常回溯
        - diagnose: 开发环境启用诊断信息，生产环境禁用（避免暴露敏感信息）
        - enqueue: 启用异步写入，提高性能
    """
    # 判断当前环境
    is_production = os.getenv('DJANGO_ENV', 'dev').lower() == 'prod'
    folder_ = _get_log_folder()
    prefix_ = "cube-"            # 日志文件前缀
    rotation_ = "10 MB"          # 日志文件大小限制
    retention_ = "30 days"       # 日志保留时间
    encoding_ = "utf-8"          # 文件编码
    backtrace_ = True            # 启用异常回溯（用于调试）
    diagnose_ = not is_production # 生产环境禁用诊断信息（避免暴露敏感信息）

    # 控制台日志级别：生产环境只输出 WARNING 及以上，开发环境输出 INFO 及以上
    console_level = "WARNING" if is_production else "INFO"
    # 文件日志最低级别：生产环境从 INFO 开始，开发环境从 DEBUG 开始
    file_min_level = "INFO" if is_production else "DEBUG"

    # 文本格式（用于开发环境控制台和日志文件）
    format_text = (
        '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | '   # 时间（绿色）
        '<level>{level: <8}</level> | '                       # 级别（带颜色）
        '<magenta>{process}</magenta>:<yellow>{thread}</yellow> | '  # 进程和线程ID
        '<cyan>{name}</cyan>:<cyan>{function}</cyan>:<yellow>{line}</yellow> - '  # 模块、函数、行号
        '<level>{message}</level>'                             # 日志消息
    )

    # JSON 格式（用于生产环境日志文件，便于日志分析工具解析）
    def format_json(record):
        return json.dumps({
            'timestamp': record['time'].strftime('%Y-%m-%dT%H:%M:%S.%f'),
            'level': record['level'].name,
            'process': record['process'],
            'thread': record['thread'],
            'module': record['name'],
            'function': record['function'],
            'line': record['line'],
            'message': record['message'],
            'exception': record['exception'] if record['exception'] else None,
        }, ensure_ascii=False) + '\n'

    # 确保日志目录存在
    if not os.path.exists(folder_):
        os.makedirs(folder_)

    # 移除 Loguru 默认的控制台输出（我们会重新配置）
    logger.remove()

    # 配置文件日志
    if is_production:
        # 生产环境：统一输出到 all.log，ERROR 级别额外输出到 error.log
        # 格式使用 JSON，便于日志分析

        # 所有日志输出到 all.log
        logger.add(
            sink=f"{folder_}{prefix_}all.log",
            level=file_min_level,
            format=format_json,
            rotation=rotation_,
            retention=retention_,
            encoding=encoding_,
            backtrace=backtrace_,
            diagnose=diagnose_,
            colorize=False,
            enqueue=True,  # 异步写入，不阻塞主线程
        )

        # ERROR 级别日志额外输出到 error.log
        logger.add(
            sink=f"{folder_}{prefix_}error.log",
            level="ERROR",
            format=format_json,
            rotation=rotation_,
            retention=retention_,
            encoding=encoding_,
            backtrace=backtrace_,
            diagnose=diagnose_,
            colorize=False,
            enqueue=True,
        )
    else:
        # 开发环境：按日志级别分别输出到不同文件
        # 格式使用文本，便于阅读

        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level_name in levels:
            # 只配置大于等于最低级别的日志文件
            if logger.level(level_name).no >= logger.level(file_min_level).no:
                logger.add(
                    sink=f"{folder_}{prefix_}{level_name.lower()}.log",
                    level=level_name,
                    format=format_text,
                    rotation=rotation_,
                    retention=retention_,
                    encoding=encoding_,
                    backtrace=backtrace_,
                    diagnose=diagnose_,
                    colorize=False,
                    enqueue=True,
                )

    # 配置控制台日志
    logger.add(
        sys.stderr,
        level=console_level,
        format=format_text,
        colorize=True,  # 控制台启用颜色
        backtrace=backtrace_,
        diagnose=diagnose_,
        enqueue=False   # 控制台同步输出，确保实时显示
    )

    # 配置标准 logging 模块，将其转发到 Loguru
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # 配置第三方库的日志级别
    # 将 Django、gunicorn、uvicorn 等库的日志也纳入 Loguru 管理
    loggers = [
        ("django", "WARNING" if is_production else "INFO"),       # Django 核心日志
        ("django.server", "WARNING"),                             # Django 服务器日志
        ("django.db.backends", "WARNING"),                        # 数据库查询日志
        ("django.utils.autoreload", "WARNING"),                   # 自动重载日志（开发环境频繁触发）
        ("gunicorn", "INFO"),                                     # Gunicorn 日志
        ("uvicorn", "INFO"),                                      # Uvicorn 日志
    ]

    for name, level in loggers:
        _logger = logging.getLogger(name)
        _logger.handlers = [InterceptHandler()]  # 使用 InterceptHandler 转发到 Loguru
        _logger.setLevel(level)                  # 设置日志级别
        _logger.propagate = False                # 禁止日志向上传播（避免重复输出）

    # 输出日志系统初始化信息
    logger.info(f"Log folder: {folder_}, Environment: {'production' if is_production else 'development'}")