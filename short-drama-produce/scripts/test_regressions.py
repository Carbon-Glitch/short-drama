from __future__ import annotations

import stat
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
from production_tool import _is_link_or_reparse
from production_tool import _markdown_reference_bindings, _markdown_audio_bindings, _normalize_reference_bindings
from provider_adapters import _prompt_with_reference_contract


class ReferenceScopeTests(unittest.TestCase):
    def test_optional_exclusions_compile_through_provider(self):
        for exclusion in ("", "；不得控制：", "；不得控制：无", "；不得控制：背景"):
            with self.subTest(exclusion=exclusion):
                section = "- 输入参考图：REF-A（顺序：1）· assets/person.png《人物》（用途：身份；控制：identity" + exclusion + "）"
                bindings = _markdown_reference_bindings(section, field_name="输入参考图")
                bindings[0]["role"] = "reference_image"
                bindings = _normalize_reference_bindings(bindings)
                expected = ["背景"] if exclusion.endswith("背景") else []
                self.assertEqual(bindings[0]["must_not_control"], expected)
                for language, marker in (("zh-CN", "不得控制"), ("en", "Must not control"), ("ja", "[-]")):
                    prompt = _prompt_with_reference_contract("Scene", {"references": ["assets/person.png"], "reference_bindings": bindings}, prompt_language=language)
                    self.assertIn("identity", prompt)
                    self.assertEqual(marker in prompt, bool(expected))

    def test_audio_optional_exclusions(self):
        for exclusion in ("", "；不得控制：", "；不得控制：无"):
            section = "- 参考音频：REF-V（顺序：1）· assets/voice.wav《人物音色》（用途：音色；角色：甲；控制：音色" + exclusion + "）"
            binding = _markdown_audio_bindings(section)[0]
            binding["role"] = "reference_audio"
            self.assertEqual(_normalize_reference_bindings([binding])[0]["must_not_control"], [])

    def test_invalid_scopes_remain_rejected(self):
        base = dict(slot_id="REF-A", order=1, path="assets/person.png", label="人物", role="reference_image", may_control=["identity"], must_not_control=[])
        for changes in ({"may_control": []}, {"must_not_control": [""]}, {"must_not_control": ["identity"]}, {"must_not_control": None}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                _normalize_reference_bindings([base | changes])


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
