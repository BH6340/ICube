import os
import sys
import logging
import json

from loguru import logger
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def _get_log_folder():
    if os.getenv('RUNNING_IN_DOCKER', 'false').lower() == 'true':
        return '/var/log/icube/'
    return os.path.join(BASE_DIR, "log/")


def setup_logging():
    is_production = os.getenv('DJANGO_ENV', 'dev').lower() == 'prod'
    folder_ = _get_log_folder()
    prefix_ = "cube-"
    rotation_ = "10 MB"
    retention_ = "30 days"
    encoding_ = "utf-8"
    backtrace_ = True
    diagnose_ = not is_production

    console_level = "WARNING" if is_production else "INFO"
    file_min_level = "INFO" if is_production else "DEBUG"

    format_text = (
        '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | '
        '<level>{level: <8}</level> | '
        '<magenta>{process}</magenta>:<yellow>{thread}</yellow> | '
        '<cyan>{name}</cyan>:<cyan>{function}</cyan>:<yellow>{line}</yellow> - '
        '<level>{message}</level>'
    )

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

    if not os.path.exists(folder_):
        os.makedirs(folder_)

    logger.remove()

    if is_production:
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
            enqueue=True,
        )

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
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level_name in levels:
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

    logger.add(
        sys.stderr,
        level=console_level,
        format=format_text,
        colorize=True,
        backtrace=backtrace_,
        diagnose=diagnose_,
        enqueue=False
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    loggers = [
        ("django", "WARNING" if is_production else "INFO"),
        ("django.server", "WARNING"),
        ("django.db.backends", "WARNING"),
        ("django.utils.autoreload", "WARNING"),
        ("gunicorn", "INFO"),
        ("uvicorn", "INFO"),
    ]

    for name, level in loggers:
        _logger = logging.getLogger(name)
        _logger.handlers = [InterceptHandler()]
        _logger.setLevel(level)
        _logger.propagate = False

    logger.info(f"Log folder: {folder_}, Environment: {'production' if is_production else 'development'}")