import unittest
import test_production as production_fixture
from prompt_references import PromptReferences
from store import Conflict

class ReferenceSelectionTests(unittest.TestCase):
 def setUp(self):
  self.fixture=production_fixture.ProductionTests();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
  self.lib=self.fixture.library;self.pid=self.fixture.project;self.store=self.fixture.store
  root=self.lib.home.parent
  a=root/'人物.png';a.write_bytes(b'character-image');b=root/'构图.png';b.write_bytes(b'composition-image')
  state=self.lib.add_media(self.pid,[a,b],self.store.state()['project']['revision'])
  self.images={e['data']['name']:e['id'] for e in state['entities'] if e['kind']=='media'}
  self.refs=PromptReferences(self.lib,self.fixture.production.tool)
 def test_selection_compiles_order_and_actual_reference_files(self):
  choices=[{'media_id':self.images['人物'],'purpose':'身份'},{'media_id':self.images['构图'],'purpose':'构图'}]
  self.refs.update(self.pid,'prompt',choices,self.store.state()['project']['revision'])
  preview=self.fixture.production.prepare(self.pid,'prompt','fixture',{})['preview']
  self.assertEqual([r['label'] for r in preview['reference_bindings']],['人物','构图'])
  self.assertEqual([r['order'] for r in preview['reference_bindings']],[1,2])
  self.assertEqual(preview['prompt'],'一束窗光落在木桌上。')
  self.assertEqual(self.refs.describe(self.pid,'prompt')['choices'],choices)
 def test_existing_custom_constraints_survive_reorder_and_removal(self):
  choices=[{'media_id':self.images['人物'],'purpose':'身份'}]
  state=self.refs.update(self.pid,'prompt',choices,self.store.state()['project']['revision'])
  entry=next(e for e in state['entities'] if e['id']=='prompt')
  text=entry['data']['text'].replace('控制：主体外观、身份','控制：鼻梁、脸上雀斑')
  state=self.store.apply(state['project']['revision'],[{'type':'update','id':'prompt','patch':{'text':text}}])
  state=self.refs.update(self.pid,'prompt',choices,state['project']['revision'])
  self.assertIn('鼻梁、脸上雀斑',next(e for e in state['entities'] if e['id']=='prompt')['data']['text'])
  state=self.refs.update(self.pid,'prompt',[],state['project']['revision'])
  self.assertIn('- 参考：无',next(e for e in state['entities'] if e['id']=='prompt')['data']['text'])
  self.assertFalse(any(d['source'] in self.images.values() for d in state['dependencies']))
 def test_stale_selection_cannot_overwrite_concurrent_edit(self):
  version=self.store.state()['project']['revision']
  self.store.apply(version,[{'type':'update','id':'prompt','patch':{'name':'新名称'}}])
  with self.assertRaises(Conflict):self.refs.update(self.pid,'prompt',[],version)

if __name__=='__main__':unittest.main()
