import unittest
from creative_context import context_ids,project_context

class CreativeContextTests(unittest.TestCase):
 def test_complete_decisions_and_neighbors_without_unrelated_episode(self):
  def e(id,kind,**data):return {'id':id,'kind':kind,'data':data,'revision':1,'stale':False}
  entities=[e('ep','episode'),e('other','episode'),e('scene','scene',parent_id='ep',text='完整准确对白'),e('design','design',parent_id='ep',code='DESIGN-001',text='先读到证据，听者才转身。'),e('unrelated','design',parent_id='other',text='别集秘密')]
  for i in range(5):entities.append(e(str(i),'shot',parent_id='scene',order=i,action='完整动作'+str(i),reaction='听者反应'+str(i),sound_cues='听到门铃后才转身'))
  entities.append(e('group','submission',parent_id='ep',shot_ids=['2'],text='执行正文'))
  state={'project':{},'entities':entities,'dependencies':[{'source':'design','target':'2','fields':['text'],'source_revision':1}]}
  ids=context_ids(state,['group'],'video-prompts');self.assertTrue({'group','2','1','3','scene','ep','design'}<=ids)
  self.assertFalse({'0','4','other','unrelated'}&ids)
  records={x['id']:x for x in project_context(state,ids)['entities']}
  self.assertEqual(records['2']['data']['reaction'],'听者反应2')
  self.assertEqual(records['design']['data']['text'],'先读到证据，听者才转身。')
 def test_old_imported_versions_never_compete_with_current_shot(self):
  state={'project':{},'dependencies':[],'entities':[
   {'id':'doc','kind':'document','data':{'structured':True,'original':'STALE DESIGN','source_baseline':'STALE BASE','name':'视觉设定.md'}},
   {'id':'shot','kind':'shot','data':{'action':'当前动作','fields':{'唯一动作':'STALE ACTION','作者备注':'保留备注'},'source_text':'- 唯一动作：STALE AGAIN\n自由创作批注。'}}]}
  result=project_context(state,{'doc','shot'})
  import json
  self.assertNotIn('STALE',json.dumps(result,ensure_ascii=False))
  self.assertIn('当前动作',json.dumps(result,ensure_ascii=False));self.assertIn('自由创作批注',json.dumps(result,ensure_ascii=False));self.assertIn('保留备注',json.dumps(result,ensure_ascii=False))
  self.assertEqual(state['entities'][1]['data']['fields']['唯一动作'],'STALE ACTION')

if __name__=='__main__':unittest.main()
