# UptimeGuard 多阶段构建：先构建运行环境与依赖（base），再复制应用代码。
# 避免 FROM uptimeguard-base:latest 在并行构建时去 Docker Hub 拉取不存在的镜像。

# ---------- base：系统依赖、pip、非 root 用户 ----------
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    ca-certificates \
    net-tools \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/logs && chmod 755 /app

RUN useradd --create-home --shell /bin/bash uptimeguard \
    && chown -R uptimeguard:uptimeguard /app

USER uptimeguard

ENV PYTHONPATH=/app

# ---------- app：业务代码 ----------
FROM base

WORKDIR /app

COPY app.py .
COPY monitor.py .
COPY ui.py .
COPY storage.py .
COPY log_manager.py .
COPY docker_utils.py .
COPY telegram_config.py .
COPY telegram_notifier.py .
COPY telegram_chat_bot.py .

COPY requirements.txt .
COPY sites.json .

USER root
RUN mkdir -p /app/logs && chmod 777 /app/logs
USER uptimeguard

ENV PYTHONPATH=/app
ENV DOCKER_RUN=true

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7863/ || exit 1

EXPOSE 7863

CMD ["python", "app.py"]
