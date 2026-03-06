import importlib.util
import pathlib
import sys
import types
import unittest
from importlib.machinery import SourceFileLoader


ROOT = pathlib.Path(__file__).resolve().parents[2]
LM_PATH = ROOT / "lm"


def load_lm_module():
    loader = SourceFileLoader("lm_module_for_tools", str(LM_PATH))
    spec = importlib.util.spec_from_loader("lm_module_for_tools", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class ToolLoadingIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lm = load_lm_module()

    def test_write_file_tool_is_loaded(self):
        # Stub optional dependency used by web_search tool so load_tools can run in minimal envs.
        fake_ddgs = types.ModuleType("ddgs")
        class DummyDDGS:
            def __init__(self, *args, **kwargs):
                pass
        fake_ddgs.DDGS = DummyDDGS
        sys.modules.setdefault("ddgs", fake_ddgs)

        schemas, funcs = self.lm.load_tools()
        schema_names = []
        for schema in schemas:
            fn = schema.get("function", {})
            schema_names.append(fn.get("name"))

        self.assertIn("write_file", schema_names)
        self.assertIn("write_file", funcs)
        self.assertTrue(callable(funcs["write_file"]))


if __name__ == "__main__":
    unittest.main()
