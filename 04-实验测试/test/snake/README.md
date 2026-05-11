# 贪吃蛇 · Snake

经典贪吃蛇游戏的现代实现，使用 TypeScript + HTML5 Canvas 构建。

![游戏界面示意](docs/preview.png)

---

## 特性

- **60fps 流畅渲染** — rAF 驱动渲染，tick-based 逻辑分离，不卡顿
- **三档难度** — EASY / NORMAL / HARD，网格尺寸与速度各不相同
- **输入缓冲** — 支持快速连按转向，自动防 180° 穿透 bug
- **蛇眼动画** — 蛇头有双眼，随方向转动
- **食物脉冲** — 食物圆形脉冲动画，每 30 tick 一周期
- **最高分持久化** — 刷新页面不丢失，存于 `localStorage`
- **Retina 屏适配** — 自动 devicePixelRatio 缩放，画面锐利
- **完整单测** — 6 个测试文件，54 个用例，核心逻辑 100% 覆盖

---

## 快速开始

### 环境要求

- Node.js ≥ 18（推荐通过 [nvm](https://github.com/nvm-sh/nvm) 安装）

### 安装与运行

```bash
# 克隆项目
git clone <repo-url>
cd snake

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

打开浏览器访问 `http://localhost:5173`，即可开始游戏。

### 其他命令

```bash
npm test          # 运行所有单元测试（一次性）
npm run test:watch  # 监听模式，文件变更自动重跑
npm run build     # 生产构建，产物在 dist/
npm run preview   # 预览生产构建
```

---

## 操作方式

| 按键 | 功能 |
|------|------|
| `↑ ↓ ← →` 或 `W A S D` | 控制蛇的方向 |
| `Space` / `Enter` | 开始游戏 / 游戏结束后重启 |
| `Esc` | 暂停 / 继续 |

---

## 难度说明

| 难度 | 网格 | 速度 | 初始蛇长 |
|------|------|------|----------|
| EASY | 20×20 | 200ms/tick | 3 |
| NORMAL | 25×25 | 130ms/tick | 4 |
| HARD | 30×30 | 80ms/tick | 5 |

---

## 项目结构

```
snake/
├── src/
│   ├── types.ts              # 类型定义（Point / Direction / GameState...）
│   ├── constants.ts          # 常量（难度配置 / 颜色 / 尺寸）
│   ├── core/
│   │   ├── GameEngine.ts     # 核心逻辑：tick / 碰撞 / 吃食物（纯函数）
│   │   ├── GameState.ts      # 初始状态工厂
│   │   └── fsm.ts            # 游戏阶段有限状态机
│   ├── input/
│   │   └── InputManager.ts   # 键盘输入 → 方向缓冲队列
│   ├── loop/
│   │   └── GameLoop.ts       # rAF 渲染循环 + tick 步进
│   ├── render/
│   │   ├── Renderer.ts       # 主渲染器（协调子渲染器）
│   │   ├── SnakeRenderer.ts  # 蛇体绘制（渐变 + 眼睛）
│   │   ├── FoodRenderer.ts   # 食物脉冲动画
│   │   └── UIRenderer.ts     # 分数 / 遮罩 / 提示文字
│   ├── utils/
│   │   ├── point.ts          # 坐标工具函数
│   │   └── random.ts         # 随机数 / 随机空格生成
│   └── main.ts               # 入口：组装模块、难度选择、持久化
├── tests/                    # 单元测试
├── index.html
├── vite.config.ts
├── tsconfig.json
└── CLAUDE.md                 # 技术设计文档
```

---

## 测试覆盖

```
测试文件       覆盖内容
─────────────────────────────────────────────
point.test        坐标工具函数（6 个用例）
fsm.test          状态机转换（8 个用例）
GameEngine.test   核心 tick 逻辑（7 个用例）
InputManager.test 输入缓冲 / 防反转（13 个用例）
GameLoop.test     循环时序 / 重启（9 个用例）
Renderer.test     子渲染器（11 个用例）
─────────────────────────────────────────────
合计              54 个用例，全部通过
```

---

## 技术架构

```
GameLoop（时序控制）
   ├── InputManager（键盘输入 → 方向队列）
   ├── GameEngine.tick()（纯函数状态推进）
   └── Renderer（Canvas 绘制）
        ├── SnakeRenderer
        ├── FoodRenderer
        └── UIRenderer
```

**核心设计原则**：

- 逻辑层（GameEngine）为纯函数，零副作用，可直接单元测试
- 渲染帧率（rAF）与逻辑 tick 完全分离，互不干扰
- 状态不可变更新（每次 tick 返回新状态对象）
- 输入与消费解耦（写队列 vs 读队列）

---

## License

MIT
