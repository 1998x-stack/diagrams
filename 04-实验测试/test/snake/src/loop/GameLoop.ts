import type { GameState } from '../types.ts'
import type { InputManager } from '../input/InputManager.ts'
import { tick, setNextDirection } from '../core/GameEngine.ts'
import { transition } from '../core/fsm.ts'
import { createInitialState } from '../core/GameState.ts'

type RenderFn = (state: GameState) => void

export class GameLoop {
  private state: GameState
  private input: InputManager
  private render: RenderFn

  private rafId: number = 0
  private lastTickTime: number = 0
  private running: boolean = false

  constructor(input: InputManager, render: RenderFn) {
    this.input = input
    this.render = render
    this.state = createInitialState()

    // 监听动作键（Space / Enter / Escape）
    this.input.onAction = (key) => { this.handleAction(key) }
  }

  getState(): GameState {
    return this.state
  }

  setState(state: GameState): void {
    this.state = state
  }

  /**
   * 启动游戏循环（rAF 驱动渲染，累积时间驱动 tick）
   */
  start(): void {
    if (this.running) return
    this.running = true
    this.lastTickTime = performance.now()
    this.loop(performance.now())
  }

  stop(): void {
    this.running = false
    cancelAnimationFrame(this.rafId)
  }

  private loop(now: number): void {
    if (!this.running) return

    // --- Tick 逻辑（固定步长）---
    if (this.state.phase === 'RUNNING') {
      const elapsed = now - this.lastTickTime
      if (elapsed >= this.state.config.tickInterval) {
        this.lastTickTime = now - (elapsed % this.state.config.tickInterval)

        // 消费输入方向
        const dir = this.input.consume()
        if (dir) {
          this.state = setNextDirection(this.state, dir)
        }

        this.state = tick(this.state)
      }
    }

    // --- Render（每帧）---
    this.render(this.state)

    this.rafId = requestAnimationFrame((t) => this.loop(t))
  }

  handleAction(key: string): void {
    switch (key) {
      case ' ':
      case 'Enter':
        if (this.state.phase === 'IDLE') {
          this.state = { ...this.state, phase: transition(this.state.phase, 'START') }
        } else if (this.state.phase === 'GAME_OVER' || this.state.phase === 'WIN') {
          const highScore = this.state.highScore
          this.state = { ...createInitialState(this.state.config), highScore }
          this.input.reset()
        }
        break
      case 'Escape':
        if (this.state.phase === 'RUNNING') {
          this.state = { ...this.state, phase: transition(this.state.phase, 'PAUSE') }
        } else if (this.state.phase === 'PAUSED') {
          this.state = { ...this.state, phase: transition(this.state.phase, 'RESUME') }
          this.lastTickTime = performance.now() // 重置 tick 基准，避免暂停后瞬间多 tick
        }
        break
    }
  }
}
