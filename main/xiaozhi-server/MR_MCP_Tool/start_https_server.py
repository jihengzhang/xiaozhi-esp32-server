#!/usr/bin/env python3
"""
HTTPS Test Server for Audio Recording
Allows getUserMedia to work with LAN IP addresses
"""

import http.server
import ssl
import os
import sys
import yaml
import json
import subprocess
from urllib.parse import urlparse

# Configuration
PORT = 8006
CERT_FILE = './ssl/cert.pem'
KEY_FILE = './ssl/key.pem'

# Global config
CONFIG = None

def load_config():
    """从配置文件加载地址信息"""
    global CONFIG
    config_path = '../data/.config.yaml'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            CONFIG = yaml.safe_load(f)
        return CONFIG
    except Exception as e:
        print(f"⚠️  Warning: Could not load config file: {e}")
        return None

def extract_host_from_url(url):
    """从URL中提取host (移除协议和端口和路径)"""
    if not url:
        return None
    # 移除协议前缀 (ws://, http://, https://, wss://)
    url = url.replace('ws://', '').replace('wss://', '').replace('http://', '').replace('https://', '')
    # 提取host:port部分（在第一个/之前）
    host_port = url.split('/')[0]
    # 如果是 host:port 格式，只提取 host 部分
    if ':' in host_port:
        host = host_port.split(':')[0]
    else:
        host = host_port
    return host

def check_firewall_port(port):
    """检查防火墙是否已开放指定端口"""
    try:
        result = subprocess.run(['sudo', 'ufw', 'status'], capture_output=True, text=True)
        if result.returncode == 0:
            return f"{port}/tcp" in result.stdout or f"{port}/udp" in result.stdout
    except Exception as e:
        print(f"⚠️  无法检查防火墙状态: {e}")
    return None

def open_firewall_port(port, protocol='tcp'):
    """打开防火墙端口"""
    try:
        print(f"🔧 尝试打开防火墙端口 {port}/{protocol}...")
        result = subprocess.run(['sudo', 'ufw', 'allow', f'{port}/{protocol}'], 
                              capture_output=True, text=True, input='y\n')
        if result.returncode == 0:
            print(f"✅ 防火墙端口 {port}/{protocol} 已打开")
            return True
        else:
            print(f"❌ 打开防火墙端口失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 无法打开防火墙: {e}")
        return False

def ensure_firewall_ports():
    """确保必要的防火墙端口已开放（非阻塞方式）"""
    ports = [8003, 8006]  # OTA服务器和HTTPS测试服务器
    
    print("\n" + "="*60)
    print("🔐 防火墙端口检查")
    print("="*60)
    
    # 跳过防火墙检查，直接启动服务
    # 因为可能需要 sudo 密码而导致阻塞
    print("⏭️  跳过防火墙检查（如需要，请手动运行）")
    print(f"   sudo ufw allow 8003/tcp && sudo ufw allow 8006/tcp")
    
    print("="*60 + "\n")

class ConfigHTTPHandler(http.server.SimpleHTTPRequestHandler):
    """自定义HTTP处理器，支持API端点"""
    
    def do_GET(self):
        # 处理 /api/config 端点
        if self.path == '/api/config':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            config_data = {}
            if CONFIG and CONFIG.get('server'):
                server_config = CONFIG['server']
                config_data = {
                    'websocket': server_config.get('websocket', ''),
                    'ota_url': server_config.get('ota_url', ''),
                    'vision_explain': server_config.get('vision_explain', ''),
                }
            
            self.wfile.write(json.dumps(config_data).encode())
            return
        
        # 其他路径使用默认处理器
        super().do_GET()
    
    def do_OPTIONS(self):
        # 处理CORS preflight请求
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def main():
    # 检查防火墙端口
    ensure_firewall_ports()
    
    # Check if certificates exist
    cert_dir = os.path.abspath(os.path.dirname(CERT_FILE))
    if not os.path.exists(CERT_FILE) or not os.path.exists(KEY_FILE):
        print(f"❌ SSL certificates not found in directory: {cert_dir}")
        print(f"  Expected cert file: {os.path.abspath(CERT_FILE)}")
        print(f"  Expected key file:  {os.path.abspath(KEY_FILE)}")
        print("Please run: bash generate_cert.sh")
        return
    
    # 从配置文件读取地址
    config = load_config()
    server_host = "192.168.0.114"  # 默认值
    
    if config and config.get('server'):
        server_config = config['server']
        websocket_url = server_config.get('websocket', '')
        if websocket_url:
            extracted_host = extract_host_from_url(websocket_url)
            if extracted_host:
                server_host = extracted_host
                print(f"ℹ️  从配置文件读取地址: {server_host}")
    
    # Create HTTPS server
    server_address = ('0.0.0.0', PORT)
    httpd = http.server.HTTPServer(server_address, ConfigHTTPHandler)
    
    # Create SSL context and wrap socket
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
    httpd.socket = ssl_context.wrap_socket(httpd.socket, server_side=True)
    
    print("=" * 60)
    print("🔒 HTTPS Test Server Started")
    print("=" * 60)
    print(f"Port: {PORT}")
    print(f"Certificate: {CERT_FILE}")
    print("")
    print("Access URLs:")
    print(f"  Local:   https://localhost:{PORT}/MR_MCP_page.html")
    print(f"  Network: https://{server_host}:{PORT}/MR_MCP_page.html")
    print("")
    print("API Endpoints:")
    print(f"  Config:  https://{server_host}:{PORT}/api/config")
    print("")
    print("⚠️  Note: You will see a security warning because this is")
    print("    a self-signed certificate. Click 'Advanced' and")
    print("    'Proceed to localhost (unsafe)' to continue.")
    print("")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped")

if __name__ == '__main__':
    main()
