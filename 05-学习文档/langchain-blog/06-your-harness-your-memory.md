# Your Harness, Your Memory

**Author:** Harrison Chase  
**Source:** [LangChain Blog](https://www.langchain.com/blog/your-harness-your-memory)  
**Date:** April 11, 2026  
**Read Time:** 7 min

---

Agent harnesses are becoming the dominant way to build agents, and they are not going anywhere. These harnesses are intimately tied to agent memory. If you used a closed harness — especially if it's behind a proprietary API — you are choosing to yield control of your agent's memory to a third party.

## Agent Harnesses Are How You Build Agents

Examples include Claude Code, Deep Agents, Pi (powers OpenClaw), OpenCode, Codex, Letta Code, and more.

When Claude Code's source code was leaked, there were **512k lines of code**. That code is the harness. Even the makers of the best model in the world are investing heavily in harnesses.

## Harnesses Are Tied to Memory

As Sarah Wooders put it: *"Memory isn't a plugin (it's the harness)"*.

A large responsibility of the harness is to interact with context. Managing context, and therefore memory, is a core capability of the agent harness. Memory is just a form of context:

- Short term memory (conversation messages, large tool call results) handled by the harness
- Long term memory (cross-session memory) needs to be updated and read by the harness
- How AGENTS.md/CLAUDE.md files are loaded into context
- How skill metadata is shown to agents
- What survives compaction, and what's lost
- How the current working directory is represented

## If You Don't Own Your Harness, You Don't Own Your Memory

**Mildly bad**: If you use a stateful API (like OpenAI's Responses API), you store state on their server. Swapping models and resuming previous threads is no longer doable.

**Bad**: If you use a closed harness (like Claude Agent SDK), it interacts with memory in an unknown way. The shape of artifacts and how to use them is non-transferable.

**Worst**: When the whole harness, including long-term memory, is behind an API — you have zero ownership or visibility into memory.

Model providers are incentivized to move more behind APIs:
- Anthropic launched Claude Managed Agents — everything behind an API, locked into their platform
- Even though Codex is open source, it generates an encrypted compaction summary not usable outside the OpenAI ecosystem

## Memory Creates Lock-in

With memory, you build up a **proprietary dataset** — a dataset of user interactions and preferences. This allows you to provide a differentiated and increasingly intelligent experience.

Without memory, agents are easily replicable by anyone who has access to the same tools. With memory, you have something that can't be easily copied.

It's been relatively easy to switch model providers because they are stateless. As soon as there's state associated with switching, it's much harder — because this memory matters, and if you switch, you lose access to it.

## Open Memory, Open Harnesses

Memory should be:
- **Open**, owned by whomever is developing the agentic experience
- **Separate from model providers** — you want optionality to try whatever models are best
- **Built on open standards** like agents.md and skills

Deep Agents as an example:
- Open source
- Model agnostic
- Uses open standards (agents.md, skills)
- Plugins to Mongo, Postgres, Redis for storing memories
- Deployable via LangSmith Deployment or self-hosted

> In order to own your memory, you need to be using an Open Harness.
