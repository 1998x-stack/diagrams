import type { GamePhase } from '../types.ts'

type PhaseEvent = 'START' | 'PAUSE' | 'RESUME' | 'COLLIDE' | 'WIN' | 'RESTART'

const TRANSITIONS: Partial<Record<GamePhase, Partial<Record<PhaseEvent, GamePhase>>>> = {
  IDLE:      { START: 'RUNNING' },
  RUNNING:   { PAUSE: 'PAUSED', COLLIDE: 'GAME_OVER', WIN: 'WIN' },
  PAUSED:    { RESUME: 'RUNNING' },
  GAME_OVER: { RESTART: 'IDLE' },
  WIN:       { RESTART: 'IDLE' },
}

export function transition(current: GamePhase, event: PhaseEvent): GamePhase {
  const next = TRANSITIONS[current]?.[event]
  return next ?? current
}

export type { PhaseEvent }
