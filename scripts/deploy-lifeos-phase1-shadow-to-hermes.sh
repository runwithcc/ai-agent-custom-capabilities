#!/usr/bin/env bash
set -euo pipefail

SSH_ALIAS="${SSH_ALIAS:-macmini-lan}"
SERVICE_LABEL="${SERVICE_LABEL:-com.newbornhermes.gateway}"
SERVICE_USER="${SERVICE_USER:-NewBornHermes}"
REMOTE_REPO="${REMOTE_REPO:-/Users/${SERVICE_USER}/.hermes/hermes-agent}"
REMOTE_PLATFORM_DIR="${REMOTE_REPO}/gateway/platforms"
LOCAL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ASSET_ROOT="${LOCAL_ROOT}/capabilities/lifeos-phase1/assets"
STAMP="$(date +%Y%m%d-%H%M%S)"
REMOTE_STAGE_DIR="/tmp/lifeos-phase1-${STAMP}"

echo "[1/4] 检查远端连通性"
ssh -o BatchMode=yes "${SSH_ALIAS}" "echo connected" >/dev/null

echo "[2/4] 上传文件到远端临时目录"
ssh "${SSH_ALIAS}" "mkdir -p '${REMOTE_STAGE_DIR}'"
scp "${ASSET_ROOT}/runtime-host-overrides/feishu.py" \
  "${SSH_ALIAS}:${REMOTE_STAGE_DIR}/feishu.py"
scp "${ASSET_ROOT}/lifeos_phase1_runtime.py" \
  "${SSH_ALIAS}:${REMOTE_STAGE_DIR}/lifeos_phase1_runtime.py"

echo "[3/4] 写入真实运行目录并备份旧文件"
ssh -tt "${SSH_ALIAS}" "
  sudo mkdir -p '${REMOTE_PLATFORM_DIR}' &&
  if [ -f '${REMOTE_PLATFORM_DIR}/feishu.py' ]; then
    sudo cp '${REMOTE_PLATFORM_DIR}/feishu.py' '${REMOTE_PLATFORM_DIR}/feishu.py.bak-${STAMP}';
  fi &&
  if [ -f '${REMOTE_PLATFORM_DIR}/lifeos_phase1_runtime.py' ]; then
    sudo cp '${REMOTE_PLATFORM_DIR}/lifeos_phase1_runtime.py' '${REMOTE_PLATFORM_DIR}/lifeos_phase1_runtime.py.bak-${STAMP}';
  fi &&
  sudo install -o '${SERVICE_USER}' -g staff -m 0644 '${REMOTE_STAGE_DIR}/feishu.py' '${REMOTE_PLATFORM_DIR}/feishu.py' &&
  sudo install -o '${SERVICE_USER}' -g staff -m 0644 '${REMOTE_STAGE_DIR}/lifeos_phase1_runtime.py' '${REMOTE_PLATFORM_DIR}/lifeos_phase1_runtime.py' &&
  rm -rf '${REMOTE_STAGE_DIR}'
"

echo "[4/4] 重启 Hermes gateway"
ssh -tt "${SSH_ALIAS}" "sudo launchctl kickstart -k system/${SERVICE_LABEL}"

echo "部署完成"
