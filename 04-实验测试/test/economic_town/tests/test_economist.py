"""经济学家 Agent 测试"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import patch

from core.simulation import TownEconomy
from analysis.statistics import EconomyStats
from agents.economist import EconomistAgent, EconomicDiagnosis, RiskScore


# ── 辅助：构造最小指标字典 ──────────────────────────────────
def _make_metrics(
    month=1, emp=0.9, wage=100.0, bad_debt=0.05, gini=0.15,
    spread=0.03, profit_margin=0.1, production=300.0, revenue=3000.0,
    bankrupt=0, bank_profit=-50.0, net_inflow=2000.0,
):
    return {
        "month": month,
        "employment_rate": emp,
        "unemployment_rate": 1 - emp,
        "avg_wage": wage,
        "bad_debt_rate": bad_debt,
        "gini_coefficient": gini,
        "interest_spread": spread,
        "avg_profit_margin": profit_margin,
        "total_production": production,
        "total_revenue": revenue,
        "bankrupt_factories": bankrupt,
        "bank_monthly_profit": bank_profit,
        "net_external_inflow": net_inflow,
        "external_revenue_inflow": revenue,
        "loan_rate": 0.04,
        "deposit_rate": 0.01,
    }


class TestRiskScore(unittest.TestCase):
    def test_total_weighted(self):
        r = RiskScore(employment=40, financial=20, inequality=30, external=50, wage=10)
        expected = 40*0.3 + 20*0.25 + 30*0.2 + 50*0.15 + 10*0.1
        self.assertAlmostEqual(r.total, expected, places=4)

    def test_level_low(self):
        r = RiskScore(10, 5, 5, 5, 5)
        self.assertIn("低风险", r.level)

    def test_level_high(self):
        r = RiskScore(80, 80, 80, 80, 80)
        self.assertIn("高风险", r.level)


class TestEconomistAgentRules(unittest.TestCase):
    def setUp(self):
        self.eco = EconomistAgent()

    def test_observe_returns_diagnosis(self):
        m = _make_metrics(month=1)
        diag = self.eco.observe(m)
        self.assertIsInstance(diag, EconomicDiagnosis)
        self.assertEqual(diag.month, 1)

    def test_phase_crisis_on_high_bankrupt(self):
        for i in range(1, 4):
            diag = self.eco.observe(_make_metrics(month=i, bankrupt=2, bad_debt=0.30))
        self.assertEqual(diag.phase, "危机")

    def test_phase_recession_low_employment(self):
        # 连续几个月就业率低且下行
        for i, emp in enumerate([0.6, 0.5, 0.38, 0.35], start=1):
            diag = self.eco.observe(_make_metrics(month=i, emp=emp))
        self.assertEqual(diag.phase, "衰退")

    def test_phase_expansion(self):
        # 就业率高且连续上升，产出增长
        for i in range(1, 6):
            emp = 0.7 + i * 0.05
            prod = 200 + i * 30
            diag = self.eco.observe(_make_metrics(month=i, emp=emp, production=prod))
        self.assertEqual(diag.phase, "扩张")

    def test_phase_steady_stable(self):
        for i in range(1, 8):
            diag = self.eco.observe(_make_metrics(month=i, emp=0.93))
        self.assertEqual(diag.phase, "稳态")

    def test_warnings_high_unemployment(self):
        diag = self.eco.observe(_make_metrics(emp=0.6))
        self.assertTrue(any("失业" in w for w in diag.warnings))

    def test_warnings_bad_debt(self):
        diag = self.eco.observe(_make_metrics(bad_debt=0.20))
        self.assertTrue(any("坏账" in w for w in diag.warnings))

    def test_no_warnings_healthy(self):
        diag = self.eco.observe(_make_metrics(emp=1.0, bad_debt=0.01))
        self.assertEqual(diag.warnings, [])

    def test_bank_advice_high_bad_debt(self):
        diag = self.eco.observe(_make_metrics(bad_debt=0.20))
        self.assertIn("收紧", diag.bank_advice)

    def test_factory_advice_negative_profit(self):
        diag = self.eco.observe(_make_metrics(profit_margin=-0.1))
        self.assertIn("削减", diag.factory_advice)

    def test_worker_advice_high_unemployment(self):
        diag = self.eco.observe(_make_metrics(emp=0.6))
        self.assertIn("心理工资", diag.worker_advice)

    def test_trends_computed_after_window(self):
        for i in range(5):
            self.eco.observe(_make_metrics(month=i+1, emp=0.6 + i*0.08))
        d = self.eco.latest_diagnosis()
        self.assertIn("employment_delta", d.trends)
        self.assertGreater(d.trends["employment_delta"], 0)

    def test_phase_history(self):
        for i in range(3):
            self.eco.observe(_make_metrics(month=i+1))
        hist = self.eco.phase_history()
        self.assertEqual(len(hist), 3)

    def test_format_diagnosis_contains_phase(self):
        self.eco.observe(_make_metrics())
        text = self.eco.format_diagnosis()
        self.assertIn("阶段", text)
        self.assertIn("风险", text)
        self.assertIn("[银行]", text)
        self.assertIn("[工厂]", text)
        self.assertIn("[工人]", text)


class TestEconomistLLMMock(unittest.TestCase):
    def setUp(self):
        self.eco = EconomistAgent()
        self.eco.observe(_make_metrics(month=1))

    def test_conclude_fills_llm_conclusion(self):
        fake = "核心矛盾：就业波动。风险：坏账积累。展望：3个月内稳定。"
        with patch("agents.economist._ollama_chat", return_value=fake):
            result = self.eco.conclude()
        self.assertEqual(result, fake)
        self.assertEqual(self.eco.latest_diagnosis().llm_conclusion, fake)

    def test_conclude_returns_empty_without_history(self):
        fresh = EconomistAgent()
        result = fresh.conclude()
        self.assertEqual(result, "")

    def test_format_includes_llm_conclusion(self):
        fake = "这是LLM的结论文字"
        with patch("agents.economist._ollama_chat", return_value=fake):
            self.eco.conclude()
        text = self.eco.format_diagnosis()
        self.assertIn(fake, text)


class TestEconomistIntegration(unittest.TestCase):
    """与 TownEconomy 集成测试"""

    def test_economist_exists_in_economy(self):
        e = TownEconomy(seed=42)
        self.assertIsInstance(e.economist, EconomistAgent)

    def test_economist_produces_diagnosis_per_month(self):
        e = TownEconomy(seed=42)
        stats = EconomyStats(e)
        for _ in range(6):
            snap = e.step()
            metrics = stats.update(snap)
            e.economist.observe(metrics)
        self.assertEqual(len(e.economist.diagnoses), 6)

    def test_all_phases_are_valid_strings(self):
        e = TownEconomy(seed=42)
        stats = EconomyStats(e)
        for _ in range(12):
            snap = e.step()
            metrics = stats.update(snap)
            diag = e.economist.observe(metrics)
            self.assertIn(diag.phase, EconomistAgent.PHASES)

    def test_risk_scores_in_valid_range(self):
        e = TownEconomy(seed=42)
        stats = EconomyStats(e)
        for _ in range(12):
            snap = e.step()
            metrics = stats.update(snap)
            diag = e.economist.observe(metrics)
            for score in [diag.risk.employment, diag.risk.financial,
                          diag.risk.inequality, diag.risk.external, diag.risk.wage]:
                self.assertGreaterEqual(score, 0.0)
                self.assertLessEqual(score, 100.0)

    def test_economist_in_60_month_run(self):
        e = TownEconomy(seed=42)
        stats = EconomyStats(e)
        for _ in range(60):
            snap = e.step()
            metrics = stats.update(snap)
            e.economist.observe(metrics)
        self.assertEqual(len(e.economist.diagnoses), 60)
        phases = e.economist.phase_history()
        # 60个月内应出现至少2种不同阶段
        self.assertGreater(len(set(phases)), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
