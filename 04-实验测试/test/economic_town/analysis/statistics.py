"""统计分析模块 —— 从月度快照中计算各项经济指标"""
from __future__ import annotations
import csv
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.simulation import TownEconomy


def compute_gini(values: list[float]) -> float:
    """计算基尼系数（0=完全平等, 1=完全不平等）"""
    if not values or sum(values) == 0:
        return 0.0
    n = len(values)
    sorted_vals = sorted(values)
    cumsum = 0.0
    for i, v in enumerate(sorted_vals):
        cumsum += (2 * (i + 1) - n - 1) * v
    return cumsum / (n * sum(sorted_vals))


def extract_monthly_metrics(snapshot: dict, economy: "TownEconomy") -> dict:
    """
    从一个月的快照中提取所有关键指标。
    返回一个扁平化的指标字典，适合写入 CSV 或传给 LLM。
    """
    month = snapshot["month"]
    bank = snapshot["bank"]
    factories = snapshot["factories"]
    workers = snapshot["workers"]
    retailer = snapshot["retailer"]

    # ── 就业指标 ─────────────────────────────────────
    num_workers = len(workers)
    employed_count = sum(1 for w in workers if w["employed"])
    unemployment_rate = 1.0 - employed_count / max(num_workers, 1)

    # ── 工资指标 ──────────────────────────────────────
    wages = [w["wage"] for w in workers if w["employed"]]
    avg_wage = sum(wages) / len(wages) if wages else 0.0
    total_wage_bill = sum(wages)

    # ── 工人储蓄分布 → 基尼系数 ──────────────────────
    savings_list = [w["savings"] for w in workers]
    gini = compute_gini(savings_list)

    # ── 工厂指标 ──────────────────────────────────────
    active_factories = [f for f in factories if not f.get("bankrupt", False)]
    total_production = sum(f["production"] for f in active_factories)
    total_revenue = sum(f["revenue"] for f in active_factories)
    avg_profit_margin = (
        sum(f["profit"] / max(f["revenue"], 1) for f in active_factories)
        / len(active_factories)
        if active_factories else 0.0
    )
    bankrupt_count = sum(1 for f in factories if f.get("bankrupt", False))

    # ── 银行指标 ──────────────────────────────────────
    interest_spread = bank["loan_rate"] - bank["deposit_rate"]
    bad_debt_rate = bank["bad_debt"] / max(bank["deposits"] + bank["bad_debt"], 1)

    # ── 资金流动 ──────────────────────────────────────
    local_spend_total = sum(w["local_spend"] for w in workers)
    external_spend_total = sum(w["external_spend"] for w in workers)
    external_revenue_inflow = total_revenue  # 外部市场收入流入

    return {
        "month": month,
        # 就业
        "employment_rate": round(1 - unemployment_rate, 4),
        "unemployment_rate": round(unemployment_rate, 4),
        "employed_count": employed_count,
        # 工资
        "avg_wage": round(avg_wage, 2),
        "total_wage_bill": round(total_wage_bill, 2),
        # 工人财富
        "gini_coefficient": round(gini, 4),
        "avg_worker_savings": round(sum(savings_list) / len(savings_list) if savings_list else 0, 2),
        # 工厂
        "active_factories": len(active_factories),
        "bankrupt_factories": bankrupt_count,
        "total_production": round(total_production, 2),
        "total_revenue": round(total_revenue, 2),
        "avg_profit_margin": round(avg_profit_margin, 4),
        # 银行
        "bank_deposits": round(bank["deposits"], 2),
        "bank_capital": round(bank["capital"], 2),
        "deposit_rate": round(bank["deposit_rate"], 4),
        "loan_rate": round(bank["loan_rate"], 4),
        "interest_spread": round(interest_spread, 4),
        "bank_bad_debt": round(bank["bad_debt"], 2),
        "bad_debt_rate": round(bad_debt_rate, 4),
        "bank_monthly_profit": round(bank["monthly_profit"], 2),
        # 零售商
        "retailer_revenue": round(retailer["revenue"], 2),
        "retailer_profit": round(retailer["profit"], 2),
        "import_cost": round(retailer["import_cost"], 2),
        # 资金流
        "local_spend_total": round(local_spend_total, 2),
        "external_spend_total": round(external_spend_total, 2),
        "external_revenue_inflow": round(external_revenue_inflow, 2),
        # 净流入 = 外部销售收入 - 进口消费品成本
        "net_external_inflow": round(external_revenue_inflow - retailer["import_cost"], 2),
    }


class EconomyStats:
    """统计分析器 —— 累积历史数据，提供查询和导出功能"""

    def __init__(self, economy: "TownEconomy"):
        self.economy = economy
        self.records: list[dict] = []

    def update(self, snapshot: dict) -> dict:
        """处理一个月的快照，计算并存储指标"""
        metrics = extract_monthly_metrics(snapshot, self.economy)
        self.records.append(metrics)
        return metrics

    def update_all(self) -> None:
        """批量处理 economy 中已有的所有快照"""
        processed_months = {r["month"] for r in self.records}
        for snap in self.economy.monthly_snapshots:
            if snap["month"] not in processed_months:
                self.update(snap)

    def latest(self) -> dict:
        """返回最新一个月的指标"""
        return self.records[-1] if self.records else {}

    def get_series(self, key: str) -> list[float]:
        """返回某个指标的时间序列"""
        return [r.get(key, 0.0) for r in self.records]

    def summary_report(self, last_n: int = 12) -> str:
        """返回最近 N 个月的文字摘要（供 LLM 分析使用）"""
        recent = self.records[-last_n:] if len(self.records) >= last_n else self.records
        if not recent:
            return "暂无数据"

        latest = recent[-1]
        first = recent[0]

        def trend(key: str) -> str:
            delta = latest.get(key, 0) - first.get(key, 0)
            return f"+{delta:.2f}" if delta >= 0 else f"{delta:.2f}"

        lines = [
            f"=== 小镇经济摘要（第{first['month']}月 ~ 第{latest['month']}月）===",
            "",
            f"【就业】就业率: {latest['employment_rate']*100:.1f}% （变化 {trend('employment_rate')}）",
            f"【工资】平均工资: {latest['avg_wage']:.1f} （变化 {trend('avg_wage')}）",
            f"【贫富】基尼系数: {latest['gini_coefficient']:.3f} （变化 {trend('gini_coefficient')}）",
            f"【生产】总产量: {latest['total_production']:.1f}，总收入: {latest['total_revenue']:.1f}",
            f"【工厂】活跃: {latest['active_factories']}/3，破产: {latest['bankrupt_factories']}",
            f"【银行】存款: {latest['bank_deposits']:.1f}，存款利率: {latest['deposit_rate']*100:.2f}%，贷款利率: {latest['loan_rate']*100:.2f}%",
            f"【银行】坏账率: {latest['bad_debt_rate']*100:.2f}%，月利润: {latest['bank_monthly_profit']:.1f}",
            f"【贸易】外部收入: {latest['external_revenue_inflow']:.1f}，进口成本: {latest['import_cost']:.1f}，净流入: {latest['net_external_inflow']:.1f}",
        ]
        return "\n".join(lines)

    def export_csv(self, filepath: str) -> None:
        """将所有记录导出为 CSV 文件"""
        if not self.records:
            return
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.records[0].keys())
            writer.writeheader()
            writer.writerows(self.records)

    def check_alerts(self) -> list[str]:
        """检查是否触发异常预警，返回预警消息列表"""
        if not self.records:
            return []
        latest = self.records[-1]
        alerts = []
        from config.params import LLM_TRIGGER_UNEMPLOYMENT_RATE, LLM_TRIGGER_BAD_DEBT_RATE
        if latest["unemployment_rate"] > LLM_TRIGGER_UNEMPLOYMENT_RATE:
            alerts.append(f"⚠️  失业率过高: {latest['unemployment_rate']*100:.1f}%")
        if latest["bad_debt_rate"] > LLM_TRIGGER_BAD_DEBT_RATE:
            alerts.append(f"⚠️  银行坏账率过高: {latest['bad_debt_rate']*100:.1f}%")
        if latest["bankrupt_factories"] >= 2:
            alerts.append(f"⚠️  多家工厂破产: {latest['bankrupt_factories']} 家")
        return alerts
