from __future__ import annotations

import json
import os
import sys
from pathlib import Path


LAYER_1 = "L1 direction-finding"


def main(argv: list[str] | None = None) -> int:
    args = argv or sys.argv[1:]
    if len(args) != 1:
        print("usage: decision_pr_gate.py <decision_contract.json>", file=sys.stderr)
        return 2

    contract_path = Path(args[0])
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    objective = contract.get("objective", "")
    layer = contract.get("layer", "")

    if layer == LAYER_1:
        message = (
            "Decision Layer blocked this PR before implementation.\n\n"
            f"Objective: {objective}\n"
            f"Layer: {layer}\n\n"
            "Clarify the problem, metric, authority, evidence bar, or stopping rule before merging."
        )
        print(message, file=sys.stderr)
        append_summary("## Decision Layer Gate\n\n" + message + "\n")
        return 1

    message = f"Decision Layer gate passed. Objective classified as {layer}."
    print(message)
    append_summary("## Decision Layer Gate\n\n" + message + "\n")
    return 0


def append_summary(text: str) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    with Path(summary_path).open("a", encoding="utf-8") as handle:
        handle.write(text)


if __name__ == "__main__":
    raise SystemExit(main())

