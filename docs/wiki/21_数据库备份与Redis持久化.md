# 21. 数据库备份与 Redis 持久化

## 1. 概述

### 1.1 为什么需要备份与持久化

ICube 是有状态的 Web 应用，核心数据存放在 MySQL（业务数据）和 Redis（缓存 + 会话 + 黑名单）中。任何一次磁盘故障、误操作、容器损坏都可能导致数据丢失。备份与持久化是数据安全的最后一道防线。

**常见风险场景**：

| 场景 | 后果 | 应对 |
|------|------|------|
| 误删数据（DROP TABLE / DELETE 漏写 WHERE） | 业务数据丢失 | MySQL 定时备份 + 恢复 |
| 服务器磁盘故障 | 全部数据丢失 | 备份文件（与数据盘分离） |
| Docker 容器损坏 / 误删 | 容器内数据丢失 | Docker 命名卷 + 卷外备份 |
| Redis 进程崩溃 / 重启 | 内存数据全丢 | Redis 持久化（RDB + AOF） |
| Redis 数据误操作（FLUSHALL） | 缓存/会话清空 | Redis 备份文件回滚 |

### 1.2 RPO / RTO 目标

| 指标 | 含义 | 当前目标 |
|------|------|---------|
| **RPO**（Recovery Point Objective） | 最多能接受丢多久的数据 | MySQL：24 小时；Redis：1 秒（AOF everysec） |
| **RTO**（Recovery Time Objective） | 恢复服务需要多久 | 30 分钟内 |

### 1.3 当前数据资产盘点

**MySQL（icube_db）**：
- 用户表、帖子、评论、公式、订单、计时器记录等核心业务数据
- 数据量：约几十 MB ~ 几百 MB（小中型项目）

**Redis**：
- JWT 黑名单（access + refresh）
- 用户实例缓存（`user_instance_cache_{id}`）
- 多端登录会话（`user:{id}:sessions` ZSet）
- 登录限流计数
- 帖子 / 公式浏览量缓存
- 关注 / 粉丝数缓存

---

## 2. MySQL 数据库备份

### 2.1 备份方案对比

| 方案 | 原理 | 优点 | 缺点 | 适用场景 |
|------|------|------|------|---------|
| **逻辑备份（mysqldump）** | 导出 SQL 语句文本 | 文件小、可读、跨版本、跨平台、可单表恢复 | 大库恢复慢、锁表（MyISAM） | 小中型库（当前项目适用） |
| **物理备份（xtrabackup）** | 直接复制数据文件 | 恢复快、不锁表（InnoDB） | 文件大、同版本、操作复杂 | 大型库、TB 级 |
| **Docker 卷备份** | 复制 mysql_data 命名卷 | 操作简单、完整一致 | 需停库、文件大 | 全量迁移、灾难恢复 |

当前项目数据量小，**mysqldump 逻辑备份**完全够用，且灵活度高。

### 2.2 mysqldump 逻辑备份原理

#### 工作机制

`mysqldump` 通过连接 MySQL 服务器，逐表读取数据并生成 `CREATE TABLE` + `INSERT` 语句，输出为 SQL 文本文件。

#### 一致性与锁行为

| 引擎 | 锁行为 | 一致性保证 |
|------|--------|-----------|
| **MyISAM** | 全程锁表（`LOCK TABLES READ`） | 读锁期间无法写入，保证一致性 |
| **InnoDB** | `--single-transaction` 开启事务快照 | 利用 MVCC，读一致性数据，**不锁表**，不阻塞写入 |

本项目用的是 **InnoDB**（Django 默认），所以使用 `--single-transaction` 参数在不锁表的前提下获得一致性备份。

#### 常用关键参数

| 参数 | 作用 |
|------|------|
| `--single-transaction` | InnoDB 一致性读，不锁表 |
| `--routines` | 导出存储过程和函数 |
| `--triggers` | 导出触发器 |
| `--quick` | 逐行读取，不缓存整个表到内存，适合大表 |
| `--default-character-set=utf8mb4` | 指定字符集，避免乱码 |

### 2.3 现有备份脚本

项目已有两套 MySQL 备份脚本，分别用于不同场景：

#### server_db_dump.py（[scripts/server_db_dump.py](file:///e:/BH/PyStudy/ICube/scripts/server_db_dump.py)）

**用途**：服务端生产环境数据库全量导出，导出为 `init_data.sql` 并自动提交到 Git 仓库。

**功能**：
- 通过 `docker compose exec db mysqldump` 导出数据库
- 首行自动加上 `USE icube_db;`
- 自动 `git add / commit / push` 到远程仓库
- push 失败自动重试 3 次，每次间隔 30 秒
- 支持 `--dry-run`（预览）、`--no-push`（只导出不推送）、`--no-media`（不提交媒体文件）

#### server_backup.sh（[scripts/server_backup.sh](file:///e:/BH/PyStudy/ICube/scripts/server_backup.sh)）

**用途**：Shell 包装器，供 crontab 定时调度调用 `server_db_dump.py`。

```bash
bash scripts/server_backup.sh
```

### 2.4 定时任务配置

当前 crontab 配置（每天 22:00 执行）：

```bash
0 22 * * * /home/bh/ICube/scripts/server_backup.sh >> /home/bh/ICube/logs/server-backup-cron.log 2>&1
```

各字段含义：

```
┌───────── 分钟 (0-59)
│ ┌─────── 小时 (0-23)
│ │ ┌───── 日 (1-31)
│ │ │ ┌─── 月 (1-12)
│ │ │ │ ┌─ 星期 (0-7, 0和7都是周日)
│ │ │ │ │
0 22 * * *
```

### 2.5 备份保留策略

| 备份类型 | 频率 | 保留天数 | 存储位置 |
|---------|------|---------|---------|
| MySQL 全量 | 每日 22:00 | 7 天 | Git 仓库（init_data.sql 历史版本）+ 服务器本地 |
| Redis RDB | 每日 03:00 | 7 天 | `data/redis_backup/` |
| Redis AOF | 每日 03:00 | 7 天 | `data/redis_backup/` |

> **说明**：MySQL 备份通过 Git 管理，天然有版本历史；Redis 备份通过脚本自动清理 7 天前的文件。

### 2.6 备份压缩

MySQL 备份文件（`init_data.sql`）是纯文本，压缩比很高（通常能压到原大小的 10%~20%）。Git 底层已做压缩存储，无需额外 gzip。

如果需要手动压缩：

```bash
# 压缩
gzip init_data.sql

# 解压
gunzip init_data.sql.gz
```

---

## 3. Redis 持久化原理

### 3.1 为什么 Redis 需要持久化

Redis 是**内存数据库**，所有数据存在 RAM 中。优点是快，缺点是：

- **进程退出数据丢失**：Redis 进程崩溃 / 服务器重启 → 内存清空
- **容器重建数据丢失**：Docker 容器删除重建 → 数据没了（除非挂载了卷）

持久化就是把内存数据**写到磁盘**上，重启后从磁盘加载恢复。

Redis 提供了 **RDB**、**AOF**、**混合持久化** 三种方式。

### 3.2 RDB 持久化原理

**RDB**（Redis DataBase）：在某个时间点，把内存中的数据拍一张"快照"，存为 `.rdb` 二进制文件。

#### 触发时机

| 触发方式 | 说明 |
|---------|------|
| **手动触发** | `SAVE`（阻塞式，慎用） / `BGSAVE`（后台异步，推荐） |
| **自动触发** | `save <seconds> <changes>` 配置规则，如 `save 3600 1` 表示 3600 秒内至少 1 次写操作就触发 |
| **shutdown 时** | 正常关闭 Redis 前自动执行一次 RDB |
| **主从复制时** | 从节点全量复制时，主节点会 BGSAVE 生成 RDB 发给从节点 |
| **DEBUG RELOAD** | 调试用，先清空再加载 RDB |

#### fork + COW（写时复制）机制

`BGSAVE` 不是直接把内存数据写到磁盘——那样会阻塞所有写操作。它用的是操作系统的 **fork + COW（Copy-On-Write，写时复制）** 技术：

```
1. Redis 主进程调用 fork() 创建子进程
2. 子进程共享父进程的内存页（此时不复制数据）
3. 子进程遍历内存，把数据写入 RDB 文件
4. 期间如果父进程有写操作 → 复制被修改的那一页（COW），父子各持一份
5. 子进程写完 RDB 后退出，通知主进程
```

**关键点**：
- fork 瞬间是阻塞的，但通常很快（毫秒级）
- 子进程写 RDB 期间，父进程继续正常服务
- 内存占用峰值 = 原内存 + 修改过的页面（不是翻倍）

#### RDB 文件格式

二进制格式，包含：
- 文件头（魔数 "REDIS" + 版本号）
- 元数据（Redis 版本、生成时间、内存大小等）
- 数据库数据（键值对 + 过期时间 + 类型编码）
- 校验和（CRC64）

文件体积小，加载速度快。

#### RDB 的优缺点

| 优点 | 缺点 |
|------|------|
| 文件紧凑，适合备份和传输 | 最后一次快照到宕机之间的数据**会丢失** |
| 恢复速度快（直接加载二进制） | fork 有性能开销，大数据量时 fork 耗时长 |
| 对性能影响小（子进程写盘，父进程不阻塞） | 频繁写的场景下 RDB 文件频繁变化 |

### 3.3 AOF 持久化原理

**AOF**（Append Only File）：把每一条**写命令**都追加到日志文件末尾，重启时按顺序重放所有命令来恢复数据。

#### 命令追加机制

```
客户端执行 SET key value
  → Redis 执行命令，修改内存
  → 命令追加到 AOF 缓冲区（aof_buf）
  → 根据刷盘策略，缓冲区内容写入磁盘
```

#### 三种刷盘策略（appendfsync）

| 策略 | 行为 | 安全性 | 性能 | 适用场景 |
|------|------|--------|------|---------|
| **always** | 每条命令都 fsync 刷盘 | 最高（最多丢 1 条） | 最差 | 金融级，数据绝对不能丢 |
| **everysec**（默认） | 每秒刷一次盘 | 高（最多丢 1 秒） | 好 | 大多数场景的最佳选择 |
| **no** | 由操作系统决定何时刷盘 | 低（可能丢几秒~几十秒） | 最好 | 对数据丢失不敏感 |

本项目用的是 **everysec**，在性能和安全之间取平衡。

#### AOF 重写原理

AOF 文件会越来越大（每条写命令都追加），需要定期"瘦身"——这就是 **AOF 重写（BGREWRITEAOF）**。

**重写做了什么**：
- 不读旧 AOF，直接扫描当前内存中的数据
- 为每个键生成一条最精简的命令（比如把 100 次 LPUSH 合并成一条 LPUSH + 100 个元素）
- 写入新的 AOF 文件，替换旧文件

**重写触发条件**：
- 手动：`BGREWRITEAOF` 命令
- 自动：`auto-aof-rewrite-percentage`（AOF 文件增长百分比）+ `auto-aof-rewrite-min-size`（最小触发体积）

本项目配置：`auto-aof-rewrite-percentage 100` + `auto-aof-rewrite-min-size 64mb`——即 AOF 文件比上次重写时大一倍，且超过 64MB 时自动触发重写。

#### Redis 7.x 的 Multi-Part AOF

Redis 7.0 引入了 **multi-part AOF** 机制，AOF 不再是单个文件，而是一个目录 `appendonlydir/`：

| 文件 | 作用 |
|------|------|
| `appendonly.aof.manifest` | 清单文件，记录 base 和 incr 文件列表 |
| `appendonly.aof.N.base.rdb` | base 文件（RDB 格式，混合持久化的基础） |
| `appendonly.aof.N.incr.aof` | 增量文件（AOF 格式，记录 base 之后的写命令） |

好处：重写时不需要整体重写，只需生成新的 base + incr，减少磁盘 IO。

#### AOF 的优缺点

| 优点 | 缺点 |
|------|------|
| 数据更安全（everysec 最多丢 1 秒） | AOF 文件通常比 RDB 大很多 |
| 写入是追加操作，不会损坏已有数据 | 恢复速度慢（逐条重放命令） |
| AOF 重写不影响正常服务 | 写放大（每条写命令都要写盘） |

### 3.4 RDB + AOF 混合持久化

**混合持久化**（`aof-use-rdb-preamble yes`）：AOF 重写时，把重写这一刻的数据以 **RDB 格式**写入 AOF 文件开头，之后的增量命令继续以 AOF 格式追加。

```
AOF 文件结构（混合模式）：
┌──────────────┬──────────────────────┐
│   RDB 数据    │   AOF 增量命令       │
│  (base部分)   │  (incr部分)          │
└──────────────┴──────────────────────┘
```

**恢复时**：先加载 RDB 部分（快），再重放后面的 AOF 增量命令（少）。

**优势**：
- 结合了 RDB 的恢复速度 和 AOF 的数据安全性
- 文件体积比纯 AOF 小
- Redis 7.x multi-part AOF 天然支持（base 文件就是 RDB 格式）

**本项目配置**：已开启混合持久化（`aof-use-rdb-preamble yes`）。

### 3.5 持久化对性能的影响分析

| 操作 | 对性能的影响 | 频率 |
|------|-------------|------|
| RDB fork | fork 瞬间阻塞（毫秒级~秒级，取决于内存大小） | 每小时 / 每天 |
| RDB 子进程写盘 | 消耗 CPU 和 IO，但不阻塞主进程 | 每次 BGSAVE |
| AOF 写入缓冲区 | 极快，内存操作 | 每次写命令 |
| AOF 每秒刷盘 | IO 操作，影响很小 | 每秒 |
| AOF 重写 fork | 同 RDB，fork 瞬间阻塞 | 自动触发（体积翻倍时） |
| AOF 重写子进程 | 消耗 CPU + IO，扫描全量内存 | 每次重写 |

**面试要点**：
- Redis 持久化不是"零成本"的，写密集场景下需要权衡
- fork 的开销和内存大小正相关，内存越大 fork 越慢
- AOF everysec 是性能和安全的最佳平衡点，绝大多数场景都用这个
- 混合持久化是 Redis 4.0 以后的标配，兼顾了 RDB 的快和 AOF 的稳

---

## 4. Redis 备份实践

### 4.1 当前项目 Redis 配置

摘自 [docker-compose.yml](file:///e:/BH/PyStudy/ICube/docker-compose.yml#L48-L55)：

```yaml
command: >
  redis-server
  --appendonly yes                  # 开启 AOF
  --appendfsync everysec            # 每秒刷盘
  --save 3600 1 300 100 60 10000    # RDB 自动触发规则
  --aof-use-rdb-preamble yes        # 混合持久化
  --auto-aof-rewrite-percentage 100 # AOF 重写触发：增长 100%
  --auto-aof-rewrite-min-size 64mb  # AOF 重写触发：最小 64MB
```

**RDB 自动触发规则说明**（三条满足任一就触发 BGSAVE）：
- `3600 1`：3600 秒内至少 1 次写操作
- `300 100`：300 秒内至少 100 次写操作
- `60 10000`：60 秒内至少 10000 次写操作

### 4.2 备份方式对比

| 方式 | 原理 | 优点 | 缺点 | 适合场景 |
|------|------|------|------|---------|
| **BGSAVE + 复制 RDB** | 触发 BGSAVE，完成后复制 dump.rdb | 文件小、恢复快 | 只能恢复到快照时刻 | 日常备份（当前使用） |
| **复制 AOF** | 复制 appendonlydir/ 目录 | 数据更全 | 文件大、恢复慢 | 数据安全要求高 |
| **RDB + AOF 都备份** | 两种都复制 | 最安全 | 占用空间多 | 生产环境推荐（当前使用） |

本项目两种都备份，RDB 用于快速恢复，AOF 用于精确恢复。

### 4.3 Redis 备份脚本

#### redis_backup.py（[scripts/redis_backup.py](file:///e:/BH/PyStudy/ICube/scripts/redis_backup.py)）

**功能**：
1. 触发 BGSAVE，等待完成（轮询 `INFO persistence` 检查 `rdb_bgsave_in_progress`）
2. 复制 `dump.rdb` 到本地备份目录，命名为 `dump_YYYYMMDD_HHMMSS.rdb`
3. 备份 AOF 文件（兼容 Redis 7.x multi-part 格式，打包为 `aof_YYYYMMDD_HHMMSS.tar.gz`）
4. 自动清理超过保留天数的备份文件

**用法**：

```bash
# 执行备份（默认保留 7 天）
python scripts/redis_backup.py

# 预览模式
python scripts/redis_backup.py --dry-run

# 指定保留天数
python scripts/redis_backup.py --keep-days 7
```

**环境变量**：

| 变量 | 作用 | 默认值 |
|------|------|--------|
| `REDIS_CONTAINER` | Redis 容器名 | `icube_redis` |
| `BACKUP_DIR` | 备份目录（相对项目根） | `data/redis_backup` |
| `BGSAVE_TIMEOUT` | BGSAVE 等待超时秒数 | `60` |

#### redis_backup.sh（[scripts/redis_backup.sh](file:///e:/BH/PyStudy/ICube/scripts/redis_backup.sh)）

Shell 包装器，供 crontab 调用：

```bash
bash scripts/redis_backup.sh
```

#### crontab 配置（每天凌晨 3 点）：

```bash
0 3 * * * /opt/icube/scripts/redis_backup.sh >> /opt/icube/logs/redis-backup-cron.log 2>&1
```

### 4.4 备份保留策略

- **保留天数**：7 天（默认，可通过 `--keep-days` 修改）
- **清理机制**：每次备份完成后自动清理过期文件
- **匹配规则**：`dump_*.rdb` 和 `aof_*.tar.gz` 文件

---

## 5. Docker 卷备份

### 5.1 命名卷备份原理

Docker 命名卷（named volume）的数据存放在宿主机的 Docker 管理目录下（`/var/lib/docker/volumes/`），不建议直接操作。标准做法是：**启动一个临时容器，挂载卷 + 挂载宿主机目录，在容器内打包复制**。

### 5.2 mysql_data 卷备份

```bash
# 备份：将 mysql_data 卷打包到当前目录
docker run --rm \
  -v icube_mysql_data:/data \
  -v $(pwd):/backup \
  alpine \
  tar czf /backup/mysql_data_$(date +%Y%m%d).tar.gz -C /data .

# 恢复：从备份文件恢复到 mysql_data 卷
docker run --rm \
  -v icube_mysql_data:/data \
  -v $(pwd):/backup \
  alpine \
  tar xzf /backup/mysql_data_YYYYMMDD.tar.gz -C /data
```

### 5.3 redis_data 卷备份

```bash
# 备份
docker run --rm \
  -v icube_redis_data:/data \
  -v $(pwd):/backup \
  alpine \
  tar czf /backup/redis_data_$(date +%Y%m%d).tar.gz -C /data .

# 恢复
docker run --rm \
  -v icube_redis_data:/data \
  -v $(pwd):/backup \
  alpine \
  tar xzf /backup/redis_data_YYYYMMDD.tar.gz -C /data
```

> **注意**：卷备份前建议先停止对应容器，保证数据一致性。MySQL 卷备份前停 db 容器，Redis 卷备份前停 redis 容器。

---

## 6. 备份恢复流程

### 6.1 MySQL 完整恢复

**场景**：数据库损坏 / 误删全库 / 服务器迁移

```bash
# 1. 确保容器在运行
docker compose up -d db

# 2. 找到要恢复的 init_data.sql（从 Git 历史或备份文件）
git log --oneline -- init_data.sql  # 查看历史版本
git show <commit>:init_data.sql > /tmp/restore.sql

# 3. 导入备份
docker compose exec -T db mysql -uroot -p$MYSQL_ROOT_PASSWORD icube_db < /tmp/restore.sql
```

### 6.2 MySQL 单表恢复

**场景**：误删某张表的数据，不想全库回滚

```bash
# 方法一：从全量备份中提取单表（需要先全量导入临时库再导出单表）

# 方法二：用 grep 提取建表+数据（适合小表）
grep -E '(CREATE TABLE.*`表名`|INSERT INTO.*`表名`)' init_data.sql > table_restore.sql
docker compose exec -T db mysql -uroot -p$MYSQL_ROOT_PASSWORD icube_db < table_restore.sql
```

### 6.3 MySQL 恢复验证

```bash
# 检查库是否存在
docker compose exec db mysql -uicube_api -picube123 -e "SHOW DATABASES;"

# 检查表数量
docker compose exec db mysql -uicube_api -picube123 icube_db -e "SHOW TABLES;" | wc -l

# 抽查关键表数据量
docker compose exec db mysql -uicube_api -picube123 icube_db -e "SELECT COUNT(*) FROM accounts_user;"
docker compose exec db mysql -uicube_api -picube123 icube_db -e "SELECT COUNT(*) FROM forum_post;"
```

### 6.4 Redis RDB 恢复

**场景**：Redis 数据损坏 / 误操作 FLUSHALL / 容器数据丢失，能接受丢失到上次快照的数据

```bash
# 1. 停止 Redis
docker compose stop redis

# 2. 备份当前数据（防止恢复失败）
docker cp icube_redis:/data/dump.rdb ./dump.rdb.bak

# 3. 复制备份 RDB 到容器内（替换原文件）
docker cp ./data/redis_backup/dump_YYYYMMDD_HHMMSS.rdb icube_redis:/data/dump.rdb

# 4. 如果 AOF 开着，需要先临时关闭 AOF 配置，否则 Redis 会优先加载 AOF
#    方法：修改 docker-compose.yml 中 --appendonly 为 no，重启后再改回来
#    或者：在容器内重命名 AOF 目录（不推荐）

# 5. 启动 Redis
docker compose start redis
```

### 6.5 Redis AOF 恢复

**场景**：需要精确恢复到某个时间点，不能接受数据丢失

```bash
# 1. 停止 Redis
docker compose stop redis

# 2. 找到 AOF 备份并解压
tar xzf aof_YYYYMMDD_HHMMSS.tar.gz -C /tmp/

# 3. 复制到容器
docker cp /tmp/appendonlydir icube_redis:/data/appendonlydir

# 4. 启动 Redis
docker compose start redis

# 5. 查看日志确认加载正常
docker compose logs redis
```

### 6.6 Redis 恢复验证

```bash
# 检查 key 总数
docker compose exec redis redis-cli DBSIZE

# 抽查关键数据
docker compose exec redis redis-cli GET "user_instance_cache_1"
docker compose exec redis redis-cli ZCARD "user:1:sessions"
```

---

## 7. 备份监控与告警

### 7.1 备份结果检查

**检查方式**：
1. **日志文件**：`logs/server-backup-cron.log`、`logs/redis-backup-cron.log`
2. **备份文件存在性**：检查当天是否有新的备份文件生成
3. **备份文件大小**：异常小（0KB）可能表示备份失败
4. **Git 提交记录**：MySQL 备份推送是否成功

### 7.2 失败告警

可通过以下方式在备份失败时收到通知：

| 方式 | 说明 |
|------|------|
| **Server酱** | 微信推送，免费版每天 5 条，适合关键告警 |
| **邮件** | 详细日志，适合存档 |
| **Uptime Kuma** | Push 监控，每天推送一次心跳，超时未推送则告警 |

> 目前监控脚本体系（`scripts/monitoring/`）已有邮件告警能力，后续可接入备份监控。

### 7.3 备份大小趋势监控

定期关注备份文件大小变化，如果突然增大或减小，可能意味着数据异常：

- **突然增大**：可能是批量导入数据 / 图片写入数据库
- **突然减小**：可能是误删数据 / 备份脚本异常

---

## 8. 操作速查

### 8.1 手动备份命令

```bash
# ===== MySQL =====
# 完整备份（导出到 init_data.sql + git push）
bash scripts/server_backup.sh

# 预览不执行
python scripts/server_db_dump.py --dry-run

# 只导出不推送
python scripts/server_db_dump.py --no-push

# ===== Redis =====
# 完整备份（RDB + AOF）
bash scripts/redis_backup.sh

# 预览模式
python scripts/redis_backup.py --dry-run

# 指定保留天数
python scripts/redis_backup.py --keep-days 7

# ===== Docker 卷 =====
# MySQL 卷备份
docker run --rm -v icube_mysql_data:/data -v $(pwd):/backup alpine tar czf /backup/mysql_data_$(date +%Y%m%d).tar.gz -C /data .

# Redis 卷备份
docker run --rm -v icube_redis_data:/data -v $(pwd):/backup alpine tar czf /backup/redis_data_$(date +%Y%m%d).tar.gz -C /data .
```

### 8.2 手动恢复命令

```bash
# ===== MySQL =====
# 完整恢复
docker compose exec -T db mysql -uroot -p$MYSQL_ROOT_PASSWORD icube_db < init_data.sql

# ===== Redis RDB =====
docker compose stop redis
docker cp dump_YYYYMMDD_HHMMSS.rdb icube_redis:/data/dump.rdb
docker compose start redis

# ===== Redis AOF =====
docker compose stop redis
tar xzf aof_YYYYMMDD_HHMMSS.tar.gz
docker cp appendonlydir icube_redis:/data/
docker compose start redis
```

### 8.3 常用排查命令

```bash
# ===== MySQL =====
# 检查连接
docker compose exec db mysql -uicube_api -picube123 -e "SELECT 1;"

# 查看数据库大小
docker compose exec db mysql -uicube_api -picube123 icube_db -e "
SELECT table_name,
       round(((data_length + index_length) / 1024 / 1024), 2) AS '大小(MB)'
FROM information_schema.TABLES
WHERE table_schema = 'icube_db'
ORDER BY (data_length + index_length) DESC;"

# ===== Redis =====
# 查看持久化状态
docker compose exec redis redis-cli INFO persistence

# 查看 RDB 文件大小
docker compose exec redis ls -lh /data/dump.rdb

# 查看 AOF 目录
docker compose exec redis ls -lh /data/appendonlydir/

# 手动触发 BGSAVE
docker compose exec redis redis-cli BGSAVE

# 查看 key 数量
docker compose exec redis redis-cli DBSIZE

# 查看内存使用
docker compose exec redis redis-cli INFO memory | grep used_memory_human
```

---

## 9. 最佳实践与注意事项

### 9.1 备份文件存储位置

- **MySQL 备份**：Git 仓库（天然版本管理）+ 服务器本地
- **Redis 备份**：`data/redis_backup/`（项目根目录下）
- `.gitignore` 已忽略 `data/redis_backup/`，不会提交到 Git

> 生产环境建议：备份文件应与数据盘分离，避免磁盘故障导致备份一起丢失。

### 9.2 定期演练恢复

备份不做恢复演练 = 没有备份。建议：
- 每季度做一次完整恢复演练
- 新员工上手时做一次恢复练习
- 大版本升级前先在测试环境恢复验证

### 9.3 磁盘空间预警

备份文件会持续占用磁盘空间，需要监控：
- 磁盘使用率超过 80% 时告警
- 定期检查备份目录大小
- 保留策略要合理（7 天足够小项目使用）

### 9.4 异地备份建议

当前备份都在同一台服务器上，如果服务器挂了备份也一起没了。进阶方案：

| 方案 | 成本 | 复杂度 | 说明 |
|------|------|--------|------|
| 阿里云 OSS / 七牛云 | 低（几元/月） | 中 | 脚本上传，生命周期自动管理 |
| 另一台服务器 rsync | 低 | 低 | 定时同步 |
| GitHub 私有仓库 | 免费 | 低 | 适合结构化小数据（MySQL 备份） |

> 本项目 MySQL 备份通过 Git 管理，天然有"异地"属性（GitHub 云端）；Redis 备份目前只有本地，后续数据重要性提升后再考虑。

### 9.5 Redis 持久化配置选型建议

| 场景 | 推荐配置 | 理由 |
|------|---------|------|
| **纯缓存**（数据丢了没关系） | 只开 RDB，甚至不开持久化 | 性能最好，Redis 挂了重建缓存就行 |
| **一般业务**（会话、限流） | RDB + AOF 混合持久化，everysec | 兼顾性能和安全，丢 1 秒可接受 |
| **金融级**（订单、支付） | AOF always + RDB 快照 | 数据绝对不能丢，接受性能损耗 |

**本项目选型**：RDB + AOF 混合持久化（everysec），理由：
1. Redis 存的是会话、缓存、限流，丢了用户重新登录就行，不影响核心业务
2. 但也不想每次重启都清空所有缓存，所以 AOF 能快速恢复
3. 为未来接入消息队列等重要数据预留能力
4. everysec 策略对性能影响极小，性价比最高
