#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ICube 服务端数据库转储脚本

通过 Docker 中的 mysqldump 导出数据库结构和数据到 init_data.sql，
首行加上 USE 语句，并推送到 Git 远程仓库。

用法：
  python scripts/server_db_dump.py              # 导出 + 推送
  python scripts/server_db_dump.py --dry-run    # 预览不执行
  python scripts/server_db_dump.py --no-push    # 只导出不推送
  python scripts/server_db_dump.py --no-media   # 不提交媒体文件

环境变量（可通过 .env.backup 加载）：
  DB_NAME           数据库名（默认 icube_db）
  DB_ROOT_PASSWORD  MySQL root 密码（默认 icube_root123）
  OUTPUT_FILE       输出文件名（默认 init_data.sql）
  REPO_PATH         项目根目录（默认自动检测为脚本上级目录）
  MEDIA_DIR         媒体目录（默认 cube_api/media）
"""

import os
import sys
import subprocess
import datetime
import shutil

try:
    from loguru import logger
    _LOGURU = True
except ImportError:
    import logging
    _LOGURU = False
    logger = logging.getLogger("server_dump")
    if not logger.handlers:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        logger.addHandler(h)
    logger.setLevel(logging.INFO)

# 脚本位于 scripts/ 子目录，向上取一层得到项目根目录
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)

# ==================== 配置 ====================
DB_NAME          = os.environ.get("DB_NAME", "icube_db")
DB_ROOT_PASSWORD = os.environ.get("DB_ROOT_PASSWORD", "icube_root123")
OUTPUT_FILE      = os.environ.get("OUTPUT_FILE", "init_data.sql")
REPO_PATH        = os.path.abspath(os.environ.get("REPO_PATH", _PROJECT_ROOT))
MEDIA_DIR        = os.environ.get("MEDIA_DIR", "cube_api/media")

DRY_RUN  = "--dry-run" in sys.argv
NO_PUSH  = "--no-push" in sys.argv
NO_MEDIA = "--no-media" in sys.argv

LOG_DIR  = os.path.join(REPO_PATH, "logs")
LOG_FILE = os.path.join(LOG_DIR, f"server_dump_{datetime.datetime.now().strftime('%Y%m%d')}.log")
# =============================================


def _setup_logger():
    os.makedirs(LOG_DIR, exist_ok=True)
    if _LOGURU:
        try:
            logger.add(LOG_FILE, rotation="00:00", retention="30 days",
                       level="INFO", encoding="utf-8", enqueue=True)
        except Exception:
            pass
    else:
        try:
            fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
            fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
            logger.addHandler(fh)
        except Exception:
            pass


def _git_env():
    env = os.environ.copy()
    env.setdefault("GIT_TERMINAL_PROMPT", "0")
    return env


def _run(cmd, **kw):
    return subprocess.run(cmd, cwd=REPO_PATH, env=_git_env(),
                          capture_output=True, text=True, **kw)


def backup_original_file():
    out_path = os.path.join(REPO_PATH, OUTPUT_FILE)
    if os.path.exists(out_path):
        bak = f"{out_path}.backup"
        shutil.copy2(out_path, bak)
        logger.info(f"已备份原文件: {bak}")


def export_database():
    logger.info(f"正在导出数据库 {DB_NAME}（通过 Docker mysqldump）...")

    cmd = [
        "docker", "compose", "exec", "-T",
        "-e", f"MYSQL_PWD={DB_ROOT_PASSWORD}",
        "db",
        "mysqldump",
        "-uroot",
        "--opt",
        "--hex-blob",
        "--routines",
        "--triggers",
        "--set-charset",
        "--default-character-set=utf8mb4",
        DB_NAME,
    ]

    result = subprocess.run(cmd, cwd=REPO_PATH, capture_output=True)

    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace")
        logger.error(f"mysqldump 失败: {stderr}")
        return False

    sql_content = result.stdout.decode("utf-8", errors="replace")

    # 首行加上 USE 语句
    header = f"USE `{DB_NAME}`;\n"
    full_content = header + sql_content

    out_path = os.path.join(REPO_PATH, OUTPUT_FILE)

    if DRY_RUN:
        logger.info(f"[DRY-RUN] 跳过写入 {OUTPUT_FILE}（{len(full_content)} 字符）")
    else:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(full_content)
        size_kb = os.path.getsize(out_path) / 1024
        logger.info(f"导出成功: {OUTPUT_FILE}（{size_kb:.2f} KB）")

    return True


def git_push():
    logger.info("正在提交并推送到远程仓库...")

    targets = [OUTPUT_FILE]
    if not NO_MEDIA:
        targets.append(MEDIA_DIR)

    if not DRY_RUN:
        for t in targets:
            r = _run(["git", "add", t])
            if r.returncode != 0:
                logger.warning(f"git add {t}: {r.stderr.strip()}")

    # 检查是否有变更
    r = _run(["git", "status", "--porcelain"] + targets)
    if not r.stdout.strip():
        logger.info("无变更，跳过提交")
        return True

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_msg = f"server backup: {timestamp}"
    logger.info(f"提交: {commit_msg}")

    if DRY_RUN:
        logger.info("[DRY-RUN] 跳过 commit / push")
        return True

    cr = _run(["git", "commit", "-m", commit_msg])
    if cr.returncode != 0:
        logger.error(f"git commit 失败: {cr.stderr.strip() or cr.stdout.strip()}")
        return False

    commit_hash = _run(["git", "rev-parse", "--short", "HEAD"]).stdout.strip()
    logger.info(f"commit: {commit_hash}")

    if NO_PUSH:
        logger.info("--no-push，跳过推送")
        return True

    pr = _run(["git", "push"])
    if pr.returncode != 0:
        if "no upstream branch" in pr.stderr:
            pr2 = _run(["git", "push", "--set-upstream", "origin", "main"])
            if pr2.returncode != 0:
                logger.error(f"git push 失败: {pr2.stderr.strip()}")
                return False
        else:
            logger.error(f"git push 失败: {pr.stderr.strip()}")
            return False

    logger.info("成功推送到远程仓库")
    return True


def main():
    _setup_logger()
    logger.info("=" * 60)
    logger.info("ICube 服务端数据库转储脚本（Docker mysqldump）")
    logger.info(f"REPO_PATH={REPO_PATH} | DB={DB_NAME}")
    logger.info(f"DRY_RUN={DRY_RUN} | NO_PUSH={NO_PUSH} | NO_MEDIA={NO_MEDIA}")
    logger.info("=" * 60)

    # 检查 Docker 环境
    r = _run(["docker", "compose", "ps", "-q", "db"])
    if r.returncode != 0 or not r.stdout.strip():
        logger.error("未找到 db 容器，请在项目目录（含 docker-compose.yml）下运行")
        return 1

    # 1. 备份原文件
    backup_original_file()

    # 2. 导出
    ok = export_database()

    # 3. Git 提交 + 推送
    if ok:
        git_push()
    else:
        logger.warning("导出失败，跳过 Git 推送")

    logger.info("=" * 60)
    logger.info("完成！" if ok else "存在异常，请检查日志")
    logger.info("=" * 60)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
