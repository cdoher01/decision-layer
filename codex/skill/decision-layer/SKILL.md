---
name: decision-layer
description: Use Decision Layer to govern agentic work with a decision contract, bounded command wrapper, and auditable trace. Trigger when the user asks Codex to install or use decision-layer, add decision architecture to a task, create a decision contract, wrap Codex/Claude/OpenHands/shell commands, or stop an agent from executing before L1/L2 decisions are clear.
---

# Decision Layer

Use this skill to put the `decision-layer` CLI in front of an agentic task. The CLI is the deterministic path; use it rather than manually recreating contracts or traces.

## Setup

1. Locate the repository root by walking up from this `SKILL.md` until `pyproject.toml` and `decision_layer/` are present.
2. If `decision --help` works, use the installed command.
3. If `decision --help` is unavailable, install from the repository root:

```bash
python -m pip install .
```

4. Verify:

```bash
decision --help
```

If install is not allowed in the current environment, run the module directly from the repo root:

```bash
python -m decision_layer.cli --help
```

## Workflow

1. Convert the user's task into a clear goal string.
2. Create a contract before execution:

```bash
decision contract --goal "<goal>"
```

3. Decide whether execution is allowed:
   - If the contract classifies the task as `L1 direction-finding`, do not force execution. Report that the problem, metric, authority, or evidence bar must be clarified first.
   - If the task is `L2 solution-selection`, prefer planning or evidence-gathering commands before implementation.
   - If the task is `L3 execution`, run a bounded command.

4. Wrap the selected harness or shell command:

```bash
decision run --harness shell --goal "<goal>" -- <command>
```

Examples:

```bash
decision run --harness codex --goal "Implement the tests" -- codex exec "Implement the tests"
decision run --harness claude-code --goal "Review auth flow" -- claude "Review auth flow"
decision run --harness openhands --goal "Fix failing CI" -- openhands run "Fix failing CI"
decision run --harness shell --goal "Run unit tests" -- python -m unittest
```

5. Review the trace:

```bash
decision review decision_trace.json
```

6. Summarize the result from `decision_trace.md` and `decision_trace.json`: objective, layer, assumptions, evidence, actions, verification, stop reason, and remaining uncertainty.

## Guardrails

- Do not bypass the wrapper when the user asked for decision governance.
- Do not run irreversible or destructive commands unless the user explicitly approved them.
- Treat `needs_decision` as a useful outcome, not a failure.
- Preserve the generated trace files unless the user asks to move or remove them.
- If the wrapper blocks an L1 goal, ask for the missing problem, metric, authority, evidence bar, or stopping rule before execution.
