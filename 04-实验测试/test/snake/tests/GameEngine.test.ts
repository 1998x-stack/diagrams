import { describe, expect, it } from 'vitest'
import type { GameState } from '../src/types.ts'
import { tick, setNextDirection } from '../src/core/GameEngine.ts'

// 辅助：构造最小测试状态（5×5 网格）
function makeState(overrides: Partial<GameState> = {}): GameState {
  const config = { tickInterval: 130, gridSize: 5, initialLength: 3 }
  return {
    snake: [{ x: 2, y: 2 }, { x: 1, y: 2 }, { x: 0, y: 2 }],
    food: { x: 4, y: 4 },
    direction: 'RIGHT',
    nextDirection: 'RIGHT',
    phase: 'RUNNING',
    score: 0,
    highScore: 0,
    tickCount: 0,
    config,
    ...overrides,
  }
}

describe('GameEngine.tick', () => {
  it('正常移动：蛇头向右移一格，蛇尾缩短', () => {
    const state = makeState()
    const next = tick(state)
    expect(next.snake[0]).toEqual({ x: 3, y: 2 })
    expect(next.snake.length).toBe(3)
    expect(next.tickCount).toBe(1)
  })

  it('非 RUNNING 状态：tick 不改变任何东西', () => {
    const state = makeState({ phase: 'PAUSED' })
    const next = tick(state)
    expect(next).toBe(state) // 同一引用
  })

  it('应用 nextDirection：tick 时切换为 nextDirection', () => {
    const state = makeState({ nextDirection: 'UP' })
    const next = tick(state)
    expect(next.direction).toBe('UP')
    expect(next.snake[0]).toEqual({ x: 2, y: 1 })
  })

  it('墙壁碰撞：撞右墙 → GAME_OVER', () => {
    // 蛇头在 (4,2)，方向 RIGHT，gridSize=5
    const state = makeState({
      snake: [{ x: 4, y: 2 }, { x: 3, y: 2 }, { x: 2, y: 2 }],
      direction: 'RIGHT',
      nextDirection: 'RIGHT',
    })
    const next = tick(state)
    expect(next.phase).toBe('GAME_OVER')
  })

  it('墙壁碰撞：撞上墙 → GAME_OVER', () => {
    const state = makeState({
      snake: [{ x: 2, y: 0 }, { x: 2, y: 1 }, { x: 2, y: 2 }],
      direction: 'UP',
      nextDirection: 'UP',
    })
    const next = tick(state)
    expect(next.phase).toBe('GAME_OVER')
  })

  it('自身碰撞：头撞入蛇身 → GAME_OVER', () => {
    // 构造 U 形蛇：头(2,2) → (3,2) → (3,3) → (2,3) → (1,3)
    // 下一步 UP：头移到 (2,1)... 不碰撞，换个场景
    // 构造：头(2,2) 右移会碰到 (3,2)（蛇身第二节）
    // 实际自碰：snake = [(2,2),(1,2),(1,1),(2,1),(3,1),(3,2)]，方向 RIGHT → 头到(3,2)= 蛇身最后一节
    // 碰撞检测排除蛇尾（最后一节），所以蛇身 slice(0,-1)，蛇尾(3,2)被排除，不触发碰撞
    // 换个简单场景：
    // snake = [(2,2),(3,2),(3,1),(2,1),(2,2)]... 会有重复，非法蛇身
    // 用确定可触发的场景：
    // snake = [(1,2),(2,2),(3,2),(3,1),(2,1)], direction=LEFT → 头到(0,2)，OK
    // snake = [(2,2),(1,2),(1,1),(2,1),(3,1),(3,2),(3,3)], nextDirection=DOWN → 头到(2,3)
    // 直接测：snake = [(2,2),(2,1),(1,1),(1,2),(1,3)], direction=DOWN → 头到(2,3)，无碰
    // 简化：蛇形成圈，头部下一步命中 slice(0,-1) 中的某节
    const state = makeState({
      snake: [
        { x: 2, y: 2 },
        { x: 2, y: 1 },
        { x: 1, y: 1 },
        { x: 1, y: 2 },
        { x: 1, y: 3 }, // 蛇尾
      ],
      direction: 'LEFT',
      nextDirection: 'LEFT',
      food: { x: 4, y: 0 },
    })
    // 向左移 → 头到 (1,2)，该点在 slice(0,-1) = [(2,1),(1,1),(1,2)]... 在！
    const next = tick(state)
    expect(next.phase).toBe('GAME_OVER')
  })

  it('吃到食物：蛇身增长 1，分数 +10，生成新食物', () => {
    // 蛇头在(3,2)，食物在(4,2)，方向 RIGHT
    const state = makeState({
      snake: [{ x: 3, y: 2 }, { x: 2, y: 2 }, { x: 1, y: 2 }],
      food: { x: 4, y: 2 },
      direction: 'RIGHT',
      nextDirection: 'RIGHT',
    })
    const next = tick(state)
    expect(next.snake.length).toBe(4)
    expect(next.snake[0]).toEqual({ x: 4, y: 2 })
    expect(next.score).toBe(10)
    // 新食物不在蛇身上
    const snakeKeys = new Set(next.snake.map(p => `${p.x},${p.y}`))
    expect(snakeKeys.has(`${next.food.x},${next.food.y}`)).toBe(false)
  })

  it('highScore 更新：游戏结束时保留最高分', () => {
    const state = makeState({
      snake: [{ x: 4, y: 2 }, { x: 3, y: 2 }, { x: 2, y: 2 }],
      direction: 'RIGHT',
      nextDirection: 'RIGHT',
      score: 50,
      highScore: 30,
    })
    const next = tick(state)
    expect(next.phase).toBe('GAME_OVER')
    expect(next.highScore).toBe(50)
  })
})

describe('GameEngine.setNextDirection', () => {
  it('更新 nextDirection', () => {
    const state = makeState()
    const next = setNextDirection(state, 'UP')
    expect(next.nextDirection).toBe('UP')
    expect(next.direction).toBe('RIGHT') // 当前方向不变
  })
})
