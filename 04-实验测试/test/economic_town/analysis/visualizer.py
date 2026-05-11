"""可视化模块 —— 将统计数据绘制成图表"""
from __future__ import annotations
import os
import matplotlib
matplotlib.use("Agg")  # 非交互式后端，适合无 GUI 环境
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from analysis.statistics import EconomyStats


def _setup_chinese_font():
    """尝试设置中文字体，找不到则退回英文标签"""
    import matplotlib.font_manager as fm
    chinese_fonts = ["PingFang SC", "Heiti SC", "SimHei", "WenQuanYi Micro Hei"]
    available = {f.name for f in fm.fontManager.ttflist}
    for font in chinese_fonts:
        if font in available:
            plt.rcParams["font.family"] = font
            return True
    # 找不到中文字体，使用英文标签
    return False


_HAS_CHINESE = _setup_chinese_font()

# 标签映射（有中文字体则用中文，否则用英文）
_LABELS = {
    "employment_rate": "Employment Rate" if not _HAS_CHINESE else "就业率",
    "avg_wage": "Avg Wage" if not _HAS_CHINESE else "平均工资",
    "bank_deposits": "Bank Deposits" if not _HAS_CHINESE else "银行存款",
    "loan_rate": "Loan Rate" if not _HAS_CHINESE else "贷款利率",
    "deposit_rate": "Deposit Rate" if not _HAS_CHINESE else "存款利率",
    "total_production": "Total Production" if not _HAS_CHINESE else "总产量",
    "total_revenue": "Total Revenue" if not _HAS_CHINESE else "总销售收入",
    "gini_coefficient": "Gini Coefficient" if not _HAS_CHINESE else "基尼系数",
    "bad_debt_rate": "Bad Debt Rate" if not _HAS_CHINESE else "坏账率",
    "net_external_inflow": "Net External Inflow" if not _HAS_CHINESE else "净外部流入",
    "avg_profit_margin": "Avg Profit Margin" if not _HAS_CHINESE else "平均利润率",
    "retailer_profit": "Retailer Profit" if not _HAS_CHINESE else "零售商利润",
}


class Visualizer:
    """图表生成器"""

    def __init__(self, stats: "EconomyStats", output_dir: str = "data/charts"):
        self.stats = stats
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _months(self) -> list[int]:
        return [r["month"] for r in self.stats.records]

    def _series(self, key: str) -> list[float]:
        return self.stats.get_series(key)

    def plot_overview(self, save: bool = True) -> str:
        """4 宫格总览图：就业率、工资、银行存款、基尼系数"""
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle("Town Economy Overview" if not _HAS_CHINESE else "小镇经济总览", fontsize=14)

        months = self._months()
        plots = [
            (axes[0, 0], "employment_rate", "b-o", True),
            (axes[0, 1], "avg_wage", "g-s", False),
            (axes[1, 0], "bank_deposits", "r-^", False),
            (axes[1, 1], "gini_coefficient", "purple", False),
        ]

        for ax, key, style, is_pct in plots:
            vals = self._series(key)
            ax.plot(months, vals, style, markersize=3, linewidth=1.5)
            ax.set_title(_LABELS[key])
            ax.set_xlabel("Month" if not _HAS_CHINESE else "月份")
            ax.grid(True, alpha=0.3)
            if is_pct:
                ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))

        plt.tight_layout()
        path = os.path.join(self.output_dir, "overview.png")
        if save:
            plt.savefig(path, dpi=100, bbox_inches="tight")
            plt.close()
        return path

    def plot_financial(self, save: bool = True) -> str:
        """金融指标：利率走势 + 坏账率"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        fig.suptitle("Financial Indicators" if not _HAS_CHINESE else "金融指标", fontsize=13)

        months = self._months()

        # 利率走势
        ax1.plot(months, self._series("loan_rate"), "r-", label=_LABELS["loan_rate"], linewidth=2)
        ax1.plot(months, self._series("deposit_rate"), "b--", label=_LABELS["deposit_rate"], linewidth=2)
        ax1.set_title("Interest Rates" if not _HAS_CHINESE else "利率走势")
        ax1.set_xlabel("Month" if not _HAS_CHINESE else "月份")
        ax1.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # 坏账率
        ax2.fill_between(months, self._series("bad_debt_rate"), alpha=0.4, color="red")
        ax2.plot(months, self._series("bad_debt_rate"), "r-", linewidth=2)
        ax2.set_title(_LABELS["bad_debt_rate"])
        ax2.set_xlabel("Month" if not _HAS_CHINESE else "月份")
        ax2.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        path = os.path.join(self.output_dir, "financial.png")
        if save:
            plt.savefig(path, dpi=100, bbox_inches="tight")
            plt.close()
        return path

    def plot_production(self, save: bool = True) -> str:
        """生产与贸易：产量、收入、净外部流入"""
        fig, axes = plt.subplots(1, 3, figsize=(14, 4))
        fig.suptitle("Production & Trade" if not _HAS_CHINESE else "生产与贸易", fontsize=13)

        months = self._months()
        keys = ["total_production", "total_revenue", "net_external_inflow"]

        for ax, key in zip(axes, keys):
            vals = self._series(key)
            color = "green" if key != "net_external_inflow" else "teal"
            ax.bar(months, vals, color=color, alpha=0.7, width=0.8)
            ax.set_title(_LABELS[key])
            ax.set_xlabel("Month" if not _HAS_CHINESE else "月份")
            ax.grid(True, axis="y", alpha=0.3)

        plt.tight_layout()
        path = os.path.join(self.output_dir, "production.png")
        if save:
            plt.savefig(path, dpi=100, bbox_inches="tight")
            plt.close()
        return path

    def plot_all(self) -> list[str]:
        """生成所有图表，返回文件路径列表"""
        paths = [
            self.plot_overview(),
            self.plot_financial(),
            self.plot_production(),
        ]
        return paths
