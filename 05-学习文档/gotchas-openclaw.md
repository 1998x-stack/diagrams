# OpenClaw Gotchas & Deep Configuration Guide

> Based on real-world debugging session on 2026-05-07 with OpenClaw 2026.5.6 (c97b9f7).
> Every gotcha below was discovered through actual production failures, not documentation.

---

## Table of Contents

1. [Architecture: Config Layer Precedence](#1-architecture-config-layer-precedence)
2. [The Proxy Provider Trap (Most Critical)](#2-the-proxy-provider-trap-most-critical)
3. [baseUrl Must Include `/v1`](#3-baseurl-must-include-v1)
4. [Reserved Provider Names Trigger Built-in Plugins](#4-reserved-provider-names-trigger-built-in-plugins)
5. [Auth Cooldown Cascade](#5-auth-cooldown-cascade)
6. [Config Changes Require Gateway Restart](#6-config-changes-require-gateway-restart)
7. [Three Places to Set Default Model](#7-three-places-to-set-default-model)
8. [Auth Profile Triple Registration](#8-auth-profile-triple-registration)
9. [Skills Symlink Escape Spam](#9-skills-symlink-escape-spam)
10. [Gateway Restart Deferred While Processing](#10-gateway-restart-deferred-while-processing)
11. [Security Blocks on URL Fetch](#11-security-blocks-on-url-fetch)
12. [Liveness Warnings Under Normal Load](#12-liveness-warnings-under-normal-load)
13. [Error Messages Are Misleading](#13-error-messages-are-misleading)
14. [Diagnostic Flowchart](#14-diagnostic-flowchart)
15. [Working Configuration Reference](#15-working-configuration-reference)
16. [Quick Debugging Commands](#16-quick-debugging-commands)
17. [The `[1m]` Context Window Suffix Is Client-Side Only](#17-the-1m-context-window-suffix-is-client-side-only)

---

## 1. Architecture: Config Layer Precedence

OpenClaw has **three** config layers that can all define model/provider settings. They do **not** cleanly override — they merge unpredictably:

```
Layer 1: ~/.openclaw/openclaw.json                        (global config)
Layer 2: ~/.openclaw/agents/main/agent/models.json        (agent-level model catalog)
Layer 3: ~/.openclaw/agents/main/agent/auth-profiles.json (auth credentials)
         ~/.openclaw/agents/main/agent/auth-state.json    (runtime auth state + cooldowns)
```

### File Purposes

| File | Purpose | Modified By |
|------|---------|------------|
| `openclaw.json` | Master config: providers, channels, auth profile declarations, defaults | `openclaw config patch/set`, `openclaw models set` |
| `agents/.../models.json` | Agent model catalog — merged with global. Can override provider baseUrl | `openclaw models scan`, manual edit |
| `agents/.../auth-profiles.json` | Actual API keys/tokens per provider | `openclaw models auth add/paste-token`, manual edit |
| `agents/.../auth-state.json` | Runtime state: last-good profile, error counts, **cooldown timers** | Written by gateway at runtime |

### The Merge Trap

`openclaw.json` declares `models.providers.X` and `agents/main/agent/models.json` also declares `providers.X`. The `models.mode: "merge"` setting means both are combined. If they disagree on `baseUrl`, the **agent-level** one can win silently.

**Rule:** Always update BOTH `openclaw.json` AND `agents/.../models.json` when changing provider settings. Or delete the provider from `models.json` and let it inherit from global.

---

## 2. The Proxy Provider Trap (Most Critical)

### Problem

When using an OpenAI-compatible proxy (e.g., LiteLLM, one-api, custom gateways) to serve Claude/GPT/etc., OpenClaw's `openai-completions` adapter sends the model ID **without** the provider prefix in the HTTP request body. However:

- OpenClaw internally references models as `provider/model-id` (e.g., `claude/claude-sonnet-4-6`)
- The HTTP request body `model` field gets only the model `id` value (e.g., `claude-sonnet-4-6`) — **this is correct**
- But the **URL path** to the endpoint is where things break (see Gotcha #3)

### Verified Behavior (via local proxy capture)

```
Request from OpenClaw → POST /chat/completions
Body: {"model": "claude-sonnet-4-6", ...}    ← correct, no prefix
Authorization: Bearer sk-xxx                  ← correct
```

The model ID in the body is **not** prefixed. This means your proxy's model list just needs to match the `id` field in your config, not the `provider/id` format.

### What Proxies Expect vs What OpenClaw Sends

| Proxy Model ID | OpenClaw `id` field | Match? |
|---|---|---|
| `claude-sonnet-4-6` | `claude-sonnet-4-6` | Yes |
| `anthropic/claude-sonnet-4-6` | `claude-sonnet-4-6` | No — proxy won't find it |
| `claude-sonnet-4-6` | `anthropic/claude-sonnet-4-6` | No — OpenClaw sends wrong ID |

**Rule:** The `id` field in the model config must exactly match what your proxy expects in the `model` JSON field.

---

## 3. baseUrl Must Include `/v1`

### Problem

The `openai-completions` adapter appends `/chat/completions` directly to `baseUrl`. It does **NOT** add `/v1/` automatically.

```
baseUrl: "https://my-proxy.com"      → POST https://my-proxy.com/chat/completions     ← 404!
baseUrl: "https://my-proxy.com/v1"   → POST https://my-proxy.com/v1/chat/completions  ← 200!
```

### Evidence

```bash
# Without /v1 — 404
curl -s -o /dev/null -w "%{http_code}" https://llm-proxy.tapsvc.com/chat/completions \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"model":"claude-sonnet-4-6","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'
# 404

# With /v1 — 200
curl -s -o /dev/null -w "%{http_code}" https://llm-proxy.tapsvc.com/v1/chat/completions \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"model":"claude-sonnet-4-6","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'
# 200
```

### Affected Providers

This matters for **all** providers using `"api": "openai-completions"` with custom `baseUrl`. Native providers (Anthropic plugin, Google, etc.) handle their own URL construction.

### Comparison with Other Tools

| Tool | baseUrl behavior |
|------|-----------------|
| OpenAI Python SDK | Appends `/chat/completions` to baseUrl (same as OpenClaw) |
| LangChain | Same — needs `/v1` in baseUrl |
| Claude Code (ANTHROPIC_BASE_URL) | Uses baseUrl directly (includes `/v1` convention) |
| Qwen/DashScope | Their API path is `/compatible-mode/v1` — already includes it |

**Rule:** For `openai-completions` adapter, always include `/v1` (or whatever path prefix your proxy uses) in `baseUrl`.

---

## 4. Reserved Provider Names Trigger Built-in Plugins

### Problem

OpenClaw ships with built-in provider plugins for certain names. When you name a provider with a reserved name, the built-in plugin loads and **overrides your config**, ignoring your `baseUrl`, `api`, and auth settings.

### Verified Reserved Names

| Provider Name | Built-in Plugin | Loaded From |
|---|---|---|
| `anthropic` | Yes — `extensions/anthropic/index.js` | Ships with OpenClaw |
| `openai` | Likely | Ships with OpenClaw |
| `google` | Likely | Ships with OpenClaw |

### What Happens

```
Provider name: "anthropic"
  → OpenClaw loads extensions/anthropic/index.js
  → Plugin ignores your baseUrl and uses api.anthropic.com directly
  → Plugin ignores "api": "openai-completions" and uses native Anthropic API
  → Your proxy token gets sent to the real Anthropic API → auth failure or 404
```

### Evidence from trace log

```
[plugins] loading anthropic from .../dist/extensions/anthropic/index.js
[plugins] loaded 1 plugin(s) (1 attempted) in 35.7ms
Error: No text output returned for provider "anthropic" model "claude-sonnet-4-6".
```

### Solution

Use a **custom provider name** that doesn't collide with built-in plugins:

```json
{
  "models": {
    "providers": {
      "claude": {                               // ← NOT "anthropic"
        "api": "openai-completions",
        "baseUrl": "https://my-proxy.com/v1",
        "models": [...]
      }
    }
  }
}
```

Good names for proxied providers: `claude`, `claude-proxy`, `my-anthropic`, `litellm`, `oneapi`, anything that isn't an exact match for a built-in plugin name.

**Rule:** Never use `anthropic`, `openai`, or `google` as provider names when routing through a proxy. The built-in plugin will hijack the request.

---

## 5. Auth Cooldown Cascade

### Problem

When a model request fails (404, 401, etc.), OpenClaw puts the auth profile into **cooldown**. During cooldown, ALL subsequent requests to that provider are rejected instantly without even trying — producing "Provider X is in cooldown (all profiles unavailable)" errors.

### The Cascade

```
Request 1 → 404 (bad baseUrl) → auth profile marked as failed → cooldown timer starts
Request 2 → instant reject: "Provider in cooldown" → no HTTP request made at all
Request 3 → same instant reject
...
(30 seconds later) cooldown expires
Request N → retries → still 404 (if root cause not fixed) → cooldown again
```

### Cooldown State File

`~/.openclaw/agents/main/agent/auth-state.json`:

```json
{
  "usageStats": {
    "anthropic:default": {
      "errorCount": 1,
      "failureCounts": { "model_not_found": 1 },
      "lastFailureAt": 1778150439030,
      "cooldownUntil": 1778150469030,     // ← 30 seconds after failure
      "cooldownReason": "model_not_found"
    }
  }
}
```

### How to Clear Cooldown

```bash
# Nuclear option: reset entire auth state
cat > ~/.openclaw/agents/main/agent/auth-state.json << 'EOF'
{
  "version": 1,
  "lastGood": {},
  "usageStats": {}
}
EOF

# Then restart gateway
openclaw gateway restart
```

**Rule:** After fixing a provider config issue, always reset `auth-state.json` before testing. Otherwise cooldown will mask whether your fix actually worked.

---

## 6. Config Changes Require Gateway Restart

### Problem

Most config changes in `openclaw.json` are **not** hot-reloaded. The gateway logs:

```
Config overwrite: ~/.openclaw/openclaw.json (sha256 xxx -> yyy)
Applied N config update(s). Restart the gateway to apply.
```

But this message is easy to miss, especially when making multiple changes.

### Which Changes Need Restart

| Change Type | Needs Restart? |
|---|---|
| `models.providers.*` | Yes |
| `auth.profiles.*` | Yes |
| `agents.defaults.model` | Yes |
| `channels.*` | Yes |
| `gateway.port` | Yes |
| Plugin changes | Yes |

### Auto-Restart Deferral

If the gateway is actively processing a request when a config change triggers restart, it **defers** the restart until all active operations complete:

```
[reload] config change requires gateway restart (auth.profiles.anthropic:default)
[reload] restart still deferred after 30046ms with 2 operation(s), 1 reply(ies), 1 embedded run(s) active
[reload] restart still deferred after 60092ms ...
[reload] restart still deferred after 90274ms ...
```

This means your config fix might not take effect for minutes if a long conversation is in progress.

**Rule:** Always run `openclaw gateway restart` after config changes. Don't rely on auto-reload.

---

## 7. Three Places to Set Default Model

### Problem

There are THREE places where the "default model" can be set, and they don't obviously override each other:

```json
// 1. openclaw.json — models.default (set by `openclaw models set`)
{ "models": { "default": "claude/claude-sonnet-4-6" } }

// 2. openclaw.json — agents.defaults.model.primary
{ "agents": { "defaults": { "model": { "primary": "qwen/qwen3.6-plus" } } } }

// 3. agents/.../models.json — default field
{ "default": "anthropic/claude-sonnet-4-6" }
```

### Resolution Order (empirical)

1. `agents.defaults.model.primary` seems to take effect for channel sessions (Feishu, Telegram)
2. `models.default` is what `openclaw models status` displays
3. Agent-level `models.json` `default` can override if set

### Recommendation

Set all three to the same value to avoid confusion:

```bash
# Set via CLI (updates openclaw.json models section)
openclaw models set claude/claude-sonnet-4-6

# Also update agents.defaults
openclaw config patch --stdin <<< '{"agents":{"defaults":{"model":{"primary":"claude/claude-sonnet-4-6"}}}}'

# Also update agent-level (manual edit)
# Set "default": "claude/claude-sonnet-4-6" in agents/main/agent/models.json
```

---

## 8. Auth Profile Triple Registration

### Problem

Auth profiles must be registered in THREE files to work:

1. **`openclaw.json` → `auth.profiles`**: Declares the profile exists and its mode
2. **`agents/.../auth-profiles.json`**: Contains the actual API key
3. **`agents/.../auth-state.json`**: Runtime tracking (auto-managed, but can block if stale)

### Missing any one of these causes different errors:

| Missing File | Error |
|---|---|
| `openclaw.json` auth declaration | `No API key found for provider "X"` |
| `auth-profiles.json` entry | `No API key found for provider "X"` |
| Stale `auth-state.json` | `Provider X is in cooldown` |

### Complete Auth Setup Checklist

```bash
# 1. Add to auth-profiles.json
openclaw models auth paste-token  # interactive

# 2. Register in openclaw.json
openclaw config patch --stdin << 'EOF'
{
  "auth": {
    "profiles": {
      "myprovider:default": {
        "provider": "myprovider",
        "mode": "api_key"
      }
    }
  }
}
EOF

# 3. Verify
openclaw models auth list

# 4. Restart gateway
openclaw gateway restart
```

---

## 9. Skills Symlink Escape Spam

### Problem

If you have skills installed as symlinks that point outside their configured root, the gateway logs a warning on EVERY message dispatch:

```
[skills] Skipping escaped skill path outside its configured root: 
  source=agents-skills-personal 
  root=~/.agents/skills 
  reason=symlink-escape 
  requested=~/.agents/skills/superpowers 
  resolved=~/.codex/superpowers/skills
```

This is **not an error** — it's a security check preventing skills from escaping their sandbox. But it floods the error log, making real errors hard to find.

### Fix

Either:
1. Copy the skills into `~/.agents/skills/` instead of symlinking
2. Or ignore these lines when debugging (they're benign)

---

## 10. Gateway Restart Deferred While Processing

### Problem

When a config change triggers a restart requirement, the gateway won't restart while actively processing messages. It logs deferrals every 30 seconds:

```
[reload] config change requires gateway restart (channels.feishu, plugins.installs.feishu) 
  — deferring until 2 operation(s), 1 reply(ies), 1 embedded run(s) complete
[reload] restart still deferred after 30046ms ...
[reload] restart still deferred after 60092ms ...
```

If a conversation goes on for minutes, your fix won't take effect until it finishes.

### Solution

Force restart with `openclaw gateway restart` — this kills active operations and restarts immediately. The user sees "Something went wrong" on their current message but subsequent messages work with the new config.

---

## 11. Security Blocks on URL Fetch

### Problem

OpenClaw blocks URL fetches to private/internal IP addresses:

```
[security] blocked URL fetch (url-fetch) targetOrigin=https://claude.com 
  reason=Blocked: resolves to private/internal/special-use IP address
```

This affects the agent's ability to fetch certain URLs during tool use. Some public domains may resolve to private IPs in certain network configurations.

---

## 12. Liveness Warnings Under Normal Load

### Problem

The gateway emits `[diagnostic] liveness warning` even under normal single-message processing:

```
[diagnostic] liveness warning: reasons=event_loop_delay interval=30s 
  eventLoopDelayP99Ms=48.6 eventLoopDelayMaxMs=1025.5 
  eventLoopUtilization=0.157 cpuCoreRatio=0.205
```

These are **informational**, not errors. The event loop delay spikes during model calls (which can take seconds) are expected.

### When to Actually Worry

- `eventLoopDelayMaxMs` > 10000 consistently
- `eventLoopUtilization` > 0.8
- Multiple `active` workers with high `age`

---

## 13. Error Messages Are Misleading

### Error Translation Table

| Error Message | Actual Cause |
|---|---|
| `⚠️ Something went wrong while processing your request` | Any unhandled error in agent dispatch — check `gateway.err.log` |
| `No API key found for provider "X"` | Auth profile not registered in ALL three files (see Gotcha #8) |
| `404 status code (no body)` | Wrong `baseUrl` (missing `/v1`) OR proxy doesn't recognize model ID |
| `Provider X is in cooldown (all profiles unavailable)` | Previous request failed; cooldown timer active (see Gotcha #5) |
| `model_not_found` | Could be: wrong baseUrl, wrong model ID, built-in plugin override, or proxy 404 |
| `No text output returned for provider "X" model "Y"` | Inference failed silently — check err log for actual HTTP error |
| `FailoverError: ...` | All configured models/profiles failed; wraps the underlying error |
| `incomplete terminal response` | Model returned data but OpenClaw couldn't parse it as a valid response |

---

## 14. Diagnostic Flowchart

```
User gets "Something went wrong"
│
├─ Step 1: Check gateway.err.log
│  $ tail -20 ~/.openclaw/gateway.err.log
│  │
│  ├─ "No API key found" → Gotcha #8 (auth triple registration)
│  ├─ "404 status code" → Gotcha #3 (baseUrl /v1) + Gotcha #4 (reserved name)  
│  ├─ "cooldown" → Gotcha #5 (reset auth-state.json)
│  └─ No new errors → Gateway didn't restart yet → Gotcha #6 (force restart)
│
├─ Step 2: Test proxy directly
│  $ curl -s https://your-proxy/v1/chat/completions \
│      -H "Authorization: Bearer $KEY" \
│      -H "Content-Type: application/json" \
│      -d '{"model":"your-model-id","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'
│  │
│  ├─ 200 → Proxy works, problem is OpenClaw config
│  ├─ 400 → Model ID format wrong (check proxy's /v1/models)
│  ├─ 401 → API key wrong
│  └─ 404 → URL path wrong (try with/without /v1)
│
├─ Step 3: Verify what OpenClaw is actually sending
│  $ openclaw models status          # shows resolved config
│  $ openclaw models auth list       # shows auth profiles
│  $ cat ~/.openclaw/agents/main/agent/auth-state.json  # check cooldowns
│
└─ Step 4: Nuclear reset
   1. Fix config (openclaw.json + agent models.json)
   2. Reset auth-state.json
   3. openclaw gateway restart
   4. Test: openclaw infer model run --model provider/model --prompt "hi" --gateway
```

---

## 15. Working Configuration Reference

### For OpenAI-compatible proxy serving Claude models

**Provider name: use anything EXCEPT `anthropic`, `openai`, `google`**

#### `~/.openclaw/openclaw.json` (relevant sections)

```json
{
  "models": {
    "mode": "merge",
    "providers": {
      "claude": {
        "api": "openai-completions",
        "baseUrl": "https://your-proxy.com/v1",
        "models": [
          {
            "id": "claude-sonnet-4-6",
            "name": "claude-sonnet-4-6",
            "reasoning": true,
            "input": ["text", "image"],
            "contextWindow": 200000,
            "maxTokens": 8192
          }
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "claude/claude-sonnet-4-6"
      }
    }
  },
  "auth": {
    "profiles": {
      "claude:default": {
        "provider": "claude",
        "mode": "api_key"
      }
    }
  }
}
```

#### `~/.openclaw/agents/main/agent/auth-profiles.json`

```json
{
  "version": 1,
  "profiles": {
    "claude:default": {
      "type": "api_key",
      "provider": "claude",
      "key": "sk-your-proxy-api-key"
    }
  }
}
```

#### `~/.openclaw/agents/main/agent/models.json` (if exists)

Either delete the provider entry and let it inherit from global, or mirror the global config:

```json
{
  "providers": {
    "claude": {
      "api": "openai-completions",
      "baseUrl": "https://your-proxy.com/v1",
      "models": [...]
    }
  },
  "default": "claude/claude-sonnet-4-6"
}
```

### Available API Adapters

| Adapter | Use For |
|---|---|
| `openai-completions` | Any OpenAI-compatible API (proxies, LiteLLM, one-api, etc.) |
| `openai-responses` | OpenAI Responses API |
| `anthropic-messages` | Direct Anthropic API (native, not through proxy) |
| `google-generative-ai` | Google Gemini API |
| `ollama` | Local Ollama |
| `github-copilot` | GitHub Copilot |
| `bedrock-converse-stream` | AWS Bedrock |
| `azure-openai-responses` | Azure OpenAI |
| `openai-codex-responses` | OpenAI Codex |

---

## 16. Quick Debugging Commands

```bash
# Health check
openclaw health

# See resolved model config
openclaw models status

# List auth profiles
openclaw models auth list

# Check for cooldowns
cat ~/.openclaw/agents/main/agent/auth-state.json | python3 -m json.tool

# Watch errors in real-time
tail -f ~/.openclaw/gateway.err.log | grep -v "\[skills\]"

# Test model inference via gateway
openclaw infer model run --model claude/claude-sonnet-4-6 --prompt "say hi" --gateway

# Test model inference locally (bypasses gateway)
openclaw infer model run --model claude/claude-sonnet-4-6 --prompt "say hi" --local

# Test proxy directly
curl -s https://your-proxy/v1/chat/completions \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"claude-sonnet-4-6","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'

# Force gateway restart
openclaw gateway restart

# Reset auth cooldowns
echo '{"version":1,"lastGood":{},"usageStats":{}}' > ~/.openclaw/agents/main/agent/auth-state.json

# Show full config
openclaw config get models
openclaw config get auth
openclaw config get agents.defaults
```

---

## Appendix: How We Discovered Each Gotcha

| # | Symptom | Red Herring | Root Cause | Time to Diagnose |
|---|---------|-------------|------------|-----------------|
| 2 | 400 from proxy | "model ID has prefix" | Actually, model ID was correct; issue was path (see #3) | 20 min |
| 3 | 404 from proxy | "auth not configured" → "wrong model name" | `baseUrl` missing `/v1` — proxy needs `/v1/chat/completions` but OpenClaw sent `/chat/completions` | 40 min |
| 4 | 404 even after fixing baseUrl in config | "config not applied" | Built-in `anthropic` plugin loaded from `extensions/anthropic/index.js`, ignoring all config | 15 min |
| 5 | Instant failures without HTTP request | "proxy is down" | Auth cooldown from previous failure still active | 5 min |
| 7 | Config shows qwen default but uses anthropic | "stale cache" | `agents.defaults.model.primary` overrode `models.default` | 10 min |
| 8 | "No API key found" despite key in auth-profiles.json | "wrong key format" | Auth profile not declared in `openclaw.json` `auth.profiles` section | 10 min |

| 17 | `claude-sonnet-4-6[1m]` returns 400 from proxy | "proxy needs model alias" | `[1m]` is a Claude Code client-side tag, not an API model ID | 15 min |

**Total debugging time: ~2 hours for what was ultimately a 3-line config fix.**

---

## 18. Model Idle Timeout for Slow Proxies

### Problem

The gateway reports:
```
The model did not produce a response before the model idle timeout.
Please try again, or increase `models.providers.<id>.timeoutSeconds` for slow local or self-hosted providers.
```

This happens when the upstream model (typically a proxy) takes too long to respond. The default timeout may be too short for slow proxies or heavily loaded backends.

### Where to Set It

In `~/.openclaw/openclaw.json`, add `timeoutSeconds` to the **provider definition** (not the model entry):

```json
{
  "models": {
    "providers": {
      "claude": {
        "api": "openai-completions",
        "baseUrl": "https://llm-proxy.tapsvc.com/v1",
        "timeoutSeconds": 180,        // ← HERE
        "models": [...] 
      }
    }
  }
}
```

### Scope

`timeoutSeconds` covers the **entire HTTP request**: connect, headers, body, and total request abort handling. Default is typically ~60s. For slow proxies or models that produce long responses, set to 120–300.

**Rule:** Use `models.providers.<id>.timeoutSeconds` for slow provider/model timeouts, NOT `agents.defaults.timeoutSeconds`. The provider-level setting is more targeted.

---

## 19. Thinking Default Must Be Set in agents.defaults

### Problem

You want the agent to always use a higher thinking level (e.g., `high`) by default. Setting it per-message via `/think high` works but doesn't persist across sessions.

### Where to Set It

In `~/.openclaw/openclaw.json`:

```json
{
  "agents": {
    "defaults": {
      "thinkingDefault": "high"
    }
  }
}
```

Valid values: `off`, `minimal`, `low`, `medium`, `high`, `xhigh`, `adaptive`, `max`.

**Note:** The selected provider/model may not support all thinking levels. Qwen models support thinking modes but may handle them differently from Claude's extended thinking. Claude Sonnet 4.6 defaults to `adaptive` thinking when no explicit level is set.

### Requires Gateway Restart

Like most `agents.defaults.*` changes, this requires `openclaw gateway restart` to take effect.

---

## 17. The `[1m]` Context Window Suffix Is Client-Side Only

### Problem

Claude Code displays its model as `claude-opus-4-6[1m]`, suggesting that `[1m]` is part of the model ID. You might naturally try to use `claude-sonnet-4-6[1m]` in OpenClaw config. The proxy rejects it with 400.

### What `[1m]` Actually Means

The `[1m]` suffix is a **Claude Code SDK client-side marker** indicating a 1-million-token context window variant. The SDK parses it locally and sends the **bare model ID** to the API. The `[1m]` never reaches the wire.

```
Claude Code internally:  model = "claude-opus-4-6[1m]"
                                        ↓ SDK strips suffix
Actual API request:      model = "claude-opus-4-6"
                         (context window negotiated separately)
```

### Evidence

```bash
# Proxy model list — no [1m] variants exist
curl -s https://llm-proxy.tapsvc.com/v1/models -H "Authorization: Bearer $KEY" \
  | python3 -c "import json,sys; [print(m['id']) for m in json.load(sys.stdin)['data'] if 'claude' in m['id']]"
# claude-sonnet-4-6
# claude-opus-4-6
# claude-opus-4-7
# claude-haiku-4-5-20251001
# claude-haiku-4-5

# With [1m] — 400
curl -s -o /dev/null -w "%{http_code}" https://llm-proxy.tapsvc.com/v1/chat/completions \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"model":"claude-sonnet-4-6[1m]","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'
# 400

# Both API endpoints reject it — OpenAI-compat AND Anthropic native:
curl -s -o /dev/null -w "%{http_code}" https://llm-proxy.tapsvc.com/v1/messages \
  -H "x-api-key: $KEY" -H "anthropic-version: 2023-06-01" -H "Content-Type: application/json" \
  -d '{"model":"claude-sonnet-4-6[1m]","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'
# 400
```

### How to Get 1M Context in OpenClaw

Set `contextWindow` in the model config — this is the OpenClaw equivalent of `[1m]`:

```json
{
  "models": {
    "providers": {
      "claude": {
        "api": "openai-completions",
        "baseUrl": "https://your-proxy.com/v1",
        "models": [{
          "id": "claude-sonnet-4-6",
          "contextWindow": 1000000,
          "maxTokens": 8192
        }]
      }
    }
  }
}
```

### Quick Reference: Client-Side vs API Model IDs

| What You See | Where | Actual API Model ID |
|---|---|---|
| `claude-opus-4-6[1m]` | Claude Code UI/system prompt | `claude-opus-4-6` |
| `claude-sonnet-4-6[1m]` | Claude Code UI/system prompt | `claude-sonnet-4-6` |
| `claude-opus-4-6` | Proxy `/v1/models` | `claude-opus-4-6` |
| `claude/claude-sonnet-4-6` | OpenClaw internal reference | `claude-sonnet-4-6` (in HTTP body) |

**Rule:** Never put `[1m]` in any config file or API request. It's a Claude Code UI concept only. Use `contextWindow` to control context size.

---

*Last updated: 2026-05-08 — added #18, #19*

---

# OpenClaw Install Guide (Qwen + Telegram)

## Prerequisites

- Node.js 22 LTS+ or Node 24
- Telegram account
- DashScope API key ([home.qwencloud.com/api-keys](https://home.qwencloud.com/api-keys))
- Telegram bot token (from [@BotFather](https://t.me/BotFather))

## 1. Install OpenClaw

```bash
npm install -g openclaw
openclaw --version
```

## 2. Onboard with Qwen (DashScope CN)

```bash
export DASHSCOPE_API_KEY="your-dashscope-api-key"
openclaw onboard --auth-choice qwen-standard-api-key-cn --non-interactive --accept-risk --skip-health
```

This creates `~/.openclaw/openclaw.json` with:
- Provider: `qwen` (DashScope CN)
- Base URL: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- Primary model: `qwen/qwen3.5-plus`

## 3. Persist Environment Variables

Create `~/.openclaw/.env` so the gateway daemon can access credentials:

```bash
cat > ~/.openclaw/.env << 'EOF'
DASHSCOPE_API_KEY=your-dashscope-api-key
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
EOF
chmod 600 ~/.openclaw/.env
```

## 4. Add Telegram Channel

```bash
openclaw config patch '{
 channels: {
 telegram: {
 enabled: true,
 botToken: "your-telegram-bot-token",
 dmPolicy: "pairing",
 groups: { "*": { requireMention: true } }
 }
 }
}'
```

## 5. Start Gateway

```bash
openclaw gateway run
```

## 6. Pair Telegram

1. Open Telegram, send any message to your bot
2. In another terminal:

```bash
openclaw pairing list telegram
openclaw pairing approve telegram <CODE>
```

Pairing codes expire after 1 hour.

## 7. Customize Workspace Files (Optional)

Edit `~/.openclaw/workspace/USER.md` and `~/.openclaw/workspace/AGENTS.md` to set behavioral guidelines. Changes take effect on next session (restart gateway).

## 8. Enable Auto-Start on Boot

```bash
# Enable the systemd user service
systemctl --user enable openclaw-gateway.service

# Enable linger so it starts without login
sudo loginctl enable-linger $(whoami)

# Verify
systemctl --user is-enabled openclaw-gateway.service # → enabled
loginctl show-user $(whoami) | grep Linger # → Linger=yes
```

## Common Commands

| Command | Description |
|---------|-------------|
| `openclaw gateway status` | Check gateway status |
| `openclaw gateway restart` | Restart gateway |
| `openclaw config validate` | Validate config |
| `openclaw models list --provider qwen` | List available models |
| `openclaw logs --follow` | Tail gateway logs |
| `openclaw doctor` | Diagnose issues |

## References

- [OpenClaw Docs](https://docs.openclaw.ai/)
- [Qwen Provider](https://docs.openclaw.ai/providers/qwen)
- [Telegram Channel](https://docs.openclaw.ai/channels/telegram)
- [DashScope API](https://www.alibabacloud.com/help/en/model-studio/compatibility-of-openai-with-dashscope)

---

# 事故记录：2026-05-07 对话中断事件

> 记录时间：2026-05-08 00:33
> 日志来源：`/tmp/openclaw/openclaw-2026-05-07.log`

## 根本原因（Root Cause）

**Claude API 返回了不完整的响应（incomplete terminal response）**，触发了 Gateway 的 config reload + SIGTERM 重启，导致当前对话被中断。

## 完整事件链

```
18:45:25  claude/claude-sonnet-4-6 返回 incomplete terminal response
          → 错误码：code=incomplete_result
          → 无 fallback 模型配置，chain exhausted

18:45:47  Gateway 检测到 config 变更（models.providers.claude.baseUrl）
          → config hot reload applied

18:45:48  Gateway 收到 SIGTERM → 开始 full process restart
          → 飞书 channel 收到 abort signal → 停止
          → 当前对话被中断

18:57:xx  同样流程再次触发（models.providers.claude.models 变更 → 再次 SIGTERM）

22:31~23:21  多次 embedded run timeout（LLM request timed out）
          → 疑似 Claude API 高负载或网络问题
          → event-loop starvation 信号（timerDelayMs 高达 908536ms）

23:05~23:56  Telegram polling stall（getUpdates 卡死 243s~934s）
          → 根因：event-loop 被大量 AI 请求阻塞，Telegram HTTP 请求超时
```

## 核心问题归纳

| 问题 | 表现 | 原因 |
|------|------|------|
| **incomplete_result** | 对话中断，报错 "ended with an incomplete terminal response" | Claude API 在长对话/大 context 时偶发截断 |
| **Config 变更触发 SIGTERM 重启** | 正在进行的对话被强制中断 | `openclaw config patch` 改了 baseUrl/models 后触发 reload → restart |
| **Event-loop starvation** | Timer 延迟高达 177s~908s，Telegram polling 卡死 | 同时跑大量 AI 请求（代码分析、多任务并行），Node.js 单线程被占满 |
| **LLM timeout（多次）** | embedded run 超时报错 | 同上，event-loop 阻塞导致请求无法及时发出 |

## 预防措施

1. **不要在活跃对话中 patch config**：`openclaw config patch` 会触发 Gateway reload/restart，中断正在进行的对话。如需改配置，等对话结束后再操作。

2. **避免同时跑大量并行 AI 任务**：多个并行 embedded run 会导致 Node.js event-loop 阻塞，进而影响所有 channel（Telegram polling 卡死、飞书响应慢）。

3. **配置 fallback 模型**：当前 `fallbackConfigured: false`，Claude 主模型出错后无 fallback，直接失败。建议配置备用模型避免单点故障。

4. **incomplete_result 应对**：Claude API 偶发截断是已知问题，通常在 context 很大时发生。可以考虑开启 `/compact` 或控制单次对话长度。

## 相关日志字段速查

```
错误类型: code=incomplete_result
重启触发: received SIGTERM; restarting
飞书中断: feishu[default]: abort signal received, stopping
loop阻塞: eventLoopDelayHint=timer delayed Xms, likely event-loop starvation
Timeout:  LLM request timed out. / failoverReason=timeout
Telegram: Polling stall detected (active getUpdates stuck for Xs)
```
