#!/bin/bash

# 设置报错退出机制，任何一步出错则脚本立即终止
set -e

echo "========================================"
echo " 开始执行一键更新与部署流程..."
echo "========================================"

# 1. 检查并拉取最新代码 (Git 一般由当前用户执行，不需要 sudo)
echo "[1/4] 正在从 Git 仓库拉取最新代码..."
git pull
if [ $? -ne 0 ]; then
    echo "【错误】Git pull 失败，请检查冲突或网络！"
    exit 1
fi

# 2. 彻底关闭并删除旧容器及数据卷 (-v)
echo "[2/4] 正在彻底关闭容器并清理旧数据卷 (-v)..."
sudo docker compose down -v

# 3. 重新构建并启动服务
echo "[3/4] 正在重新构建并启动 Docker 服务..."
sudo docker compose up -d --build

# 4. 等待 MySQL 启动并自动注入最新的初始化数据
echo "[4/4] 正在等待 MySQL 就绪并初始化数据..."
until sudo docker compose exec -T db mysqladmin ping -h"localhost" -u"root" -p"icube_root123" --silent 2>/dev/null; do
    sleep 2
    echo -n "."
done
echo -e "\nMySQL 已成功启动！"

# 5. 自动定位项目中的 init_data.sql 并注入（最前面自动拼接 USE icube_db;）
SQL_FILE="./init_data.sql" # 请根据实际路径调整
if [ -f "$SQL_FILE" ]; then
    echo "正在注入最新初始化数据..."
    (echo "USE icube_db;"; cat "$SQL_FILE") | sudo docker compose exec -T db mysql -u"root" -p"你的数据库密码"
    echo "【成功】数据库数据已更新！"
else
    echo "【提示】未找到 init_data.sql，跳过额外数据注入。"
fi

echo "========================================"
echo " 【完成】全套部署与数据更新大功告成！"
echo "========================================"