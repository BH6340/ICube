# Redis RDB+AOF 混合持久化与备份 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 为 Redis 配置 RDB+AOF 混合持久化，并提供每日备份脚本，确保 Redis 数据在重启或故障时可恢复。

**架构：** 通过 docker-compose command 参数开启 AOF + RDB 混合持久化（`appendfsync everysec` + `aof-use-rdb-preamble yes`）；备份脚本通过 `docker exec` 触发 BGSAVE 后复制 RDB/AOF 文件到备份目录，保留 7 天。

**技术栈：** Redis 7-alpine、Docker Compose、Python 3（备份脚本）

---

## 文件清单

| 文件 | 操作 | 职责 |
|------|------|------|
| `docker-compose.yml` | 修改 | Redis 服务添加持久化配置 command |
| `scripts/redis_backup.py` | 新建 | Redis 备份主脚本（触发 BGSAVE → 复制文件 → 清理过期） |
| `scripts/redis_backup.sh` | 新建 | Shell 包装器，供 crontab 调用 |

---

### 任务 1：配置 Redis RDB+AOF 混合持久化

**文件：**
- 修改：`docker-compose.yml:40-52`

- [ ] **步骤 1：修改 docker-compose.yml 的 redis 服务，添加 command 字段**

将 `redis` 服务修改为：

```yaml
  redis:
    # 缓存、JWT 黑名单及 Session 存储
    image: redis:7-alpine
    container_name: icube_redis
    restart: always
    command: >
      redis-server
      --appendonly yes
      --appendfsync everysec
      --save 3600 1 300 100 60 10000
      --aof-use-rdb-preamble yes
      --auto-aof-rewrite-percentage 100
      --auto-aof-rewrite-min-size 64mb
    volumes:
      # 持久化 Redis 数据，避免容器重建后缓存数据立即丢失
      - redis_data:/data
    ports:
      # 允许宿主机调试 Redis；仅容器内部访问时可移除
      - "6379:6379"
    networks:
      - icube_network
```

**各参数说明：**
- `appendonly yes` — 开启 AOF 持久化
- `appendfsync everysec` — 每秒刷盘，最多丢 1 秒数据（性能与安全平衡）
- `save 3600 1 300 100 60 10000` — RDB 快照策略（Redis 默认值，显式声明便于运维）
- `aof-use-rdb-preamble yes` — 混合模式，AOF rewrite 时文件头用 RDB 格式
- `auto-aof-rewrite-percentage 100` — AOF 大小翻倍时自动 rewrite
- `auto-aof-rewrite-min-size 64mb` — rewrite 最小触发体积

- [ ] **步骤 2：本地验证 docker compose 配置语法**

运行：
```bash
cd /path/to/ICube
docker compose config
```

预期：无报错，输出中 redis 服务的 Command 包含 `--appendonly yes` 等参数。

- [ ] **步骤 3：提交**

```bash
git add docker-compose.yml
git commit -m "chore(redis): 开启 RDB+AOF 混合持久化

为 Redis 配置 AOF everysec + RDB 快照的混合持久化模式，
确保 JWT 黑名单、帖子浏览量等数据在容器重启后不丢失。"
```

---

### 任务 2：编写 Redis 备份脚本（Python）

**文件：**
- 新建：`scripts/redis_backup.py`

- [ ] **步骤 1：创建备份脚本 `scripts/redis_backup.py`**

脚本遵循项目现有 Python 脚本风格（参考 `server_db_dump.py`），包含：
- 日志输出（loguru）
- 触发 BGSAVE 并等待完成
- 复制 RDB + AOF 文件到备份目录
- 按保留天数清理旧备份
- 错误处理与退出码

完整代码：

```python
#!/usr/bin/env python3
# --------------------------------------------------------------
# Redis 备份脚本
# 触发 BGSAVE → 等待完成 → 复制 RDB/AOF 文件 → 清理过期备份
# 用法：
#   python scripts/redis_backup.py                 # 执行备份
#   python scripts/redis_backup.py --dry-run       # 预览不执行
#   python scripts/redis_backup.py --keep-days 7   # 指定保留天数（默认7天）
# --------------------------------------------------------------

import argparse
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from loguru import logger

# 容器名
REDIS_CONTAINER = "icube_redis"

# 容器内数据目录
CONTAINER_DATA_DIR = "/data"

# 本地备份目录（相对项目根的 data/redis_backup/）
BACKUP_SUBDIR = "data/redis_backup"

# 默认保留天数
DEFAULT_KEEP_DAYS = 7

# BGSAVE 等待超时（秒）
BGSAVE_TIMEOUT = 60


def _run(cmd: list[str], *, check: bool = True, capture: bool = True, text: bool = True) -> subprocess.CompletedProcess:
    """运行 shell 命令"""
    logger.debug("执行命令: {}", " ".join(cmd))
    return subprocess.run(
        cmd,
        check=check,
        capture_output=capture,
        text=text,
    )


def redis_cli(*args: str) -> str:
    """在 Redis 容器内执行 redis-cli 命令，返回 stdout"""
    result = _run(["docker", "exec", REDIS_CONTAINER, "redis-cli", *args])
    return result.stdout.strip()


def trigger_bgsave() -> None:
    """触发 BGSAVE"""
    output = redis_cli("BGSAVE")
    if "Background saving started" in output:
        logger.info("BGSAVE 已触发")
    else:
        raise RuntimeError(f"BGSAVE 触发失败: {output}")


def wait_bgsave_done(timeout: int = BGSAVE_TIMEOUT) -> None:
    """等待 BGSAVE 完成"""
    start = time.time()
    while time.time() - start < timeout:
        info = redis_cli("INFO", "persistence")
        for line in info.splitlines():
            if line.startswith("rdb_bgsave_in_progress:"):
                val = line.split(":")[1].strip()
                if val == "0":
                    logger.info("BGSAVE 完成")
                    return
        time.sleep(1)
    raise TimeoutError(f"BGSAVE 等待超时（{timeout}s）")


def get_backup_dir(project_root: Path) -> Path:
    """获取本地备份目录，不存在则创建"""
    backup_dir = project_root / BACKUP_SUBDIR
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def copy_from_container(container_path: str, local_path: Path) -> bool:
    """从容器复制文件到本地，文件不存在返回 False"""
    # 先检查文件是否存在
    result = _run(
        ["docker", "exec", REDIS_CONTAINER, "test", "-f", container_path],
        check=False,
        capture=True,
    )
    if result.returncode != 0:
        logger.warning("容器内文件不存在，跳过: {}", container_path)
        return False

    # 复制
    _run(["docker", "cp", f"{REDIS_CONTAINER}:{container_path}", str(local_path)])
    logger.info("已复制: {} → {}", container_path, local_path.name)
    return True


def cleanup_old_backups(backup_dir: Path, keep_days: int) -> int:
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Redis 备份脚本")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不执行实际操作")
    parser.add_argument("--keep-days", type=int, default=DEFAULT_KEEP_DAYS,
                        help=f"备份保留天数（默认 {DEFAULT_KEEP_DAYS} 天）")
    args = parser.parse_args()

    # 项目根目录
    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    logger.info("=" * 60)
    logger.info("Redis 备份开始")
    logger.info("  项目根目录: {}", project_root)
    logger.info("  保留天数: {}", args.keep_days)
    logger.info("  预览模式: {}", args.dry_run)
    logger.info("=" * 60)

    if args.dry_run:
        logger.info("[dry-run] 将执行: BGSAVE → 复制 RDB/AOF → 清理 {} 天前的备份", args.keep_days)
        return 0

    # 1. 触发 BGSAVE
    try:
        trigger_bgsave()
        wait_bgsave_done()
    except Exception as exc:
        logger.error("BGSAVE 失败: {}", exc)
        return 1

    # 2. 准备备份目录和时间戳
    backup_dir = get_backup_dir(project_root)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 3. 复制 RDB 文件
    rdb_backed = copy_from_container(
        f"{CONTAINER_DATA_DIR}/dump.rdb",
        backup_dir / f"dump_{timestamp}.rdb",
    )

    # 4. 复制 AOF 文件（如果开启了 AOF）
    aof_backed = copy_from_container(
        f"{CONTAINER_DATA_DIR}/appendonly.aof",
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
    backup_files = list(backup_dir.iterdir())
    total_size = sum(f.stat().st_size for f in backup_files if f.is_file())
    logger.info("备份完成: {} 个文件，共 {:.2f} MB",
                len(backup_files), total_size / 1024 / 1024)

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **步骤 2：确认脚本可执行**

```bash
chmod +x scripts/redis_backup.py
```

（Windows 本地开发不需要此步骤，服务器上需要）

- [ ] **步骤 3：预览模式验证**

```bash
python scripts/redis_backup.py --dry-run
```

预期：输出预览信息，退出码 0，不实际操作。

- [ ] **步骤 4：提交**

```bash
git add scripts/redis_backup.py
git commit -m "feat(redis): 新增 Redis 备份脚本

支持 BGSAVE 触发、RDB/AOF 文件备份、按天清理过期备份，
与数据库备份脚本风格一致，可通过 crontab 每日调度。"
```

---

### 任务 3：编写 Shell 包装器（供 crontab 调用）

**文件：**
- 新建：`scripts/redis_backup.sh`

- [ ] **步骤 1：创建 `scripts/redis_backup.sh`**

参考 `scripts/server_backup.sh` 的风格：

```bash
#!/usr/bin/env bash
# --------------------------------------------------------------
# ICube Redis 备份脚本（crontab 入口）
# 用法：每天凌晨 3 点执行
#   0 3 * * * /opt/icube/scripts/redis_backup.sh >> /opt/icube/logs/redis-backup-cron.log 2>&1
# --------------------------------------------------------------
set -eu

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR" || exit 1

mkdir -p "$PROJECT_DIR/logs"

# 找 Python 解释器
PYTHON_BIN=""
if [ -x "$PROJECT_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python)"
else
    echo "[$(date '+%F %T')] 找不到 python 解释器" >> "$PROJECT_DIR/logs/redis-backup-cron.log"
    exit 1
fi

# 加载 .env（如存在）
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    . "$PROJECT_DIR/.env"
    set +a
fi

echo ""
echo "============================================================"
echo "[$(date '+%F %T')] Redis 备份开始 @ $(hostname)"
echo "  PROJECT_DIR = $PROJECT_DIR"
echo "  PYTHON_BIN  = $PYTHON_BIN"
echo "============================================================"

RC=0
"$PYTHON_BIN" "$PROJECT_DIR/scripts/redis_backup.py" || RC=$?

if [ "$RC" -eq 0 ]; then
    echo "[$(date '+%F %T')] Redis 备份成功 (exit=0)"
else
    echo "[$(date '+%F %T')] Redis 备份失败 (exit=$RC)"
fi

exit $RC
```

- [ ] **步骤 2：确认脚本可执行**

```bash
chmod +x scripts/redis_backup.sh
```

- [ ] **步骤 3：提交**

```bash
git add scripts/redis_backup.sh
git commit -m "chore(redis): 新增 Redis 备份 shell 包装器

供 crontab 调度，与 server_backup.sh 风格一致。"
```

---

### 任务 4：更新 .gitignore（忽略 Redis 备份文件）

**文件：**
- 修改：`.gitignore`

- [ ] **步骤 1：在 .gitignore 中添加 Redis 备份目录规则**

找到 data 相关的忽略规则附近，添加：

```
# Redis 备份文件
data/redis_backup/
```

- [ ] **步骤 2：验证**

```bash
git check-ignore -v data/redis_backup/dump_20260101_000000.rdb
```

预期：输出匹配的 .gitignore 规则。

- [ ] **步骤 3：提交**

```bash
git add .gitignore
git commit -m "chore: 忽略 Redis 备份文件目录"
```

---

### 任务 5：更新修改日志

**文件：**
- 修改：`docs/修改日志.md`

- [ ] **步骤 1：在「工程与部署」分类下添加记录**

```
## 工程与部署

### 2026-11-06 Redis 持久化与备份

- **修改时间**：2026-11-06
- **修改内容**：
  1. Redis 开启 RDB + AOF 混合持久化（appendfsync everysec）
  2. 新增 Redis 备份脚本（scripts/redis_backup.py + redis_backup.sh），每日备份 RDB/AOF 文件，保留 7 天
- **修改原因**：原 Redis 仅靠 RDB 默认快照，JWT 黑名单和帖子浏览量在崩溃时可能丢失较多数据；AOF everysec 将丢失控制在 1 秒内；备份脚本用于应对磁盘损坏等极端情况
- **影响范围**：后端（Redis 配置）、运维脚本
```

- [ ] **步骤 2：提交**

```bash
git add docs/修改日志.md
git commit -m "docs: 更新 Redis 持久化与备份修改日志"
```

---

### 任务 6：服务器部署验证

**说明：** 此任务在服务器上手动执行，或通过 CI/CD 自动完成。

- [ ] **步骤 1：拉取最新代码并重启 Redis**

```bash
cd /opt/icube
git pull
docker compose up -d redis
```

- [ ] **步骤 2：验证 AOF 已开启**

```bash
docker exec icube_redis redis-cli INFO persistence | grep aof_enabled
```

预期：输出 `aof_enabled:1`

- [ ] **步骤 3：验证 appendfsync 配置**

```bash
docker exec icube_redis redis-cli CONFIG GET appendfsync
```

预期：输出 `everysec`

- [ ] **步骤 4：验证 AOF 文件已生成**

```bash
docker exec icube_redis ls -la /data/appendonly.aof
```

预期：文件存在且大小 > 0

- [ ] **步骤 5：验证 RDB 快照正常**

```bash
docker exec icube_redis redis-cli LASTSAVE
```

预期：返回一个 Unix 时间戳（最近一次 RDB 保存时间）

- [ ] **步骤 6：手动执行一次备份脚本验证**

```bash
bash scripts/redis_backup.sh
```

预期：备份成功，`data/redis_backup/` 目录下生成 `dump_*.rdb` 和 `appendonly_*.aof` 文件

- [ ] **步骤 7：配置 crontab 每日执行**

```bash
crontab -e
# 添加：
# 0 3 * * * /opt/icube/scripts/redis_backup.sh >> /opt/icube/logs/redis-backup-cron.log 2>&1
```

---

## 回滚方案

如果持久化配置有问题导致 Redis 无法启动：

1. 移除 `docker-compose.yml` 中 redis 服务的 `command` 字段
2. 执行 `docker compose up -d redis`
3. Redis 会用默认 RDB 模式启动，数据不受影响（AOF 文件仍保留在卷中）

如果备份脚本有问题：
- 删除脚本文件即可，不影响 Redis 正常运行
