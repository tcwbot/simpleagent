import os
import shutil
import tempfile
import unittest
from pathlib import Path

from tools import write_file


class WriteFileToolTests(unittest.TestCase):
    def setUp(self):
        self.original_cwd = os.getcwd()
        self.original_workspace_root = os.environ.get("SIMPLEAGENT_WORKSPACE_ROOT")
        self.tmpdir = tempfile.mkdtemp(prefix="write-file-tool-test-")
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.original_cwd)
        if self.original_workspace_root is None:
            os.environ.pop("SIMPLEAGENT_WORKSPACE_ROOT", None)
        else:
            os.environ["SIMPLEAGENT_WORKSPACE_ROOT"] = self.original_workspace_root
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_write_new_file_overwrite_mode(self):
        result = write_file.execute(path="a.txt", content="hello", mode="overwrite")
        self.assertIn("SUCCESS:", result)
        self.assertEqual(Path("a.txt").read_text(encoding="utf-8"), "hello")

    def test_overwrite_requires_confirmation(self):
        Path("b.txt").write_text("old", encoding="utf-8")
        result = write_file.execute(path="b.txt", content="new", mode="overwrite", confirm_overwrite=False)
        self.assertIn("Overwrite blocked", result)
        self.assertEqual(Path("b.txt").read_text(encoding="utf-8"), "old")

    def test_overwrite_with_confirmation(self):
        Path("c.txt").write_text("old", encoding="utf-8")
        result = write_file.execute(path="c.txt", content="new", mode="overwrite", confirm_overwrite=True)
        self.assertIn("SUCCESS:", result)
        self.assertEqual(Path("c.txt").read_text(encoding="utf-8"), "new")

    def test_append_mode(self):
        Path("d.txt").write_text("a", encoding="utf-8")
        result = write_file.execute(path="d.txt", content="b", mode="append")
        self.assertIn("SUCCESS:", result)
        self.assertEqual(Path("d.txt").read_text(encoding="utf-8"), "ab")

    def test_create_dirs_flag(self):
        result = write_file.execute(path="nested/e.txt", content="x", create_dirs=False)
        self.assertIn("Parent directory does not exist", result)
        result2 = write_file.execute(path="nested/e.txt", content="x", create_dirs=True)
        self.assertIn("SUCCESS:", result2)
        self.assertEqual(Path("nested/e.txt").read_text(encoding="utf-8"), "x")

    def test_blocks_outside_cwd(self):
        outside = Path(self.tmpdir).parent / "outside-write-test.txt"
        result = write_file.execute(path=str(outside), content="blocked")
        self.assertIn("Refusing to write outside workspace root", result)
        self.assertFalse(outside.exists())

    def test_workspace_root_anchor_allows_subdirs_from_nested_cwd(self):
        nested = Path(self.tmpdir) / "child"
        nested.mkdir(parents=True, exist_ok=True)
        os.environ["SIMPLEAGENT_WORKSPACE_ROOT"] = self.tmpdir
        os.chdir(nested)

        result = write_file.execute(path="docs/demo.txt", content="ok", create_dirs=True)
        self.assertIn("SUCCESS:", result)
        self.assertEqual((Path(self.tmpdir) / "docs" / "demo.txt").read_text(encoding="utf-8"), "ok")


if __name__ == "__main__":
    unittest.main()
