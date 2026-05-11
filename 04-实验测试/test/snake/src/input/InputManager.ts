import type { Direction } from '../types.ts'
import { OPPOSITE_DIRECTION } from '../constants.ts'

const KEY_MAP: Record<string, Direction> = {
  ArrowUp:    'UP',
  ArrowDown:  'DOWN',
  ArrowLeft:  'LEFT',
  ArrowRight: 'RIGHT',
  w: 'UP',
  s: 'DOWN',
  a: 'LEFT',
  d: 'RIGHT',
}

const QUEUE_LIMIT = 2

export class InputManager {
  private queue: Direction[] = []
  private currentDirection: Direction = 'RIGHT'
  private listener: ((e: KeyboardEvent) => void) | null = null

  // 回调：非方向键（Space、Escape、Enter）
  onAction: ((key: string) => void) | null = null

  /**
   * 绑定到 window 键盘事件
   */
  attach(target: { addEventListener: Window['addEventListener'] }): void {
    this.listener = (e: KeyboardEvent) => this.handleKey(e)
    target.addEventListener('keydown', this.listener as EventListener)
  }

  /**
   * 解绑事件监听
   */
  detach(target: { removeEventListener: Window['removeEventListener'] }): void {
    if (this.listener) {
      target.removeEventListener('keydown', this.listener as EventListener)
      this.listener = null
    }
  }

  private handleKey(e: KeyboardEvent): void {
    const dir = KEY_MAP[e.key]
    if (dir) {
      e.preventDefault()
      this.enqueue(dir)
    } else if (this.onAction) {
      this.onAction(e.key)
    }
  }

  /**
   * 入队方向（防 180° 反转、防队列溢出）
   */
  enqueue(dir: Direction): void {
    // 参考基准：队列末尾已有方向，若无则参考当前生效方向
    const reference = this.queue.length > 0
      ? this.queue[this.queue.length - 1]!
      : this.currentDirection

    if (OPPOSITE_DIRECTION[dir] === reference) return // 180° 反转，拒绝
    if (this.queue.length >= QUEUE_LIMIT) return       // 队列已满，丢弃

    this.queue.push(dir)
  }

  /**
   * 消费队首方向（每 tick 调用一次）。
   * 若队列为空，返回 null（保持当前方向）。
   */
  consume(): Direction | null {
    const dir = this.queue.shift() ?? null
    if (dir) this.currentDirection = dir
    return dir
  }

  /**
   * 重置状态（游戏重新开始时调用）
   */
  reset(initialDirection: Direction = 'RIGHT'): void {
    this.queue = []
    this.currentDirection = initialDirection
  }

  /** 仅测试使用：查看当前队列 */
  _getQueue(): Direction[] {
    return [...this.queue]
  }
}
