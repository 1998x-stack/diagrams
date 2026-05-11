import type { Point } from '../types.ts'

export function pointEquals(a: Point, b: Point): boolean {
  return a.x === b.x && a.y === b.y
}

export function serializePoint(p: Point): string {
  return `${p.x},${p.y}`
}

export function addPoint(a: Point, b: Point): Point {
  return { x: a.x + b.x, y: a.y + b.y }
}

export function buildSnakeSet(snake: Point[]): Set<string> {
  return new Set(snake.map(serializePoint))
}

export function isInBounds(p: Point, gridSize: number): boolean {
  return p.x >= 0 && p.x < gridSize && p.y >= 0 && p.y < gridSize
}
