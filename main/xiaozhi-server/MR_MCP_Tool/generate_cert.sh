#!/bin/bash

# 为测试服务器生成自签名证书
# 用于在局域网中通过 HTTPS 访问

CERT_DIR="./ssl"
CERT_FILE="$CERT_DIR/cert.pem"
KEY_FILE="$CERT_DIR/key.pem"

# 创建证书目录
mkdir -p $CERT_DIR

echo "Generating self-signed SSL certificate..."

# 生成自签名证书（有效期365天）
openssl req -new -x509 -keyout $KEY_FILE -out $CERT_FILE -days 365 -nodes \
    -subj "/C=CN/ST=State/L=City/O=HiPanda/OU=Test/CN=192.168.0.114"

echo ""
echo "✅ Certificate generated successfully!"
echo ""
echo "Certificate: $CERT_FILE"
echo "Private Key: $KEY_FILE"
echo ""
echo "To start HTTPS server, run:"
echo "python3 start_https_server.py"
