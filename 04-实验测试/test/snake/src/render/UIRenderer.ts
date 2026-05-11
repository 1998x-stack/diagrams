import type { GameState } from '../types.ts'
import { CELL_SIZE, COLORS } from '../constants.ts'

export class UIRenderer {
  render(ctx: CanvasRenderingContext2D, state: GameState): void {
    const { phase, score, highScore, config } = state
    const canvasSize = config.gridSize * CELL_SIZE

    // 分数
    ctx.fillStyle = COLORS.TEXT
    ctx.font = 'bold 14px monospace'
    ctx.textAlign = 'left'
    ctx.fillText(`SCORE: ${score}`, 8, 18)
    ctx.textAlign = 'right'
    ctx.fillText(`BEST: ${highScore}`, canvasSize - 8, 18)

    // 阶段遮罩
    switch (phase) {
      case 'IDLE':
        this.drawOverlay(ctx, canvasSize, 'SNAKE', 'Press SPACE to start')
        break
      case 'PAUSED':
        this.drawOverlay(ctx, canvasSize, 'PAUSED', 'Press ESC to resume')
        break
      case 'GAME_OVER':
        this.drawOverlay(ctx, canvasSize, 'GAME OVER', 'Press ENTER to restart')
        break
      case 'WIN':
        this.drawOverlay(ctx, canvasSize, 'YOU WIN!', 'Press ENTER to restart')
        break
    }
  }

  private drawOverlay(
    ctx: CanvasRenderingContext2D,
    size: number,
    title: string,
    subtitle: string,
  ): void {
    ctx.fillStyle = COLORS.OVERLAY
    ctx.fillRect(0, 0, size, size)

    const cx = size / 2

    ctx.fillStyle = COLORS.TEXT
    ctx.font = 'bold 32px monospace'
    ctx.textAlign = 'center'
    ctx.fillText(title, cx, size / 2 - 10)

    ctx.font = '16px monospace'
    ctx.fillText(subtitle, cx, size / 2 + 24)
  }
}
