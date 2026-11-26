import json,hashlib,os
from pathlib import Path
import tempfile
import unittest
from discovery import Discovery
from library import Library
from source_sync import ScriptSync

class SourceSyncTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);root=Path(self.temp.name)
  self.source=root/'source';self.source.mkdir();self.file=self.source/'剧本.md'
  self.original='# EP001\n## EP001-SC001 第一场\n甲：原句。\n## EP001-SC002 第二场\n乙：不变。'
  self.file.write_text(self.original,encoding='utf8')
  registry=root/'registry';registry.mkdir();key=hashlib.sha256(os.path.normcase(str(self.source.resolve())).encode()).hexdigest()
  (registry/(key+'.json')).write_text(json.dumps({'path':str(self.source),'title':'原项目'}),encoding='utf8')
  self.lib=Library(root/'library');self.discovery=Discovery(self.lib,registry);self.pid=self.discovery.open(key);self.store=self.lib.project(self.pid);self.sync=ScriptSync(self.lib,self.discovery)
  self.doc=next(e['id'] for e in self.store.state()['entities'] if e['kind']=='document')
  self.scene=next(e['id'] for e in self.store.state()['entities'] if e['kind']=='scene' and e['data']['code']=='EP001-SC001')
 def apply(self,preview,choices={}):return self.sync.apply(self.pid,self.doc,preview['revision'],preview['source_hash'],choices)
 def test_remote_change_preserves_scene_identity_and_local_unrelated_edit(self):
  second=next(e['id'] for e in self.store.state()['entities'] if e['kind']=='scene' and e['id']!=self.scene)
  self.store.apply(self.store.state()['project']['revision'],[{'type':'update','id':second,'patch':{'text':'乙：本地保留。'}}])
  self.file.write_text(self.original.replace('甲：原句。','甲：外部新句。'),encoding='utf8')
  self.assertEqual(len(self.sync.sources(self.pid)),1)
  state=self.apply(self.sync.preview(self.pid,self.doc))
  self.assertEqual(next(e for e in state['entities'] if e['id']==self.scene)['data']['text'],'甲：外部新句。')
  self.assertEqual(next(e for e in state['entities'] if e['id']==second)['data']['text'],'乙：本地保留。')
  self.assertEqual(self.sync.sources(self.pid),[])
  self.assertIn('甲：外部新句。',self.file.read_text(encoding='utf8'))
 def test_merge_can_be_undone_and_external_update_remains_available(self):
  self.file.write_text(self.original.replace('甲：原句。','甲：新句。'),encoding='utf8')
  state=self.apply(self.sync.preview(self.pid,self.doc));self.store.undo(state['project']['revision'])
  self.assertEqual(next(e for e in self.store.state()['entities'] if e['id']==self.scene)['data']['text'],'甲：原句。')
  self.assertEqual(len(self.sync.sources(self.pid)),1)
 def test_conflict_requires_choice_and_can_keep_local(self):
  self.store.apply(self.store.state()['project']['revision'],[{'type':'update','id':self.scene,'patch':{'text':'甲：本地句。'}}])
  self.file.write_text(self.original.replace('甲：原句。','甲：外部句。'),encoding='utf8')
  preview=self.sync.preview(self.pid,self.doc);change=next(c for c in preview['changes'] if c.get('field')=='text')
  self.assertTrue(change['conflict'])
  with self.assertRaises(ValueError):self.apply(preview)
  state=self.apply(preview,{change['key']:'current'})
  self.assertEqual(next(e for e in state['entities'] if e['id']==self.scene)['data']['text'],'甲：本地句。')
 def test_external_change_during_review_does_not_apply_stale_preview(self):
  self.file.write_text(self.original+'\n补充。',encoding='utf8');preview=self.sync.preview(self.pid,self.doc)
  self.file.write_text(self.original+'\n又一次改稿。',encoding='utf8')
  with self.assertRaisesRegex(ValueError,'又有更新'):self.apply(preview)
 def test_external_removal_preserves_scene_until_explicitly_acknowledged(self):
  self.file.write_text('# EP001\n## EP001-SC002 第二场\n乙：不变。',encoding='utf8')
  preview=self.sync.preview(self.pid,self.doc);removed=next(c for c in preview['changes'] if c['kind']=='removed')
  with self.assertRaises(ValueError):self.apply(preview)
  state=self.apply(preview,{removed['key']:'current'})
  self.assertTrue(any(e['id']==self.scene for e in state['entities']))

if __name__=='__main__':unittest.main()
