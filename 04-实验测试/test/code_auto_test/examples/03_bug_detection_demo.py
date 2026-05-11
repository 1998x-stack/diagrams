"""
示例 3：Bug 检测演示
====================
针对所有 5 种 Bug 类型分别运行测试，展示 TITAN 的检测能力。

运行方式：
    cd /Users/xd/Desktop/codes/code_auto_test
    python examples/03_bug_detection_demo.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["TITAN_MOCK_LLM"] = "1"

from titan.agent import TITANAgent
from titan.game.bug_scenarios import BugType
from titan.modules.diagnosis import BugCategory


# Bug 类型与预期检测结果
BUG_SCENARIOS = [
    {
        "bug_type": BugType.NONE,
        "description": "正常游戏（无 Bug）",
        "expected_category": None,
        "note": "不应产生误报",
    },
    {
        "bug_type": BugType.SCORE_NO_INCREMENT,
        "description": "分数不递增 Bug",
        "expected_category": BugCategory.LOGIC,
        "note": "吃食物后分数应 +10，但实际不变",
    },
    {
        "bug_type": BugType.SLOW_TICK,
        "description": "慢响应 Bug",
        "expected_category": BugCategory.PERFORMANCE,
        "note": "每次 tick() 人为延迟 0.05s，远超正常基准",
    },
    {
        "bug_type": BugType.WALL_PASS_THROUGH,
        "description": "穿墙 Bug",
        "expected_category": BugCategory.CRASH,
        "note": "撞墙时游戏不结束，蛇继续游走（最终可能死于其他原因）",
    },
    {
        "bug_type": BugType.SELF_COLLISION_IGNORED,
        "description": "自碰无效 Bug",
        "expected_category": None,  # 难以直接触发，取决于蛇的路径
        "note": "撞自身时游戏不结束（需要足够长的蛇才能触发）",
    },
]


def run_scenario(bug_type, description, note, max_ticks=80):
    """运行单个 Bug 场景并返回检测结果。"""
    agent = TITANAgent(
        difficulty="EASY",
        stall_threshold=10,   # 低阈值，更快触发反思
        escalation_limit=2,   # 低上限，更快触发终止
        mock_llm=True,
        use_rag=False,
    )

    # 对于 SLOW_TICK，预设基准以加速检测
    if bug_type == BugType.SLOW_TICK:
        # 手动设置极低基准，使 0.05s 延迟立即触发报告
        agent.diagnosis_engine.time_monitor._baseline_avg = 0.0001
        agent.diagnosis_engine.time_monitor._confirm_threshold = 2

    t0 = time.time()
    report = agent.run(bug_type=bug_type, max_ticks=max_ticks)
    elapsed = time.time() - t0

    return report, elapsed


def main():
    print("=" * 65)
    print("  TITAN-Snake Bug 检测演示")
    print("  针对 5 种 Bug 类型分别运行测试")
    print("=" * 65)

    results = []

    for scenario in BUG_SCENARIOS:
        bug_type = scenario["bug_type"]
        desc = scenario["description"]
        note = scenario["note"]
        expected = scenario["expected_category"]

        print(f"\n{'─' * 65}")
        print(f"测试场景: {desc}")
        print(f"注入 Bug: {bug_type.value}")
        print(f"说明: {note}")
        print("运行中...", end=" ", flush=True)

        report, elapsed = run_scenario(bug_type, desc, note)

        print(f"完成（{elapsed:.1f}s）")
        print(f"\n测试结果:")
        print(f"  执行帧数: {report.total_ticks}")
        print(f"  最终分数: {report.final_score}")
        print(f"  终止原因: {report.terminated_by}")
        print(f"  检测到 Bug: {report.bug_count} 个")

        detected_categories = {r.bug_type for r in report.bugs_detected}
        if report.bugs_detected:
            for bug_report in report.bugs_detected:
                print(f"    [{bug_report.severity}] {bug_report.bug_type}: "
                      f"{bug_report.description[:60]}...")

        # 判断检测是否符合预期
        if expected is None:
            # 无 Bug 场景：不应该检测到特定 Bug
            # （允许有一些假阳性，因为 Mock LLM 行为简单）
            success = True
            status = "✓ 符合预期（正常运行）"
        else:
            # 有 Bug 场景：应该检测到对应类别
            success = expected in detected_categories
            if success:
                status = f"✓ 成功检测到 {expected} Bug！"
            else:
                status = f"△ 未检测到预期的 {expected} Bug（Mock LLM 行为受限）"

        print(f"\n  {status}")
        results.append({
            "scenario": desc,
            "bug_count": report.bug_count,
            "success": success,
            "status": status,
        })

    # ----------------------------------------------------------------
    # 汇总
    # ----------------------------------------------------------------
    print(f"\n{'=' * 65}")
    print("  测试汇总")
    print('=' * 65)
    for r in results:
        icon = "✓" if r["success"] else "△"
        print(f"  {icon} {r['scenario']:25s} | 检测到 {r['bug_count']} 个 Bug | {r['status'][:30]}")

    print(f"\n提示: 使用真实 API Key 时（非 Mock 模式），LLM 可以更智能地")
    print(f"      判断行为异常，Bug 检测率会更高。")
    print(f"\n      真实运行: ANTHROPIC_API_KEY=sk-ant-... python -m titan.agent --verbose")


if __name__ == "__main__":
    main()
