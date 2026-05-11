// 坐标点（网格单元）
export type Point = { x: number; y: number }

// 运动方向
export type Direction = 'UP' | 'DOWN' | 'LEFT' | 'RIGHT'

// 游戏阶段（有限状态机节点）
export type GamePhase = 'IDLE' | 'RUNNING' | 'PAUSED' | 'GAME_OVER' | 'WIN'

// 游戏难度配置
export type Difficulty = {
  tickInterval: number  // ms per tick
  gridSize: number      // 网格边长（正方形）
  initialLength: number // 初始蛇身长度
}

// 核心状态
export type GameState = {
  snake: Point[]           // index 0 = 蛇头，末尾 = 蛇尾
  food: Point
  direction: Direction     // 当前生效方向
  nextDirection: Direction // 下一 tick 将生效方向
  phase: GamePhase
  score: number
  highScore: number
  tickCount: number        // 已经历 tick 数（用于动画计算）
  config: Difficulty
}

// 方向向量映射
export type DirectionVector = { dx: number; dy: number }
