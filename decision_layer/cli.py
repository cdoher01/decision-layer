from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import (
    contract_from_config,
    contract_markdown,
    default_contract,
    review_trace,
    run_bounded,
    write_init_file,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="decision", description="Add a governed decision layer to any agent in one command.")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Create a starter decision.yaml.")
    init.add_argument("--path", default="decision.yaml", help="Config path to create.")

    contract = sub.add_parser("contract", help="Create a decision contract from a goal or config.")
    contract.add_argument("--goal", help="Objective to govern.")
    contract.add_argument("--config", default="decision.yaml", help="Config path.")
    contract.add_argument("--harness", default="shell", help="Harness name.")
    contract.add_argument("--out", default="decision_contract.json", help="JSON output path.")

    run = sub.add_parser("run", help="Run a bounded command through the decision layer.")
    run.add_argument("--goal", help="Objective to govern.")
    run.add_argument("--config", default="decision.yaml", help="Config path.")
    run.add_argument("--harness", default="shell", help="Harness name.")
    run.add_argument("--output-dir", default=".", help="Where to write decision_trace.md/json.")
    run.add_argument("--allow-l1-execution", action="store_true", help="Allow execution even when the objective is classified as L1.")
    run.add_argument("wrapped_command", nargs=argparse.REMAINDER, help="Command to run after --.")

    review = sub.add_parser("review", help="Review a decision trace.")
    review.add_argument("trace", nargs="?", default="decision_trace.json", help="Trace JSON path.")
    review.add_argument("--json", action="store_true", help="Print JSON review.")

    return parser


def cmd_init(args: argparse.Namespace) -> int:
    created = write_init_file(Path(args.path))
    print(f"created {args.path}" if created else f"exists {args.path}")
    return 0


def cmd_contract(args: argparse.Namespace) -> int:
    if args.goal:
        contract = default_contract(args.goal, args.harness)
    else:
        contract = contract_from_config(Path(args.config), harness=args.harness)
    out = Path(args.out)
    out.write_text(json.dumps(contract.__dict__, indent=2, sort_keys=True), encoding="utf-8")
    out.with_suffix(".md").write_text(contract_markdown(contract), encoding="utf-8")
    print(f"wrote {out} and {out.with_suffix('.md')}")
    print(f"layer: {contract.layer}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    contract = contract_from_config(Path(args.config), goal=args.goal, harness=args.harness)
    command = list(args.wrapped_command)
    if command and command[0] == "--":
        command = command[1:]
    trace = run_bounded(contract, command, allow_l1_execution=args.allow_l1_execution, output_dir=Path(args.output_dir))
    print(f"status: {trace['status']}")
    print(f"stop_reason: {trace['stop_reason']}")
    print(f"wrote {Path(args.output_dir) / 'decision_trace.md'}")
    print(f"wrote {Path(args.output_dir) / 'decision_trace.json'}")
    return 0 if trace["status"] in {"pass", "needs_decision", "needs_action"} else 1


def cmd_review(args: argparse.Namespace) -> int:
    review = review_trace(Path(args.trace))
    if args.json:
        print(json.dumps(review, indent=2, sort_keys=True))
    else:
        print(f"status: {review['status']}")
        print(f"score: {review['score']}")
        for finding in review["findings"]:
            print(f"- {finding}")
    return 0 if review["status"] == "pass" else 1


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            return cmd_init(args)
        if args.command == "contract":
            return cmd_contract(args)
        if args.command == "run":
            return cmd_run(args)
        if args.command == "review":
            return cmd_review(args)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
