import type { Direction, GameState } from '../types.ts'
import { DIRECTION_VECTORS } from '../constants.ts'
import { addPoint, buildSnakeSet, isInBounds, pointEquals, serializePoint } from '../utils/point.ts'
import { randomFreePoint } from '../utils/random.ts'
import { transition } from './fsm.ts'

/**
 * 执行一次 tick。
 * 纯函数：输入旧状态，输出新状态（不可变更新）。
 */
export function tick(state: GameState): GameState {
  if (state.phase !== 'RUNNING') return state

  // 应用缓冲方向
  const direction = state.nextDirection
  const vec = DIRECTION_VECTORS[direction]
  const head = state.snake[0]!
  const newHead = addPoint(head, { x: vec.dx, y: vec.dy })

  // 墙壁碰撞
  if (!isInBounds(newHead, state.config.gridSize)) {
    return {
      ...state,
      direction,
      phase: transition(state.phase, 'COLLIDE'),
      highScore: Math.max(state.score, state.highScore),
      tickCount: state.tickCount + 1,
    }
  }

  // 自身碰撞（排除蛇尾，因为尾部会移走）
  const bodyWithoutTail = state.snake.slice(0, -1)
  const bodySet = buildSnakeSet(bodyWithoutTail)
  if (bodySet.has(serializePoint(newHead))) {
    return {
      ...state,
      direction,
      phase: transition(state.phase, 'COLLIDE'),
      highScore: Math.max(state.score, state.highScore),
      tickCount: state.tickCount + 1,
    }
  }

  // 判断是否吃到食物
  const ate = pointEquals(newHead, state.food)

  let newSnake: typeof state.snake
  if (ate) {
    // 吃食物：头部 push，保留蛇尾（蛇身增长）
    newSnake = [newHead, ...state.snake]
  } else {
    // 正常移动：头部 push，去掉蛇尾
    newSnake = [newHead, ...state.snake.slice(0, -1)]
  }

  // 生成新食物
  let newFood = state.food
  let newScore = state.score
  if (ate) {
    newScore = state.score + 10
    const occupied = buildSnakeSet(newSnake)
    try {
      newFood = randomFreePoint(state.config.gridSize, occupied)
    } catch {
      // 无空格可放 → 胜利
      return {
        ...state,
        snake: newSnake,
        direction,
        score: newScore,
        highScore: Math.max(newScore, state.highScore),
        phase: transition(state.phase, 'WIN'),
        tickCount: state.tickCount + 1,
      }
    }
  }

  // 蛇填满整个地图 → 胜利
  const totalCells = state.config.gridSize * state.config.gridSize
  const phase =
    newSnake.length === totalCells
      ? transition(state.phase, 'WIN')
      : state.phase

  return {
    ...state,
    snake: newSnake,
    food: newFood,
    direction,
    score: newScore,
    highScore: Math.max(newScore, state.highScore),
    phase,
    tickCount: state.tickCount + 1,
  }
}

/**
 * 更新下一帧生效方向（防 180° 反转由 InputManager 负责）。
 */
export function setNextDirection(state: GameState, dir: Direction): GameState {
  return { ...state, nextDirection: dir }
}
