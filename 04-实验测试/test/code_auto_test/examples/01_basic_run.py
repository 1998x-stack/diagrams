"""
示例 1：基础运行
================
演示如何启动 TITAN Agent，运行一次完整的测试会话。
无需 API Key（使用 Mock LLM 模式）。

运行方式：
    cd /Users/xd/Desktop/codes/code_auto_test
    python examples/01_basic_run.py
"""
import os
import sys

# 确保可以导入 titan 包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 使用 Mock 模式（无需真实 API Key）
os.environ["TITAN_MOCK_LLM"] = "1"

from titan.agent import TITANAgent
from titan.game.bug_scenarios import BugType


def main():
    print("=" * 60)
    print("TITAN-Snake 基础运行示例")
    print("=" * 60)

    # 创建 Agent（Mock LLM 模式）
    agent = TITANAgent(
        difficulty="EASY",
        stall_threshold=20,
        escalation_limit=3,
        mock_llm=True,
        use_rag=False,  # 示例中禁用 RAG 以加快速度
    )

    print("\n[1] 运行正常游戏（无 Bug）")
    print("-" * 40)
    report = agent.run(
        bug_type=BugType.NONE,
        max_ticks=100,
        verbose=True,
    )
    print("\n" + report.summary())

    print("\n[2] 运行注入 Bug 的游戏")
    print("-" * 40)
    print("注入 Bug: SCORE_NO_INCREMENT（吃食物分数不增加）")
    report = agent.run(
        bug_type=BugType.SCORE_NO_INCREMENT,
        max_ticks=100,
        verbose=True,
    )
    print("\n" + report.summary())

    if report.bug_count > 0:
        print(f"\n成功检测到 {report.bug_count} 个 Bug！")
        for i, bug in enumerate(report.bugs_detected, 1):
            print(f"  Bug #{i}: [{bug.severity}] {bug.bug_type} - {bug.description[:80]}...")
    else:
        print("\n本次运行未检测到 Bug（Mock LLM 可能未触发足够的停滞）")


if __name__ == "__main__":
    main()
