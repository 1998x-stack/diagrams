"""测试终止条件检查器和 run_until_termination 流程"""
import unittest
from unittest.mock import MagicMock, patch
from core.termination import TerminationChecker, TerminationResult
from config.params import (
    TERMINATION_BANK_CAPITAL_MIN,
    TERMINATION_CHRONIC_UNEMPLOYMENT_RATE,
    TERMINATION_CHRONIC_UNEMPLOYMENT_MONTHS,
)


def _make_economy(capital=10000, active_factories=3, unemp_rate=0.1, num_workers=10):
    """构建 mock Economy"""
    economy = MagicMock()
    economy.month = 1

    # 银行
    economy.bank.capital = capital

    # 工厂
    factories = []
    for i in range(3):
        f = MagicMock()
        f.is_bankrupt = (i >= active_factories)
        factories.append(f)
    economy.factories = factories

    # 工人
    workers = []
    unemployed_count = int(num_workers * unemp_rate)
    for i in range(num_workers):
        w = MagicMock()
        w.is_employed = (i >= unemployed_count)
        workers.append(w)
    economy.workers = workers

    return economy


class TestTerminationChecker(unittest.TestCase):
    def setUp(self):
        self.checker = TerminationChecker()

    def test_no_termination_normal(self):
        eco = _make_economy(capital=10000, active_factories=3, unemp_rate=0.1)
        self.assertIsNone(self.checker.check(eco))

    def test_bank_bankrupt(self):
        eco = _make_economy(capital=TERMINATION_BANK_CAPITAL_MIN - 1000)
        result = self.checker.check(eco)
        self.assertIsNotNone(result)
        self.assertEqual(result.reason, "bank_bankrupt")

    def test_bank_at_exact_limit_no_termination(self):
        # 恰好等于下限：不触发（严格小于才触发）
        eco = _make_economy(capital=TERMINATION_BANK_CAPITAL_MIN)
        self.assertIsNone(self.checker.check(eco))

    def test_all_factories_bankrupt(self):
        eco = _make_economy(active_factories=0)
        result = self.checker.check(eco)
        self.assertIsNotNone(result)
        self.assertEqual(result.reason, "all_factories_bankrupt")

    def test_one_active_factory_no_termination(self):
        eco = _make_economy(active_factories=1)
        self.assertIsNone(self.checker.check(eco))

    def test_chronic_unemployment_streak(self):
        high_unemp = TERMINATION_CHRONIC_UNEMPLOYMENT_RATE + 0.05
        checker = TerminationChecker()
        eco = _make_economy(unemp_rate=high_unemp)

        # 连续 N-1 个月不触发
        for i in range(TERMINATION_CHRONIC_UNEMPLOYMENT_MONTHS - 1):
            eco.month = i + 1
            self.assertIsNone(checker.check(eco))

        # 第 N 个月触发
        eco.month = TERMINATION_CHRONIC_UNEMPLOYMENT_MONTHS
        result = checker.check(eco)
        self.assertIsNotNone(result)
        self.assertEqual(result.reason, "chronic_high_unemployment")

    def test_unemployment_streak_resets(self):
        high_unemp = TERMINATION_CHRONIC_UNEMPLOYMENT_RATE + 0.05
        checker = TerminationChecker()
        eco = _make_economy(unemp_rate=high_unemp)

        # 3 个月高失业
        for i in range(3):
            eco.month = i + 1
            checker.check(eco)
        self.assertEqual(checker.unemployment_streak, 3)

        # 失业率下降，计数器重置
        eco2 = _make_economy(unemp_rate=0.1)
        checker.check(eco2)
        self.assertEqual(checker.unemployment_streak, 0)

    def test_termination_result_fields(self):
        eco = _make_economy(capital=TERMINATION_BANK_CAPITAL_MIN - 1)
        eco.month = 42
        result = self.checker.check(eco)
        self.assertIsInstance(result, TerminationResult)
        self.assertEqual(result.month, 42)
        self.assertIsInstance(result.description, str)
        self.assertGreater(len(result.description), 0)


class TestRunUntilTermination(unittest.TestCase):
    def test_terminates_on_bank_collapse(self):
        """整合测试：银行破产后仿真立即终止"""
        from core.simulation import TownEconomy
        from analysis.statistics import EconomyStats

        economy = TownEconomy(seed=42)
        stats   = EconomyStats(economy)

        # 强制银行破产
        economy.bank.capital = TERMINATION_BANK_CAPITAL_MIN - 9999

        months_run = []

        def on_step(month, snap, diag):
            months_run.append(month)

        result = economy.run_until_termination(
            stats=stats, on_step=on_step, use_llm=False
        )

        # 应在第 1 月终止（银行已破产）
        self.assertEqual(result.reason, "bank_bankrupt")
        self.assertEqual(len(months_run), 1)

    def test_autonomous_runs_multiple_months(self):
        """自主模式能正常运行多个月"""
        from core.simulation import TownEconomy
        from analysis.statistics import EconomyStats

        economy = TownEconomy(seed=99)
        stats   = EconomyStats(economy)

        months_run = []

        def on_step(month, snap, diag):
            months_run.append(month)
            # 人为终止：运行 5 个月后让银行破产
            if month >= 5:
                economy.bank.capital = TERMINATION_BANK_CAPITAL_MIN - 1

        result = economy.run_until_termination(
            stats=stats, on_step=on_step, use_llm=False
        )

        self.assertGreaterEqual(len(months_run), 5)
        self.assertIn(result.reason, ("bank_bankrupt", "all_factories_bankrupt",
                                     "chronic_high_unemployment", "max_months"))


if __name__ == "__main__":
    unittest.main()
