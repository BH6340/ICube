# 20. SSH 隧道连接数据库

> 本文档介绍如何通过 SSH 隧道从本地安全连接服务器上的 Docker MySQL 容器，涵盖原理、密钥配置、多种连接方式及常见问题排查。

## 20.1 SSH 隧道原理

### 本地端口转发机制

SSH 隧道（Local Port Forwarding）利用 SSH 协议的加密通道，将本地端口的流量转发到远程服务器上的目标端口。对于 ICube 项目，MySQL 容器仅绑定在服务器的 `127.0.0.1:3306`，外部无法直接访问。通过 SSH 隧道，本地工具（如 Navicat）连接本地端口，流量经 SSH 加密后到达服务器，再由服务器转发到 `127.0.0.1:3306`，从而访问 Docker 中的 MySQL 容器。

### 数据流向

```
本地 GUI 工具 (Navicat/DBeaver)
  → 连接 127.0.0.1:13306 (本地端口)
    → SSH 加密隧道 (经公网 22 端口)
      → 服务器 SSH 服务解密
        → 转发到 127.0.0.1:3306
          → Docker MySQL 容器 (icube_db)
```

关键点：
- 本地端口可任意选择（如 `13306`），避免与本地 MySQL `3306` 冲突
- SSH 连接保持期间隧道有效，断开 SSH 即断开隧道
- 整条链路加密，数据库凭据不经过公网明文传输

## 20.2 ICube 数据库连接信息

### Docker MySQL 容器配置

参见 [docker-compose.yml](/code/docker-compose.yml) `db` 服务：

| 配置项 | 值 |
| ------ | -- |
| 镜像 | `mysql:8.0` |
| 容器名 | `icube_db` |
| 字符集 | `utf8mb4` / `utf8mb4_unicode_ci` |
| 端口绑定 | `127.0.0.1:3306:3306`（仅本机，不暴露公网） |
| 数据库名 | `icube_db` |
| 数据卷 | `mysql_data`（持久化） |

### 端口绑定策略

```yaml
ports:
  - "127.0.0.1:3306:3306"
```

`127.0.0.1` 前缀表示仅监听服务器本地回环地址，公网无法直接访问。这是安全最佳实践——数据库不暴露公网，只能通过 SSH 进入服务器后访问。

### 数据库账号一览

| 账号 | 用户名 | 密码 | 用途 |
| ---- | ------ | ---- | ---- |
| 业务用户 | `icube_api` | `icube123` | Django 后端连接使用 |
| 管理员 | `root` | `icube_root123` | 运维管理、DDL 操作 |

## 20.3 SSH 密钥配置

### 生成 PEM 格式密钥对

Windows PowerShell 中执行：

```powershell
ssh-keygen -t rsa -b 4096 -m PEM -f "C:\Users\Administrator\.ssh\id_rsa" -N ""
```

参数说明：

| 参数 | 作用 |
| ---- | ---- |
| `-t rsa` | 密钥类型 RSA |
| `-b 4096` | 密钥长度 4096 位 |
| `-m PEM` | 输出 PEM 格式（兼容 Navicat） |
| `-f` | 指定输出路径 |
| `-N ""` | 私钥不设密码 |

生成两个文件：
- `id_rsa` — 私钥（本地保管，不可泄露）
- `id_rsa.pub` — 公钥（需上传到服务器）

验证格式正确：

```powershell
Get-Content "C:\Users\Administrator\.ssh\id_rsa" -TotalCount 1
```

应输出 `-----BEGIN RSA PRIVATE KEY-----`。如果输出 `-----BEGIN OPENSSH PRIVATE KEY-----` 则是 OpenSSH 新格式，Navicat 不兼容。

### 上传公钥到服务器

```powershell
type "C:\Users\Administrator\.ssh\id_rsa.pub" | ssh bh@服务器IP "cat >> ~/.ssh/authorized_keys"
```

执行时会提示输入服务器密码（最后一次），输入后公钥追加到服务器的 `~/.ssh/authorized_keys` 文件。

### 验证免密登录

```powershell
ssh bh@服务器IP
```

不再提示输入密码即成功。如果仍要求密码，检查：

- 服务器 `~/.ssh/authorized_keys` 是否包含公钥内容
- 服务器 `~/.ssh/` 目录权限应为 `700`，`authorized_keys` 应为 `600`
- 服务器 `/etc/ssh/sshd_config` 中 `PubkeyAuthentication` 应为 `yes`

### 密钥格式兼容性问题

**问题**：OpenSSH 7.8+ 默认生成新格式私钥（`BEGIN OPENSSH PRIVATE KEY`），Navicat 等旧版 GUI 工具不支持。

**解决方案对比**：

| 方案 | 命令 | 适用场景 |
| ---- | ---- | -------- |
| 生成时指定 PEM | `ssh-keygen -m PEM ...` | 全新生成密钥（推荐） |
| 转换已有密钥格式 | `ssh-keygen -p -m PEM -f id_rsa -N ""` | 保留已有密钥不重新生成 |

**转换已有密钥**（先备份）：

```powershell
Copy-Item "C:\Users\Administrator\.ssh\id_rsa" "C:\Users\Administrator\.ssh\id_rsa.bak"
ssh-keygen -p -m PEM -f "C:\Users\Administrator\.ssh\id_rsa" -N ""
```

转换仅改变私钥文件头格式，密钥内容不变，服务器端公钥无需重新部署。

## 20.4 连接方式

### 方式一：Navicat 内置 SSH 隧道（推荐）

无需手动开终端，Navicat 自动建立并管理隧道。

**配置步骤**：

1. Navicat → 连接 → MySQL，打开连接属性窗口
2. **常规** 标签页（数据库连接信息）：

   | 参数 | 值 |
   | ---- | -- |
   | 连接名 | `ICube生产库` |
   | 主机 | `127.0.0.1` |
   | 端口 | `3306` |
   | 用户名 | `icube_api`（业务）或 `root`（管理） |
   | 密码 | `icube123` 或 `icube_root123` |
   | 数据库 | `icube_db` |

3. **SSH** 标签页，勾选「使用 SSH 隧道」：

   | 参数 | 值 |
   | ---- | -- |
   | 主机 | 服务器公网 IP |
   | 端口 | `22` |
   | 用户名 | `bh` |
   | 验证方式 | 公钥 |
   | 私钥 | `C:\Users\Administrator\.ssh\id_rsa` |
   | 密码 | 留空（私钥无密码时） |

4. 点击「测试连接」，提示成功后保存

**原理**：Navicat 在后台自动建立 SSH 隧道，将本地请求转发到服务器 `127.0.0.1:3306`。常规页的 `127.0.0.1:3306` 是隧道目标端，不是本地地址。

### 方式二：命令行 SSH 隧道 + GUI 工具

适合所有不支持内置 SSH 隧道的工具。

**第一步：建立隧道**

```powershell
ssh -L 13306:127.0.0.1:3306 bh@服务器IP
```

| 参数 | 含义 |
| ---- | ---- |
| `-L` | 本地端口转发 |
| `13306` | 本地监听端口（避免与本地 MySQL 冲突） |
| `127.0.0.1:3306` | 服务器端目标地址和端口 |
| `bh@服务器IP` | SSH 登录凭据 |

终端保持打开期间隧道有效。加 `-N` 参数可仅建隧道不执行命令：

```powershell
ssh -N -L 13306:127.0.0.1:3306 bh@服务器IP
```

**第二步：GUI 工具连接**

| 参数 | 值 |
| ---- | -- |
| 主机 | `127.0.0.1` |
| 端口 | `13306`（本地隧道端口） |
| 用户名 | `icube_api` 或 `root` |
| 密码 | `icube123` 或 `icube_root123` |
| 数据库 | `icube_db` |

### 方式三：直接 SSH 进服务器命令行

无需本地工具，适合快速查询。

```bash
# 登录服务器后进入容器（业务用户）
docker compose exec db mysql -uicube_api -picube123 icube_db

# 管理员
docker compose exec db mysql -uroot -picube_root123 icube_db

# 进入容器后执行单条 SQL
docker compose exec db mysql -uicube_api -picube123 icube_db -e "SHOW TABLES;"
```

### 方式四：VSCode Remote-SSH + MySQL 扩展

1. 安装 VSCode 扩展 `Remote - SSH` 和 `MySQL`（或 `Database Client`）
2. `F1` → `Remote-SSH: Connect to Host` → 输入 `bh@服务器IP`
3. 连接成功后，MySQL 扩展新建连接：

   | 参数 | 值 |
   | ---- | -- |
   | 主机 | `127.0.0.1` |
   | 端口 | `3306` |
   | 用户名 | `icube_api` 或 `root` |
   | 密码 | `icube123` 或 `icube_root123` |
   | 数据库 | `icube_db` |

VSCode Remote-SSH 自动建立隧道，MySQL 扩展直接连服务器本地端口即可。

## 20.5 注意事项

### 安全组端口开放

| 端口 | 协议 | 用途 | 是否需开放 |
| ---- | ---- | ---- | ---------- |
| 22 | TCP | SSH 登录 | 阿里云安全组需开放，来源限制为可信 IP |
| 3306 | TCP | MySQL | **无需开放**，仅监听 127.0.0.1 |
| 80/443/8443 | TCP | Web 访问 | 需开放 |

SSH 22 端口建议将安全组来源限制为可信 IP（如本地开发机固定 IP），避免暴露给全网。

### 私钥格式兼容性

| 工具 | 支持 OpenSSH 新格式 | 支持 PEM 格式 |
| ---- | -------------------- | -------------- |
| Navicat Premium 16+ | 部分 | 是 |
| DBeaver | 是 | 是 |
| VSCode MySQL 扩展 | 是 | 是 |
| 命令行 ssh | 是 | 是 |

如遇 `公钥认证失败` 错误，首先检查私钥格式是否为 PEM（`BEGIN RSA PRIVATE KEY`）。

### 隧道断开场景

| 场景 | 原因 | 解决 |
| ---- | ---- | ---- |
| 关闭终端窗口 | SSH 连接断开导致隧道关闭 | 使用方式一（Navicat 内置）或 `nohup`/`screen` 保持 |
| 网络波动 | SSH 空闲超时断开 | 加 `-o ServerAliveInterval=60` 保活 |
| 休眠/待机 | 本地网络中断 | 唤醒后重新连接 |
| 服务器重启 | SSH 服务重启 | 重新建立隧道 |

### 权限问题排查

**SSH 公钥认证失败排查清单**：

1. 服务器 `~/.ssh/authorized_keys` 是否包含公钥内容
   ```bash
   cat ~/.ssh/authorized_keys
   ```
2. 权限是否正确
   ```bash
   chmod 700 ~/.ssh
   chmod 600 ~/.ssh/authorized_keys
   ```
3. `sshd_config` 是否启用公钥认证
   ```bash
   grep PubkeyAuthentication /etc/ssh/sshd_config
   # 应为 PubkeyAuthentication yes
   ```
4. 私钥格式是否正确（PEM 格式）
5. SSH 用户名是否正确（`bh` 不是 `root`，除非服务器允许 root 登录）

**MySQL 连接被拒绝排查清单**：

| 错误信息 | 原因 | 解决 |
| -------- | ---- | ---- |
| `Access denied for user` | 用户名/密码错误 | 核对账号密码 |
| `Can't connect to MySQL server on 127.0.0.1` | 隧道未建立或 MySQL 未运行 | 检查隧道状态、`docker ps` 查看容器 |
| `Lost connection to MySQL server` | 隧道中断 | 重新建立 SSH 连接 |
| 连上了看不到表 | 用户权限不足 | 用 root 账号连接 |
