# hiPanda MCP 服务使用指南

## 概述

`hiPanda.py` 是运行在 MR 设备端的本地 MCP 工具服务，通过 HTTP API 为浏览器提供工具调用能力。

## 架构

```
┌─────────────────────────────────────────────────────────┐
│                    MR 设备 (本地)                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐         HTTP API        ┌──────────┐ │
│  │ 浏览器        │  ←─────────────────→   │ hiPanda  │ │
│  │ (tools.js)   │   localhost:8765        │ Python   │ │
│  └──────────────┘                         └──────────┘ │
│                                                         │
│  工具调用流程:                                           │
│  1. 服务器通过 WebSocket 发送 MCP tools/call            │
│  2. 浏览器接收并调用 executeHiPandaTool()               │
│  3. HTTP POST 到 http://127.0.0.1:8765/tools/call      │
│  4. hiPanda 执行 Python 工具函数                        │
│  5. 返回结果到浏览器                                     │
│  6. 浏览器返回结果到服务器                               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 启动 hiPanda 服务

### 方式 1: HTTP 服务（推荐用于浏览器）

```bash
cd /home/tester/AI_Tool/xiaozhi-esp32-server_sdk/main/xiaozhi-server/MR_MCP_Tool
python3 hiPanda_http.py
```

**输出**:
```
[hiPanda HTTP] MCP Server 运行在 http://127.0.0.1:8765
[hiPanda HTTP] 健康检查: http://127.0.0.1:8765/health
[hiPanda HTTP] 工具列表: http://127.0.0.1:8765/tools/list
[hiPanda HTTP] 工具调用: POST http://127.0.0.1:8765/tools/call
```

### 方式 2: stdio 服务（用于进程间通信）

```bash
python3 hiPanda.py
```

## API 端点

### 1. 健康检查

```bash
curl http://127.0.0.1:8765/health
```

**响应**:
```json
{
    "status": "ok",
    "server": "hiPanda HTTP MCP Server",
    "version": "1.0.0"
}
```

### 2. 获取工具列表

```bash
curl http://127.0.0.1:8765/tools/list
```

**响应**:
```json
{
    "tools": [
        {
            "name": "hello_world",
            "description": "在设备端打印 Hello World 消息，用于测试 MCP 工具调用流程",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "要问候的名字（可选，默认为 World）"
                    }
                }
            }
        }
    ]
}
```

### 3. 调用工具

```bash
curl -X POST http://127.0.0.1:8765/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "hello_world",
    "arguments": {
      "name": "MR User"
    }
  }'
```

**响应**:
```json
{
    "success": true,
    "message": "Hello, MR User! 🎉",
    "timestamp": "2026-01-21T10:30:00.123456",
    "device": "hiPanda HTTP MCP Server (Python)",
    "version": "1.0.0"
}
```

## 在浏览器中测试

### 1. 启动 hiPanda 服务

```bash
python3 hiPanda_http.py
```

### 2. 打开测试页面并执行

在浏览器控制台运行：

```javascript
// 测试 1: 无参数调用
const result1 = await executeMcpTool('hello_world', {});
console.log('结果 1:', result1);
// 输出: {success: true, message: "Hello, World! 🎉", timestamp: "...", device: "hiPanda HTTP MCP Server (Python)", version: "1.0.0"}

// 测试 2: 带参数调用
const result2 = await executeMcpTool('hello_world', { name: 'Alice' });
console.log('结果 2:', result2);
// 输出: {success: true, message: "Hello, Alice! 🎉", ...}
```

## 添加新工具

在 `hiPanda_http.py` 中添加新工具：

### 1. 在 TOOLS 字典中注册

```python
TOOLS = {
    "hello_world": {
        # ... 已有定义
    },
    
    # 新工具定义
    "get_device_info": {
        "name": "get_device_info",
        "description": "获取 MR 设备信息",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
}
```

### 2. 实现工具函数

```python
def _execute_get_device_info(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """获取设备信息"""
    import platform
    
    return {
        "success": True,
        "device_info": {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version()
        },
        "timestamp": datetime.now().isoformat()
    }
```

### 3. 在 handle_tools_call 中调用

```python
def handle_tools_call(self):
    # ... 现有代码 ...
    
    # 执行工具
    if tool_name == "hello_world":
        result = self._execute_hello_world(arguments)
    elif tool_name == "get_device_info":
        result = self._execute_get_device_info(arguments)
    else:
        result = {"error": f"Tool {tool_name} not implemented"}
```

### 4. 在 default-mcp-tools.json 中添加定义

```json
[
    {
        "name": "hello_world",
        "description": "..."
    },
    {
        "name": "get_device_info",
        "description": "获取 MR 设备信息",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]
```

## 完整执行流程

```
时刻  | 服务器                    | MR 设备浏览器              | hiPanda Python
-----|--------------------------|---------------------------|------------------
t=0  | LLM 决策调用 hello_world   |                           |
t=10 | 构建 MCP tools/call       |                           |
t=20 | WebSocket.send() →        |                           |
t=30 |                          | ← 接收 MCP 消息            |
t=40 |                          | handleMCPMessage()        |
t=50 |                          | executeMcpTool()          |
t=60 |                          | executeHiPandaTool()      |
t=70 |                          | HTTP POST →               |
t=80 |                          |                           | ← 接收 HTTP 请求
t=90 |                          |                           | _execute_hello_world()
t=100|                          |                           | 返回结果 →
t=110|                          | ← 接收 HTTP 响应           |
t=120|                          | 构建 MCP result           |
t=130|                          | WebSocket.send() →        |
t=140| ← 接收结果                |                           |
t=150| ✅ 完成                   |                           |
```

## 故障排查

### 问题 1: hiPanda 服务不可用

**症状**: 浏览器日志显示 `[hiPanda] 服务不可用`

**解决**:
```bash
# 检查服务是否运行
curl http://127.0.0.1:8765/health

# 如果没有响应，启动服务
python3 hiPanda_http.py
```

### 问题 2: CORS 错误

**症状**: 浏览器控制台显示 CORS 策略错误

**解决**: hiPanda HTTP 服务已经配置了 CORS 头允许所有来源，确保使用 `hiPanda_http.py` 而不是 `hiPanda.py`

### 问题 3: 工具未找到

**症状**: HTTP 404 错误

**检查**:
1. 工具是否在 `TOOLS` 字典中注册
2. 工具名称是否拼写正确
3. 工具是否在 `handle_tools_call` 中实现

## 与 ESP32-box 的对比

| 特性 | hiPanda (MR 设备) | ESP32-box |
|------|------------------|-----------|
| **语言** | Python | C/C++ |
| **通信** | HTTP (浏览器 ↔ Python) | WebSocket (直接到服务器) |
| **部署** | 本地 Python 进程 | 嵌入式固件 |
| **工具定义** | Python 字典 + HTTP API | MCP 协议实现 |
| **执行位置** | MR 设备本地 | ESP32 设备 |
| **扩展性** | 容易（添加 Python 函数） | 需要固件编译 |

## 优势

1. **开发便捷**: Python 开发比 C++ 快速
2. **调试简单**: 直接打印日志，无需串口
3. **功能丰富**: 可以使用 Python 生态系统的所有库
4. **易于扩展**: 添加新工具只需几行代码
5. **独立部署**: 可以独立于主服务器运行

## 生产部署建议

1. **安全**: 限制监听地址为 `127.0.0.1`（已配置）
2. **认证**: 添加 API 密钥验证
3. **日志**: 使用专业日志库（如 `logging`）
4. **进程管理**: 使用 systemd 或 supervisor 管理
5. **错误处理**: 添加更详细的错误处理和重试逻辑
