"""
RAG Knowledge Base for TITAN-Snake
Pure Python TF-IDF retrieval over snake project documentation.
No heavy ML dependencies required.
"""
from __future__ import annotations

import math
import os
import re
from collections import Counter
from typing import Optional


# ---------------------------------------------------------------------------
# Expert rules (hard-coded domain knowledge for snake testing)
# ---------------------------------------------------------------------------

SNAKE_EXPERT_RULES: dict[str, str] = {
    "danger_ahead": "当前方向前方有墙壁或蛇身，立即转向以避免游戏结束",
    "food_close": "食物在3格以内，优先向食物方向移动以获得分数",
    "score_increase": "吃到食物分数应增加10分，蛇身长度+1；若未增加则为逻辑Bug",
    "win_condition": "蛇填满整个网格（gridSize×gridSize格）即为胜利",
    "game_over": "碰撞墙壁或蛇自身即游戏结束（phase=GAME_OVER）",
    "direction_reverse": "不允许180度反向操作（如右行时不能直接向左）",
    "food_placement": "食物必须生成在蛇身之外的空格；若在蛇身内则为食物放置Bug",
    "self_collision": "蛇头碰到蛇身（不含将移走的蛇尾）则游戏结束",
    "score_formula": "每吃一个食物得10分，当前分数=食物数量×10",
    "difficulty_easy": "EASY难度：20×20网格，200ms/tick，初始蛇长3",
    "difficulty_normal": "NORMAL难度：25×25网格，130ms/tick，初始蛇长4",
    "difficulty_hard": "HARD难度：30×30网格，80ms/tick，初始蛇长5",
}

# Default knowledge document paths
_DEFAULT_DOCS = [
    "/Users/xd/Desktop/codes/test/snake/README.md",
    "/Users/xd/Desktop/codes/test/snake/CLAUDE.md",
]


# ---------------------------------------------------------------------------
# Text processing
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> list[str]:
    """Simple tokenizer: lowercase, split on non-alphanumeric (supports Chinese)."""
    # For Chinese text, we keep individual characters as tokens
    # For English, we split by whitespace/punctuation
    text = text.lower()
    # Split on whitespace and common punctuation
    tokens = re.findall(r'[\w\u4e00-\u9fff]+', text)
    return [t for t in tokens if len(t) > 0]


def _chunk_text(text: str, max_chars: int = 300) -> list[str]:
    """Split document text into chunks by paragraph, max max_chars each."""
    # Split by double newline (paragraph break)
    paragraphs = re.split(r'\n\s*\n', text.strip())
    chunks = []
    current = []
    current_len = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # If single paragraph is too long, split by newline
        if len(para) > max_chars:
            lines = para.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if current_len + len(line) > max_chars and current:
                    chunks.append(' '.join(current))
                    current = [line]
                    current_len = len(line)
                else:
                    current.append(line)
                    current_len += len(line)
        else:
            if current_len + len(para) > max_chars and current:
                chunks.append(' '.join(current))
                current = [para]
                current_len = len(para)
            else:
                current.append(para)
                current_len += len(para)

    if current:
        chunks.append(' '.join(current))

    return chunks


# ---------------------------------------------------------------------------
# TF-IDF Engine (pure Python)
# ---------------------------------------------------------------------------

class TFIDFRetriever:
    """Lightweight TF-IDF retrieval engine using only stdlib."""

    def __init__(self):
        self.chunks: list[str] = []
        self.chunk_tokens: list[list[str]] = []
        self.chunk_tf: list[Counter] = []
        self.idf: dict[str, float] = {}
        self._built = False

    def add_chunks(self, chunks: list[str]) -> None:
        """Add text chunks to the index."""
        for chunk in chunks:
            tokens = _tokenize(chunk)
            if tokens:
                self.chunks.append(chunk)
                self.chunk_tokens.append(tokens)
                self.chunk_tf.append(Counter(tokens))

    def build_index(self) -> None:
        """Compute IDF scores."""
        n = len(self.chunks)
        if n == 0:
            return
        df: Counter = Counter()
        for tf in self.chunk_tf:
            df.update(set(tf.keys()))
        self.idf = {
            term: math.log((n + 1) / (freq + 1)) + 1
            for term, freq in df.items()
        }
        self._built = True

    def score(self, query_tokens: list[str], doc_idx: int) -> float:
        """Compute TF-IDF score for a document given query tokens."""
        tf = self.chunk_tf[doc_idx]
        total_tokens = sum(tf.values()) or 1
        score = 0.0
        for token in query_tokens:
            if token in tf:
                term_tf = tf[token] / total_tokens
                term_idf = self.idf.get(token, 0.0)
                score += term_tf * term_idf
        return score

    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        """Return top_k most relevant chunks for the query."""
        if not self._built or not self.chunks:
            return []

        query_tokens = _tokenize(query)
        if not query_tokens:
            return self.chunks[:top_k]

        scores = [
            (self.score(query_tokens, i), i)
            for i in range(len(self.chunks))
        ]
        scores.sort(key=lambda x: x[0], reverse=True)
        return [self.chunks[i] for _, i in scores[:top_k] if _ > 0]


# ---------------------------------------------------------------------------
# KnowledgeBase: main interface
# ---------------------------------------------------------------------------

class KnowledgeBase:
    """
    TITAN RAG knowledge base for snake game.
    Indexes game documentation and provides retrieval + expert rules.
    """

    def __init__(self, doc_paths: Optional[list[str]] = None):
        self.retriever = TFIDFRetriever()
        self._expert_rules = dict(SNAKE_EXPERT_RULES)
        self._loaded_docs: list[str] = []

        paths = doc_paths if doc_paths is not None else _DEFAULT_DOCS
        for path in paths:
            self._load_doc(path)

        self.retriever.build_index()

    def _load_doc(self, path: str) -> None:
        """Load and chunk a markdown document into the retriever."""
        if not os.path.exists(path):
            return
        with open(path, encoding="utf-8") as f:
            text = f.read()
        chunks = _chunk_text(text, max_chars=300)
        self.retriever.add_chunks(chunks)
        self._loaded_docs.append(path)

    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        """
        Retrieve top-k relevant document chunks + matching expert rules.
        Returns combined list of relevant knowledge strings.
        """
        doc_results = self.retriever.retrieve(query, top_k=top_k)

        # Also check expert rules for keyword matches
        query_lower = query.lower()
        rule_results = []
        for key, rule in self._expert_rules.items():
            # Match if any keyword from the rule or key appears in query
            if (key in query_lower or
                    any(word in query_lower for word in key.split('_'))):
                rule_results.append(f"[专家规则] {rule}")

        return (doc_results + rule_results)[:top_k + 2]

    def get_expert_rule(self, rule_key: str) -> Optional[str]:
        """Get a specific expert rule by key."""
        return self._expert_rules.get(rule_key)

    def get_all_expert_rules(self) -> dict[str, str]:
        """Return all expert rules."""
        return dict(self._expert_rules)

    @property
    def loaded_docs(self) -> list[str]:
        return list(self._loaded_docs)

    @property
    def chunk_count(self) -> int:
        return len(self.retriever.chunks)
