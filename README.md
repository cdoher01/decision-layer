# Decision Layer

Add a governed decision layer to any AI agent in one command.

Decision Layer is a tiny, model-agnostic wrapper for agentic work. It does not replace Codex, Claude Code, OpenHands, shell scripts, or your own harness. It sits above them and forces the work through a simple decision architecture:

```text
contract -> plan -> select -> act -> observe -> update -> verify -> decide
```

The goal is to stop agents from confusing motion with progress. Before work starts, Decision Layer creates a **Decision Contract**: objective, decision layer, authority, constraints, evidence bar, allowed actions, budget, and stopping rule. After the run, it emits a **Decision Trace** as Markdown and JSON.

## Why This Exists

Most agent failures are not model failures. They are decision failures:

- The task was actually direction-finding, but the agent jumped into execution.
- The objective was vague, but the agent optimized a proxy.
- Tool use was allowed, but authority and stopping rules were implicit.
- The agent said "done" without verification.

Decision Layer makes those boundaries explicit.

## Install

```bash
git clone https://github.com/cdoher01/decision-layer.git
cd decision-layer
python -m pip install .
```

## Quickstart

```bash
decision init
decision contract --goal "Improve onboarding conversion"
decision run --goal "Improve onboarding conversion" -- echo "draft onboarding fixes"
decision review decision_trace.json
```

The vague onboarding goal is intentionally classified as **L1 direction-finding**. By default, Decision Layer refuses to execute downstream work until the problem, metric, and evidence bar are explicit.

Example output:

```text
status: needs_decision
stop_reason: decision_required: L1 direction-finding must clarify problem, metric, and evidence bar before execution
```

## Use with Codex

Paste this into Codex:

```text
Install https://github.com/cdoher01/decision-layer as a Codex skill and use it to govern this task.
```

The repo includes a native Codex skill at `codex/skill/decision-layer/SKILL.md`, a plugin-packaged copy at `skills/decision-layer/SKILL.md`, and a plugin manifest at `.codex-plugin/plugin.json`. The skill tells Codex to install and use the `decision` CLI as the deterministic execution path.

Use the CLI directly when you want to govern your own shell commands. Use the Codex skill when you want Codex to set up the CLI, create the contract, run the bounded wrapper, review the trace, and stop before execution when the task is really L1 direction-finding.

## Run a Concrete Execution Task

```bash
decision run --goal "Create a file listing the current directory" -- ls
decision review decision_trace.json
```

That emits:

- `decision_trace.md`
- `decision_trace.json`

## Harness-Agnostic Wrapping

Decision Layer wraps commands. That means any harness can be used as long as it has a command-line entry point:

```bash
decision run --harness codex --goal "Implement the tests" -- codex exec "Implement the tests"
decision run --harness claude-code --goal "Review auth flow" -- claude "Review auth flow"
decision run --harness openhands --goal "Fix failing CI" -- openhands run "Fix failing CI"
decision run --harness shell --goal "Run unit tests" -- python -m unittest
```

No vendor is required. The wrapper records the contract, the bounded action, the result, and the verification state.

## Agent-Ready Surfaces

Decision Layer now ships three repo-native surfaces:

- `AGENTS.md` tells agents the rule: classify vague work before executing, stop on L1, and review traces before claiming completion.
- MCP gives agents the tool: `decision-mcp` exposes `classify_goal`, `create_contract`, `run_bounded_command`, and `review_trace`.
- GitHub Actions enforces the rule automatically: pull requests with L1-style vague titles fail the Decision Layer gate until the objective is clearer.

After install, run the MCP server over stdio:

```bash
decision-mcp
```

For Codex or other MCP clients, configure the command as:

```toml
[mcp_servers.decision-layer]
command = "decision-mcp"
```

The Codex plugin manifest also points to `.mcp.json`, so plugin installs can expose the same MCP tools.

## The Three Decision Layers

| Layer | Use When | Decision Layer Behavior |
| --- | --- | --- |
| L1 direction-finding | Problem or objective is unclear | Stop before execution and force objective/metric/evidence clarity |
| L2 solution-selection | Problem is known, approach is unclear | Require assumptions, alternatives, and evidence before execution |
| L3 execution | Objective and approach are clear | Run a bounded command and verify completion |

## Concrete Decision Examples

The same broad project often contains decisions at all three levels. The level depends on what is still undecided.

- Product onboarding:
  - L1: Decide whether the real problem is signup drop-off, first-run confusion, low-quality traffic, or weak trial-to-paid conversion. Pick the target user, metric, baseline, and evidence bar.
  - L2: Choose between shortening signup, adding an onboarding checklist, rewriting lifecycle emails, changing traffic quality, or improving empty states.
  - L3: Implement the selected checklist copy, add the `checklist_started` event, and run the onboarding tests.
- Engineering reliability:
  - L1: Decide whether "make CI better" means faster feedback, fewer flaky failures, stricter release blocking, or lower infrastructure cost.
  - L2: Choose between quarantining flaky tests, pinning a dependency, splitting slow jobs, increasing timeouts, or rewriting a brittle integration test.
  - L3: Pin the selected dependency, update the workflow file, rerun CI, and verify the failing job passes.
- Customer operations:
  - L1: Decide whether the team should optimize first-response time, resolution quality, escalation rate, renewal risk, or support cost.
  - L2: Choose between new routing rules, a revised priority rubric, agent macros, self-serve docs, or a manager review queue.
  - L3: Add the selected routing rule, update the CRM field mapping, and test it on five sample tickets.
- Research or strategy:
  - L1: Decide which market, buyer, or use case is worth investigating and what evidence would change the strategy.
  - L2: Choose between customer interviews, survey research, usage analysis, competitive research, or a prototype test.
  - L3: Schedule five interviews, summarize the notes, and update the evidence log.

Rule of thumb: L1 decides what success means, L2 decides which path to take, and L3 carries out a chosen path under clear constraints.

## Commands

```bash
decision init
decision contract --goal "..."
decision run --goal "..." -- <command>
decision review decision_trace.json
```

## Tests

```bash
python -m unittest discover -s tests
```

## Philosophy

Decision architecture should be portable. Teams should not need to migrate to a new agent framework to get better governance. The smallest useful layer is a contract, a bounded loop, and a trace that makes the decision legible.

Decision Layer is intentionally small:

- no model dependency
- no vendor lock-in
- no hidden orchestration platform
- one wrapper around the tools you already use

The product promise is simple: **make any AI agent more governable in five minutes.**
