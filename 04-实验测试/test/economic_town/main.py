#!/usr/bin/env python3
"""
封闭小镇经济体 Multi-Agent 仿真 —— 主入口

用法：
  python3 main.py                    # 自主运行直到经济崩溃
  python3 main.py --months 60        # 固定 60 个月（旧模式）
  python3 main.py --no-llm           # 跳过 LLM 分析（更快）
  python3 main.py --verbose          # 每月打印详细状态
  python3 main.py --seed 123         # 指定随机种子

运行模式：
  autonomous（默认）：while True 直到三大终止条件触发
    - 银行资本金崩溃
    - 所有工厂破产
    - 失业率连续 6 个月 >= 60%
  fixed：固定月数，用于研究和对比
"""
import argparse
import os

from core.simulation import TownEconomy
from analysis.statistics import EconomyStats
from analysis.llm_analyst import LLMAnalyst, is_ollama_available
from analysis.visualizer import Visualizer
from config.params import SIMULATION_MONTHS, RANDOM_SEED


def main():
    parser = argparse.ArgumentParser(description="小镇经济体 Multi-Agent 仿真")
    parser.add_argument("--months", type=int, default=None,
                        help="固定运行月数（不设则自主运行至崩溃）")
    parser.add_argument("--seed",       type=int,  default=RANDOM_SEED)
    parser.add_argument("--no-llm",     action="store_true", help="跳过 LLM 分析")
    parser.add_argument("--verbose",    action="store_true", help="每月打印状态")
    parser.add_argument("--output-dir", default="data")
    args = parser.parse_args()

    autonomous = args.months is None

    print("=" * 65)
    print("  封闭小镇经济体 Multi-Agent 仿真")
    print("=" * 65)
    mode_str = "自主运行（直到崩溃）" if autonomous else f"固定 {args.months} 个月"
    print(f"  模式: {mode_str}  |  随机种子: {args.seed}")

    # ── 初始化 ─────────────────────────────────────────────
    economy  = TownEconomy(seed=args.seed)
    stats    = EconomyStats(economy)
    economist = economy.economist

    use_llm = not args.no_llm
    analyst = None
    if use_llm:
        if is_ollama_available():
            print("  LLM: qwen2.5:0.5b（ollama 本地）")
            analyst = LLMAnalyst(stats)
        else:
            print("  ⚠  ollama 不可用，LLM 已禁用")
            use_llm = False
    else:
        print("  LLM: 已禁用（--no-llm）")
    print()

    os.makedirs(args.output_dir, exist_ok=True)

    # ── 自主模式（while True 直到崩溃）───────────────────────
    if autonomous:
        print("开始自主仿真...\n")

        def on_step(month: int, snapshot: dict, diag):
            llm_outputs = snapshot.get("llm_outputs", {})

            if args.verbose:
                strat = " | ".join(
                    f"{f.name}:{f.goals.current_strategy[0].upper()}"
                    for f in economy.factories if not f.is_bankrupt
                )
                print(f"  [{month:4d}月] {economy.status_summary()}")
                print(f"         经济学家: [{diag.phase}] 风险{diag.risk.total:.0f} | 策略: {strat}")
                if diag.warnings:
                    print(f"         ⚠  {' | '.join(diag.warnings)}")

            # 展示经济学家 LLM 结论
            if "economist" in llm_outputs:
                print(f"\n{economist.format_diagnosis(diag)}\n")

            # 展示银行 LLM 信贷政策
            if "bank" in llm_outputs:
                print(f"\n  [银行信贷政策 LLM建议] {llm_outputs['bank']}\n")

            # 展示工厂 LLM 策略复盘
            for key, text in llm_outputs.items():
                if key.startswith("factory_"):
                    fid = int(key.split("_")[1])
                    fname = economy.factories[fid].name
                    print(f"\n  [{fname} 季度复盘] {text}\n")

            # 展示年报
            if "annual" in llm_outputs:
                year = month // 12
                print(f"\n{'─'*65}")
                print(f"  ★ 第{year}年 宏观年报")
                print(f"{'─'*65}")
                print(llm_outputs["annual"])
                print()

            # 失业率预警（非 verbose 也显示）
            if not args.verbose and diag.warnings:
                print(f"  [{month:4d}月] [{diag.phase}] ⚠ {' | '.join(diag.warnings)}")

        termination = economy.run_until_termination(
            stats=stats,
            on_step=on_step,
            use_llm=use_llm,
            llm_analyst=analyst,
        )

        # ── 打印终止原因 ──────────────────────────────
        print("\n" + "=" * 65)
        print("  ★ 经济体终止运行")
        print("=" * 65)
        print(f"  原因: {termination.description}")
        print(f"  共运行: {termination.month} 个月")
        print(f"  终止代码: {termination.reason}")
        if economy.terminator.unemployment_streak > 0:
            print(f"  连续高失业月数: {economy.terminator.unemployment_streak}")

    # ── 固定月数模式 ───────────────────────────────────────
    else:
        print(f"开始仿真（{args.months} 个月）...\n")

        def on_step_fixed(month: int, snapshot: dict):
            metrics = stats.update(snapshot)
            diag    = economy.run_economist(metrics)

            if args.verbose:
                print(f"  [{month:3d}月] {economy.status_summary()} | [{diag.phase}] 风险{diag.risk.total:.0f}")
                if diag.warnings:
                    print(f"         ⚠  {' | '.join(diag.warnings)}")

            if use_llm and economist.should_trigger_llm(month):
                economist.conclude(diag)
                print(f"\n{economist.format_diagnosis(diag)}\n")

            if use_llm and analyst and analyst.should_run_annual(month):
                year = month // 12
                print(f"\n{'─'*65}")
                print(f"  ★ 第{year}年 宏观年报")
                print(f"{'─'*65}")
                print(analyst.annual_report(month))
                print()

        economy.run(args.months, on_step=on_step_fixed)

    # ── 最终统计 ─────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("  仿真结束 — 最终经济状况")
    print("=" * 65)
    print(stats.summary_report())

    # 经济学家最终 LLM 综合结论
    if use_llm and economist.diagnoses:
        final_diag = economist.latest_diagnosis()
        phases     = economist.phase_history()
        final_diag.phase_reason += f"；全程阶段：{_summarize_phases(phases)}"
        print(f"\n{'='*65}")
        print("  经济学家 · 最终综合结论")
        print(f"{'='*65}")
        print(economist.conclude(final_diag))
        print()

    # ── 导出数据 + 图表 ────────────────────────────────────
    csv_path = os.path.join(args.output_dir, "simulation_results.csv")
    stats.export_csv(csv_path)
    print(f"  数据已导出: {csv_path}")

    viz = Visualizer(stats, output_dir=os.path.join(args.output_dir, "charts"))
    chart_paths = viz.plot_all()
    print("  图表已生成:")
    for p in chart_paths:
        print(f"    {p}")
    print("\n  仿真完成！")


def _summarize_phases(phases: list[str]) -> str:
    """将阶段序列压缩，如 '扩张×3→稳态×20→...' """
    if not phases:
        return ""
    result, cur, count = [], phases[0], 1
    for p in phases[1:]:
        if p == cur:
            count += 1
        else:
            result.append(f"{cur}×{count}" if count > 1 else cur)
            cur, count = p, 1
    result.append(f"{cur}×{count}" if count > 1 else cur)
    return " → ".join(result)


if __name__ == "__main__":
    main()
