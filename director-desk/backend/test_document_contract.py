import tempfile
import unittest
from pathlib import Path
from document_contract import split_fields, render_fields, check_headings, validate_agent_fields
from store import ProjectStore
from transfer import project_markdown
from storyboard_sync import StoryboardSync

class ContractTests(unittest.TestCase):
    def test_multiline_alias_empty_and_custom_roundtrip(self):
        source='- 运镜：先推近\n  再侧移\n  - 人物回头时停止\n- 景别：特写\n- 声音：\n- 自定义：保留\n\n说明正文'
        values,prose=split_fields(source)
        self.assertEqual(values['运镜'],'先推近\n再侧移\n- 人物回头时停止')
        self.assertEqual(values['景别/机位'],'特写')
        self.assertEqual(prose,'说明正文')
        self.assertEqual(split_fields(render_fields(values))[0],values)

    def test_unknown_heading_and_duplicate_are_actionable(self):
        for text in ('## 镜头一\n- 动作：转身','## SHOT-001\n\n## SHOT-001'):
            with self.assertRaises(ValueError):check_headings('分镜.md',text)
        with self.assertRaisesRegex(ValueError,'字段重复'):split_fields('- 景别：近景\n- 景别/机位：远景')
        with self.assertRaisesRegex(ValueError,'版本'):check_headings('分镜.md','<!-- director-document:99 -->')

    def test_agent_unknown_and_wrong_type_rejected(self):
        for patch in ({'camera_angle':'仰拍'},{'camera':['特写']},{'duration':4}):
            with self.assertRaises(ValueError):validate_agent_fields('shot',patch)
        validate_agent_fields('shot',{'camera':'特写','movement':'缓推'})

    def test_export_reimport_preserves_multiline_and_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);store=ProjectStore.create(root/'project','测试')
            state=store.apply(0,[{'type':'create','id':'ep','kind':'episode','data':{'name':'测试','code':'EP001'}},
                {'type':'create','id':'sc','kind':'scene','data':{'parent_id':'ep','name':'场景','code':'EP001-SC001'}},
                {'type':'create','id':'shot','kind':'shot','data':{'parent_id':'sc','name':'回头','code':'SHOT-001','movement':'先推近\n然后侧移','camera':'特写，侧光','action':'回头','source_excerpt':'EP001-SC001'}}])
            project_markdown(root/'out',state)
            text=(root/'out/剧集/EP001/分镜.md').read_text(encoding='utf8')
            _,rows=StoryboardSync(None,None).specs('分镜.md',text)
            self.assertEqual(rows[0]['key'],'SHOT-001')
            self.assertEqual(rows[0]['data']['movement'],'先推近\n然后侧移')
            self.assertEqual(rows[0]['data']['source_text'],'')
            with self.assertRaises(ValueError):store.apply(state['project']['revision'],[{'type':'update','id':'shot','patch':{'camera':{}}}])
            self.assertEqual(store.state(),state)

if __name__=='__main__':unittest.main()
