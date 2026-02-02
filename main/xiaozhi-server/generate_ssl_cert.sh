#!/bin/bash

# 为 xiaozhi-server 生成 SSL 证书
# 支持 HTTPS 和 WSS (WebSocket Secure)

# 获取脚本所在目录的绝对路径
# SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CERT_DIR="./ssl"
CERT_FILE="$CERT_DIR/server.crt"
KEY_FILE="$CERT_DIR/server.key"

# 创建证书目录
mkdir -p $CERT_DIR

echo "🔐 Generating SSL certificate for xiaozhi-server..."
echo ""

# 获取本机IP
LOCAL_IP=$(hostname -I | awk '{print $1}')

# 生成自签名证书（有效期365天）
# 支持 localhost, 127.0.0.1 和本机局域网IP
openssl req -new -x509 -days 365 -nodes \
    -keyout "$KEY_FILE" \
    -out "$CERT_FILE" \
    -subj "/C=CN/ST=State/L=City/O=HiPanda/OU=Server/CN=$LOCAL_IP" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1,IP:$LOCAL_IP"

# 设置权限
chmod 600 "$KEY_FILE"
chmod 644 "$CERT_FILE"

echo ""
echo "✅ SSL certificate generated successfully!"
echo ""
echo "Certificate: $CERT_FILE"
echo "Private Key: $KEY_FILE"
echo "Valid for:   localhost, 127.0.0.1, $LOCAL_IP"
echo ""
echo "📝 Next steps:"
echo "1. Update config.yaml:"
echo "   server:"
echo "     ssl:"
echo "       enabled: true"
echo "       cert_file: $CERT_FILE"
echo "       key_file: $KEY_FILE"
echo ""
echo "2. Restart xiaozhi-server"
echo ""
echo "3. Access via:"
echo "   - HTTPS: https://$LOCAL_IP:8002/xiaozhi/ota/"
echo "   - WSS:   wss://$LOCAL_IP:8000/xiaozhi/v1/"
echo ""
