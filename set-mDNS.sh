#!/usr/bin/env bash
# set-mDNS.sh - configure hostname and ensure mDNS (Avahi) is installed and running.
# Usage example:
#   ./set-mDNS.sh -hostname myserver
# After运行，局域网设备可通过 myserver.local 访问。
#  ws://myserver.local:8000/...）

echo "[info] enabling and starting avahi-daemon"
sudo systemctl enable --now avahi-daemon >/dev/null 2>&1 || \
echo "[info] restarting avahi-daemon to re-announce hostname"
sudo systemctl restart avahi-daemon >/dev/null 2>&1 || \
echo "[done] mDNS ready. Test: ping ${HOSTNAME}.local"
# set -euo pipefail
# set -o pipefail

status_report() {
  local h
  h=$(hostnamectl --static 2>/dev/null || hostname)
  echo "[status] hostname: $h"

  local avahi_state
  avahi_state=$(systemctl is-active avahi-daemon 2>/dev/null || echo "inactive")
  echo "[status] avahi-daemon: $avahi_state"

  local avahi_name
  avahi_name=$(avahi-resolve-host-name -4 "${h}.local" 2>/dev/null || true)
  if [[ -n "$avahi_name" ]]; then
    echo "[status] resolve ${h}.local -> $avahi_name"
  else
    echo "[status] resolve ${h}.local -> not found"
  fi
}

install_pkg_if_missing() {
  local pkg="$1"
  if ! dpkg -s "$pkg" >/dev/null 2>&1; then
    echo "[info] installing $pkg"
    sudo apt-get update -y >/dev/null 2>&1 || true
    sudo apt-get install -y "$pkg"
  else
    echo "[info] $pkg already installed"
  fi
}

main() {
  local HOSTNAME=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -hostname)
        HOSTNAME="$2"; shift 2 ;;
      -mDNS|-mdns)
        shift ;;
      -h|--help)
        echo "Usage: $0 [-hostname <name>]"; return 0 ;;
      *)
        echo "Unknown option: $1"; return 1 ;;
    esac
  done

  if [[ -z "$HOSTNAME" ]]; then
    status_report
    return 0
  fi

  echo "[info] setting hostname to $HOSTNAME"
  sudo hostnamectl set-hostname "$HOSTNAME"
  sudo avahi-set-host-name "$HOSTNAME" >/dev/null 2>&1 || true

  install_pkg_if_missing avahi-daemon
  install_pkg_if_missing avahi-utils

  echo "[info] enabling and starting avahi-daemon"
  sudo systemctl enable --now avahi-daemon >/dev/null 2>&1 || \
    echo "[warn] avahi-daemon enable/start failed (maybe not systemd); continuing"

  echo "[info] restarting avahi-daemon to re-announce hostname"
  sudo systemctl restart avahi-daemon >/dev/null 2>&1 || \
    echo "[warn] avahi-daemon restart failed (maybe not systemd); continuing"

  if command -v ufw >/dev/null 2>&1; then
    if sudo ufw status | grep -q "Status: active"; then
      echo "[info] ufw active, allowing 5353/udp"
      sudo ufw allow 5353/udp >/dev/null 2>&1 || true
    else
      echo "[info] ufw not active, skip rule"
    fi
  else
    echo "[info] ufw not installed, skip firewall rule"
  fi

  echo "[done] mDNS ready. Test: ping ${HOSTNAME}.local"
  return 0
}

main "$@"
