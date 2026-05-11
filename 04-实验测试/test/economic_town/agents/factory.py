"""
工厂主 Agent —— 借贷、雇工、生产、销售（感知-策略-行动循环）

架构：
  感知层  →  读取经济阶段、银行利率方向、信贷政策
  规则层  →  策略选择（aggressive/normal/defensive）+ 防御陷阱逃脱机制
             ① 防御陷阱逃脱：连续 N 月 defensive 且外部环境改善则主动松绑
             ② 银行信贷放松信号：可提高借贷目标
  LLM层   →  每季度策略复盘，解析建议后反馈到下一轮策略选择（闭环）
  行动层  →  发布信用评分给银行

长远目标（FactoryGoals）：
  - 目标净利润率 >= 5%
  - 最低现金储备 >= 300
  - 杠杆上限 <= 2.0（动态调整）
  - 扩张门槛：利润率 > 10%
  - 收缩触发：利润率 < -5%
"""
from __future__ import annotations
import math
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from agents.bank import Bank
    from agents.worker import Worker
    from agents.external_market import ExternalMarket
    from core.message_bus import MessageBus

from config.params import FACTORY_BASE_PRICE, OLLAMA_MODEL
from core.goals import FactoryGoals
from core.messages import make_credit_score, TOPIC_ECONOMIC_REPORT, TOPIC_RATE_ANNOUNCEMENT


class FactoryOwner:
    """
    输入（感知）：
      - TOPIC_ECONOMIC_REPORT：经济阶段、综合风险、工厂建议
      - TOPIC_RATE_ANNOUNCEMENT：利率方向、是否收紧/放松信贷

    输出（行动）：
      - TOPIC_CREDIT_SCORE：本工厂信用评分（银行参考）
      - 借贷目标、雇工预算、定价（影响银行贷款和劳动力市场）
    """

    def __init__(self, factory_id: int, config: dict):
        self.id            = factory_id
        self.name          = config["name"]
        self.tech_factor   = config["tech_factor"]
        self.capital_alpha = config["capital_alpha"]
        self.labor_beta    = config["labor_beta"]
        self.cash          = config["initial_capital"]

        self.loan_amount: float = 0.0
        self.workers: list["Worker"] = []
        self.production: float = 0.0
        self.revenue: float = 0.0
        self.wage_bill: float = 0.0
        self.monthly_profit: float = 0.0
        self.is_bankrupt: bool = False

        self.price: float = FACTORY_BASE_PRICE
        self.history: list[dict] = []
        self.goals: FactoryGoals = FactoryGoals()

        # 感知状态
        self._perceived: dict = {}

        # 策略持续追踪（防御陷阱逃脱机制）
        self._months_in_strategy: int = 0
        self._prev_strategy: str = "normal"

        # LLM 反馈（上一轮建议，下一轮策略使用）
        self._llm_strategy_hint: Optional[str] = None   # "aggressive"/"normal"/"defensive"
        self._llm_hint_used: bool = False               # 用过一次后清空
        self._last_llm_month: int = 0

        self._llm_strategy_note: str = ""

    # ═══════════════════════════════════════════════════════════
    # 感知层
    # ═══════════════════════════════════════════════════════════

    def perceive(self, bus: "MessageBus") -> dict:
        """
        读取经济形势和银行利率信号，更新策略状态。

        新增逻辑：
          - 银行放松信贷（loosen_credit=True）→ 可适当增加借贷
          - 综合多信号才切换到 aggressive，防止误判
        """
        perceived: dict = {}

        econ_msg = bus.get_latest(TOPIC_ECONOMIC_REPORT)
        if econ_msg:
            p = econ_msg.payload
            perceived["phase"]           = p.get("phase", "")
            perceived["risk_total"]      = p.get("risk_total", 0.0)
            perceived["factory_advice"]  = p.get("factory_advice", "")
            perceived["warnings"]        = p.get("warnings", [])

        rate_msg = bus.get_latest(TOPIC_RATE_ANNOUNCEMENT)
        if rate_msg:
            p = rate_msg.payload
            perceived["loan_rate"]         = p.get("loan_rate", 0.05)
            perceived["credit_tightening"] = p.get("credit_tightening", False)
            perceived["loosen_credit"]     = p.get("loosen_credit", False)
            perceived["rate_direction"]    = p.get("rate_direction", "hold")
            perceived["risk_appetite"]     = p.get("risk_appetite", 0.5)

        self._perceived = perceived
        self._update_strategy()
        return perceived

    # ═══════════════════════════════════════════════════════════
    # 规则决策层：策略选择（含陷阱逃脱 + LLM 闭环）
    # ═══════════════════════════════════════════════════════════

    def _update_strategy(self) -> None:
        """
        策略选择逻辑（优先级从高到低）：

        1. 硬性防御条件（立即切换 defensive，无论 LLM 怎么说）
        2. 防御陷阱逃脱（久守不攻，主动松绑）
        3. LLM 建议（在安全范围内采纳）
        4. 扩张条件
        5. 默认维持 normal
        """
        p          = self._perceived
        phase      = p.get("phase", "")
        risk_total = p.get("risk_total", 30.0)
        tighten    = p.get("credit_tightening", False)
        loosen     = p.get("loosen_credit", False)
        rate_dir   = p.get("rate_direction", "hold")

        # 近期财务状况
        recent     = self.history[-3:] if self.history else []
        avg_profit = sum(h.get("profit", 0) for h in recent) / max(len(recent), 1)
        avg_rev    = sum(h.get("revenue", 1) for h in recent) / max(len(recent), 1)
        profit_margin = avg_profit / max(avg_rev, 1)

        # ── 追踪策略持续时长 ──────────────────────────────────
        cur = self.goals.current_strategy
        if cur == self._prev_strategy:
            self._months_in_strategy += 1
        else:
            self._months_in_strategy = 1
            self._prev_strategy = cur

        # ── 1. 硬性防御条件 ───────────────────────────────────
        # 满足任意一条：立刻进入 defensive，LLM 无法覆盖
        hard_defensive = (
            phase in ("危机", "衰退")
            or risk_total > 70
            or (tighten and self.cash < self.goals.min_cash_reserve * 2)
            or profit_margin < self.goals.contraction_trigger
            or self.cash < self.goals.min_cash_reserve
        )
        if hard_defensive:
            self.goals.current_strategy = "defensive"
            self.goals.max_loan_to_cash_ratio = max(0.5, self.goals.max_loan_to_cash_ratio - 0.15)
            self._llm_hint_used = True   # 危机时忽略 LLM 建议
            return

        # ── 2. 防御陷阱逃脱机制 ─────────────────────────────────
        # 在 defensive 超过 5 个月，且外部环境已明显改善 → 主动松绑到 normal
        # 这解决"一旦进入 defensive 就永远出不来"的问题
        if (
            self.goals.current_strategy == "defensive"
            and self._months_in_strategy >= 5
            and phase in ("触底", "复苏", "稳态", "扩张")
            and risk_total < 55
            and not tighten
        ):
            self.goals.current_strategy = "normal"
            self.goals.max_loan_to_cash_ratio = 1.5
            self._months_in_strategy = 0
            return

        # ── 3. LLM 建议（安全范围内采纳，一次性）──────────────
        if self._llm_strategy_hint and not self._llm_hint_used:
            hint = self._llm_strategy_hint
            safe_to_apply = (
                risk_total < 60
                and not tighten
                and phase not in ("危机", "衰退")
            )
            if safe_to_apply:
                if hint == "normal" and self.goals.current_strategy == "defensive":
                    self.goals.current_strategy = "normal"
                    self.goals.max_loan_to_cash_ratio = 1.5
                    self._llm_hint_used = True
                    return
                elif hint == "aggressive" and self.goals.current_strategy in ("normal", "defensive"):
                    # LLM 建议激进，但还需要看是否利润支持
                    if profit_margin > 0.03:
                        self.goals.current_strategy = "aggressive"
                        self._llm_hint_used = True
                        return
            self._llm_hint_used = True  # 不安全时也消耗掉，避免堆积

        # ── 4. 扩张条件（全部满足才进入 aggressive）──────────────
        if (
            phase in ("扩张", "复苏")
            and risk_total < 40
            and not tighten
            and (loosen or rate_dir in ("hold", "down"))
            and profit_margin > self.goals.expansion_profit_threshold
        ):
            self.goals.current_strategy = "aggressive"
            self.goals.max_loan_to_cash_ratio = min(2.5, self.goals.max_loan_to_cash_ratio + 0.1)
            return

        # ── 5. 一般收缩判断 ─────────────────────────────────────
        if (tighten and not loosen) or risk_total > 55:
            self.goals.current_strategy = "defensive"
            self.goals.max_loan_to_cash_ratio = max(1.0, self.goals.max_loan_to_cash_ratio - 0.1)
            return

        # ── 6. 默认：维持/恢复 normal ────────────────────────────
        self.goals.current_strategy = "normal"
        self.goals.max_loan_to_cash_ratio = max(1.5, min(2.0, self.goals.max_loan_to_cash_ratio))

    # ═══════════════════════════════════════════════════════════
    # LLM 辅助层（闭环）
    # ═══════════════════════════════════════════════════════════

    def should_trigger_llm(self, month: int) -> bool:
        return month - self._last_llm_month >= 3 and len(self.history) >= 3

    def llm_strategy_review(self, month: int) -> str:
        """
        季度策略复盘：请 LLM 评估当前策略并给出调整建议。
        输出将被 apply_llm_advice() 解析后用于下轮策略选择。
        """
        p = self._perceived
        recent = self.history[-3:]
        avg_profit  = sum(h.get("profit", 0) for h in recent) / max(len(recent), 1)
        avg_revenue = sum(h.get("revenue", 0) for h in recent) / max(len(recent), 1)
        avg_workers = sum(h.get("workers", 0) for h in recent) / max(len(recent), 1)
        avg_sold    = sum(h.get("sold_ratio", 0) for h in recent) / max(len(recent), 1)

        prompt = f"""你是{self.name}工厂的老板，请用120字以内做季度经营复盘并给出策略建议。

【工厂现状】
  现金: {self.cash:.0f}  当前策略: {self.goals.current_strategy}  连续此策略: {self._months_in_strategy}月
  近3月平均利润: {avg_profit:.0f}  平均营收: {avg_revenue:.0f}
  平均雇工: {avg_workers:.0f}人  平均销售率: {avg_sold*100:.0f}%

【外部环境】
  经济阶段: {p.get('phase','未知')}  综合风险: {p.get('risk_total',0):.0f}/100
  银行利率方向: {p.get('rate_direction','hold')}
  信贷收紧: {p.get('credit_tightening',False)}  信贷放松: {p.get('loosen_credit',False)}
  经济学家对工厂建议: {p.get('factory_advice','无')}

请给出：
①本季度最大挑战（一句话）
②下季度策略建议：aggressive（扩张借贷）/ normal（维持）/ defensive（收缩保守）
③理由（一句话）"""

        from analysis.llm_analyst import _ollama_chat
        text = _ollama_chat(prompt, model=OLLAMA_MODEL, timeout=45)
        self._llm_strategy_note = text
        self._last_llm_month = month
        return text

    def apply_llm_advice(self, text: str) -> None:
        """
        解析 LLM 策略建议，存为下一轮 _update_strategy() 的参考输入。
        形成 LLM→决策闭环。
        """
        text_lower = text.lower()
        hint = None

        # 按优先级检测策略关键词
        aggressive_kws = ["aggressive", "扩张借贷", "增加借贷", "扩大生产", "积极扩张", "提高借贷"]
        defensive_kws  = ["defensive", "收缩", "保守", "削减借贷", "减少借贷", "降低杠杆", "保存现金"]
        normal_kws     = ["normal", "维持", "保持稳定", "正常运营", "稳定经营", "维持现状"]

        if any(k in text for k in aggressive_kws):
            hint = "aggressive"
        elif any(k in text for k in defensive_kws):
            hint = "defensive"
        elif any(k in text for k in normal_kws):
            hint = "normal"

        if hint:
            self._llm_strategy_hint = hint
            self._llm_hint_used = False   # 新建议，标记为未使用

    # ═══════════════════════════════════════════════════════════
    # 行动层：发布信用评分
    # ═══════════════════════════════════════════════════════════

    def act(self, bus: "MessageBus") -> None:
        """向消息总线发布本工厂信用评分，银行据此调整贷款额度。"""
        if self.is_bankrupt:
            return

        cash_safety     = min(1.0, self.cash / max(self.goals.min_cash_reserve * 5, 1.0))
        recent_profits  = [h.get("profit", 0) for h in self.history[-3:]] if self.history else [0]
        profit_stable   = 1.0 if all(p > 0 for p in recent_profits) else (
                          0.5 if sum(1 for p in recent_profits if p > 0) >= 1 else 0.0)
        score           = round(0.5 * cash_safety + 0.5 * profit_stable, 3)

        avg_profit        = sum(recent_profits) / max(len(recent_profits), 1)
        repayment_history = "good" if score > 0.6 else ("fair" if score > 0.3 else "poor")

        bus.publish(make_credit_score(
            month=len(self.history),
            factory_id=self.id,
            score=score,
            history=repayment_history,
            avg_profit=avg_profit,
            requested=min(self.cash * self.goals.max_loan_to_cash_ratio, 4000.0),
        ))

    # ═══════════════════════════════════════════════════════════
    # 核心经济操作（策略驱动）
    # ═══════════════════════════════════════════════════════════

    def plan_and_borrow(self, bank: "Bank") -> float:
        """
        根据策略和银行信贷政策决定借贷规模。
        银行信贷放松时可提高借贷目标（实现多 Agent 协同）。
        """
        if self.is_bankrupt:
            return 0.0

        strategy = self.goals.current_strategy
        loosen   = self._perceived.get("loosen_credit", False)

        if not self.history:
            target_loan = min(self.cash * 1.0, 3000.0)
        elif strategy == "aggressive":
            target_loan = min(self.cash * self.goals.max_loan_to_cash_ratio, 4000.0)
        elif strategy == "defensive":
            # 若银行主动放松信贷，defensive 时也适度借贷（不为 0）
            base = max(300.0, self.cash * 0.3)
            target_loan = base * 1.5 if loosen else base
        else:  # normal
            last_profit = self.history[-1].get("profit", 0)
            if last_profit > 0:
                target_loan = min(self.cash * 1.2, 3500.0)
                if loosen:
                    target_loan = min(self.cash * 1.5, 4000.0)
            else:
                target_loan = max(500.0, self.cash * 0.5)

        approved = bank.grant_loan(self.id, target_loan)
        self.loan_amount = approved
        self.cash       += approved
        return approved

    def hire_workers(self, available_workers: list["Worker"]) -> list["Worker"]:
        """
        策略影响工资预算比例：
          aggressive → 70%   defensive → 40%   normal → 60%
        """
        if self.is_bankrupt:
            return []

        budget_ratio = {"aggressive": 0.70, "normal": 0.60, "defensive": 0.40}.get(
            self.goals.current_strategy, 0.60
        )
        wage_budget = self.cash * budget_ratio

        if available_workers:
            avg_res = sum(w.effective_reservation_wage for w in available_workers) / len(available_workers)
        else:
            avg_res = 100.0

        multiplier   = {"aggressive": 1.15, "normal": 1.10, "defensive": 1.02}.get(
            self.goals.current_strategy, 1.10
        )
        offered_wage = avg_res * multiplier
        max_workers  = max(1, int(wage_budget / max(offered_wage, 1.0)))

        candidates = sorted(available_workers, key=lambda w: -w.skill_level)
        hired = []
        for w in candidates[:max_workers]:
            if w.accept_job(self.id, offered_wage):
                hired.append(w)

        self.workers = hired
        return hired

    def produce(self) -> float:
        """柯布-道格拉斯生产函数：Q = A × K^α × L^β"""
        if self.is_bankrupt or not self.workers:
            self.production = 0.0
            return 0.0

        effective_capital = self.loan_amount + self.cash * 0.3
        effective_labor   = sum(w.skill_level for w in self.workers)

        self.production = (
            self.tech_factor
            * math.pow(max(effective_capital, 1.0), self.capital_alpha)
            * math.pow(max(effective_labor, 1.0), self.labor_beta)
        )
        return self.production

    def sell(self, market: "ExternalMarket") -> tuple[float, float]:
        """定价策略受运营策略影响"""
        if self.production <= 0:
            self.revenue = 0.0
            return 0.0, 0.0

        if self.history:
            last_sold = self.history[-1].get("sold_ratio", 1.0)
            strategy  = self.goals.current_strategy

            if strategy == "defensive":
                if last_sold < 0.85:
                    self.price = max(4.0, self.price * 0.92)   # 积极降价保销量
                elif last_sold > 0.98:
                    self.price = min(18.0, self.price * 1.01)
            elif strategy == "aggressive":
                if last_sold < 0.80:
                    self.price = max(5.0, self.price * 0.96)
                elif last_sold > 0.92:
                    self.price = min(22.0, self.price * 1.05)  # 大幅提价冲利润
            else:
                if last_sold < 0.80:
                    self.price = max(5.0, self.price * 0.95)
                elif last_sold > 0.95:
                    self.price = min(20.0, self.price * 1.03)

        self.revenue = market.sell(self.id, self.production, self.price)
        self.cash   += self.revenue
        sold_ratio   = self.revenue / (self.production * self.price) if self.production > 0 else 0.0
        return self.revenue, sold_ratio

    def pay_wages(self) -> float:
        self.wage_bill = sum(w.monthly_wage for w in self.workers)
        self.cash -= self.wage_bill
        return self.wage_bill

    def repay_loan(self, bank: "Bank") -> float:
        if self.loan_amount <= 0:
            return 0.0
        due       = self.loan_amount * (1 + bank.loan_rate)
        repayable = min(self.cash, due)
        actual    = bank.repay_loan(self.id, repayable)
        self.cash -= repayable

        if repayable < due * 0.5 and self.cash < 0:
            self.is_bankrupt = True

        self.loan_amount = 0.0
        return actual

    def monthly_settle(self, bank: "Bank", market: "ExternalMarket") -> dict:
        self.monthly_profit = self.revenue - self.wage_bill - (
            self.loan_amount * bank.loan_rate if self.loan_amount > 0 else 0
        )
        sold_ratio = (
            self.revenue / (self.production * self.price)
            if self.production > 0 and self.price > 0 else 0.0
        )
        snapshot = {
            "factory_id": self.id,
            "name":       self.name,
            "loan":       self.loan_amount,
            "workers":    len(self.workers),
            "production": self.production,
            "revenue":    self.revenue,
            "wage_bill":  self.wage_bill,
            "profit":     self.monthly_profit,
            "price":      self.price,
            "cash":       self.cash,
            "bankrupt":   self.is_bankrupt,
            "sold_ratio": sold_ratio,
            "strategy":   self.goals.current_strategy,
        }
        self.history.append(snapshot)
        self.workers   = []
        self.revenue   = 0.0
        self.wage_bill = 0.0
        return snapshot

    def __repr__(self) -> str:
        return (f"FactoryOwner(id={self.id}, name={self.name}, cash={self.cash:.1f}, "
                f"strategy={self.goals.current_strategy}[{self._months_in_strategy}m], "
                f"bankrupt={self.is_bankrupt})")
