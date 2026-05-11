# 阶段二：语义子目标生成（Semantic Subgoal Generation）

## 概述

语义子目标生成阶段由 LLM 驱动，负责将复杂的游戏任务（quest）**自动分解为有序的自然语言子目标序列**。这一阶段将底层代码变化翻译为人类可理解的测试步骤，为后续奖励生成和锚点映射奠定语义基础。

---

## 核心目标

> 给定与某个新游戏任务相关的代码更新，LLM 子目标生成器（Subgoal Generator）分析这些原始代码变化，将其分解为逻辑有序的子目标序列。

---

## 输入

- **Stage 1 输出**：AST 差异报告（$C_L$, $C_B$）
- 对应单个新游戏任务的代码变更集合

---

## LLM 分析过程

LLM 通过分析以下三类信息推断必要的中间步骤：

| 分析对象 | 内容 |
|----------|------|
| **函数调用关系** | 哪些函数被新增、被调用、被依赖 |
| **数据依赖关系** | 某函数需要 `chopped_tomato` 作为输入，则切番茄必须先完成 |
| **任务逻辑** | 从 AST Diff 中提取的整体任务流程结构 |

---

## 输出格式

最终输出为一个**语义有序的子目标序列**：

$$S = (sg_1, sg_2, \dots, sg_n)$$

其中每个 $sg_j \in S$ 是一个**自然语言字符串**，描述整体任务中的一个独立、可验证的步骤。

### 子目标的三个要求

1. **自然语言描述**：LLM 可直接生成，人类可理解
2. **可验证性**：可通过游戏状态变量在代码层面确认是否完成
3. **相对原子性**：不需要进一步拆分为独立子步骤

---

## 动机示例（Onion Pizza Quest）

**任务背景：** 玩家需按照顺序完成多步烹饪操作，最终制作并配送洋葱披萨。

**LLM 生成的子目标序列：**

| 编号 | 子目标 $sg_j$ | 描述 |
|------|--------------|------|
| $sg_1$ | "Obtain and chop a tomato" | 取得番茄并在砧板上切碎 |
| $sg_2$ | "Process the chopped tomato into sauce using a mixer" | 用搅拌机将碎番茄处理成酱 |
| $sg_3$ | "Assemble the pizza on a base with sauce and cheese" | 在面团底座上放置酱和奶酪，组装生披萨 |
| $sg_4$ | "Bake the assembled pizza in the oven" | 将生披萨放入烤箱烘烤至熟 |

（后续还可能包含添加洋葱、配送等子目标）

---

## Prompt 设计要点

论文附录中披露了 LLM Prompt 的核心结构：

```json
{
  "system_role": "You are a subgoal generator and structural anchor annotator.",
  "task_description": {
    "steps": [
      "Identify newly added or significantly expanded game tasks.",
      "Decompose each complex task into an ordered sequence of subgoals S = (sg1, ..., sgN)",
      "Annotate each subgoal with structural anchors"
    ]
  },
  "input_data": {
    "source": "AST difference report (ast_diff.txt)",
    "line_type_description": {
      "added_lines": "Lines beginning with '+'. Prefer these as anchors.",
      "removed_lines": "Lines beginning with '-'. Use only when describing removed behavior."
    }
  }
}
```

---

## 与其他阶段的关系

```
Stage 1（AST Diff）
       ↓
Stage 2（子目标生成）→ 输出 S = (sg1, ..., sgn)
       ↓                          ↓
Stage 3（奖励生成）       Stage 4（锚点映射）
```

- **Stage 3** 将 $S$ 中每个 $sg_j$ 转换为可执行的奖励函数
- **Stage 4** 将 $S$ 中每个 $sg_j$ 与具体结构锚点关联

---

## 关键价值

1. **语义桥梁**：将机器可读的代码差异翻译为人类可理解的测试目标
2. **有序性保证**：子目标序列反映了真实的依赖关系（如必须先切番茄才能组装披萨）
3. **LLM 的强项**：利用 LLM 对代码语义和游戏逻辑的理解能力，自动完成人工难以替代的意图理解任务

---

## 潜在风险

> **LLM 幻觉问题**（见论文 4.4 节局限性）
>
> 若 LLM 误解代码变更的意图——例如将一次简单的重构误判为新功能，或未能捕捉平衡性调整的细微差别——生成的子目标序列可能与实际功能意图不符，导致后续奖励函数偏差，最终引导 RL 智能体走向错误行为。

**缓解方向**：论文提出在未来工作中引入**闭环精炼机制**，将智能体的失败轨迹和低覆盖率报告反馈给 LLM，动态调试和优化生成的子目标与锚点映射。
