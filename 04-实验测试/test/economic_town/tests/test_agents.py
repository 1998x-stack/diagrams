"""阶段1 单元测试 —— 验证所有 Agent 类的基础行为"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
import unittest

from agents.bank import Bank
from agents.worker import Worker
from agents.factory import FactoryOwner
from agents.retailer import Retailer
from agents.external_market import ExternalMarket
from config.params import FACTORY_CONFIGS


class TestBank(unittest.TestCase):

    def setUp(self):
        self.bank = Bank()

    def test_initial_state(self):
        self.assertGreater(self.bank.capital, 0)
        self.assertEqual(self.bank.deposits, 0.0)
        self.assertEqual(len(self.bank.loans), 0)

    def test_accept_deposit(self):
        self.bank.accept_deposit(1000.0)
        self.assertEqual(self.bank.deposits, 1000.0)

    def test_grant_loan_basic(self):
        self.bank.accept_deposit(2000.0)
        amount = self.bank.grant_loan(1, 500.0)
        self.assertGreater(amount, 0)
        self.assertLessEqual(amount, 500.0)
        self.assertIn(1, self.bank.loans)

    def test_grant_loan_liquidity_limit(self):
        """存款不足时不应超额贷款"""
        self.bank.accept_deposit(100.0)  # 很少存款
        amount = self.bank.grant_loan(1, 10000.0)
        # 贷款后准备金应仍满足要求
        remaining = self.bank.deposits + self.bank.capital - amount
        reserve_needed = self.bank.deposits * 0.20
        self.assertGreaterEqual(remaining, reserve_needed - 0.01)  # 允许浮点误差

    def test_repay_loan_full(self):
        self.bank.accept_deposit(2000.0)
        loan = self.bank.grant_loan(1, 300.0)
        due = loan * (1 + self.bank.loan_rate)
        repaid = self.bank.repay_loan(1, due)
        self.assertAlmostEqual(repaid, due, places=2)
        self.assertNotIn(1, self.bank.loans)

    def test_repay_loan_partial_bad_debt(self):
        self.bank.accept_deposit(2000.0)
        loan = self.bank.grant_loan(1, 300.0)
        repaid = self.bank.repay_loan(1, 0.0)  # 完全违约
        self.assertGreater(self.bank.bad_debt, 0)

    def test_update_rates_high_liquidity(self):
        """流动性充裕时利率应下降"""
        self.bank.accept_deposit(10000.0)
        old_deposit_rate = self.bank.deposit_rate
        self.bank.update_rates()
        self.assertLessEqual(self.bank.deposit_rate, old_deposit_rate)

    def test_monthly_settle_returns_snapshot(self):
        self.bank.accept_deposit(500.0)
        snap = self.bank.monthly_settle()
        self.assertIn("capital", snap)
        self.assertIn("deposits", snap)
        self.assertIn("loan_rate", snap)


class TestWorker(unittest.TestCase):

    def setUp(self):
        self.rng = random.Random(42)
        self.worker = Worker(worker_id=1, rng=self.rng)
        self.bank = Bank()
        self.bank.accept_deposit(5000.0)
        self.retailer = Retailer(retailer_id=0)

    def test_initial_state(self):
        self.assertFalse(self.worker.is_employed)
        self.assertGreater(self.worker.skill_level, 0)
        self.assertGreater(self.worker.savings, 0)

    def test_accept_job_above_reservation(self):
        high_wage = self.worker.reservation_wage * 2
        result = self.worker.accept_job(factory_id=1, wage=high_wage)
        self.assertTrue(result)
        self.assertTrue(self.worker.is_employed)

    def test_reject_job_below_reservation(self):
        result = self.worker.accept_job(factory_id=1, wage=0.01)
        self.assertFalse(result)
        self.assertFalse(self.worker.is_employed)

    def test_reservation_wage_drops_with_unemployment(self):
        self.worker.months_unemployed = 20
        eff = self.worker.effective_reservation_wage
        self.assertLess(eff, self.worker.reservation_wage)

    def test_lose_job(self):
        self.worker.accept_job(1, self.worker.reservation_wage * 2)
        self.worker.lose_job()
        self.assertFalse(self.worker.is_employed)

    def test_monthly_step_employed(self):
        wage = self.worker.reservation_wage * 2
        self.worker.accept_job(1, wage)
        snap = self.worker.monthly_step(self.bank, self.retailer)
        self.assertEqual(snap["employed"], True)
        self.assertGreater(snap["wage"], 0)
        self.assertGreater(self.bank.deposits, 5000.0)  # 存款增加了

    def test_monthly_step_unemployed(self):
        snap = self.worker.monthly_step(self.bank, self.retailer)
        self.assertEqual(snap["employed"], False)
        self.assertEqual(snap["wage"], 0)


class TestFactoryOwner(unittest.TestCase):

    def setUp(self):
        self.bank = Bank()
        self.bank.accept_deposit(5000.0)
        self.market = ExternalMarket(factory_ids=[0, 1, 2])
        self.factory = FactoryOwner(factory_id=0, config=FACTORY_CONFIGS[0])

    def test_initial_state(self):
        self.assertGreater(self.factory.cash, 0)
        self.assertFalse(self.factory.is_bankrupt)

    def test_plan_and_borrow(self):
        loan = self.factory.plan_and_borrow(self.bank)
        self.assertGreaterEqual(loan, 0)
        self.assertIn(0, self.bank.loans)

    def test_produce_positive_output(self):
        rng = random.Random(1)
        workers = [Worker(i, rng) for i in range(5)]
        for w in workers:
            w.accept_job(0, 120.0)
        self.factory.workers = workers
        self.factory.loan_amount = 300.0
        output = self.factory.produce()
        self.assertGreater(output, 0)

    def test_sell_returns_revenue(self):
        self.factory.production = 100.0
        revenue, sold_ratio = self.factory.sell(self.market)
        self.assertGreaterEqual(revenue, 0)
        self.assertGreaterEqual(sold_ratio, 0)

    def test_full_settle_cycle(self):
        """完整月度结算后应有历史记录"""
        self.factory.plan_and_borrow(self.bank)
        rng = random.Random(2)
        workers = [Worker(i, rng) for i in range(3)]
        available = workers[:]
        self.factory.hire_workers(available)
        self.factory.produce()
        self.factory.sell(self.market)
        self.factory.pay_wages()
        self.factory.repay_loan(self.bank)
        snap = self.factory.monthly_settle(self.bank, self.market)
        self.assertEqual(snap["factory_id"], 0)
        self.assertIn("profit", snap)


class TestRetailer(unittest.TestCase):

    def setUp(self):
        self.bank = Bank()
        self.bank.accept_deposit(1000.0)
        self.retailer = Retailer(retailer_id=0)

    def test_receive_spending(self):
        self.retailer.receive_spending(500.0)
        self.assertEqual(self.retailer.monthly_revenue, 500.0)

    def test_monthly_settle(self):
        self.retailer.receive_spending(1000.0)
        snap = self.retailer.monthly_settle(self.bank)
        self.assertAlmostEqual(snap["profit"], 100.0, places=2)    # 10% markup
        self.assertAlmostEqual(snap["import_cost"], 900.0, places=2)
        self.assertEqual(self.retailer.monthly_revenue, 0.0)  # 重置

    def test_profit_deposited_to_bank(self):
        deposits_before = self.bank.deposits
        self.retailer.receive_spending(1000.0)
        self.retailer.monthly_settle(self.bank)
        self.assertGreater(self.bank.deposits, deposits_before)


class TestExternalMarket(unittest.TestCase):

    def setUp(self):
        self.market = ExternalMarket(factory_ids=[0, 1, 2], seed=42)

    def test_demand_decreases_with_higher_price(self):
        d1 = self.market.get_demand(0, 8.0)
        d2 = self.market.get_demand(0, 12.0)
        self.assertGreater(d1, d2)

    def test_demand_positive(self):
        for fid in [0, 1, 2]:
            self.assertGreater(self.market.get_demand(fid, 10.0), 0)

    def test_sell_caps_at_demand(self):
        demand = self.market.get_demand(0, 10.0)
        revenue, ratio = self.market.sell(0, demand * 10, 10.0), None  # 供给远超需求
        # revenue 不应超过 demand * price
        self.assertLessEqual(revenue, demand * 10.0 + 0.01)

    def test_shock_changes_over_time(self):
        shock_before = self.market.shock[0]
        self.market.step_shock()
        # shock 可能变化（大概率）
        # 不做严格断言，只确保不报错且值合理
        self.assertGreater(self.market.shock[0], 0)

    def test_zero_price_returns_zero(self):
        self.assertEqual(self.market.get_demand(0, 0.0), 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
