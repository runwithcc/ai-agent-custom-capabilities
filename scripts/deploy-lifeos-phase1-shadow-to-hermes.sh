#!/usr/bin/env bash
set -euo pipefail

SSH_ALIAS="${SSH_ALIAS:-macmini-ts}"
REMOTE_REPO="${REMOTE_REPO:-/Users/hermes-svc/Agents/hermes-agent}"
REMOTE_PLATFORM_DIR="${REMOTE_REPO}/gateway/platforms"
LOCAL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ASSET_ROOT="${LOCAL_ROOT}/capabilities/lifeos-phase1/assets"

echo "[1/4] 检查远端连通性"
ssh -o BatchMode=yes "${SSH_ALIAS}" "echo connected" >/dev/null

echo "[2/4] 备份远端现有文件"
STAMP="$(date +%Y%m%d-%H%M%S)"
ssh "${SSH_ALIAS}" "cp '${REMOTE_PLATFORM_DIR}/feishu.py' '${REMOTE_PLATFORM_DIR}/feishu.py.bak-${STAMP}'"

echo "[3/4] 上传新文件"
scp "${ASSET_ROOT}/runtime-host-overrides/feishu.py" "${SSH_ALIAS}:${REMOTE_PLATFORM_DIR}/feishu.py"
scp "${ASSET_ROOT}/lifeos_phase1_runtime.py" "${SSH_ALIAS}:${REMOTE_PLATFORM_DIR}/lifeos_phase1_runtime.py"

echo "[4/4] 重启 Hermes gateway"
ssh "${SSH_ALIAS}" "bash '${REMOTE_REPO}/scripts/restart_hermes_gateway_remote.sh'"

echo "部署完成"
