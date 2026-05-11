# 新手上手指南

> 这份文档面向第一次接触本项目的开发者，从零开始带你运行、理解、修改这个贪吃蛇项目。

---

## 第一步：准备环境

### 1.1 安装 Node.js

本项目需要 Node.js 运行时。推荐使用 **nvm**（Node Version Manager）管理版本。

```bash
# 安装 nvm（macOS / Linux）
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash

# 重新加载 shell（或重开终端）
source ~/.bashrc   # bash 用户
source ~/.zshrc    # zsh 用户

# 安装 Node.js LTS 版本
nvm install --lts

# 验证安装
node --version   # 应输出 v20.x.x 或更高
npm --version    # 应输出 10.x.x 或更高
```

> Windows 用户：请访问 [nodejs.org](https://nodejs.org) 直接下载安装包，或使用 WSL。

### 1.2 获取代码

```bash
git clone <repo-url>
cd snake
```

---

## 第二步：安装依赖并启动

```bash
# 安装项目依赖（只需执行一次）
npm install

# 启动开发服务器
npm run dev
```

终端会输出类似：

```
  VITE v5.x.x  ready in 300 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

在浏览器打开 `http://localhost:5173`，即可看到游戏界面。

---

## 第三步：玩游戏

1. 在难度选择面板选择 **EASY / NORMAL / HARD**
2. 点击 **START GAME** 进入游戏画面
3. 按 `Space` 或 `Enter` 开始移动蛇
4. 用方向键（或 WASD）控制方向
5. 吃到红色食物得 10 分，蛇身增长 1 格
6. 撞墙或撞自身游戏结束，按 `Enter` 重新开始

| 按键 | 效果 |
|------|------|
| `↑ / W` | 向上 |
| `↓ / S` | 向下 |
| `← / A` | 向左 |
| `→ / D` | 向右 |
| `Space` / `Enter` | 开始 / 重启 |
| `Esc` | 暂停 / 继续 |

---

## 第四步：运行测试

```bash
npm test
```

正常输出：

```
 Test Files  6 passed (6)
      Tests  54 passed (54)
   Duration  ~100ms
```

如果所有测试通过，说明你的环境配置正确。

```bash
# 监听模式：修改代码后自动重跑相关测试
npm run test:watch
```

---

## 第五步：理解代码结构

打开 `src/` 目录，文件按功能分层：

```
src/
├── types.ts        ← 从这里开始！所有数据类型定义
├── constants.ts    ← 游戏常量（颜色、难度、尺寸）
├── core/           ← 游戏逻辑，不依赖浏览器
├── input/          ← 键盘输入处理
├── loop/           ← 游戏主循环
├── render/         ← 画面绘制
└── utils/          ← 通用工具函数
```

**建议阅读顺序：**

```
types.ts
  → utils/point.ts
    → core/fsm.ts
      → core/GameEngine.ts（核心！）
        → input/InputManager.ts
          → loop/GameLoop.ts
            → render/Renderer.ts
              → main.ts（入口）
```

---

## 第六步：尝试修改

以下是几个适合新手的修改练习：

### 练习 1：修改蛇头颜色

打开 `src/constants.ts`，找到 `COLORS` 对象：

```ts
export const COLORS = {
  SNAKE_HEAD: '#00ff88',  // 改成你喜欢的颜色，如 '#ffdd00'
  ...
}
```

保存后浏览器会自动热更新，无需重启。

---

### 练习 2：调整游戏速度

同样在 `src/constants.ts`，修改 `DIFFICULTIES`：

```ts
export const DIFFICULTIES = {
  EASY: { tickInterval: 200, ... },  // 数字越大越慢，越小越快
  ...
}
```

---

### 练习 3：吃食物得更多分

打开 `src/core/GameEngine.ts`，找到：

```ts
newScore = state.score + 10
```

改为你想要的分值，比如 `+ 20`。

然后运行测试验证没有破坏逻辑：

```bash
npm test
```

---

### 练习 4：增加一种新难度

在 `src/constants.ts` 的 `DIFFICULTIES` 中添加：

```ts
INSANE: { tickInterval: 50, gridSize: 35, initialLength: 5 },
```

在 `index.html` 的 `<select>` 中添加选项：

```html
<option value="INSANE">INSANE — 极限 35×35</option>
```

---

## 常见问题

### Q：运行 `npm run dev` 报错 `command not found: npm`

Node.js 没有正确安装或没加入 PATH。运行：

```bash
export NVM_DIR="$HOME/.nvm" && source "$NVM_DIR/nvm.sh"
nvm use --lts
```

### Q：浏览器打开后页面空白

确认终端没有报错。如果看到 TypeScript 错误，按报错信息排查。
也可以尝试：

```bash
npm install   # 确保依赖已安装
npm run dev
```

### Q：测试失败

先确认你修改的代码逻辑正确：

```bash
npm run test:watch   # 监听模式，看具体哪个用例失败
```

失败信息会告诉你「期望值」和「实际值」，根据差异定位问题。

### Q：改了代码，游戏行为不对

运行测试：

```bash
npm test
```

如果测试都通过但游戏行为仍不对，可能是渲染层的问题，用浏览器 DevTools 的 Console 查看报错。

---

## 下一步

- 阅读 [CLAUDE.md](../CLAUDE.md) 了解完整的架构设计思路
- 查看 [architecture.md](./architecture.md) 深入理解各模块设计
- 查看 [testing.md](./testing.md) 了解如何为新功能编写测试
