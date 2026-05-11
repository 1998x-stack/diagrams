"""阶段3 测试 —— 验证统计分析模块"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import tempfile
import csv

from core.simulation import TownEconomy
from analysis.statistics import EconomyStats, compute_gini, extract_monthly_metrics


class TestGini(unittest.TestCase):

    def test_perfect_equality(self):
        """完全平等时基尼系数为 0"""
        vals = [100.0, 100.0, 100.0, 100.0]
        self.assertAlmostEqual(compute_gini(vals), 0.0, places=4)

    def test_perfect_inequality(self):
        """一人拥有全部财富时接近 1"""
        vals = [0.0, 0.0, 0.0, 1000.0]
        gini = compute_gini(vals)
        self.assertGreater(gini, 0.7)

    def test_partial_inequality(self):
        vals = [10.0, 50.0, 100.0, 200.0]
        gini = compute_gini(vals)
        self.assertGreater(gini, 0)
        self.assertLess(gini, 1)

    def test_empty_list(self):
        self.assertEqual(compute_gini([]), 0.0)

    def test_all_zeros(self):
        self.assertEqual(compute_gini([0.0, 0.0, 0.0]), 0.0)


class TestExtractMetrics(unittest.TestCase):

    def setUp(self):
        self.economy = TownEconomy(seed=42)
        self.economy.step()
        self.snapshot = self.economy.monthly_snapshots[0]

    def test_returns_dict_with_required_keys(self):
        metrics = extract_monthly_metrics(self.snapshot, self.economy)
        required = [
            "month", "employment_rate", "unemployment_rate", "avg_wage",
            "gini_coefficient", "total_production", "total_revenue",
            "bank_deposits", "loan_rate", "deposit_rate", "bad_debt_rate",
            "net_external_inflow",
        ]
        for key in required:
            self.assertIn(key, metrics, f"缺少指标: {key}")

    def test_employment_rate_in_range(self):
        metrics = extract_monthly_metrics(self.snapshot, self.economy)
        self.assertGreaterEqual(metrics["employment_rate"], 0.0)
        self.assertLessEqual(metrics["employment_rate"], 1.0)

    def test_unemployment_plus_employment_equals_1(self):
        metrics = extract_monthly_metrics(self.snapshot, self.economy)
        total = metrics["employment_rate"] + metrics["unemployment_rate"]
        self.assertAlmostEqual(total, 1.0, places=4)

    def test_gini_in_range(self):
        metrics = extract_monthly_metrics(self.snapshot, self.economy)
        self.assertGreaterEqual(metrics["gini_coefficient"], 0.0)
        self.assertLessEqual(metrics["gini_coefficient"], 1.0)

    def test_non_negative_production(self):
        metrics = extract_monthly_metrics(self.snapshot, self.economy)
        self.assertGreaterEqual(metrics["total_production"], 0)

    def test_interest_spread_positive(self):
        metrics = extract_monthly_metrics(self.snapshot, self.economy)
        self.assertGreater(metrics["interest_spread"], 0)


class TestEconomyStats(unittest.TestCase):

    def setUp(self):
        self.economy = TownEconomy(seed=42)
        self.economy.run(12)
        self.stats = EconomyStats(self.economy)
        self.stats.update_all()

    def test_update_all_fills_records(self):
        self.assertEqual(len(self.stats.records), 12)

    def test_latest_returns_last_month(self):
        latest = self.stats.latest()
        self.assertEqual(latest["month"], 12)

    def test_get_series_correct_length(self):
        series = self.stats.get_series("employment_rate")
        self.assertEqual(len(series), 12)

    def test_get_series_values_in_range(self):
        series = self.stats.get_series("employment_rate")
        for v in series:
            self.assertGreaterEqual(v, 0.0)
            self.assertLessEqual(v, 1.0)

    def test_summary_report_contains_key_sections(self):
        report = self.stats.summary_report()
        self.assertIn("就业", report)
        self.assertIn("银行", report)
        self.assertIn("工厂", report)
        self.assertIn("贸易", report)

    def test_export_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "output", "test.csv")
            self.stats.export_csv(path)
            self.assertTrue(os.path.exists(path))
            with open(path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            self.assertEqual(len(rows), 12)
            self.assertIn("month", rows[0])
            self.assertIn("employment_rate", rows[0])

    def test_check_alerts_returns_list(self):
        alerts = self.stats.check_alerts()
        self.assertIsInstance(alerts, list)

    def test_incremental_update(self):
        """每步更新与批量更新结果一致"""
        e2 = TownEconomy(seed=42)
        stats2 = EconomyStats(e2)
        for _ in range(12):
            snap = e2.step()
            stats2.update(snap)
        self.assertEqual(len(stats2.records), 12)
        # 对比最终就业率
        self.assertAlmostEqual(
            self.stats.latest()["employment_rate"],
            stats2.latest()["employment_rate"],
            places=4,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
