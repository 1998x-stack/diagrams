"""终止条件检查器 —— 判断经济体是否已无法自我维持"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.simulation import TownEconomy

from config.params import (
    TERMINATION_BANK_CAPITAL_MIN,
    TERMINATION_CHRONIC_UNEMPLOYMENT_RATE,
    TERMINATION_CHRONIC_UNEMPLOYMENT_MONTHS,
)


@dataclass
class TerminationResult:
    reason: str         # bank_bankrupt | all_factories_bankrupt | chronic_unemployment | max_months
    description: str
    month: int


class TerminationChecker:
    """
    每月末调用 check()，满足任一终止条件则返回 TerminationResult，否则返回 None。

    三大终止条件：
    1. 银行资本金低于下限（资不抵债）
    2. 所有工厂全部破产
    3. 失业率连续 N 个月超过阈值（社会无法自我修复）
    """

    def __init__(self):
        self._high_unemployment_streak: int = 0

    def check(self, economy: "TownEconomy") -> Optional[TerminationResult]:
        month = economy.month
        bank = economy.bank
        factories = economy.factories
        workers = economy.workers

        # ── 条件 1：银行破产 ──────────────────────────────
        if bank.capital < TERMINATION_BANK_CAPITAL_MIN:
            return TerminationResult(
                reason="bank_bankrupt",
                description=(
                    f"第{month}月：银行资本金 {bank.capital:.0f} < "
                    f"破产线 {TERMINATION_BANK_CAPITAL_MIN}，系统性金融崩溃"
                ),
                month=month,
            )

        # ── 条件 2：全厂倒闭 ──────────────────────────────
        active = sum(1 for f in factories if not f.is_bankrupt)
        if active == 0:
            return TerminationResult(
                reason="all_factories_bankrupt",
                description=(
                    f"第{month}月：全部 {len(factories)} 家工厂破产，"
                    f"实体经济彻底崩溃"
                ),
                month=month,
            )

        # ── 条件 3：长期高失业 ────────────────────────────
        employed = sum(1 for w in workers if w.is_employed)
        unemp_rate = 1.0 - employed / max(len(workers), 1)

        if unemp_rate >= TERMINATION_CHRONIC_UNEMPLOYMENT_RATE:
            self._high_unemployment_streak += 1
        else:
            self._high_unemployment_streak = 0

        if self._high_unemployment_streak >= TERMINATION_CHRONIC_UNEMPLOYMENT_MONTHS:
            return TerminationResult(
                reason="chronic_high_unemployment",
                description=(
                    f"第{month}月：失业率连续 {self._high_unemployment_streak} 个月 "
                    f">= {TERMINATION_CHRONIC_UNEMPLOYMENT_RATE*100:.0f}%"
                    f"（当前 {unemp_rate*100:.1f}%），经济无法自我修复"
                ),
                month=month,
            )

        return None

    @property
    def unemployment_streak(self) -> int:
        return self._high_unemployment_streak
