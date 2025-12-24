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

