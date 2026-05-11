"""
工人 Agent —— 就业、收入、储蓄、消费（感知驱动行为调整）

架构：
  感知层  →  读取经济预警和阶段，调整储蓄率和心理工资预期
  规则层  →  基于就业状况 + 经济形势 + 目标做出储蓄/消费决策
  （无 LLM，工人决策简单，规则足够描述异质性行为）

长远目标（WorkerGoals）：
  - 目标存款 = 3 个月工资
  - 最低心理工资 = 初始值 × 50%（最大折扣）
  - 危机时储蓄率额外提升 15%
"""
from __future__ import annotations
import random
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from agents.bank import Bank
    from agents.retailer import Retailer
    from core.message_bus import MessageBus

from config.params import (
    WORKER_SKILL_RANGE, WORKER_SAVINGS_RATE_RANGE,
    WORKER_RESERVATION_WAGE_RANGE, WORKER_LOCAL_SPEND_RATIO_RANGE,
    WORKER_INITIAL_SAVINGS,
)
from core.goals import WorkerGoals
from core.messages import TOPIC_WARNING_ALERT, TOPIC_ECONOMIC_REPORT


class Worker:
    """
    输入（感知）：
      - TOPIC_WARNING_ALERT：预警信息（触发危机储蓄模式）
      - TOPIC_ECONOMIC_REPORT：经济阶段（调整消费/储蓄行为）

    输出：
      - 向 Bank 存款、向 Retailer 消费（直接方法调用）
      - 通过就业接受行为影响劳动力市场供需
    """

    def __init__(self, worker_id: int, rng: random.Random):
        self.id = worker_id

        # 异质性属性（初始化时随机确定，终身稳定）
        self.skill_level:       float = rng.uniform(*WORKER_SKILL_RANGE)
        self._base_savings_rate: float = rng.uniform(*WORKER_SAVINGS_RATE_RANGE)
        self.savings_rate:      float = self._base_savings_rate
        self.reservation_wage:  float = rng.uniform(*WORKER_RESERVATION_WAGE_RANGE)
        self.local_spend_ratio: float = rng.uniform(*WORKER_LOCAL_SPEND_RATIO_RANGE)

        # 就业状态
        self.employer_id: Optional[int] = None
        self.monthly_wage: float = 0.0
        self.months_unemployed: int = 0

        # 财富状态
        self.savings: float = WORKER_INITIAL_SAVINGS
        self.cumulative_income: float = 0.0

        self.history: list[dict] = []
        self.goals: WorkerGoals = WorkerGoals()
        self._crisis_mode: bool = False   # 危机节约模式

    @property
    def is_employed(self) -> bool:
        return self.employer_id is not None

    @property
    def effective_reservation_wage(self) -> float:
        """
        失业越久，心理工资预期越低（理性妥协）。
        每月降低 2%，最低降到初始值的 goals.min_reservation_wage_ratio。
        """
        min_ratio = self.goals.min_reservation_wage_ratio
        discount  = max(min_ratio, 1.0 - 0.02 * self.months_unemployed)
        return self.reservation_wage * discount

    # ═══════════════════════════════════════════════════════════
    # 感知层
    # ═══════════════════════════════════════════════════════════

    def perceive(self, bus: "MessageBus") -> None:
        """
        读取经济预警和经济阶段，调整储蓄行为。

        危机模式（保守）：提升储蓄率 + 减少消费
        正常模式（恢复）：储蓄率逐步回归基准水平
        """
        econ_msg = bus.get_latest(TOPIC_ECONOMIC_REPORT)
        warn_msg = bus.get_latest(TOPIC_WARNING_ALERT)

        in_crisis = False
        if warn_msg and warn_msg.payload.get("severity") in ("critical", "warning"):
            in_crisis = True
        if econ_msg and econ_msg.payload.get("phase") in ("危机", "衰退", "收缩"):
            in_crisis = True

        self._crisis_mode = in_crisis

        if in_crisis:
            # 危机期：储蓄率提升，最高 70%
            boosted = min(0.70, self._base_savings_rate + self.goals.crisis_savings_rate_boost)
            self.savings_rate = boosted
        else:
            # 好转期：储蓄率逐步回归基准（每月恢复 2pp）
            recovered = max(self._base_savings_rate, self.savings_rate - 0.02)
            self.savings_rate = recovered

    # ═══════════════════════════════════════════════════════════
    # 就业操作
    # ═══════════════════════════════════════════════════════════

    def accept_job(self, factory_id: int, wage: float) -> bool:
        """接受工作邀约，当出价 >= 心理工资时接受"""
        if wage >= self.effective_reservation_wage:
            self.employer_id   = factory_id
            self.monthly_wage  = wage
            self.months_unemployed = 0
            return True
        return False

    def lose_job(self) -> None:
        self.employer_id  = None
        self.monthly_wage = 0.0

    # ═══════════════════════════════════════════════════════════
    # 月度收支（规则层核心）
    # ═══════════════════════════════════════════════════════════

    def monthly_step(self, bank: "Bank", retailer: "Retailer") -> dict:
        """
        执行一个月的收入/储蓄/消费决策。

        决策逻辑：
          - 就业 → 工资收入 × 储蓄率 存入银行，其余消费
          - 失业 → 无收入，月末更新失业计数器
          - 消费按 local_spend_ratio 拆分本地/外地
        """
        income = self.monthly_wage

        if not self.is_employed:
            self.months_unemployed += 1
            income = 0.0

        self.cumulative_income += income

        # 储蓄与消费（受 crisis_mode 影响的储蓄率）
        save_amount  = income * self.savings_rate
        spend_amount = income * (1.0 - self.savings_rate)

        # 危机模式：本地消费比例提升（更依赖本地，减少外地支出）
        if self._crisis_mode:
            local_ratio = min(0.9, self.local_spend_ratio + 0.1)
        else:
            local_ratio = self.local_spend_ratio

        local_spend    = spend_amount * local_ratio
        external_spend = spend_amount * (1.0 - local_ratio)

        # 操作
        if save_amount > 0:
            bank.accept_deposit(save_amount)
            self.savings += save_amount

        if local_spend > 0:
            retailer.receive_spending(local_spend)

        snapshot = {
            "worker_id":     self.id,
            "employed":      self.is_employed,
            "wage":          income,
            "savings":       self.savings,
            "savings_rate":  self.savings_rate,
            "local_spend":   local_spend,
            "external_spend": external_spend,
            "crisis_mode":   self._crisis_mode,
        }
        self.history.append(snapshot)
        return snapshot

    def __repr__(self) -> str:
        status = f"employed@factory{self.employer_id}" if self.is_employed else f"unemployed({self.months_unemployed}m)"
        return f"Worker(id={self.id}, skill={self.skill_level:.2f}, {status}, savings={self.savings:.0f})"
