from __future__ import annotations

import stat
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
from production_tool import _is_link_or_reparse


class PathSafetyTests(unittest.TestCase):
    def test_regular_file_is_not_reparse(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "regular.txt"
            source.write_text("ok", encoding="utf-8")
            self.assertFalse(_is_link_or_reparse(source.lstat()))

    def test_windows_reparse_attribute_is_detected(self):
        details = SimpleNamespace(
            st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT,
            st_mode=stat.S_IFREG,
        )
        self.assertTrue(_is_link_or_reparse(details))


if __name__ == "__main__":
    unittest.main()
