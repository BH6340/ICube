# 构建阶段：编译 mysqlclient 等包含原生扩展的 Python 依赖
FROM python:3.13-slim AS builder

WORKDIR /build

# 编译工具仅存在于 builder，避免进入最终运行镜像
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources \
    && sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        default-libmysqlclient-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖清单，业务代码变化时可复用依赖构建缓存
COPY requirements.txt .

# 将全部依赖构建为 wheel，运行阶段无需编译器
RUN pip wheel \
        --no-cache-dir \
        --wheel-dir /wheels \
        --index-url https://pypi.tuna.tsinghua.edu.cn/simple \
        gunicorn \
        -r requirements.txt


# 运行阶段：只保留 Python、运行时动态库、项目代码和已安装依赖
FROM python:3.13-slim AS runtime

# 禁止生成 .pyc，并让 Python 日志立即输出到容器标准流
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# mysqlclient 运行时需要 MariaDB/MySQL 客户端动态库
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources \
    && sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends libmariadb3 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
COPY --from=builder /wheels /wheels

# 仅从 builder 生成的 wheel 安装，完成后删除临时安装包
RUN pip install \
        --no-cache-dir \
        --no-index \
        --find-links=/wheels \
        gunicorn \
        -r requirements.txt \
    && rm -rf /wheels

# 依赖层稳定后再复制代码，减少日常构建时的重复安装
COPY . .

# Loguru 文件日志目录；媒体和静态文件由 Compose 单独挂载
RUN mkdir -p /app/logs

EXPOSE 8000

# 先刷新共享静态文件卷，再启动 Gunicorn；生产环境禁用 --reload
# exec 让 Gunicorn 接管 PID 1，确保容器停止信号能够正确传递
CMD ["sh", "-c", "python manage.py collectstatic --noinput && exec gunicorn cube_api.wsgi:application --bind 0.0.0.0:8000 --workers 3 --access-logfile - --error-logfile -"]
