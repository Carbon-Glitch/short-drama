import tempfile
import unittest
from pathlib import Path
from entry_tool import read_entry,update_entry

class EntryToolTests(unittest.TestCase):
 def test_edit_keeps_other_fields_prose_and_shots_and_leaves_no_sidecars(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);path=root/'分镜.md'
   original='## SHOT-001 · 等待\n- 景别/机位：近景\n- 运镜：固定\n\n导演批注保留。\n\n## SHOT-002 · 回头\n- 唯一动作：回头\n'
   path.write_text(original,encoding='utf8')
   info=read_entry(root,'分镜.md','SHOT-001')
   result=update_entry(root,'分镜.md','SHOT-001',info['revision'],{'fields':{'movement':'先固定\n回头时缓推'}})
   text=path.read_text(encoding='utf8')
   self.assertIn('- 运镜：先固定\n  回头时缓推',text)
   self.assertIn('- 景别/机位：近景',text)
   self.assertTrue(text.endswith(original[original.index('## SHOT-002'):]))
   self.assertIn('导演批注保留。',text)
   self.assertEqual([p.name for p in root.iterdir()],['分镜.md'])
   with self.assertRaisesRegex(ValueError,'已更新'):update_entry(root,'分镜.md','SHOT-001',info['revision'],{'fields':{'camera':'远景'}})
   self.assertEqual(read_entry(root,'分镜.md','SHOT-001'),result)

 def test_prompt_edit_keeps_metadata_and_field_edit_stays_outside_prompt(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);path=root/'视频提示词.md'
   path.write_text('## MOTION-001 · 一段\n- 分镜：SHOT-001\n\n### 可复制提示词\n> summary:\n> A woman waits.\n',encoding='utf8')
   info=read_entry(root,'视频提示词.md','MOTION-001')
   update_entry(root,'视频提示词.md','MOTION-001',info['revision'],{'fields':{'时长':'5s'}})
   text=path.read_text(encoding='utf8')
   self.assertLess(text.index('- 时长：5s'),text.index('### 可复制提示词'))
   self.assertTrue(text.endswith('> A woman waits.\n'))

 def test_invalid_update_does_not_write(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);p=root/'分镜.md';p.write_text('## SHOT-001 · 一镜\n- 运镜：固定\n',encoding='utf8')
   info=read_entry(root,'分镜.md','SHOT-001');before=p.read_bytes()
   for patch in ({'fields':{'camerra':'近景'}},{'text':'## SHOT-002\n覆盖别镜'},{'fields':{'运镜':[]}}):
    with self.assertRaises(ValueError):update_entry(root,'分镜.md','SHOT-001',info['revision'],patch)
    self.assertEqual(p.read_bytes(),before)
   self.assertEqual(len(list(root.iterdir())),1)

if __name__=='__main__':unittest.main()
