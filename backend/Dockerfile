# ===== AI Images Studio 后端镜像（多阶段） =====
# Stage1: node 构建前端 dist；Stage2: python:3.11-slim 运行 FastAPI 并静态托管前端
# 构建上下文为仓库根目录（docker compose build 的默认 context=.）

# ---------- Stage 1: 前端构建 ----------
FROM node:20-alpine AS frontend-builder
WORKDIR /build

# 先拷贝依赖清单利用层缓存
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# 拷贝前端源码并构建（生产模式 base=./，同域由后端托管）
COPY frontend/ ./
RUN npm run build

# ---------- Stage 2: 后端运行时 ----------
FROM python:3.11-slim AS runtime

# pip 镜像源加速（可构建时覆盖：--build-arg PIP_INDEX_URL=...）
ARG PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple
ENV PIP_INDEX_URL=${PIP_INDEX_URL} \
    PYTHONUNBUFFERED=1 \
    # 后端监听端口
    STUDIO_PORT=8191 \
    # 容器内数据目录（compose 挂载 ./data:/app/data 持久化）
    STUDIO_DATA_DIR=/app/data \
    # 前端构建产物目录（由 docker_asgi.py 静态托管）
    SPA_DIR=/app/static

# curl 供 healthcheck 使用；fonts-noto-cjk 提供中文黑体（含拉丁字形）、fonts-dejavu-core 为英文备选
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl fonts-noto-cjk fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先装依赖利用层缓存
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝后端源码（根目录 .dockerignore 已排除 data/__pycache__/.venv 等）
COPY backend/ ./

# 前端构建产物 → 静态托管目录
COPY --from=frontend-builder /build/dist/ /app/static/

EXPOSE 8191

# docker_asgi.py 在 app.main:app 基础上注入 SPA 托管（不改动 backend/app 任何文件）
CMD ["uvicorn", "docker_asgi:app", "--host", "0.0.0.0", "--port", "8191"]
