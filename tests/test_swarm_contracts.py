import importlib.util
import pathlib
import unittest
from importlib.machinery import SourceFileLoader


ROOT = pathlib.Path(__file__).resolve().parents[1]
LM_PATH = ROOT / "lm"


def load_lm_module():
    loader = SourceFileLoader("lm_module", str(LM_PATH))
    spec = importlib.util.spec_from_loader("lm_module", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class DummyArgs:
    def __init__(self, max_steps=12):
        self.max_steps = max_steps


class SwarmContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lm = load_lm_module()

    def test_parse_json_payload_with_wrapped_text(self):
        payload = "Some preface\n```json\n{\"status\":\"pass\",\"feedback\":\"ok\"}\n```\ntrailing"
        parsed = self.lm.parse_json_payload(payload)
        self.assertEqual(parsed["status"], "pass")
        self.assertEqual(parsed["feedback"], "ok")

    def test_normalize_critic_review_payload_valid(self):
        parsed = {
            "status": "fail",
            "feedback": "need more checks",
            "summary": "missing evidence",
            "follow_up_tasks": ["  add test  ", "", 123, "verify timeout"],
        }
        norm = self.lm.normalize_critic_review_payload(parsed)
        self.assertIsNotNone(norm)
        self.assertEqual(norm["status"], "fail")
        self.assertEqual(norm["follow_up_tasks"], ["add test", "verify timeout"])
        self.assertFalse(norm["schema_invalid"])

    def test_normalize_critic_review_payload_invalid(self):
        parsed = {"status": "maybe", "feedback": "n/a"}
        norm = self.lm.normalize_critic_review_payload(parsed)
        self.assertIsNone(norm)

    def test_normalize_synth_payload_valid(self):
        parsed = {"status": "ok", "final_answer": "result", "details": "summary"}
        norm = self.lm.normalize_synth_payload(parsed)
        self.assertEqual(norm["status"], "ok")
        self.assertEqual(norm["final_answer"], "result")

    def test_build_output_payload_critic_rejected(self):
        args = DummyArgs(max_steps=12)
        payload = self.lm.build_swarm_output_payload(
            parsed_args=args,
            prompt_text="goal",
            critic_review={"status": "fail", "feedback": "bad schema", "schema_invalid": False},
            synth_result=None,
            final_results=[{"task_id": "task-1", "output": "x"}],
            error_result=None,
        )
        self.assertEqual(payload["status"], "rejected")
        self.assertEqual(payload["error_type"], "critic_rejected")

    def test_build_output_payload_synth_fallback(self):
        args = DummyArgs(max_steps=12)
        payload = self.lm.build_swarm_output_payload(
            parsed_args=args,
            prompt_text="goal",
            critic_review={"status": "pass", "schema_invalid": False},
            synth_result={"status": "error", "details": "synth timeout"},
            final_results=[
                {"task_id": "task-2", "output": "second"},
                {"task_id": "task-1", "output": "first"},
            ],
            error_result=None,
        )
        self.assertEqual(payload["status"], "ok")
        self.assertTrue(payload["fallback_used"])
        self.assertIn("[task-1] first", payload["final_answer"])
        self.assertIn("synth timeout", payload["error"])


if __name__ == "__main__":
    unittest.main()
