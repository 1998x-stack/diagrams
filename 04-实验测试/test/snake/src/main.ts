import type { Difficulty } from './types.ts'
import { DIFFICULTIES } from './constants.ts'
import { createInitialState } from './core/GameState.ts'
import { InputManager } from './input/InputManager.ts'
import { GameLoop } from './loop/GameLoop.ts'
import { Renderer } from './render/Renderer.ts'

function loadHighScore(): number {
  return parseInt(localStorage.getItem('snake_highScore') ?? '0', 10) || 0
}

function saveHighScore(score: number): void {
  localStorage.setItem('snake_highScore', String(score))
}

const canvas = document.getElementById('game-canvas') as HTMLCanvasElement
const diffSelect = document.getElementById('difficulty') as HTMLSelectElement
const diffPanel = document.getElementById('diff-panel') as HTMLDivElement

const renderer = new Renderer(canvas)
const input = new InputManager()

let loop: GameLoop | null = null

function startGame(difficulty: Difficulty): void {
  if (loop) loop.stop()

  diffPanel.style.display = 'none'
  renderer.resize(difficulty.gridSize)

  loop = new GameLoop(input, (state) => {
    if (state.highScore > loadHighScore()) {
      saveHighScore(state.highScore)
    }
    renderer.render(state)
  })

  // 注入带 highScore 的初始状态
  loop.setState({ ...createInitialState(difficulty), highScore: loadHighScore() })

  input.attach(window)
  loop.start()
}

const btnStart = document.getElementById('btn-start') as HTMLButtonElement
btnStart.addEventListener('click', () => {
  const key = diffSelect.value as keyof typeof DIFFICULTIES
  const difficulty = DIFFICULTIES[key] ?? DIFFICULTIES['NORMAL']!
  startGame(difficulty)
})

// 初始预览
renderer.resize(DIFFICULTIES['NORMAL']!.gridSize)
renderer.render(createInitialState(DIFFICULTIES['NORMAL']!))
