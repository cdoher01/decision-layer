import sys
import tempfile
import unittest
from pathlib import Path

from decision_layer.mcp import call_tool, handle_request


class DecisionLayerMcpTests(unittest.TestCase):
    def test_initialize_advertises_tools(self):
        response = handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2025-06-18"},
            }
        )
        self.assertEqual(response["result"]["capabilities"], {"tools": {"listChanged": False}})
        self.assertEqual(response["result"]["serverInfo"]["name"], "decision-layer")

    def test_tools_list_contains_decision_tools(self):
        response = handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        names = {tool["name"] for tool in response["result"]["tools"]}
        self.assertIn("classify_goal", names)
        self.assertIn("create_contract", names)
        self.assertIn("run_bounded_command", names)
        self.assertIn("review_trace", names)

    def test_classify_goal_tool_returns_layer(self):
        result = call_tool("classify_goal", {"goal": "Improve onboarding conversion"})
        self.assertEqual(result["structuredContent"]["layer"], "L1 direction-finding")

    def test_run_bounded_command_tool_blocks_l1_and_writes_trace(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = call_tool(
                "run_bounded_command",
                {
                    "goal": "Improve onboarding conversion",
                    "command": [sys.executable, "-c", "print('should not run')"],
                    "output_dir": tmp,
                },
            )
            self.assertEqual(result["structuredContent"]["status"], "needs_decision")
            self.assertTrue((Path(tmp) / "decision_trace.json").exists())


if __name__ == "__main__":
    unittest.main()

