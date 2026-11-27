import tempfile,unittest
from pathlib import Path
from creator_context import build_context

class ContextTests(unittest.TestCase):
 def test_exact_source_text_and_selected_design_identity(self):
  with tempfile.TemporaryDirectory() as tmp:
   ep=Path(tmp)
   (ep/'分镜.md').write_text('## 场景站位 · EP001-SC001\n共用光影。\n## SHOT-001 · 票\n- 来源：EP001-SC001\n- 设计承接：DESIGN-001\n- 听者与反馈：乙迟疑，然后接住。\n## SHOT-002 · 接住\n- 来源：EP001-SC001\n- 声画触发：铃响才松手。',encoding='utf8')
   (ep/'剧本.md').write_text('## EP001-SC001 夜\n甲：等一下。',encoding='utf8')
   p=ep/'视觉设定.md';text='## DESIGN-001 · 顺序\n车票先可读，再响铃。\n## DESIGN-002 · 未用\n另一个选择。\n';p.write_text(text,encoding='utf8')
   first=build_context(ep,['SHOT-001'])
   self.assertTrue(any('乙迟疑，然后接住。' in r['text'] for r in first['records']))
   self.assertTrue(any(r['role']=='neighbor' and '铃响才松手。' in r['text'] for r in first['records']))
   p.write_text(text.replace('另一个选择。','无关修改。'),encoding='utf8');self.assertEqual(first,build_context(ep,['SHOT-001']))
   p.write_text(text.replace('车票先可读','车票先翻面'),encoding='utf8');self.assertNotEqual(first['fingerprint'],build_context(ep,['SHOT-001'])['fingerprint'])
   p.write_text(text.replace('DESIGN-001','DESIGN-003'),encoding='utf8')
   with self.assertRaisesRegex(ValueError,'设计承接未找到'):build_context(ep,['SHOT-001'])
if __name__=='__main__':unittest.main()
