#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ICube Redis 备份脚本

通过 docker exec 触发 BGSAVE，等待完成后复制 RDB/AOF 文件
到本地备份目录，并按保留天数清理过期备份。

用法：
  python scripts/redis_backup.py                 # 执行备份
  python scripts/redis_backup.py --dry-run       # 预览不执行
  python scripts/redis_backup.py --keep-days 7   # 指定保留天数（默认 7 天）

环境变量（可通过 .env 加载）：
  REDIS_CONTAINER   Redis 容器名（默认 icube_redis）
  BACKUP_DIR        备份目录（默认 data/redis_backup）
  BGSAVE_TIMEOUT    BGSAVE 等待超时秒数（默认 60）
"""

import os
import sys
import subprocess
import shutil
import time
import argparse
from datetime import datetime
from pathlib import Path

try:
    from loguru import logger
    _LOGURU = True
except ImportError:
    import logging
    _LOGURU = False
    logger = logging.getLogger("redis_backup")
    if not logger.handlers:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        logger.addHandler(h)
    logger.setLevel(logging.INFO)


# ---- 配置默认值 ----
DEFAULT_REDIS_CONTAINER = "icube_redis"
DEFAULT_BACKUP_SUBDIR = "data/redis_backup"
DEFAULT_KEEP_DAYS = 7
DEFAULT_BGSAVE_TIMEOUT = 60


def _run(cmd, check=True, capture=True, text=True):
    """运行 shell 命令，返回 CompletedProcess"""
    logger.debug("执行命令: {}", " ".join(cmd))
    return subprocess.run(
        cmd,
        check=check,
        capture_output=capture,
        text=text,
    )


def redis_cli(container, *args):
    """在 Redis 容器内执行 redis-cli，返回 stdout 字符串"""
    result = _run(["docker", "exec", container, "redis-cli", *args])
    return result.stdout.strip()


def trigger_bgsave(container):
    """触发 BGSAVE 后台快照"""
    output = redis_cli(container, "BGSAVE")
    if "Background saving started" in output:
        logger.info("BGSAVE 已触发")
    else:
        raise RuntimeError(f"BGSAVE 触发失败: {output}")


def wait_bgsave_done(container, timeout):
    """等待 BGSAVE 完成，超时抛 TimeoutError"""
    start = time.time()
    while time.time() - start < timeout:
        info = redis_cli(container, "INFO", "persistence")
        for line in info.splitlines():
            if line.startswith("rdb_bgsave_in_progress:"):
                val = line.split(":", 1)[1].strip()
                if val == "0":
                    logger.info("BGSAVE 完成")
                    return
        time.sleep(1)
    raise TimeoutError(f"BGSAVE 等待超时（{timeout}s）")


def copy_from_container(container, container_path, local_path):
    """从容器复制文件到本地；文件不存在返回 False"""
    result = _run(
        ["docker", "exec", container, "test", "-f", container_path],
        check=False,
        capture=True,
    )
    if result.returncode != 0:
        logger.warning("容器内文件不存在，跳过: {}", container_path)
        return False

    _run(["docker", "cp", f"{container}:{container_path}", str(local_path)])
    logger.info("已复制: {} → {}", container_path, local_path.name)
    return True


def cleanup_old_backups(backup_dir, keep_days):
    """清理超过保留天数的备份文件，返回删除数量"""
    cutoff = time.time() - keep_days * 86400
    deleted = 0
    for f in backup_dir.iterdir():
        if not f.is_file():
            continue
        # 只清理匹配备份命名格式的文件
        if not (f.name.startswith("dump_") and f.name.endswith(".rdb")) and \
           not (f.name.startswith("appendonly_") and f.name.endswith(".aof")):
            continue
        if f.stat().st_mtime < cutoff:
            f.unlink()
            logger.info("清理过期备份: {}", f.name)
            deleted += 1
    return deleted


def main():
    parser = argparse.ArgumentParser(description="ICube Redis 备份脚本")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不执行实际操作")
    parser.add_argument("--keep-days", type=int, default=DEFAULT_KEEP_DAYS,
                        help=f"备份保留天数（默认 {DEFAULT_KEEP_DAYS}）")
    args = parser.parse_args()

    # 从环境变量读取（如通过 .env 加载）
    container = os.getenv("REDIS_CONTAINER", DEFAULT_REDIS_CONTAINER)
    backup_subdir = os.getenv("BACKUP_DIR", DEFAULT_BACKUP_SUBDIR)
    bgsave_timeout = int(os.getenv("BGSAVE_TIMEOUT", DEFAULT_BGSAVE_TIMEOUT))

    # 项目根目录
    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    logger.info("=" * 60)
    logger.info("Redis 备份开始")
    logger.info("  项目根目录: {}", project_root)
    logger.info("  Redis 容器: {}", container)
    logger.info("  备份目录:   {}/{}", project_root.name, backup_subdir)
    logger.info("  保留天数:   {}", args.keep_days)
    logger.info("  预览模式:   {}", args.dry_run)
    logger.info("=" * 60)

    if args.dry_run:
        logger.info("[dry-run] 将执行: BGSAVE → 复制 RDB/AOF → 清理 {} 天前的备份",
                    args.keep_days)
        return 0

    # 1. 触发 BGSAVE
    try:
        trigger_bgsave(container)
        wait_bgsave_done(container, bgsave_timeout)
    except Exception as exc:
        logger.error("BGSAVE 失败: {}", exc)
        return 1

    # 2. 准备备份目录和时间戳
    backup_dir = project_root / backup_subdir
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 3. 复制 RDB 文件
    rdb_backed = copy_from_container(
        container,
        "/data/dump.rdb",
        backup_dir / f"dump_{timestamp}.rdb",
    )

    # 4. 复制 AOF 文件
    aof_backed = copy_from_container(
        container,
        "/data/appendonly.aof",
        backup_dir / f"appendonly_{timestamp}.aof",
    )

    if not rdb_backed and not aof_backed:
        logger.error("没有备份任何文件，备份失败")
        return 1

    # 5. 清理过期备份
    deleted = cleanup_old_backups(backup_dir, args.keep_days)
    if deleted > 0:
        logger.info("已清理 {} 个过期备份文件", deleted)

    # 6. 统计
    backup_files = [f for f in backup_dir.iterdir() if f.is_file()]
    total_size = sum(f.stat().st_size for f in backup_files)
    logger.info("备份完成: {} 个文件，共 {:.2f} MB",
                len(backup_files), total_size / 1024 / 1024)

    return 0


if __name__ == "__main__":
    sys.exit(main())
