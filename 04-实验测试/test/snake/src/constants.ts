import type { Difficulty, Direction, DirectionVector } from './types.ts'

export const DIFFICULTIES: Record<string, Difficulty> = {
  EASY:   { tickInterval: 200, gridSize: 20, initialLength: 3 },
  NORMAL: { tickInterval: 130, gridSize: 25, initialLength: 4 },
  HARD:   { tickInterval: 80,  gridSize: 30, initialLength: 5 },
}

export const DEFAULT_DIFFICULTY = DIFFICULTIES['NORMAL']!

// 方向向量：RIGHT = +x, DOWN = +y（Canvas 坐标系）
export const DIRECTION_VECTORS: Record<Direction, DirectionVector> = {
  UP:    { dx: 0,  dy: -1 },
  DOWN:  { dx: 0,  dy:  1 },
  LEFT:  { dx: -1, dy:  0 },
  RIGHT: { dx:  1, dy:  0 },
}

// 180° 反向映射
export const OPPOSITE_DIRECTION: Record<Direction, Direction> = {
  UP:    'DOWN',
  DOWN:  'UP',
  LEFT:  'RIGHT',
  RIGHT: 'LEFT',
}

export const CELL_SIZE = 20 // px（逻辑尺寸）

export const COLORS = {
  BACKGROUND:   '#1a1a2e',
  GRID_LINE:    '#16213e',
  SNAKE_HEAD:   '#00ff88',
  SNAKE_TAIL:   '#004422',
  SNAKE_EYE:    '#ffffff',
  FOOD:         '#ff4455',
  TEXT:         '#ffffff',
  OVERLAY:      'rgba(0, 0, 0, 0.6)',
} as const
