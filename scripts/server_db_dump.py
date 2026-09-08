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
  DB_ROOT_PASSWORD  MySQL root 密码（必填，无默认值）
  OUTPUT_FILE       输出文件名（默认 init_data.sql）
  REPO_PATH         项目根目录（默认自动检测为脚本上级目录）
  MEDIA_DIR         媒体目录（默认 cube_api/media）
  BACKUP_BRANCH     备份提交的目标分支（默认 dev）
  BACKUP_KEEP_COUNT 本地 SQL 备份保留份数（默认 7）
"""

import os
import sys
import subprocess
import datetime
import shutil
import time

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
DB_ROOT_PASSWORD = os.environ.get("DB_ROOT_PASSWORD", "")
OUTPUT_FILE      = os.environ.get("OUTPUT_FILE", "init_data.sql")
REPO_PATH        = os.path.abspath(os.environ.get("REPO_PATH", _PROJECT_ROOT))
MEDIA_DIR        = os.environ.get("MEDIA_DIR", "cube_api/media")
BACKUP_BRANCH    = os.environ.get("BACKUP_BRANCH", "dev")

DRY_RUN  = "--dry-run" in sys.argv
NO_PUSH  = "--no-push" in sys.argv
NO_MEDIA = "--no-media" in sys.argv

PUSH_MAX_RETRIES = 3
PUSH_RETRY_DELAY = 30  # 秒

BACKUP_KEEP_COUNT = int(os.environ.get("BACKUP_KEEP_COUNT", "7"))  # 保留最近几份 SQL 备份

LOG_DIR  = os.path.join(REPO_PATH, "logs")
LOG_FILE = os.path.join(LOG_DIR, f"server_dump_{datetime.datetime.now().strftime('%Y%m%d')}.log")
LOCK_FILE = os.path.join(LOG_DIR, "server_dump.lock")
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


def _acquire_lock():
    """获取文件锁，防止脚本重复执行。
    成功返回锁文件句柄（持有引用避免被 GC 释放），失败返回 None。
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    # 检查是否已有锁文件且进程存活
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r") as f:
                old_pid = f.read().strip()
            if old_pid and old_pid.isdigit():
                old_pid = int(old_pid)
                # 检查进程是否还在运行
                try:
                    os.kill(old_pid, 0)
                    logger.warning(f"检测到已有实例在运行 (PID={old_pid})，本次跳过")
                    return None
                except OSError:
                    # 进程不存在，锁过期，清理
                    logger.info(f"清理过期锁文件 (旧 PID={old_pid})")
                    os.remove(LOCK_FILE)
        except (IOError, ValueError):
            # 锁文件损坏，清理
            try:
                os.remove(LOCK_FILE)
            except OSError:
                pass

    # 创建新锁
    try:
        fd = open(LOCK_FILE, "w")
        fd.write(str(os.getpid()))
        fd.flush()
        return fd
    except IOError as e:
        logger.error(f"创建锁文件失败: {e}")
        return None


def _release_lock(lock_fd):
    """释放文件锁"""
    if lock_fd is None:
        return
    try:
        lock_fd.close()
        os.remove(LOCK_FILE)
    except OSError:
        pass


def _git_env():
    env = os.environ.copy()
    env.setdefault("GIT_TERMINAL_PROMPT", "0")
    env.setdefault("GIT_AUTHOR_NAME", "ICube Server")
    env.setdefault("GIT_AUTHOR_EMAIL", "icube@localhost")
    env.setdefault("GIT_COMMITTER_NAME", "ICube Server")
    env.setdefault("GIT_COMMITTER_EMAIL", "icube@localhost")
    return env


def _run(cmd, **kw):
    return subprocess.run(cmd, cwd=REPO_PATH, env=_git_env(),
                          capture_output=True, text=True, **kw)


def backup_original_file():
    out_path = os.path.join(REPO_PATH, OUTPUT_FILE)
    if not os.path.exists(out_path):
        return

    # 带时间戳的备份文件名
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = os.path.join(REPO_PATH, f"{OUTPUT_FILE}.backup_{ts}")
    shutil.copy2(out_path, bak)
    logger.info(f"已备份原文件: {bak}")

    # 清理旧备份，只保留最近 BACKUP_KEEP_COUNT 份
    import glob
    pattern = os.path.join(REPO_PATH, f"{OUTPUT_FILE}.backup_*")
    backups = sorted(glob.glob(pattern), reverse=True)
    if len(backups) > BACKUP_KEEP_COUNT:
        for old in backups[BACKUP_KEEP_COUNT:]:
            try:
                os.remove(old)
                logger.info(f"清理旧备份: {os.path.basename(old)}")
            except OSError as e:
                logger.warning(f"清理旧备份失败 {old}: {e}")


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

    result = _run(cmd, text=False)

    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace")
        logger.error(f"mysqldump 失败: {stderr}")
        return False

    sql_content = result.stdout.decode("utf-8", errors="replace")

    # 校验导出内容非空且包含有效 SQL
    stripped = sql_content.strip()
    if not stripped:
        logger.error("mysqldump 输出为空，拒绝写入文件")
        return False
    if "CREATE TABLE" not in stripped and "INSERT INTO" not in stripped:
        logger.error("mysqldump 输出未检测到表结构或数据，疑似导出失败")
        logger.error(f"输出前 500 字符: {stripped[:500]}")
        return False

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


def _save_orig_ref():
    """记录当前 HEAD 引用，返回 (ref_type, ref_value)
    ref_type: 'branch' 或 'detached'
    """
    # 先尝试获取分支名
    r = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    name = r.stdout.strip()
    if name and name != "HEAD":
        return ("branch", name)
    # detached HEAD，记录 commit hash
    r = _run(["git", "rev-parse", "HEAD"])
    return ("detached", r.stdout.strip())


def _restore_ref(ref_type, ref_value):
    """切回原始引用"""
    if ref_type == "branch":
        r = _run(["git", "checkout", ref_value])
        if r.returncode != 0:
            logger.error(f"切回原分支 {ref_value} 失败: {r.stderr.strip()}")
            return False
    else:
        r = _run(["git", "checkout", ref_value])
        if r.returncode != 0:
            logger.error(f"切回原 commit {ref_value} 失败: {r.stderr.strip()}")
            return False
    return True


def _ensure_backup_branch():
    """确保备份分支存在且与远端同步。
    切换到 BACKUP_BRANCH，失败则从远端创建，远端也没有则新建。
    返回 True 表示切换成功。
    """
    # 尝试直接切换到本地备份分支
    r = _run(["git", "checkout", BACKUP_BRANCH])
    if r.returncode == 0:
        logger.info(f"已切换到本地分支: {BACKUP_BRANCH}")
        # 尝试从远端同步（远端可能不存在，不存在也没关系）
        _git_pull_rebase(silent_on_no_remote=True)
        return True

    # 本地分支不存在，尝试从远端创建
    logger.info(f"本地分支 {BACKUP_BRANCH} 不存在，尝试从远端创建...")
    r = _run(["git", "fetch", "origin", BACKUP_BRANCH])
    if r.returncode == 0:
        r2 = _run(["git", "checkout", "-b", BACKUP_BRANCH, f"origin/{BACKUP_BRANCH}"])
        if r2.returncode == 0:
            logger.info(f"已从远端创建分支: {BACKUP_BRANCH}")
            return True
        logger.warning(f"从远端创建分支失败: {r2.stderr.strip()}")

    # 远端也没有，新建本地分支
    logger.info(f"远端也无 {BACKUP_BRANCH}，新建本地分支...")
    r = _run(["git", "checkout", "-b", BACKUP_BRANCH])
    if r.returncode == 0:
        logger.info(f"已新建分支: {BACKUP_BRANCH}")
        return True

    logger.error(f"无法创建或切换到分支 {BACKUP_BRANCH}: {r.stderr.strip()}")
    return False


def git_push():
    logger.info("正在提交并推送到远程仓库...")

    targets = [OUTPUT_FILE]
    if not NO_MEDIA:
        targets.append(MEDIA_DIR)

    # 记录当前引用（分支或 commit hash），提交后切回
    orig_ref_type, orig_ref = _save_orig_ref()
    on_backup_branch = (orig_ref_type == "branch" and orig_ref == BACKUP_BRANCH)

    # 切换到备份分支（main 受保护不能直接 push）
    if not on_backup_branch:
        logger.info(f"切换到备份分支: {BACKUP_BRANCH}")
        # 保存导出的文件内容（切换分支可能会覆盖已跟踪文件）
        out_path = os.path.join(REPO_PATH, OUTPUT_FILE)
        saved_content = None
        if os.path.isfile(out_path):
            with open(out_path, "r", encoding="utf-8") as f:
                saved_content = f.read()

        if not _ensure_backup_branch():
            logger.error("切换备份分支失败，终止推送")
            return False

        # 恢复导出的内容（untracked 的媒体文件不受 checkout 影响）
        if saved_content is not None:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(saved_content)

    if not DRY_RUN:
        for t in targets:
            r = _run(["git", "add", t])
            if r.returncode != 0:
                logger.warning(f"git add {t}: {r.stderr.strip()}")

    # 检查是否有变更
    r = _run(["git", "status", "--porcelain"] + targets)
    if not r.stdout.strip():
        logger.info("无变更，跳过提交")
        if not on_backup_branch:
            _restore_ref(orig_ref_type, orig_ref)
        return True

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_msg = f"server backup: {timestamp}"
    logger.info(f"提交: {commit_msg}")

    if DRY_RUN:
        logger.info("[DRY-RUN] 跳过 commit / push")
        if not on_backup_branch:
            _restore_ref(orig_ref_type, orig_ref)
        return True

    cr = _run(["git", "commit", "-m", commit_msg])
    if cr.returncode != 0:
        logger.error(f"git commit 失败: {cr.stderr.strip() or cr.stdout.strip()}")
        if not on_backup_branch:
            _restore_ref(orig_ref_type, orig_ref)
        return False

    commit_hash = _run(["git", "rev-parse", "--short", "HEAD"]).stdout.strip()
    logger.info(f"commit: {commit_hash}")

    if NO_PUSH:
        logger.info("--no-push，跳过推送")
        if not on_backup_branch:
            _restore_ref(orig_ref_type, orig_ref)
        return True

    # push 前先 pull --rebase，避免远端有新提交时冲突
    if not _git_pull_rebase():
        logger.warning("git pull --rebase 失败，仍尝试推送")

    # push，显式指定远端和分支，失败自动重试
    pr = None
    for attempt in range(1, PUSH_MAX_RETRIES + 1):
        pr = _run(["git", "push", "origin", BACKUP_BRANCH])
        if pr.returncode == 0:
            logger.info("成功推送到远程仓库")
            break

        logger.warning(f"第 {attempt} 次 push 失败: {pr.stderr.strip()}")

        if attempt < PUSH_MAX_RETRIES:
            logger.info(f"{PUSH_RETRY_DELAY} 秒后重试（{attempt}/{PUSH_MAX_RETRIES}）...")
            time.sleep(PUSH_RETRY_DELAY)
            # 重试前先同步远端
            _git_pull_rebase()
    else:
        logger.error(f"git push 失败，已重试 {PUSH_MAX_RETRIES} 次")

    # 切回原引用
    if not on_backup_branch:
        logger.info(f"切回原引用: {orig_ref}")
        _restore_ref(orig_ref_type, orig_ref)

    return pr is not None and pr.returncode == 0


def _git_pull_rebase(silent_on_no_remote=False):
    """git pull --rebase，显式指定远端和分支，同步远端最新提交。
    silent_on_no_remote: 远端分支不存在时只打 info 不打 warning。
    """
    logger.info(f"执行 git pull --rebase 同步远端 {BACKUP_BRANCH}...")
    r = _run(["git", "pull", "--rebase", "origin", BACKUP_BRANCH])
    if r.returncode == 0:
        logger.info("pull 成功")
        return True

    stderr = r.stderr.strip() or r.stdout.strip()

    # 远端分支不存在（首次推送前）
    if "couldn't find remote ref" in stderr or "fatal: couldn't find remote ref" in stderr:
        if silent_on_no_remote:
            logger.info(f"远端尚无 {BACKUP_BRANCH} 分支，首次推送将创建")
        else:
            logger.warning(f"远端尚无 {BACKUP_BRANCH} 分支")
        return False

    logger.warning(f"pull 失败: {stderr}")

    # 如果 rebase 冲突，中止 rebase 回到原状态
    if "rebase" in stderr.lower():
        _run(["git", "rebase", "--abort"])
        logger.warning("已中止 rebase，保留本地提交")
    return False


def main():
    _setup_logger()
    logger.info("=" * 60)
    logger.info("ICube 服务端数据库转储脚本（Docker mysqldump）")
    logger.info(f"REPO_PATH={REPO_PATH} | DB={DB_NAME}")
    logger.info(f"DRY_RUN={DRY_RUN} | NO_PUSH={NO_PUSH} | NO_MEDIA={NO_MEDIA}")
    logger.info("=" * 60)

    # 校验必要配置
    if not DB_ROOT_PASSWORD:
        logger.error("DB_ROOT_PASSWORD 未设置，请通过环境变量或 .env.backup 配置")
        return 1

    # 获取并发锁
    lock_fd = _acquire_lock()
    if lock_fd is None:
        logger.error("无法获取锁，退出")
        return 1

    try:
        # 检查 Docker 环境
        r = _run(["docker", "compose", "ps", "-q", "db"])
        if r.returncode != 0 or not r.stdout.strip():
            logger.error("未找到 db 容器，请在项目目录（含 docker-compose.yml）下运行")
            return 1

        # 1. 备份原文件
        if not DRY_RUN:
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
    finally:
        _release_lock(lock_fd)


if __name__ == "__main__":
    sys.exit(main())
