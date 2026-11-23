from __future__ import annotations

import stat
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
from project_tool import _is_link_or_reparse


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


class DocumentationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skills = Path(__file__).resolve().parents[2]

    def test_stage_contracts_share_rule_taxonomy(self):
        names = [
            "assets", "develop", "edit", "novel-analyze", "review",
            "storyboard", "video-prompts", "write",
        ]
        for name in names:
            with self.subTest(skill=name):
                text = (self.skills / f"short-drama-{name}/references/stage-contract.md").read_text(encoding="utf-8")
                self.assertIn("../../short-drama/references/contract-and-ownership.md#规则分级", text)
                self.assertNotIn("规则分级由高到低", text)

    def test_provider_documents_have_machine_readable_metadata(self):
        documents = [
            self.skills / "short-drama-video-prompts/references/seedance-2.0.md",
            self.skills / "short-drama-video-prompts/references/seedance-2.5.md",
            self.skills / "short-drama-video-prompts/references/minimax-h3.md",
            self.skills / "short-drama-video-prompts/references/wan-3.0.md",
            self.skills / "short-drama-produce/references/providers/seedance.md",
            self.skills / "short-drama-produce/references/providers/minimax-h3-video.md",
            self.skills / "short-drama-produce/references/providers/gpt-image-2.md",
            self.skills / "short-drama-produce/references/providers/minimax-music.md",
            self.skills / "short-drama-produce/references/providers/minimax-speech.md",
        ]
        for document in documents:
            with self.subTest(document=document.name):
                text = document.read_text(encoding="utf-8")
                self.assertTrue(text.startswith("---\n"))
                self.assertIn("metadata_reviewed_at: 2026-11-22", text)

    def test_repeated_skill_opening_is_removed(self):
        for document in self.skills.glob("short-drama*/SKILL.md"):
            with self.subTest(document=document.parent.name):
                text = document.read_text(encoding="utf-8")
                self.assertNotIn("先把画面设计得漂亮、独特、有想象力，再以角色行为、表演和剪辑兑现故事", text)
                self.assertNotIn("## 创作目标与默认阅读", text)

    def test_character_documents_use_shared_definition(self):
        for name in ["assets", "image-prompts"]:
            with self.subTest(skill=name):
                text = (self.skills / f"short-drama-{name}/references/character-and-look.md").read_text(encoding="utf-8")
                self.assertIn("../../short-drama/references/character-identity-and-look.md", text)

    def test_multiagent_fallback_is_explicit(self):
        text = (self.skills / "short-drama/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("不支持子 Agent", text)
        self.assertIn("作者自检", text)


class CreativeDirectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skills = Path(__file__).resolve().parents[2]

    def test_viewing_value_drives_expression_choice(self):
        core = (self.skills / "short-drama/references/viewer-first.md").read_text(encoding="utf-8")
        router = (self.skills / "short-drama/SKILL.md").read_text(encoding="utf-8")
        evaluation = (self.skills / "short-drama/references/skill-evaluation.md").read_text(encoding="utf-8")
        self.assertIn("常规方案作为比较基线", core)
        self.assertIn("观看机制真正不同", core)
        self.assertIn("技术正确性是兑现选定表达的下限", core)
        self.assertIn("观众愿意看、愿意停留", router)
        self.assertIn("关键场次的表达选择", evaluation)

    def test_key_stages_compare_and_choose(self):
        design = (self.skills / "short-drama-design/SKILL.md").read_text(encoding="utf-8")
        storyboard = (self.skills / "short-drama-storyboard/SKILL.md").read_text(encoding="utf-8")
        edit = (self.skills / "short-drama-edit/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("不自动取中间方案", design)
        self.assertIn("选中机制、观看收益", design)
        self.assertIn("观看机制不同的方案", storyboard)
        self.assertIn("主动选择能放大体验的表达", storyboard)
        self.assertIn("references/editing-decision-library.md", edit)
        self.assertIn("不把平均切镜", edit)

    def test_downstream_preserves_selected_mechanism(self):
        prompts = (self.skills / "short-drama-video-prompts/SKILL.md").read_text(encoding="utf-8")
        review = (self.skills / "short-drama-review/SKILL.md").read_text(encoding="utf-8")
        ladder = (self.skills / "short-drama-review/references/quality-ladder.md").read_text(encoding="utf-8")
        self.assertIn("保留观看机制、改实现路径", prompts)
        self.assertIn("不能在提示词编译中静默换成", prompts)
        self.assertIn("正确但普通", review)
        self.assertIn("保守降级", review)
        self.assertIn("有意的简洁、克制", ladder)


class StoryboardPreviewTests(unittest.TestCase):
    def setUp(self):
        self.sample = (
            "# EP001 审阅样例\n\n"
            "## SHOT-EP001-001 · 钥匙交接\n"
            "- 来源：EP001-SC001\n"
            "- 时长：4s\n"
            "- 目的：让观众看见乙是否接住甲的条件。\n"
            "- 景别/机位：双人中景，桌侧机位。\n"
            "- 运镜：固定；保留双方同时反应。\n"
            "- 起点：甲右手持钥匙，乙左手张开。\n"
            "- 唯一动作：甲递出钥匙，乙在“还我”落下时握稳并看向甲。\n"
            "- 终点：钥匙在乙左手，甲右手离开，乙仍看着甲。\n"
            "- 声音：甲（画内）：“明早还我。”；乙（画内）：“好。”；钥匙轻碰声。\n"
            "- 画面文字：无\n"
            "- 剪辑意图：握稳后再切乙的回答。\n"
            "- 制作分工：钥匙与手部由模型负责。\n"
            "- 接镜：下一镜从乙已握稳开始。\n\n"
            "## SHOT-EP001-002 · 画外压力\n"
            "- 来源：EP001-SC001\n"
            "- 时长：2.5s\n"
            "- 目的：让条件继续影响乙。\n"
            "- 景别/机位：乙近景，桌边机位。\n"
            "- 运镜：固定。\n"
            "- 起点：乙握着钥匙，笑容尚未退去。\n"
            "- 唯一动作：甲画外补充条件，乙收住笑并低头看钥匙。\n"
            "- 终点：乙笑容收住，左手仍握钥匙。\n"
            "- 声音：甲（画外）：“别交给别人。”；乙无台词，走廊底声继续。\n"
        )

    def test_preview_preserves_complete_sound_picture(self):
        from storyboard_preview import build_preview

        preview, warnings = build_preview(self.sample)
        self.assertIn("| 分镜号 | 时间 | 镜长 | 完整声画调度 |", preview)
        self.assertIn("计划总时长 6.5 秒", preview)
        self.assertIn("00:00–00:04", preview)
        self.assertIn("00:04–00:06.5", preview)
        self.assertIn("甲（画内）：“明早还我。”；乙（画内）：“好。”；钥匙轻碰声。", preview)
        self.assertIn("甲画外补充条件，乙收住笑并低头看钥匙。", preview)
        self.assertIn("剪辑意图：握稳后再切乙的回答。", preview)
        self.assertIn("制作分工：钥匙与手部由模型负责。", preview)
        self.assertIn("接镜：下一镜从乙已握稳开始。", preview)
        self.assertEqual(warnings, [])

    def test_preview_surfaces_missing_fields_and_time(self):
        from storyboard_preview import build_preview

        document = self.sample.replace("- 时长：4s\n", "", 1).replace(
            "- 声音：甲（画内）：“明早还我。”；乙（画内）：“好。”；钥匙轻碰声。\n", "", 1
        )
        preview, warnings = build_preview(document)
        self.assertIn("计划总时长待核（1 镜未声明时长）", preview)
        self.assertGreaterEqual(preview.count("| 待核 |"), 2)
        self.assertIn("声音：未写", preview)
        self.assertTrue(any("未写声音" in warning for warning in warnings))
        self.assertTrue(any("无法计算完整时间轴" in warning for warning in warnings))

    def test_preview_cli_writes_utf8_and_never_overwrites_source(self):
        import subprocess

        script = Path(__file__).resolve().with_name("storyboard_preview.py")
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "分镜.md"
            output = Path(folder) / "分镜预览.md"
            source.write_text(self.sample, encoding="utf-8")
            direct = subprocess.run([sys.executable, str(script), str(source)], check=True, capture_output=True)
            self.assertIn("完整声画调度", direct.stdout.decode("utf-8"))
            subprocess.run(
                [sys.executable, str(script), str(source), "--output", str(output)],
                check=True,
                capture_output=True,
            )
            self.assertIn("完整声画调度", output.read_text(encoding="utf-8"))
            refused = subprocess.run(
                [sys.executable, str(script), str(source), "--output", str(source)],
                capture_output=True,
            )
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("预览不能覆盖权威", refused.stderr.decode("utf-8"))
            self.assertEqual(source.read_text(encoding="utf-8"), self.sample)

    def test_preview_document_is_derived_not_a_gate(self):
        skills = Path(__file__).resolve().parents[2]
        document = (skills / "short-drama-storyboard/references/storyboard-preview.md").read_text(encoding="utf-8")
        skill = (skills / "short-drama-storyboard/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("完整声画调度", document)
        self.assertIn("不是第六份创作文档", document)
        self.assertIn("工具直接投影现有 SHOT 字段", document)
        self.assertIn("不强制经过预览或确认", skill)


if __name__ == "__main__":
    unittest.main()
