"""外部市场 —— 需求曲线 + 随机冲击（虚拟节点，非 Agent）"""
from __future__ import annotations
import random
import math
from config.params import (
    EXTERNAL_BASE_DEMAND, EXTERNAL_PRICE_ELASTICITY,
    EXTERNAL_DEMAND_VOLATILITY, FACTORY_BASE_PRICE,
)


class ExternalMarket:
    """
    每个工厂对应一条独立需求曲线（差异化产品）。
    需求量 Q = Q_base * (P_base / P)^ε * shock
    shock 随机游走，模拟外部经济周期。
    """

    def __init__(self, factory_ids: list[int], seed: int = 42):
        self.rng = random.Random(seed)
        self.factory_ids = factory_ids
        # 每个工厂的基准需求（略有差异）
        self.base_demand: dict[int, float] = {
            fid: EXTERNAL_BASE_DEMAND * self.rng.uniform(0.8, 1.2)
            for fid in factory_ids
        }
        # 当前需求冲击系数（从1.0开始随机游走）
        self.shock: dict[int, float] = {fid: 1.0 for fid in factory_ids}

    def step_shock(self) -> None:
        """每月更新需求冲击（均值回归随机游走）"""
        for fid in self.factory_ids:
            delta = self.rng.gauss(0, EXTERNAL_DEMAND_VOLATILITY)
            # 均值回归：偏离1.0越远，拉力越强
            reversion = 0.1 * (1.0 - self.shock[fid])
            self.shock[fid] = max(0.2, self.shock[fid] + delta + reversion)

    def get_demand(self, factory_id: int, price: float) -> float:
        """
        给定工厂 id 和定价，返回外部市场需求量。
        price 必须 > 0。
        """
        if price <= 0:
            return 0.0
        q_base = self.base_demand[factory_id]
        elasticity = EXTERNAL_PRICE_ELASTICITY
        p_base = FACTORY_BASE_PRICE
        shock = self.shock[factory_id]
        demand = q_base * math.pow(p_base / price, elasticity) * shock
        return max(0.0, demand)

    def sell(self, factory_id: int, quantity: float, price: float) -> float:
        """
        工厂以 price 卖出 quantity 单位，返回实际销售收入。
        实际销量 = min(quantity, 市场需求量)
        """
        demand = self.get_demand(factory_id, price)
        actual_qty = min(quantity, demand)
        return actual_qty * price
