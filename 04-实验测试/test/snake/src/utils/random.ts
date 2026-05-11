import type { Point } from '../types.ts'

// [min, max) 随机整数
export function randInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min)) + min
}

/**
 * 在网格内随机生成一个不在排除集合中的点。
 * 策略 A：随机重试（蛇短时高效）
 * 策略 B：穷举空格后随机取（超过 10 次重试时自动切换）
 */
export function randomFreePoint(gridSize: number, occupied: Set<string>): Point {
  const totalCells = gridSize * gridSize
  const freeCells = totalCells - occupied.size

  if (freeCells === 0) {
    throw new Error('No free cells available')
  }

  // 策略 A
  for (let i = 0; i < 10; i++) {
    const p: Point = { x: randInt(0, gridSize), y: randInt(0, gridSize) }
    if (!occupied.has(`${p.x},${p.y}`)) return p
  }

  // 策略 B
  const free: Point[] = []
  for (let y = 0; y < gridSize; y++) {
    for (let x = 0; x < gridSize; x++) {
      if (!occupied.has(`${x},${y}`)) free.push({ x, y })
    }
  }
  const idx = randInt(0, free.length)
  return free[idx]!
}
