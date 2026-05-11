import type { GameState } from '../types.ts'
import { CELL_SIZE, COLORS } from '../constants.ts'

export class FoodRenderer {
  render(ctx: CanvasRenderingContext2D, state: GameState): void {
    const { food, tickCount } = state
    const cs = CELL_SIZE

    // 脉冲动画：每 30 tick 完成一次 scale 0.8 → 1.2 → 0.8
    const pulse = tickCount % 30
    const scale = pulse < 15
      ? 0.8 + (pulse / 15) * 0.4      // 0.8 → 1.2
      : 1.2 - ((pulse - 15) / 15) * 0.4 // 1.2 → 0.8

    const cx = food.x * cs + cs / 2
    const cy = food.y * cs + cs / 2
    const radius = (cs / 2 - 2) * scale

    ctx.fillStyle = COLORS.FOOD
    ctx.beginPath()
    ctx.arc(cx, cy, radius, 0, Math.PI * 2)
    ctx.fill()
  }
}
