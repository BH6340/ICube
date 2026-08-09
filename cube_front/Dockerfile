# 构建阶段：安装依赖并生成 Vue 生产文件
FROM node:20-alpine AS builder

WORKDIR /app

# 先复制依赖清单，源码变化时可以复用 npm 依赖缓存
COPY package.json package-lock.json ./

# npm ci 严格使用锁文件，保证本地、CI 和服务器构建结果一致
RUN npm ci --registry=https://registry.npmmirror.com

COPY . .

# Vite 将生产文件输出到 /app/dist
RUN npm run build


# 运行阶段：仅使用 Nginx 提供静态文件，不携带 Node.js 和源码
FROM nginx:1.28-alpine AS runtime

# 替换默认站点配置，支持 Vue Router history 模式的 SPA 回退
COPY nginx.conf /etc/nginx/conf.d/default.conf

# dist 直接写入镜像，不再通过 front_dist 命名卷共享
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

# 基础镜像默认以前台模式启动 Nginx，此处显式声明便于理解容器行为
CMD ["nginx", "-g", "daemon off;"]
