#!/usr/bin/env python3
"""
MCP HTTP Bridge - 将 mcp_function_calling_definition.py 暴露为 HTTP 服务
使 tools.js 可以通过 HTTP 调用 MCP 工具

与后端实现的区别:
1. 后端实现: xiaozhi-server → WebSocket → Browser
2. HTTP Bridge: Browser → HTTP (localhost) → MCP Tools (MR 设备本地)

这样 MCP 工具运行在 MR 设备上，而不是远程服务器上！
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import sys
import os
from datetime import datetime
import importlib.util
import inspect
import re

# 导入 MCP 工具定义
# 这里通过动态导入 mcp_function_calling_definition.py 中的工具
sys.path.insert(0, os.path.dirname(__file__))

class MCPHTTPBridge(BaseHTTPRequestHandler):
    """
    将 MCP 工具暴露为 HTTP 接口
    兼容 tools.js 的 executeHiPandaTool() 调用格式
    """
    
    # 从 mcp_function_calling_definition.py 导入的工具函数
    MCP_TOOLS = {}
    
    @classmethod
    def load_mcp_tools(cls):
        """从 mcp_function_calling_definition.py 加载所有 @server.tool() 工具"""
        try:
            # 直接导入模块（已移除 mcp 依赖）
            import mcp_function_calling_definition as mcp_tools
            
            # 读取源代码提取工具信息
            mcp_file = os.path.join(os.path.dirname(__file__), "mcp_function_calling_definition.py")
            with open(mcp_file, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            # 正则提取函数名和文档
            pattern = r'@server\.tool\(\)\s+def\s+(\w+)\s*\(([^)]*)\)\s*->\s*\w+:\s*"""(.*?)"""'
            matches = re.findall(pattern, source_code, re.DOTALL)
            
            print(f"[MCP HTTP Bridge] 找到 {len(matches)} 个工具定义", file=sys.stderr)
            
            # 构建工具列表
            for tool_name, params_str, doc_string in matches:
                if hasattr(mcp_tools, tool_name):
                    func = getattr(mcp_tools, tool_name)
                    
                    # 解析文档
                    description = doc_string.strip().split('\n')[0].strip()
                    
                    # 提取参数
                    params_section = re.search(r'Parameters:\s*\n(.*?)(?:Returns:|$)', doc_string, re.DOTALL)
                    parameters = {}
                    
                    if params_section:
                        param_lines = params_section.group(1).strip().split('\n')
                        for line in param_lines:
                            param_match = re.match(r'\s*(\w+)\s*\(([^)]+)\):\s*(.+)', line.strip())
                            if param_match:
                                param_name = param_match.group(1)
                                param_type = param_match.group(2).strip()
                                param_desc = param_match.group(3).strip()
                                
                                json_type = 'string'
                                if 'int' in param_type.lower():
                                    json_type = 'integer'
                                elif 'float' in param_type.lower():
                                    json_type = 'number'
                                
                                parameters[param_name] = {
                                    'type': json_type,
                                    'description': param_desc
                                }
                    
                    cls.MCP_TOOLS[tool_name] = {
                        'function': func,
                        'schema': {
                            'name': tool_name,
                            'description': description,
                            'inputSchema': {
                                'type': 'object',
                                'properties': parameters
                            }
                        }
                    }
            
            print(f"[MCP HTTP Bridge] 已加载 {len(cls.MCP_TOOLS)} 个 MCP 工具", file=sys.stderr)
                
        except Exception as e:
            print(f"[MCP HTTP Bridge] 加载工具失败: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
    
    def _set_cors_headers(self):
        """设置 CORS 头，允许浏览器跨域访问"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def do_OPTIONS(self):
        """处理 CORS 预检请求"""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        """处理 GET 请求"""
        if self.path == '/health':
            self.handle_health()
        elif self.path == '/tools/list':
            self.handle_tools_list()
        else:
            self.send_error(404, "Not Found")
    
    def do_POST(self):
        """处理 POST 请求"""
        if self.path == '/tools/call':
            self.handle_tools_call()
        else:
            self.send_error(404, "Not Found")
    
    def handle_health(self):
        """健康检查"""
        self.send_response(200)
        self._set_cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        response = {
            "status": "ok",
            "server": "MCP HTTP Bridge",
            "mcp_tools_count": len(self.MCP_TOOLS),
            "timestamp": datetime.now().isoformat()
        }
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
    
    def handle_tools_list(self):
        """返回所有可用工具列表"""
        self.send_response(200)
        self._set_cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        tools = [
            {
                "name": tool_info['schema']['name'],
                "description": tool_info['schema']['description'],
                "inputSchema": tool_info['schema']['inputSchema']
            }
            for tool_info in self.MCP_TOOLS.values()
        ]
        
        response = {"tools": tools}
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
    
    def handle_tools_call(self):
        """执行工具调用"""
        try:
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            # 解析 JSON 请求
            request = json.loads(post_data)
            tool_name = request.get('name')
            arguments = request.get('arguments', {})
            
            print(f"[MCP HTTP Bridge] 调用工具: {tool_name}, 参数: {arguments}", file=sys.stderr)
            
            # 检查工具是否存在
            if tool_name not in self.MCP_TOOLS:
                self.send_response(404)
                self._set_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                
                response = {
                    "success": False,
                    "error": f"工具 {tool_name} 不存在",
                    "available_tools": list(self.MCP_TOOLS.keys())
                }
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                return
            
            # 执行工具
            tool_func = self.MCP_TOOLS[tool_name]['function']
            
            # 获取函数签名并准备参数
            sig = inspect.signature(tool_func)
            prepared_args = {}
            for param_name in sig.parameters:
                if param_name in arguments:
                    prepared_args[param_name] = arguments[param_name]
            
            # 调用函数
            result = tool_func(**prepared_args)
            
            # 返回结果
            self.send_response(200)
            self._set_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            response = {
                "success": True,
                "result": result,
                "tool": tool_name,
                "arguments": prepared_args,
                "timestamp": datetime.now().isoformat(),
                "device": "MCP HTTP Bridge (MR Device)"
            }
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
            print(f"[MCP HTTP Bridge] 工具 {tool_name} 执行成功", file=sys.stderr)
            
        except Exception as e:
            print(f"[MCP HTTP Bridge] 执行失败: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            
            self.send_response(500)
            self._set_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            response = {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))


def main():
    """启动 HTTP 服务器"""
    # 加载 MCP 工具
    MCPHTTPBridge.load_mcp_tools()
    
    # 启动服务器
    port = 8765
    server = HTTPServer(('127.0.0.1', port), MCPHTTPBridge)
    
    print(f"[MCP HTTP Bridge] 启动成功", file=sys.stderr)
    print(f"[MCP HTTP Bridge] 监听地址: http://127.0.0.1:{port}", file=sys.stderr)
    print(f"[MCP HTTP Bridge] 可用工具: {len(MCPHTTPBridge.MCP_TOOLS)} 个", file=sys.stderr)
    print(f"[MCP HTTP Bridge] 健康检查: curl http://127.0.0.1:{port}/health", file=sys.stderr)
    print(f"[MCP HTTP Bridge] 工具列表: curl http://127.0.0.1:{port}/tools/list", file=sys.stderr)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[MCP HTTP Bridge] 服务器关闭", file=sys.stderr)
        server.shutdown()


if __name__ == "__main__":
    main()
