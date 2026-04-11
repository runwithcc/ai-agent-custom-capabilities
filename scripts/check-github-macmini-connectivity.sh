#!/usr/bin/env bash
set -euo pipefail

echo "== GitHub auth =="
if gh auth status; then
  echo
else
  echo
  echo "GitHub auth is broken. Suggested fix:"
  echo "  gh auth logout -h github.com -u runwithcc"
  echo "  gh auth login -h github.com -p https -w -s repo"
  echo
fi

echo "== Tailscale peers =="
tailscale status --json | jq -r '.Peer[] | [.HostName,.DNSName,.TailscaleIPs[0],.Online] | @tsv'
echo

echo "== SSH checks =="
set +e
ssh -o BatchMode=yes -o ConnectTimeout=5 macmini-lan 'echo ok'
lan_status=$?
ssh -o BatchMode=yes -o ConnectTimeout=5 macmini-ts 'echo ok'
ts_status=$?
set -e

echo
echo "macmini-lan status: $lan_status"
echo "macmini-ts status: $ts_status"

if [[ $lan_status -eq 0 && $ts_status -ne 0 ]]; then
  echo
  echo "LAN works, Tailscale path is still broken."
  echo "Use macmini-lan for immediate deployment."
fi
