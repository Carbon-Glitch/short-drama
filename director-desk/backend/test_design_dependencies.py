from pathlib import Path
import tempfile
import unittest
from store import ProjectStore

class DesignDependencyTests(unittest.TestCase):
 def test_design_update_marks_only_matching_scene_shots(self):
  with tempfile.TemporaryDirectory() as temp:
   store=ProjectStore.create(Path(temp),'测试');ops=[]
   for i in (1,2):
    ops.extend([{'type':'create','id':f'sc{i}','kind':'scene','data':{'name':'场景','code':f'EP001-SC00{i}'}},
     {'type':'create','id':f'shot{i}','kind':'shot','data':{'parent_id':f'sc{i}','name':'镜头'}}])
   ops.append({'type':'create','id':'design','kind':'design','data':{'name':'场面设计 · EP001-SC001','text':'暖光'}})
   state=store.apply(0,ops)
   self.assertEqual([d['target'] for d in state['dependencies']],['shot1'])
   after=store.apply(state['project']['revision'],[{'type':'update','id':'design','patch':{'text':'冷光'}}])
   self.assertEqual([e['id'] for e in after['entities'] if e['stale']],['shot1'])
   store.undo(after['project']['revision'])
   self.assertFalse(any(e['stale'] for e in store.state()['entities']))

 def test_asset_owner_propagates_design_changes_without_mutating_media(self):
  with tempfile.TemporaryDirectory() as temp:
   store=ProjectStore.create(Path(temp),'资产链路')
   state=store.apply(0,[
    {'type':'create','id':'ep','kind':'episode','data':{'name':'第一集'}},
    {'type':'create','id':'sc','kind':'scene','data':{'parent_id':'ep'}},
    {'type':'create','id':'d','kind':'design','data':{'parent_id':'ep','code':'DESIGN-001','text':'透明玻璃手套'}},
    {'type':'create','id':'img','kind':'image_prompt','data':{'parent_id':'ep','text':'- 设计承接：DESIGN-001','adopted_media':'media'}},
    {'type':'create','id':'media','kind':'media','data':{'path':'media/image.png','type':'image','sha256':'f'*64}},
    {'type':'create','id':'shot','kind':'shot','data':{'parent_id':'sc','references':['media']}},
    {'type':'create','id':'other','kind':'shot','data':{'parent_id':'sc'}},
    {'type':'create','id':'unit','kind':'submission','data':{'parent_id':'ep','shot_ids':['shot']}},
    {'type':'bind','source':'shot','target':'unit','fields':['action']}])
   for kind in ('image_prompt','shot','submission'):
    for entity in list(state['entities']):
     if entity['kind']==kind and entity['stale']:state=store.review(entity['id'],state['project']['revision'])
   old_media=next(e for e in state['entities'] if e['id']=='media')
   state=store.apply(state['project']['revision'],[{'type':'update','id':'d','patch':{'text':'保留半透明磨砂玻璃'}}])
   self.assertEqual({e['id'] for e in state['entities'] if e['stale']},{'img','shot','unit'})
   self.assertEqual(next(e for e in state['entities'] if e['id']=='media'),old_media)

if __name__=='__main__':unittest.main()
