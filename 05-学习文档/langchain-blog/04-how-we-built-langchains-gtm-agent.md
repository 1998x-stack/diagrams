# How We Built LangChain's GTM Agent

**Authors:** Vishnu Suresh, Jess Ou  
**Source:** [LangChain Blog](https://www.langchain.com/blog/how-we-built-langchains-gtm-agent)  
**Date:** March 9, 2026  
**Read Time:** 11 min

---

Every outbound at LangChain used to start the same way: a rep toggling between tabs — Salesforce, Gong, LinkedIn, company website. Fifteen minutes of research before a single word was written.

We built a GTM agent that runs the process end-to-end: triggers on new Salesforce leads, checks whether to reach out, gathers context (including meeting history), and sends a Slack draft (with reasoning + sources) for the rep to approve.

## Key Results

- **Lead-to-qualified-opportunity conversion rate up 250%** (Dec 2025 → Mar 2026)
- **Sales reps reclaimed 40 hours per month each**, totaling 1,320 hours across the team
- **50% daily and 86% weekly active usage** for sales team members

## Non-negotiables

- **Human-in-the-loop**: Nothing is sent without explicit rep review and approval
- **Contact history knowledge**: Check whether a teammate had already reached out
- **Relationship-aware personalization**: Drafts reflect account state (customer vs. warm prospect vs. cold)
- **Explainability**: Reps can see the agent's reasoning and key inputs
- **Learning loop**: Agent learns from rep edits over time

## What We Built

### Inbound Lead Processing

When a new lead shows up in Salesforce:
1. First checks for reasons **not** to send anything (support ticket filed, teammate already reached out)
2. Pulls full Salesforce record, reads Gong transcripts, checks LinkedIn
3. Uses Exa for web research if internal history is sparse
4. Follows a defined outbound **skill** (playbook) covering warm and cold cases
5. Sends Slack DM with buttons to send, edit, or cancel
6. 48-hour SLA for silver leads — auto-sends if rep hasn't responded

### Account Intelligence

Every Monday morning, the agent pulls data from Salesforce and BigQuery, checks the outside world for funding rounds, product launches, and AI initiatives. Tailored reports for two audiences:

- **Sales team**: Expansion opportunities, deal risks, competitive moves
- **Deployed engineers**: Account health, usage trends, open tickets, credit limits

## Architecture

**Deep Agents** was chosen for multi-step orchestration because inputs are inherently spiky — meeting data, CRM history, and web research vary a lot in size and structure. With Deep Agents, large tool results get offloaded into a virtual filesystem automatically.

## Agent Patterns That Emerged

### Memory System

When a rep edits a draft in Slack, the system compares the original against the revised version. An LLM analyzes the diff and extracts structured style observations stored in PostgreSQL, keyed per rep. Every future run reads them before drafting. A weekly cron compacts these memories.

### Subagent Delegation

Account intelligence runs through compiled subagents — lightweight agents with constrained tool sets and structured output schemas. The parent agent spawns one subagent per account, keeping tools isolated and outputs predictable. Subagents can run in parallel.

## Evals and Feedback

- Rule-based assertions check basics: right tools, right order, no duplicate drafts
- LLM judge scores tone, word count, and formatting
- Every Slack action (send, edit, cancel) is tracked and attached to the trace in LangSmith
- Correlates writing patterns with real outcomes across reps

## Learnings

1. **Start with a definition of success, not code** — Build a scenario library before writing production code
2. **Human-in-the-loop goes beyond safety** — It's also a data collection mechanism
3. **Connect to systems of record from the start** — Organic adoption happened because the agent already had access to needed data
4. **Long-running workflows need the right infrastructure** — Deep Agents saved from rebuilding orchestration from scratch
