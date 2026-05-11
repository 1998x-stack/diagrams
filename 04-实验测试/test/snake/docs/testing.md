# 测试文档

> 本文档说明项目的测试策略、测试结构，以及如何为新功能编写测试。

---

## 测试概览

| 文件 | 覆盖模块 | 用例数 |
|------|----------|--------|
| `tests/point.test.ts` | `utils/point.ts` | 6 |
| `tests/fsm.test.ts` | `core/fsm.ts` | 8 |
| `tests/GameEngine.test.ts` | `core/GameEngine.ts` | 7 |
| `tests/InputManager.test.ts` | `input/InputManager.ts` | 13 |
| `tests/GameLoop.test.ts` | `loop/GameLoop.ts` | 9 |
| `tests/Renderer.test.ts` | `render/*` | 11 |
| **合计** | | **54** |

---

## 运行测试

```bash
# 单次运行（CI 使用）
npm test

# 监听模式（开发时使用）
npm run test:watch
```

---

## 测试分层策略

项目使用 **Vitest** 作为测试框架。测试按层分文件，每层各自独立验证。

### Layer 0：工具函数（`point.test.ts`）

最底层，无任何依赖。直接调用函数验证返回值。

```ts
it('serializePoint: formats as "x,y"', () => {
  expect(serializePoint({ x: 2, y: 7 })).toBe('2,7')
})
```

### Layer 1：状态机（`fsm.test.ts`）

验证所有合法转换，以及非法转换不改变状态。

```ts
it('RUNNING + PAUSE → PAUSED', () => {
  expect(transition('RUNNING', 'PAUSE')).toBe('PAUSED')
})

it('invalid: 不在转换表中 → 返回当前状态', () => {
  expect(transition('IDLE', 'PAUSE')).toBe('IDLE')
})
```

### Layer 2：核心引擎（`GameEngine.test.ts`）

使用辅助函数 `makeState()` 构造最小测试状态（5×5 网格），覆盖所有分支路径。

```ts
function makeState(overrides = {}): GameState {
  return {
    snake: [{ x: 2, y: 2 }, { x: 1, y: 2 }, { x: 0, y: 2 }],
    food: { x: 4, y: 4 },
    direction: 'RIGHT',
    ...defaults,
    ...overrides,
  }
}
```

关键场景：

- **正常移动**：蛇头坐标 +1，蛇尾消失，蛇身长度不变
- **吃食物**：蛇身 +1，分数 +10，生成新食物（不在蛇身上）
- **墙壁碰撞**：phase → GAME_OVER
- **自身碰撞**：phase → GAME_OVER
- **非 RUNNING 状态**：tick 原样返回，不做任何推进

### Layer 3：输入管理（`InputManager.test.ts`）

验证队列语义和防反转逻辑。

核心测试用例：

```ts
// 180° 反转拒绝
it('当前 RIGHT，拒绝 LEFT', () => {
  im.enqueue('LEFT')
  expect(im._getQueue()).toEqual([])
})

// 基于队尾的防反转
it('队列=[UP]，拒绝 DOWN', () => {
  im.enqueue('UP')
  im.enqueue('DOWN')  // 基于队尾 UP，DOWN 是 180°
  expect(im._getQueue()).toEqual(['UP'])
})

// 队列上限
it('超过 2 个方向被丢弃', () => {
  im.enqueue('UP')
  im.enqueue('LEFT')
  im.enqueue('DOWN')  // 第 3 个，丢弃
  expect(im._getQueue()).toEqual(['UP', 'LEFT'])
})
```

### Layer 4：游戏循环（`GameLoop.test.ts`）

GameLoop 依赖浏览器 API（`requestAnimationFrame`、`performance.now`），测试中使用 `vi.stubGlobal` 替换：

```ts
// mock rAF：同步注册回调，手动触发
vi.stubGlobal('requestAnimationFrame', (cb) => {
  pending.set(++id, cb)
  return id
})

function flush(now = 0) {
  const cbs = [...pending.values()]
  pending.clear()
  cbs.forEach(cb => cb(now))
}
```

关键验证：

```ts
it('PAUSED 时不推进 tickCount', () => {
  input.onAction!('Escape')  // 暂停
  const before = loop.getState().tickCount
  flush(500)                 // 模拟时间流逝
  expect(loop.getState().tickCount).toBe(before)  // 不变
})
```

### Layer 5：渲染层（`Renderer.test.ts`）

Canvas 2D API 在 Node 环境中不可用，使用对象 mock 追踪调用：

```ts
function makeCtx() {
  const texts: string[] = []
  return {
    fillText: vi.fn((...args) => texts.push(String(args[0]))),
    fillRect: vi.fn(),
    arc: vi.fn(),
    // ...
    _texts: texts,
  }
}
```

验证策略：
- **UIRenderer**：检查 `fillText` 被调用时的文字内容，确认各 phase 输出正确
- **FoodRenderer**：检查 `arc` 被调用的 radius 参数，验证脉冲动画计算
- **SnakeRenderer**：检查 `fillRect` 调用次数（蛇身节数 + 2 只眼睛）

---

## 如何为新功能编写测试

### 场景：你新增了「吃食物得 20 分」的功能

**Step 1：找到对应层的测试文件**

分数逻辑在 `GameEngine.ts` → 对应 `tests/GameEngine.test.ts`

**Step 2：在已有 describe 块中添加用例**

```ts
it('吃食物：分数 +20', () => {
  const state = makeState({
    snake: [{ x: 3, y: 2 }, { x: 2, y: 2 }],
    food: { x: 4, y: 2 },  // 食物在蛇头右侧
    direction: 'RIGHT',
    nextDirection: 'RIGHT',
  })
  const next = tick(state)
  expect(next.score).toBe(20)  // 之前是 10，现在改为 20
})
```

**Step 3：运行测试，先看到失败**

```bash
npm test
# AssertionError: expected 10 to equal 20
```

**Step 4：修改实现，让测试通过**

```ts
// GameEngine.ts
newScore = state.score + 20  // 改这里
```

**Step 5：再次运行，确认全绿**

```bash
npm test
# 54 passed ✓
```

---

## 测试命名规范

```
it('[被测状态/行为]：[期望结果]', () => { ... })
```

示例：
- `'正常移动：蛇头向右移一格，蛇尾缩短'`
- `'墙壁碰撞：撞右墙 → GAME_OVER'`
- `'180° 反转拒绝：当前 RIGHT，拒绝 LEFT'`

---

## 不需要测试的内容

- `Renderer` 的视觉效果（颜色、像素精度）— 属于视觉回归测试范畴，当前不引入
- `main.ts` 的 DOM 操作 — 属于 E2E 测试范畴
- 随机数生成的具体值 — 只测「结果不在蛇身上」这一性质，而非具体坐标

---

## 调试失败的测试

```bash
# 只跑某个测试文件
npx vitest run tests/GameEngine.test.ts

# 只跑名字包含关键词的用例
npx vitest run --testNamePattern="碰撞"

# 监听模式 + 只跑指定文件
npx vitest tests/GameEngine.test.ts
```

失败输出示例：

```
AssertionError: expected 'RUNNING' to equal 'GAME_OVER'

- Expected: "GAME_OVER"
+ Received: "RUNNING"

 ❯ tests/GameEngine.test.ts:45:30
```

→ 说明碰撞逻辑没有被触发，检查碰撞判断条件是否正确。
