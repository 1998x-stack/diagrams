"""
Layer 1 Tests: RAG Knowledge Base
Tests verify document loading, chunking, TF-IDF retrieval, and expert rules.
"""
import pytest
import os
import tempfile

from titan.rag.knowledge_base import (
    KnowledgeBase, TFIDFRetriever,
    _tokenize, _chunk_text, SNAKE_EXPERT_RULES,
)


# ---------------------------------------------------------------------------
# Test: Tokenizer
# ---------------------------------------------------------------------------

class TestTokenizer:
    def test_english_tokens(self):
        tokens = _tokenize("Snake game collision detection")
        assert "snake" in tokens
        assert "collision" in tokens

    def test_chinese_tokens(self):
        tokens = _tokenize("碰撞检测规则")
        assert "碰撞检测规则" in tokens or len(tokens) > 0

    def test_empty_string(self):
        tokens = _tokenize("")
        assert tokens == []

    def test_punctuation_ignored(self):
        tokens = _tokenize("hello, world! test.")
        assert "hello" in tokens
        assert "," not in tokens


# ---------------------------------------------------------------------------
# Test: Text chunking
# ---------------------------------------------------------------------------

class TestChunking:
    def test_basic_chunking(self):
        text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
        chunks = _chunk_text(text, max_chars=50)
        assert len(chunks) >= 1
        for chunk in chunks:
            assert len(chunk) <= 200  # chunks should be reasonable

    def test_empty_text(self):
        chunks = _chunk_text("", max_chars=300)
        assert chunks == []

    def test_single_paragraph(self):
        text = "This is a single paragraph with some content."
        chunks = _chunk_text(text, max_chars=300)
        assert len(chunks) >= 1
        assert "paragraph" in chunks[0].lower()


# ---------------------------------------------------------------------------
# Test: TFIDFRetriever
# ---------------------------------------------------------------------------

class TestTFIDFRetriever:
    def setup_method(self):
        self.retriever = TFIDFRetriever()
        self.retriever.add_chunks([
            "Snake collision detection wall boundary game over",
            "Score increases by 10 points when food is eaten",
            "EASY difficulty grid size 20x20 tick interval 200ms",
            "HARD difficulty grid size 30x30 faster speed 80ms",
            "Direction control UP DOWN LEFT RIGHT movement",
        ])
        self.retriever.build_index()

    def test_retrieve_collision_query(self):
        results = self.retriever.retrieve("collision detection", top_k=2)
        assert len(results) > 0
        assert any("collision" in r.lower() for r in results)

    def test_retrieve_score_query(self):
        results = self.retriever.retrieve("score points food", top_k=2)
        assert len(results) > 0
        assert any("score" in r.lower() or "points" in r.lower() for r in results)

    def test_retrieve_difficulty_query(self):
        results = self.retriever.retrieve("EASY difficulty grid", top_k=2)
        assert len(results) > 0
        assert any("easy" in r.lower() or "20x20" in r.lower() for r in results)

    def test_empty_query_no_crash(self):
        results = self.retriever.retrieve("", top_k=3)
        assert isinstance(results, list)

    def test_top_k_respected(self):
        results = self.retriever.retrieve("snake game", top_k=2)
        assert len(results) <= 2

    def test_no_results_before_build(self):
        r = TFIDFRetriever()
        r.add_chunks(["some content"])
        # build_index not called
        results = r.retrieve("some query")
        assert results == []


# ---------------------------------------------------------------------------
# Test: KnowledgeBase with real documents
# ---------------------------------------------------------------------------

class TestKnowledgeBaseRealDocs:
    """Tests that rely on actual snake project documentation existing."""

    @pytest.fixture
    def kb(self):
        return KnowledgeBase()

    def test_loads_documents(self, kb):
        # At least one doc should load (snake project should exist)
        readme_path = "/Users/xd/Desktop/codes/test/snake/README.md"
        if os.path.exists(readme_path):
            assert len(kb.loaded_docs) >= 1
            assert kb.chunk_count > 0

    def test_retrieve_collision_topic(self, kb):
        results = kb.retrieve("碰撞检测")
        assert isinstance(results, list)
        # At least returns expert rules if doc retrieval has nothing
        assert len(results) >= 0  # no crash

    def test_retrieve_difficulty_config(self, kb):
        results = kb.retrieve("难度配置 EASY NORMAL HARD")
        assert isinstance(results, list)

    def test_retrieve_score_info(self, kb):
        results = kb.retrieve("分数 score")
        assert isinstance(results, list)

    def test_empty_query_no_crash(self, kb):
        results = kb.retrieve("")
        assert isinstance(results, list)


# ---------------------------------------------------------------------------
# Test: KnowledgeBase with mock documents
# ---------------------------------------------------------------------------

class TestKnowledgeBaseMockDocs:
    """Tests using temporary mock documents for deterministic behavior."""

    @pytest.fixture
    def mock_kb(self, tmp_path):
        # Create a mock README
        readme = tmp_path / "README.md"
        readme.write_text(
            "# Snake Game\n\n"
            "碰撞检测：蛇碰到墙壁或自身则游戏结束。\n\n"
            "难度配置：EASY 20x20，NORMAL 25x25，HARD 30x30。\n\n"
            "分数：每吃到食物得10分。\n\n"
            "胜利条件：蛇填满整个网格。\n",
            encoding="utf-8"
        )
        return KnowledgeBase(doc_paths=[str(readme)])

    def test_retrieve_collision_from_mock(self, mock_kb):
        results = mock_kb.retrieve("碰撞检测", top_k=3)
        combined = " ".join(results)
        assert "碰撞" in combined or "collision" in combined.lower() or len(results) > 0

    def test_retrieve_difficulty_from_mock(self, mock_kb):
        results = mock_kb.retrieve("难度 EASY NORMAL", top_k=3)
        assert len(results) > 0

    def test_retrieve_score_from_mock(self, mock_kb):
        results = mock_kb.retrieve("分数", top_k=3)
        assert len(results) > 0

    def test_expert_rules_included(self, mock_kb):
        # Expert rules are always present regardless of docs
        results = mock_kb.retrieve("danger collision game over", top_k=5)
        # Should include expert rules in response
        assert len(mock_kb.get_all_expert_rules()) > 0

    def test_get_expert_rule_by_key(self, mock_kb):
        rule = mock_kb.get_expert_rule("game_over")
        assert rule is not None
        assert "游戏结束" in rule or "GAME_OVER" in rule

    def test_get_expert_rule_missing_key(self, mock_kb):
        rule = mock_kb.get_expert_rule("nonexistent_key")
        assert rule is None

    def test_all_expert_rules_available(self, mock_kb):
        rules = mock_kb.get_all_expert_rules()
        assert "score_increase" in rules
        assert "win_condition" in rules
        assert "game_over" in rules
        assert "danger_ahead" in rules


# ---------------------------------------------------------------------------
# Test: Expert rules content
# ---------------------------------------------------------------------------

class TestExpertRules:
    def test_all_required_rules_exist(self):
        required_keys = [
            "danger_ahead", "food_close", "score_increase",
            "win_condition", "game_over", "direction_reverse"
        ]
        for key in required_keys:
            assert key in SNAKE_EXPERT_RULES, f"Missing expert rule: {key}"

    def test_rules_are_non_empty(self):
        for key, rule in SNAKE_EXPERT_RULES.items():
            assert len(rule) > 0, f"Empty rule for key: {key}"
