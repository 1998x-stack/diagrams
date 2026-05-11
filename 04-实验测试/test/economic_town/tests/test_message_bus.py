"""测试 MessageBus 和消息协议"""
import unittest
from core.message_bus import MessageBus
from core.messages import (
    Message, make_economic_report, make_rate_announcement,
    make_credit_score, make_warning_alert, make_labor_market_signal,
    TOPIC_ECONOMIC_REPORT, TOPIC_RATE_ANNOUNCEMENT, TOPIC_CREDIT_SCORE,
    TOPIC_WARNING_ALERT, TOPIC_LABOR_MARKET,
)
from agents.economist import EconomicDiagnosis, RiskScore


def _make_diag(month=1, phase="稳态") -> EconomicDiagnosis:
    return EconomicDiagnosis(
        month=month, phase=phase, phase_reason="测试",
        risk=RiskScore(10, 10, 10, 10, 10),
        trends={}, warnings=[], bank_advice="", factory_advice="", worker_advice=""
    )


class TestMessageBus(unittest.TestCase):
    def setUp(self):
        self.bus = MessageBus()

    def test_publish_and_get_latest(self):
        msg = Message(topic="test.topic", month=1, sender="x", payload={"v": 1})
        self.bus.publish(msg)
        result = self.bus.get_latest("test.topic")
        self.assertIsNotNone(result)
        self.assertEqual(result.payload["v"], 1)

    def test_get_latest_returns_none_for_unknown_topic(self):
        self.assertIsNone(self.bus.get_latest("nonexistent"))

    def test_latest_is_most_recent(self):
        for i in range(3):
            self.bus.publish(Message("t", i, "x", {"v": i}))
        self.assertEqual(self.bus.get_latest("t").payload["v"], 2)

    def test_get_history(self):
        for i in range(5):
            self.bus.publish(Message("t", i, "x", {"v": i}))
        hist = self.bus.get_history("t", n=3)
        self.assertEqual(len(hist), 3)
        self.assertEqual(hist[-1].payload["v"], 4)

    def test_get_by_month(self):
        for i in range(5):
            self.bus.publish(Message("t", i + 1, "x", {"v": i}))
        msg = self.bus.get_by_month("t", month=3)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.payload["v"], 2)

    def test_subscribe_callback(self):
        received = []
        self.bus.subscribe("evt", lambda m: received.append(m.payload["v"]))
        self.bus.publish(Message("evt", 1, "x", {"v": 42}))
        self.assertEqual(received, [42])

    def test_count(self):
        for _ in range(4):
            self.bus.publish(Message("t", 1, "x", {}))
        self.assertEqual(self.bus.count("t"), 4)

    def test_topics(self):
        self.bus.publish(Message("a", 1, "x", {}))
        self.bus.publish(Message("b", 1, "y", {}))
        self.assertIn("a", self.bus.topics())
        self.assertIn("b", self.bus.topics())

    def test_clear(self):
        self.bus.publish(Message("t", 1, "x", {}))
        self.bus.clear()
        self.assertIsNone(self.bus.get_latest("t"))


class TestMessages(unittest.TestCase):
    def test_make_economic_report(self):
        diag = _make_diag(month=5, phase="扩张")
        msg = make_economic_report(5, diag)
        self.assertEqual(msg.topic, TOPIC_ECONOMIC_REPORT)
        self.assertEqual(msg.month, 5)
        self.assertEqual(msg.payload["phase"], "扩张")
        self.assertIn("risk_total", msg.payload)
        self.assertIn("recommended_loan_rate_delta", msg.payload)

    def test_make_rate_announcement(self):
        from agents.bank import Bank
        bank = Bank()
        msg = make_rate_announcement(3, bank)
        self.assertEqual(msg.topic, TOPIC_RATE_ANNOUNCEMENT)
        self.assertIn("loan_rate", msg.payload)
        self.assertIn("deposit_rate", msg.payload)

    def test_make_credit_score(self):
        msg = make_credit_score(2, factory_id=0, score=0.8,
                                history="good", avg_profit=100.0, requested=2000.0)
        self.assertEqual(msg.topic, TOPIC_CREDIT_SCORE)
        self.assertEqual(msg.payload["factory_id"], 0)
        self.assertEqual(msg.payload["credit_score"], 0.8)

    def test_make_warning_alert(self):
        msg = make_warning_alert(4, ["失业率过高"], severity="critical")
        self.assertEqual(msg.topic, TOPIC_WARNING_ALERT)
        self.assertEqual(msg.payload["severity"], "critical")
        self.assertIn("失业率过高", msg.payload["warnings"])

    def test_make_labor_market_signal(self):
        msg = make_labor_market_signal(1, 0.2, 90.0, 24, 6)
        self.assertEqual(msg.topic, TOPIC_LABOR_MARKET)
        self.assertAlmostEqual(msg.payload["unemployment_rate"], 0.2)


class TestMessageBusIntegration(unittest.TestCase):
    """测试 Agent 通过消息总线通信"""

    def test_economist_publishes_to_bus(self):
        from agents.economist import EconomistAgent
        bus = MessageBus()
        economist = EconomistAgent()
        diag = _make_diag(month=1, phase="复苏")
        economist.act(diag, bus)
        self.assertIsNotNone(bus.get_latest(TOPIC_ECONOMIC_REPORT))
        self.assertEqual(bus.get_latest(TOPIC_ECONOMIC_REPORT).payload["phase"], "复苏")

    def test_economist_publishes_warning(self):
        from agents.economist import EconomistAgent
        bus = MessageBus()
        economist = EconomistAgent()
        diag = _make_diag(month=1)
        diag.warnings = ["失业率过高 35.0%"]
        economist.act(diag, bus)
        self.assertIsNotNone(bus.get_latest(TOPIC_WARNING_ALERT))

    def test_bank_perceives_economist_report(self):
        from agents.bank import Bank
        from agents.economist import EconomistAgent
        bus = MessageBus()
        bank = Bank()
        economist = EconomistAgent()

        # 经济学家发布报告
        diag = _make_diag(month=1, phase="危机")
        economist.act(diag, bus)

        # 银行读取
        perceived = bank.perceive(bus)
        self.assertEqual(perceived.get("phase"), "危机")
        self.assertIn("econ_rate_delta", perceived)

    def test_bank_perceives_credit_scores(self):
        from agents.bank import Bank
        bus = MessageBus()
        bank = Bank()

        # 工厂发布信用评分
        msg = make_credit_score(1, factory_id=0, score=0.9,
                                history="good", avg_profit=200.0, requested=3000.0)
        bus.publish(msg)

        perceived = bank.perceive(bus)
        self.assertIn(0, perceived["factory_credit_scores"])
        self.assertAlmostEqual(perceived["factory_credit_scores"][0], 0.9)

    def test_factory_perceives_rate_announcement(self):
        from agents.factory import FactoryOwner
        from agents.bank import Bank
        from config.params import FACTORY_CONFIGS
        bus = MessageBus()
        bank = Bank()
        factory = FactoryOwner(0, FACTORY_CONFIGS[0])

        # 银行发布利率公告
        msg = make_rate_announcement(1, bank)
        msg.payload["rate_direction"] = "up"
        msg.payload["credit_tightening"] = True
        bus.publish(msg)

        perceived = factory.perceive(bus)
        self.assertEqual(perceived.get("rate_direction"), "up")
        self.assertTrue(perceived.get("credit_tightening"))
        # 信贷收紧 → 工厂应切换到 defensive
        self.assertEqual(factory.goals.current_strategy, "defensive")

    def test_worker_perceives_warning(self):
        import random
        from agents.worker import Worker
        bus = MessageBus()
        w = Worker(0, random.Random(42))
        base_rate = w.savings_rate

        # 发布危机预警
        bus.publish(make_warning_alert(1, ["失业率过高"], severity="critical"))
        w.perceive(bus)

        self.assertTrue(w._crisis_mode)
        self.assertGreater(w.savings_rate, base_rate)

    def test_worker_recovers_from_crisis(self):
        import random
        from agents.worker import Worker
        bus = MessageBus()
        w = Worker(0, random.Random(42))

        # 危机 → 储蓄率提升
        bus.publish(make_warning_alert(1, ["失业率过高"], severity="critical"))
        w.perceive(bus)
        crisis_rate = w.savings_rate

        # 好转（无新预警）
        bus2 = MessageBus()
        w.perceive(bus2)
        self.assertFalse(w._crisis_mode)
        self.assertLess(w.savings_rate, crisis_rate)


if __name__ == "__main__":
    unittest.main()
