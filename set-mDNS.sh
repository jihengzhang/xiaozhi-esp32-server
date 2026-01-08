#!/usr/bin/env bash
# set-mDNS.sh - configure hostname and ensure mDNS (Avahi) is installed and running.
# 用法:
#   ./set-mDNS.sh                  # 显示说明与当前状态
#   ./set-mDNS.sh -hostname myserver  # 设置主机名并广播 mDNS（myserver.local）
#   ./set-mDNS.sh -mDNS              # 仅检查/启动 mDNS 服务

# 
# 主机名解析（mDNS）
# ping -c 2 Z8G4-M.local
# 或 avahi-resolve-host-name Z8G4-M.local
# 端口连通性
# nc -vz Z8G4-M.local 8000 # 仅测 TCP 可达
# 若没有 nc，也可 telnet Z8G4-M.local 8000 看能否建立连接
# WebSocket 简单握手
# 如果有 websocat（推荐）：
# websocat ws://Z8G4-M.local:8000/ （能连上会保持挂起，Ctrl+C 退出）
# 如果只能用 curl（版本需支持 websocket，较新）：
# curl -v -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Key: testtesttest1234" -H "Sec-WebSocket-Version: 13" ws://Z8G4-M.local:8000/
# curl http://Z8G4-M.local:8000/
# 能看到 101 Switching Protocols 就说明 WS 通了。


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

usage() {
  echo "Usage: $0 [-hostname <name>] [-mDNS]"
  echo "  no args      : show this help and current status"
  echo "  -hostname n  : set hostname and broadcast n.local via mDNS"
  echo "  -mDNS        : ensure mDNS service is installed/running"
}

main() {
  local HOSTNAME=""
  local DO_MDNS=false

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -hostname)
        HOSTNAME="$2"; shift 2 ;;
      -mDNS|-mdns)
        DO_MDNS=true; shift ;;
      -h|--help)
        usage; return 0 ;;
      *)
        echo "Unknown option: $1"; return 1 ;;
    esac
  done

  if [[ -z "$HOSTNAME" && "$DO_MDNS" == false ]]; then
    usage
    status_report
    return 0
  fi

  if [[ -n "$HOSTNAME" ]]; then
    echo "[info] setting hostname to $HOSTNAME"
    sudo hostnamectl set-hostname "$HOSTNAME"
    sudo avahi-set-host-name "$HOSTNAME" >/dev/null 2>&1 || true
    DO_MDNS=true
  fi

  if [[ "$DO_MDNS" == true ]]; then
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

    echo "[done] mDNS ready. Test: ping ${HOSTNAME:-$(hostnamectl --static 2>/dev/null || hostname)}.local"
  fi

  status_report
  return 0
}

main "$@"
