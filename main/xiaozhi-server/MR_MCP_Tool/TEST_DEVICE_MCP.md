# 测试设备端 MCP 工具调用

## 概述

本测试演示**设备端（MR设备/浏览器）本地实现工具**的 MCP 调用流程，模拟 ESP32-box 的工作方式。

## 架构说明

```
服务器端 (xiaozhi-server)
    ↓ LLM 决策需要调用工具
    ↓ 通过 WebSocket 发送 MCP 消息
    
MR 设备端 (浏览器)
    ↓ 接收 MCP tools/call 请求
    ↓ 在本地执行 hello_world() 函数
    ↓ 返回执行结果
    
服务器端
    ↓ 接收结果
    ↓ LLM 生成自然语言回复
    ✅ 完成
```

## 工具定义

### hello_world

**位置**: `tools.js` 中的 `localToolImplementations.hello_world`

**功能**: 在设备端打印问候消息

**参数**:
- `name` (string, 可选): 要问候的名字，默认为 "World"

**返回**:
```json
{
    "success": true,
    "message": "Hello, {name}! 🎉",
    "timestamp": "2026-01-21T10:30:00.000Z",
    "device": "MR Device (Browser)"
}
```

## 测试步骤

### 1. 准备工作

确保 `default-mcp-tools.json` 中已定义 `hello_world` 工具（已自动创建）。

### 2. 启动服务器

```bash
cd /home/tester/AI_Tool/xiaozhi-esp32-server_sdk/main/xiaozhi-server
python app.py
```

### 3. 打开测试页面

访问 MR_MCP_Tool 测试页面，连接 WebSocket。

### 4. 服务器发送 MCP 调用

当服务器发送以下消息时：

```json
{
    "type": "mcp",
    "session_id": "xxx",
    "payload": {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "hello_world",
            "arguments": {
                "name": "MR User"
            }
        }
    }
}
```

### 5. 查看执行过程

**浏览器控制台日志**:
```
[INFO] 收到服务器消息: {"type":"mcp",...}
[SUCCESS] [本地工具] hello_world 执行: Hello, MR User! 🎉
[SUCCESS] 本地工具 hello_world 执行成功
[INFO] 工具 hello_world 通过本地实现执行
[INFO] 回复服务器: {"jsonrpc":"2.0","id":3,"result":{...}}
```

**设备端返回给服务器**:
```json
{
    "session_id": "xxx",
    "type": "mcp",
    "payload": {
        "jsonrpc": "2.0",
        "id": 3,
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": "{\"success\":true,\"message\":\"Hello, MR User! 🎉\",\"timestamp\":\"2026-01-21T10:30:00.000Z\",\"device\":\"MR Device (Browser)\"}"
                }
            ],
            "isError": false
        }
    }
}
```

## 模拟服务器调用（测试用）

在浏览器控制台手动触发测试：

```javascript
// 模拟服务器发送的 MCP 调用
const mockServerCall = {
    type: 'mcp',
    session_id: 'test-session-001',
    payload: {
        jsonrpc: '2.0',
        id: 999,
        method: 'tools/call',
        params: {
            name: 'hello_world',
            arguments: {
                name: 'Test User'
            }
        }
    }
};

// 触发处理（需要在 websocket.js 中暴露 handleTextMessage）
// 或者直接调用本地函数测试
const result = executeMcpTool('hello_world', { name: 'Test User' });
console.log('本地执行结果:', result);
```

**预期输出**:
```javascript
{
    success: true,
    message: "Hello, Test User! 🎉",
    timestamp: "2026-01-21T10:30:00.000Z",
    device: "MR Device (Browser)"
}
```

## 添加新的本地工具

在 `tools.js` 的 `localToolImplementations` 中添加：

```javascript
const localToolImplementations = {
    hello_world: function(args) {
        // ... 已有实现
    },
    
    // 新工具示例：获取设备信息
    get_device_info: function(args) {
        return {
            success: true,
            device_type: 'MR Headset',
            browser: navigator.userAgent,
            screen: {
                width: window.screen.width,
                height: window.screen.height
            },
            timestamp: new Date().toISOString()
        };
    },
    
    // 新工具示例：播放提示音
    play_notification: function(args) {
        const type = args.type || 'success';
        // 实际实现播放音频的逻辑
        log(`播放提示音: ${type}`, 'info');
        return {
            success: true,
            message: `提示音 ${type} 已播放`
        };
    }
};
```

同时在 `default-mcp-tools.json` 中添加工具定义：

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
    },
    {
        "name": "play_notification",
        "description": "播放提示音",
        "inputSchema": {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["success", "warning", "error", "info"],
                    "description": "提示音类型"
                }
            }
        }
    }
]
```

## 与 ESP32-box 的对比

| 方面 | MR 设备（浏览器） | ESP32-box |
|------|-----------------|-----------|
| **实现语言** | JavaScript | C/C++ |
| **工具定义** | JSON + JS 函数 | MCP 服务端实现 |
| **执行位置** | 浏览器 | 设备固件 |
| **通信协议** | WebSocket + MCP | WebSocket + MCP |
| **工具发现** | tools/list 响应 | tools/list 响应 |
| **工具调用** | tools/call → 本地执行 | tools/call → 固件执行 |

## 数据流时序图

```
时刻  | 服务器                           | MR 设备（浏览器）
-----|----------------------------------|----------------------------------
t=0  | LLM: 需要调用 hello_world         |
t=10 | 构建 MCP tools/call 消息          |
t=20 | WebSocket.send(mcp_message) →    |
t=30 |                                  | ← 接收 WebSocket 消息
t=40 |                                  | handleMCPMessage() 解析
t=50 |                                  | executeMcpTool('hello_world', {name: 'Alice'})
t=60 |                                  | executeLocalTool() 执行
t=70 |                                  | localToolImplementations.hello_world()
t=80 |                                  | 返回: {success: true, message: "Hello, Alice! 🎉"}
t=90 |                                  | 构建 MCP result 响应
t=100|                                  | WebSocket.send(result) →
t=110| ← 接收响应                        |
t=120| handle_mcp_message() 处理         |
t=130| 提取 result.content[0].text       |
t=140| LLM: 生成自然语言回复              |
t=150| ✅ 完成                           |
```

## 优势

1. **低延迟**: 工具在设备端本地执行，无需网络往返
2. **离线能力**: 部分功能可离线运行
3. **设备特定**: 可访问设备独有的硬件和传感器
4. **符合架构**: 与 ESP32-box 的 DEVICE_MCP 模式一致

## 下一步

1. 添加更多实用工具（设备信息、传感器数据等）
2. 与 MR 设备的原生 API 集成
3. 测试复杂工具调用场景
4. 性能优化和错误处理
