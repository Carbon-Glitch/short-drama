import hashlib,json,os,tempfile,unittest
from pathlib import Path
from library import Library
from discovery import Discovery
from source_sync import ScriptSync

class DocumentSyncTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);root=Path(self.tmp.name)
  self.source=root/'source';self.source.mkdir();(self.source/'剧本.md').write_text('# EP001\n## EP001-SC001 第一场\n甲：你好。',encoding='utf8')
  self.visual='# 视觉设定\n## 人物 · 甲\n灰衣，沉默。\n## 体验设计\n先等待。'
  (self.source/'视觉设定.md').write_text(self.visual,encoding='utf8')
  (self.source/'视频提示词.md').write_text('# 视频提示词\n## MOTION-001 · 等待\n- 分镜：SHOT-001\n### 可复制提示词\n> Wait.',encoding='utf8')
  (self.source/'分镜.md').write_text('## SHOT-001 · 等待\n- 来源：EP001-SC001\n- 唯一动作：等待',encoding='utf8')
  registry=root/'registry';registry.mkdir();key=hashlib.sha256(os.path.normcase(str(self.source.resolve())).encode()).hexdigest()
  (registry/(key+'.json')).write_text(json.dumps({'path':str(self.source)}),encoding='utf8')
  self.lib=Library(root/'library');self.discovery=Discovery(self.lib,registry);self.pid=self.discovery.open(key);self.store=self.lib.project(self.pid);self.sync=ScriptSync(self.lib,self.discovery)
 def doc(self,name):return next(e for e in self.store.state()['entities'] if e['kind']=='document' and e['data']['name']==name)
 def merge(self,doc,choices={}):
  preview=self.sync.preview(self.pid,doc['id']);return self.sync.apply(self.pid,doc['id'],preview['revision'],preview['source_hash'],choices)
 def test_visual_text_merges_without_replacing_identity_or_local_name(self):
  char=next(e for e in self.store.state()['entities'] if e['kind']=='character')
  self.store.apply(self.store.state()['project']['revision'],[{'type':'update','id':char['id'],'patch':{'name':'甲的新显示名'}}])
  (self.source/'视觉设定.md').write_text(self.visual.replace('灰衣，沉默。','灰衣，试探。'),encoding='utf8')
  self.assertEqual(len(self.sync.sources(self.pid)),1)
  state=self.merge(self.doc('视觉设定.md'));updated=next(e for e in state['entities'] if e['id']==char['id'])
  self.assertEqual(updated['data']['text'],'灰衣，试探。');self.assertEqual(updated['data']['name'],'甲的新显示名')
  self.assertEqual(self.sync.sources(self.pid),[])
  self.store.undo(state['project']['revision']);self.assertEqual(len(self.sync.sources(self.pid)),1)
 def test_same_section_conflict_requires_explicit_choice(self):
  char=next(e for e in self.store.state()['entities'] if e['kind']=='character')
  self.store.apply(self.store.state()['project']['revision'],[{'type':'update','id':char['id'],'patch':{'text':'本地蓝衣'}}])
  (self.source/'视觉设定.md').write_text(self.visual.replace('灰衣，沉默。','外部红衣'),encoding='utf8')
  doc=self.doc('视觉设定.md');preview=self.sync.preview(self.pid,doc['id'])
  change=next(c for c in preview['changes'] if c.get('field')=='text');self.assertTrue(change['conflict'])
  with self.assertRaises(ValueError):self.merge(doc)
  result=self.merge(doc,{change['key']:'current'})
  self.assertEqual(next(e for e in result['entities'] if e['id']==char['id'])['data']['text'],'本地蓝衣')
 def test_new_video_entry_keeps_shot_binding_and_existing_id(self):
  doc=self.doc('视频提示词.md');old=next(e for e in self.store.state()['entities'] if e['kind']=='submission')
  path=self.source/'视频提示词.md';path.write_text(path.read_text(encoding='utf8').replace('等待','静默')+'\n## MOTION-002 · 插入\n- 分镜：SHOT-001\n### 可复制提示词\n> Cut.',encoding='utf8')
  state=self.merge(doc);existing=next(e for e in state['entities'] if e['id']==old['id']);new=next(e for e in state['entities'] if e['data'].get('code')=='MOTION-002')
  self.assertEqual(existing['data']['name'],'静默');self.assertEqual(len(new['data']['shot_ids']),1)
  self.assertTrue(any(d['source']==new['data']['shot_ids'][0] and d['target']==new['id'] for d in state['dependencies']))
 def test_duplicate_heading_and_source_race_do_not_overwrite(self):
  doc=self.doc('视觉设定.md');path=self.source/'视觉设定.md';path.write_text(self.visual+'\n## 人物 · 甲\n重复',encoding='utf8')
  with self.assertRaisesRegex(ValueError,'重复'):self.sync.preview(self.pid,doc['id'])
  path.write_text(self.visual+'\n新说明',encoding='utf8');preview=self.sync.preview(self.pid,doc['id'])
  path.write_text(self.visual+'\n又变了',encoding='utf8')
  with self.assertRaisesRegex(ValueError,'又有更新'):self.sync.apply(self.pid,doc['id'],preview['revision'],preview['source_hash'],{})

if __name__=='__main__':unittest.main()
