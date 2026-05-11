# 架构设计文档

> 本文档深入解释各模块的设计决策，适合想要理解或扩展项目的开发者。

---

## 整体架构

```
┌─────────────────────────────────────────┐
│              main.ts                    │
│  组装模块 + 持久化 + 难度选择            │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│            GameLoop                     │
│   rAF 渲染帧 + 固定步长 tick 逻辑        │
└──────┬──────────────────────┬───────────┘
       │                      │
┌──────▼──────┐       ┌───────▼─────────┐
│ InputManager│       │    Renderer     │
│ 键盘→方向队列│       │  Canvas 绘制    │
└──────┬──────┘       └─────────────────┘
       │ consume()
┌──────▼──────────────────────────────────┐
│           GameEngine.tick()             │
│   纯函数：推进状态，碰撞，吃食物         │
└──────────────────────────────────────────┘
```

---

## 核心设计决策

### 决策 1：tick-based 而非帧同步

游戏逻辑基于固定时间步长（tick），而非每帧推进。

**原因：**
- 逻辑层与渲染帧率完全解耦
- 不同设备帧率（60fps / 120fps）不影响游戏速度
- 暂停时可以停止 tick，但渲染仍可继续（显示暂停画面）

```
渲染帧（rAF）：~16ms 一帧，由显示器刷新率决定
逻辑 tick：    按难度配置固定间隔（80ms~200ms）

两者在 GameLoop 中通过累积时间（elapsed）解耦：
  elapsed = now - lastTickTime
  if (elapsed >= tickInterval) → 执行一次 tick
```

### 决策 2：纯函数状态推进

`GameEngine.tick()` 是纯函数：

```ts
tick(state: GameState): GameState  // 输入旧状态 → 输出新状态
```

**原因：**
- 零副作用，可以在任何环境（包括测试）直接调用
- 状态历史可追溯（快照、回放）
- 避免难以调试的隐式状态突变

**代价：** 每次 tick 创建新对象。对于贪吃蛇这种规模可忽略。

### 决策 3：输入与消费解耦（方向缓冲队列）

```
输入时机：keydown 事件触发 → 写入队列
消费时机：tick 开始时 → 从队列读取一个方向
```

**原因：** 解决「快速连按导致穿墙」问题。

```
场景：蛇向右走，用户在一个 tick 内快速按 UP → LEFT
朴素做法：只记最后一个方向 LEFT → 蛇直接从 RIGHT 变 LEFT → 穿墙！
队列做法：[UP, LEFT] → 本 tick 消费 UP，下一 tick 消费 LEFT → 正确
```

防 180° 反转检查基于队列末尾（非当前生效方向），确保连续快速输入时判断准确。

### 决策 4：有限状态机管理游戏阶段

```
IDLE → RUNNING → PAUSED → RUNNING → GAME_OVER → IDLE
                      ↘ WIN ↗
```

所有阶段转换通过 `transition(current, event)` 函数集中管理，非法转换静默返回当前状态（防御性编程）。

---

## 各模块详解

### GameEngine（`src/core/GameEngine.ts`）

最核心的模块，一个 tick 的执行步骤：

```
1. 检查 phase === 'RUNNING'（非运行态直接返回原状态）
2. 应用 nextDirection（切换为用户最新输入的方向）
3. 计算新头部坐标 = 头部 + 方向向量
4. 检查墙壁碰撞 → GAME_OVER
5. 检查自身碰撞（排除蛇尾）→ GAME_OVER
6. 判断是否吃到食物
   - 吃到：保留蛇尾（增长）、+10 分、生成新食物
   - 未吃：去掉蛇尾（移动）
7. 检查胜利条件（蛇长 === 格子总数）
8. 返回新状态
```

自身碰撞检测排除蛇尾的原因：

```
移动时，蛇尾会离开当前位置。
如果头部下一步恰好是蛇尾的位置，蛇尾已经走了，不构成碰撞。
所以只检查 snake.slice(0, -1)，而非整条蛇。
```

### InputManager（`src/input/InputManager.ts`）

关键状态：

```ts
private queue: Direction[]        // 待消费方向队列（最多 2 个）
private currentDirection: Direction  // 当前已生效方向（用于防 180° 检查）
```

`enqueue` 的防反转逻辑：

```ts
// 参考基准：优先使用队列末尾（非 currentDirection）
const reference = queue.length > 0 ? queue[last] : currentDirection
if (OPPOSITE_DIRECTION[dir] === reference) return  // 拒绝
```

### Renderer（`src/render/Renderer.ts`）

每帧绘制顺序（重要，后绘制的会覆盖前面）：

```
1. fillRect 清空背景
2. drawGrid 网格线
3. FoodRenderer.render 食物（在蛇下面）
4. SnakeRenderer.render 蛇
5. UIRenderer.render 分数 + 遮罩（最上层）
```

DPR 适配（Retina 屏幕）：

```ts
const dpr = window.devicePixelRatio  // Retina = 2, 普通屏 = 1
canvas.width = logicalSize * dpr     // 物理像素数
canvas.style.width = logicalSize + 'px'  // CSS 逻辑尺寸
ctx.scale(dpr, dpr)                  // 后续坐标按逻辑坐标写，自动放大
```

### GameLoop（`src/loop/GameLoop.ts`）

tick 时机计算（防止帧率变化影响游戏速度）：

```ts
const elapsed = now - lastTickTime
if (elapsed >= tickInterval) {
  // 补偿：减去多余时间，保持精确步长
  lastTickTime = now - (elapsed % tickInterval)
  executeTick()
}
```

---

## 数据流图

```
keydown 事件
    │
    ▼
InputManager.enqueue(dir)
    │ 队列
    ▼
GameLoop（每帧）
    │
    ├─► [elapsed >= tickInterval?]
    │         │ YES
    │         ▼
    │   InputManager.consume() → dir | null
    │         │
    │         ▼
    │   GameEngine.setNextDirection(state, dir)
    │         │
    │         ▼
    │   GameEngine.tick(state) → newState
    │         │
    │   state = newState
    │
    ▼
Renderer.render(state)
    ├── drawGrid
    ├── FoodRenderer
    ├── SnakeRenderer
    └── UIRenderer
```

---

## 扩展指南

### 添加障碍物

1. 在 `types.ts` 的 `GameState` 中添加：
   ```ts
   obstacles: Point[]
   ```

2. 在 `GameEngine.ts` 的碰撞检测中增加：
   ```ts
   const obstacleSet = buildSnakeSet(state.obstacles)
   if (obstacleSet.has(serializePoint(newHead))) → GAME_OVER
   ```

3. 在 `Renderer` 中绘制障碍物。

4. 在 `GameState.ts` 初始化障碍物。

### 添加音效

新建 `src/audio/AudioManager.ts`：

```ts
export class AudioManager {
  eat(): void  { /* play eat sound */ }
  die(): void  { /* play die sound */ }
  win(): void  { /* play win sound */ }
}
```

在 `GameLoop` 中注入，检测状态变化（phase 变为 GAME_OVER / score 增加）时触发。

### 双人模式

将 `GameState.snake: Point[]` 改为 `snakes: Snake[]`，每条蛇有独立的方向和分数。需要两个 `InputManager` 实例绑定不同的按键。
