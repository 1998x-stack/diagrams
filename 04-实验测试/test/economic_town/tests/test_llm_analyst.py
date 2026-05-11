"""阶段4 测试 —— LLM 分析层（包含 mock 测试 + 真实调用测试）"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import json
import urllib.request
from unittest.mock import patch, MagicMock

from core.simulation import TownEconomy
from analysis.statistics import EconomyStats
from analysis.llm_analyst import LLMAnalyst, _ollama_chat, is_ollama_available


class TestOllamaConnection(unittest.TestCase):
    """测试 ollama 服务连通性（真实网络调用）"""

    def test_ollama_is_available(self):
        """ollama 服务必须运行且 qwen2.5:0.5b 已加载"""
        available = is_ollama_available()
        self.assertTrue(available, "ollama 服务不可用或 qwen2.5:0.5b 未加载，请运行: ollama serve")

    def test_ollama_generate_returns_text(self):
        """实际调用 ollama 生成一句话"""
        result = _ollama_chat("用一个词描述经济学", timeout=30)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)
        self.assertNotIn("[LLM 调用失败", result)
        self.assertNotIn("[LLM 异常", result)


class TestLLMAnalystMock(unittest.TestCase):
    """使用 mock 替代 ollama 调用，测试 LLM 分析层逻辑"""

    def setUp(self):
        self.economy = TownEconomy(seed=42)
        self.economy.run(12)
        self.stats = EconomyStats(self.economy)
        self.stats.update_all()
        self.analyst = LLMAnalyst(self.stats)

    def _mock_ollama(self, fake_response: str):
        """返回一个 patch context，将 ollama 替换为固定返回值"""
        return patch(
            "analysis.llm_analyst._ollama_chat",
            return_value=fake_response
        )

    def test_annual_report_stored(self):
        """年度报告应被存入 reports 列表"""
        fake_text = "本年经济稳健，就业充分。建议银行维持利率。"
        with self._mock_ollama(fake_text):
            result = self.analyst.annual_report(month=12)
        self.assertEqual(result, fake_text)
        self.assertEqual(len(self.analyst.reports), 1)
        self.assertEqual(self.analyst.reports[0]["type"], "annual")

    def test_alert_analysis_stored(self):
        alerts = ["⚠️  失业率过高: 35.0%"]
        fake_text = "失业率上升源于工厂贷款成本过高。"
        with self._mock_ollama(fake_text):
            result = self.analyst.alert_analysis(alerts)
        self.assertIn(result, fake_text)
        self.assertEqual(len(self.analyst.reports), 1)
        self.assertEqual(self.analyst.reports[0]["type"], "alert")

    def test_alert_analysis_empty_returns_empty(self):
        result = self.analyst.alert_analysis([])
        self.assertEqual(result, "")

    def test_worker_story_returns_string(self):
        worker_data = {
            "employed": True, "wage": 120.0,
            "savings": 500.0, "local_spend": 60.0
        }
        fake_text = "小王这个月在厂A辛勤工作，存下了不少积蓄。"
        with self._mock_ollama(fake_text):
            result = self.analyst.worker_story(worker_data)
        self.assertEqual(result, fake_text)

    def test_should_run_annual_logic(self):
        self.assertTrue(self.analyst.should_run_annual(12))
        self.assertTrue(self.analyst.should_run_annual(24))
        self.assertFalse(self.analyst.should_run_annual(0))
        self.assertFalse(self.analyst.should_run_annual(6))
        self.assertFalse(self.analyst.should_run_annual(11))

    def test_should_run_alert_logic(self):
        self.assertTrue(self.analyst.should_run_alert(["⚠️ 失业率过高"]))
        self.assertFalse(self.analyst.should_run_alert([]))

    def test_prompt_contains_data(self):
        """确保 Prompt 中包含关键数据"""
        prompt = self.analyst._build_annual_prompt(year=1)
        self.assertIn("就业率", prompt)
        self.assertIn("贷款利率", prompt)
        self.assertIn("基尼系数", prompt)


class TestLLMAnalystRealCall(unittest.TestCase):
    """真实调用 ollama，验证年度报告内容质量（非结构性，只验证长度和无错误）"""

    def setUp(self):
        if not is_ollama_available():
            self.skipTest("ollama 不可用，跳过真实调用测试")
        self.economy = TownEconomy(seed=42)
        self.economy.run(12)
        self.stats = EconomyStats(self.economy)
        self.stats.update_all()
        self.analyst = LLMAnalyst(self.stats)

    def test_real_annual_report_not_empty(self):
        report = self.analyst.annual_report(month=12)
        self.assertGreater(len(report), 10)
        self.assertNotIn("[LLM 调用失败", report)

    def test_real_alert_analysis(self):
        alerts = ["⚠️  失业率过高: 35.0%", "⚠️  银行坏账率过高: 25.0%"]
        result = self.analyst.alert_analysis(alerts)
        self.assertGreater(len(result), 10)


if __name__ == "__main__":
    unittest.main(verbosity=2)
