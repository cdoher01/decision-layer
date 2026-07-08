import json
import sys
import tempfile
import unittest
from pathlib import Path

from decision_layer.core import (
    LAYER_1,
    LAYER_3,
    contract_from_config,
    default_contract,
    infer_layer,
    review_trace,
    run_bounded,
    write_init_file,
)


class DecisionLayerTests(unittest.TestCase):
    def test_infers_direction_finding_for_vague_growth_goal(self):
        self.assertEqual(infer_layer("Improve onboarding conversion"), LAYER_1)

    def test_infers_execution_for_concrete_create_goal(self):
        self.assertEqual(infer_layer("Create a file listing the current directory"), LAYER_3)

    def test_init_and_contract_from_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "decision.yaml"
            self.assertTrue(write_init_file(config))
            contract = contract_from_config(config)
            self.assertEqual(contract.objective, "Improve onboarding conversion")
            self.assertEqual(contract.layer, LAYER_1)

    def test_l1_run_is_blocked_and_writes_trace(self):
        with tempfile.TemporaryDirectory() as tmp:
            contract = default_contract("Improve onboarding conversion")
            trace = run_bounded(contract, ["echo", "hello"], output_dir=Path(tmp))
            self.assertEqual(trace["status"], "needs_decision")
            self.assertFalse(trace["verified"])
            self.assertTrue((Path(tmp) / "decision_trace.json").exists())
            self.assertTrue((Path(tmp) / "decision_trace.md").exists())

    def test_l3_run_executes_and_review_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            contract = default_contract("Create a file listing the current directory")
            trace = run_bounded(contract, [sys.executable, "-c", "print('ok')"], output_dir=Path(tmp))
            self.assertEqual(trace["status"], "pass")
            self.assertTrue(trace["verified"])
            review = review_trace(Path(tmp) / "decision_trace.json")
            self.assertEqual(review["status"], "pass")

    def test_trace_contains_required_contract_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            contract = default_contract("Create a file listing the current directory")
            run_bounded(contract, [sys.executable, "-c", "print('ok')"], output_dir=Path(tmp))
            trace = json.loads((Path(tmp) / "decision_trace.json").read_text())
            for key in ["objective", "layer", "authority", "constraints", "evidence_bar", "allowed_actions", "budget", "stopping_rule"]:
                self.assertIn(key, trace["contract"])


if __name__ == "__main__":
    unittest.main()
