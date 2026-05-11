"""LLM 分析层 —— 对接本地 ollama，生成经济分析报告"""
from __future__ import annotations
import json
import urllib.request
import urllib.error
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from analysis.statistics import EconomyStats

from config.params import OLLAMA_MODEL, OLLAMA_BASE_URL, LLM_ANNUAL_REPORT_INTERVAL


def _ollama_chat(prompt: str, model: str = OLLAMA_MODEL, timeout: int = 60) -> str:
    """
    调用本地 ollama /api/generate 接口，返回生成文本。
    使用标准库 urllib，不依赖第三方包。
    """
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.7, "num_predict": 512},
    }).encode("utf-8")

    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("response", "").strip()
    except urllib.error.URLError as e:
        return f"[LLM 调用失败: {e}]"
    except Exception as e:
        return f"[LLM 异常: {e}]"


def is_ollama_available(model: str = OLLAMA_MODEL) -> bool:
    """检查 ollama 服务和模型是否可用"""
    try:
        url = f"{OLLAMA_BASE_URL}/api/tags"
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m["name"] for m in data.get("models", [])]
            return any(model in m for m in models)
    except Exception:
        return False


class LLMAnalyst:
    """
    LLM 经济分析师 —— 根据统计数据生成自然语言分析报告。
    规则引擎负责经济计算，LLM 负责解读和叙述。
    """

    def __init__(self, stats: "EconomyStats", model: str = OLLAMA_MODEL):
        self.stats = stats
        self.model = model
        self.reports: list[dict] = []   # 历史报告存档

    def _build_annual_prompt(self, year: int) -> str:
        """构建年度报告 Prompt"""
        report_text = self.stats.summary_report(last_n=12)
        latest = self.stats.latest()
        return f"""你是一位小镇经济分析师，请用简洁的中文（300字以内）分析以下经济数据，给出：
1. 本年度经济整体状况评价（一句话）
2. 最值得关注的 2 个问题及原因
3. 对银行、工厂、工人三方各一条具体建议

=== 第 {year} 年经济数据摘要 ===
{report_text}

关键数据：
- 就业率: {latest.get('employment_rate', 0)*100:.1f}%
- 平均工资: {latest.get('avg_wage', 0):.1f}
- 银行贷款利率: {latest.get('loan_rate', 0)*100:.2f}%
- 工厂平均利润率: {latest.get('avg_profit_margin', 0)*100:.1f}%
- 基尼系数: {latest.get('gini_coefficient', 0):.3f}
- 净外部资金流入: {latest.get('net_external_inflow', 0):.1f}

请直接给出分析，不要重复数据。"""

    def _build_alert_prompt(self, alerts: list[str], last_n: int = 3) -> str:
        """构建异常预警分析 Prompt"""
        report_text = self.stats.summary_report(last_n=last_n)
        alert_text = "\n".join(alerts)
        return f"""小镇经济出现以下异常预警：
{alert_text}

最近 {last_n} 个月经济数据：
{report_text}

请用 150 字以内分析：异常的可能原因是什么？会带来什么连锁反应？最紧急的应对措施是什么？"""

    def _build_worker_story_prompt(self, worker_data: dict) -> str:
        """为某个工人生成一段生活叙述"""
        status = "在职" if worker_data.get("employed") else "失业"
        return f"""请用第三人称，用 100 字以内，生动描述这位小镇工人这个月的生活：
- 就业状态: {status}
- 工资收入: {worker_data.get('wage', 0):.1f}
- 存款余额: {worker_data.get('savings', 0):.1f}
- 本地消费: {worker_data.get('local_spend', 0):.1f}

不要虚构数据，基于以上信息描述即可。"""

    def annual_report(self, month: int) -> str:
        """生成年度经济报告"""
        year = month // 12
        prompt = self._build_annual_prompt(year)
        analysis = _ollama_chat(prompt, model=self.model)
        report = {
            "type": "annual",
            "month": month,
            "year": year,
            "content": analysis,
        }
        self.reports.append(report)
        return analysis

    def alert_analysis(self, alerts: list[str]) -> str:
        """分析异常预警"""
        if not alerts:
            return ""
        prompt = self._build_alert_prompt(alerts)
        analysis = _ollama_chat(prompt, model=self.model)
        report = {
            "type": "alert",
            "month": self.stats.latest().get("month", 0),
            "alerts": alerts,
            "content": analysis,
        }
        self.reports.append(report)
        return analysis

    def worker_story(self, worker_snapshot: dict) -> str:
        """为工人生成生活叙述"""
        prompt = self._build_worker_story_prompt(worker_snapshot)
        return _ollama_chat(prompt, model=self.model)

    def should_run_annual(self, month: int) -> bool:
        return month > 0 and month % LLM_ANNUAL_REPORT_INTERVAL == 0

    def should_run_alert(self, alerts: list[str]) -> bool:
        return len(alerts) > 0
