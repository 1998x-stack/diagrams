"""阶段2 集成测试 —— 验证仿真核心循环正确运行"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from core.simulation import TownEconomy


class TestSimulationBasic(unittest.TestCase):

    def setUp(self):
        self.economy = TownEconomy(seed=42)

    def test_initial_state(self):
        self.assertEqual(self.economy.month, 0)
        self.assertEqual(len(self.economy.factories), 3)
        self.assertEqual(len(self.economy.workers), 30)
        self.assertEqual(len(self.economy.retailers), 1)
        self.assertGreater(self.economy.bank.deposits, 0)

    def test_single_step_returns_snapshot(self):
        snap = self.economy.step()
        self.assertEqual(snap["month"], 1)
        self.assertIn("bank", snap)
        self.assertIn("factories", snap)
        self.assertIn("workers", snap)
        self.assertIn("retailer", snap)

    def test_single_step_bank_data(self):
        snap = self.economy.step()
        bank = snap["bank"]
        self.assertIn("deposits", bank)
        self.assertIn("loan_rate", bank)
        self.assertIn("deposit_rate", bank)
        self.assertGreater(bank["deposits"], 0)

    def test_single_step_factory_data(self):
        snap = self.economy.step()
        self.assertGreater(len(snap["factories"]), 0)
        for f in snap["factories"]:
            self.assertIn("production", f)
            self.assertIn("revenue", f)
            self.assertIn("profit", f)
            self.assertGreaterEqual(f["production"], 0)

    def test_single_step_worker_data(self):
        snap = self.economy.step()
        self.assertEqual(len(snap["workers"]), 30)
        for w in snap["workers"]:
            self.assertIn("employed", w)
            self.assertIn("wage", w)
            self.assertIn("savings", w)

    def test_month_counter_increments(self):
        for i in range(5):
            snap = self.economy.step()
            self.assertEqual(snap["month"], i + 1)

    def test_run_12_months_no_crash(self):
        """跑满12个月不崩溃，返回正确数量快照"""
        snapshots = self.economy.run(12)
        self.assertEqual(len(snapshots), 12)
        self.assertEqual(self.economy.month, 12)

    def test_run_60_months_no_crash(self):
        """跑满60个月（5年）仿真不崩溃"""
        snapshots = self.economy.run(60)
        self.assertEqual(len(snapshots), 60)

    def test_employment_after_first_step(self):
        """第一个月后应有工人被雇佣"""
        self.economy.step()
        employed = sum(1 for w in self.economy.workers if w.is_employed)
        self.assertGreater(employed, 0)

    def test_bank_has_loans_after_step(self):
        """第一步后银行应该有贷款记录（或已还清）"""
        self.economy.step()
        # 贷款在月末会还清，检查历史快照中有贷款记录
        snap = self.economy.monthly_snapshots[0]
        # 工厂应该有产出（说明贷款被批了）
        total_production = sum(f["production"] for f in snap["factories"])
        self.assertGreater(total_production, 0)

    def test_retailer_receives_spending(self):
        """零售商应该收到工人消费"""
        self.economy.step()
        snap = self.economy.monthly_snapshots[0]
        # 如果有工人就业，零售商应有收入
        employed = sum(1 for w in snap["workers"] if w["employed"])
        if employed > 0:
            self.assertGreater(snap["retailer"]["revenue"], 0)

    def test_on_step_callback(self):
        """on_step 回调被正确调用"""
        called_months = []
        def callback(month, snapshot):
            called_months.append(month)
        self.economy.run(6, on_step=callback)
        self.assertEqual(called_months, [1, 2, 3, 4, 5, 6])

    def test_status_summary_string(self):
        self.economy.step()
        summary = self.economy.status_summary()
        self.assertIn("月份=1", summary)
        self.assertIn("在职=", summary)

    def test_bank_deposits_grow_with_workers(self):
        """工人储蓄应使银行存款随时间增长（至少不降为零）"""
        for _ in range(12):
            self.economy.step()
        self.assertGreater(self.economy.bank.deposits, 0)

    def test_no_negative_production(self):
        """任意时刻产量不应为负数"""
        snapshots = self.economy.run(12)
        for snap in snapshots:
            for f in snap["factories"]:
                self.assertGreaterEqual(f["production"], 0)

    def test_deterministic_with_same_seed(self):
        """相同种子应产生完全相同的结果"""
        e1 = TownEconomy(seed=99)
        e2 = TownEconomy(seed=99)
        s1 = e1.run(6)
        s2 = e2.run(6)
        for i in range(6):
            self.assertAlmostEqual(
                s1[i]["bank"]["deposits"],
                s2[i]["bank"]["deposits"],
                places=4
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
