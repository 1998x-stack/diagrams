# LLM Game Difficulty Framework

> Implementation of **"LLMs May Not Be Human-Level Players, But They Can Be Testers"**
> (arXiv: 2410.02829) — using Claude to measure Wordle puzzle difficulty.

---

## What This Does

This framework uses a Large Language Model to play Wordle puzzles and measures how well the LLM's difficulty perception correlates with real human players. The key insight from the paper:

> **LLMs don't need to play as well as humans — they just need to find the same puzzles hard.**

```
Easy puzzle (CRANE) → LLM solves in ~4 guesses  → Humans also find it easy ✓
Hard puzzle (JAZZY) → LLM needs ~9 guesses       → Humans also struggle    ✓
```

When this correlation is strong (r > 0.6), the LLM can replace expensive human playtesting.

---

## Quick Start (5 minutes)

### 1. Clone & setup

```bash
cd playtest
bash scripts/setup.sh        # Creates .venv, installs deps, runs unit tests
```

### 2. Set your API key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."   # Get one at console.anthropic.com
```

### 3. Run the demo

```bash
source .venv/bin/activate
bash scripts/quickstart.sh   # 3 words × 2 trials (~2-5 min)
```

You'll see output like:

```
Strategy:         zero_shot
Puzzles analyzed: 3

LLM avg guesses:   8.87
Human avg guesses: 4.44

Pearson r = 0.785  (strong correlation ✅)

Puzzle Difficulty Ranking (Hardest → Easiest):
1. JAZZY   LLM: 12.0   Human: 5.4
2. STARE   LLM:  8.5   Human: 3.7
3. CRANE   LLM:  6.0   Human: 3.8
```

---

## Project Structure

```
playtest/
│
├── wordle/                    ← Phase 1: Game Engine
│   ├── engine.py              #   WordleEngine, GameState, GuessResult
│   └── word_list.py           #   WordList management
│
├── agent/                     ← Phase 2: LLM Agent
│   ├── prompts.py             #   Prompt builder (ZS / CoT / CoT+)
│   │                          #   serialize_state(), parse_action()
│   └── llm_client.py          #   LLMClient, WordleAgent
│
├── analysis/                  ← Phase 3: Difficulty Analysis
│   ├── runner.py              #   ExperimentRunner, PuzzleResult
│   ├── stats.py               #   pearson_correlation(), DifficultyAnalyzer
│   └── report.py              #   Markdown report generator
│
├── tests/
│   ├── test_engine.py         #   31 unit tests (Phase 1)
│   ├── test_agent.py          #   36 unit tests (Phase 2)
│   └── test_analysis.py       #   20 unit + 1 integration test (Phase 3)
│
├── scripts/
│   ├── setup.sh               #   One-time environment setup
│   ├── quickstart.sh          #   Interactive demo
│   └── test_all.sh            #   Run all tests with phase report
│
├── main.py                    ← CLI entry point
├── requirements.txt
└── pytest.ini
```

---

## Understanding the Code

### How a Game Works

```
WordleEngine("CRANE")           # Create a game with target word
    ↓
engine.guess("SLATE")           # Submit a guess
    ↓
GuessResult(
    word="SLATE",
    feedback=[GRAY, GRAY, GREEN, GRAY, GREEN],  # A and E correct
    is_correct=False
)
    ↓
engine.get_state()              # Get GameState for LLM
    ↓
GameState(
    guesses_made=["SLATE"],
    correct_positions={2: "A", 4: "E"},
    wrong_positions={},
    incorrect_letters={"S", "L", "T"},
    remaining_guesses=11
)
```

### How the LLM Agent Works

```
GameState  →  serialize_state()  →  Natural language text
                                         ↓
              PromptBuilder.build()  →  Full prompt (Rule + CoT + State)
                                         ↓
                   LLMClient.complete()  →  LLM response text
                                         ↓
                      parse_action()  →  "CRANE"  (5-letter word)
                                         ↓
                  engine.guess("CRANE")  →  Next GuessResult
```

### The Three Prompting Strategies

| Strategy | What it adds | Typical r vs humans |
|----------|-------------|---------------------|
| **Zero-Shot** | Game rules only | ~0.26–0.44 |
| **CoT** | + Step-by-step reasoning | ~0.37–0.51 |
| **CoT+** | + Expert Wordle strategies | ~0.39–0.62 |

From the paper: GPT-4 CoT+ achieves **r = 0.624** on 529 puzzles.

---

## Running Tests

```bash
# Unit tests only (no API key needed, ~0.2s)
python3 -m pytest tests/ -m "not integration" -v

# Phase by phase with a summary
bash scripts/test_all.sh

# Full integration test (~11 min, calls real API)
bash scripts/test_all.sh --integration
```

### Test Gate Rules

The project enforces a strict phase gate — each phase must pass before the next was built:

```
Phase 1: test_engine.py   → 31/31 ✅  (game logic, duplicate letters, state tracking)
Phase 2: test_agent.py    → 36/36 ✅  (serialization, parsing, mock agent)
Phase 3: test_analysis.py → 20/20 ✅  (Pearson correlation, runner, reports)
Integration               →  1/1  ✅  (r = 0.785 on 5 words)
```

---

## Running Experiments

### CLI options

```bash
python3 main.py --help

# Quick demo (5 words, 3 trials, Zero-Shot)
python3 main.py --quick-test

# Custom words
python3 main.py --words CRANE SLATE JAZZY QUEEN TRYST --trials 5

# Change strategy
python3 main.py --quick-test --strategy cot
python3 main.py --quick-test --strategy cot_plus

# Use a different model
python3 main.py --quick-test --model claude-opus-4-6

# Save report to specific file
python3 main.py --quick-test --output my_report.md
```

### From Python (programmatic)

```python
from wordle.engine import WordleEngine
from wordle.word_list import WordList
from agent.llm_client import LLMClient, WordleAgent
from agent.prompts import PromptStrategy
from analysis.runner import ExperimentRunner
from analysis.stats import DifficultyAnalyzer

# 1. Build agent
client = LLMClient(model="claude-haiku-4-5-20251001")
agent  = WordleAgent(strategy=PromptStrategy.COT, llm_client=client)

# 2. Run experiment
runner = ExperimentRunner(agent=agent, max_guesses=12)
results = runner.run_experiment(["CRANE", "JAZZY", "SLATE"], num_trials=5)

# 3. Analyze
human_data = {"CRANE": 3.8, "JAZZY": 5.4, "SLATE": 3.9}
analyzer   = DifficultyAnalyzer()
report     = analyzer.analyze(results, human_data)

print(f"Pearson r = {report.correlation.r:.3f}")
print(f"p-value   = {report.correlation.p_value:.4f}")
```

---

## Key Design Decisions (from the paper)

### G1: Letters as lists, not strings

The paper found LLMs miscount letter positions when words are written as plain strings, because tokenizers split words into subwords (e.g., "APPLE" → `APP` + `LE`).

```python
# ❌ Wrong — causes tokenization confusion
"Your guess: APPLE"

# ✅ Correct — each letter is explicit
"Your guess: [A, P, P, L, E]"
"Correct position: [#, #, #, #, E]"
```

### G2: 12 guesses, not 6

Standard Wordle gives 6 guesses. LLMs perform below human level and would fail most puzzles with 6 guesses, making it impossible to distinguish easy vs hard. We extend to 12 guesses so LLMs can complete most puzzles with varying effort.

### G3: Relative difficulty, not absolute

Don't ask "will 70% of humans solve JAZZY?" — ask "is JAZZY harder than CRANE?" The LLM's relative ordering is reliable even when absolute numbers differ.

---

## Extending the Framework

### Add a new word to test

```python
# In main.py, add to HUMAN_DIFFICULTY dict:
HUMAN_DIFFICULTY["TRYST"] = 5.3   # from WordleBot data
```

### Add a new prompting strategy

```python
# In agent/prompts.py, extend PromptStrategy enum:
class PromptStrategy(Enum):
    ZERO_SHOT = "zero_shot"
    COT       = "cot"
    COT_PLUS  = "cot_plus"
    MY_CUSTOM = "my_custom"   # ← add here

# Then handle it in PromptBuilder.build():
if strategy == PromptStrategy.MY_CUSTOM:
    parts.append("Your custom instruction here...")
```

### Use a different LLM model

```python
client = LLMClient(model="claude-opus-4-6")   # Most capable
client = LLMClient(model="claude-haiku-4-5-20251001")  # Fastest/cheapest
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `command not found: python3` | Install Python 3.9+ from python.org |
| `anthropic not found` | Run `pip install -r requirements.txt` or `bash scripts/setup.sh` |
| `ANTHROPIC_API_KEY not set` | `export ANTHROPIC_API_KEY='sk-ant-...'` |
| `RateLimitError` | The framework retries automatically. If persistent, wait 60s. |
| LLM returns non-word | The agent retries up to 3 times, then uses a fallback word. |
| Integration test timeout | Normal — 5 words × 3 trials × ~90s per game = ~11 min. Use `--trials 1` to speed up. |

---

## Background Reading

- **Paper**: [arXiv:2410.02829](https://arxiv.org/abs/2410.02829) — Chang Xiao, Brenda Z. Yang (2024)
- **Paper analysis**: [`paper_analysis.md`](./paper_analysis.md) — Chinese summary with all key results
- **Design doc**: [`implementation_plan.md`](./implementation_plan.md) — Deep Work methodology & architecture
- **Claude API**: [docs.anthropic.com](https://docs.anthropic.com)
- **WordleBot data**: [engaging-data.com/wordle-guess-distribution](https://engaging-data.com/wordle-guess-distribution/)
