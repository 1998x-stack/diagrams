import type { Difficulty, GameState, Point } from '../types.ts'
import { DEFAULT_DIFFICULTY } from '../constants.ts'
import { buildSnakeSet } from '../utils/point.ts'
import { randomFreePoint } from '../utils/random.ts'

function buildInitialSnake(config: Difficulty): Point[] {
  // 蛇初始水平居中，向右移动
  const midY = Math.floor(config.gridSize / 2)
  const startX = Math.floor(config.gridSize / 2)
  const snake: Point[] = []
  for (let i = 0; i < config.initialLength; i++) {
    snake.push({ x: startX - i, y: midY })
  }
  return snake
}

export function createInitialState(config: Difficulty = DEFAULT_DIFFICULTY): GameState {
  const snake = buildInitialSnake(config)
  const occupied = buildSnakeSet(snake)
  const food = randomFreePoint(config.gridSize, occupied)

  return {
    snake,
    food,
    direction: 'RIGHT',
    nextDirection: 'RIGHT',
    phase: 'IDLE',
    score: 0,
    highScore: 0,
    tickCount: 0,
    config,
  }
}
