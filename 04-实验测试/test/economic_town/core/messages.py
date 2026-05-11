"""Agent 间消息协议定义"""
from dataclasses import dataclass, field
from typing import Any

# ── Topic 常量 ────────────────────────────────────────────────
TOPIC_ECONOMIC_REPORT    = "economist.report.monthly"
TOPIC_RATE_ANNOUNCEMENT  = "bank.announcement.rates"
TOPIC_CREDIT_SCORE       = "factory.credit.score"
TOPIC_WARNING_ALERT      = "economist.warning.alert"
TOPIC_LABOR_MARKET       = "simulation.signal.labor_market"
TOPIC_FACTORY_STRATEGY   = "factory.strategy.update"


@dataclass
class Message:
    topic: str
    month: int
    sender: str
    payload: dict = field(default_factory=dict)


# ── payload 构建工具函数 ──────────────────────────────────────

def make_economic_report(month: int, diag) -> Message:
    """由 EconomistAgent 每月发布"""
    return Message(
        topic=TOPIC_ECONOMIC_REPORT,
        month=month,
        sender="economist",
        payload={
            "phase": diag.phase,
            "phase_reason": diag.phase_reason,
            "risk_total": diag.risk.total,
            "risk_employment": diag.risk.employment,
            "risk_financial": diag.risk.financial,
            "risk_inequality": diag.risk.inequality,
            "risk_external": diag.risk.external,
            "warnings": diag.warnings,
            "bank_advice": diag.bank_advice,
            "factory_advice": diag.factory_advice,
            "worker_advice": diag.worker_advice,
            # 具体操作信号：银行参考
            "recommended_loan_rate_delta": _phase_to_rate_delta(diag.phase, diag.risk.total),
            "credit_tightening": diag.risk.financial > 40 or diag.risk.total > 50,
        },
    )


def make_rate_announcement(month: int, bank) -> Message:
    """由 Bank 在更新利率后发布"""
    return Message(
        topic=TOPIC_RATE_ANNOUNCEMENT,
        month=month,
        sender="bank",
        payload={
            "deposit_rate": bank.deposit_rate,
            "loan_rate": bank.loan_rate,
            "rate_direction": "hold",   # 由 bank.act() 填写
        },
    )


def make_credit_score(month: int, factory_id: int, score: float,
                      history: str, avg_profit: float, requested: float) -> Message:
    return Message(
        topic=TOPIC_CREDIT_SCORE,
        month=month,
        sender=f"factory_{factory_id}",
        payload={
            "factory_id": factory_id,
            "credit_score": score,
            "repayment_history": history,
            "avg_profit_3m": avg_profit,
            "requested_amount": requested,
        },
    )


def make_warning_alert(month: int, warnings: list, severity: str = "warning") -> Message:
    return Message(
        topic=TOPIC_WARNING_ALERT,
        month=month,
        sender="economist",
        payload={
            "severity": severity,
            "warnings": warnings,
            "affected_agents": ["bank", "factory", "worker"],
        },
    )


def make_labor_market_signal(month: int, unemployment_rate: float,
                              avg_wage: float, jobs: int, seeking: int) -> Message:
    return Message(
        topic=TOPIC_LABOR_MARKET,
        month=month,
        sender="simulation",
        payload={
            "unemployment_rate": unemployment_rate,
            "avg_offered_wage": avg_wage,
            "jobs_available": jobs,
            "workers_seeking": seeking,
        },
    )


def _phase_to_rate_delta(phase: str, risk_total: float) -> float:
    """根据经济阶段给出建议利率变化幅度"""
    mapping = {
        "危机": +0.02,   # 危机时反直觉：短期提高利率防资本外流
        "衰退": -0.01,
        "收缩": -0.005,
        "触底":  0.0,
        "复苏": -0.002,
        "扩张": +0.002,
        "过热": +0.01,
        "稳态":  0.0,
    }
    base = mapping.get(phase, 0.0)
    # 综合风险过高时额外收紧
    if risk_total > 60:
        base += 0.005
    return round(base, 4)
