#!/usr/bin/env bash
# 自动拉取仓库最新代码，若有更新则触发 docker-auto.sh 重新构建并启动容器
# 用法:
#   autopull.sh             # cron 模式：无新提交时直接退出
#   autopull.sh --force     # 强制模式：无论有无新提交，都重跑 docker-auto.sh
#   autopull.sh -f          # 同 --force
# 若在 TTY 下手动运行（交互终端），默认自动开启 --force。
#
# 建议通过 cron 每 20 分钟执行一次：
#   */20 * * * * /home/ubuntu/UptimeGuard/autopull.sh >> /home/ubuntu/UptimeGuard/autopull.log 2>&1
set -uo pipefail

# cron 环境 PATH 较窄，这里显式补齐 docker/git 等常用路径
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH:-}"

REPO_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
LOG_FILE="${REPO_DIR}/autopull.log"
LOCK_FILE="${REPO_DIR}/.autopull.lock"
BRANCH="main"

FORCE=0
for arg in "$@"; do
  case "${arg}" in
    -f|--force) FORCE=1 ;;
    -h|--help)
      sed -n '2,9p' "$0"
      exit 0
      ;;
  esac
done

# TTY 环境视为手动运行，自动启用 force
if [[ "${FORCE}" -eq 0 && -t 1 ]]; then
  FORCE=1
  MANUAL_TTY=1
else
  MANUAL_TTY=0
fi

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

# 通过 flock 防止重叠执行（上一次还没跑完时直接跳过本次）
exec 9>"${LOCK_FILE}"
if ! flock -n 9; then
  log "已有 autopull 在运行，跳过本次"
  exit 0
fi

cd "${REPO_DIR}"

if [[ "${FORCE}" -eq 1 ]]; then
  if [[ "${MANUAL_TTY}" -eq 1 ]]; then
    log "手动运行 (TTY)，已启用强制模式"
  else
    log "已启用强制模式 (--force)"
  fi
fi

log "开始拉取: ${REPO_DIR} (${BRANCH})"

OLD_HEAD="$(git rev-parse HEAD 2>/dev/null || echo '')"

if ! git fetch --quiet origin "${BRANCH}"; then
  log "git fetch 失败，退出"
  exit 1
fi

NEW_HEAD="$(git rev-parse "origin/${BRANCH}")"

NEED_DEPLOY=0
if [[ "${OLD_HEAD}" == "${NEW_HEAD}" ]]; then
  if [[ "${FORCE}" -eq 1 ]]; then
    log "无新提交，当前 HEAD=${OLD_HEAD:0:7}；强制模式继续执行"
    NEED_DEPLOY=1
  else
    log "无新提交，当前 HEAD=${OLD_HEAD:0:7}"
    exit 0
  fi
else
  log "发现新提交: ${OLD_HEAD:0:7} -> ${NEW_HEAD:0:7}"
  # 使用 reset --hard 强制与远端一致，避免本地脏目录导致 pull 失败
  if ! git reset --hard "origin/${BRANCH}" >/dev/null; then
    log "git reset --hard 失败，退出"
    exit 1
  fi
  NEED_DEPLOY=1
fi

run_docker_auto() {
  local script="${REPO_DIR}/docker-auto.sh"

  if [[ ! -x "${script}" ]]; then
    log "未找到可执行脚本 ${script}，尝试添加执行权限"
    if [[ -f "${script}" ]]; then
      chmod +x "${script}" || true
    fi
  fi

  if [[ ! -x "${script}" ]]; then
    log "脚本仍不可执行，跳过部署: ${script}"
    return
  fi

  log "执行 docker-auto.sh ..."
  echo "---------- docker-auto.sh output begin ----------"
  local rc=0
  (cd "${REPO_DIR}" && bash "${script}") || rc=$?
  echo "---------- docker-auto.sh output end   ----------"
  if [[ "${rc}" -eq 0 ]]; then
    log "部署完成"
  else
    log "部署失败 (exit=${rc})"
  fi
}

if [[ "${NEED_DEPLOY}" -eq 1 ]]; then
  run_docker_auto
else
  log "无需部署"
fi

log "本次任务完成"
