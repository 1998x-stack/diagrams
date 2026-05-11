# LLM 游戏难度测量框架：代码设计与实现路线

> 基于深度工作法（Deep Work）设计原则：聚焦核心、拒绝分散、阶段验证

---

## 深度工作法原则应用

| 原则 | 在本项目中的体现 |
|------|----------------|
| **专注单一目标** | 每个阶段只做一件事，不跨阶段 |
| **可测量的完成标准** | 每阶段有明确的测试通过标准才能推进 |
| **渐进式复杂度** | 从最简单的游戏引擎出发，逐层添加 LLM 能力 |
| **快速反馈循环** | 每阶段结束必须运行测试，数据说话 |

---

## 系统架构总览

```
playtest/
├── wordle/
│   ├── engine.py          # Phase 1: 游戏引擎（纯逻辑，无依赖）
│   ├── word_list.py       # 词库管理
│   └── __init__.py
├── agent/
│   ├── prompts.py         # Phase 2: Prompt 模板（ZS/CoT/CoT+）
│   ├── io_component.py    # I/O 组件：状态序列化与动作解析
│   ├── llm_client.py      # LLM API 客户端封装
│   └── __init__.py
├── analysis/
│   ├── runner.py          # Phase 3: 批量实验运行器
│   ├── stats.py           # 统计分析：Pearson 相关系数
│   └── report.py          # 报告生成
├── data/
│   ├── words_5letter.txt  # 5字母单词词库
│   └── human_difficulty.json  # 人类难度基准数据（模拟）
├── tests/
│   ├── test_engine.py     # Phase 1 测试套件
│   ├── test_agent.py      # Phase 2 测试套件
│   └── test_analysis.py   # Phase 3 测试套件
├── config.py              # 全局配置
└── main.py                # 入口点
```

---

## Phase 1：Wordle 游戏引擎

### 目标
实现完整的 Wordle 游戏逻辑，**不依赖任何外部服务**，纯 Python 实现。

### 核心模块

#### `wordle/engine.py` — 游戏核心逻辑

```python
class WordleEngine:
    """
    职责：管理单局 Wordle 游戏的完整生命周期
    """
    # 关键方法
    def __init__(target_word: str, max_guesses: int = 12)
    def guess(word: str) -> GuessResult
    def get_state() -> GameState
    def is_finished() -> bool
    def is_won() -> bool

class GuessResult:
    """单次猜测的反馈"""
    word: str
    feedback: List[LetterStatus]  # GREEN / YELLOW / GRAY
    is_correct: bool

class GameState:
    """完整游戏状态（用于 LLM 输入）"""
    target_word: str  # 仅供引擎使用，不传给 LLM
    guesses_made: List[str]
    feedbacks: List[GuessResult]
    correct_positions: Dict[int, str]   # {位置: 字母}
    wrong_positions: Dict[str, List[int]]  # {字母: 错误位置列表}
    incorrect_letters: Set[str]         # 不存在的字母
    remaining_guesses: int
    status: GameStatus  # ONGOING / WON / LOST
```

#### `wordle/word_list.py` — 词库管理

```python
class WordList:
    def load_from_file(path: str) -> WordList
    def get_random_word() -> str
    def is_valid_word(word: str) -> bool
    def get_all_words() -> List[str]
```

### Phase 1 测试标准（必须全部通过才能进入 Phase 2）

```
✅ test_correct_guess()        - 正确猜出目标词，所有字母绿色
✅ test_wrong_position()       - 字母存在但位置错，标记黄色
✅ test_incorrect_letter()     - 字母不在词中，标记灰色
✅ test_duplicate_letters()    - 重复字母处理正确（如猜 APPLE 目标 CRANE）
✅ test_max_guesses_exceeded() - 超出最大猜测次数，游戏结束
✅ test_invalid_word()         - 非法词汇被拒绝
✅ test_game_state_tracking()  - 游戏状态正确累积
✅ test_win_detection()        - 正确检测胜利条件
```

---

## Phase 2：LLM Agent 接口

### 目标
实现论文中的 Game I/O Component + Instruction Component，支持三种 Prompting 策略。

### 核心模块

#### `agent/io_component.py` — I/O 组件

```python
class GameIOComponent:
    """
    职责：游戏状态 ↔ LLM 文本的双向转换
    """
    def serialize_state(state: GameState) -> str
    """
    将游戏状态转为 LLM 可理解的自然语言

    输出示例：
    Your last guess is [C, R, A, N, E]
    Correct letters in correct position: [#, #, #, #, E]
    Correct letters in wrong position: [A:3]
    Incorrect letters: [C, R, N]
    """

    def parse_action(llm_response: str) -> str
    """
    从 LLM 响应中提取 5 字母单词
    处理各种格式：'CRANE', "crane", 'my guess is CRANE', etc.
    """
```

#### `agent/prompts.py` — Prompt 模板

```python
GAME_RULE_PROMPT = """
You are playing a word guessing game. For each try, you propose
a five letter English word to guess the target. I will provide
feedback on the status of each letter in your guess.
- A letter in the correct position is marked as '#'
- A letter in the word but wrong position is marked as 'letter:position'
- A letter not in the word is listed as incorrect
"""

COT_PROMPT = """
Please think and follow these steps exactly before submitting your next guess:
1. Review all previous guesses and their feedback
2. List letters confirmed in correct positions
3. List letters confirmed in wrong positions
4. List letters not in the word
5. Generate candidate words that satisfy all constraints
6. Select the best candidate and explain your reasoning
"""

COT_PLUS_STRATEGIES = """
Here are some expert strategies for Wordle:
1. Start with words containing common letters (E, A, R, I, O, T, N, S)
2. Use early guesses to gather information about multiple letters
3. Avoid reusing letters already confirmed absent
4. When you have limited guesses, prioritize words that narrow possibilities
"""

class PromptBuilder:
    def build_prompt(
        state: GameState,
        strategy: PromptStrategy  # ZERO_SHOT / COT / COT_PLUS
    ) -> str
```

#### `agent/llm_client.py` — LLM 客户端

```python
class LLMClient:
    """
    封装 Claude API 调用，支持重试与错误处理
    """
    def __init__(model: str = "claude-opus-4-6")
    def complete(prompt: str) -> str
    def complete_with_retry(prompt: str, max_retries: int = 3) -> str

class WordleAgent:
    """
    完整的 LLM Agent：组合 I/O + Prompt + LLM 客户端
    """
    def __init__(
        strategy: PromptStrategy,
        llm_client: LLMClient,
        io_component: GameIOComponent
    )
    def make_guess(state: GameState) -> str
    def play_game(engine: WordleEngine) -> int  # 返回猜测次数
```

### Phase 2 测试标准（必须全部通过才能进入 Phase 3）

```
✅ test_state_serialization()      - 状态正确序列化为文本
✅ test_action_parsing()           - 从各种格式响应提取词汇
✅ test_action_parsing_edge_cases() - 处理换行、大小写、解释文字等
✅ test_prompt_building_zs()       - Zero-Shot prompt 格式正确
✅ test_prompt_building_cot()      - CoT prompt 包含推理步骤
✅ test_prompt_building_cot_plus() - CoT+ prompt 包含策略信息
✅ test_llm_client_mock()          - Mock LLM 响应，验证 Agent 流程
✅ test_full_game_session_mock()   - 完整游戏 Mock 测试（不调用真实 API）
✅ test_invalid_word_retry()       - LLM 返回非法词汇时自动重试
```

---

## Phase 3：难度分析与相关性评估

### 目标
批量运行实验，计算 LLM 难度感知与人类数据的 Pearson 相关系数，生成报告。

### 核心模块

#### `analysis/runner.py` — 实验运行器

```python
class ExperimentRunner:
    """
    批量运行多个 puzzle 的多次试验
    """
    def run_single_puzzle(
        word: str,
        strategy: PromptStrategy,
        num_trials: int = 20
    ) -> PuzzleResult

    def run_experiment(
        word_list: List[str],
        strategy: PromptStrategy,
        num_trials: int = 20,
        max_guesses: int = 12
    ) -> ExperimentResult

    def run_all_strategies(
        word_list: List[str],
        num_trials: int = 20
    ) -> Dict[PromptStrategy, ExperimentResult]

class PuzzleResult:
    word: str
    trials: List[int]        # 每次试验的猜测次数（-1 表示失败）
    avg_guesses: float
    win_rate: float
```

#### `analysis/stats.py` — 统计分析

```python
class DifficultyAnalyzer:
    def pearson_correlation(
        llm_scores: List[float],
        human_scores: List[float]
    ) -> Tuple[float, float]  # (r, p_value)

    def compare_agents(
        results: Dict[str, ExperimentResult],
        human_data: Dict[str, float]
    ) -> ComparisonReport

    def rank_puzzles_by_difficulty(
        result: ExperimentResult
    ) -> List[Tuple[str, float]]  # (word, avg_guesses)
```

#### `analysis/report.py` — 报告生成

```python
class ReportGenerator:
    def generate_markdown_report(
        comparison: ComparisonReport
    ) -> str

    def generate_summary_table(
        comparison: ComparisonReport
    ) -> str
```

### Phase 3 测试标准（全部通过 = 项目完成）

```
✅ test_pearson_calculation()       - 计算结果与 scipy 一致
✅ test_perfect_correlation()       - 完全相关时 r=1.0
✅ test_no_correlation()            - 随机数据时 r≈0
✅ test_experiment_runner_mock()    - Mock 运行器，验证统计聚合
✅ test_report_generation()         - 报告生成无崩溃，包含关键字段
✅ integration_test_5_words()       - 用 5 个词做完整端到端测试（调用真实 API）
```

---

## 阶段门控规则（Gate Rules）

```
Phase 1 Gate: pytest tests/test_engine.py → 8/8 PASSED
                    ↓ 只有全部通过才能进入
Phase 2 Gate: pytest tests/test_agent.py → 9/9 PASSED
                    ↓ 只有全部通过才能进入
Phase 3 Gate: pytest tests/test_analysis.py → 6/6 PASSED
                    ↓
              集成测试：python main.py --quick-test
```

---

## 技术栈

| 组件 | 技术选型 | 理由 |
|------|---------|------|
| 语言 | Python 3.11+ | 生态丰富，LLM SDK 支持 |
| LLM | Claude API (claude-opus-4-6) | 最新最强推理能力 |
| 统计 | scipy.stats | Pearson 相关系数标准实现 |
| 测试 | pytest | 简洁、可读性强 |
| 依赖管理 | pip + requirements.txt | 轻量 |

---

## 关键设计决策

### 决策 1：字母表示为列表而非字符串
```
# 错误（LLM tokenization 问题）
"Your guess: APPLE"

# 正确（论文 G1 指南）
"Your guess: [A, P, P, L, E]"
"Correct position: [#, #, #, #, E]"
```

### 决策 2：猜测上限设为 12（非原始的 6）
- 原因：LLM 水平低于人类，6 次上限导致大量失败，无法区分难度
- 论文实验设定：12 次上限

### 决策 3：每个 puzzle 跑 20 次取平均
- 原因：LLM 响应有随机性，需多次采样消除噪声
- 小规模测试时可降至 3-5 次

### 决策 4：Mock 优先测试策略
- Phase 1 & 2 的测试**不调用真实 LLM API**（使用 Mock）
- 只有 Phase 3 的集成测试才调用真实 API（节约成本）

---

## 预期输出示例

```
=== Wordle 难度分析报告 ===

策略: GPT-4 CoT+
测试词汇数: 10
每词试验次数: 5

难度排序（从难到易）:
1. JAZZY  avg_guesses=9.8  human_difficulty=5.1
2. QUEUE  avg_guesses=8.6  human_difficulty=4.8
3. TRYST  avg_guesses=7.2  human_difficulty=4.3
...

统计结果:
Pearson r = 0.61  (p < 0.001)
结论: LLM 难度感知与人类高度相关 ✅
```
