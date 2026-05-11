# 贪吃蛇项目技术文档

> 深度工作法（Deep Work）驱动的系统设计文档
> 版本：1.0 | 状态：设计阶段

---

## 一、项目全景

### 1.1 核心目标

构建一个高质量、可扩展的经典贪吃蛇游戏，具备以下特征：

- **流畅体验**：60fps 渲染，零卡顿输入响应
- **模块清晰**：游戏逻辑、渲染、输入完全解耦
- **可测试性**：核心逻辑不依赖 DOM，纯函数驱动
- **可扩展性**：支持多种模式（经典 / 竞速 / 无限地图）

### 1.2 技术选型

| 层次       | 技术方案              | 理由                              |
|------------|----------------------|----------------------------------|
| 渲染       | HTML5 Canvas          | 像素级控制，避免 DOM reflow 开销  |
| 逻辑       | 纯 TypeScript         | 类型安全，逻辑可脱离环境测试      |
| 状态管理   | 有限状态机（FSM）     | 游戏状态转换天然契合 FSM 模型     |
| 构建       | Vite                  | 零配置热更新，ESM 原生支持        |
| 测试       | Vitest                | 与 Vite 生态一致，速度快          |

---

## 二、深度工作阶段划分

深度工作法要求将项目拆解为「不可中断的专注块」，每块对应一个不可分割的设计决策。

### Phase 0：问题建模（≈2h 专注块）

在写任何代码前，必须完整回答：

1. 游戏世界是什么？→ 有限网格，二维坐标系
2. 蛇是什么？→ 有序坐标队列，头部驱动移动
3. 碰撞是什么？→ 集合成员检查（O(1) with Set）
4. 时间是什么？→ 离散 tick，非连续时间流
5. 输入是什么？→ 方向意图，非瞬时事件

> **决策锁定**：游戏逻辑基于「tick-based」步进，而非帧同步，
> 这使得逻辑层完全独立于渲染帧率。

---

## 三、系统架构

### 3.1 分层架构图

```
┌─────────────────────────────────────────┐
│              Entry Point                │
│         main.ts / index.html            │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│            Game Loop (Loop)             │
│   requestAnimationFrame + tick timer    │
│   职责：协调 Update → Render 的时序      │
└──────┬───────────────────────┬──────────┘
       │                       │
┌──────▼──────┐        ┌───────▼─────────┐
│  Game State  │        │    Renderer     │
│  (FSM Core)  │        │  (Canvas 2D)   │
│             │        │                 │
│ - Snake     │──read──▶ - drawGrid()    │
│ - Food      │        │ - drawSnake()   │
│ - Score     │        │ - drawFood()    │
│ - Phase     │        │ - drawUI()      │
└──────▲──────┘        └─────────────────┘
       │
┌──────┴──────────────────────────────────┐
│            Input Manager                │
│   键盘事件 → 方向队列（防抖 + 缓冲）    │
└─────────────────────────────────────────┘
```

### 3.2 模块职责边界

#### `GameState`（核心领域模型）

```
职责：
  - 维护蛇的坐标队列（snake: Point[]）
  - 维护食物坐标（food: Point）
  - 维护当前阶段（phase: GamePhase）
  - 维护分数（score: number）

约束：
  - 纯数据结构，零副作用
  - 不持有任何 DOM 引用
  - 所有状态变更通过 reducer 函数产生新状态（不可变更新）
```

#### `GameEngine`（规则执行器）

```
职责：
  - tick() → 根据当前方向推进一步
  - checkCollision() → 墙壁 / 自身碰撞检测
  - generateFood() → 在非蛇身位置随机生成食物
  - processEat() → 吃食物后增长蛇身 + 更新分数

约束：
  - 输入：GameState + Direction
  - 输出：新的 GameState（或 GAME_OVER 信号）
  - 纯函数，可直接单元测试
```

#### `GameLoop`（时序控制器）

```
职责：
  - 维护 tick 间隔（由难度决定）
  - 在正确时机调用 engine.tick()
  - 在每帧调用 renderer.render()

核心设计：
  - 渲染帧（rAF）与逻辑 tick（setInterval/累积时间）分离
  - 逻辑 tick 固定步长，渲染帧自适应屏幕刷新率
```

#### `InputManager`（意图捕获器）

```
职责：
  - 监听 keydown 事件
  - 过滤非法方向（不允许 180° 反转）
  - 维护方向缓冲队列（最多缓存 2 个待处理方向）

核心设计：
  - 输入与消费解耦：输入时写队列，tick 时读队列
  - 防止快速按键导致的穿墙 bug
```

#### `Renderer`（视觉翻译器）

```
职责：
  - 将 GameState 映射为 Canvas 绘制指令
  - 管理 Canvas 尺寸与 DPR（devicePixelRatio）适配
  - 提供动画效果（蛇头眼睛、食物脉冲等）

约束：
  - 只读 GameState，不修改任何逻辑状态
  - 每帧完整重绘（clearRect → drawAll）
```

---

## 四、核心数据结构

### 4.1 基础类型

```typescript
// 坐标点（网格单元）
type Point = { x: number; y: number };

// 运动方向
type Direction = 'UP' | 'DOWN' | 'LEFT' | 'RIGHT';

// 游戏阶段（有限状态机节点）
type GamePhase =
  | 'IDLE'       // 等待开始
  | 'RUNNING'    // 游戏进行中
  | 'PAUSED'     // 暂停
  | 'GAME_OVER'  // 结束（可重启）
  | 'WIN';       // 胜利（蛇填满整个地图）

// 游戏难度配置
type Difficulty = {
  tickInterval: number;  // ms per tick，越小越快
  gridSize: number;      // 网格边长（正方形）
  initialLength: number; // 初始蛇身长度
};
```

### 4.2 核心状态结构

```typescript
type GameState = {
  snake: Point[];          // index 0 = 蛇头，末尾 = 蛇尾
  food: Point;
  direction: Direction;    // 当前生效方向
  nextDirection: Direction; // 下一 tick 将生效方向
  phase: GamePhase;
  score: number;
  highScore: number;
  tickCount: number;       // 已经历的 tick 数（用于动画计算）
  config: Difficulty;
};
```

### 4.3 游戏阶段状态机

```
                    ┌─────────┐
               ┌──▶│  IDLE   │◀──────────────┐
               │   └────┬────┘               │
               │        │ SPACE / ENTER       │
               │        ▼                     │
               │   ┌─────────┐   ESC    ┌─────┴───┐
    restart    │   │ RUNNING │─────────▶│ PAUSED  │
               │   └────┬────┘          └─────────┘
               │        │                   ▲
               │        │ 碰撞              │ ESC
               │        ▼                   │
               │   ┌─────────┐             │
               └───│GAME_OVER│             │
                   └─────────┘             │
                        │                  │
                        │ 填满地图          │
                        ▼                  │
                   ┌─────────┐             │
                   │   WIN   │─────────────┘
                   └─────────┘
```

---

## 五、关键算法设计

### 5.1 蛇的移动（O(n) → O(1) 优化路径）

**朴素实现**：每 tick 将整个 snake 数组复制并移位
```
新头部 = 根据方向计算
新蛇身 = [新头部, ...旧蛇身.去掉尾部]
```

**优化思路**（如蛇极长时）：使用双端队列（Deque），头部 push，尾部 pop，O(1) 操作。
标准场景下朴素实现已足够，网格 ≤ 40×40 时性能无感知差异。

### 5.2 碰撞检测（Set 优化）

```
墙壁碰撞：新头部坐标超出 [0, gridSize) 范围
自身碰撞：新头部坐标 ∈ 蛇身坐标集合

优化：维护 snakeSet: Set<string>（坐标序列化为 "x,y"）
      检查时间复杂度 O(1) vs 数组遍历 O(n)
```

### 5.3 食物生成（排除蛇身）

```
策略 A（小蛇时高效）：
  随机生成坐标，若在蛇身上则重试
  期望重试次数 = n / (gridSize² - n)，蛇短时几乎不重试

策略 B（大蛇时保底）：
  计算所有空格坐标集合，随机取一个
  时间复杂度 O(gridSize²)，但确保有限次完成

实现：先用策略 A，超过 10 次重试自动切换策略 B
```

### 5.4 输入缓冲（防穿墙）

```
问题：用户在一个 tick 内快速按 RIGHT 再按 DOWN
      若只记录最后方向，RIGHT 会被跳过，产生逻辑错误

解法：方向队列（最大长度 2）
  - keydown 时：若新方向合法（非 180° 反转），入队
  - tick 开始时：出队首个方向作为本 tick 生效方向

合法性检查（防 180° 反转）：
  UP ↔ DOWN 互为非法
  LEFT ↔ RIGHT 互为非法
```

---

## 六、渲染设计

### 6.1 Canvas 分层策略

```
Layer 0（静态背景层，只绘制一次）：
  - 网格线
  - 边框

Layer 1（动态游戏层，每帧绘制）：
  - 蛇身（渐变色，头尾区分）
  - 食物（带脉冲动画）

Layer 2（UI 层，状态变化时绘制）：
  - 分数
  - 游戏阶段提示（PAUSED / GAME OVER 遮罩）
```

实现方案：使用多个叠加的 `<canvas>` 元素，或单 canvas 按层序绘制。

### 6.2 视觉规格

```
网格单元大小：20px × 20px（基准）
边框：2px solid #333
背景：#1a1a2e（深海军蓝）

蛇头：#00ff88（荧光绿）
蛇身：从头到尾渐变 #00ff88 → #004422
蛇眼：白色圆点，根据方向偏移位置

食物：#ff4455（鲜红）
食物动画：每 30 tick 完成一次 scale 0.8→1.2→0.8 脉冲
```

### 6.3 DPR 适配（Retina 屏幕）

```
逻辑尺寸（CSS px）= gridSize × cellSize
物理尺寸（实际像素）= 逻辑尺寸 × devicePixelRatio

canvas.width = 物理尺寸
canvas.style.width = 逻辑尺寸 + 'px'
ctx.scale(dpr, dpr)  // 统一缩放，后续按逻辑坐标绘制
```

---

## 七、目录结构

```
snake/
├── index.html
├── vite.config.ts
├── tsconfig.json
├── CLAUDE.md                  ← 本文档
│
├── src/
│   ├── main.ts                ← 入口，组装所有模块
│   │
│   ├── types.ts               ← 所有类型定义（Point / Direction / GameState...）
│   ├── constants.ts           ← 游戏常量（DIFFICULTIES / COLORS / GRID_SIZE...）
│   │
│   ├── core/
│   │   ├── GameEngine.ts      ← 纯函数：tick / collision / food / eat
│   │   ├── GameState.ts       ← 状态工厂：createInitialState()
│   │   └── fsm.ts             ← 状态机：phaseTransition()
│   │
│   ├── loop/
│   │   └── GameLoop.ts        ← rAF 循环 + tick 步进
│   │
│   ├── input/
│   │   └── InputManager.ts    ← 键盘事件 → 方向队列
│   │
│   ├── render/
│   │   ├── Renderer.ts        ← 主渲染器（协调各子渲染器）
│   │   ├── SnakeRenderer.ts   ← 蛇的绘制逻辑
│   │   ├── FoodRenderer.ts    ← 食物动画逻辑
│   │   └── UIRenderer.ts      ← 分数 / 遮罩 / 提示
│   │
│   └── utils/
│       ├── point.ts           ← 坐标工具（add / equals / serialize）
│       └── random.ts          ← 随机数工具（randInt / shuffle）
│
└── tests/
    ├── GameEngine.test.ts     ← 核心逻辑单测
    ├── InputManager.test.ts   ← 输入缓冲单测
    └── collision.test.ts      ← 碰撞边界用例
```

---

## 八、测试策略

### 8.1 单元测试覆盖目标

| 模块            | 覆盖目标       | 关键用例                                      |
|-----------------|----------------|----------------------------------------------|
| `GameEngine`    | 100% 逻辑分支  | 正常移动、吃食物、墙壁碰撞、自身碰撞          |
| `InputManager`  | 100% 逻辑分支  | 方向入队、180°拦截、队列上限、快速连按        |
| `point.ts`      | 100%           | 坐标序列化、边界值                            |
| `Renderer`      | 视觉快照测试   | 确保关键帧像素输出稳定（可选）                |

### 8.2 关键测试场景（BDD 风格描述）

```
Feature: 蛇的移动
  Scenario: 向右移动一格
    Given 蛇头在 (5, 5)，方向为 RIGHT
    When 执行一次 tick
    Then 蛇头移动至 (6, 5)
    And 蛇尾缩短（若未吃食物）

Feature: 碰撞检测
  Scenario: 撞墙
    Given 蛇头在 (gridSize-1, y)，方向为 RIGHT
    When 执行一次 tick
    Then phase 变为 GAME_OVER

  Scenario: 撞自身
    Given 蛇身形成 U 形，头部即将进入自身
    When 执行一次 tick
    Then phase 变为 GAME_OVER

Feature: 输入缓冲
  Scenario: 防止 180° 反转
    Given 当前方向为 RIGHT
    When 用户按下 LEFT
    Then 方向队列不入队 LEFT

  Scenario: 快速转向缓冲
    Given 当前方向为 RIGHT，tick 尚未到来
    When 用户依次按下 UP → LEFT
    Then 方向队列为 [UP, LEFT]
    And 下一 tick 消费 UP，再下一 tick 消费 LEFT
```

---

## 九、难度与扩展设计

### 9.1 内置难度配置

```typescript
const DIFFICULTIES = {
  EASY:   { tickInterval: 200, gridSize: 20, initialLength: 3 },
  NORMAL: { tickInterval: 130, gridSize: 25, initialLength: 4 },
  HARD:   { tickInterval: 80,  gridSize: 30, initialLength: 5 },
  CUSTOM: { tickInterval: ???, gridSize: ???, initialLength: ??? },
} as const;
```

### 9.2 扩展点预留

| 扩展方向     | 设计预留位置                                        |
|-------------|-----------------------------------------------------|
| 多种食物类型 | `FoodType` 枚举 + `GameState.foodType` 字段          |
| 障碍物       | `GameState.obstacles: Point[]` + 碰撞检测扩展        |
| 双人模式     | `GameState.snakes: Snake[]` 数组化                   |
| 音效         | `AudioManager` 模块，监听 GameState 变化触发          |
| 本地排行榜   | `highScore` 持久化到 `localStorage`                  |
| 移动端支持   | `InputManager` 增加 Touch 事件处理                   |

---

## 十、实现顺序（深度工作执行计划）

按「最小可验证切片」原则，每完成一层即可独立验证：

```
Sprint 1：数据层（无 UI）
  □ types.ts + constants.ts
  □ point.ts 工具函数 + 测试
  □ GameState 初始化工厂
  □ GameEngine 核心 tick 逻辑 + 完整单测

Sprint 2：输入层
  □ InputManager（方向队列 + 防抖）
  □ InputManager 单测

Sprint 3：循环层
  □ GameLoop（rAF + tick 分离）
  □ 在 console 打印 GameState 验证逻辑正确性

Sprint 4：渲染层
  □ Canvas 初始化 + DPR 适配
  □ 网格 + 蛇 + 食物基础绘制
  □ UI 文字（分数 / 阶段提示）

Sprint 5：集成 + 打磨
  □ main.ts 组装所有模块
  □ 动画细节（蛇眼、食物脉冲、死亡闪烁）
  □ 难度选择界面
  □ 排行榜持久化
```

---

## 十一、性能基准

| 指标             | 目标                  | 测量方法                       |
|------------------|-----------------------|-------------------------------|
| 渲染帧率         | ≥ 60fps（稳定）       | Chrome DevTools Performance   |
| 单次 tick 耗时   | ≤ 1ms                 | `performance.now()` 包裹       |
| 单次 render 耗时 | ≤ 5ms（40×40 网格）   | `performance.now()` 包裹       |
| 内存占用         | ≤ 20MB                | Chrome Memory Snapshot        |
| 首次加载         | ≤ 500ms（本地）       | Lighthouse                    |

---

*文档遵循深度工作原则：每个设计决策均有明确理由，每个模块均有清晰边界，实现顺序按最小可验证切片排列。*
