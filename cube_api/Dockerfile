FROM python:3.13-slim

WORKDIR /app

# 创建日志文件夹，防止日志写入失败
RUN mkdir -p /app/logs

# 1. 适配 Python 3.13 的国内清华源加速
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources \
    && sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 2. 复制依赖文件并安装
COPY requirements.txt .

# 💡 核心修复：在这里通过 pip 显式安装 gunicorn，并用清华源加速
RUN pip install --no-cache-dir gunicorn -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3. 复制其余所有代码
COPY . .

EXPOSE 8000

# 4. 启动命令
CMD ["gunicorn", "cube_api.wsgi:application", "--env", "DJANGO_SETTINGS_MODULE=cube_api.settings.prod", "--bind", "0.0.0.0:8000", "--workers", "3", "--reload"]