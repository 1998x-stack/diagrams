# The Anatomy of an Agent Harness

**Author:** Vivek Trivedy  
**Source:** [LangChain Blog](https://www.langchain.com/blog/the-anatomy-of-an-agent-harness)  
**Date:** March 10, 2026  
**Read Time:** 12 min

---

TLDR: Agent = Model + Harness. Harness engineering is how we build systems around models to turn them into work engines. The model contains the intelligence and the harness makes that intelligence useful. We define what a harness is and derive the core components today's and tomorrow's agents need.

## Can Someone Please Define a "Harness"?

Agent = Model + Harness

If you're not the model, you're the harness.

A harness is every piece of code, configuration, and execution logic that isn't the model itself. A raw model is not an agent. But it becomes one when a harness gives it things like state, tool execution, feedback loops, and enforceable constraints.

Concretely, a harness includes things like:

- System Prompts
- Tools, Skills, MCPs + and their descriptions
- Bundled Infrastructure (filesystem, sandbox, browser)
- Orchestration Logic (subagent spawning, handoffs, model routing)
- Hooks/Middleware for deterministic execution (compaction, continuation, lint checks)

## Why Do We Need Harnesses? From a Model's Perspective

Models (mostly) take in data like text, images, audio, video and they output text. That's it. Out of the box they cannot:

- Maintain durable state across interactions
- Execute code
- Access realtime knowledge
- Setup environments and install packages to complete work

These are all harness level features. For example, to get a product UX like "chatting", we wrap the model in a while loop to track previous messages and append new user messages.

## Filesystems for Durable Storage and Context Management

Harnesses ship with filesystem abstractions and tools for fs-ops. The filesystem is arguably the most foundational harness primitive because of what it unlocks:

- Agents get a workspace to read data, code, and documentation
- Work can be incrementally added and offloaded instead of holding everything in context
- The filesystem is a natural collaboration surface. Multiple agents and humans can coordinate through shared files
- Git adds versioning so agents can track work, rollback errors, and branch experiments

## Bash + Code as a General Purpose Tool

Harnesses ship with a bash tool so models can solve problems autonomously by writing & executing code. Bash + code exec is a big step towards giving models a computer and letting them figure out the rest autonomously.

## Sandboxes and Tools to Execute & Verify Work

Sandboxes give agents safe operating environments. Instead of executing locally, the harness can connect to a sandbox to run code, inspect files, install dependencies, and complete tasks. Tools like browsers, logs, screenshots, and test runners give agents a way to observe and analyze their work.

## Memory & Search for Continual Learning

For memory, the filesystem is again a core primitive. Harnesses support memory file standards like AGENTS.md which get injected into context on agent start. As agents add and edit this file, harnesses load the updated file into context. This is a form of continual learning where agents durably store knowledge from one session and inject that knowledge into future sessions.

## Battling Context Rot

Context Rot describes how models become worse at reasoning and completing tasks as their context window fills up. Compaction addresses what to do when the context window is close to filling up. Tool call offloading helps reduce the impact of large tool outputs. Skills address the issue of too many tools or MCP servers loaded into context on agent start.

## Long Horizon Autonomous Execution

Long-horizon work requires durable state, planning, observation, and verification to keep working across multiple context windows:

- **Filesystems and git** for tracking work across sessions
- **Ralph Loops** for continuing work — intercepts the model's exit attempt and reinjects the original prompt in a clean context window
- **Planning and self-verification** to stay on track — agents decompose goals into steps and check correctness via tests

## The Future of Harnesses

### The Coupling of Model Training and Harness Design

Today's agent products like Claude Code and Codex are post-trained with models and harnesses in the loop. This creates a feedback loop: useful primitives are discovered, added to the harness, and then used when training the next generation of models.

But this doesn't mean the best harness is the one a model was post-trained with. On Terminal Bench 2.0, Opus 4.6 in Claude Code scores far below Opus 4.6 in other harnesses. By only changing the harness, a coding agent went from Top 30 to Top 5.

### Where Harness Engineering is Going

As models get more capable, some of what lives in the harness today will get absorbed into the model. But harnesses also engineer systems around model intelligence to make them more effective. Open problems being explored:

- Orchestrating hundreds of agents working in parallel on a shared codebase
- Agents that analyze their own traces to identify and fix harness-level failure modes
- Harnesses that dynamically assemble the right tools and context just-in-time

> The model contains the intelligence and the harness is the system that makes that intelligence useful.
