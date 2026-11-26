import json,sys,unittest,zipfile
import test_source_sync as fixture
from documents import render_document
from production import Production
from prompt_references import PromptReferences
from transfer import export_project

class SourceMediaTests(unittest.TestCase):
 def setUp(self):
  self.case=fixture.SourceSyncTests();self.case.setUp();self.addCleanup(self.case.doCleanups)
  self.store=self.case.store;self.sync=self.case.sync;self.pid=self.case.pid;self.source=self.case.source
  self.path=self.source/'图片提示词.md'
  self.text='# 图片提示词\n## IMG-001 · 门口\n- 参考：REF-A（顺序：1）· actor.png《人物》（用途：身份；控制：外观；不得控制：背景）\n### 可复制提示词\n> 甲站在门边。'
  self.path.write_text(self.text,encoding='utf8');(self.source/'actor.png').write_bytes(b'version-one')
 def merge(self,choices={}):
  doc=next(s for s in self.sync.sources(self.pid) if s['name']=='图片提示词.md');p=self.sync.preview(self.pid,doc['id'])
  return self.sync.apply(self.pid,doc['id'],p['revision'],p['source_hash'],choices)
 def entry(self,state):return next(e for e in state['entities'] if e['kind']=='image_prompt')
 def test_new_media_copies_with_document_and_exports_actual_path(self):
  state=self.merge();entry=self.entry(state);mid=entry['data']['references'][0]
  self.assertEqual(self.case.lib.file(self.pid,mid).read_bytes(),b'version-one')
  doc=next(e for e in state['entities'] if e['id']==entry['data']['document_id'])
  rendered=render_document(state,doc);media=next(e for e in state['entities'] if e['id']==mid)
  self.assertIn(media['data']['path'],rendered);self.assertNotIn('· actor.png《',rendered)
  archive=self.source.parent/'export.zip';export_project(self.store,archive)
  with zipfile.ZipFile(archive) as z:self.assertEqual(z.read(media['data']['path']),b'version-one')
  from reference_media import render_paths
  dialogue='> <d>[Chinese] 原句 · actor.png《原样保留》</d>'
  self.assertEqual(render_paths(dialogue,state,entry),dialogue)
 def test_same_named_file_adds_version_and_production_uses_selected_bytes(self):
  state=self.merge();entry=self.entry(state);old=entry['data']['references'][0]
  (self.source/'actor.png').write_bytes(b'version-two');self.path.write_text(self.text.replace('站在门边','走到门边'),encoding='utf8')
  state=self.merge();entry=self.entry(state);new=entry['data']['references'][0]
  self.assertNotEqual(old,new);self.assertEqual(self.case.lib.file(self.pid,old).read_bytes(),b'version-one')
  config=self.source.parent/'adapters.json';config.write_text(json.dumps({'adapters':{'fixture':{'command':[sys.executable,'unused.py']}}}))
  production=Production(self.case.lib,config);prepared=production.prepare(self.pid,entry['id'],'fixture',{})
  binding=prepared['preview']['reference_bindings'][0]
  self.assertEqual((self.store.root/prepared['workspace']/binding['path']).read_bytes(),b'version-two')
  selection=PromptReferences(self.case.lib,production.tool).describe(self.pid,entry['id'])
  self.assertEqual(selection['choices'][0]['media_id'],new)
  self.store.undo(self.store.state()['project']['revision'])
  self.assertEqual(self.entry(self.store.state())['data']['references'],[old])
 def test_missing_file_does_not_partially_create_doc(self):
  (self.source/'actor.png').unlink();before=self.store.state()
  with self.assertRaisesRegex(ValueError,'尚未落盘'):self.merge()
  self.assertEqual(self.store.state(),before)
 def test_media_changed_after_preview_requires_new_preview(self):
  source=self.sync.sources(self.pid)[0];p=self.sync.preview(self.pid,source['id']);before=self.store.state()
  self.assertEqual(p['media'][0]['status'],'new')
  (self.source/'actor.png').write_bytes(b'changed-after-preview')
  with self.assertRaisesRegex(ValueError,'又有更新'):self.sync.apply(self.pid,source['id'],p['revision'],p['source_hash'],{})
  self.assertEqual(before,self.store.state())
 def test_skipped_external_entry_does_not_copy_media(self):
  source=self.sync.sources(self.pid)[0];p=self.sync.preview(self.pid,source['id'])
  self.merge({c['key']:'current' for c in p['changes']})
  self.assertFalse(any(e['kind']=='media' for e in self.store.state()['entities']))
 def test_media_only_update_is_discovered_and_can_be_kept_or_undone(self):
  state=self.merge();old=self.entry(state)['data']['references'][0]
  (self.source/'actor.png').write_bytes(b'new-only-media')
  source=self.sync.sources(self.pid)[0];self.assertTrue(source['media_changed'])
  preview=self.sync.preview(self.pid,source['id']);change=next(c for c in preview['changes'] if c.get('reason')=='media')
  state=self.merge({change['key']:'current'})
  self.assertEqual(self.entry(state)['data']['references'],[old]);self.assertEqual(self.sync.sources(self.pid),[])
  self.store.undo(state['project']['revision'])
  state=self.merge();new=self.entry(state)['data']['references'][0]
  self.assertNotEqual(old,new);self.assertEqual(self.case.lib.file(self.pid,new).read_bytes(),b'new-only-media')
  self.assertEqual(self.sync.sources(self.pid),[])
 def test_removed_external_file_preserves_bound_version(self):
  state=self.merge();old=self.entry(state)['data']['references'][0]
  (self.source/'actor.png').unlink()
  source=self.sync.sources(self.pid)[0];preview=self.sync.preview(self.pid,source['id'])
  self.assertEqual(preview['media'][0]['status'],'missing')
  state=self.merge();self.assertEqual(self.entry(state)['data']['references'],[old])
  self.assertEqual(self.case.lib.file(self.pid,old).read_bytes(),b'version-one')
  self.assertEqual(self.sync.sources(self.pid),[])

if __name__=='__main__':unittest.main()
