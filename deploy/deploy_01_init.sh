#!/bin/bash
# ICube 半自动化部署脚本 - 第 1 步：服务器初始化（root 执行）
# 功能：系统更新、时区、创建部署用户、安装 Docker & Docker Compose、镜像加速

set -e

# ---------- 颜色 ----------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'
pass()  { echo -e "${GREEN}✅ $1${NC}"; }
warn()  { echo -e "${YELLOW}⚠️  $1${NC}"; }
fail()  { echo -e "${RED}❌ $1${NC}"; exit 1; }
step()  { echo -e "\n${YELLOW}[$STEPS/$TOTAL] $1${NC}"; }

TOTAL=10
STEPS=0

# ---------- 权限检查 ----------
if [ "$USER" != "root" ]; then
    fail "此脚本必须以 root 身份运行，请先 su - root"
fi

# ---------- 1. 系统更新 ----------
((STEPS++)) || true; step "系统更新 (apt update & upgrade)"
apt update -y && apt upgrade -y -qq
pass "系统更新完成"

# ---------- 2. 时区 ----------
((STEPS++)) || true; step "设置时区 Asia/Shanghai"
timedatectl set-timezone Asia/Shanghai
pass "时区已设置为: $(timedatectl | grep 'Time zone' | awk '{print $3}')"

# ---------- 3. 创建部署用户 ----------
((STEPS++)) || true; step "创建部署用户 bh"
if id "bh" &>/dev/null; then
    warn "用户 bh 已存在，跳过创建"
else
    useradd -m -s /bin/bash bh
    # 默认密码 123456（首次登录会强制要求修改，这里改成永不过期免强制改）
    echo "bh:123456" | chpasswd
    usermod -aG sudo bh
    pass "用户 bh 已创建（默认密码 123456，登录后请自行修改）"
fi

# ---------- 4. 基础依赖 ----------
((STEPS++)) || true; step "安装基础依赖 (git/curl/vim/...)"
apt install -y -qq git curl wget vim htop net-tools unzip ca-certificates gnupg lsb-release
pass "基础依赖安装完成"

# ---------- 5. 卸载旧 Docker ----------
((STEPS++)) || true; step "卸载可能存在的旧版 Docker"
apt remove -y -qq docker docker-engine docker.io containerd runc 2>/dev/null || true
pass "旧 Docker 已清理（如存在）"

# ---------- 6. Docker GPG 密钥 + 软件源 ----------
((STEPS++)) || true; step "配置 Docker 官方 GPG 密钥 & 阿里云软件源"
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg -f
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://mirrors.aliyun.com/docker-ce/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt update -y -qq
pass "Docker 软件源配置完成"

# ---------- 7. 安装 Docker ----------
((STEPS++)) || true; step "安装 Docker & Docker Compose Plugin"
apt install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
pass "Docker 安装完成: $(docker --version)"
pass "Docker Compose: $(docker compose version)"

# ---------- 8. Docker 镜像加速 ----------
((STEPS++)) || true; step "配置 Docker 国内镜像加速 + 日志轮转"
mkdir -p /etc/docker
cat > /etc/docker/daemon.json << 'EOF'
{
  "registry-mirrors": [
    "https://docker.1ms.run",
    "https://docker.xuanyuan.me",
    "https://hub-mirror.c.163.com"
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  }
}
EOF
pass "daemon.json 写入完成"

# ---------- 9. Docker 开机自启 & 把 bh 加入 docker 组 ----------
((STEPS++)) || true; step "启动 Docker / 开机自启 / 将 bh 加入 docker 组"
systemctl enable docker
systemctl restart docker
usermod -aG docker bh
pass "Docker 已启动并设为开机自启，bh 已加入 docker 组"

# ---------- 10. 验证 ----------
((STEPS++)) || true; step "最终验证"
echo "  Docker 版本: $(docker --version)"
echo "  Compose 版本: $(docker compose version)"
echo "  Docker 状态: $(systemctl is-active docker)"
echo "  bh 是否在 docker 组: $(groups bh | grep -q docker && echo YES || echo NO)"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   第 1 步初始化全部完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "下一步操作："
echo -e "  ${YELLOW}1. 退出 SSH 重新登录（或执行 newgrp docker）让 docker 组生效${NC}"
echo -e "  ${YELLOW}2. 切换用户： su - bh${NC}"
echo -e "  ${YELLOW}3. 执行： bash deploy/deploy_02_app.sh${NC}"
echo ""
