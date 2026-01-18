#!/usr/bin/env python3
"""
HTTPS Test Server for Audio Recording
Allows getUserMedia to work with LAN IP addresses
"""

import http.server
import ssl
import os

# Configuration
PORT = 8006
CERT_FILE = './ssl/cert.pem'
KEY_FILE = './ssl/key.pem'

def main():
    # Check if certificates exist
    if not os.path.exists(CERT_FILE) or not os.path.exists(KEY_FILE):
        print("❌ SSL certificates not found!")
        print("Please run: bash generate_cert.sh")
        return
    
    # Create HTTPS server
    server_address = ('0.0.0.0', PORT)
    httpd = http.server.HTTPServer(server_address, http.server.SimpleHTTPRequestHandler)
    
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
    print(f"  Local:   https://localhost:{PORT}/test_page.html")
    print(f"  Network: https://192.168.0.114:{PORT}/test_page.html")
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
