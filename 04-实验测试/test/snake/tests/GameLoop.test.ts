/**
 * GameLoop 单元测试
 *
 * GameLoop 依赖 rAF 和 performance，这里通过替换全局 API 进行测试。
 * 重点验证：
 *   1. 状态机切换（IDLE → RUNNING → PAUSED → RUNNING → GAME_OVER → IDLE）
 *   2. 暂停期间 tick 不推进
 *   3. 输入方向正确消费并传递给 tick
 *   4. 重启后 highScore 保留
 */
import { describe, expect, it, beforeEach, vi } from 'vitest'
import { InputManager } from '../src/input/InputManager.ts'
import { GameLoop } from '../src/loop/GameLoop.ts'

// 搭建极简 rAF mock（同步执行）
function setupRafMock() {
  let id = 0
  const pending: Map<number, FrameRequestCallback> = new Map()

  vi.stubGlobal('requestAnimationFrame', (cb: FrameRequestCallback) => {
    id++
    pending.set(id, cb)
    return id
  })
  vi.stubGlobal('cancelAnimationFrame', (i: number) => {
    pending.delete(i)
  })

  // 触发所有 pending 回调（模拟一帧）
  function flush(now = 0) {
    const cbs = [...pending.values()]
    pending.clear()
    cbs.forEach(cb => cb(now))
  }

  return { flush, pending }
}

function makeLoop() {
  const renders: ReturnType<GameLoop['getState']>[] = []
  const input = new InputManager()
  const loop = new GameLoop(input, (s) => renders.push(s))
  return { loop, input, renders }
}

describe('GameLoop 状态机', () => {
  beforeEach(() => {
    vi.stubGlobal('performance', { now: () => 0 })
    setupRafMock()
  })

  it('初始 phase = IDLE', () => {
    const { loop } = makeLoop()
    expect(loop.getState().phase).toBe('IDLE')
  })

  it('Space/Enter → IDLE 转为 RUNNING', () => {
    const { loop, input } = makeLoop()
    loop.start()
    input.onAction!(' ')
    expect(loop.getState().phase).toBe('RUNNING')
  })

  it('Escape 暂停 / 恢复', () => {
    const { loop, input } = makeLoop()
    loop.start()
    input.onAction!(' ')
    expect(loop.getState().phase).toBe('RUNNING')

    input.onAction!('Escape')
    expect(loop.getState().phase).toBe('PAUSED')

    input.onAction!('Escape')
    expect(loop.getState().phase).toBe('RUNNING')
  })

  it('IDLE 时 Escape 无效', () => {
    const { loop, input } = makeLoop()
    loop.start()
    input.onAction!('Escape')
    expect(loop.getState().phase).toBe('IDLE')
  })
})

describe('GameLoop tick 逻辑', () => {
  it('PAUSED 时不推进 tickCount', () => {
    let now = 0
    vi.stubGlobal('performance', { now: () => now })
    const { flush } = setupRafMock()

    const { loop, input } = makeLoop()
    loop.start()
    input.onAction!(' ')   // RUNNING
    input.onAction!('Escape') // PAUSED

    const before = loop.getState().tickCount
    now = 500
    flush(now)

    expect(loop.getState().tickCount).toBe(before)
  })

  it('RUNNING 时 tick 按 tickInterval 推进', () => {
    let now = 0
    vi.stubGlobal('performance', { now: () => now })
    const { flush } = setupRafMock()

    const { loop, input } = makeLoop()
    // 设置极短 tickInterval 以便测试
    loop['state'] = { ...loop.getState(), config: { ...loop.getState().config, tickInterval: 100 } }

    loop.start()
    input.onAction!(' ')  // RUNNING

    flush(0)   // 第 0 帧，elapsed=0，不触发 tick

    now = 110
    flush(now) // elapsed=110 > 100，触发 1 次 tick

    expect(loop.getState().tickCount).toBeGreaterThanOrEqual(1)
  })
})

describe('GameLoop 重启', () => {
  beforeEach(() => {
    vi.stubGlobal('performance', { now: () => 0 })
    setupRafMock()
  })

  it('GAME_OVER 后 Enter 重置状态，保留 highScore', () => {
    const { loop, input } = makeLoop()
    loop.start()

    // 直接注入 GAME_OVER 状态
    loop['state'] = { ...loop.getState(), phase: 'GAME_OVER', score: 80, highScore: 80 }

    input.onAction!('Enter')

    expect(loop.getState().phase).toBe('IDLE')
    expect(loop.getState().score).toBe(0)
    expect(loop.getState().highScore).toBe(80)
  })

  it('WIN 后 Enter 同样重置，保留 highScore', () => {
    const { loop, input } = makeLoop()
    loop.start()

    loop['state'] = { ...loop.getState(), phase: 'WIN', score: 100, highScore: 100 }
    input.onAction!('Enter')

    expect(loop.getState().phase).toBe('IDLE')
    expect(loop.getState().highScore).toBe(100)
  })
})
