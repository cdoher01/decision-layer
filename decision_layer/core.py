from __future__ import annotations

import json
import re
import shlex
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


LAYER_1 = "L1 direction-finding"
LAYER_2 = "L2 solution-selection"
LAYER_3 = "L3 execution"


@dataclass
class DecisionContract:
    objective: str
    layer: str
    authority: str = "human approval required for objective, scope, or irreversible action changes"
    constraints: list[str] = field(default_factory=list)
    evidence_bar: str = "agent must name assumptions, evidence used, verification performed, and remaining uncertainty"
    allowed_actions: list[str] = field(default_factory=lambda: ["read", "write", "shell"])
    budget: dict[str, Any] = field(default_factory=lambda: {"max_steps": 1, "timeout_seconds": 120, "max_cost": "not_set"})
    stopping_rule: str = "stop when the objective is verified, a boundary is hit, or a higher-level decision is required"
    harness: str = "shell"

    def is_complete(self) -> bool:
        return all(
            [
                self.objective.strip(),
                self.layer.strip(),
                self.authority.strip(),
                self.evidence_bar.strip(),
                self.stopping_rule.strip(),
            ]
        )


def infer_layer(objective: str) -> str:
    text = objective.lower()
    l1_terms = [
        "improve",
        "increase",
        "reduce",
        "grow",
        "optimize",
        "fix engagement",
        "what should",
        "which problem",
        "where should",
    ]
    l2_terms = ["design", "choose", "select", "plan", "strategy", "architecture", "approach"]
    l3_terms = ["create", "write", "edit", "implement", "run", "test", "ship", "publish", "generate"]

    has_metric = bool(re.search(r"\b\d+%|\bmetric\b|\bby [a-z]+ \d{1,2}\b|\bacceptance\b", text))
    if any(term in text for term in l1_terms) and not has_metric:
        return LAYER_1
    if any(term in text for term in l2_terms):
        return LAYER_2
    if any(term in text for term in l3_terms):
        return LAYER_3
    return LAYER_2


def default_contract(objective: str, harness: str = "shell") -> DecisionContract:
    layer = infer_layer(objective)
    constraints = [
        "do not exceed the declared budget",
        "do not take irreversible actions without approval",
        "preserve an audit trail of assumptions, actions, and verification",
    ]
    if layer == LAYER_1:
        constraints.append("do not execute downstream work until the problem, metric, and evidence bar are explicit")
    return DecisionContract(objective=objective, layer=layer, constraints=constraints, harness=harness)


def parse_simple_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data: dict[str, Any] = {}
    current_key: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- ") and current_key:
            data.setdefault(current_key, []).append(stripped[2:].strip().strip('"'))
            continue
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        current_key = key
        if value == "":
            data[key] = []
        elif value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            data[key] = [] if not inner else [item.strip().strip('"') for item in inner.split(",")]
        elif value.startswith("{") and value.endswith("}"):
            data[key] = json.loads(value)
        else:
            data[key] = value.strip('"')
    return data


def contract_from_config(path: Path, goal: str | None = None, harness: str | None = None) -> DecisionContract:
    config = parse_simple_yaml(path)
    objective = goal or str(config.get("objective", "")).strip()
    if not objective:
        raise ValueError("No objective provided. Pass --goal or set objective in decision.yaml.")
    contract = default_contract(objective, harness or str(config.get("harness", "shell")))
    for field_name in [
        "layer",
        "authority",
        "evidence_bar",
        "allowed_actions",
        "budget",
        "stopping_rule",
        "constraints",
    ]:
        if field_name in config and config[field_name] not in ("", [], {}):
            setattr(contract, field_name, config[field_name])
    return contract


def write_init_file(path: Path) -> bool:
    if path.exists():
        return False
    path.write_text(
        """# Decision Layer config.
objective: "Improve onboarding conversion"
harness: "shell"
authority: "human approval required for objective, scope, or irreversible action changes"
evidence_bar: "name assumptions, evidence used, verification performed, and remaining uncertainty"
allowed_actions:
  - read
  - write
  - shell
budget: {"max_steps": 1, "timeout_seconds": 120, "max_cost": "not_set"}
stopping_rule: "stop when the objective is verified, a boundary is hit, or a higher-level decision is required"
constraints:
  - do not exceed the declared budget
  - do not take irreversible actions without approval
  - preserve an audit trail of assumptions, actions, and verification
""",
        encoding="utf-8",
    )
    return True


def contract_markdown(contract: DecisionContract) -> str:
    constraints = "\n".join(f"- {item}" for item in contract.constraints) or "- none"
    allowed = ", ".join(contract.allowed_actions)
    return f"""# Decision Contract

**Objective:** {contract.objective}

**Layer:** {contract.layer}

**Authority:** {contract.authority}

**Evidence bar:** {contract.evidence_bar}

**Allowed actions:** {allowed}

**Budget:** `{json.dumps(contract.budget, sort_keys=True)}`

**Stopping rule:** {contract.stopping_rule}

## Constraints
{constraints}
"""


def trace_markdown(trace: dict[str, Any]) -> str:
    contract = trace["contract"]
    steps = "\n".join(
        f"- **{step['phase']}**: {step['summary']}" for step in trace.get("loop", [])
    )
    result = trace.get("result") or {}
    return f"""# Decision Trace

## Contract
- **Objective:** {contract['objective']}
- **Layer:** {contract['layer']}
- **Harness:** {contract['harness']}
- **Stopping rule:** {contract['stopping_rule']}

## Loop
{steps}

## Result
- **Status:** {trace['status']}
- **Stop reason:** {trace['stop_reason']}
- **Exit code:** {result.get('exit_code', 'not_run')}
- **Verified:** {trace['verified']}

## Remaining Uncertainty
{trace['remaining_uncertainty']}
"""


def should_execute(contract: DecisionContract, allow_l1_execution: bool) -> tuple[bool, str]:
    if contract.layer == LAYER_1 and not allow_l1_execution:
        return False, "decision_required: L1 direction-finding must clarify problem, metric, and evidence bar before execution"
    if "shell" not in contract.allowed_actions:
        return False, "boundary_hit: shell action is not allowed by the decision contract"
    return True, "execution_allowed"


def run_bounded(
    contract: DecisionContract,
    command: list[str],
    *,
    allow_l1_execution: bool = False,
    output_dir: Path = Path("."),
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    max_steps = int(contract.budget.get("max_steps", 1))
    timeout = int(contract.budget.get("timeout_seconds", 120))
    command_display = " ".join(shlex.quote(part) for part in command) if command else ""
    started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    loop = [
        {"phase": "plan", "summary": f"Classify work as {contract.layer} and prepare a bounded {contract.harness} action."},
        {"phase": "select", "summary": command_display or "No command supplied; decision layer will only emit a contract and trace."},
    ]

    if max_steps < 1:
        trace = _trace(contract, loop, None, "blocked", "boundary_hit: max_steps is less than 1", False, started_at)
        return write_trace(output_dir, trace)

    can_execute, reason = should_execute(contract, allow_l1_execution)
    if not command:
        trace = _trace(contract, loop, None, "needs_action", "no_command_supplied", False, started_at)
        return write_trace(output_dir, trace)
    if not can_execute:
        loop.append({"phase": "decide", "summary": reason})
        trace = _trace(contract, loop, None, "needs_decision", reason, False, started_at)
        return write_trace(output_dir, trace)

    loop.append({"phase": "act", "summary": f"Run command with timeout={timeout}s and max_steps=1."})
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
        result = {
            "command": command,
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
        loop.append({"phase": "observe", "summary": f"Command exited with code {completed.returncode}."})
    except subprocess.TimeoutExpired as exc:
        result = {
            "command": command,
            "exit_code": None,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "timeout": timeout,
        }
        loop.append({"phase": "observe", "summary": f"Command timed out after {timeout}s."})

    verified = result.get("exit_code") == 0
    loop.append({"phase": "update", "summary": "Record command output, exit code, and remaining uncertainty."})
    loop.append({"phase": "verify", "summary": "V1 verification checks successful command exit; domain checks should be added by the harness or reviewer."})
    loop.append({"phase": "decide", "summary": "verified_complete" if verified else "execution_failed"})
    status = "pass" if verified else "fail"
    stop_reason = "verified_complete" if verified else "execution_failed"
    trace = _trace(contract, loop, result, status, stop_reason, verified, started_at)
    return write_trace(output_dir, trace)


def _trace(
    contract: DecisionContract,
    loop: list[dict[str, str]],
    result: dict[str, Any] | None,
    status: str,
    stop_reason: str,
    verified: bool,
    started_at: str,
) -> dict[str, Any]:
    uncertainty = "None recorded by the wrapper." if verified else "Human review required before downstream execution."
    return {
        "schema_version": "0.1",
        "started_at": started_at,
        "contract": asdict(contract),
        "loop": loop,
        "result": result,
        "status": status,
        "stop_reason": stop_reason,
        "verified": verified,
        "remaining_uncertainty": uncertainty,
    }


def write_trace(output_dir: Path, trace: dict[str, Any]) -> dict[str, Any]:
    (output_dir / "decision_trace.json").write_text(json.dumps(trace, indent=2, sort_keys=True), encoding="utf-8")
    (output_dir / "decision_trace.md").write_text(trace_markdown(trace), encoding="utf-8")
    return trace


def review_trace(path: Path) -> dict[str, Any]:
    trace = json.loads(path.read_text(encoding="utf-8"))
    contract = trace.get("contract", {})
    findings: list[str] = []
    if not contract.get("objective"):
        findings.append("missing objective")
    if not contract.get("layer"):
        findings.append("missing decision layer")
    if not contract.get("stopping_rule"):
        findings.append("missing stopping rule")
    if trace.get("stop_reason", "").startswith("decision_required"):
        findings.append("higher-level decision required before execution")
    if trace.get("status") == "fail":
        findings.append("execution failed")
    if not trace.get("verified"):
        findings.append("completion was not verified")

    score = 100
    score -= 20 * len(findings)
    score = max(score, 0)
    status = "pass" if score >= 80 and trace.get("verified") else "needs_decision"
    return {"status": status, "score": score, "findings": findings, "trace": str(path)}
