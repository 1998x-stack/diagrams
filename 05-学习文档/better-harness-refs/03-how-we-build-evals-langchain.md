# How We Build Evals for Deep Agents

> 来源：LangChain Blog
> 链接：https://www.langchain.com/blog/how-we-build-evals-for-deep-agents
> 标签：#eval #agent #deep-agents #langchain

---

## 核心主张

> **"More evals ≠ better agents. 构建能反映生产行为的有针对性 Eval。"**

每个 Eval 都是一个向量，会对 Agent 系统施加压力，塑造行为。盲目堆砌 Eval 会产生"在评测套件上分数好看但生产行为差"的假象。

---

## 一、Eval 数据来源

| 来源 | 说明 |
|------|------|
| **Dogfooding（内部试用）** | 每天使用 Agent，每个错误都变成 Eval Case |
| **外部 Benchmark** | TerminalBench 2.0、BFCL 等，需人工筛选和调整 |
| **手写（Artisanal）** | 针对重要行为手写单元测试和集成测试 |

**关键原则**：SDK 单元/集成测试（系统提示透传、中断配置、子 Agent 路由）与**模型能力 Eval 分开**——前者不体现模型差异，不计入评分。

---

## 二、Eval 分类体系

按**测试内容**分类，而非来源：

| 类别 | 测试内容 |
|------|----------|
| `file_operations` | 文件读写编辑、并行调用、分页 |
| `retrieval` | 跨文件信息检索、多跳文档合成 |
| `tool_use` | 工具选择、多步骤链式调用、跨轮状态追踪 |
| `memory` | 回忆注入的上下文、提取隐式偏好、持久化信息 |
| `conversation` | 模糊请求追问、多轮对话中的正确行动 |
| `summarization` | 上下文溢出处理、触发摘要、压缩后信息恢复 |
| `unit_tests` | SDK 管道测试 |

---

## 三、评估指标体系

**优先顺序**：正确性 → 效率

### 3.1 指标定义

| 指标 | 定义 | 方向 |
|------|------|------|
| **Correctness** | 任务是否正确完成 | 越高越好 |
| **Step ratio** | 实际步骤数 / 理想步骤数 | 越低越好 |
| **Tool call ratio** | 实际工具调用数 / 理想工具调用数 | 越低越好 |
| **Latency ratio** | 实际延迟 / 理想延迟 | 越低越好 |
| **Solve rate** | 期望步骤数 / 实际延迟（任务未完成则为 0） | 越高越好 |

### 3.2 理想轨迹（Ideal Trajectory）

以"已知最优模型的执行路径"作为参考基准，随模型和 Harness 改进而动态更新。

**示例**：
```
请求："告诉我现在我所在地的时间和天气"

理想轨迹（4步）：
  resolve_user → resolve_location → fetch_time + fetch_weather（并行）→ 最终回答
  共 4 步，4 次工具调用，~8 秒

低效轨迹（6步）：
  额外步骤，无并行，~14 秒
  Step ratio: 1.5  |  Tool call ratio: 1.25  |  Latency ratio: 1.75
```

### 3.3 模型选择流程

1. **正确性优先**：哪些模型能可靠完成目标任务？
2. **效率对比**：在"足够好"的模型中，谁的正确性 / 延迟 / 成本权衡最佳？

---

## 四、如何运行 Eval

- **工具**：pytest + GitHub Actions（CI 自动运行）
- **Trace 接入**：所有运行接入 LangSmith，全团队可见
- **按标签运行子集**：节省费用，支持定向实验

```bash
uv run pytest tests/evals \
  --eval-category file_operations \
  --eval-category tool_use \
  --model baseten:nvidia/zai-org/GLM-5
```

---

## 五、核心原则总结

1. **Eval 是行为向量**，每个 Eval 都施加压力，要审慎添加
2. **质量 > 数量**：少量覆盖核心行为的精准 Eval > 大量噪声 Eval
3. **Dogfooding 是最好的 Eval 来源**：每个生产错误 = 一个新 Eval Case
4. **按行为分类，不按来源分类**：分类体系要反映 Agent 能力维度
5. **建立理想轨迹**：提供可量化的效率参考基准
