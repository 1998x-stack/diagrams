"""本地零售商 Agent —— 工人本地消费的中转节点"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.bank import Bank

from config.params import RETAILER_MARKUP_RATE


class Retailer:
    def __init__(self, retailer_id: int):
        self.id = retailer_id
        self.monthly_revenue: float = 0.0   # 当月收到工人消费额
        self.monthly_profit: float = 0.0
        self.cash: float = 0.0              # 留存现金
        self.history: list[dict] = []

    def receive_spending(self, amount: float) -> None:
        """接收工人消费支出"""
        self.monthly_revenue += amount

    def monthly_settle(self, bank: "Bank") -> dict:
        """
        月末结算：
        - 利润 = 收入 × markup_rate（留在镇内）
        - 进货成本 = 收入 × (1 - markup_rate)（流出镇外，购买外部商品）
        - 利润存入银行
        """
        profit = self.monthly_revenue * RETAILER_MARKUP_RATE
        import_cost = self.monthly_revenue * (1 - RETAILER_MARKUP_RATE)

        self.monthly_profit = profit
        self.cash += profit
        bank.accept_deposit(profit)  # 零售商利润存银行

        snapshot = {
            "retailer_id": self.id,
            "revenue": self.monthly_revenue,
            "profit": profit,
            "import_cost": import_cost,  # 流出镇外
        }
        self.history.append(snapshot)

        # 重置月度收入
        self.monthly_revenue = 0.0
        return snapshot

    def __repr__(self) -> str:
        return f"Retailer(id={self.id}, cash={self.cash:.1f})"
