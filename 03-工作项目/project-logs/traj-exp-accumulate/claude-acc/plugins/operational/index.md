# operational — Gene Index

**Gene count:** 4

| # | ID | Title | Category | Sessions | Signals (top 3) |
|---|---|---|---|---|---|
| 1 | `gene_cfg_surgical_json_field_update` | Surgical JSON Config Field Update — Precision Single-Field Patch with Preservation Constraint | operational | 2x: 019cf9e3, ef2c887b | `intent:configuration`, `target:build_config`, `mentions_specific_file` |
| 2 | `gene_cfg_build_entry_missing_fix` | UrhoX Build Entry Config Missing — Read entry from project.json and Retry | operational | 4x: 125a7a4a, 68e3fa89, a7d1b207 +1 | `build_error`, `entry_config_missing`, `urhox_sce_build_system` |
| 3 | `gene_mw_github_code_backup_proxy` | GitHub Code Backup Upload — Proxy Config, Subfolder Copy, HTTPS Auth Limitation | operational | 1x: 4c171670 | `intent:meta_workflow`, `github_url_in_prompt`, `code_backup_or_upload_request` |
| 4 | `gene_nf_inaccessible_url_github_asset_fallback` | Auth-Gated URL Fallback — Explain Barrier then Clone Specific Asset from GitHub and Integrate | operational | 1x: c44d6be2 | `intent:content_creation`, `intent:new_feature`, `external_cloud_storage_url_in_prompt` |

---

## `gene_cfg_surgical_json_field_update`

**单字段精准更新：外科手术式 JSON 配置修改** / Surgical JSON Config Field Update — Precision Single-Field Patch with Preservation Constraint

Category: `operational`

**Signals:**
- `intent:configuration`
- `target:build_config`
- `mentions_specific_file`
- `explicit_field_path_specified`
- `preservation_constraint`
- `cn_keywords:zhigenxin,baochi,ziduan,bubian`
- `lua_config_field_named`

**Preconditions:**
- 用户明确指定了目标文件路径（如 .project/project.json）和要更新的字段路径（如 taptap_publish.developer_id）。
- 用户附加了明确的保留约束（如「只更新…字段，保持其他字段不变」）。
- 这是一次单字段值的精确替换或新增，而非整体结构的重构。

**Evidence:** 019cf9e3 T01 (3 steps, 12.6s): user requested update of taptap_publish.developer_id in .project/project.json to 378112, explicitly constraining 'only update developer_id, keep all other fields unchanged'. Agent: (1) Read file to confirm structure, (2) surgical Edit anchoring on the last existing field to append new developer_id at object end, (3) confirm. Diff: only 1 line added (+developer_id:378112) and 1 comma to preceding last field. No reformatting, no adjacent changes. Pattern: field-path + preservation constraint -> read-first + surgical string-anchor edit. | ef2c887b T4 (3 steps, 0 reads, 1 edit, 1 build, 0 errors): user sent [xiugai forcePlayTimeRestrict wei false]. Agent: (1) Edit x1 (direct field value change -- no read-before-edit). (2) build x1. (3) respond. LUA VARIANT: field in Lua game_logic (not JSON build_config); no explicit preservation constraint; no read step (field name unambiguous from prompt); build present to validate logic change. DIFFERS FROM 019cf9e3: (a) Lua not JSON; (b) no read-before-edit; (c) build present; (d) no [baochi qita ziduan bubian] constraint. Pattern generalization: explicit field_name + new_value = minimal single-Edit + Build, regardless of config format.

---

## `gene_cfg_build_entry_missing_fix`

**UrhoX 构建入口配置缺失：从 project.json 读取 entry 并重试** / UrhoX Build Entry Config Missing — Read entry from project.json and Retry

Category: `operational`

**Signals:**
- `build_error`
- `entry_config_missing`
- `urhox_sce_build_system`
- `build_called_without_entry_param`
- `cn_error:入口配置缺失`
- `terse_build_trigger`
- `proactive_glob_before_build`
- `build_called_with_wrong_entry_path`
- `doc_opened_alongside_terse_build`

**Preconditions:**
- 调用 mcp__sce-urhox__build 时仅传入了 scriptsPath，未指定 entry 参数。
- 构建失败，错误信息为「入口配置缺失：请设置 entry（单机游戏）或 entry_client + entry_server（联机 C/S）」。
- 项目根目录下存在 .project/project.json，其中包含 entry 字段（通常为 main.lua）。
- （变体）用户发送的提示词只有一个词「build」，代理在调用构建工具前会主动 Glob 探查项目结构和入口文件，而非等待失败后再修复。
- （错误路径变体）调用 mcp__sce-urhox__build 时传入了错误的 entry 路径（如 games/p1-puzzle-land/main.lua）而非项目根相对路径（main.lua）。构建失败后，用两次 Glob 探查正确路径（先 Glob 游戏目录下 *.lua，未找到；再 Glob scripts/**/main.lua，定位正确路径），然后重调构建。
- （文档伴随变体）用户通过 file:// 在 UI 中打开了某份开发记录文档，同时在提示词中写了「build」。代理先读取该已打开文档（作为上下文确认），再执行主动 Glob + 读取 project.json 的入口发现流程，最后一次性构建成功。

**Evidence:** 125a7a4a T01 (14 steps): after editing outfit-manager.lua, agent called mcp__sce-urhox__build(scriptsPath=scripts) without entry param → error 入口配置缺失：请设置 entry. Recovery: (1) Grep .project/project.json for "entry" → found entry: main.lua. (2) Glob scripts/main*.lua → confirmed /workspace/scripts/main.lua exists. (3) Retry mcp__sce-urhox__build(scriptsPath=scripts, entry=main.lua) → 🎉 构建成功. No code files were changed; the fix was purely a build tool parameter correction. | 68e3fa89 T00 (6 steps, 0 edits, 1 build, 29s total): user sent single-word prompt "build". Agent proactively: (1) Glob scripts/**/*.lua to map project structure and identify main.lua as entry. (2) Glob .project/project.json to confirm entry config. (3) mcp__sce-urhox__build(scriptsPath=scripts, entry=main.lua) → 🎉 构建成功 immediately. Proactive variant: agent infers entry before calling build rather than triggering the error first. Thought: "让我先检查项目结构，找到入口文件。" This is the preventive counterpart to the error-recovery pattern in 125a7a4a. | a7d1b207 T02 (8 steps, feature_modification, level parameter changes): after editing levels.lua for P1 Sokoban, agent called mcp__sce-urhox__build(entry='games/p1-puzzle-land/main.lua') — wrong path variant (entry too deep, not project-root-relative). Build failed. Recovery: (1) Glob 'scripts/games/p1-puzzle-land/*.lua' — listed all .lua files in that dir, confirmed no main.lua there. (2) Glob 'scripts/**/main.lua' — found the correct entry at scripts/main.lua (root-level). (3) Retry mcp__sce-urhox__build(entry='main.lua') → 🎉 构建成功. New variant: wrong-path error (not missing-param error) — recovery requires two Glob steps to confirm the error and find correct path. | b67698e4 T00 (8 steps, 0 edits, 1 build, 41.7s): user opened 开发记录-主线系统M1.md via file:// UI context AND typed 'build' in same prompt. Agent: (1) respond_to_user. (2) Read opened doc 开发记录-主线系统M1.md (courtesy read of the user-opened document). (3) Glob scripts/**/*.lua (project structure discovery). (4) Glob .project/project.json. (5) Read .project/project.json → confirmed entry=main.lua. (6) respond_to_user. (7) mcp__sce-urhox__build(scriptsPath=scripts, entry=main.lua) → 🎉 构建成功. (8) respond_to_user. Doc-alongside-build variant: when user opens a dev log doc via file:// and types 'build' together, agent reads the opened doc first (as context acknowledgment), then performs standard proactive entry discovery (Glob × 2 + Read project.json), then builds successfully in one shot. 8 steps vs 6 in 68e3fa89 due to doc read + extra respond_to_user.

---

## `gene_mw_github_code_backup_proxy`

**GitHub 代码备份上传：代理配置 + 子文件夹复制 + HTTPS 认证限制** / GitHub Code Backup Upload — Proxy Config, Subfolder Copy, HTTPS Auth Limitation

Category: `operational`

**Signals:**
- `intent:meta_workflow`
- `github_url_in_prompt`
- `code_backup_or_upload_request`
- `subfolder_target_specified`
- `cn_keywords:shangchuan,github,xinjianjianjia,cangku,cangku_dizhi,shangchuan_daima`

**Preconditions:**
- 用户提供了一个 GitHub 仓库 URL（HTTPS 格式），要求将当前项目代码上传/备份到该仓库的某个指定子文件夹中。
- UrhoX/TapTap Maker 沙箱环境中访问 GitHub 需要配置本地代理（127.0.0.1:1080）。
- 用户未提供 GitHub 认证凭据（SSH key 或 PAT token），仅提供了 HTTPS 仓库地址和目标子文件夹名。

**Evidence:** 4c171670 T01 (14 steps): user provided GitHub URL https://github.com/Wzp-xd/Tools.git + subfolder name "game001". Agent: (1) TodoWrite 3 tasks. (2) Bash: configure http.proxy + https.proxy to 127.0.0.1:1080 + git clone → success. (3) Bash: mkdir game001 + cp -r /workspace/{scripts,assets,docs,.project} game001/ → success (structure verified via tree). (4) Bash: git config user info + git add game001/ + git commit → TIMED OUT at 15s, but commit 3b7830c succeeded in background. (5) Bash: git status --short | wc -l → 0. (6) Bash: git log --oneline -3 → commit 3b7830c confirmed. (7) Bash: git push origin main || git push origin master → FAILED: "fatal: could not read Username for https://github.com: No such device or address". HTTPS interactive auth is unavailable in this sandbox environment. Agent reported failure and auth limitation to user. Key lessons: proxy is required; git commit can time out but still succeed (verify via git log); HTTPS push always fails without embedded credentials in URL.

---

## `gene_nf_inaccessible_url_github_asset_fallback`

**认证壁垒 URL 触发 GitHub 资源克隆集成：百度网盘无法访问 → 转向 GitHub 克隆指定资产文件** / Auth-Gated URL Fallback — Explain Barrier then Clone Specific Asset from GitHub and Integrate

Category: `operational`

**Signals:**
- `intent:content_creation`
- `intent:new_feature`
- `external_cloud_storage_url_in_prompt`
- `asset_resource_target`
- `auth_gated_download_source`
- `cn_keywords:ziti,xiazai,wangpan,baidu,yingyong,github_cangku,yinyong_wenjian`

**Preconditions:**
- 用户提供了一个需要浏览器登录认证才能下载的云存储链接（如百度网盘），要求下载某个资源文件（字体、图片、音频等）并应用到项目中。
- 沙箱命令行环境无法完成交互式浏览器认证，因此直接下载不可行。
- 用户在收到无法下载的说明后，可能改为提供 GitHub 仓库 URL 并指定仓库中的具体文件路径。

**Evidence:** c44d6be2 T0 (json idx 0, 1 step, 0 edits, 0 builds): 用户提供百度网盘链接 https://pan.baidu.com/s/1DMcj2R6vchEeTB_KWPQ0sw?pwd=4pi2，要求下载字体文件并应用到项目。Agent: 1步 respond_to_user（无工具调用）。思考内容：「百度网盘需要浏览器登录认证才能下载，命令行环境无法完成这个操作」，提供三条恢复建议：(1) 用户本地下载后上传；(2) 提供字体文件名；(3) 直接拖拽文件到对话。关键点：agent 不尝试任何下载命令，直接通过文本说明解释限制并引导用户提供替代方案。

c44d6be2 T1 (json idx 1, 27 steps, 6 edits, 1 build): 用户提供 GitHub 仓库 https://github.com/Wzp-xd/Tools.git，指定引用 LongZhuTi-Regular.ttf。Agent 执行完整资产获取+集成流程：
  Step 1: Bash — git clone --depth 1 https://github.com/Wzp-xd/Tools.git（浅克隆）
  Step 2: Bash — find /workspace/Tools -name 'LongZhuTi-Regular.ttf'（定位文件）
  Step 3: respond_to_user（找到文件，准备复制）
  Step 4: Bash — mkdir -p /workspace/assets/Fonts && cp .../LongZhuTi-Regular.ttf /workspace/assets/Fonts/
  Step 5: respond_to_user（文件已就位，了解项目结构）
  Step 6: Glob（扫描项目结构）
  Step 7: respond_to_user（了解字体配置入口）
  Step 8: Grep（搜索 nvgCreateFont 引用）
  Step 9: Grep（搜索 UI.Init 字体配置）
  Step 10: Read（/workspace/scripts/main.lua，了解集成入口）
  Step 11: respond_to_user（确认 UI.Init + nvgCreateFont 两种引用模式）
  Step 12: TodoWrite（3任务：修改初始化配置 + 替换适配器引用 + 构建验证）
  Steps 13-18: 6x Edit（main.lua + p4/adapter.lua + home/init.lua + p3/adapter.lua + p2/adapter.lua + p1/adapter.lua — 全项目字体引用批量替换）
  Step 19: respond_to_user（确认全部替换完毕）
  Step 20: Grep（验证无遗漏旧路径）
  Step 21: respond_to_user（准备构建）
  Step 22: TodoWrite（更新状态）
  Step 23: mcp__sce-urhox__build（构建成功）
  Step 24: TodoWrite（标记完成）
  Step 25: respond_to_user（完整回顾所有改动）
总计：3 Bash + 6 Edit + 1 Build + 3 Grep/Glob + 多次 respond_to_user + TodoWrite。注意：本次 GitHub 访问无需额外代理配置（与 gene_mw_github_code_backup_proxy 的上传场景不同），浅克隆在沙箱中直接成功，无认证问题（公开仓库 + 只读操作）。

---
