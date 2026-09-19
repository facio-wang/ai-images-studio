# ===== 前端 Admin Dockerfile (Phase 5 CICD) =====
# 多阶段构建：node 构建 -> nginx 静态托管
# 构建产物部署在 bitmystic.online/admin/ 路径下，故 VITE_BASE_URL=/admin/

# ---------- Stage 1: builder ----------
FROM node:20-alpine AS builder
WORKDIR /app

# 利用 Docker 缓存：先装依赖
COPY package*.json ./
RUN npm ci

# 拷贝源码并构建（base 路径设为 /admin/ 以匹配 nginx 的 location /admin/）
COPY . .
ENV VITE_BASE_URL=/admin/
RUN npm run build

# ---------- Stage 2: nginx ----------
FROM nginx:alpine
# 构建产物放到 nginx 的 admin 子目录（与 nginx.conf 的 alias 对齐）
COPY --from=builder /app/dist /usr/share/nginx/html/admin
# 自定义站点配置
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
