# Lua 与游戏引擎深度研究：链接、交互与调用全景

> **研究范围**：Lua 作为嵌入式脚本语言的底层机制、C/C++ API 绑定原理、主流引擎集成模式、高级模式与最佳实践

---

## 目录

1. [Lua 的嵌入式设计哲学](#1-lua-的嵌入式设计哲学)
2. [Lua C API 核心机制](#2-lua-c-api-核心机制)
3. [C/C++ ↔ Lua 双向调用详解](#3-cc--lua-双向调用详解)
4. [主流游戏引擎集成全景](#4-主流游戏引擎集成全景)
   - 4.1 [LÖVE2D — 纯 Lua 引擎](#41-löve2d--纯-lua-引擎)
   - 4.2 [Roblox / Luau](#42-roblox--luau)
   - 4.3 [Defold](#43-defold)
   - 4.4 [Unity via MoonSharp/NLua](#44-unity-via-moonsharpnlua)
   - 4.5 [CryEngine / Lumberyard](#45-cryengine--lumberyard)
   - 4.6 [Cocos2d-x](#46-cocos2d-x)
   - 4.7 [Corona SDK / Solar2D](#47-corona-sdk--solar2d)
   - 4.8 [自定义引擎嵌入 Lua](#48-自定义引擎嵌入-lua)
5. [高级集成模式](#5-高级集成模式)
   - 5.1 [热重载系统](#51-热重载系统)
   - 5.2 [沙盒执行环境](#52-沙盒执行环境)
   - 5.3 [Lua 协程与游戏状态机](#53-lua-协程与游戏状态机)
   - 5.4 [面向对象与组件系统](#54-面向对象与组件系统)
   - 5.5 [事件/信号系统](#55-事件信号系统)
   - 5.6 [内存管理与 GC 调优](#56-内存管理与-gc-调优)
6. [LuaJIT 与性能优化](#6-luajit-与性能优化)
7. [调试与性能分析](#7-调试与性能分析)
8. [Luau — Roblox 的类型化 Lua](#8-luau--roblox-的类型化-lua)
9. [工具链与生态系统](#9-工具链与生态系统)
10. [架构决策指南](#10-架构决策指南)

---

## 1. Lua 的嵌入式设计哲学

### 1.1 为什么游戏引擎选择 Lua

Lua 自 1993 年由 PUC-Rio 创建，核心设计目标就是**作为宿主语言的嵌入式脚本**。这使它与 Python、JavaScript 等自托管语言有本质区别：

| 特性 | Lua | Python | JavaScript |
|------|-----|--------|-----------|
| 虚拟机大小 | ~200KB | ~4MB | ~10MB+ |
| 嵌入复杂度 | 极低 | 高 | 高 |
| C API 设计 | 原生 | 复杂 | 无标准 |
| 全局状态 | 无（lua_State 隔离） | 有 GIL | 有 |
| 协程 | 原生支持 | 3.5+ async | Generator |
| 类型系统 | 动态 | 动态 | 动态 |

### 1.2 Lua 虚拟机架构

```
┌────────────────────────────────────────────────────────┐
│                    宿主进程（C/C++）                      │
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │                  lua_State                        │  │
│  │                                                  │  │
│  │  ┌────────────┐   ┌──────────┐   ┌───────────┐  │  │
│  │  │  Value     │   │  Stack   │   │   GC      │  │  │
│  │  │  Stack     │   │  Frame   │   │   Heap    │  │  │
│  │  └────────────┘   └──────────┘   └───────────┘  │  │
│  │                                                  │  │
│  │  ┌────────────┐   ┌──────────┐   ┌───────────┐  │  │
│  │  │  Registry  │   │  Globals │   │  Upvalues │  │  │
│  │  │  Table     │   │  Table   │   │           │  │  │
│  │  └────────────┘   └──────────┘   └───────────┘  │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  C/C++ ←→ Stack Interface ←→ Lua VM                  │
└────────────────────────────────────────────────────────┘
```

**核心设计原则**：
- `lua_State`：完整的解释器实例，线程安全隔离
- **基于栈的通信**：C 与 Lua 的所有数据交换通过虚拟栈完成
- **注册表（Registry）**：C 侧存储 Lua 引用的持久化机制
- **Userdata**：将 C 结构体暴露给 Lua 的机制

---

## 2. Lua C API 核心机制

### 2.1 生命周期管理

```c
#include "lua.h"
#include "lualib.h"
#include "lauxlib.h"

// 创建独立的 Lua 状态机
lua_State *L = luaL_newstate();

// 加载标准库（按需选择）
luaL_openlibs(L);          // 全部标准库
// 或细粒度加载：
lua_pushcfunction(L, luaopen_math);
lua_call(L, 0, 0);

// 执行脚本文件
int status = luaL_dofile(L, "game/scripts/main.lua");
if (status != LUA_OK) {
    fprintf(stderr, "Error: %s\n", lua_tostring(L, -1));
    lua_pop(L, 1);  // 清除错误消息
}

// 执行脚本字符串
luaL_dostring(L, "print('Hello from Lua!')");

// 销毁状态机（释放所有内存）
lua_close(L);
```

### 2.2 Lua 栈详解

Lua 栈是 C 与 Lua 交互的**唯一通道**。理解栈操作是嵌入 Lua 的核心：

```
栈索引规则：
  正索引: 1（栈底） → top（栈顶）
  负索引: -1（栈顶） → -n（向栈底）

调用前的栈状态：      push 操作后：
  ┌─────────────┐     ┌─────────────┐
  │ [3]  "hi"   │     │ [5]  42.0   │  ← lua_pushnumber
  │ [2]  true   │     │ [4]  "str"  │  ← lua_pushstring
  │ [1]  table  │     │ [3]  "hi"   │
  └─────────────┘     │ [2]  true   │
   top = 3            │ [1]  table  │
                      └─────────────┘
                       top = 5
```

**常用栈操作 API**：

```c
// ── 推入操作 ─────────────────────────────────────────
lua_pushnil(L);                    // nil
lua_pushboolean(L, 1);             // true
lua_pushnumber(L, 3.14);           // number (double)
lua_pushinteger(L, 42);            // integer
lua_pushstring(L, "hello");        // string (自动复制)
lua_pushlstring(L, buf, len);      // 带长度字符串
lua_pushcfunction(L, my_func);     // C 函数
lua_pushvalue(L, idx);             // 复制栈上某值
lua_pushlightuserdata(L, ptr);     // 轻量 userdata（C指针）

// ── 读取操作（不弹出）────────────────────────────────
lua_toboolean(L, idx);             // 转 int (0/1)
lua_tonumber(L, idx);              // 转 lua_Number (double)
lua_tointeger(L, idx);             // 转 lua_Integer
const char *s = lua_tostring(L, idx);  // 转 C 字符串
void *p = lua_touserdata(L, idx);  // 转 void*

// ── 类型检查 ─────────────────────────────────────────
lua_type(L, idx);    // 返回 LUA_TNIL/TBOOLEAN/TNUMBER/TSTRING/TTABLE/TFUNCTION/TUSERDATA
lua_isnumber(L, idx);
lua_isstring(L, idx);
lua_istable(L, idx);
lua_isnoneornil(L, idx);

// ── 栈管理 ───────────────────────────────────────────
lua_gettop(L);                     // 获取栈顶索引（= 元素数量）
lua_settop(L, n);                  // 设置栈大小（n=0 清空）
lua_pop(L, n);                     // 弹出 n 个元素
lua_remove(L, idx);                // 移除指定位置元素
lua_insert(L, idx);                // 将栈顶元素移入指定位置
lua_replace(L, idx);               // 用栈顶替换指定位置
lua_checkstack(L, n);              // 确保有 n 个额外空间

// ── 安全读取（失败时抛 Lua 错误）────────────────────
lua_Number n   = luaL_checknumber(L, 1);
lua_Integer i  = luaL_checkinteger(L, 2);
const char *s  = luaL_checkstring(L, 3);
luaL_checktype(L, 4, LUA_TTABLE);
```

### 2.3 表操作

```c
// 创建表
lua_newtable(L);                   // {} 推入栈顶
lua_createtable(L, arr_n, hash_n); // 预分配大小的表

// 设置字段（key 为字符串）
lua_pushstring(L, "value");
lua_setfield(L, -2, "key");        // table.key = "value"

// 获取字段
lua_getfield(L, idx, "key");       // 推入 table.key

// 数组风格操作
lua_pushinteger(L, 1);             // key
lua_pushstring(L, "element");      // value
lua_settable(L, -3);               // table[1] = "element"

// 迭代表
lua_pushnil(L);                    // 初始 key
while (lua_next(L, table_idx)) {
    // 栈: ... key value
    const char *k = lua_tostring(L, -2);
    // 处理 value ...
    lua_pop(L, 1);                 // 弹出 value，保留 key
}
```

---

## 3. C/C++ ↔ Lua 双向调用详解

### 3.1 从 C 调用 Lua 函数

```c
// Lua 脚本: function update(dt) return dt * 2 end

// 方式一：直接调用
lua_getglobal(L, "update");        // 推入函数
lua_pushnumber(L, delta_time);     // 推入参数
int rc = lua_pcall(L, 1, 1, 0);   // 1 参数, 1 返回值, 0=无错误处理

if (rc != LUA_OK) {
    fprintf(stderr, "Lua error: %s\n", lua_tostring(L, -1));
    lua_pop(L, 1);
} else {
    double result = lua_tonumber(L, -1);
    lua_pop(L, 1);
}

// 方式二：通过 Registry 保存引用（避免重复查全局表）
lua_getglobal(L, "update");
int func_ref = luaL_ref(L, LUA_REGISTRYINDEX);  // 存入注册表

// 之后任意位置调用：
lua_rawgeti(L, LUA_REGISTRYINDEX, func_ref);   // 从注册表取出
lua_pushnumber(L, dt);
lua_pcall(L, 1, 1, 0);

// 释放引用
luaL_unref(L, LUA_REGISTRYINDEX, func_ref);
```

### 3.2 从 Lua 调用 C 函数

**C 函数签名必须是** `int my_func(lua_State *L)`，参数从栈读取，返回值压栈，返回值数量为函数返回的整数。

```c
// 游戏引擎暴露 API 示例：Entity 系统

// C 侧实现
static int entity_create(lua_State *L) {
    const char *name = luaL_checkstring(L, 1);
    float x = luaL_optnumber(L, 2, 0.0f);
    float y = luaL_optnumber(L, 3, 0.0f);

    Entity *e = engine_create_entity(name, x, y);
    
    // 创建 userdata 包装 C 指针
    Entity **ud = (Entity **)lua_newuserdata(L, sizeof(Entity *));
    *ud = e;
    
    // 设置 metatable
    luaL_getmetatable(L, "Entity");
    lua_setmetatable(L, -2);
    
    return 1;  // 返回 1 个值（userdata）
}

static int entity_move(lua_State *L) {
    Entity **ud = (Entity **)luaL_checkudata(L, 1, "Entity");
    float dx = luaL_checknumber(L, 2);
    float dy = luaL_checknumber(L, 3);
    
    entity_set_position(*ud, (*ud)->x + dx, (*ud)->y + dy);
    return 0;  // 无返回值
}

static int entity_get_name(lua_State *L) {
    Entity **ud = (Entity **)luaL_checkudata(L, 1, "Entity");
    lua_pushstring(L, (*ud)->name);
    return 1;
}

static int entity_gc(lua_State *L) {
    Entity **ud = (Entity **)lua_touserdata(L, 1);
    if (*ud) engine_destroy_entity(*ud);
    return 0;
}

// 注册 Entity 类
static const luaL_Reg entity_methods[] = {
    {"move",     entity_move},
    {"get_name", entity_get_name},
    {NULL, NULL}
};

static const luaL_Reg entity_lib[] = {
    {"create", entity_create},
    {NULL, NULL}
};

void register_entity_lib(lua_State *L) {
    // 创建 metatable
    luaL_newmetatable(L, "Entity");
    
    // __index 指向方法表（OOP 调用语法 entity:move(dx, dy)）
    lua_pushvalue(L, -1);
    lua_setfield(L, -2, "__index");
    
    // 注册方法
    luaL_setfuncs(L, entity_methods, 0);
    
    // __gc：Lua GC 时自动调用
    lua_pushcfunction(L, entity_gc);
    lua_setfield(L, -2, "__gc");
    
    lua_pop(L, 1);  // 弹出 metatable
    
    // 创建 Entity 模块表
    luaL_newlib(L, entity_lib);
    lua_setglobal(L, "Entity");
}
```

**Lua 侧使用**：

```lua
local e = Entity.create("Player", 100, 200)
e:move(10, 0)
print(e:get_name())  -- "Player"
-- e 离开作用域时自动调用 __gc
```

### 3.3 错误处理机制

```c
// lua_pcall vs lua_call
// lua_call：错误会传播为 C 长跳转（危险！）
// lua_pcall：捕获错误，返回 LUA_OK / LUA_ERRRUN / LUA_ERRMEM 等

// 自定义错误处理器（msgh 参数）
static int error_handler(lua_State *L) {
    const char *msg = lua_tostring(L, 1);
    
    // 附加 traceback
    luaL_traceback(L, L, msg, 1);
    return 1;
}

// 注册错误处理器并调用
int call_lua_safe(lua_State *L, const char *func, int nargs, int nret) {
    // 压入错误处理器到函数下方
    int err_handler_idx = lua_gettop(L) - nargs;
    lua_pushcfunction(L, error_handler);
    lua_insert(L, err_handler_idx);
    
    int status = lua_pcall(L, nargs, nret, err_handler_idx);
    lua_remove(L, err_handler_idx);  // 移除错误处理器
    
    if (status != LUA_OK) {
        fprintf(stderr, "[LuaError] %s\n", lua_tostring(L, -1));
        lua_pop(L, 1);
        return -1;
    }
    return 0;
}
```

### 3.4 Coroutine 与 C 的交互

```c
// 创建并执行协程
lua_State *co = lua_newthread(L);  // 新协程共享主 lua_State 的全局表

// 将函数移入协程栈
lua_getglobal(L, "my_coroutine");
lua_xmove(L, co, 1);  // 从主栈移到协程栈

// 恢复协程（首次调用或从 yield 恢复）
int nresults;
int status = lua_resume(co, L, 0, &nresults);

while (status == LUA_YIELD) {
    // 处理 yield 返回的值
    float delay = lua_tonumber(co, -1);
    lua_pop(co, nresults);
    
    // 等待 delay 秒后继续...
    sleep(delay);
    status = lua_resume(co, L, 0, &nresults);  // 传入 0 个参数恢复
}

if (status != LUA_OK) {
    fprintf(stderr, "Coroutine error: %s\n", lua_tostring(co, -1));
}
```

---

## 4. 主流游戏引擎集成全景

### 4.1 LÖVE2D — 纯 Lua 引擎

LÖVE2D（love2d.org）是最经典的 Lua 游戏框架，引擎核心用 C++ 编写，完全通过 Lua 暴露 API。

**引擎回调结构**：

```lua
-- main.lua — LÖVE 生命周期回调
function love.load()
    -- 初始化：加载资源、设置状态
    love.window.setTitle("My Game")
    love.window.setMode(800, 600)
    
    player = {
        img = love.graphics.newImage("player.png"),
        x = 400, y = 300,
        speed = 200
    }
    
    -- 物理世界
    world = love.physics.newWorld(0, 300, true)
    body = love.physics.newBody(world, 400, 300, "dynamic")
    shape = love.physics.newRectangleShape(32, 32)
    fixture = love.physics.newFixture(body, shape)
end

function love.update(dt)
    -- 每帧逻辑更新
    world:update(dt)
    
    if love.keyboard.isDown("right") then
        player.x = player.x + player.speed * dt
    end
end

function love.draw()
    -- 渲染（在 love.graphics 批次内）
    love.graphics.clear(0.1, 0.1, 0.2)
    love.graphics.draw(player.img, player.x, player.y)
    
    -- 调试绘制物理形状
    love.graphics.setColor(0, 1, 0, 0.3)
    local bx, by = body:getPosition()
    love.graphics.rectangle("line", bx-16, by-16, 32, 32)
end

function love.keypressed(key)
    if key == "escape" then love.event.quit() end
end

function love.mousepressed(x, y, button)
    if button == 1 then
        -- 左键点击
    end
end
```

**内部实现机制**：LÖVE 在 C++ 层实现所有 Module（graphics, audio, physics 等），通过 `luaL_newlib` 注册为 Lua 模块，主循环从 C++ 触发 `love.update(dt)` 和 `love.draw()`。

### 4.2 Roblox / Luau

Roblox 使用 **Luau**（lua.org 的 Roblox fork），增加了可选静态类型、性能优化和安全沙盒。

**服务端/客户端架构**：

```
Roblox Studio
├── ServerScriptService/    ← 仅服务端执行
│   └── GameManager.lua
├── StarterPlayer/
│   └── StarterPlayerScripts/  ← 仅客户端执行
│       └── UIController.lua
├── ReplicatedStorage/      ← 服务端+客户端共享
│   └── Shared/
│       └── GameConfig.lua
└── Workspace/              ← 3D 场景
```

**RemoteEvent 客户端-服务端通信**：

```lua
-- 服务端：ServerScriptService/GameServer.lua
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

-- 创建 RemoteEvent
local damageEvent = Instance.new("RemoteEvent")
damageEvent.Name = "DamageEvent"
damageEvent.Parent = ReplicatedStorage

-- 监听客户端触发
damageEvent.OnServerEvent:Connect(function(player, targetId, damage)
    -- 验证：服务端永远不信任客户端数据！
    if typeof(damage) ~= "number" or damage > 100 then return end
    
    local target = Players:GetPlayerByUserId(targetId)
    if target then
        local character = target.Character
        local humanoid = character and character:FindFirstChild("Humanoid")
        if humanoid then
            humanoid:TakeDamage(damage)
        end
    end
end)

-- 客户端：StarterPlayerScripts/Combat.lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local damageEvent = ReplicatedStorage:WaitForChild("DamageEvent")

-- 触发服务端事件
damageEvent:FireServer(targetPlayer.UserId, 25)
```

**Luau 类型注解**：

```lua
-- Luau 独有：类型系统
type Vector2 = {x: number, y: number}
type PlayerState = "idle" | "running" | "jumping" | "dead"

local function movePlayer(player: Player, direction: Vector2, speed: number): boolean
    local character = player.Character
    if not character then return false end
    
    local root = character:FindFirstChild("HumanoidRootPart") :: BasePart
    local velocity = Vector3.new(direction.x * speed, 0, direction.y * speed)
    root.AssemblyLinearVelocity = velocity
    return true
end
```

### 4.3 Defold

Defold 是由 King/Defold Foundation 开发的 2D 游戏引擎，使用 Lua 5.1 作为脚本语言。

**消息传递架构**（Defold 最核心的设计）：

```lua
-- /game/player.script
local SPEED = 200
local GRAVITY = -800

function init(self)
    -- self 是 script 组件的上下文
    self.velocity = vmath.vector3(0, 0, 0)
    self.grounded = false
    
    -- 获取动画组件引用
    self.anim_url = msg.url("#sprite")
    msg.post(self.anim_url, "play_animation", {id = hash("idle")})
    
    -- 请求输入焦点
    msg.post(".", "acquire_input_focus")
end

function update(self, dt)
    -- 重力
    if not self.grounded then
        self.velocity.y = self.velocity.y + GRAVITY * dt
    end
    
    -- 移动
    local pos = go.get_position()
    pos = pos + self.velocity * dt
    go.set_position(pos)
    
    -- 碰撞边界
    if pos.y < 0 then
        pos.y = 0
        self.velocity.y = 0
        self.grounded = true
    end
    go.set_position(pos)
end

function on_message(self, message_id, message, sender)
    -- Defold 消息系统：通过 hash 识别消息类型
    if message_id == hash("contact_point_response") then
        -- 碰撞检测响应
        local correction = vmath.vector3()
        if message.distance > 0 then
            local proj = vmath.dot(correction, message.normal)
            local comp = (message.distance - proj) * message.normal
            correction = correction + comp
        end
        go.set_position(go.get_position() + correction)
        
        if message.normal.y > 0.7 then
            self.grounded = true
            self.velocity.y = 0
        end
    end
end

function on_input(self, action_id, action)
    if action_id == hash("jump") and action.pressed and self.grounded then
        self.velocity.y = 500
        self.grounded = false
        msg.post(self.anim_url, "play_animation", {id = hash("jump")})
    end
    
    if action_id == hash("move_right") then
        self.velocity.x = action.value * SPEED
    elseif action_id == hash("move_left") then
        self.velocity.x = -action.value * SPEED
    end
end
```

### 4.4 Unity via MoonSharp/NLua

Unity 原生使用 C#，通过第三方库嵌入 Lua：

**MoonSharp 集成**（推荐，纯 C# 实现）：

```csharp
// C# 侧
using MoonSharp.Interpreter;

[MoonSharpUserData]
public class EntityProxy {
    private GameObject go;
    
    public EntityProxy(GameObject gameObject) { go = gameObject; }
    
    public void Move(float x, float y) {
        go.transform.position += new Vector3(x, y, 0);
    }
    
    public float GetX() => go.transform.position.x;
    public float GetY() => go.transform.position.y;
    
    public void SetAnimation(string name) {
        go.GetComponent<Animator>()?.Play(name);
    }
}

public class LuaScriptRunner : MonoBehaviour {
    private Script luaScript;
    private DynValue updateFunc;
    
    void Start() {
        // 注册代理类型
        UserData.RegisterType<EntityProxy>();
        
        luaScript = new Script();
        
        // 注入引擎对象
        luaScript.Globals["entity"] = new EntityProxy(gameObject);
        luaScript.Globals["Debug"] = (Action<string>)Debug.Log;
        
        // 加载脚本
        string scriptText = Resources.Load<TextAsset>("Scripts/ai_behavior").text;
        luaScript.DoString(scriptText);
        
        // 缓存 update 函数引用
        updateFunc = luaScript.Globals.Get("update");
    }
    
    void Update() {
        if (updateFunc != DynValue.Nil) {
            luaScript.Call(updateFunc, Time.deltaTime);
        }
    }
}
```

```lua
-- Resources/Scripts/ai_behavior.lua (MoonSharp)
local state = "patrol"
local patrol_timer = 0

function update(dt)
    if state == "patrol" then
        patrol_timer = patrol_timer + dt
        entity:Move(math.sin(patrol_timer) * 2 * dt, 0)
        
        if patrol_timer > 5.0 then
            state = "idle"
            patrol_timer = 0
            entity:SetAnimation("idle")
        end
    elseif state == "idle" then
        patrol_timer = patrol_timer + dt
        if patrol_timer > 2.0 then
            state = "patrol"
            entity:SetAnimation("run")
        end
    end
end
```

### 4.5 CryEngine / Lumberyard

CryEngine 内置 Lua 脚本系统，用于实体行为、AI 和关卡脚本：

```lua
-- CryEngine 实体脚本
Script.ReloadScript("Scripts/Utils/EntityUtils.lua")

MyEntity = {
    Properties = {
        bActive = 1,
        fSpeed = 5.0,
        esMovementType = "walk",
    },
    
    -- 编辑器中显示的属性
    Editor = {
        Icon = "object.bmp",
        IconOnTop = 1,
    },
}

function MyEntity:OnInit()
    self:OnReset()
end

function MyEntity:OnPropertyChange()
    self:OnReset()
end

function MyEntity:OnReset()
    if self.Properties.bActive == 1 then
        self:Activate(1)
    end
end

function MyEntity:OnUpdate(dt)
    local dir = {x = 0, y = self.Properties.fSpeed * dt, z = 0}
    self:SetWorldPos(AddVectors(self:GetWorldPos(), dir))
end

function MyEntity:Event_Enable()
    self:Activate(1)
end
```

### 4.6 Cocos2d-x

Cocos2d-x 通过 cocos2d-lua binding 支持 Lua：

```lua
-- Cocos2d-x Lua 绑定
local scene = cc.Scene:create()
local layer = cc.Layer:create()
scene:addChild(layer)

-- 精灵
local sprite = cc.Sprite:create("hero.png")
sprite:setPosition(cc.p(240, 160))
layer:addChild(sprite, 1)

-- 动作系统
local moveRight = cc.MoveBy:create(2.0, cc.p(100, 0))
local moveLeft = moveRight:reverse()
local seq = cc.Sequence:create(moveRight, moveLeft)
sprite:runAction(cc.RepeatForever:create(seq))

-- 物理引擎
local physicsWorld = scene:getPhysicsWorld()
physicsWorld:setGravity(cc.p(0, -300))

local body = cc.PhysicsBody:createBox(cc.size(50, 50))
body:setDynamic(true)
sprite:setPhysicsBody(body)

-- 触摸事件
local listener = cc.EventListenerTouchOneByOne:create()
listener:setSwallowTouches(true)

listener:registerScriptHandler(function(touch, event)
    local location = touch:getLocation()
    local action = cc.MoveTo:create(0.3, location)
    sprite:runAction(action)
    return true
end, cc.Handler.EVENT_TOUCH_BEGAN)

cc.Director:getInstance():getEventDispatcher()
    :addEventListenerWithSceneGraphPriority(listener, sprite)

-- 启动场景
cc.Director:getInstance():runWithScene(scene)
```

### 4.7 Corona SDK / Solar2D

```lua
-- Solar2D (Corona SDK) 游戏示例
local physics = require("physics")
physics.start()
physics.setGravity(0, 9.8)

-- 显示组
local gameGroup = display.newGroup()

-- 创建地面
local ground = display.newRect(gameGroup, display.contentCenterX, display.contentHeight - 25, 
                                display.contentWidth, 50)
ground:setFillColor(0.5, 0.4, 0.3)
physics.addBody(ground, "static", {friction = 0.5})

-- 创建玩家
local player = display.newCircle(gameGroup, 160, 200, 20)
player:setFillColor(0.2, 0.6, 1)
physics.addBody(player, "dynamic", {
    radius = 20,
    bounce = 0.3,
    friction = 0.5,
    density = 1.0
})

-- 运行时事件监听
local function onCollision(event)
    if event.phase == "began" then
        if event.object1 == player or event.object2 == player then
            -- 玩家碰撞处理
            Runtime:addEventListener("tap", function()
                player:setLinearVelocity(0, -400)  -- 跳跃
            end)
        end
    end
end
Runtime:addEventListener("collision", onCollision)

-- 更新循环
Runtime:addEventListener("enterFrame", function(event)
    -- 视口跟随
    local px, py = player.x, player.y
    gameGroup.y = display.contentCenterY - py
end)
```

### 4.8 自定义引擎嵌入 Lua

完整的 C++ 游戏引擎嵌入流程：

```cpp
// engine/scripting/LuaSystem.h
class LuaSystem {
public:
    lua_State* L;
    
    LuaSystem() {
        L = luaL_newstate();
        luaL_openlibs(L);
        RegisterEngineAPI();
    }
    
    ~LuaSystem() { lua_close(L); }
    
    void RegisterEngineAPI() {
        // 注册所有引擎模块
        RegisterModule("Engine", engine_funcs);
        RegisterModule("Entity", entity_funcs);
        RegisterModule("Input", input_funcs);
        RegisterModule("Audio", audio_funcs);
        RegisterModule("Physics", physics_funcs);
        RegisterModule("Graphics", graphics_funcs);
    }
    
    void RegisterModule(const char* name, const luaL_Reg* funcs) {
        luaL_newlib(L, funcs);
        lua_setglobal(L, name);
    }
    
    bool LoadScript(const std::string& path) {
        int status = luaL_loadfile(L, path.c_str());
        if (status != LUA_OK) {
            LogError("Load", path);
            return false;
        }
        status = lua_pcall(L, 0, 0, 0);
        if (status != LUA_OK) {
            LogError("Exec", path);
            return false;
        }
        return true;
    }
    
    template<typename... Args>
    bool CallFunction(const char* func, Args... args) {
        lua_getglobal(L, func);
        if (!lua_isfunction(L, -1)) {
            lua_pop(L, 1);
            return false;
        }
        // 递归展开参数推栈
        PushArgs(args...);
        return lua_pcall(L, sizeof...(args), 0, 0) == LUA_OK;
    }
    
    // 游戏主循环中调用
    void Update(float dt) {
        CallFunction("update", dt);
    }
    
    void Draw() {
        CallFunction("draw");
    }
    
private:
    void LogError(const char* phase, const std::string& path) {
        fprintf(stderr, "[LuaSystem] %s error in '%s': %s\n",
                phase, path.c_str(), lua_tostring(L, -1));
        lua_pop(L, 1);
    }
    
    template<typename T, typename... Rest>
    void PushArgs(T first, Rest... rest) {
        PushValue(first);
        PushArgs(rest...);
    }
    void PushArgs() {}
    
    void PushValue(bool v)        { lua_pushboolean(L, v); }
    void PushValue(int v)         { lua_pushinteger(L, v); }
    void PushValue(float v)       { lua_pushnumber(L, v); }
    void PushValue(double v)      { lua_pushnumber(L, v); }
    void PushValue(const char* v) { lua_pushstring(L, v); }
};
```

---

## 5. 高级集成模式

### 5.1 热重载系统

允许运行时重新加载 Lua 脚本而不重启游戏：

```lua
-- hot_reload.lua
local HotReload = {}
local loaded_modules = {}
local file_timestamps = {}

local function get_mtime(path)
    local f = io.popen("stat -c %Y " .. path .. " 2>/dev/null")
    if not f then return 0 end
    local t = tonumber(f:read("*n")) or 0
    f:close()
    return t
end

function HotReload.watch(module_name, path)
    file_timestamps[module_name] = get_mtime(path)
    loaded_modules[module_name] = path
end

function HotReload.check()
    for name, path in pairs(loaded_modules) do
        local current_mtime = get_mtime(path)
        if current_mtime > file_timestamps[name] then
            file_timestamps[name] = current_mtime
            
            -- 清除旧模块缓存
            package.loaded[name] = nil
            
            -- 重新加载
            local ok, err = pcall(require, name)
            if ok then
                print("[HotReload] Reloaded: " .. name)
                -- 触发重载事件
                if EventBus then
                    EventBus.emit("module_reloaded", name)
                end
            else
                print("[HotReload] Error reloading " .. name .. ": " .. err)
            end
        end
    end
end

-- 在游戏循环中调用（仅调试模式）
-- HotReload.check() 每秒调用一次

return HotReload
```

### 5.2 沙盒执行环境

安全执行不受信任的用户脚本：

```lua
-- sandbox.lua
local Sandbox = {}

-- 白名单：允许使用的安全函数
local SAFE_ENV = {
    -- 数学
    math = {
        abs=math.abs, ceil=math.ceil, floor=math.floor,
        max=math.max, min=math.min, sqrt=math.sqrt,
        sin=math.sin, cos=math.cos, tan=math.tan,
        pi=math.pi, huge=math.huge, random=math.random
    },
    -- 字符串
    string = {
        format=string.format, len=string.len,
        sub=string.sub, find=string.find,
        gmatch=string.gmatch, gsub=string.gsub,
        upper=string.upper, lower=string.lower,
        rep=string.rep, byte=string.byte, char=string.char
    },
    -- 表
    table = {
        insert=table.insert, remove=table.remove,
        sort=table.sort, concat=table.concat,
        unpack=table.unpack or unpack
    },
    -- 基础
    ipairs=ipairs, pairs=pairs, next=next,
    select=select, tostring=tostring, tonumber=tonumber,
    type=type, error=error, pcall=pcall, xpcall=xpcall,
    unpack=table.unpack or unpack,
    setmetatable=setmetatable, getmetatable=getmetatable,
    rawget=rawget, rawset=rawset, rawequal=rawequal, rawlen=rawlen,
    print=print,  -- 或替换为受控输出
    
    -- 禁止的：io, os, require, dofile, loadfile, load, debug
}

function Sandbox.create(allowed_api)
    local env = {}
    -- 深拷贝安全环境
    for k, v in pairs(SAFE_ENV) do
        env[k] = v
    end
    -- 注入额外的游戏 API
    if allowed_api then
        for k, v in pairs(allowed_api) do
            env[k] = v
        end
    end
    env._ENV = env  -- 自引用
    return env
end

function Sandbox.run(code, env, chunk_name)
    chunk_name = chunk_name or "=user_script"
    
    local f, err = load(code, chunk_name, "t", env)
    if not f then
        return false, "Compile error: " .. err
    end
    
    -- 指令计数限制（防止无限循环）
    local instruction_count = 0
    local MAX_INSTRUCTIONS = 1000000
    
    debug.sethook(function()
        instruction_count = instruction_count + 1
        if instruction_count > MAX_INSTRUCTIONS then
            error("Script execution limit exceeded", 2)
        end
    end, "c", 100)  -- 每 100 条指令检查一次
    
    local ok, result = xpcall(f, function(e)
        debug.sethook()  -- 移除 hook
        return debug.traceback(tostring(e), 2)
    end)
    
    debug.sethook()
    
    if not ok then
        return false, result
    end
    return true, result
end

return Sandbox
```

### 5.3 Lua 协程与游戏状态机

```lua
-- coroutine_scheduler.lua
-- 基于协程的任务调度器，实现非阻塞的时序逻辑

local Scheduler = {}
local tasks = {}
local current_time = 0

-- 等待指定秒数
function wait(seconds)
    local resume_time = current_time + seconds
    coroutine.yield(resume_time)
end

-- 等待条件满足
function wait_until(condition_fn)
    while not condition_fn() do
        coroutine.yield(current_time + 0)
    end
end

-- 等待下一帧
function wait_frame()
    coroutine.yield(current_time)
end

function Scheduler.spawn(fn, ...)
    local co = coroutine.create(fn)
    local args = {...}
    local task = {
        co = co,
        resume_at = 0,
        args = args,
        first_run = true
    }
    table.insert(tasks, task)
    return task
end

function Scheduler.update(dt)
    current_time = current_time + dt
    local i = 1
    while i <= #tasks do
        local task = tasks[i]
        if current_time >= task.resume_at then
            local ok, next_resume
            if task.first_run then
                task.first_run = false
                ok, next_resume = coroutine.resume(task.co, table.unpack(task.args))
            else
                ok, next_resume = coroutine.resume(task.co)
            end
            
            if not ok then
                print("[Scheduler] Error: " .. tostring(next_resume))
                table.remove(tasks, i)
            elseif coroutine.status(task.co) == "dead" then
                table.remove(tasks, i)
            else
                task.resume_at = next_resume or current_time
                i = i + 1
            end
        else
            i = i + 1
        end
    end
end

-- ── 使用示例 ────────────────────────────────────────────
-- Scheduler.spawn(function()
--     entity:playAnimation("attack")
--     wait(0.5)                         -- 等 0.5 秒
--     entity:dealDamage(enemy, 25)
--     wait(0.2)
--     entity:playAnimation("idle")
--     wait_until(function() return enemy.hp <= 0 end)
--     print("Enemy defeated!")
-- end)

return Scheduler
```

### 5.4 面向对象与组件系统

```lua
-- oop.lua — Lua 经典 OOP 实现
local Class = {}
Class.__index = Class

function Class:new(o)
    o = o or {}
    setmetatable(o, self)
    self.__index = self
    return o
end

function Class:extend()
    local subclass = {}
    subclass.__index = subclass
    setmetatable(subclass, {
        __index = self,
        __call = function(cls, ...)
            local instance = setmetatable({}, cls)
            if instance.init then instance:init(...) end
            return instance
        end
    })
    subclass.super = self
    return subclass
end

-- ── 组件系统 ────────────────────────────────────────────
local Component = Class:extend()

function Component:init(entity)
    self.entity = entity
    self.enabled = true
end

function Component:update(dt) end
function Component:draw() end
function Component:on_destroy() end

-- ── 实体系统 ────────────────────────────────────────────
local Entity = Class:extend()

function Entity:init(x, y)
    self.x = x or 0
    self.y = y or 0
    self.active = true
    self.components = {}
    self.tags = {}
end

function Entity:add_component(ComponentClass, ...)
    local comp = ComponentClass(self, ...)
    table.insert(self.components, comp)
    return comp
end

function Entity:get_component(ComponentClass)
    for _, comp in ipairs(self.components) do
        if getmetatable(comp) == ComponentClass or
           getmetatable(getmetatable(comp)) == ComponentClass then
            return comp
        end
    end
    return nil
end

function Entity:update(dt)
    if not self.active then return end
    for _, comp in ipairs(self.components) do
        if comp.enabled then comp:update(dt) end
    end
end

function Entity:draw()
    if not self.active then return end
    for _, comp in ipairs(self.components) do
        if comp.enabled then comp:draw() end
    end
end

-- 使用示例
local HealthComponent = Component:extend()
function HealthComponent:init(entity, max_hp)
    HealthComponent.super.init(self, entity)
    self.max_hp = max_hp
    self.hp = max_hp
end
function HealthComponent:take_damage(amount)
    self.hp = math.max(0, self.hp - amount)
    if self.hp == 0 then
        self.entity.active = false
    end
end

-- local player = Entity(100, 200)
-- local health = player:add_component(HealthComponent, 100)
-- health:take_damage(25)

return { Class=Class, Component=Component, Entity=Entity }
```

### 5.5 事件/信号系统

```lua
-- event_bus.lua — 全局事件总线
local EventBus = {}
local listeners = {}

function EventBus.on(event_name, callback, priority)
    priority = priority or 0
    if not listeners[event_name] then
        listeners[event_name] = {}
    end
    local entry = {fn = callback, priority = priority}
    table.insert(listeners[event_name], entry)
    -- 按优先级排序
    table.sort(listeners[event_name], function(a, b)
        return a.priority > b.priority
    end)
    -- 返回取消订阅函数
    return function()
        EventBus.off(event_name, callback)
    end
end

function EventBus.off(event_name, callback)
    if not listeners[event_name] then return end
    for i, entry in ipairs(listeners[event_name]) do
        if entry.fn == callback then
            table.remove(listeners[event_name], i)
            return
        end
    end
end

function EventBus.emit(event_name, ...)
    if not listeners[event_name] then return end
    -- 复制列表防止回调中修改监听器
    local snapshot = {}
    for _, entry in ipairs(listeners[event_name]) do
        table.insert(snapshot, entry)
    end
    for _, entry in ipairs(snapshot) do
        local ok, err = pcall(entry.fn, ...)
        if not ok then
            print("[EventBus] Error in handler for '" .. event_name .. "': " .. err)
        end
    end
end

function EventBus.once(event_name, callback)
    local unsub
    unsub = EventBus.on(event_name, function(...)
        callback(...)
        unsub()
    end)
    return unsub
end

function EventBus.clear(event_name)
    if event_name then
        listeners[event_name] = nil
    else
        listeners = {}
    end
end

return EventBus
```

### 5.6 内存管理与 GC 调优

```lua
-- gc_tuning.lua — Lua GC 调优

-- 查看当前内存使用
local function get_memory_kb()
    return collectgarbage("count")
end

-- GC 模式配置
-- Lua 5.4 引入了增量模式和分代模式
if _VERSION >= "Lua 5.4" then
    -- 分代模式（适合生命周期短的对象为主的场景）
    -- collectgarbage("generational", minor_mul, major_mul)
    collectgarbage("generational", 20, 200)
else
    -- 增量模式（默认）：pause=200, stepmul=200
    -- pause: GC 触发阈值（100=内存翻倍时触发）
    -- stepmul: 每步 GC 工作量（越大越激进）
    collectgarbage("setpause", 150)
    collectgarbage("setstepmul", 400)
end

-- 游戏帧中的 GC 策略
local GCManager = {}
GCManager.step_budget_ms = 1.0  -- 每帧 GC 最多耗时 1ms

function GCManager.update()
    -- 手动步进 GC，控制每帧 GC 时间
    local start = os.clock()
    while (os.clock() - start) * 1000 < GCManager.step_budget_ms do
        if collectgarbage("step", 10) then
            break  -- GC 完成一个完整周期
        end
    end
end

-- 对象池（避免频繁分配/GC）
local ObjectPool = {}
ObjectPool.__index = ObjectPool

function ObjectPool.new(create_fn, reset_fn, initial_size)
    local pool = setmetatable({}, ObjectPool)
    pool.create_fn = create_fn
    pool.reset_fn = reset_fn or function() end
    pool.available = {}
    pool.active = {}
    
    for i = 1, (initial_size or 10) do
        table.insert(pool.available, create_fn())
    end
    return pool
end

function ObjectPool:acquire(...)
    local obj = table.remove(self.available)
    if not obj then
        obj = self.create_fn(...)
    end
    self.reset_fn(obj, ...)
    self.active[obj] = true
    return obj
end

function ObjectPool:release(obj)
    if self.active[obj] then
        self.active[obj] = nil
        table.insert(self.available, obj)
    end
end

-- 使用示例
-- local bullet_pool = ObjectPool.new(
--     function() return {x=0, y=0, vx=0, vy=0, alive=false} end,
--     function(b, x, y, vx, vy) b.x=x; b.y=y; b.vx=vx; b.vy=vy; b.alive=true end,
--     50
-- )
```

---

## 6. LuaJIT 与性能优化

### 6.1 LuaJIT 架构

```
┌────────────────────────────────────────────────┐
│                  LuaJIT                         │
│                                                 │
│  ┌──────────┐  ┌─────────────────────────────┐ │
│  │ Lua 5.1  │  │    Tracing JIT Compiler      │ │
│  │ Bytecode │  │                             │ │
│  │ Interp.  │  │  Hot path → native x86/x64  │ │
│  └──────────┘  └─────────────────────────────┘ │
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │              FFI Library                │   │
│  │  直接调用 C 函数，无需手写绑定代码         │   │
│  └─────────────────────────────────────────┘   │
└────────────────────────────────────────────────┘
```

### 6.2 LuaJIT FFI — 零成本 C 绑定

```lua
-- LuaJIT FFI 示例：直接调用 C 数学库
local ffi = require("ffi")

-- 声明 C 结构和函数
ffi.cdef[[
    typedef struct {
        float x, y, z;
    } Vec3;
    
    typedef struct {
        float m[16];
    } Mat4;
    
    // 声明引擎 C 函数
    void engine_set_transform(int entity_id, const Mat4 *mat);
    Vec3 engine_get_position(int entity_id);
    float engine_distance(Vec3 a, Vec3 b);
    
    // 标准 C 库
    void *malloc(size_t size);
    void free(void *ptr);
    double sqrt(double x);
]]

-- 直接使用 C 结构（无 GC 开销）
local v1 = ffi.new("Vec3", {x=1.0, y=2.0, z=3.0})
local v2 = ffi.new("Vec3", {x=4.0, y=5.0, z=6.0})

-- 调用 C 函数（接近原生速度）
local dist = ffi.C.engine_distance(v1, v2)

-- 批量操作：使用 C 数组
local positions = ffi.new("Vec3[1000]")  -- 1000 个 Vec3
for i = 0, 999 do
    positions[i].x = i * 0.1
    positions[i].y = 0
    positions[i].z = 0
end
```

### 6.3 性能最佳实践

```lua
-- ✅ 好的做法：局部化全局访问
local math_sin = math.sin
local math_cos = math.cos
local math_sqrt = math.sqrt

-- ✅ 预分配表
local vertices = {}
for i = 1, 1000 do vertices[i] = 0 end  -- 预分配避免动态扩展

-- ✅ 避免在热路径中创建闭包
-- ❌ 不好：
for i = 1, n do
    table.sort(items, function(a, b) return a.priority > b.priority end)
end
-- ✅ 好：
local function by_priority(a, b) return a.priority > b.priority end
for i = 1, n do
    table.sort(items, by_priority)
end

-- ✅ 字符串拼接用 table.concat
local parts = {}
for i = 1, 1000 do
    parts[i] = "part" .. i
end
local result = table.concat(parts, ", ")

-- ✅ LuaJIT: 整数运算比浮点快
-- 使用 bit 库进行位操作
local bit = require("bit")
local flags = bit.bor(FLAG_VISIBLE, FLAG_COLLIDABLE)
local is_visible = bit.band(flags, FLAG_VISIBLE) ~= 0
```

---

## 7. 调试与性能分析

### 7.1 调试工具

```lua
-- debug_utils.lua
local Debug = {}

-- 深度打印表结构
function Debug.dump(obj, depth, indent)
    depth = depth or 3
    indent = indent or ""
    local t = type(obj)
    
    if t ~= "table" or depth == 0 then
        return tostring(obj)
    end
    
    local parts = {"{"}
    local next_indent = indent .. "  "
    
    for k, v in pairs(obj) do
        local key = type(k) == "string" and k or "[" .. tostring(k) .. "]"
        local val = Debug.dump(v, depth - 1, next_indent)
        table.insert(parts, next_indent .. key .. " = " .. val)
    end
    
    table.insert(parts, indent .. "}")
    return table.concat(parts, "\n")
end

-- 性能计时器
function Debug.profile(name, fn)
    local t0 = os.clock()
    local results = {fn()}
    local elapsed = (os.clock() - t0) * 1000
    print(string.format("[Profile] %s: %.3f ms", name, elapsed))
    return table.unpack(results)
end

-- 断言增强
function Debug.assert(cond, msg, ...)
    if not cond then
        local formatted = string.format(msg or "Assertion failed", ...)
        error(formatted .. "\n" .. debug.traceback(), 2)
    end
    return cond
end

-- 调用栈打印
function Debug.traceback(msg, level)
    print(debug.traceback(msg, level or 2))
end

return Debug
```

### 7.2 使用 LuaProfiler / ZeroBrane Studio

```lua
-- 用于 ZeroBrane Studio 的远程调试
-- 在脚本最顶部添加：
-- if os.getenv("LUA_DEBUG") then
--     require("mobdebug").start("localhost", 8172)
-- end

-- 轻量性能分析
local Profiler = {}
local call_counts = {}
local call_times = {}

function Profiler.wrap(name, fn)
    return function(...)
        local t0 = os.clock()
        local results = {fn(...)}
        local elapsed = os.clock() - t0
        call_counts[name] = (call_counts[name] or 0) + 1
        call_times[name] = (call_times[name] or 0) + elapsed
        return table.unpack(results)
    end
end

function Profiler.report()
    local sorted = {}
    for name, total in pairs(call_times) do
        table.insert(sorted, {name=name, total=total, count=call_counts[name]})
    end
    table.sort(sorted, function(a, b) return a.total > b.total end)
    
    print("=== Profiler Report ===")
    for _, entry in ipairs(sorted) do
        print(string.format("  %-30s calls=%-6d total=%.3fms avg=%.3fms",
            entry.name, entry.count,
            entry.total * 1000,
            entry.total / entry.count * 1000))
    end
end
```

---

## 8. Luau — Roblox 的类型化 Lua

Luau 是 Roblox 对 Lua 5.1 的扩展，主要特性：

### 8.1 类型系统

```lua
-- Luau 类型注解

-- 基础类型
local x: number = 42
local name: string = "Player"
local active: boolean = true

-- 可选类型
local maybe: string? = nil  -- 等价于 string | nil

-- 函数类型
type Callback = (player: Player, score: number) -> ()
type Transform = (value: number) -> number

-- 泛型
type Array<T> = {T}
type Result<T, E> = {success: true, value: T} | {success: false, error: E}

-- 复合类型
type PlayerData = {
    userId: number,
    displayName: string,
    level: number,
    inventory: Array<string>,
    stats: {
        kills: number,
        deaths: number,
        score: number,
    }
}

-- 交叉类型
type Named = {name: string}
type Aged = {age: number}
type Person = Named & Aged

-- 泛型函数
local function map<T, U>(arr: Array<T>, fn: (T) -> U): Array<U>
    local result: Array<U> = {}
    for i, v in ipairs(arr) do
        result[i] = fn(v)
    end
    return result
end
```

### 8.2 Luau 性能特性

- **向量类型内建**：`Vector3` 等是值类型，无 GC 压力
- **本地化字节码编译**：在首次执行时编译，非解释执行
- **Native codegen**（实验性）：热函数编译为机器码

---

## 9. 工具链与生态系统

### 9.1 包管理

```bash
# LuaRocks — Lua 包管理器
luarocks install lua-cjson    # JSON 解析
luarocks install penlight      # 实用工具库
luarocks install luasocket     # 网络库
luarocks install luafilesystem # 文件系统
luarocks install busted        # 单元测试框架
luarocks install inspect       # 对象打印调试
```

### 9.2 常用库

| 库名 | 用途 | 引擎适用 |
|------|------|---------|
| **LÖVE** | 2D 游戏框架 | 独立 |
| **LuaSocket** | 网络通信 | 所有 |
| **lua-cjson** | JSON 序列化 | 所有 |
| **Penlight** | Python-style 工具库 | 所有 |
| **middleclass** | OOP 库 | 所有 |
| **classic** | 轻量 OOP | LÖVE |
| **hump** | 游戏工具集 | LÖVE |
| **bump.lua** | AABB 碰撞检测 | 所有 |
| **flux** | Tween 动画 | 所有 |
| **lume** | 游戏函数集 | 所有 |
| **cron.lua** | 定时任务 | 所有 |
| **roact** | React-style UI | Roblox |
| **promise** | 异步 Promise | Roblox |

### 9.3 构建工具

```lua
-- .rockspec — LuaRocks 包定义
package = "my-game-lib"
version = "1.0-1"
source = {
    url = "git+https://github.com/user/my-game-lib.git"
}
dependencies = {
    "lua >= 5.1",
    "lua-cjson >= 2.1",
}
build = {
    type = "builtin",
    modules = {
        ["mygame.core"] = "src/core.lua",
        ["mygame.entity"] = "src/entity.lua",
    }
}
```

---

## 10. 架构决策指南

### 10.1 何时选择 Lua

```
适合 Lua 脚本化的场景：
✅ 游戏逻辑（AI、任务、事件）
✅ 配置和数据驱动设计
✅ 玩家自定义内容（Mod 系统）
✅ 快速迭代的游戏规则
✅ 关卡脚本和过场动画序列

不适合 Lua 脚本化的场景：
❌ 渲染管线核心代码
❌ 物理引擎内部实现
❌ 网络底层传输
❌ 音频 DSP 处理
❌ 需要精确内存控制的系统
```

### 10.2 架构模式对比

| 模式 | 优点 | 缺点 | 适用引擎 |
|------|------|------|---------|
| **全 Lua** | 最快迭代 | 性能上限低 | LÖVE, Solar2D |
| **C++ 引擎 + Lua 脚本** | 平衡性能与灵活性 | 绑定维护成本 | 自定义引擎, CryEngine |
| **C# 引擎 + Lua 解释** | 生态丰富 | 双语言开销 | Unity + MoonSharp |
| **Luau 类型化** | 安全性+性能 | 仅 Roblox | Roblox |
| **LuaJIT FFI** | 接近 C 性能 | 复杂性高 | LuaJIT 平台 |

### 10.3 常见陷阱

```lua
-- ❌ 陷阱1：以 0 为数组起始（Lua 数组从 1 开始！）
local arr = {10, 20, 30}
print(arr[0])    -- nil（错误！）
print(arr[1])    -- 10（正确）

-- ❌ 陷阱2：table 引用传递
local function bad_init(t)
    t = {}  -- 这只是修改了局部变量，不影响原表！
end

-- ✅ 正确做法：
local function clear_table(t)
    for k in pairs(t) do t[k] = nil end
end

-- ❌ 陷阱3：混淆 # 操作符
local sparse = {[1]=1, [3]=3}
print(#sparse)  -- 结果未定义！# 只对连续数组可靠

-- ❌ 陷阱4：全局污染（忘记 local）
function update()  -- 这是全局函数！
    position = 100  -- 全局变量！
end

-- ✅ 始终使用 local
local function update()
    local position = 100
end

-- ❌ 陷阱5：字符串比较大小写
if name == "Player" then  -- 大小写敏感！
```

---

*本文档涵盖 Lua 5.1 / 5.4 / LuaJIT / Luau 标准，适用于 LÖVE2D、Roblox、Defold、Unity、CryEngine、Cocos2d-x 等主流引擎环境。*
