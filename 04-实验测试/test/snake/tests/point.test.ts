import { describe, expect, it } from 'vitest'
import { addPoint, buildSnakeSet, isInBounds, pointEquals, serializePoint } from '../src/utils/point.ts'

describe('point utils', () => {
  it('pointEquals: same coords → true', () => {
    expect(pointEquals({ x: 3, y: 5 }, { x: 3, y: 5 })).toBe(true)
  })

  it('pointEquals: different coords → false', () => {
    expect(pointEquals({ x: 3, y: 5 }, { x: 3, y: 6 })).toBe(false)
  })

  it('serializePoint: formats as "x,y"', () => {
    expect(serializePoint({ x: 2, y: 7 })).toBe('2,7')
  })

  it('addPoint: adds coordinates', () => {
    expect(addPoint({ x: 1, y: 2 }, { x: 3, y: -1 })).toEqual({ x: 4, y: 1 })
  })

  it('buildSnakeSet: contains all serialized points', () => {
    const snake = [{ x: 0, y: 0 }, { x: 1, y: 0 }, { x: 2, y: 0 }]
    const set = buildSnakeSet(snake)
    expect(set.has('0,0')).toBe(true)
    expect(set.has('1,0')).toBe(true)
    expect(set.has('2,0')).toBe(true)
    expect(set.has('3,0')).toBe(false)
  })

  it('isInBounds: inside grid → true', () => {
    expect(isInBounds({ x: 0, y: 0 }, 10)).toBe(true)
    expect(isInBounds({ x: 9, y: 9 }, 10)).toBe(true)
  })

  it('isInBounds: outside grid → false', () => {
    expect(isInBounds({ x: -1, y: 0 }, 10)).toBe(false)
    expect(isInBounds({ x: 10, y: 0 }, 10)).toBe(false)
    expect(isInBounds({ x: 0, y: 10 }, 10)).toBe(false)
  })
})
