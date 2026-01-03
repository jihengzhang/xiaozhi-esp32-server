# 小智ESP32服务器部署记录

## 关键操作记录 (2025-12-23)

### 1. 修复Docker连接问题

**问题：** 执行 `docker compose up -d` 时报错无法连接到Docker daemon

```
Cannot connect to the Docker daemon at unix:///home/tester/.docker/desktop/docker.sock. Is the docker daemon running?
error getting credentials - err: exec: "docker-credential-desktop": executable file not found in $PATH
```

**解决方案：**

1. 切换Docker context到default：
   ```bash
   docker context use default
   ```

2. 移除Docker Desktop的credential helper配置：
   ```bash
   # 备份配置文件
   cp ~/.docker/config.json ~/.docker/config.json.bak
   
   # 移除 credsStore 字段（使用fix_dock.sh脚本自动完成）
   ./fix_dock.sh
   ```

**脚本：** `fix_dock.sh` - 自动化修复Docker配置的脚本

---

### 2. 移除旧容器解决挂载错误

**问题：** 容器启动时报错文件挂载失败

```
Error response from daemon: failed to create task for container: ... error mounting .../models/SenseVoiceSmall/model.pt
```

**解决方案：**

移除旧的容器实例，让docker compose重新创建：

```bash
# 查看所有容器（包括已停止的）
docker ps -a

# 移除旧容器
docker rm xiaozhi-esp32-server

# 重新启动服务
docker compose up -d
```

---

## 服务验证

启动成功后，可通过以下方式验证：

```bash
# 查看运行状态
docker ps

# 查看服务日志
docker logs -f xiaozhi-esp32-server

# 测试端口连通性
curl http://localhost:8003/xiaozhi/ota/
```

## 服务端口

- **8000**: WebSocket服务端口 `ws://localhost:8000/xiaozhi/v1/`
- **8003**: HTTP服务端口（OTA接口和视觉分析接口）

## 配置说明

- 配置文件：`data/config.yaml`
- 模型文件：`models/SenseVoiceSmall/model.pt`
- 需要配置LLM的API key才能使用对话功能

---

## 启动日志示例

服务正常启动后的日志输出（最后20行）：

```
2025-12-23 21:15:20 [W:onnxruntime:Default] GPU device discovery failed
251223 21:15:21 [core.utils.gc_manager]-INFO-启动全局GC管理器，间隔300秒
251223 21:15:22 [core.providers.llm.openai.openai]-ERROR-配置错误: LLM 的 API key 未设置,当前值为: 你的doubao web key
251223 21:15:22 [core.utils.modules_initialize]-INFO-初始化组件: llm成功 DoubaoLLM
251223 21:15:22 [core.utils.modules_initialize]-INFO-初始化组件: intent成功 function_call
251223 21:15:22 [core.utils.modules_initialize]-INFO-初始化组件: memory成功 nomem
251223 21:15:25 [core.providers.vad.silero]-INFO-SileroVAD
251223 21:15:26 [core.utils.modules_initialize]-INFO-初始化组件: vad成功 SileroVAD
251223 21:15:41 [core.providers.asr.fun_local]-INFO-funasr version: 1.2.7.
251223 21:15:41 [core.utils.modules_initialize]-INFO-ASR模块初始化完成
251223 21:15:41 [core.utils.modules_initialize]-INFO-初始化组件: asr成功 FunASR
251223 21:15:42 [__main__]-INFO-OTA接口是         http://192.168.0.115:8003/xiaozhi/ota/   172.19.0.2
251223 21:15:42 [__main__]-INFO-视觉分析接口是    http://192.168.0.115:8003/mcp/vision/explain
251223 21:15:42 [__main__]-INFO-Websocket地址是   ws://192.168.0.115:8000/xiaozhi/v1/
251223 21:15:42 [__main__]-INFO-=======上面的地址是websocket协议地址，请勿用浏览器访问=======
251223 21:15:42 [__main__]-INFO-如想测试websocket请用谷歌浏览器打开test目录下的test_page.html
251223 21:15:42 [__main__]-INFO-=============================================================

curl http://192.168.0.115:8003/xiaozhi/ota/
OTA接口运行正常，向设备发送的websocket地址是：ws://192.168.0.115:8003/xiaozhi/v1/(base) tester@Z8G4:~/AI_Tools/xiaozhi_server$ curl http://192.168.0.115:8003/mcp/vision/explain
MCP Vision 接口运行正常，视觉解释接口地址是：http://172.19.0.2:8003/mcp/vision/explain(base) tester@Z8G4:~/AI_Tools/xiaozhi_server$ curl ws://192.168.0.115:8000/xiaozhi/v1/

CONFIG_OTA_URL="https://api.tenclass.net/xiaozhi/ota/"

```

**关键初始化组件：**
- ✅ GC管理器
- ✅ LLM (DoubaoLLM) - 需配置API key
- ✅ Intent识别 (function_call)
- ✅ Memory (nomem)
- ✅ VAD语音活动检测 (SileroVAD)
- ✅ ASR语音识别 (FunASR v1.2.7)

**注意事项：**
- GPU discovery失败是正常的（系统无GPU或未配置）
- 需要配置正确的LLM API key才能使用对话功能

---

## MRTool MCP工具发现调试记录 (2025-12-28)

### 问题描述

在ESP32设备端实现了 MRTool（MR专用工具），并在设备端代码中通过 `McpServer::AddMROnlyTools()` 进行了注册。但服务端始终无法发现该工具，函数列表中看不到 `mr.start_examination`。

**设备端日志显示：**
```
当前支持的函数列表: ['get_news_from_newsnow', 'play_music', 'get_lunar', 'get_weather', 
                      'change_role', 'handle_exit_intent', 'self_get_device_status', 
                      'self_audio_speaker_set_volume', 'self_screen_set_brightness', 
                      'self_screen_set_theme', 'self_camera_take_photo', 
                      'self_system_reconfigure_wifi']
```

注意：**看不到 `mr.start_examination`**

### 根本原因分析

#### 1. 工具分类体系

设备端 (`mcp_server.cc`) 中的工具被分为三类：

| 工具类型 | 注册函数 | 过滤参数 | 备注 |
|---------|--------|--------|------|
| **普通工具** | `AddCommonTools()` | 无过滤 | 始终返回（如 `self.get_device_status`） |
| **User-only工具** | `AddUserOnlyTools()` | `withUserTools` | 需要服务端请求此参数 |
| **MR-only工具** | `AddMROnlyTools()` | `withMRTools` | 需要服务端请求此参数 |

#### 2. 设备端工具过滤逻辑

在 [mcp_server.cc](../esp/xiaozhi-esp32_r2/main/mcp_server.cc) 的 `GetToolsList()` 函数中：

```cpp
void McpServer::GetToolsList(int id, const std::string& cursor, 
                             bool list_user_only_tools, bool list_mr_only_tools) {
    // ... 遍历所有工具 ...
    
    // 过滤逻辑：
    if (!list_user_only_tools && (*it)->user_only()) {
        ++it;
        continue;  // 跳过user-only工具（除非请求了withUserTools）
    }
    if (!list_mr_only_tools && (*it)->mr_only()) {
        ++it;
        continue;  // 跳过mr-only工具（除非请求了withMRTools）
    }
}
```

**关键：** 如果 `tools/list` 请求中没有 `withMRTools: true` 参数，MR-only 工具会被自动过滤掉。

#### 3. 服务端请求缺陷

服务端在发送 `tools/list` 请求时，没有包含 `withMRTools` 和 `withUserTools` 参数：

**旧代码** (device_mcp/mcp_handler.py)：
```python
async def send_mcp_tools_list_request(conn):
    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        # 缺少 params 字段！
    }
```

**同样的问题** 也存在于 mcp_endpoint_handler.py 中。

### 解决方案

#### Step 1: 更新服务端请求参数

修改 [device_mcp/mcp_handler.py](../main/xiaozhi-server/core/providers/tools/device_mcp/mcp_handler.py)：

```python
async def send_mcp_tools_list_request(conn):
    """发送MCP工具列表请求"""
    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {
            "withMRTools": True,      # 请求包含MR-only工具
            "withUserTools": True     # 请求包含user-only工具
        }
    }
```

同时更新 `send_mcp_tools_list_continue_request()` 函数，在 cursor 分页请求中也要包含这两个参数。

修改 [mcp_endpoint/mcp_endpoint_handler.py](../main/xiaozhi-server/core/providers/tools/mcp_endpoint/mcp_endpoint_handler.py)，方式完全相同。

#### Step 2: 修改Docker Compose配置

在 [docker-compose.yml](docker-compose.yml) 中添加 volume 挂载，使修改后的 Python 文件立即生效：

```yaml
volumes:
  # ... 其他挂载 ...
  # 挂载修改后的设备MCP处理器文件，使withMRTools参数生效
  - ./main/xiaozhi-server/core/providers/tools/device_mcp/mcp_handler.py:/opt/xiaozhi-esp32-server/core/providers/tools/device_mcp/mcp_handler.py
  # 挂载修改后的MCP接入点处理器文件
  - ./main/xiaozhi-server/core/providers/tools/mcp_endpoint/mcp_endpoint_handler.py:/opt/xiaozhi-esp32-server/core/providers/tools/mcp_endpoint/mcp_endpoint_handler.py
```

#### Step 3: 重启服务

```bash
cd /home/tester/AI_Tools/xiaozhi-esp32-server
docker compose down
docker compose up -d
```

验证修改已应用：

```bash
docker compose exec xiaozhi-esp32-server grep -A 10 "def send_mcp_tools_list_request" \
  /opt/xiaozhi-esp32-server/core/providers/tools/device_mcp/mcp_handler.py
```

应该看到 `"withMRTools": True` 参数。

### 修改文件清单

| 文件 | 修改内容 | 目的 |
|------|--------|------|
| [device_mcp/mcp_handler.py](../main/xiaozhi-server/core/providers/tools/device_mcp/mcp_handler.py) | `send_mcp_tools_list_request()` 添加 params | 请求MR工具 |
| [device_mcp/mcp_handler.py](../main/xiaozhi-server/core/providers/tools/device_mcp/mcp_handler.py) | `send_mcp_tools_list_continue_request()` 添加 params | 分页请求中也包含参数 |
| [mcp_endpoint/mcp_endpoint_handler.py](../main/xiaozhi-server/core/providers/tools/mcp_endpoint/mcp_endpoint_handler.py) | `send_mcp_endpoint_tools_list()` 添加 params | 请求MR工具 |
| [mcp_endpoint/mcp_endpoint_handler.py](../main/xiaozhi-server/core/providers/tools/mcp_endpoint/mcp_endpoint_handler.py) | `send_mcp_endpoint_tools_list_continue()` 添加 params | 分页请求中也包含参数 |
| [docker-compose.yml](docker-compose.yml) | 添加 volume 挂载 | 应用代码修改到容器 |
| [data/.config.yaml](data/.config.yaml) | 添加 mcp_endpoint 配置和注释 | 文档化MCP配置 |

### 关键学习点

1. **工具过滤是对称的**
   - user-only 和 mr-only 工具的过滤机制完全相同
   - 都需要服务端在 `tools/list` 请求中显式声明参数

2. **为什么普通工具之前工作**
   - `self.get_device_status`、`self.audio_speaker.set_volume` 等都是**普通工具**，无任何标记
   - 普通工具不受过滤影响，始终被返回
   - 这就是为什么之前没有察觉到这个问题

3. **Docker volume 挂载的重要性**
   - 修改源代码文件后，需要 volume 挂载才能让容器内的代码生效
   - 否则需要重新构建镜像

### 验证步骤

设备连接后，查看服务日志：

```bash
docker compose logs xiaozhi-esp32-server | grep "当前支持的函数列表"
```

应该包含 `mr.start_examination` 或其他 mr-only 工具。

### 参考链接

- [MCP规范 - tools/list](https://modelcontextprotocol.io/specification/2024-11-05)
- [ESP32 MCP服务器实现](../esp/xiaozhi-esp32_r2/main/mcp_server.cc)
- [设备端MR工具定义](../esp/xiaozhi-esp32_r2/main/MR_Tool.h)

## 配置切换为外部FunASR Server (2026-01-03)

### 背景

之前的部署使用**本地FunASR模型**（SenseVoiceSmall），这会占用大量服务器资源。通过配置切换到**外部FunASR Server**，可以将ASR处理卸载到独立容器，减轻主服务器的资源压力。

### 问题与解决

#### 问题：Docker权限错误

在停止容器时遇到 AppArmor 阻止的权限错误：
```
Error response from daemon: cannot kill container: ... permission denied
```

**原因：** 系统中同时运行了两个Docker daemon：
1. Snap版Docker（通过 `/run/snap.docker` 连接）
2. 常规Docker（通过 `/var/run/docker.sock` 连接）

AppArmor安全策略只允许一个daemon运行。

**解决方案：**
```bash
# 方案1：临时修复AppArmor冲突
sudo snap stop docker
sudo snap start docker

# 方案2：永久修复（移除Snap Docker）
sudo snap remove docker
# 验证只有常规Docker运行
docker version
```

### 配置修改步骤

#### Step 1: 更新 `.config.yaml`

修改 `data/.config.yaml`，将ASR模块从本地切换为服务器模式：

```yaml
selected_module:
  # 语音识别模块：使用外部 FunASRServer（禁用本地模型）
  ASR: FunASRServer
  LLM: AliCloudLLM

ASR:
  # FunASR (本地模型，已禁用):
  #   type: fun_local
  #   model_dir: models/SenseVoiceSmall
  #   output_dir: tmp/
  
  FunASRServer:
    type: fun_server
    host: 127.0.0.1
    port: 10096
    is_ssl: true
    api_key: none
    output_dir: tmp/
```

**关键变更：**
- `selected_module.ASR: FunASRServer` - 选择服务器模式
- 本地 `FunASR` 配置被注释掉
- FunASRServer 使用内部通信地址 `127.0.0.1:10096`（Docker网络内通信）

#### Step 2: 启动FunASR Server容器（可选，如未运行）

如果FunASR Server不在运行，需要独立启动：

```bash
# 创建模型目录
mkdir -p ./funasr-runtime-resources/models

# 启动FunASR容器（使用CPU推理）
sudo docker run -p 10096:10095 -it --privileged=true \
  -v $PWD/funasr-runtime-resources/models:/workspace/models \
  registry.cn-hangzhou.aliyuncs.com/funasr_repo/funasr:funasr-runtime-sdk-online-cpu-0.1.12

# 在容器内执行以下命令
cd FunASR/runtime

# 启动FunASR服务器（后台运行）
nohup bash run_server_2pass.sh \
  --download-model-dir /workspace/models \
  --vad-dir damo/speech_fsmn_vad_zh-cn-16k-common-onnx \
  --model-dir damo/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-onnx \
  --online-model-dir damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-online-onnx \
  --punc-dir damo/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727-onnx \
  --lm-dir damo/speech_ngram_lm_zh-cn-ai-wesp-fst \
  --itn-dir thuduj12/fst_itn_zh \
  --hotword /workspace/models/hotwords.txt > log.txt 2>&1 &

# 查看启动日志
tail -f log.txt
```

**GPU加速** （可选）：
如果服务器有GPU，参考 [FunASR官方文档](https://github.com/modelscope/FunASR/blob/main/runtime/docs/SDK_advanced_guide_online_zh.md)。

#### Step 3: 重启xiaozhi-esp32-server容器

```bash
cd /home/tester/AI_Tools/xiaozhi-esp32-server

# 重启服务
docker restart xiaozhi-esp32-server

# 查看初始化日志
sleep 3 && docker logs xiaozhi-esp32-server --tail 30 | grep -E "(ASR|asr|初始化组件)"
```

**验证成功的日志输出：**
```
260103 11:21:43[...][core.utils.modules_initialize]-INFO-ASR模块初始化完成
260103 11:21:43[...][core.utils.modules_initialize]-INFO-初始化组件: asr成功 FunASRServer
```

### 架构说明

**本地模式 vs 服务器模式对比：**

| 指标 | 本地 (FunASR) | 服务器 (FunASRServer) |
|-----|--------------|-------|
| **资源占用** | 高（加载模型到内存） | 低（仅WebSocket客户端） |
| **内存需求** | >2GB | <100MB |
| **启动时间** | ~30-40秒 | ~2秒 |
| **ASR延迟** | 低（本地处理） | 中（网络往返） |
| **并发能力** | 单instance | 共享server instance |
| **适用场景** | 单机/低功耗 | 服务集群/资源受限 |

**通信流程：**
```
Device/Client 
  ↓ (WebSocket: opus audio)
xiaozhi-esp32-server (fun_server provider)
  ↓ (WebSocket: PCM data)
FunASR Server (port 10095)
  ↓ (Speech recognition)
Result (JSON with recognized text)
```

### 配置检验

验证配置是否正确应用：

```bash
# 查看容器内的配置
docker exec xiaozhi-esp32-server cat data/.config.yaml | grep -A 5 "selected_module:"

# 应该输出：
# selected_module:
#   ASR: FunASRServer
#   LLM: AliCloudLLM
```

### 常见问题

**Q: 切换后仍然看到FunASR的日志？**
A: 这是正常的，旧日志来自容器重启前的状态。重启容器后，最新的日志会显示 `FunASRServer`。

**Q: FunASR Server连接失败怎么办？**
A: 检查以下几点：
1. FunASR容器是否运行：`docker ps | grep funasr`
2. 端口映射是否正确：`docker port <container_name>`
3. 服务器地址配置：`data/.config.yaml` 中的 host 和 port
4. SSL证书验证：如果使用自签名证书，确保 `is_ssl: true` 和 `ssl_context` 配置

**Q: 如何切换回本地模式？**
A: 编辑 `data/.config.yaml`，将 `selected_module.ASR` 改为 `FunASR`，然后重启容器。

### 修改文件清单

| 文件 | 修改内容 | 目的 |
|------|--------|------|
| [data/.config.yaml](data/.config.yaml) | `selected_module.ASR: FunASRServer` | 选择服务器模式 |
| [data/.config.yaml](data/.config.yaml) | 注释本地FunASR配置 | 禁用本地模型加载 |
| [core/utils/modules_initialize.py](main/xiaozhi-server/core/utils/modules_initialize.py) | 增强ASR初始化日志 | 清晰显示使用的ASR类型 |