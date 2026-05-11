"""
核心仿真循环 —— 月度步进，协调所有 Agent

每月执行顺序：
  ① Bank perceive→decide→act（利率公告）
  ② Factory perceive（感知利率/经济形势，更新策略）
  ③ Factory plan_and_borrow（按策略借贷）
  ④ 劳动力市场（工厂雇工）
  ⑤ 生产
  ⑥ 销售
  ⑦ 工资发放
  ⑧ Worker perceive（感知预警，调整储蓄率）
  ⑨ Worker monthly_step（储蓄/消费）
  ⑩ Factory repay→settle→act（发布信用评分）
  ⑪ Retailer settle
  ⑫ Bank settle
  ⑬ Stats 计算
  ⑭ 仿真发布劳动力市场信号
  ⑮ Economist perceive→observe→act（发布月度经济报告）
  ⑯ 按需触发 LLM（经济学家月报 / 工厂策略复盘 / 银行信贷政策）
"""
from __future__ import annotations
import random
from typing import Optional, Callable

from agents.bank import Bank
from agents.factory import FactoryOwner
from agents.worker import Worker
from agents.retailer import Retailer
from agents.external_market import ExternalMarket
from agents.economist import EconomistAgent
from core.message_bus import MessageBus
from core.messages import make_labor_market_signal
from core.termination import TerminationChecker, TerminationResult
from config.params import (
    NUM_FACTORIES, NUM_WORKERS, NUM_RETAILERS,
    FACTORY_CONFIGS, RANDOM_SEED, TERMINATION_MAX_MONTHS,
)


class TownEconomy:
    """封闭小镇经济体 —— 协调所有 Agent 的月度仿真循环"""

    def __init__(self, seed: int = RANDOM_SEED):
        self.rng   = random.Random(seed)
        self.month: int = 0

        # ── 初始化所有 Agent ──────────────────────────
        self.bank = Bank()
        self.factories: list[FactoryOwner] = [
            FactoryOwner(i, FACTORY_CONFIGS[i]) for i in range(NUM_FACTORIES)
        ]
        self.workers: list[Worker] = [
            Worker(i, random.Random(seed + i + 1)) for i in range(NUM_WORKERS)
        ]
        self.retailers: list[Retailer] = [
            Retailer(i) for i in range(NUM_RETAILERS)
        ]
        self.market    = ExternalMarket(factory_ids=list(range(NUM_FACTORIES)), seed=seed)
        self.economist = EconomistAgent()

        # ── 基础设施 ─────────────────────────────────
        self.bus        = MessageBus()
        self.terminator = TerminationChecker()

        # 工人初始存款存入银行
        for w in self.workers:
            self.bank.accept_deposit(w.savings)

        # 月度快照列表（供 EconomyStats 使用）
        self.monthly_snapshots: list[dict] = []

    def _retailer(self) -> Retailer:
        return self.retailers[0]

    # ═══════════════════════════════════════════════════════════
    # 单月步进
    # ═══════════════════════════════════════════════════════════

    def step(self) -> dict:
        """
        执行一个月的完整仿真，返回本月快照摘要。
        包含完整的多 Agent 感知-决策-行动循环。
        """
        self.month += 1
        retailer = self._retailer()
        active   = [f for f in self.factories if not f.is_bankrupt]

        # ── ① 银行：感知→决策→行动（设定本月利率）────
        self.bank.perceive(self.bus)
        intention = self.bank.decide()
        self.bank.act(intention, self.bus)

        # ── ② 工厂：感知（更新策略，不阻塞）──────────
        for factory in active:
            factory.perceive(self.bus)

        # ── ③ 工厂：申请贷款（受策略驱动）────────────
        for factory in active:
            factory.plan_and_borrow(self.bank)

        # ── ④ 劳动力市场：全部释放，重新匹配 ──────────
        for w in self.workers:
            w.lose_job()

        sorted_factories = sorted(active, key=lambda f: -f.tech_factor)
        available_workers = list(self.workers)
        for factory in sorted_factories:
            hired = factory.hire_workers(available_workers)
            for w in hired:
                available_workers.remove(w)

        # ── ⑤ 生产 ────────────────────────────────────
        for factory in active:
            factory.produce()

        # ── ⑥ 外部市场冲击 + 销售 ────────────────────
        self.market.step_shock()
        for factory in active:
            factory.sell(self.market)

        # ── ⑦ 工资发放 ───────────────────────────────
        for factory in active:
            factory.pay_wages()

        # ── ⑧ 工人：感知（调整储蓄率）────────────────
        for w in self.workers:
            w.perceive(self.bus)

        # ── ⑨ 工人：月度收支 ──────────────────────────
        worker_snapshots = []
        for w in self.workers:
            snap = w.monthly_step(self.bank, retailer)
            worker_snapshots.append(snap)

        # ── ⑩ 工厂：还贷→结算→发布信用评分 ──────────
        factory_snapshots = []
        for factory in active:
            factory.repay_loan(self.bank)
            snap = factory.monthly_settle(self.bank, self.market)
            factory_snapshots.append(snap)
            factory.act(self.bus)   # 发布信用评分

        # ── ⑪ 零售商结算 ─────────────────────────────
        retailer_snap = retailer.monthly_settle(self.bank)

        # ── ⑫ 银行月末结算 ───────────────────────────
        bank_snap = self.bank.monthly_settle()

        # ── ⑬ 汇总快照 ───────────────────────────────
        employed_count = sum(1 for w in self.workers if w.is_employed)
        monthly = {
            "month":            self.month,
            "bank":             bank_snap,
            "factories":        factory_snapshots,
            "workers":          worker_snapshots,
            "retailer":         retailer_snap,
            "active_factories": len(active),
        }
        self.monthly_snapshots.append(monthly)

        # ── ⑭ 仿真发布劳动力市场信号 ─────────────────
        jobs_available  = sum(f.history[-1].get("workers", 0) if f.history else 0 for f in active)
        total_employed  = employed_count
        offered_wages   = [w.monthly_wage for w in self.workers if w.is_employed]
        avg_wage        = sum(offered_wages) / max(len(offered_wages), 1)
        unemp_rate      = 1.0 - total_employed / max(len(self.workers), 1)
        workers_seeking = len(self.workers) - total_employed

        self.bus.publish(make_labor_market_signal(
            month=self.month,
            unemployment_rate=unemp_rate,
            avg_wage=avg_wage,
            jobs=total_employed,
            seeking=workers_seeking,
        ))

        return monthly

    # ═══════════════════════════════════════════════════════════
    # 经济学家循环（独立于 step，由外层调用）
    # ═══════════════════════════════════════════════════════════

    def run_economist(self, metrics: dict) -> "EconomicDiagnosis":
        """
        ⑮ 经济学家：感知→规则诊断→发布报告
        由外层（main.py / run_until_termination）在 stats.update() 后调用。
        """
        # 感知：读取劳动力市场信号（补充 metrics 之外的信息）
        self.economist.perceive(self.bus)
        # 规则诊断
        diag = self.economist.observe(metrics)
        # 行动：发布经济报告 + 预警到消息总线
        self.economist.act(diag, self.bus)
        return diag

    # ═══════════════════════════════════════════════════════════
    # 固定月数运行（兼容旧接口）
    # ═══════════════════════════════════════════════════════════

    def run(self, months: int, on_step: Optional[Callable] = None) -> list[dict]:
        """运行 N 个月仿真（旧接口，不触发终止条件）"""
        for _ in range(months):
            snap = self.step()
            if on_step:
                on_step(self.month, snap)
        return self.monthly_snapshots

    # ═══════════════════════════════════════════════════════════
    # 自主运行（while True 直到崩溃）
    # ═══════════════════════════════════════════════════════════

    def run_until_termination(
        self,
        stats,                               # EconomyStats 实例
        on_step: Optional[Callable] = None,  # 每月回调 (month, snapshot, diag)
        use_llm: bool = True,
        llm_analyst=None,                    # LLMAnalyst 实例（可选）
    ) -> TerminationResult:
        """
        核心自主循环：while True，直到满足终止条件。

        流程（每月）：
          1. step()          ← 所有 Agent 的感知-决策-行动
          2. stats.update()  ← 统计指标
          3. run_economist() ← 经济学家诊断 + 发布报告
          4. LLM 触发判断    ← 经济学家 / 工厂 / 银行
          5. 终止检查        ← 三大条件
          6. 回调 on_step
        """
        from core.termination import TerminationResult

        while True:
            # ── 1. 单月仿真步进 ──────────────────────
            snapshot = self.step()
            month    = self.month

            # ── 2. 统计指标 ──────────────────────────
            metrics = stats.update(snapshot)

            # ── 3. 经济学家诊断 + 发布到总线 ──────────
            diag = self.run_economist(metrics)

            # ── 4. LLM 触发逻辑 + 反馈闭环 ─────────────────
            llm_outputs = {}

            if use_llm:
                # 经济学家：每3月或危机时触发叙述（叙述写入 diag.llm_conclusion）
                if self.economist.should_trigger_llm(month):
                    llm_outputs["economist"] = self.economist.conclude(diag)

                # 银行：存款负担或坏账危机时触发（每3月一次，避免过频）
                recent_bank_profit = (
                    sum(h.get("monthly_profit", 0) for h in self.bank.history[-3:]) / 3
                    if len(self.bank.history) >= 3 else 0.0
                )
                bank_needs_llm = (
                    self.bank._perceived.get("warning_severity") == "critical"
                    or recent_bank_profit < -200
                )
                if bank_needs_llm and month % 3 == 0:
                    bank_llm = self.bank.llm_credit_policy()
                    llm_outputs["bank"] = bank_llm
                    # ★ 闭环：解析 LLM 建议 → 影响银行下一轮 decide()
                    self.bank.apply_llm_advice(bank_llm)

                # 工厂：每季度策略复盘（每3月）
                for factory in self.factories:
                    if not factory.is_bankrupt and factory.should_trigger_llm(month):
                        factory_llm = factory.llm_strategy_review(month)
                        llm_outputs[f"factory_{factory.id}"] = factory_llm
                        # ★ 闭环：解析 LLM 建议 → 影响工厂下一轮 _update_strategy()
                        factory.apply_llm_advice(factory_llm)

                # LLMAnalyst 年报
                if llm_analyst and llm_analyst.should_run_annual(month):
                    llm_outputs["annual"] = llm_analyst.annual_report(month)

            snapshot["llm_outputs"] = llm_outputs

            # ── 5. 终止条件检查 ──────────────────────
            result = self.terminator.check(self)
            if result:
                if on_step:
                    on_step(month, snapshot, diag)
                return result

            # 超过最长运行月数也终止
            if month >= TERMINATION_MAX_MONTHS:
                if on_step:
                    on_step(month, snapshot, diag)
                return TerminationResult(
                    reason="max_months",
                    description=f"第{month}月：达到最长运行月数 {TERMINATION_MAX_MONTHS}，仿真结束",
                    month=month,
                )

            # ── 6. 回调 ──────────────────────────────
            if on_step:
                on_step(month, snapshot, diag)

    # ═══════════════════════════════════════════════════════════
    # 辅助
    # ═══════════════════════════════════════════════════════════

    def status_summary(self) -> str:
        employed = sum(1 for w in self.workers if w.is_employed)
        active   = sum(1 for f in self.factories if not f.is_bankrupt)
        return (
            f"月份={self.month} | 在职={employed}/{len(self.workers)} | "
            f"活跃工厂={active}/{len(self.factories)} | "
            f"银行存款={self.bank.deposits:.0f} | "
            f"贷款利率={self.bank.loan_rate:.3f}"
        )
