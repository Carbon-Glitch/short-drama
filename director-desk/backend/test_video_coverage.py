import tempfile,unittest
from pathlib import Path
from library import Library
from video_coverage import VideoCoverage
from documents import declared_shots
from store import Conflict

class VideoCoverageTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.lib=Library(self.tmp.name);self.pid=self.lib.create('覆盖测试');self.store=self.lib.project(self.pid)
  state=self.store.state();ep=next(e['id'] for e in state['entities'] if e['kind']=='episode');scene=next(e['id'] for e in state['entities'] if e['kind']=='scene')
  self.text='- 时长：8s\n- 输入参考图：无\n### 可复制提示词\n> <d>[Chinese] 别动。</d>'
  self.store.apply(1,[{'type':'create','id':'s1','kind':'shot','data':{'name':'前镜','parent_id':scene,'order':0,'duration':'3s'}},
                      {'type':'create','id':'s2','kind':'shot','data':{'name':'后镜','parent_id':scene,'order':1,'duration':'5s'}},
                      {'type':'create','id':'doc','kind':'document','data':{'name':'视频提示词.md','parent_id':ep,'structured':True}},
                      {'type':'create','id':'unit','kind':'submission','data':{'name':'生成段','parent_id':ep,'document_id':'doc','code':'MOTION-001','text':self.text}}])
  self.service=VideoCoverage(self.lib)
 def update(self,ids):return self.service.update(self.pid,'unit',ids,self.store.state()['project']['revision'])
 def test_selection_assigns_stable_codes_preserves_prompt_and_links_in_order(self):
  before=self.store.state();state=self.update(['s2','s1'])
  unit=next(e for e in state['entities'] if e['id']=='unit')
  self.assertEqual(unit['data']['shot_ids'],['s1','s2']);self.assertTrue(unit['data']['text'].endswith(self.text))
  codes=[next(e for e in state['entities'] if e['id']==sid)['data']['code'] for sid in ('s1','s2')]
  self.assertEqual(len(set(codes)),2);self.assertEqual(declared_shots(unit['data']['text']),set(codes))
  self.assertEqual({d['source'] for d in state['dependencies'] if d['target']=='unit'},{'s1','s2'})
  self.store.undo(state['project']['revision'])
  self.assertEqual(next(e for e in self.store.state()['entities'] if e['id']=='unit')['data']['text'],self.text)
 def test_remove_selection_does_not_delete_shot_or_reinfer_from_motion_name(self):
  self.update(['s1']);state=self.update([])
  unit=next(e for e in state['entities'] if e['id']=='unit')
  self.assertEqual(unit['data']['shot_ids'],[]);self.assertEqual(declared_shots(unit['data']['text'],'MOTION-001'),set())
  self.assertTrue(any(e['id']=='s1' for e in state['entities']))
  self.assertFalse(any(d['target']=='unit' for d in state['dependencies']))
 def test_invalid_scope_and_stale_dialog_cannot_overwrite(self):
  before=self.store.state()
  with self.assertRaises(ValueError):self.update(['unit'])
  with self.assertRaises(ValueError):self.update(['s1','s1'])
  self.assertEqual(before,self.store.state())
  revision=before['project']['revision'];self.update(['s1'])
  with self.assertRaises(Conflict):self.service.update(self.pid,'unit',['s2'],revision)
 def test_old_foreign_link_is_presented_as_local_repair_without_read_mutation(self):
  self.update(['s1']);state=self.store.state()
  self.store.apply(state['project']['revision'],[{'type':'update','id':'unit','patch':{'shot_ids':['missing-old-shot']}}])
  before=self.store.state();description=self.service.describe(self.pid,'unit')
  self.assertTrue(description['invalid_previous']);self.assertEqual(description['selected'],['s1'])
  self.assertEqual(before,self.store.state())
  state=self.update(description['selected']);self.assertEqual(next(e for e in state['entities'] if e['id']=='unit')['data']['shot_ids'],['s1'])

if __name__=='__main__':unittest.main()
