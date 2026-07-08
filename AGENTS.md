# AGENTS.md

## Decision Layer Rule

This repo is the reference implementation for Decision Layer. Agents working here should use the project itself to govern ambiguous work.

- Before executing vague or agentic work, run `decision contract --goal "<goal>"`.
- If the result is `L1 direction-finding`, stop before implementation and ask for the missing problem, metric, authority, evidence bar, or stopping rule.
- If the result is `L2 solution-selection`, gather alternatives and evidence before implementation.
- If the result is `L3 execution`, run bounded work with `decision run --goal "<goal>" -- <command>`.
- After a governed run, review the trace with `decision review decision_trace.json`.

## Development Commands

```bash
python -m pip install .
python -m unittest discover -s tests
```

For MCP smoke testing after install:

```bash
decision-mcp
```

