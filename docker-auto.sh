#!/usr/bin/env bash
set -euo pipefail

# 宿主机 logs 目录需对容器内用户可写，否则会 Permission denied: /app/logs/uptime.log
mkdir -p logs && chmod 777 logs

# 通过 docker compose 的 build/up 来确保代码变更生效
docker compose down
docker compose up -d --build