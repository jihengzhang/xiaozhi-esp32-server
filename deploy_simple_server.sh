#!/usr/bin/env bash
set -euo pipefail

# 小智ESP32服务器 - 简易部署脚本（Docker方式）
# 参考文档: https://github.com/xinnan-tech/xiaozhi-esp32-server/blob/main/docs/Deployment.md

info() { printf '\033[0;32m[INFO]\033[0m %s\n' "$*"; }
error() { printf '\033[0;31m[ERROR]\033[0m %s\n' "$*" >&2; }
warn() { printf '\033[0;33m[WARN]\033[0m %s\n' "$*"; }

# 检查Docker是否安装
if ! command -v docker >/dev/null 2>&1; then
    error "Docker未安装，请先安装Docker"
    error "参考: https://www.runoob.com/docker/ubuntu-docker-install.html"
    exit 1
fi

# 目标部署目录
DEPLOY_DIR="${HOME}/AI_Tools/xiaozhi-server"
info "目标部署目录: ${DEPLOY_DIR}"

# 1. 创建目录结构
info "步骤 1/5: 创建目录结构"
mkdir -p "${DEPLOY_DIR}"/{data,models/SenseVoiceSmall}

# 2. 下载docker-compose.yml
info "步骤 2/5: 下载 docker-compose.yml"
DOCKER_COMPOSE_URL="https://raw.githubusercontent.com/xinnan-tech/xiaozhi-esp32-server/main/main/xiaozhi-server/docker-compose.yml"
if ! curl -fsSL "${DOCKER_COMPOSE_URL}" -o "${DEPLOY_DIR}/docker-compose.yml"; then
    error "下载 docker-compose.yml 失败"
    exit 1
fi

# 3. 下载config.yaml模板到data目录并重命名为.config.yaml
info "步骤 3/5: 下载配置文件模板"
CONFIG_URL="https://raw.githubusercontent.com/xinnan-tech/xiaozhi-esp32-server/main/main/xiaozhi-server/config.yaml"
if ! curl -fsSL "${CONFIG_URL}" -o "${DEPLOY_DIR}/data/.config.yaml"; then
    error "下载 config.yaml 失败"
    exit 1
fi

# 4. 下载语音识别模型文件
info "步骤 4/5: 下载语音识别模型文件 SenseVoiceSmall/model.pt"
MODEL_FILE="${DEPLOY_DIR}/models/SenseVoiceSmall/model.pt"

if [ -f "${MODEL_FILE}" ]; then
    info "模型文件已存在，跳过下载"
else
    warn "模型文件较大(约890MB)，下载可能需要较长时间"
    MODEL_URL="https://modelscope.cn/models/iic/SenseVoiceSmall/resolve/master/model.pt"
    
    if ! curl -fL --progress-bar "${MODEL_URL}" -o "${MODEL_FILE}"; then
        error "模型文件下载失败"
        error "请手动下载并放置到: ${MODEL_FILE}"
        error "下载地址1: ${MODEL_URL}"
        error "下载地址2(备用): https://pan.baidu.com/share/init?surl=QlgM58FHhYv1tFnUT_A8Sg&pwd=qvna"
        exit 1
    fi
fi

# 5. 检查目录结构
info "步骤 5/5: 验证目录结构"
if [ ! -f "${DEPLOY_DIR}/docker-compose.yml" ] || \
   [ ! -f "${DEPLOY_DIR}/data/.config.yaml" ] || \
   [ ! -f "${MODEL_FILE}" ]; then
    error "目录结构不完整，部署失败"
    exit 1
fi

info "目录结构验证成功:"
tree -L 3 "${DEPLOY_DIR}" 2>/dev/null || ls -R "${DEPLOY_DIR}"

# 显示配置提示
echo ""
warn "=========================================="
warn "部署文件准备完成！"
warn "=========================================="
echo ""
info "下一步操作:"
info "1. 编辑配置文件: ${DEPLOY_DIR}/data/.config.yaml"
info "   - 配置LLM的API key（如ChatGLM、Doubao等）"
info "   - 配置server.websocket地址为你的局域网IP"
echo ""
info "2. 启动服务:"
info "   cd ${DEPLOY_DIR}"
info "   docker compose up -d"
echo ""
info "3. 查看日志:"
info "   docker logs -f xiaozhi-esp32-server"
echo ""
info "4. 验证服务:"
info "   - WebSocket地址: ws://你的IP:8000/xiaozhi/v1/"
info "   - OTA接口: http://你的IP:8003/xiaozhi/ota/"
echo ""
warn "=========================================="
