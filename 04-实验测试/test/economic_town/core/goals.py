"""各 Agent 的长远目标结构定义（纯数据，不含逻辑）"""
from dataclasses import dataclass, field


@dataclass
class BankGoals:
    """银行长远目标：稳健经营、防范系统性风险"""
    target_capital_ratio: float = 0.12      # 资本充足率目标
    max_bad_debt_rate: float = 0.15         # 坏账率红线
    min_interest_spread: float = 0.02       # 利差保护线
    target_deposit_growth_rate: float = 0.01  # 月存款增速目标
    risk_appetite: float = 0.5              # 风险偏好 0=保守 1=激进（动态调整）


@dataclass
class EconomistGoals:
    """经济学家长远目标：准确诊断并及时预警"""
    publish_monthly: bool = True
    llm_interval_months: int = 3            # 每3月触发 LLM 叙述
    warning_unemployment_threshold: float = 0.30
    warning_bad_debt_threshold: float = 0.15
    accuracy_window: int = 3                # 后验校验窗口


@dataclass
class FactoryGoals:
    """工厂长远目标：盈利生存、适度扩张"""
    target_profit_margin: float = 0.05      # 目标净利润率
    min_cash_reserve: float = 300.0         # 生存底线
    max_loan_to_cash_ratio: float = 2.0     # 杠杆上限
    expansion_profit_threshold: float = 0.10  # 触发扩张的利润率
    contraction_trigger: float = -0.05      # 触发收缩的亏损率
    current_strategy: str = "normal"        # aggressive | normal | defensive


@dataclass
class WorkerGoals:
    """工人长远目标：稳定就业、积累储蓄"""
    target_savings_months: int = 3          # 目标存款 = N 个月工资
    min_reservation_wage_ratio: float = 0.5
    prefer_stable_job: bool = True
    crisis_savings_rate_boost: float = 0.15  # 预警时储蓄率额外提升
