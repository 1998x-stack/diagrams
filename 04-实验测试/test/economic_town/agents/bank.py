"""
银行 Agent —— 存款、贷款、利率调整（感知-决策-行动循环）

架构：
  感知层  →  读取经济学家报告、预警、工厂信用评分（多信源）
  规则层  →  区分两种亏损类型并分别应对（核心逻辑升级）
             ① 存款负担型：流动性充裕但利息支出拖垮资本 → 主动降低存款利率
             ② 坏账危机型：贷款违约导致资本损失 → 收紧信贷 + 拉高贷款利率
  LLM层   →  危机时请求 LLM 给出信贷政策建议，解析后反馈到下一轮决策（闭环）
  行动层  →  调整存贷款利率，发布利率公告

长远目标（BankGoals）：
  - 资本充足率 >= 12%
  - 坏账率 < 15%
  - 利差 >= 2%
  - 风险偏好动态调整

决策权重：
  规则自诊断   55%（含存款负担 / 坏账危机区分）
  经济学家建议 35%
  LLM反馈      10%（上一轮 LLM 建议解析后应用）
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.message_bus import MessageBus

from config.params import (
    BANK_INITIAL_CAPITAL, BANK_DEPOSIT_RATE, BANK_LOAN_RATE,
    BANK_RESERVE_RATIO, BANK_MAX_LOAN_PER_FACTORY, OLLAMA_MODEL,
)
from core.goals import BankGoals
from core.messages import (
    make_rate_announcement,
    TOPIC_ECONOMIC_REPORT, TOPIC_WARNING_ALERT, TOPIC_CREDIT_SCORE,
)


@dataclass
class LoanRecord:
    factory_id: int
    principal: float
    monthly_rate: float
    months_remaining: int
    is_default: bool = False


class Bank:
    """
    输入（感知）：
      - TOPIC_ECONOMIC_REPORT：经济阶段、风险评分、建议利率变化
      - TOPIC_WARNING_ALERT：预警级别
      - TOPIC_CREDIT_SCORE：各工厂信用评分

    输出（行动）：
      - TOPIC_RATE_ANNOUNCEMENT：存贷款利率 + 信贷收紧标志
      - grant_loan() 依据信用评分动态调整额度
    """

    def __init__(self):
        self.capital: float = BANK_INITIAL_CAPITAL
        self.deposits: float = 0.0
        self.loans: dict[int, LoanRecord] = {}
        self.deposit_rate: float = BANK_DEPOSIT_RATE
        self.loan_rate: float = BANK_LOAN_RATE
        self.bad_debt: float = 0.0
        self.monthly_profit: float = 0.0
        self.history: list[dict] = []
        self.goals: BankGoals = BankGoals()

        # 感知状态
        self._perceived: dict = {}
        self._factory_credit: dict[int, float] = {}
        self._tighten_credit: bool = False

        # LLM 反馈信号（上一轮 LLM 建议解析结果，下一轮 decide 使用）
        self._llm_rate_delta: float = 0.0    # LLM 建议的利率调整方向
        self._llm_tighten: Optional[bool] = None  # LLM 建议是否收紧信贷

    # ═══════════════════════════════════════════════════════════
    # 感知层
    # ═══════════════════════════════════════════════════════════

    def perceive(self, bus: "MessageBus") -> dict:
        """
        从消息总线读取多信源信息。

        信源1：经济学家报告（阶段、风险、利率建议）
        信源2：经济预警（严重程度）
        信源3：工厂信用评分（贷款风险评估）
        """
        perceived: dict = {}

        econ_msg = bus.get_latest(TOPIC_ECONOMIC_REPORT)
        if econ_msg:
            p = econ_msg.payload
            perceived["phase"]             = p.get("phase", "")
            perceived["risk_total"]        = p.get("risk_total", 0.0)
            perceived["risk_financial"]    = p.get("risk_financial", 0.0)
            perceived["econ_rate_delta"]   = p.get("recommended_loan_rate_delta", 0.0)
            perceived["credit_tightening"] = p.get("credit_tightening", False)
            perceived["bank_advice"]       = p.get("bank_advice", "")

        warn_msg = bus.get_latest(TOPIC_WARNING_ALERT)
        if warn_msg:
            perceived["warning_severity"] = warn_msg.payload.get("severity", "")
            perceived["warnings"]         = warn_msg.payload.get("warnings", [])

        credit_scores: dict[int, float] = {}
        for msg in bus.get_history(TOPIC_CREDIT_SCORE, n=15):
            fid   = msg.payload.get("factory_id")
            score = msg.payload.get("credit_score", 0.5)
            if fid is not None:
                credit_scores[fid] = score
        perceived["factory_credit_scores"] = credit_scores

        self._perceived = perceived
        self._factory_credit = credit_scores
        return perceived

    # ═══════════════════════════════════════════════════════════
    # 规则决策层（核心逻辑）
    # ═══════════════════════════════════════════════════════════

    def decide(self) -> dict:
        """
        区分两种危机类型并分别应对，避免"一刀切"加息。

        ─── 存款负担型（Deposit Burden）───────────────────────
          症状：流动性极充裕（存款远超贷款）+ 无坏账 + 月利润为负
          原因：工厂不借贷，银行无利息收入，但存款利息支出不断累积
          应对：主动大幅降低存款利率，鼓励信贷（降低贷款门槛）
          ⚠ 不能在此时加息（会进一步抑制借贷，恶化亏损）

        ─── 坏账危机型（Bad Debt Crisis）───────────────────────
          症状：坏账率高 + 资本金迅速下降
          应对：收紧信贷审核，拉高贷款利率，请求 LLM 政策建议

        决策权重：规则55% + 经济学家35% + LLM反馈10%
        """
        p = self._perceived
        intention: dict = {
            "rate_delta":          0.0,
            "deposit_rate_delta":  0.0,   # 单独控制存款利率（存款负担场景）
            "tighten_credit":      False,
            "loosen_credit":       False,
            "llm_needed":          False,
        }

        total_loans      = sum(r.principal for r in self.loans.values())
        loan_utilization = total_loans / max(self.deposits, 1.0)
        liquidity        = (self.deposits + self.capital - total_loans) / max(self.deposits, 1.0)
        spread           = self.loan_rate - self.deposit_rate

        # ── 诊断一：存款负担型 ────────────────────────────────
        # 流动性极充裕 + 坏账低 + 月利润持续为负 = 存款利息拖垮资本
        recent_profit = (
            sum(h.get("monthly_profit", 0) for h in self.history[-3:]) / 3
            if len(self.history) >= 3 else self.monthly_profit
        )
        deposit_burden = (
            loan_utilization < 0.25          # 贷款严重不足
            and self.bad_debt_rate < 0.05    # 坏账率低（不是信用问题）
            and recent_profit < -50          # 连续亏损
        )

        rule_loan_delta    = 0.0  # 贷款利率调整
        rule_deposit_delta = 0.0  # 存款利率调整（独立控制）

        if deposit_burden:
            # 存款负担：大幅降低存款利率，适度降低贷款利率鼓励借贷
            rule_deposit_delta = -0.008    # 主动压低存款成本
            rule_loan_delta    = -0.003    # 降低贷款门槛吸引工厂借贷
            intention["loosen_credit"]  = True
            intention["llm_needed"]     = True
        else:
            # ── 诊断二：常规流动性管理 ──
            if liquidity > 0.5 and spread > self.goals.min_interest_spread + 0.01:
                rule_loan_delta -= 0.002   # 流动性充裕，小幅降低贷款利率
            elif liquidity < BANK_RESERVE_RATIO + 0.05:
                rule_loan_delta += 0.003   # 流动性偏紧，小幅上调
            if spread < self.goals.min_interest_spread:
                rule_loan_delta += 0.002   # 保护利差

            # ── 诊断三：坏账危机 ──
            if self.bad_debt_rate > self.goals.max_bad_debt_rate:
                rule_loan_delta    += 0.005
                rule_deposit_delta += 0.002  # 吸引存款补充资本
                intention["tighten_credit"] = True
                intention["llm_needed"]     = True

        # ── 经济学家建议（35%权重）────────────────────────────
        econ_delta = p.get("econ_rate_delta", 0.0) * 0.35

        if p.get("credit_tightening") or p.get("warning_severity") in ("critical", "warning"):
            if not deposit_burden:    # 存款负担时不收紧（矛盾方向）
                intention["tighten_credit"] = True
        if p.get("warning_severity") == "critical":
            intention["llm_needed"] = True

        # ── LLM 反馈（10%权重）─────────────────────────────────
        llm_adjustment = self._llm_rate_delta * 0.10
        if self._llm_tighten is True and not deposit_burden:
            intention["tighten_credit"] = True
        elif self._llm_tighten is False:
            intention["loosen_credit"] = True

        # ── 汇总决策 ─────────────────────────────────────────
        risk_total = p.get("risk_total", 30.0)
        self.goals.risk_appetite = max(0.1, 1.0 - risk_total / 100.0)

        intention["rate_delta"]         = round(rule_loan_delta * 0.55 + econ_delta + llm_adjustment, 4)
        intention["deposit_rate_delta"] = round(rule_deposit_delta, 4)
        self._tighten_credit = intention["tighten_credit"] and not intention["loosen_credit"]
        return intention

    # ═══════════════════════════════════════════════════════════
    # LLM 辅助层（闭环）
    # ═══════════════════════════════════════════════════════════

    def llm_credit_policy(self) -> str:
        """
        在坏账危机或存款负担危机时，请 LLM 给出信贷政策建议。
        返回文本，同时由 apply_llm_advice() 解析后反馈到下一轮 decide()。
        """
        p = self._perceived
        total_loans      = sum(r.principal for r in self.loans.values())
        loan_utilization = total_loans / max(self.deposits, 1.0)
        recent_profit = (
            sum(h.get("monthly_profit", 0) for h in self.history[-3:]) / 3
            if len(self.history) >= 3 else 0.0
        )

        prompt = f"""你是一位经验丰富的银行行长，请用100字以内给出当前最优信贷政策。

【银行现状】
  坏账率: {self.bad_debt_rate*100:.1f}%   贷款利用率: {loan_utilization*100:.1f}%
  存款利率: {self.deposit_rate*100:.2f}%  贷款利率: {self.loan_rate*100:.2f}%
  资本金: {self.capital:.0f}  存款总额: {self.deposits:.0f}
  近3月平均月利润: {recent_profit:.0f}

【经济环境】
  阶段: {p.get('phase','未知')}  综合风险: {p.get('risk_total',0):.0f}/100
  预警: {', '.join(p.get('warnings',[])) or '无'}

【判断问题类型】
  {'⚠ 存款负担型：贷款利用率低，利息支出拖垮资本，需降低存款利率鼓励借贷' if loan_utilization < 0.25 and recent_profit < 0 else ''}
  {'⚠ 坏账危机型：坏账率偏高，需收紧信贷' if self.bad_debt_rate > 0.10 else ''}

请给出：①存款利率应上调/维持/下调 ②贷款利率应上调/维持/下调 ③信贷应收紧/维持/放松 ④核心理由（一句话）"""

        from analysis.llm_analyst import _ollama_chat
        text = _ollama_chat(prompt, model=OLLAMA_MODEL, timeout=45)
        return text

    def apply_llm_advice(self, text: str) -> None:
        """
        解析 LLM 建议文本，提取利率方向信号，存入内部状态。
        下一轮 decide() 时以 10% 权重应用，形成 LLM→决策闭环。
        """
        # 解析利率方向
        if any(k in text for k in ["下调", "降低利率", "降息", "利率降", "应降"]):
            self._llm_rate_delta = -0.003
        elif any(k in text for k in ["上调", "提高利率", "加息", "利率升", "应升"]):
            self._llm_rate_delta = +0.003
        else:
            self._llm_rate_delta = 0.0

        # 解析信贷方向
        if any(k in text for k in ["收紧", "暂停贷款", "减少贷款", "严格审核"]):
            self._llm_tighten = True
        elif any(k in text for k in ["放松", "放开", "扩大信贷", "鼓励借贷", "降低门槛"]):
            self._llm_tighten = False
        else:
            self._llm_tighten = None

    # ═══════════════════════════════════════════════════════════
    # 行动层
    # ═══════════════════════════════════════════════════════════

    def act(self, intention: dict, bus: "MessageBus") -> Optional[str]:
        """
        执行利率调整（存贷款独立调整），发布利率公告。
        触发 LLM 时返回建议文本（调用方负责调 apply_llm_advice）。
        """
        # 贷款利率
        loan_delta = intention.get("rate_delta", 0.0)
        self.loan_rate = round(max(0.01, min(0.20, self.loan_rate + loan_delta)), 4)

        # 存款利率（可独立调整）
        dep_delta = intention.get("deposit_rate_delta", 0.0)
        if dep_delta != 0.0:
            # 存款负担/坏账场景：存款利率独立调整
            self.deposit_rate = round(
                max(0.005, min(self.loan_rate - 0.005, self.deposit_rate + dep_delta)), 4
            )
        else:
            # 常规：维持利差约束
            self.deposit_rate = round(
                max(0.005, min(self.loan_rate - 0.01,
                               self.loan_rate - self.goals.min_interest_spread)), 4
            )

        direction = "up" if loan_delta > 0.001 else ("down" if loan_delta < -0.001 else "hold")
        msg = make_rate_announcement(month=len(self.history) + 1, bank=self)
        msg.payload["rate_direction"]    = direction
        msg.payload["credit_tightening"] = self._tighten_credit
        msg.payload["loosen_credit"]     = intention.get("loosen_credit", False)
        msg.payload["risk_appetite"]     = self.goals.risk_appetite
        bus.publish(msg)

        # LLM 调用（需要时）
        if intention.get("llm_needed", False):
            return self.llm_credit_policy()
        return None

    # ═══════════════════════════════════════════════════════════
    # 核心金融操作
    # ═══════════════════════════════════════════════════════════

    def accept_deposit(self, amount: float) -> None:
        self.deposits += amount

    def withdraw_deposit(self, amount: float) -> float:
        actual = min(amount, self.deposits)
        self.deposits -= actual
        return actual

    def pay_deposit_interest(self) -> float:
        interest = self.deposits * self.deposit_rate
        self.capital -= interest
        return interest

    def can_lend(self, amount: float) -> bool:
        total_loans_after = sum(r.principal for r in self.loans.values()) + amount
        available         = self.deposits + self.capital
        reserve_needed    = self.deposits * BANK_RESERVE_RATIO
        return (available - total_loans_after) >= reserve_needed

    def grant_loan(self, factory_id: int, requested: float) -> float:
        """
        审批贷款，结合信用评分和信贷政策动态调整额度。
        信贷放松（存款负担场景）时提高额度上限。
        """
        credit = self._factory_credit.get(factory_id, 0.5)

        if self._tighten_credit:
            credit_multiplier = 0.3 + 0.7 * credit
        elif hasattr(self, '_perceived') and self._perceived.get('loosen_credit'):
            # 存款负担时主动放宽信贷
            credit_multiplier = 0.7 + 0.3 * credit
        else:
            credit_multiplier = 0.5 + 0.5 * credit

        adjusted_max = BANK_MAX_LOAN_PER_FACTORY * credit_multiplier
        max_allowed  = min(requested, adjusted_max)

        if not self.can_lend(max_allowed):
            headroom = max(0.0, (self.deposits + self.capital)
                           - self.deposits * BANK_RESERVE_RATIO
                           - sum(r.principal for r in self.loans.values()))
            max_allowed = min(max_allowed, headroom)

        if max_allowed <= 0:
            return 0.0

        self.loans[factory_id] = LoanRecord(
            factory_id=factory_id,
            principal=max_allowed,
            monthly_rate=self.loan_rate,
            months_remaining=1,
        )
        return max_allowed

    def repay_loan(self, factory_id: int, amount: float) -> float:
        if factory_id not in self.loans:
            return 0.0
        record    = self.loans[factory_id]
        due       = record.principal * (1 + record.monthly_rate)
        actual    = min(amount, due)
        shortfall = due - actual
        if shortfall > 0:
            record.is_default = True
            self.bad_debt  += shortfall
            self.capital   -= shortfall
        self.monthly_profit += actual - record.principal
        del self.loans[factory_id]
        return actual

    def monthly_settle(self) -> dict:
        interest_paid = self.pay_deposit_interest()
        self.monthly_profit -= interest_paid

        snapshot = {
            "capital":        self.capital,
            "deposits":       self.deposits,
            "total_loans":    sum(r.principal for r in self.loans.values()),
            "deposit_rate":   self.deposit_rate,
            "loan_rate":      self.loan_rate,
            "bad_debt":       self.bad_debt,
            "monthly_profit": self.monthly_profit,
        }
        self.history.append(snapshot)
        self.monthly_profit = 0.0
        return snapshot

    # 兼容旧接口
    def update_rates(self) -> None:
        total_assets = self.deposits + self.capital
        total_loans  = sum(r.principal for r in self.loans.values())
        liquidity    = (total_assets - total_loans) / max(self.deposits, 1.0)
        if liquidity > 0.5:
            self.deposit_rate = max(0.005, self.deposit_rate - 0.002)
            self.loan_rate    = max(0.02,  self.loan_rate - 0.001)
        elif liquidity < BANK_RESERVE_RATIO + 0.05:
            self.deposit_rate = min(0.08,  self.deposit_rate + 0.003)
            self.loan_rate    = min(0.15,  self.loan_rate + 0.002)

    @property
    def bad_debt_rate(self) -> float:
        total = sum(r.principal for r in self.loans.values()) + self.bad_debt
        return self.bad_debt / max(total, 1.0)

    def __repr__(self) -> str:
        return (f"Bank(capital={self.capital:.1f}, dep_rate={self.deposit_rate:.3f}, "
                f"loan_rate={self.loan_rate:.3f}, bad_debt={self.bad_debt_rate*100:.1f}%)")
