/**
 * 渲染层单元测试
 *
 * Canvas 不在 node 环境中原生可用，使用轻量 mock 验证：
 *   1. 各子渲染器被正确调用（调用追踪）
 *   2. UIRenderer 在各 phase 输出正确文字
 *   3. FoodRenderer 脉冲动画 scale 边界值
 */
import { describe, expect, it, vi, beforeEach } from 'vitest'
import type { GameState } from '../src/types.ts'
import { UIRenderer } from '../src/render/UIRenderer.ts'
import { FoodRenderer } from '../src/render/FoodRenderer.ts'
import { SnakeRenderer } from '../src/render/SnakeRenderer.ts'
import { CELL_SIZE } from '../src/constants.ts'

// 构造 canvas 2D context mock
function makeCtx() {
  const calls: string[] = []
  const texts: string[] = []

  const ctx = {
    fillStyle: '',
    strokeStyle: '',
    lineWidth: 0,
    font: '',
    textAlign: '',
    fillRect: vi.fn((...args: number[]) => calls.push(`fillRect(${args.join(',')})`)),
    strokeRect: vi.fn(),
    clearRect: vi.fn(),
    beginPath: vi.fn(),
    arc: vi.fn(),
    fill: vi.fn(),
    stroke: vi.fn(),
    moveTo: vi.fn(),
    lineTo: vi.fn(),
    fillText: vi.fn((...args: unknown[]) => texts.push(String(args[0]))),
    scale: vi.fn(),
  } as unknown as CanvasRenderingContext2D & { _calls: string[]; _texts: string[] }

  ;(ctx as unknown as { _calls: string[]; _texts: string[] })._calls = calls
  ;(ctx as unknown as { _texts: string[] })._texts = texts

  return ctx
}

function makeState(overrides: Partial<GameState> = {}): GameState {
  return {
    snake: [{ x: 2, y: 2 }, { x: 1, y: 2 }],
    food: { x: 4, y: 4 },
    direction: 'RIGHT',
    nextDirection: 'RIGHT',
    phase: 'RUNNING',
    score: 0,
    highScore: 0,
    tickCount: 0,
    config: { tickInterval: 130, gridSize: 5, initialLength: 3 },
    ...overrides,
  }
}

describe('UIRenderer', () => {
  let ui: UIRenderer
  let ctx: ReturnType<typeof makeCtx>

  beforeEach(() => {
    ui = new UIRenderer()
    ctx = makeCtx()
  })

  it('RUNNING：显示 SCORE 和 BEST，无遮罩 fillRect（整屏覆盖）', () => {
    ui.render(ctx, makeState({ phase: 'RUNNING', score: 10, highScore: 50 }))
    const texts = (ctx as unknown as { _texts: string[] })._texts
    expect(texts.some(t => t.includes('10'))).toBe(true)
    expect(texts.some(t => t.includes('50'))).toBe(true)
  })

  it('IDLE：显示 SNAKE 标题和提示文字', () => {
    ui.render(ctx, makeState({ phase: 'IDLE' }))
    const texts = (ctx as unknown as { _texts: string[] })._texts
    expect(texts).toContain('SNAKE')
    expect(texts.some(t => t.includes('SPACE'))).toBe(true)
  })

  it('PAUSED：显示 PAUSED', () => {
    ui.render(ctx, makeState({ phase: 'PAUSED' }))
    const texts = (ctx as unknown as { _texts: string[] })._texts
    expect(texts).toContain('PAUSED')
  })

  it('GAME_OVER：显示 GAME OVER', () => {
    ui.render(ctx, makeState({ phase: 'GAME_OVER' }))
    const texts = (ctx as unknown as { _texts: string[] })._texts
    expect(texts).toContain('GAME OVER')
  })

  it('WIN：显示 YOU WIN!', () => {
    ui.render(ctx, makeState({ phase: 'WIN' }))
    const texts = (ctx as unknown as { _texts: string[] })._texts
    expect(texts).toContain('YOU WIN!')
  })
})

describe('FoodRenderer 脉冲动画', () => {
  it('tickCount=0：scale=0.8，arc 调用半径为最小值', () => {
    const food = new FoodRenderer()
    const ctx = makeCtx()
    food.render(ctx, makeState({ tickCount: 0 }))
    expect((ctx.arc as ReturnType<typeof vi.fn>).mock.calls.length).toBe(1)
  })

  it('tickCount=15：scale=1.2，最大半径', () => {
    const food = new FoodRenderer()
    const ctx = makeCtx()
    food.render(ctx, makeState({ tickCount: 15 }))
    const arcCall = (ctx.arc as ReturnType<typeof vi.fn>).mock.calls[0] as number[]
    // radius = (CELL_SIZE/2 - 2) * 1.2
    const expectedRadius = (CELL_SIZE / 2 - 2) * 1.2
    expect(arcCall[2]).toBeCloseTo(expectedRadius, 2)
  })
})

describe('SnakeRenderer', () => {
  it('渲染蛇：调用 fillRect 次数 = 蛇身长度 + 2 个眼睛', () => {
    const snake = new SnakeRenderer()
    const ctx = makeCtx()
    const state = makeState({
      snake: [{ x: 2, y: 2 }, { x: 1, y: 2 }, { x: 0, y: 2 }],
    })
    snake.render(ctx, state)
    // 3 节蛇身 + 2 只眼睛 = 5 次 fillRect
    expect((ctx.fillRect as ReturnType<typeof vi.fn>).mock.calls.length).toBe(5)
  })

  it('空蛇：不调用任何 fillRect', () => {
    const snake = new SnakeRenderer()
    const ctx = makeCtx()
    snake.render(ctx, makeState({ snake: [] }))
    expect((ctx.fillRect as ReturnType<typeof vi.fn>).mock.calls.length).toBe(0)
  })
})
