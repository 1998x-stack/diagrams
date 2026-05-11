"""
Prompt templates for LLM Wordle agents.
Implements the Instruction Component from the paper:
  - Game Rule (all agents)
  - Prompting Techniques: Zero-Shot / CoT / CoT+
  - Game Strategy (CoT+ only)

Key implementation aligned with paper Guideline G1:
  Letters are always represented as lists [A, P, P, L, E], not plain strings,
  to avoid LLM tokenization issues that miscount letter positions.
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Set

from wordle.engine import GameState, LetterStatus


class PromptStrategy(Enum):
    ZERO_SHOT = "zero_shot"
    COT = "cot"
    COT_PLUS = "cot_plus"


# ─── Game Rule (shared by all agents) ──────────────────────────────────────────

GAME_RULE = """\
You are playing a word guessing game called Wordle.

RULES:
- The target is a secret 5-letter English word.
- Each turn, you propose exactly one 5-letter English word as your guess.
- After each guess, you receive feedback for each letter:
  * '#' means the letter is in the CORRECT position (green).
  * The letter listed with a position number (e.g., 'A:0') means the letter IS in the word but in the WRONG position (yellow).
  * A letter listed under 'Incorrect letters' means it is NOT in the word at all (gray).
- Use this feedback to narrow down your next guess.
- Respond with ONLY the 5-letter word. No punctuation, no explanation in your final answer line.\
"""

# ─── Prompting Techniques ───────────────────────────────────────────────────────

COT_INSTRUCTIONS = """\
Before submitting your guess, reason step by step:
1. Review all previous guesses and their feedback carefully.
2. List letters confirmed in their correct positions.
3. List letters confirmed to be IN the word (but wrong position) and positions they are NOT at.
4. List letters confirmed NOT in the word.
5. Generate candidate words that satisfy ALL constraints.
6. Choose the best candidate that maximizes information gain.
7. On the final line, write ONLY the 5-letter word (uppercase, no extra text).\
"""

COT_PLUS_STRATEGIES = """\
EXPERT WORDLE STRATEGIES (use these to guide your reasoning):
- Common starting words contain high-frequency letters: E, A, R, I, O, T, N, S, L, C.
- In early guesses, prefer words that test many new letters rather than reusing confirmed ones.
- Never include letters already confirmed as absent (gray letters).
- Honor position constraints: confirmed letters must go in their correct position;
  yellow letters must NOT go back to the positions where they were yellow.
- When multiple candidates exist with similar information value, prefer more common English words.
- Avoid words with repeated letters in early guesses (unless you have strong evidence).\
"""

# ─── Output format instruction ──────────────────────────────────────────────────

OUTPUT_FORMAT = """\
Now, please submit your next guess.
Respond with ONLY the 5-letter uppercase word on the last line. Example: CRANE\
"""


# ─── I/O serialization ─────────────────────────────────────────────────────────

def serialize_state(state: GameState) -> str:
    """
    Convert GameState to natural language text for the LLM.

    Letters are represented as lists per paper Guideline G1.
    Example output:
        Your last guess is [C, R, A, N, E]
        Correct letters in correct position: [#, #, #, #, E]
        Correct letters in wrong position: [A:0]
        Incorrect letters: [C, R, N]
    """
    if not state.guesses_made:
        return "No guesses made yet. This is your first guess."

    lines: List[str] = []

    # Last guess summary
    last_feedback = state.feedbacks[-1]
    last_word_list = ", ".join(last_feedback.word)
    lines.append(f"Your last guess is [{last_word_list}]")

    # Correct positions (GREEN)
    correct_display = []
    for i in range(5):
        if i in state.correct_positions:
            correct_display.append(state.correct_positions[i])
        else:
            correct_display.append("#")
    lines.append(f"Correct letters in correct position: [{', '.join(correct_display)}]")

    # Wrong positions (YELLOW)
    wrong_pos_items = []
    for letter, positions in sorted(state.wrong_positions.items()):
        for pos in positions:
            wrong_pos_items.append(f"{letter}:{pos}")
    if wrong_pos_items:
        lines.append(f"Correct letters in wrong position: [{', '.join(wrong_pos_items)}]")
    else:
        lines.append("Correct letters in wrong position: []")

    # Incorrect letters (GRAY)
    if state.incorrect_letters:
        incorrect_sorted = sorted(state.incorrect_letters)
        lines.append(f"Incorrect letters: [{', '.join(incorrect_sorted)}]")
    else:
        lines.append("Incorrect letters: []")

    # Full history if more than 1 guess made
    if len(state.guesses_made) > 1:
        lines.append("")
        lines.append(f"You have previously guessed: [{', '.join(state.guesses_made)}]")

    lines.append(f"Guesses used: {state.num_guesses} | Remaining: {state.remaining_guesses}")

    return "\n".join(lines)


def parse_action(llm_response: str) -> Optional[str]:
    """
    Extract a 5-letter word from LLM response.
    Handles various formats:
      - "CRANE"
      - "crane"
      - "My next guess is CRANE."
      - "Based on analysis, I'll guess 'CRANE'"
      - "CRANE\n"

    Returns uppercase 5-letter word, or None if extraction fails.
    """
    import re

    response = llm_response.strip()

    # Try last non-empty line first (most reliable with CoT responses)
    lines = [line.strip() for line in response.split("\n") if line.strip()]
    if lines:
        last_line = lines[-1]
        # Clean quotes and punctuation
        cleaned = re.sub(r"[\"'`.,!?]", "", last_line).strip().upper()
        if len(cleaned) == 5 and cleaned.isalpha():
            return cleaned

    # Search for any 5-letter uppercase word in the response
    matches = re.findall(r"\b([A-Za-z]{5})\b", response)
    if matches:
        # Prefer the last match (usually the conclusion)
        return matches[-1].upper()

    return None


# ─── Prompt Builder ─────────────────────────────────────────────────────────────

class PromptBuilder:
    """
    Assembles the full prompt from components based on the chosen strategy.

    Prompt structure:
      [Game Rule]           ← always present
      [CoT Instructions]    ← CoT and CoT+ only
      [Expert Strategies]   ← CoT+ only
      [In-game Info]        ← always present (serialized GameState)
      [Output Format]       ← always present
    """

    def build(self, state: GameState, strategy: PromptStrategy) -> str:
        parts: List[str] = []

        # 1. Game Rule — always
        parts.append(GAME_RULE)

        # 2. CoT reasoning instructions
        if strategy in (PromptStrategy.COT, PromptStrategy.COT_PLUS):
            parts.append(COT_INSTRUCTIONS)

        # 3. Expert strategies (CoT+ only)
        if strategy == PromptStrategy.COT_PLUS:
            parts.append(COT_PLUS_STRATEGIES)

        # 4. In-game state
        parts.append("--- CURRENT GAME STATE ---")
        parts.append(serialize_state(state))

        # 5. Output format
        parts.append(OUTPUT_FORMAT)

        return "\n\n".join(parts)
