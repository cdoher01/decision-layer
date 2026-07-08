from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .core import default_contract, infer_layer, review_trace, run_bounded


PROTOCOL_VERSION = "2025-06-18"
SERVER_NAME = "decision-layer"
SERVER_VERSION = "0.1.0"


class ToolInputError(ValueError):
    pass


TOOLS: list[dict[str, Any]] = [
    {
        "name": "classify_goal",
        "title": "Classify Goal",
        "description": "Classify a goal as L1 direction-finding, L2 solution-selection, or L3 execution.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal": {"type": "string", "description": "The goal or task to classify."}
            },
            "required": ["goal"],
        },
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "create_contract",
        "title": "Create Decision Contract",
        "description": "Create a Decision Contract for a goal without executing work.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal": {"type": "string", "description": "The goal to govern."},
                "harness": {"type": "string", "description": "The harness name.", "default": "shell"},
            },
            "required": ["goal"],
        },
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "run_bounded_command",
        "title": "Run Bounded Command",
        "description": "Run a command through Decision Layer and write decision_trace.md/json.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal": {"type": "string", "description": "The governed objective."},
                "command": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Command argv to execute. Do not pass a shell string.",
                },
                "harness": {"type": "string", "description": "The harness name.", "default": "shell"},
                "output_dir": {"type": "string", "description": "Directory for trace files.", "default": "."},
                "allow_l1_execution": {
                    "type": "boolean",
                    "description": "Allow execution even if the goal is classified as L1.",
                    "default": False,
                },
            },
            "required": ["goal", "command"],
        },
    },
    {
        "name": "review_trace",
        "title": "Review Decision Trace",
        "description": "Review an existing decision_trace.json file.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to decision_trace.json.", "default": "decision_trace.json"}
            },
            "required": [],
        },
        "annotations": {"readOnlyHint": True},
    },
]


def handle_request(message: dict[str, Any]) -> dict[str, Any] | None:
    request_id = message.get("id")
    method = message.get("method")
    params = message.get("params") or {}

    if "id" not in message and method == "notifications/initialized":
        return None
    if not isinstance(params, dict):
        return error_response(request_id, -32602, "params must be an object")

    if method == "initialize":
        requested = params.get("protocolVersion")
        protocol_version = requested if requested == PROTOCOL_VERSION else PROTOCOL_VERSION
        return result_response(
            request_id,
            {
                "protocolVersion": protocol_version,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {
                    "name": SERVER_NAME,
                    "title": "Decision Layer",
                    "version": SERVER_VERSION,
                },
                "instructions": (
                    "Use Decision Layer to classify goals, create decision contracts, "
                    "run bounded commands, and review decision traces. Treat L1 results "
                    "as a stop signal unless the user explicitly approves execution."
                ),
            },
        )
    if method == "ping":
        return result_response(request_id, {})
    if method == "tools/list":
        return result_response(request_id, {"tools": TOOLS})
    if method == "tools/call":
        try:
            name = _required_str(params, "name")
            arguments = params.get("arguments") or {}
            if not isinstance(arguments, dict):
                raise ToolInputError("arguments must be an object")
            return result_response(request_id, call_tool(name, arguments))
        except ToolInputError as exc:
            return result_response(request_id, tool_result({"error": str(exc)}, is_error=True))
        except Exception as exc:
            return result_response(request_id, tool_result({"error": str(exc)}, is_error=True))
    if "id" not in message:
        return None
    return error_response(request_id, -32601, f"method not found: {method}")


def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "classify_goal":
        goal = _required_str(arguments, "goal")
        return tool_result({"goal": goal, "layer": infer_layer(goal)})

    if name == "create_contract":
        goal = _required_str(arguments, "goal")
        harness = _optional_str(arguments, "harness", "shell")
        contract = default_contract(goal, harness)
        return tool_result({"contract": asdict(contract)})

    if name == "run_bounded_command":
        goal = _required_str(arguments, "goal")
        command = _required_command(arguments, "command")
        harness = _optional_str(arguments, "harness", "shell")
        output_dir = Path(_optional_str(arguments, "output_dir", "."))
        allow_l1_execution = bool(arguments.get("allow_l1_execution", False))
        contract = default_contract(goal, harness)
        trace = run_bounded(
            contract,
            command,
            allow_l1_execution=allow_l1_execution,
            output_dir=output_dir,
        )
        return tool_result(trace)

    if name == "review_trace":
        path = Path(_optional_str(arguments, "path", "decision_trace.json"))
        return tool_result(review_trace(path))

    raise ToolInputError(f"unknown tool: {name}")


def tool_result(data: dict[str, Any], *, is_error: bool = False) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": json.dumps(data, indent=2, sort_keys=True)}],
        "structuredContent": data,
        "isError": is_error,
    }


def result_response(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def error_response(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def _required_str(arguments: dict[str, Any], key: str) -> str:
    value = arguments.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ToolInputError(f"{key} must be a non-empty string")
    return value.strip()


def _optional_str(arguments: dict[str, Any], key: str, default: str) -> str:
    value = arguments.get(key, default)
    if not isinstance(value, str) or not value.strip():
        raise ToolInputError(f"{key} must be a non-empty string")
    return value.strip()


def _required_command(arguments: dict[str, Any], key: str) -> list[str]:
    value = arguments.get(key)
    if not isinstance(value, list) or not value:
        raise ToolInputError(f"{key} must be a non-empty array of strings")
    if not all(isinstance(item, str) and item for item in value):
        raise ToolInputError(f"{key} must be a non-empty array of strings")
    return value


def write_message(message: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(message, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def main() -> int:
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            message = json.loads(raw)
        except json.JSONDecodeError as exc:
            write_message(error_response(None, -32700, f"parse error: {exc.msg}"))
            continue
        if not isinstance(message, dict):
            write_message(error_response(None, -32600, "invalid request"))
            continue
        response = handle_request(message)
        if response is not None:
            write_message(response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

