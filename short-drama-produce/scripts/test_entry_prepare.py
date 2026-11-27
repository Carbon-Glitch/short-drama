import json
import tempfile
import unittest
from pathlib import Path
from production_tool import prepare_entry,prepare_payload,prepare_job,_job_path,entry_inputs

class EntryPrepareTests(unittest.TestCase):
 def test_direct_entry_matches_file_protocol_without_input_job_copy(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);(root/'short-drama.json').write_text('{}',encoding='utf8')
   ep=root/'剧集/EP001';ep.mkdir(parents=True)
   (ep/'图片提示词.md').write_text('## IMG-TEST · 窗光\n- 参考：无外部参考\n\n### 可复制提示词\n> Window light on a table.\n',encoding='utf8')
   preview=prepare_entry(root,source='剧集/EP001/图片提示词.md',entry='IMG-TEST',adapter='fixture',output='production/out.png',job_id='same')
   stored=json.loads(_job_path(root,'same').read_text(encoding='utf8'))
   raw={k:stored[k] for k in ('schema_version','job_id','modality','adapter','prompt','source','source_entry','references','reference_bindings','outputs','parameters','overwrite')}
   file=root/'legacy-job.json';file.write_text(json.dumps(raw),encoding='utf8')
   legacy=prepare_job(root,file)
   self.assertEqual(preview['confirmation'],legacy['confirmation'])
   self.assertEqual(stored['fingerprint'],json.loads(_job_path(root,'same').read_text(encoding='utf8'))['fingerprint'])
   self.assertFalse((root/'输入').exists())
   self.assertEqual(len(list((root/'.short-drama/production/jobs').glob('*.json'))),1)

 def test_voice_forces_full_reference_and_rejects_frame_claim(self):
  section='- 输入参考图：REF-A（顺序：1）· a.png《人物》（用途：起始帧；控制：外观）\n- 参考音频：REF-V（顺序：1）· v.wav《声音》（用途：音色；角色：甲；控制：音色）\n### 可复制提示词\n> subject_definitions: a character'
  result=entry_inputs(section,field='输入参考图',is_video=True,provider='minimax-h3')
  self.assertEqual(result['mode'],'reference')
  self.assertEqual([b['role'] for b in result['bindings']],['reference_image','reference_audio'])
  with self.assertRaisesRegex(ValueError,'控制路线'):entry_inputs(section,field='输入参考图',is_video=True,declared='first_frame')

 def test_missing_source_does_not_make_job(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);(root/'short-drama.json').write_text('{}',encoding='utf8')
   with self.assertRaises((ValueError,OSError)):prepare_entry(root,source='剧集/EP001/视频提示词.md',entry='MOTION-001',adapter='fixture',output='production/out.mp4')
   self.assertFalse((root/'.short-drama/production/jobs').exists())

 def test_video_job_freezes_design_text_and_detects_changed_input(self):
  from production_tool import _read_job, _inputs_current
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);(root/'short-drama.json').write_text('{}',encoding='utf8');ep=root/'剧集/EP001';ep.mkdir(parents=True)
   (ep/'分镜.md').write_text('## SHOT-001 · 车票\n- 来源：EP001-SC001\n- 设计承接：DESIGN-001\n- 动作与表演：甲递票，乙迟疑。',encoding='utf8')
   design=ep/'视觉设定.md';design.write_text('## DESIGN-001 · 顺序\n先见票，再响铃。',encoding='utf8')
   (ep/'视频提示词.md').write_text('## MOTION-001 · 车票\n- 分镜：SHOT-001\n- 生成方式：文生视频\n- 输入参考图：无\n- 时长：5s\n### 可复制提示词\n> A ticket passes between two hands.',encoding='utf8')
   prepare_entry(root,source='剧集/EP001/视频提示词.md',entry='MOTION-001',adapter='fixture',output='production/out.mp4',job_id='context',mode='text',parameters={'duration':5})
   stored=_read_job(root,'context');self.assertTrue(_inputs_current(root,stored))
   self.assertIn('先见票，再响铃。',str(stored['creative_context']))
   design.write_text('## DESIGN-001 · 顺序\n先响铃再见票。',encoding='utf8')
   self.assertFalse(_inputs_current(root,stored))
   self.assertIn('先见票，再响铃。',str(_read_job(root,'context')['creative_context']))

if __name__=='__main__':unittest.main()
