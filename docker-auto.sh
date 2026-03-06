#!/usr/bin/env bash
set -euo pipefail

# 通过 docker compose 的 build/up 来确保代码变更生效（不要构建无关镜像名）
docker compose down
docker compose up -d --build