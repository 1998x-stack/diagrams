# ds4.c — DeepSeek V4 Flash 本地推理引擎

> 项目：[antirez/ds4](https://github.com/antirez/ds4)  
> 作者：antirez（Redis 创始人）  
> 已克隆至：`~/Documents/ds4/`

---

## 一句话总结

专为 DeepSeek V4 Flash 编写的 **纯 Metal GPU 推理引擎**，不依赖 llama.cpp 运行时，代码仅 C + Objective-C。配合自定义 2-bit/4-bit 量化 GGUF，目标是让高端个人设备（Mac Studio / 128GB+ MacBook）跑满 1M 上下文窗口。

## 核心特性

| 特性 | 说明 |
|------|------|
| 推理后端 | **仅 Metal**（Apple GPU），CPU 路径仅供调试 |
| 模型 | 仅支持本项目提供的 DeepSeek V4 Flash GGUF |
| 量化 | **2-bit (q2)** ~81GB / **4-bit (q4)** ~153GB |
| 上下文窗口 | 最高 **1,000,000 tokens** |
| 磁盘 KV 缓存 | 持久化 KV checkpoint，跨 session 复用前缀 |
| 推理模式 | 支持 thinking / no-thinking / Think Max |
| API | OpenAI `/v1/chat/completions` + Anthropic `/v1/messages` |
| 投机解码 | 可选 MTP (Multi-Token Prediction) 加速 |

## 模型下载

```bash
cd ~/Documents/ds4

# 2-bit 量化 (~81GB)，最低 128GB 内存
./download_model.sh q2

# 4-bit 量化 (~153GB)，需要 256GB+ 内存
./download_model.sh q4

# 可选：MTP 投机解码 (~3.5GB)
./download_model.sh mtp
```

模型来源：[huggingface.co/antirez/deepseek-v4-gguf](https://huggingface.co/antirez/deepseek-v4-gguf)

## 编译

```bash
cd ~/Documents/ds4
make
# 产出：ds4 (CLI) 和 ds4-server (HTTP API)
```

## 使用方式

### 命令行交互

```bash
# 单次问答
./ds4 -p "Explain Redis streams in one paragraph."

# 交互模式（多轮对话，保留 KV 上下文）
./ds4

# 关闭 thinking 模式
./ds4 --nothink -p "Hello"

# 启用 MTP 投机解码
./ds4 --mtp gguf/DeepSeek-V4-Flash-MTP-*.gguf --mtp-draft 2
```

交互模式命令：`/help`, `/think`, `/think-max`, `/nothink`, `/ctx N`, `/read FILE`, `/quit`，Ctrl+C 中断生成。

### HTTP API 服务器

```bash
./ds4-server \
  --ctx 100000 \
  --kv-disk-dir /tmp/ds4-kv \
  --kv-disk-space-mb 8192
```

启动后监听 `http://127.0.0.1:8000`，支持：

- `GET /v1/models`
- `POST /v1/chat/completions` (OpenAI 兼容)
- `POST /v1/messages` (Anthropic 兼容)
- SSE 流式输出

### 集成 Coding Agent

**Claude Code 包装脚本：**
```bash
#!/bin/sh
export ANTHROPIC_BASE_URL="http://127.0.0.1:8000"
export ANTHROPIC_AUTH_TOKEN="dsv4-local"
export ANTHROPIC_MODEL="deepseek-v4-flash"
exec "$HOME/.local/bin/claude" "$@"
```

**Pi / OpenClaw 集成：** 添加 provider 到 `~/.pi/agent/models.json`，支持 `thinkingFormat: "deepseek"`。

## 性能参考（来自 README）

| 机器 | 量化 | 提示 | 预填充 | 生成 |
|------|------|------|--------|------|
| M3 Max 128GB | q2 | 短 | 58.52 t/s | 26.68 t/s |
| M3 Max 128GB | q2 | 11709 tokens | 250.11 t/s | 21.47 t/s |
| M3 Ultra 512GB | q2 | 短 | 84.43 t/s | 36.86 t/s |
| M3 Ultra 512GB | q4 | 短 | 78.95 t/s | 35.50 t/s |

## ⚠️ 硬件要求

| 量化 | 模型文件大小 | 最低内存 | 推荐内存 |
|------|-------------|---------|---------|
| **q2** | ~81 GB | 128 GB | 128 GB |
| **q4** | ~153 GB | 256 GB | 256 GB+ |

**你的机器是 M4 Max 64GB 内存，无法运行 ds4.c 本地推理。** q2 模型文件本身就 81GB，加上运行时 KV 缓存（1M 上下文约 26GB），总计远超 64GB。

## 替代方案

| 方案 | 说明 |
|------|------|
| **Ollama + 小模型** | 跑 DeepSeek-R1:8b 或 qwen2.5-coder:14b 等小模型 |
| **MLX 框架** | Apple 官方 ML 推理，支持更多模型的量化 |
| **云端 API** | DeepSeek API、硅基流动等平台按需调用 |

## 关键技术细节

### KV 缓存设计

- 内存中只保留一个活动 session 的 KV
- 磁盘 KV 缓存以 `<sha1>.kv` 文件存储
- 四个 checkpoint 时机：cold / continued / evict / shutdown
- 冷保存时裁剪尾部 token 并对齐到预填充 chunk 边界

### 2-bit 量化策略

- 仅对路由 MoE 专家进行量化（up/gate: IQ2_XXS，down: Q2_K）
- 共享专家、投影层、路由层保持未量化
- 这种非对称量化保证质量的同时大幅减小体积

### 安全警告

- macOS VM bug：CPU 路径在大型映射时会 **kernel panic**，不要在生产环境使用
- 不要同时运行多个大模型进程（有实例锁保护）
- CPU 路径仅供正确性验证

## 项目哲学

> "This project takes a deliberately narrow bet: one model at a time, official-vector validation, long-context tests, and enough agent integration to know if it really works."

不做通用 GGUF 加载器，不做包装层，专注把一个模型在本地跑到极致。
