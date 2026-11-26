import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from discovery import Discovery
from library import Library

class DiscoveryTests(unittest.TestCase):
    def test_skill_init_appears_then_imports_once_without_changing_source(self):
        tool_path=Path(__file__).resolve().parents[2]/'short-drama/scripts/project_tool.py'
        spec=importlib.util.spec_from_file_location('discovery_project_tool',tool_path)
        tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);registry=root/'registry';source=root/'Agent 新作品'
            with patch.dict(os.environ,{'SHORT_DRAMA_PROJECT_REGISTRY':str(registry)}):
                tool.initialize_project(source,title='自动出现的故事',language='zh-CN',aspect_ratio='9:16')
            library=Library(root/'library');discovery=Discovery(library,registry)
            found=discovery.list();self.assertEqual(len(found),1)
            self.assertEqual(found[0]['title'],'自动出现的故事');self.assertFalse(found[0]['ready'])
            self.assertEqual(library.list(),[])
            with self.assertRaises(ValueError):discovery.open(found[0]['id'])
            episode=source/'剧集/EP001';episode.mkdir(parents=True,exist_ok=True)
            script=episode/'剧本.md';script.write_text('# EP001\n## EP001-SC001 内 · 客厅 · 日\n甲：等一下。',encoding='utf8')
            before=script.read_bytes();self.assertTrue(discovery.list()[0]['ready'])
            project=discovery.open(found[0]['id'])
            self.assertEqual(discovery.open(found[0]['id']),project)
            self.assertEqual(discovery.list(),[]);self.assertEqual(len(library.list()),1)
            self.assertEqual(script.read_bytes(),before)
            (registry/'broken.json').write_text('{')
            self.assertEqual(discovery.list(),[])

if __name__=='__main__':unittest.main()
