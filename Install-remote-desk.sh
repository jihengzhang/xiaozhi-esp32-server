#!/bin/bash
# 远程桌面安装脚本
# 用法: sudo ./Install-remote.sh --xrdp [--vnc] [--ssh]

[ "$EUID" -ne 0 ] && { echo "需要 root 权限"; return 1; }

install_xrdp() {
    apt update
    apt install -y xrdp
    
    cat > /etc/xrdp/startwm.sh << 'EOF'
#!/bin/sh
unset DBUS_SESSION_BUS_ADDRESS XDG_RUNTIME_DIR
exec /etc/X11/Xsession
EOF
    
    chmod +x /etc/xrdp/startwm.sh
    chmod 640 /etc/xrdp/key.pem 2>/dev/null || true
    
    # 修复 color profile 权限问题
    mkdir -p /etc/polkit-1/localauthority/50-local.d
    cat > /etc/polkit-1/localauthority/50-local.d/45-allow-colord.pkla << 'EOF'
[Allow Colord all Users]
Identity=unix-user:*
Action=org.freedesktop.color-manager.create-device;org.freedesktop.color-manager.create-profile;org.freedesktop.color-manager.delete-device;org.freedesktop.color-manager.delete-profile;org.freedesktop.color-manager.modify-device;org.freedesktop.color-manager.modify-profile
ResultAny=no
ResultInactive=no
ResultActive=yes
EOF
    
    systemctl enable xrdp xrdp-sesman
    systemctl restart xrdp xrdp-sesman
    
    ufw allow 3389/tcp
    echo "XRDP 已安装 - 端口 3389 - 使用默认桌面环境"
}

install_vnc() {
    apt install -y tigervnc-standalone-server xfce4
    
    mkdir -p /etc/skel/.vnc
    cat > /etc/skel/.vnc/xstartup << 'EOF'
#!/bin/sh
exec startxfce4
EOF
    chmod +x /etc/skel/.vnc/xstartup
    
    ufw allow 5900:5910/tcp
    echo "VNC 已安装 - 端口 5900-5910"
    echo "运行: vncserver :1 启动 VNC"
}

install_ssh() {
    apt install -y openssh-server
    systemctl enable ssh
    systemctl restart ssh
    ufw allow 22/tcp
    echo "SSH 已安装 - 端口 22"
}

# 解析参数
[ $# -eq 0 ] && { echo "用法: $0 --xrdp [--vnc] [--ssh]"; return 0; }

while [ $# -gt 0 ]; do
    case $1 in
        --xrdp) install_xrdp ;;
        --vnc) install_vnc ;;
        --ssh) install_ssh ;;
        *) echo "未知选项: $1"; return 1 ;;
    esac
    shift
done

echo "安装完成 - IP: $(hostname -I | awk '{print $1}')"
