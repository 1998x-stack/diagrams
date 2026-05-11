import { describe, expect, it } from 'vitest'
import { transition } from '../src/core/fsm.ts'

describe('FSM transitions', () => {
  it('IDLE + START → RUNNING', () => {
    expect(transition('IDLE', 'START')).toBe('RUNNING')
  })

  it('RUNNING + PAUSE → PAUSED', () => {
    expect(transition('RUNNING', 'PAUSE')).toBe('PAUSED')
  })

  it('PAUSED + RESUME → RUNNING', () => {
    expect(transition('PAUSED', 'RESUME')).toBe('RUNNING')
  })

  it('RUNNING + COLLIDE → GAME_OVER', () => {
    expect(transition('RUNNING', 'COLLIDE')).toBe('GAME_OVER')
  })

  it('RUNNING + WIN → WIN', () => {
    expect(transition('RUNNING', 'WIN')).toBe('WIN')
  })

  it('GAME_OVER + RESTART → IDLE', () => {
    expect(transition('GAME_OVER', 'RESTART')).toBe('IDLE')
  })

  it('WIN + RESTART → IDLE', () => {
    expect(transition('WIN', 'RESTART')).toBe('IDLE')
  })

  it('invalid transitions: returns current phase', () => {
    expect(transition('IDLE', 'PAUSE')).toBe('IDLE')
    expect(transition('RUNNING', 'RESTART')).toBe('RUNNING')
  })
})
