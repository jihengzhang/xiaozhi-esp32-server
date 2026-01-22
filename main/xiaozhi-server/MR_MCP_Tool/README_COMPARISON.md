# hiPanda 运行方式对比

## 三种运行方式

### 1. PyWebView 方式（推荐 - 无需 HTTP）✨

**特点**: JavaScript 直接调用 Python 函数，无需 HTTP 服务

**架构**:
```
┌──────────────────────────────────┐
│     hiPanda PyWebView 应用        │
├──────────────────────────────────┤
│  JavaScript (WebView)             │
│     ↕ 直接调用                    │
│  Python (hiPanda API)             │
└──────────────────────────────────┘
```

**启动**:
```bash
# 1. 安装依赖
pip3 install pywebview

# 2. 运行应用
cd /home/tester/AI_Tool/xiaozhi-esp32-server_sdk/main/xiaozhi-server/MR_MCP_Tool
python3 hiPanda_webview.py
```

**JavaScript 调用**:
```javascript
// 直接调用 Python 函数，无需 HTTP！
const result = await window.pywebview.api.hello_world("Alice");
console.log(result);
// 输出: {success: true, message: "Hello, Alice! 🎉", ...}
```

**优点**:
- ✅ 无需启动 HTTP 服务
- ✅ 直接调用，延迟最低（<1ms）
- ✅ 自动集成 WebView 窗口
- ✅ 可以打包成独立应用

**缺点**:
- ❌ 需要重构为 PyWebView 应用
- ❌ 需要安装 pywebview 依赖

---

### 2. HTTP 服务方式（灵活 - 适合浏览器）

**特点**: Python HTTP 服务器，浏览器通过 HTTP API 调用

**架构**:
```
┌──────────────┐      HTTP API      ┌──────────────┐
│   浏览器      │  ←─────────────→  │ hiPanda HTTP │
│ (任何浏览器)  │  localhost:8765    │   Python     │
└──────────────┘                    └──────────────┘
```

**启动**:
```bash
python3 hiPanda_http.py
```

**JavaScript 调用**:
```javascript
// 通过 HTTP POST 调用
const result = await executeMcpTool('hello_world', {name: 'Alice'});
```

**优点**:
- ✅ 适用于任何浏览器
- ✅ 无需修改现有代码
- ✅ RESTful API，易于测试
- ✅ 可以远程调用（如果开放端口）

**缺点**:
- ❌ 需要单独启动服务
- ❌ 有网络延迟（50-100ms）
- ❌ 需要处理 CORS

---

### 3. stdio 方式（进程间通信）

**特点**: 标准输入/输出模式，通过管道通信

**架构**:
```
┌──────────────┐      stdin/stdout   ┌──────────────┐
│  主进程       │  ←─────────────→   │ hiPanda      │
│              │     JSON-RPC        │   Python     │
└──────────────┘                     └──────────────┘
```

**启动**:
```bash
python3 hiPanda.py
# 然后通过 stdin 发送 JSON 请求
```

**用途**:
- 进程间通信
- MCP 标准协议
- 命令行工具

---

## 性能对比

| 方式 | 延迟 | CPU | 内存 | 适用场景 |
|------|------|-----|------|---------|
| **PyWebView** | <1ms | 低 | 中 | MR 设备应用 |
| **HTTP** | 50-100ms | 低 | 低 | 浏览器测试 |
| **stdio** | 5-10ms | 低 | 低 | 进程通信 |

---

## 推荐方案

### 场景 1: MR 设备独立应用
**使用**: **PyWebView 方式**
```bash
python3 hiPanda_webview.py
```

- JavaScript 直接调用 Python
- 无需 HTTP 服务
- 可以打包成 exe/app

### 场景 2: 浏览器开发测试
**使用**: **HTTP 方式**
```bash
python3 hiPanda_http.py
```

- 在任何浏览器中测试
- 方便调试
- 可以用 curl 测试

### 场景 3: 与其他服务集成
**使用**: **stdio 方式**
```bash
python3 hiPanda.py
```

- 标准 MCP 协议
- 易于集成

---

## 快速测试

### PyWebView 测试

```bash
# 1. 安装
pip3 install pywebview

# 2. 运行
python3 hiPanda_webview.py
```

在打开的窗口中按 F12 打开开发者工具，执行：
```javascript
// 直接调用 Python 函数
const result = await window.pywebview.api.hello_world("PyWebView User");
console.log(result);
```

### HTTP 测试

```bash
# 1. 启动服务
python3 hiPanda_http.py

# 2. 测试（新终端）
curl http://127.0.0.1:8765/health
curl -X POST http://127.0.0.1:8765/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "hello_world", "arguments": {"name": "HTTP User"}}'
```

---

## 代码已自动切换

`tools.js` 已经实现了自动检测和切换：

```javascript
// 自动检测运行环境
const isPyWebView = typeof window.pywebview !== 'undefined';

export async function executeMcpTool(toolName, toolArgs) {
    // 1️⃣ 优先使用 PyWebView 直接调用（无 HTTP）
    if (isPyWebView) {
        return await executePyWebViewTool(toolName, toolArgs);
    }
    
    // 2️⃣ 回退到 HTTP 方式
    return await executeHiPandaTool(toolName, toolArgs);
}
```

**工作原理**:
- 在 PyWebView 环境中：自动使用 `window.pywebview.api` 直接调用
- 在普通浏览器中：自动回退到 HTTP API 调用

---

## 总结

对于你的 MR 设备场景，**最佳方案是 PyWebView**：

1. **无需 HTTP** - JavaScript 直接调用 Python 函数
2. **性能最优** - 延迟 <1ms
3. **部署简单** - 单个应用，无需启动多个服务
4. **扩展方便** - 在 Python 中添加函数，JavaScript 立即可用

只需在 `hiPanda_webview.py` 的 `HiPandaAPI` 类中添加方法，JavaScript 就能通过 `window.pywebview.api.your_method()` 调用！
