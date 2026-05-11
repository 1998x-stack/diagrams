"""
经济学家 Agent —— 独立观察经济体，诊断周期阶段，输出结构化结论

架构：
  感知层  →  从消息总线读取劳动力市场信号
  规则层  →  计算趋势指标、判断经济阶段、生成风险评分（每月，毫秒级）
  LLM层   →  将诊断结果转化为自然语言结论（每3个月或危机时触发）
  行动层  →  将诊断报告 + 预警发布到消息总线

长远目标：准确诊断、及时预警、为其他 Agent 提供决策依据
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.message_bus import MessageBus

from analysis.llm_analyst import _ollama_chat
from config.params import OLLAMA_MODEL
from core.goals import EconomistGoals
from core.messages import (
    make_economic_report, make_warning_alert,
    TOPIC_LABOR_MARKET,
)


# ── 数据结构 ──────────────────────────────────────────────────

@dataclass
class RiskScore:
    """五维风险评分（0~100，越高越危险）"""
    employment: float    # 就业风险
    financial:  float    # 金融风险（坏账 + 利差收窄）
    inequality: float    # 贫富差距风险（基尼系数）
    external:   float    # 外部依存风险（过度依赖出口）
    wage:       float    # 工资停滞风险

    @property
    def total(self) -> float:
        return (self.employment * 0.3 + self.financial * 0.25
                + self.inequality * 0.2 + self.external * 0.15
                + self.wage * 0.1)

    @property
    def level(self) -> str:
        t = self.total
        if t < 20:  return "低风险"
        if t < 40:  return "中低风险"
        if t < 60:  return "中高风险"
        return "高风险"


@dataclass
class EconomicDiagnosis:
    """经济体月度诊断报告（规则引擎输出）"""
    month: int
    phase: str                      # 经济周期阶段
    phase_reason: str               # 判断理由
    risk: RiskScore                 # 五维风险
    trends: dict                    # 关键指标趋势（3个月移动平均变化率）
    warnings: list[str]             # 规则触发的预警
    bank_advice: str                # 对银行的建议
    factory_advice: str             # 对工厂的建议
    worker_advice: str              # 对工人的建议
    llm_conclusion: str = ""        # LLM 补充的叙述性结论（按需填充）


# ── 经济学家 Agent ────────────────────────────────────────────

class EconomistAgent:
    """
    经济学家 Agent

    输入（感知）：
      - TOPIC_LABOR_MARKET：劳动力市场信号（来自仿真）
      - metrics dict：本月统计指标（来自 EconomyStats）

    输出（行动）：
      - TOPIC_ECONOMIC_REPORT：完整诊断报告（每月）
      - TOPIC_WARNING_ALERT：预警信息（有警告时发布）

    LLM 触发条件：
      - 每 goals.llm_interval_months 个月一次
      - 经济阶段为"危机"时立即触发
    """

    PHASES = ["危机", "衰退", "收缩", "触底", "复苏", "扩张", "过热", "稳态"]

    def __init__(self, model: str = OLLAMA_MODEL, window: int = 3):
        self.model = model
        self.window = window
        self.goals = EconomistGoals()
        self._history: list[dict] = []     # 历史指标（原始）
        self.diagnoses: list[EconomicDiagnosis] = []
        self._last_llm_month: int = 0      # 上次触发 LLM 的月份

    # ── 感知层 ────────────────────────────────────────────────

    def perceive(self, bus: "MessageBus") -> dict:
        """
        读取劳动力市场信号，补充感知上下文。
        返回从总线获取的补充信息（与主 metrics 合并使用）。
        """
        msg = bus.get_latest(TOPIC_LABOR_MARKET)
        if msg is None:
            return {}
        return {
            "bus_unemployment_rate": msg.payload.get("unemployment_rate", 0.0),
            "bus_avg_wage":          msg.payload.get("avg_offered_wage", 0.0),
            "bus_jobs_available":    msg.payload.get("jobs_available", 0),
            "bus_workers_seeking":   msg.payload.get("workers_seeking", 0),
        }

    # ── 规则层（核心诊断）─────────────────────────────────────

    def observe(self, metrics: dict) -> EconomicDiagnosis:
        """
        接收本月指标，执行规则分析，返回诊断报告。
        metrics 由 EconomyStats.update() 生成。
        """
        self._history.append(metrics)
        diag = self._run_rules(metrics)
        self.diagnoses.append(diag)
        return diag

    # ── LLM 层（按需叙述）────────────────────────────────────

    def conclude(self, diag: Optional[EconomicDiagnosis] = None) -> str:
        """
        调用 LLM 为最新诊断生成叙述性结论。
        结论写入 diag.llm_conclusion 并返回。
        """
        target = diag or (self.diagnoses[-1] if self.diagnoses else None)
        if target is None:
            return ""
        prompt = self._build_conclusion_prompt(target)
        text = _ollama_chat(prompt, model=self.model, timeout=60)
        target.llm_conclusion = text
        self._last_llm_month = target.month
        return text

    def should_trigger_llm(self, month: int) -> bool:
        """判断是否应触发 LLM（满足任一条件）"""
        latest = self.diagnoses[-1] if self.diagnoses else None
        if latest is None:
            return False
        # 条件1：周期性触发
        if month - self._last_llm_month >= self.goals.llm_interval_months:
            return True
        # 条件2：危机或高风险立即触发
        if latest.phase in ("危机", "衰退") or latest.risk.total > 70:
            return True
        return False

    # ── 行动层（发布消息）────────────────────────────────────

    def act(self, diag: EconomicDiagnosis, bus: "MessageBus") -> None:
        """
        将诊断报告和预警发布到消息总线。
        其他 Agent 通过拉取消息获知经济形势。
        """
        # 发布完整经济报告
        bus.publish(make_economic_report(diag.month, diag))

        # 有预警时额外发布警告消息
        if diag.warnings:
            severity = "critical" if diag.risk.total > 60 else "warning"
            bus.publish(make_warning_alert(diag.month, diag.warnings, severity))

    # ── 辅助查询 ─────────────────────────────────────────────

    def latest_diagnosis(self) -> Optional[EconomicDiagnosis]:
        return self.diagnoses[-1] if self.diagnoses else None

    def phase_history(self) -> list[str]:
        return [d.phase for d in self.diagnoses]

    # ── 内部：规则引擎 ────────────────────────────────────────

    def _run_rules(self, m: dict) -> EconomicDiagnosis:
        month = m["month"]
        trends = self._compute_trends()
        risk = self._compute_risk(m, trends)
        phase, reason = self._detect_phase(m, trends, risk)
        warnings = self._check_warnings(m, trends, risk)
        bank_adv, factory_adv, worker_adv = self._generate_advice(m, trends, risk, phase)

        return EconomicDiagnosis(
            month=month,
            phase=phase,
            phase_reason=reason,
            risk=risk,
            trends=trends,
            warnings=warnings,
            bank_advice=bank_adv,
            factory_advice=factory_adv,
            worker_advice=worker_adv,
        )

    def _compute_trends(self) -> dict:
        """计算关键指标的近期变化率（与 window 个月前对比）"""
        n = len(self._history)
        zero = {k: 0.0 for k in [
            "employment_delta", "wage_delta", "production_delta",
            "bank_deposits_delta", "gini_delta", "bad_debt_delta",
            "profit_margin_delta", "net_inflow_delta",
        ]}
        if n < 2:
            return zero

        now = self._history[-1]
        ago = self._history[max(0, n - 1 - self.window)]

        def delta(key: str) -> float:
            return now.get(key, 0.0) - ago.get(key, 0.0)

        def pct(key: str) -> float:
            base = ago.get(key, 0.0)
            return delta(key) / base if base != 0 else 0.0

        return {
            "employment_delta":    delta("employment_rate"),
            "wage_delta":          delta("avg_wage"),
            "production_delta":    pct("total_production"),
            "bank_deposits_delta": pct("bank_deposits"),
            "gini_delta":          delta("gini_coefficient"),
            "bad_debt_delta":      delta("bad_debt_rate"),
            "profit_margin_delta": delta("avg_profit_margin"),
            "net_inflow_delta":    delta("net_external_inflow"),
        }

    def _compute_risk(self, m: dict, trends: dict) -> RiskScore:
        # 就业风险：失业率直接映射
        emp_risk = m.get("unemployment_rate", 0.0) * 100

        # 金融风险：坏账率 + 利差收窄
        bad_debt_score = m.get("bad_debt_rate", 0.0) * 200   # 坏账 10% → 20分
        spread = m.get("interest_spread", 0.03)
        spread_score = max(0.0, (0.03 - spread) / 0.03 * 40)
        fin_risk = min(100.0, bad_debt_score + spread_score)

        # 贫富差距风险：基尼系数 × 200（0.5 → 100分）
        ineq_risk = min(100.0, m.get("gini_coefficient", 0.0) * 200)

        # 外部依存风险
        total_rev = m.get("total_revenue", 1.0)
        ext_ratio = m.get("external_revenue_inflow", 0.0) / max(total_rev, 1.0)
        ext_risk = min(100.0, ext_ratio * 80)

        # 工资停滞风险
        avg_wage = m.get("avg_wage", 100.0)
        wage_risk = min(100.0, max(0.0, (100.0 - avg_wage) / 100.0 * 100))

        return RiskScore(
            employment=round(emp_risk, 1),
            financial=round(fin_risk, 1),
            inequality=round(ineq_risk, 1),
            external=round(ext_risk, 1),
            wage=round(wage_risk, 1),
        )

    def _detect_phase(self, m: dict, trends: dict, risk: RiskScore) -> tuple[str, str]:
        emp      = m.get("employment_rate", 0.0)
        d_emp    = trends["employment_delta"]
        d_prod   = trends["production_delta"]
        d_profit = trends["profit_margin_delta"]
        bankrupt = m.get("bankrupt_factories", 0)
        bad_debt = m.get("bad_debt_rate", 0.0)

        # 优先级从高到低：危机 > 衰退 > 收缩 > 触底 > 扩张 > 复苏 > 过热 > 稳态
        if bankrupt >= 2 or bad_debt > 0.25:
            return "危机", f"工厂破产{bankrupt}家，坏账率{bad_debt*100:.1f}%"
        if emp < 0.4 and d_emp < -0.1:
            return "衰退", f"就业率{emp*100:.0f}%持续下滑"
        if emp < 0.7 and d_emp < 0:
            return "收缩", f"就业率{emp*100:.0f}%，下行趋势"
        if emp < 0.7 and d_emp >= 0:
            return "触底", f"就业率{emp*100:.0f}%，跌势放缓"
        if emp >= 0.9 and d_prod > 0.05 and d_profit >= -0.02:
            return "扩张", f"高就业{emp*100:.0f}%，产出+{d_prod*100:.1f}%"
        if emp >= 0.7 and d_emp > 0.05 and d_prod > 0:
            return "复苏", f"就业率{emp*100:.0f}%回升，产出增长"
        if emp >= 0.95 and d_prod <= 0 and risk.financial > 30:
            return "过热", f"满就业但产出停滞，金融风险{risk.financial:.0f}"
        if emp >= 0.85 and abs(d_emp) < 0.05 and abs(d_prod) < 0.03:
            return "稳态", f"就业率{emp*100:.0f}%，各指标平稳"
        if d_emp >= 0:
            return "复苏", f"就业率{emp*100:.0f}%，趋势向好"
        return "收缩", f"就业率{emp*100:.0f}%，仍在下行"

    def _check_warnings(self, m: dict, trends: dict, risk: RiskScore) -> list[str]:
        warns = []
        if m.get("unemployment_rate", 0) > self.goals.warning_unemployment_threshold:
            warns.append(f"失业率过高 {m['unemployment_rate']*100:.1f}%")
        if m.get("bad_debt_rate", 0) > self.goals.warning_bad_debt_threshold:
            warns.append(f"银行坏账率危险 {m['bad_debt_rate']*100:.1f}%")
        if m.get("bank_monthly_profit", 0) < -200:
            warns.append(f"银行月亏损 {m['bank_monthly_profit']:.0f}")
        if trends["gini_delta"] > 0.02:
            warns.append(f"贫富差距快速扩大 +{trends['gini_delta']:.3f}")
        if trends["wage_delta"] < -10:
            warns.append(f"工资快速下滑 {trends['wage_delta']:.1f}")
        if m.get("interest_spread", 0.05) < 0.01:
            warns.append("银行利差极低，盈利能力受威胁")
        return warns

    def _generate_advice(self, m, trends, risk, phase) -> tuple[str, str, str]:
        """基于规则生成三方建议"""
        spread   = m.get("interest_spread", 0.03)
        bad_debt = m.get("bad_debt_rate", 0.0)

        # 银行建议
        if bad_debt > 0.15:
            bank = "收紧信贷审核，优先保住资本金，暂停高风险工厂贷款"
        elif spread < 0.01:
            bank = "利差过低，应适当上调贷款利率以恢复盈利能力"
        elif phase in ("扩张", "过热"):
            bank = "经济向好，可扩大信贷规模，但密切监控坏账率"
        elif phase in ("衰退", "危机"):
            bank = "降低贷款门槛、下调利率以支持工厂渡过难关"
        else:
            bank = "维持现有利率，保持流动性观望"

        # 工厂建议
        profit_margin = m.get("avg_profit_margin", 0.0)
        emp_rate      = m.get("employment_rate", 1.0)
        if profit_margin < 0:
            factory = "利润为负，削减工资预算或减少贷款，控制生产成本"
        elif phase == "扩张" and emp_rate < 0.9:
            factory = "扩张时机良好，增加借贷扩大生产，积极抢占市场"
        elif phase in ("收缩", "衰退"):
            factory = "市场下行，降低定价争取销量，减少贷款依赖"
        elif trends["production_delta"] > 0.1:
            factory = "产能快速扩张，注意不要过度借贷，留足还款缓冲"
        else:
            factory = "保持当前规模，优化定价策略提升销售率"

        # 工人建议
        gini         = m.get("gini_coefficient", 0.0)
        unemployment = m.get("unemployment_rate", 0.0)
        if unemployment > 0.3:
            worker = "失业率高，主动降低心理工资预期以尽快重返就业"
        elif gini > 0.3:
            worker = "贫富差距大，技能低的工人应优先提升自身竞争力"
        elif trends["wage_delta"] > 5:
            worker = "工资上升期，适当提高储蓄率防备未来波动"
        elif phase in ("稳态", "扩张"):
            worker = "经济稳定，可适当提高消费比例，促进本地零售循环"
        else:
            worker = "经济不确定，保持储蓄率，减少非必要消费"

        return bank, factory, worker

    # ── LLM Prompt 构建 ───────────────────────────────────────

    def _build_conclusion_prompt(self, diag: EconomicDiagnosis) -> str:
        m = self._history[-1] if self._history else {}
        phase_hist = self.phase_history()[-6:]
        phase_str  = " → ".join(phase_hist) if phase_hist else "无历史"

        return f"""你是一位严谨的宏观经济学家，请用简洁的中文（200字以内）给出本月经济诊断结论。

【第{diag.month}月经济诊断】
经济阶段: {diag.phase}（{diag.phase_reason}）
近6月演变: {phase_str}

风险评分（0=低，100=高）:
  就业 {diag.risk.employment:.0f}  |  金融 {diag.risk.financial:.0f}  |  贫富 {diag.risk.inequality:.0f}
  外部 {diag.risk.external:.0f}    |  工资 {diag.risk.wage:.0f}        |  综合 {diag.risk.total:.0f}（{diag.risk.level}）

关键数据:
  就业率 {m.get('employment_rate',0)*100:.1f}%  工资 {m.get('avg_wage',0):.1f}
  工厂利润率 {m.get('avg_profit_margin',0)*100:.1f}%  基尼 {m.get('gini_coefficient',0):.3f}
  贷款利率 {m.get('loan_rate',0)*100:.2f}%  坏账率 {m.get('bad_debt_rate',0)*100:.2f}%

规则建议:
  银行: {diag.bank_advice}
  工厂: {diag.factory_advice}
  工人: {diag.worker_advice}

预警: {', '.join(diag.warnings) if diag.warnings else '无'}

请输出：①当前阶段的核心矛盾 ②最大潜在风险 ③对未来1~3个月的判断"""

    # ── 格式化输出 ────────────────────────────────────────────

    def format_diagnosis(self, diag: Optional[EconomicDiagnosis] = None) -> str:
        d = diag or self.latest_diagnosis()
        if d is None:
            return "暂无诊断"
        lines = [
            f"┌── 经济学家诊断报告 · 第{d.month}月 {'─'*30}",
            f"│  阶段: {d.phase}  ({d.phase_reason})",
            f"│  综合风险: {d.risk.total:.1f}/100  [{d.risk.level}]",
            f"│  就业{d.risk.employment:.0f}  金融{d.risk.financial:.0f}  贫富{d.risk.inequality:.0f}  外部{d.risk.external:.0f}  工资{d.risk.wage:.0f}",
        ]
        if d.warnings:
            lines.append(f"│  ⚠  {' | '.join(d.warnings)}")
        lines += [
            f"│  [银行] {d.bank_advice}",
            f"│  [工厂] {d.factory_advice}",
            f"│  [工人] {d.worker_advice}",
        ]
        if d.llm_conclusion:
            for line in d.llm_conclusion.strip().split("\n"):
                lines.append(f"│  {line}")
        lines.append("└" + "─" * 50)
        return "\n".join(lines)
