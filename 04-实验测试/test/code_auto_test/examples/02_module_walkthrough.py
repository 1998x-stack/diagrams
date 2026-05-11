"""
示例 2：模块逐步演示
====================
逐步展示 TITAN 各模块的工作原理，帮助新手理解数据流。

运行方式：
    cd /Users/xd/Desktop/codes/code_auto_test
    python examples/02_module_walkthrough.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["TITAN_MOCK_LLM"] = "1"


def separator(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def main():
    # ----------------------------------------------------------------
    # Step 1: 游戏环境
    # ----------------------------------------------------------------
    separator("Step 1: 游戏环境（snake_env.py）")

    from titan.game.snake_env import (
        create_initial_state, set_phase, set_next_direction, tick, Point
    )

    state = create_initial_state("EASY")
    state = set_phase(state, "RUNNING")

    print(f"初始状态:")
    print(f"  网格大小: {state.config.grid_size}×{state.config.grid_size}")
    print(f"  蛇头位置: ({state.snake[0].x}, {state.snake[0].y})")
    print(f"  蛇身长度: {len(state.snake)} 节")
    print(f"  食物位置: ({state.food.x}, {state.food.y})")
    print(f"  当前方向: {state.direction}")
    print(f"  当前分数: {state.score}")
    print(f"  游戏阶段: {state.phase}")

    # 执行一步
    state = set_next_direction(state, "RIGHT")
    state = tick(state)
    print(f"\n执行 tick() 后:")
    print(f"  蛇头位置: ({state.snake[0].x}, {state.snake[0].y})  ← 向右移动1格")
    print(f"  tick_count: {state.tick_count}")

    # ----------------------------------------------------------------
    # Step 2: RAG 知识库
    # ----------------------------------------------------------------
    separator("Step 2: RAG 知识库（knowledge_base.py）")

    from titan.rag.knowledge_base import KnowledgeBase

    kb = KnowledgeBase()

    queries = [
        "danger ahead wall collision",
        "score food eaten",
        "game over win condition",
    ]

    for query in queries:
        results = kb.retrieve(query, top_k=2)
        print(f"\n查询: '{query}'")
        for r in results:
            print(f"  → {r[:80]}")

    # ----------------------------------------------------------------
    # Step 3: 感知抽象
    # ----------------------------------------------------------------
    separator("Step 3: 感知抽象（perception.py）")

    from titan.modules.perception import abstract, check_danger, estimate_open_space

    # 检查各方向危险
    print("危险检测（从当前蛇头位置）:")
    for direction in ["UP", "DOWN", "LEFT", "RIGHT"]:
        dangerous = check_danger(state, direction)
        status = "⚠️ 危险" if dangerous else "✓ 安全"
        print(f"  {direction:5s}: {status}")

    # 开放空间
    space = estimate_open_space(state)
    print(f"\n开放空间比例: {space:.1%}  （越高越不容易被困住）")

    # 完整抽象状态
    ab_state = abstract(state, knowledge_base=kb)
    print(f"\n抽象状态（LLM 可理解的符号表示）:")
    skip_keys = {"relevant_rules", "grid_size", "tick_count", "snake_length_raw",
                 "food_distance_raw"}
    for k, v in ab_state.items():
        if k not in skip_keys:
            print(f"  {k:20s}: {v}")

    if ab_state.get("relevant_rules"):
        print(f"\n  RAG 检索到的相关规则:")
        for rule in ab_state["relevant_rules"][:2]:
            print(f"    • {rule[:70]}")

    # ----------------------------------------------------------------
    # Step 4: 动作优化
    # ----------------------------------------------------------------
    separator("Step 4: 动作优化（action_opt.py）")

    from titan.modules.action_opt import recommend
    from titan.llm_client import LLMClient

    llm = LLMClient(mock=True)
    bundle = recommend(ab_state, state, llm_client=llm)

    print(f"推荐动作（按优先级）: {bundle.recommended}")
    print(f"所有安全动作:         {bundle.safe_actions}")
    print(f"\n推荐理由:")
    for part in bundle.reasoning.split("; "):
        print(f"  • {part}")

    # ----------------------------------------------------------------
    # Step 5: 反射推理
    # ----------------------------------------------------------------
    separator("Step 5: 反射推理（reflection.py）")

    from titan.modules.reflection import ReflectionEngine

    engine = ReflectionEngine(stall_threshold=5, escalation_limit=3)

    print("模拟5步相同状态（触发停滞检测）:")
    for i in range(6):
        # 第一步是新状态，第2-5步是重复 → 触发停滞
        stalled = engine.record_step(ab_state, "RIGHT", score=0, tick=i)
        indicator = "🔔 触发反思！" if stalled else ""
        print(f"  Step {i}: stall_count={engine.monitor.stall_count} {indicator}")

    # 模拟 LLM 反思
    llm.set_mock_response("ACTIONS: UP,LEFT\nIS_BUG: no\nREASON: Try different path")
    result = engine.reflect(ab_state, llm)
    print(f"\n反思结果:")
    print(f"  建议动作: {result.suggested_actions}")
    print(f"  疑似 Bug: {result.is_bug}")
    print(f"  原因分析: {result.reason}")
    print(f"  已反思次数: {engine.escalation_count}/{engine.escalation_limit}")

    # ----------------------------------------------------------------
    # Step 6: 问题诊断
    # ----------------------------------------------------------------
    separator("Step 6: 问题诊断（diagnosis.py）")

    from titan.modules.diagnosis import DiagnosisEngine, CrashMonitor

    engine = DiagnosisEngine()

    # 模拟意外崩溃：danger_ahead=False 但游戏结束
    from titan.game.snake_env import set_phase
    game_over_state = set_phase(state, "GAME_OVER")
    safe_ab_state = dict(ab_state)
    safe_ab_state["danger_ahead"] = False  # 感知认为安全

    # 替换为 confirm_count=1 的 monitor，立即确认
    engine.crash_monitor = CrashMonitor(confirm_count=1)

    print("场景: 感知模块认为前方安全，但游戏突然结束")
    reports = engine.check(
        state=game_over_state,
        abstract_state=safe_ab_state,
        action_history=[],
        tick_elapsed=0.001,
    )

    if reports:
        r = reports[0]
        print(f"\n检测到 Bug！")
        print(f"  类型: {r.bug_type}")
        print(f"  严重度: {r.severity}")
        print(f"  描述: {r.description[:100]}")
        print(f"  时间戳: {r.timestamp}")
    else:
        print("未检测到 Bug（可能需要更多轮次确认）")

    # ----------------------------------------------------------------
    # 总结
    # ----------------------------------------------------------------
    separator("完成！")
    print("上述步骤展示了 TITAN 的完整数据流：")
    print("  GameState → 感知抽象 → 动作优化 → LLM 决策 → 执行")
    print("                ↓                              ↓")
    print("           反射推理 ←←←←←←←←←←← 进度监控")
    print("                ↓")
    print("           问题诊断 → DiagnosisReport")


if __name__ == "__main__":
    main()
