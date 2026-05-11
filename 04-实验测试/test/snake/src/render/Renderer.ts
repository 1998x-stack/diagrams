import type { GameState } from '../types.ts'
import { CELL_SIZE, COLORS } from '../constants.ts'
import { SnakeRenderer } from './SnakeRenderer.ts'
import { FoodRenderer } from './FoodRenderer.ts'
import { UIRenderer } from './UIRenderer.ts'

export class Renderer {
  private canvas: HTMLCanvasElement
  private ctx: CanvasRenderingContext2D
  private dpr: number

  private snakeRenderer = new SnakeRenderer()
  private foodRenderer = new FoodRenderer()
  private uiRenderer = new UIRenderer()

  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas
    const ctx = canvas.getContext('2d')
    if (!ctx) throw new Error('Cannot get 2D context')
    this.ctx = ctx
    this.dpr = window.devicePixelRatio ?? 1
  }

  /**
   * 根据配置调整 canvas 物理/逻辑尺寸（首次或重启时调用）
   */
  resize(gridSize: number): void {
    const logicalSize = gridSize * CELL_SIZE
    this.canvas.width = logicalSize * this.dpr
    this.canvas.height = logicalSize * this.dpr
    this.canvas.style.width = `${logicalSize}px`
    this.canvas.style.height = `${logicalSize}px`
    this.ctx.scale(this.dpr, this.dpr)
  }

  render(state: GameState): void {
    const size = state.config.gridSize * CELL_SIZE
    const ctx = this.ctx

    // 清空
    ctx.fillStyle = COLORS.BACKGROUND
    ctx.fillRect(0, 0, size, size)

    // 网格线
    this.drawGrid(ctx, state.config.gridSize)

    // 游戏元素
    if (state.phase !== 'IDLE') {
      this.foodRenderer.render(ctx, state)
      this.snakeRenderer.render(ctx, state)
    }

    // UI 遮罩 / 分数
    this.uiRenderer.render(ctx, state)
  }

  private drawGrid(ctx: CanvasRenderingContext2D, gridSize: number): void {
    ctx.strokeStyle = COLORS.GRID_LINE
    ctx.lineWidth = 0.5
    const cs = CELL_SIZE
    const total = gridSize * cs

    for (let i = 0; i <= gridSize; i++) {
      const pos = i * cs
      ctx.beginPath()
      ctx.moveTo(pos, 0)
      ctx.lineTo(pos, total)
      ctx.stroke()

      ctx.beginPath()
      ctx.moveTo(0, pos)
      ctx.lineTo(total, pos)
      ctx.stroke()
    }
  }
}
