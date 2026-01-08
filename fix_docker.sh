#!/usr/bin/env bash

# Docker Installation and Configuration Fix Script
# 
# This script handles Docker installation (if needed) and fixes common Docker configuration issues:
# 1. Installs Docker using apt package manager (avoids snap version)
# 2. Installs Docker Compose plugin and BuildX for full functionality
# 3. Switches Docker context to default 
# 4. Removes Desktop credential helper that can cause auth issues
# 5. Ensures proper Docker daemon setup and permissions
#
# Usage: ./fix_docker.sh
# Note: This script may require sudo privileges for Docker installation

# 不使用 set -e，避免任何命令失败导致脚本/终端退出
# 改为手动检查关键命令的状态
set -o pipefail

# Helper function to exit script without closing terminal
# 检测脚本是如何被调用的（source 或直接执行）
safe_exit() {
    local exit_code=${1:-1}
    if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
        # 脚本被 source 执行，使用 return 而不是 exit
        return "$exit_code"
    else
        # 脚本被直接执行，可以安全使用 exit
        exit "$exit_code"
    fi
}

info() { printf '[info] %s\n' "$*"; }
error() { printf '[error] %s\n' "$*" >&2; }
warning() { printf '[warning] %s\n' "$*"; }

# Function to check and install missing components
check_and_install_components() {
    local docker_installed=false
    local compose_installed=false
    local packages_to_install=()
    
    # 检查 Docker 是否安装
    if command -v docker >/dev/null 2>&1; then
        docker_installed=true
        info "Docker is already installed: $(docker --version)"
    else
        warning "Docker is not installed"
        packages_to_install+=("docker.io")
    fi
    
    # 检查 docker compose (V2 插件版本) 是否可用
    if docker compose version >/dev/null 2>&1; then
        compose_installed=true
        info "Docker Compose V2 is already installed: $(docker compose version)"
    else
        warning "Docker Compose V2 plugin is not installed"
        # 只安装 V2 版本（作为 Docker 插件）
        packages_to_install+=("docker-compose-v2")
    fi
    
    # 检查是否需要安装 buildx
    if ! dpkg -l | grep -q docker-buildx 2>/dev/null; then
        packages_to_install+=("docker-buildx")
    fi
    
    # 如果有需要安装的包
    if [ ${#packages_to_install[@]} -gt 0 ]; then
        echo ""
        info "Missing components detected. The following will be installed:"
        printf '  - %s\n' "${packages_to_install[@]}"
        echo ""
        info "Note: Installing docker-compose-v2 enables 'docker compose' command (V2 plugin version)"
        echo ""
        read -p "Do you want to install these components? (y/n): " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            info "Installing missing components..."
            sudo apt update
            sudo apt install -y "${packages_to_install[@]}"
            
            # 如果安装了 Docker，配置用户组和服务
            if [[ " ${packages_to_install[@]} " =~ " docker.io " ]]; then
                sudo usermod -aG docker $USER || true
                info "Added user $USER to docker group"
                info "You may need to log out and back in for group changes to take effect"
                
                sudo systemctl start docker || true
                sudo systemctl enable docker || true
                info "Docker service started and enabled"
            fi
            
            # 验证安装
            echo ""
            info "Verifying installation..."
            command -v docker >/dev/null 2>&1 && docker --version || warning "Docker not found"
            docker compose version >/dev/null 2>&1 && docker compose version || warning "docker compose plugin not found"
            echo ""
            info "Installation completed!"
            info "You can now use: docker compose up -d"
            return 0
            info "Installation completed!"
            return 0
        else
            error "Installation cancelled by user"
            return 1
        fi
    else
        info "All required components are already installed!"
        echo ""
        docker --version
        docker compose version 2>/dev/null || warning "docker compose plugin not available"
        echo ""
        return 0
    fi
}

# Function to uninstall Docker
uninstall_docker() {
    echo ""
    echo "=========================================="
    echo "Docker Uninstallation"
    echo "=========================================="
    echo ""
    echo "This will remove:"
    echo "  - docker.io / docker-ce"
    echo "  - docker-compose-plugin"
    echo "  - docker-buildx"
    echo "  - All Docker images, containers, volumes, and networks"
    echo ""
    read -p "Are you sure you want to uninstall Docker? (yes/no): " confirm
    
    if [[ "$confirm" == "yes" ]]; then
        info "Stopping Docker service..."
        sudo systemctl stop docker || true
        sudo systemctl disable docker || true
        
        info "Removing Docker packages..."
        # 只卸载 Ubuntu 仓库中存在的包
        sudo apt remove -y docker.io docker-compose docker-compose-v2 docker-buildx containerd 2>/dev/null || true
        sudo apt autoremove -y || true
        
        info "Removing user from docker group..."
        sudo gpasswd -d $USER docker || true
        
        read -p "Do you want to remove all Docker data (images, containers, volumes)? (yes/no): " remove_data
        if [[ "$remove_data" == "yes" ]]; then
            info "Removing Docker data directories..."
            sudo rm -rf /var/lib/docker || true
            sudo rm -rf /var/lib/containerd || true
            sudo rm -rf ~/.docker || true
            info "All Docker data removed"
        else
            info "Docker data preserved in /var/lib/docker"
        fi
        
        echo ""
        info "Docker has been uninstalled successfully!"
        echo ""
        safe_exit 0
    else
        error "Uninstallation cancelled."
        safe_exit 1
    fi
}

# Main script logic
echo ""
echo "=========================================="
echo "Docker Installation & Configuration Tool"
echo "=========================================="
echo ""

# 检查并安装缺失的组件
check_and_install_components

# 如果用户取消安装，询问是否继续配置
if [ $? -ne 0 ]; then
    echo ""
    read -p "Do you want to continue with configuration fixes? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        info "Exiting."
        safe_exit 0
    fi
fi

# 检查是否需要其他操作
if command -v docker >/dev/null 2>&1; then
    echo ""
    echo "What would you like to do next?"
    echo "1) Fix Docker configuration (switch context, remove credsStore)"
    echo "2) Reinstall all Docker components"
    echo "3) Uninstall Docker"
    echo "0) Exit"
    echo ""
    read -p "Enter your choice (1/2/3/0): " action
    
    case $action in
        1)
            info "Proceeding with Docker configuration fix..."
            ;;
        2)
            info "Reinstalling Docker..."
            # 先卸载（只卸载 Ubuntu 仓库中存在的包）
            sudo apt remove -y docker.io docker-compose docker-compose-v2 docker-buildx containerd 2>/dev/null || true
            sudo apt autoremove -y || true
            
            # 重新安装（只安装 V2 版本）
            info "Installing docker.io and related components..."
            sudo apt update
            sudo apt install -y docker.io docker-compose-v2 docker-buildx
            
            sudo usermod -aG docker $USER || true
            info "Added user $USER to docker group"
            
            sudo systemctl start docker || true
            sudo systemctl enable docker || true
            info "Docker service started and enabled"
            
            info "Verifying installation..."
            docker --version || true
            docker compose version || true
            info "You can now use: docker compose up -d"
            ;;
        3)
            uninstall_docker
            ;;
        0)
            info "Exiting without changes."
            safe_exit 0
            ;;
        *)
            error "Invalid choice. Exiting."
            safe_exit 1
            ;;
    esac
fi

# Docker Configuration Fix Section
# ================================

info "Switching docker context to 'default'"
# Use || true to prevent exit if context switching fails
docker context use default >/dev/null 2>&1 || true

CONFIG_FILE="${HOME}/.docker/config.json"
BACKUP_FILE="${CONFIG_FILE}.bak-$(date +%Y%m%d%H%M%S)"

if [ -f "$CONFIG_FILE" ]; then
    info "Backing up existing config to $BACKUP_FILE"
    cp "$CONFIG_FILE" "$BACKUP_FILE"
else
    info "Creating ${CONFIG_FILE}"
    mkdir -p "${HOME}/.docker"
    printf '{"auths":{}}' >"$CONFIG_FILE"
fi

info "Removing credsStore from ${CONFIG_FILE} if present"
# Use || true to prevent exit if Python script fails
python - <<'PY' || true
import json
from pathlib import Path

cfg = Path("~/.docker/config.json").expanduser()
data = {}
if cfg.exists():
    content = cfg.read_text().strip()
    if content:
        data = json.loads(content)

removed = data.pop("credsStore", None)
cfg.write_text(json.dumps(data, indent=4))
if removed:
    print("Removed credsStore entry")
else:
    print("credsStore was not set")
PY

# Final instructions and completion message
echo ""
echo "=============================================="
echo "Docker setup completed successfully!"
echo "=============================================="
echo ""
echo "Next steps:"
echo "1. If you installed docker.io, you may need to:"
echo "   - Log out and back in for group permissions to take effect"
echo "   - Or run: newgrp docker"
echo ""
echo "2. Test Docker installation:"
echo "   docker --version"
echo "   docker run hello-world"
echo ""
echo "3. For Docker Compose (V2 plugin), use:"
echo "   docker compose up -d"
echo "   docker compose down"
echo ""
echo "Note: If you get permission errors, try logging out and back in,"
echo "or run 'newgrp docker' to refresh group membership."
echo ""
