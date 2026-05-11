import type { GameState } from '../types.ts'
import { CELL_SIZE, COLORS } from '../constants.ts'

export class SnakeRenderer {
  render(ctx: CanvasRenderingContext2D, state: GameState): void {
    const { snake, direction } = state
    const n = snake.length
    if (n === 0) return

    const cs = CELL_SIZE

    for (let i = 0; i < n; i++) {
      const p = snake[i]!
      // 渐变：头部亮绿，尾部深绿
      const t = n === 1 ? 0 : i / (n - 1)
      ctx.fillStyle = lerpColor(COLORS.SNAKE_HEAD, COLORS.SNAKE_TAIL, t)
      ctx.fillRect(p.x * cs + 1, p.y * cs + 1, cs - 2, cs - 2)
    }

    // 蛇眼（仅绘制头部）
    const head = snake[0]!
    ctx.fillStyle = COLORS.SNAKE_EYE
    const eyeSize = 3
    const eyeOffset = 4

    // 根据方向决定眼睛位置
    const hx = head.x * cs
    const hy = head.y * cs
    let eye1x: number, eye1y: number, eye2x: number, eye2y: number

    switch (direction) {
      case 'RIGHT':
        eye1x = hx + cs - eyeOffset - eyeSize; eye1y = hy + eyeOffset
        eye2x = hx + cs - eyeOffset - eyeSize; eye2y = hy + cs - eyeOffset - eyeSize
        break
      case 'LEFT':
        eye1x = hx + eyeOffset; eye1y = hy + eyeOffset
        eye2x = hx + eyeOffset; eye2y = hy + cs - eyeOffset - eyeSize
        break
      case 'UP':
        eye1x = hx + eyeOffset;                eye1y = hy + eyeOffset
        eye2x = hx + cs - eyeOffset - eyeSize; eye2y = hy + eyeOffset
        break
      case 'DOWN':
        eye1x = hx + eyeOffset;                eye1y = hy + cs - eyeOffset - eyeSize
        eye2x = hx + cs - eyeOffset - eyeSize; eye2y = hy + cs - eyeOffset - eyeSize
        break
    }

    ctx.fillRect(eye1x, eye1y, eyeSize, eyeSize)
    ctx.fillRect(eye2x, eye2y, eyeSize, eyeSize)
  }
}

// 十六进制颜色线性插值
function lerpColor(a: string, b: string, t: number): string {
  const ra = parseInt(a.slice(1, 3), 16)
  const ga = parseInt(a.slice(3, 5), 16)
  const ba = parseInt(a.slice(5, 7), 16)
  const rb = parseInt(b.slice(1, 3), 16)
  const gb = parseInt(b.slice(3, 5), 16)
  const bb = parseInt(b.slice(5, 7), 16)

  const r = Math.round(ra + (rb - ra) * t)
  const g = Math.round(ga + (gb - ga) * t)
  const bl = Math.round(ba + (bb - ba) * t)

  return `rgb(${r},${g},${bl})`
}
