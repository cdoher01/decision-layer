import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "codex" / "skill" / "decision-layer" / "SKILL.md"
PLUGIN_SKILL = ROOT / "skills" / "decision-layer" / "SKILL.md"
PLUGIN = ROOT / ".codex-plugin" / "plugin.json"


def frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    values = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


class CodexPackagingTests(unittest.TestCase):
    def test_skill_frontmatter_exists(self):
        self.assertTrue(SKILL.exists(), "SKILL.md is missing")
        meta = frontmatter(SKILL.read_text(encoding="utf-8"))
        self.assertEqual(meta.get("name"), "decision-layer")
        self.assertTrue(meta.get("description"))
        self.assertTrue(PLUGIN_SKILL.exists(), "plugin-packaged SKILL.md is missing")
        self.assertEqual(SKILL.read_text(encoding="utf-8"), PLUGIN_SKILL.read_text(encoding="utf-8"))

    def test_skill_instructs_cli_setup_and_trace_flow(self):
        text = SKILL.read_text(encoding="utf-8")
        for expected in [
            "python -m pip install .",
            "decision --help",
            "decision contract",
            "decision run",
            "decision review",
            "needs_decision",
            "decision_trace.md",
            "decision_trace.json",
        ]:
            self.assertIn(expected, text)

    def test_plugin_manifest_points_to_skill_folder(self):
        self.assertTrue(PLUGIN.exists(), "plugin.json is missing")
        manifest = json.loads(PLUGIN.read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "decision-layer")
        self.assertEqual(manifest["skills"], "./skills/")
        skill_root = (ROOT / manifest["skills"]).resolve()
        self.assertTrue((skill_root / "decision-layer" / "SKILL.md").exists())
        self.assertEqual(manifest["interface"]["displayName"], "Decision Layer")


if __name__ == "__main__":
    unittest.main()
