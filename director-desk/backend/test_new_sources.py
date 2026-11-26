import unittest
import test_source_sync as fixture

class NewSourceTests(unittest.TestCase):
 def setUp(self):
  self.case=fixture.SourceSyncTests();self.case.setUp();self.addCleanup(self.case.doCleanups)
  self.sync=self.case.sync;self.store=self.case.store;self.pid=self.case.pid
 def merge(self,source,choices={}):
  preview=self.sync.preview(self.pid,source['id']);return self.sync.apply(self.pid,source['id'],preview['revision'],preview['source_hash'],choices)
 def test_new_visual_doc_is_discovered_without_mutation_and_undoable(self):
  before=self.store.state()
  (self.case.source/'视觉设定.md').write_text('# 视觉设定\n## 人物 · 甲\n蓝衣，少言。',encoding='utf8')
  source=self.sync.sources(self.pid)[0];self.assertTrue(source['new'])
  self.assertEqual(self.store.state(),before)
  preview=self.sync.preview(self.pid,source['id']);self.assertEqual(self.store.state(),before)
  state=self.merge(source)
  self.assertEqual(len([e for e in state['entities'] if e['kind']=='character']),1)
  self.assertEqual(self.sync.sources(self.pid),[])
  self.store.undo(state['project']['revision'])
  self.assertEqual(self.sync.sources(self.pid)[0]['id'],source['id'])
 def test_new_external_doc_links_existing_local_doc_without_duplication(self):
  ep=next(e['id'] for e in self.store.state()['entities'] if e['kind']=='episode')
  self.store.apply(self.store.state()['project']['revision'],[
   {'type':'create','id':'local-doc','kind':'document','data':{'name':'视觉设定.md','parent_id':ep,'structured':True,'preamble':'# 视觉设定'}},
   {'type':'create','id':'local-char','kind':'character','data':{'name':'甲','heading':'人物 · 甲','text':'本地版本','order':0,'parent_id':ep,'document_id':'local-doc'}}])
  (self.case.source/'视觉设定.md').write_text('# 视觉设定\n## 人物 · 甲\n外部版本',encoding='utf8')
  source=self.sync.sources(self.pid)[0];self.assertEqual(source['id'],'local-doc')
  preview=self.sync.preview(self.pid,source['id']);change=next(c for c in preview['changes'] if c.get('field')=='text')
  self.assertTrue(change['conflict'])
  state=self.merge(source,{c['key']:'current' for c in preview['changes']})
  self.assertEqual(next(e for e in state['entities'] if e['id']=='local-char')['data']['text'],'本地版本')
  self.assertEqual(len([e for e in state['entities'] if e['kind']=='document' and e['data']['name']=='视觉设定.md']),1)
 def test_new_storyboard_is_atomic_and_requires_existing_scene(self):
  path=self.case.source/'分镜.md';path.write_text('## SHOT-001 · 转身\n- 来源：EP001-SC999\n- 唯一动作：转身',encoding='utf8')
  source=self.sync.sources(self.pid)[0];before=self.store.state()
  with self.assertRaisesRegex(ValueError,'唯一场次'):self.merge(source)
  self.assertEqual(before,self.store.state())
  path.write_text(path.read_text(encoding='utf8').replace('SC999','SC001'),encoding='utf8')
  state=self.merge(source);shot=next(e for e in state['entities'] if e['kind']=='shot')
  self.assertEqual(shot['data']['parent_id'],self.case.scene)
  self.assertEqual(self.sync.sources(self.pid),[])

if __name__=='__main__':unittest.main()
