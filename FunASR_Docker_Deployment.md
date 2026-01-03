# FunASR SDK 阿里云下载与Docker部署完整指南

## 概述

本指南介绍如何从**阿里云ModelScope**下载**FunASR Runtime SDK**，并将其部署到Docker容器中，建立一个独立的语音识别服务器。

## 适用场景

- ✅ 服务端需要独立的ASR服务，减轻主应用压力
- ✅ 多个应用共享一个ASR服务器
- ✅ 需要GPU加速或定制化部署
- ✅ 生产环境中需要高可用性

## 前置条件

- Docker已安装（版本19.03+）
- 网络连接正常，可访问阿里云镜像仓库
- 硬盘空间 ≥ 10GB（用于模型存储）
- 内存 ≥ 4GB（推荐）

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│          xiaozhi-esp32-server (主应用)                   │
│  Port 8000: WebSocket                                    │
│  Port 8003: HTTP                                         │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │ ASR Module (fun_server provider)                   │ │
│  │  - 接收opus/pcm音频数据                            │ │
│  │  - 通过WebSocket转发到FunASR Server                │ │
│  │  - 返回识别结果给设备                              │ │
│  └───────────────┬──────────────────────────────────┘ │
└─────────────────┼─────────────────────────────────────┘
                  │ WebSocket
                  │ Port 10095 (内部)
                  │ Port 10096 (外部)
                  ▼
┌─────────────────────────────────────────────────────────┐
│            FunASR Server Docker容器                      │
│  - 模型: SenseVoiceSmall, Paraformer等                  │
│  - 协议: WebSocket (TCP/10095)                          │
│  - 资源: CPU/GPU推理                                    │
│  - 数据: 持久化到 funasr-runtime-resources/models       │
└─────────────────────────────────────────────────────────┘
```

## 方案对比

| 特性 | 本地FunASR | FunASR Server |
|------|----------|---------------|
| **内存占用** | 2-4GB | 100-500MB |
| **启动时间** | 30-40秒 | 2-3秒 |
| **并发性** | 单instance | 多instance共享 |
| **GPU支持** | ✅ | ✅ |
| **扩展性** | 低 | 高 |
| **维护成本** | 低 | 中 |
| **推荐场景** | 单机/演示 | 生产/集群 |

---

## 快速启动 (5步)

### Step 1: 准备本地目录

```bash
# 创建模型存储目录
mkdir -p ./funasr-runtime-resources/models
cd ./funasr-runtime-resources/models

# 验证目录创建成功
ls -la ..
```

### Step 2: 启动FunASR Docker容器

**CPU版本（推荐）：**

```bash
sudo docker run \
  -p 10096:10095 \
  -it \
  --privileged=true \
  -v $PWD/funasr-runtime-resources/models:/workspace/models \
  registry.cn-hangzhou.aliyuncs.com/funasr_repo/funasr:funasr-runtime-sdk-online-cpu-0.1.12
```

**GPU版本（CUDA 11.8）：**

```bash
sudo docker run \
  -p 10096:10095 \
  -it \
  --gpus all \
  --privileged=true \
  -v $PWD/funasr-runtime-resources/models:/workspace/models \
  registry.cn-hangzhou.aliyuncs.com/funasr_repo/funasr:funasr-runtime-sdk-online-gpu-0.1.12
```

**说明：**
- `-p 10096:10095` : 将容器内10095端口映射到主机10096端口
- `-v $PWD/...:/$workspace/models` : 挂载本地模型目录到容器
- `--privileged=true` : 获取特权模式（某些模型需要）
- `--gpus all` : 启用GPU（GPU版本）

### Step 3: 在容器内下载模型和启动服务

容器启动后会进入bash shell，执行以下命令：

```bash
# 进入FunASR运行时目录
cd FunASR/runtime

# 后台启动FunASR服务器（2-pass模式）
nohup bash run_server_2pass.sh \
  --download-model-dir /workspace/models \
  --vad-dir damo/speech_fsmn_vad_zh-cn-16k-common-onnx \
  --model-dir damo/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-onnx \
  --online-model-dir damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-online-onnx \
  --punc-dir damo/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727-onnx \
  --lm-dir damo/speech_ngram_lm_zh-cn-ai-wesp-fst \
  --itn-dir thuduj12/fst_itn_zh \
  --hotword /workspace/models/hotwords.txt \
  > log.txt 2>&1 &
```

**参数说明：**
- `--download-model-dir` : 模型下载目录
- `--vad-dir` : 语音活动检测模型
- `--model-dir` : 离线ASR模型
- `--online-model-dir` : 在线ASR模型
- `--punc-dir` : 标点符号恢复模型
- `--lm-dir` : 语言模型
- `--itn-dir` : 反向文本规范化
- `--hotword` : 热词文件（可选）

### Step 4: 监控模型下载进度

```bash
# 实时查看下载日志
tail -f log.txt

# 典型输出示例：
# [2026-01-03 11:30:45] Downloading damo/speech_fsmn_vad_zh-cn-16k-common-onnx...
# [2026-01-03 11:31:20] Model downloaded successfully
# [2026-01-03 11:31:25] Server starting on port 10095
# [2026-01-03 11:32:15] All models ready, listening for connections...
```

**首次启动预期耗时：**
- 模型下载: 2-5分钟（取决于网速）
- 模型加载: 1-2分钟
- 服务就绪: 3-7分钟总计

### Step 5: 验证服务可用性

在主机上创建测试脚本 `test_funasr.py`：

```python
#!/usr/bin/env python3
import websockets
import json
import asyncio

async def test_funasr():
    uri = "ws://127.0.0.1:10096"  # 访问FunASR服务
    
    async with websockets.connect(uri, subprotocols=["binary"]) as ws:
        # 发送配置消息
        config = {
            "mode": "offline",
            "chunk_size": [5, 10, 5],
            "chunk_interval": 10,
            "wav_name": "test_audio",
            "is_speaking": True,
            "itn": False
        }
        await ws.send(json.dumps(config))
        
        # 发送PCM数据（示例：1秒的16kHz PCM）
        # 实际使用时替换为真实音频数据
        import struct
        duration = 1  # 秒
        sample_rate = 16000
        frequency = 440  # Hz
        amplitude = 32767
        
        pcm_data = b''
        for i in range(duration * sample_rate):
            import math
            sample = int(amplitude * math.sin(2 * math.pi * frequency * i / sample_rate))
            pcm_data += struct.pack('<h', sample)
        
        await ws.send(pcm_data)
        
        # 发送结束信号
        await ws.send(json.dumps({"is_speaking": False}))
        
        # 接收结果
        result = await ws.recv()
        result_data = json.loads(result)
        print(f"识别结果: {result_data}")

if __name__ == "__main__":
    asyncio.run(test_funasr())
```

运行测试：

```bash
pip install websockets
python test_funasr.py
```

---

## 详细部署说明

### Docker镜像详情

**镜像来源：** 阿里云ModelScope容器仓库

| 版本 | 镜像地址 | 推理方式 | 适用场景 |
|------|--------|--------|--------|
| CPU-0.1.12 | `registry.cn-hangzhou.aliyuncs.com/funasr_repo/funasr:funasr-runtime-sdk-online-cpu-0.1.12` | CPU | 一般服务器 |
| GPU-0.1.12 | `registry.cn-hangzhou.aliyuncs.com/funasr_repo/funasr:funasr-runtime-sdk-online-gpu-0.1.12` | GPU (CUDA 11.8) | 高性能服务器 |
| GPU-12-0.1.12 | `registry.cn-hangzhou.aliyuncs.com/funasr_repo/funasr:funasr-runtime-sdk-online-gpu-12-0.1.12` | GPU (CUDA 12.x) | 最新GPU |

**镜像内容：**
- FunASR Runtime SDK (完整源码)
- 预装Python 3.8+、ONNX Runtime
- ModelScope SDK（用于自动下载模型）
- 示例脚本和文档

### 阿里云镜像仓库访问

**仓库信息：**
- 镜像仓库地址: `registry.cn-hangzhou.aliyuncs.com`
- 仓库命名空间: `funasr_repo`
- 公开访问: ✅ 无需登录

**镜像查询：**

```bash
# 列出所有可用版本
curl -s 'https://registry.cn-hangzhou.aliyuncs.com/v2/funasr_repo/funasr/tags/list' | grep -o 'funasr-runtime-sdk[^"]*'

# 输出示例：
# funasr-runtime-sdk-online-cpu-0.1.12
# funasr-runtime-sdk-online-gpu-0.1.12
# funasr-runtime-sdk-online-gpu-12-0.1.12
```

**镜像拉取：**

```bash
# CPU版本
docker pull registry.cn-hangzhou.aliyuncs.com/funasr_repo/funasr:funasr-runtime-sdk-online-cpu-0.1.12

# GPU版本
docker pull registry.cn-hangzhou.aliyuncs.com/funasr_repo/funasr:funasr-runtime-sdk-online-gpu-0.1.12

# 查看本地镜像
docker images | grep funasr
```

### 模型下载详解

FunASR服务器启动时会自动从阿里云ModelScope下载所需模型。

**预装模型列表：**

| 模型名称 | 功能 | 大小 | 用途 |
|---------|------|------|------|
| `damo/speech_fsmn_vad_zh-cn-16k-common-onnx` | VAD (语音活动检测) | ~200MB | 检测是否有语音 |
| `damo/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-onnx` | 离线ASR + 标点 | ~400MB | 离线识别+标点符号 |
| `damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-online-onnx` | 在线ASR | ~400MB | 实时流式识别 |
| `damo/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727-onnx` | 标点符号恢复 | ~100MB | 为文本添加标点 |
| `damo/speech_ngram_lm_zh-cn-ai-wesp-fst` | 语言模型 | ~500MB | 提高识别准确率 |
| `thuduj12/fst_itn_zh` | ITN模型 | ~50MB | 反向文本规范化 |

**总计下载量:** ~1.5-2GB

**下载位置:** `/workspace/models/` (容器内) → `./funasr-runtime-resources/models/` (主机)

**下载过程：**

```bash
# 可选：手动下载特定模型
# 注意：通常自动下载更方便

# 使用ModelScope SDK下载
python -m modelscope download \
  --model damo/speech_fsmn_vad_zh-cn-16k-common-onnx \
  --local_dir ./funasr-runtime-resources/models/

# 查看下载的模型
ls -lh ./funasr-runtime-resources/models/damo/
```

### Docker Compose 配置（推荐）

创建 `docker-compose-funasr.yml`：

```yaml
version: '3.8'

services:
  funasr-server:
    image: registry.cn-hangzhou.aliyuncs.com/funasr_repo/funasr:funasr-runtime-sdk-online-cpu-0.1.12
    container_name: funasr-server
    ports:
      - "10096:10095"
    volumes:
      - ./funasr-runtime-resources/models:/workspace/models
    environment:
      - PYTHONUNBUFFERED=1
    privileged: true
    command: >
      bash -c "
        cd FunASR/runtime &&
        bash run_server_2pass.sh \
          --download-model-dir /workspace/models \
          --vad-dir damo/speech_fsmn_vad_zh-cn-16k-common-onnx \
          --model-dir damo/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-onnx \
          --online-model-dir damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-online-onnx \
          --punc-dir damo/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727-onnx \
          --lm-dir damo/speech_ngram_lm_zh-cn-ai-wesp-fst \
          --itn-dir thuduj12/fst_itn_zh \
          --hotword /workspace/models/hotwords.txt
      "
    restart: unless-stopped
    networks:
      - xiaozhi-network

networks:
  xiaozhi-network:
    driver: bridge
```

**使用Docker Compose启动：**

```bash
docker-compose -f docker-compose-funasr.yml up -d
docker-compose -f docker-compose-funasr.yml logs -f funasr-server
```

---

## 与xiaozhi-esp32-server集成

### 配置文件修改

编辑 `data/.config.yaml`：

```yaml
selected_module:
  ASR: FunASRServer    # 选择FunASR Server模式
  LLM: AliCloudLLM
  # ... 其他配置

ASR:
  FunASRServer:
    type: fun_server
    host: 127.0.0.1    # Docker网络内部地址
    port: 10096        # 映射到主机的端口
    is_ssl: true       # 使用SSL加密
    api_key: none
    output_dir: tmp/
```

### Docker Compose 联合部署

更新主应用的 `docker-compose.yml`，添加FunASR服务：

```yaml
version: '3.8'

services:
  xiaozhi-esp32-server:
    # ... 原有配置 ...
    depends_on:
      - funasr-server
    environment:
      - FUNASR_HOST=funasr-server
      - FUNASR_PORT=10095    # 容器内部通信
    networks:
      - xiaozhi-network

  funasr-server:
    image: registry.cn-hangzhou.aliyuncs.com/funasr_repo/funasr:funasr-runtime-sdk-online-cpu-0.1.12
    container_name: funasr-server
    ports:
      - "10096:10095"        # 外部访问端口
    volumes:
      - ./funasr-runtime-resources/models:/workspace/models
    environment:
      - PYTHONUNBUFFERED=1
    privileged: true
    command: >
      bash -c "
        cd FunASR/runtime &&
        bash run_server_2pass.sh \
          --download-model-dir /workspace/models \
          --vad-dir damo/speech_fsmn_vad_zh-cn-16k-common-onnx \
          --model-dir damo/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-onnx \
          --online-model-dir damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-online-onnx \
          --punc-dir damo/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727-onnx \
          --lm-dir damo/speech_ngram_lm_zh-cn-ai-wesp-fst \
          --itn-dir thuduj12/fst_itn_zh \
          --hotword /workspace/models/hotwords.txt
      "
    restart: unless-stopped
    networks:
      - xiaozhi-network

networks:
  xiaozhi-network:
    driver: bridge
```

**启动联合部署：**

```bash
docker-compose up -d
docker-compose logs -f funasr-server    # 监控FunASR启动
docker-compose logs -f xiaozhi-esp32-server  # 监控主应用
```

---

## 故障排查

### 问题1: 镜像拉取失败

**症状：**
```
Error response from daemon: manifest not found
```

**解决方案：**

```bash
# 检查镜像名称拼写
docker pull registry.cn-hangzhou.aliyuncs.com/funasr_repo/funasr:funasr-runtime-sdk-online-cpu-0.1.12

# 如果仍然失败，尝试手动构建镜像
git clone https://github.com/modelscope/FunASR.git
cd FunASR/runtime
docker build -f Dockerfile.runtime.cpu -t funasr:latest .
```

### 问题2: 模型下载卡住或失败

**症状：**
```
[2026-01-03 11:30:45] Downloading damo/speech_fsmn_vad_zh-cn-16k-common-onnx...
[2026-01-03 11:35:45] (hang, no progress)
```

**解决方案：**

```bash
# 进入容器手动下载
docker exec -it funasr-server bash
cd /workspace/models

# 使用Python直接下载
python -m modelscope download \
  --model damo/speech_fsmn_vad_zh-cn-16k-common-onnx \
  --local_dir ./ \
  --cache_dir ./

# 或使用git-lfs下载
git lfs clone https://modelscope.cn/damo/speech_fsmn_vad_zh-cn-16k-common-onnx.git
```

### 问题3: WebSocket连接超时

**症状：**
```
[ERROR] WebSocket connection timeout to 127.0.0.1:10096
```

**解决方案：**

```bash
# 检查容器是否运行
docker ps | grep funasr

# 检查端口映射
docker port funasr-server

# 检查防火墙
sudo ufw allow 10096

# 测试连接
nc -zv 127.0.0.1 10096
```

### 问题4: 内存不足

**症状：**
```
out of memory: Kill process... fatal signal 9
```

**解决方案：**

```bash
# 增加Docker内存限制
docker run ... -m 4G ...  # 分配4GB内存

# 或使用GPU版本（模型加载更快）
docker run ... -it \
  --gpus all \
  registry.cn-hangzhou.aliyuncs.com/funasr_repo/funasr:funasr-runtime-sdk-online-gpu-0.1.12
```

### 问题5: 识别准确率低

**症状：**
```
输入: "你好"
输出: "你哈" 或 "你好啊"
```

**解决方案：**

```yaml
# 在run_server_2pass.sh中调整参数：
--model-dir damo/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-onnx

# 尝试其他模型版本：
# - speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-onnx
# - speech_paraformer-large_asr_nat-zh-cn-16k-tsinghua-vocab25704-onnx
```

---

## 性能优化

### CPU优化

```bash
# 指定CPU核心数
docker run ... \
  --cpus 4 \
  --cpuset-cpus 0-3 \
  ...
```

### GPU优化

```bash
# GPU版本Dockerfile配置
FROM registry.cn-hangzhou.aliyuncs.com/funasr_repo/funasr:funasr-runtime-sdk-online-gpu-0.1.12

# 在run_server_2pass.sh中添加GPU参数
bash run_server_2pass.sh \
  --num_threads 8 \
  --use_gpu true \
  --gpu_device 0 \
  ...
```

### 网络优化

```bash
# 使用本地镜像加速（如果有本地镜像仓库）
docker run ... \
  registry.local:5000/funasr:funasr-runtime-sdk-online-cpu-0.1.12
```

---

## 参考资源

### 官方链接

- **FunASR GitHub**: https://github.com/modelscope/FunASR
- **阿里ModelScope**: https://modelscope.cn
- **FunASR文档**: https://github.com/modelscope/FunASR/blob/main/runtime/docs/SDK_advanced_guide_online_zh.md
- **Docker Hub**: https://hub.docker.com/

### 相关模型

- **SenseVoice**: 多语言自监督学习语音识别
- **Paraformer**: 高精度离线ASR模型
- **VAD**: 语音活动检测（端点检测）
- **标点符号恢复**: 自动添加标点
- **ITN**: 反向文本规范化（例如："一百二十三" → "123"）

### 故障排查资源

- FunASR Issues: https://github.com/modelscope/FunASR/issues
- ModelScope社区: https://www.modelscope.cn
- Docker文档: https://docs.docker.com

---

## 总结

本指南涵盖了从阿里云下载FunASR SDK到部署在Docker中的完整流程：

| 步骤 | 操作 | 耗时 |
|-----|------|------|
| 1 | 准备目录 | <1分钟 |
| 2 | 启动容器 | 1-2分钟 |
| 3 | 下载模型 | 2-5分钟 |
| 4 | 加载模型 | 1-2分钟 |
| 5 | 验证服务 | <1分钟 |
| **总计** | | **5-10分钟** |

**下次启动** (模型已缓存)：仅需 30-60秒

## 更新记录

- **2026-01-03**: 初始版本，包含CPU和GPU部署方案
