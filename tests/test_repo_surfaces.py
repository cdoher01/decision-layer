import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RepoSurfaceTests(unittest.TestCase):
    def test_agents_md_tells_agents_the_rule(self):
        text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("decision contract", text)
        self.assertIn("L1 direction-finding", text)
        self.assertIn("decision run", text)
        self.assertIn("decision review", text)

    def test_plugin_manifest_exposes_mcp_server(self):
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["mcpServers"], ".mcp.json")
        mcp_manifest = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))
        server = mcp_manifest["mcpServers"]["decision-layer"]
        self.assertEqual(server["command"], "python")
        self.assertEqual(server["args"], ["-m", "decision_layer.mcp"])

    def test_github_action_runs_decision_gate(self):
        workflow = (ROOT / ".github" / "workflows" / "decision-layer.yml").read_text(encoding="utf-8")
        self.assertIn("Enforce PR decision clarity", workflow)
        self.assertIn("decision contract", workflow)
        self.assertIn("decision_pr_gate.py", workflow)

    def test_pr_gate_fails_l1_and_passes_l3(self):
        gate = ROOT / ".github" / "scripts" / "decision_pr_gate.py"
        with tempfile.TemporaryDirectory() as tmp:
            l1 = Path(tmp) / "l1.json"
            l3 = Path(tmp) / "l3.json"
            l1.write_text('{"objective": "Improve onboarding", "layer": "L1 direction-finding"}', encoding="utf-8")
            l3.write_text('{"objective": "Implement tests", "layer": "L3 execution"}', encoding="utf-8")

            blocked = subprocess.run([sys.executable, str(gate), str(l1)], capture_output=True, text=True, check=False)
            passed = subprocess.run([sys.executable, str(gate), str(l3)], capture_output=True, text=True, check=False)

            self.assertEqual(blocked.returncode, 1)
            self.assertIn("blocked this PR", blocked.stderr)
            self.assertEqual(passed.returncode, 0)
            self.assertIn("gate passed", passed.stdout)


if __name__ == "__main__":
    unittest.main()

