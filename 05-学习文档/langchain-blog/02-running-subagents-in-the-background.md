# Running Subagents in the Background

**Authors:** Hunter Lovell, Colin Francis  
**Source:** [LangChain Blog](https://www.langchain.com/blog/running-subagents-in-the-background)  
**Date:** April 16, 2026  
**Read Time:** 4 min

---

We're starting to ask more of our agents — we want them to take on longer and more complex tasks. As we've done that, the typical way that we've orchestrated agents has started to show some cracks. Async subagents shipped to Deep Agents recently to help address that!

## Where Traditional Subagents Break Down

A subagent is an agent that a supervisor agent delegates scoped work to. This pattern works. But as we've given agents longer and more complex tasks, inline subagents have started to break down.

### Problem 1: Deadlock While Subagents Are Working

Because of the way that tool calling works inside of an agent, the supervisor can't reason about anything else until the tool call has been answered with the subagent response. If a subagent takes an hour, you have to wait an hour before you can interact with the agent again.

### Problem 2: New Information Is Hard to Coordinate

With inline subagents:
- User can't talk to the supervisor while it's blocked
- Subagents can't run concurrently — no cross-pollination of results
- Subagent turns are all-or-nothing — no mid-task updates

## Enter: Async Subagents

A simple way to think about async subagents: subagents that run in the background instead of sequentially. The supervisor launches a task, gets a task ID back immediately, and continues working. It's "fire-and-steer" rather than "fire-and-forget."

### How They Work — Task Management Tools

| Tool | Purpose |
|------|---------|
| `start_async_task` | Launch a task on a remote agent. Returns a task ID immediately |
| `check_async_task` | Poll a task's status and retrieve its result when complete |
| `update_async_task` | Send follow-up instructions to a running task |
| `cancel_async_task` | Cancel a running task |
| `list_async_tasks` | List all tracked tasks with their current statuses |

### Built on Agent Protocol

Async subagents are built on [Agent Protocol](https://github.com/langchain-ai/agent-protocol), a framework-agnostic API specification for managing remote agents. It defines standard endpoints for creating threads, launching runs, polling status, sending updates, and managing long-term memory.

Deployment flexibility: run on LangSmith deployments for a managed experience, or host yourself on your own infrastructure.

### Usage Example (TypeScript)

```typescript
// agents.ts
import { createAgent } from "langchain";
import { createDeepAgent } from "deepagents";

export const researcher = createAgent({
  model: "anthropic:claude-sonnet-4-6",
  instructions: "Perform deep research on the given topic.",
  tools: [searchWeb, readUrl],
});

export const agent = createDeepAgent({
  model: "anthropic:claude-opus-4-6",
  subagents: [{
    name: "researcher",
    description: "Performs deep research on a topic.",
    graphId: "researcher",
  }],
});
```

### Self-hosted

```typescript
export const agent = createDeepAgent({
  model: "anthropic:claude-opus-4-6",
  subagents: [{
    name: "researcher",
    description: "Performs deep research on a topic.",
    graphId: "researcher",
    url: "http://localhost:2024", // points to your self-hosted server
  }],
});
```

The self-hosted server implements Agent Protocol endpoints and can run anywhere — Docker container, VM, or Kubernetes cluster.

---

**Learn more:** [Async Subagents Documentation](https://docs.langchain.com/oss/javascript/deepagents/async-subagents)
