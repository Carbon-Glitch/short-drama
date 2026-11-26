import unittest
import test_document_sync as fixture
from transfer import project_markdown

class StoryboardSyncTests(unittest.TestCase):
 def setUp(self):
  self.case=fixture.DocumentSyncTests();self.case.setUp();self.addCleanup(self.case.doCleanups)
  self.store=self.case.store;self.sync=self.case.sync;self.pid=self.case.pid
  self.doc=self.case.doc('分镜.md');self.path=self.case.source/'分镜.md';self.original=self.path.read_text(encoding='utf8')
  self.shot=next(e for e in self.store.state()['entities'] if e['kind']=='shot')
 def apply(self,choices={}):return self.case.merge(self.doc,choices)
 def test_action_merge_keeps_local_camera_identity_and_adoption(self):
  self.store.apply(self.store.state()['project']['revision'],[{'type':'update','id':self.shot['id'],'patch':{'camera':'局部特写','adopted_media':'preserve-version'}}])
  self.path.write_text(self.original.replace('唯一动作：等待','唯一动作：手伸向门把'),encoding='utf8')
  preview=self.sync.preview(self.pid,self.doc['id'])
  self.assertEqual([(c['field'],c['conflict']) for c in preview['changes']],[('action',False)])
  state=self.apply();shot=next(e for e in state['entities'] if e['id']==self.shot['id'])
  self.assertEqual(shot['data']['action'],'手伸向门把');self.assertEqual(shot['data']['camera'],'局部特写')
  self.assertEqual(shot['data']['adopted_media'],'preserve-version')
  self.store.undo(state['project']['revision']);self.assertEqual(len(self.sync.sources(self.pid)),1)
 def test_same_field_conflict_preserves_current_when_chosen(self):
  self.store.apply(self.store.state()['project']['revision'],[{'type':'update','id':self.shot['id'],'patch':{'action':'向后退'}}])
  self.path.write_text(self.original.replace('唯一动作：等待','唯一动作：向前走'),encoding='utf8')
  preview=self.sync.preview(self.pid,self.doc['id']);change=next(c for c in preview['changes'] if c['field']=='action')
  self.assertTrue(change['conflict'])
  with self.assertRaises(ValueError):self.apply()
  state=self.apply({change['key']:'current'})
  self.assertEqual(next(e for e in state['entities'] if e['id']==self.shot['id'])['data']['action'],'向后退')
 def test_new_shot_and_scene_plan_have_real_parent_and_export(self):
  self.path.write_text('## 场景站位 · EP001-SC001\n甲在门左。\n- 生成安排：全能参考，共两段。\n'+self.original+'\n## SHOT-002 · 反应\n- 来源：EP001-SC001\n- 唯一动作：回头\n- 运镜：固定\n- 接镜：动作切\n- 视觉依据：人物「甲」',encoding='utf8')
  preview=self.sync.preview(self.pid,self.doc['id']);state=self.apply({c['key']:'source' for c in preview['changes']})
  scene=next(e for e in state['entities'] if e['kind']=='scene');shot=next(e for e in state['entities'] if e['data'].get('code')=='SHOT-002')
  self.assertEqual(scene['data']['blocking'],'甲在门左。');self.assertEqual(shot['data']['parent_id'],scene['id'])
  self.assertEqual(shot['data']['movement'],'固定');self.assertEqual(len(shot['data']['design_refs']),1)
  self.assertNotIn('extra_fields',shot['data'])
  out=self.case.source.parent/'export';out.mkdir();project_markdown(out,state)
  exported=(out/'剧集/EP001/分镜.md').read_text(encoding='utf8');self.assertIn('- 运镜：固定',exported);self.assertIn('全能参考，共两段。',exported)
 def test_unknown_scene_and_removed_shot_do_not_silently_reparent_or_delete(self):
  self.path.write_text(self.original.replace('EP001-SC001','EP001-SC999'),encoding='utf8')
  before=self.store.state()
  with self.assertRaisesRegex(ValueError,'唯一场次'):self.apply()
  self.assertEqual(before,self.store.state())
  self.path.write_text('# 分镜\n',encoding='utf8');preview=self.sync.preview(self.pid,self.doc['id'])
  with self.assertRaises(ValueError):self.apply()
  state=self.apply({c['key']:'current' for c in preview['changes']})
  self.assertTrue(any(e['id']==self.shot['id'] for e in state['entities']))

if __name__=='__main__':unittest.main()
