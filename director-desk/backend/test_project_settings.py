import json
from pathlib import Path
import tempfile
import unittest
import zipfile
import test_production as fixture
from library import Library
from project_settings import settings,edit_format,update_specification,model_presets
from transfer import export_project,restore_project

class ProjectSpecificationTests(unittest.TestCase):
 def test_model_choice_reads_skill_and_preserves_custom_choices_until_changed(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);skills=root/'skills';file=skills/'short-drama-video-prompts/references/minimax-h3.md';file.parent.mkdir(parents=True)
   choice={'target_video_model':'minimax-h3','video_prompt_dialect':'minimax-h3','video_prompt_language':'en','native_duration_seconds':{'min':4,'max':11}}
   file.write_text('```json\n'+json.dumps(choice)+'\n```',encoding='utf8')
   lib=Library(root/'library');store=lib.project(lib.create('模型选择'));scene=next(e for e in store.state()['entities'] if e['kind']=='scene')
   state=store.apply(1,[{'type':'create','id':'shot','kind':'shot','data':{'parent_id':scene['id']}}, {'type':'create','id':'image','kind':'image_prompt','data':{'name':'图'}}])
   state=store.review('shot',state['project']['revision']);state=store.review('image',state['project']['revision'])
   state=update_specification(store,state['project']['revision'],{'aspect_ratio':'16:9','fps':30},'minimax-h3',skills)
   self.assertEqual(settings(state)['production_profile']['choices'],choice)
   self.assertTrue(next(e for e in state['entities'] if e['id']=='shot')['stale'])
   self.assertFalse(next(e for e in state['entities'] if e['id']=='image')['stale'])
   spec=next(e for e in state['entities'] if e['kind']=='project_settings');profile=settings(state)['production_profile'];profile['choices']['native_duration_seconds']['max']=8
   state=store.apply(state['project']['revision'],[{'type':'update','id':spec['id'],'patch':{'production_profile':profile}}])
   state=update_specification(store,state['project']['revision'],{'aspect_ratio':'9:16'},'minimax-h3',skills)
   self.assertEqual(settings(state)['production_profile']['choices']['native_duration_seconds']['max'],8)
 def test_edit_format_uses_project_ratio_and_fps_without_upscaling_long_edge(self):
  state={'entities':[{'kind':'project_settings','data':{'format':{'aspect_ratio':'16:9','fps':30}}}]}
  self.assertEqual(edit_format(state,720,1280),{'width':1280,'height':720,'fps':30})
  state['entities'][0]['data']['format']={'aspect_ratio':'9:16','fps':23.976}
  self.assertEqual(edit_format(state,1920,1080),{'width':1080,'height':1920,'fps':23.976})
  state['entities'][0]['data']['format']={}
  self.assertEqual(edit_format(state,720,1290),{'width':720,'height':1290,'fps':24})
  state['entities'][0]['data']['format']={'fps':float('nan')}
  with self.assertRaises(ValueError):edit_format(state,720,1280)
 def test_import_and_single_episode_export_keep_specifications_without_credentials(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);source=root/'legacy';source.mkdir()
   config={'title':'横屏项目','language':'zh-CN','format':{'aspect_ratio':'16:9','prompt_language':'en','target_seconds_per_episode':45},
    'api_key':'must-not-travel','creator_authority':{'production_profile':{'status':'accepted','choices':{'target_video_model':'minimax-h3','native_duration_seconds':{'min':4,'max':15},'api_key':'also-private'}}}}
   (source/'short-drama.json').write_text(json.dumps(config),encoding='utf8')
   (source/'剧本.md').write_text('# EP001\n## EP001-SC001 第一场\n甲：别走。',encoding='utf8')
   lib=Library(root/'library');pid=lib.import_project(source);store=lib.project(pid);state=store.state()
   self.assertEqual(settings(state)['format'],config['format'])
   episode=next(e['id'] for e in state['entities'] if e['kind']=='episode')
   archive=root/'single.zip';export_project(store,archive,episode=episode)
   with zipfile.ZipFile(archive) as bundle:
    exported=json.loads(bundle.read('short-drama.json'))
    self.assertEqual(exported['format']['aspect_ratio'],'16:9')
    self.assertEqual(exported['creator_authority']['production_profile']['choices']['native_duration_seconds'],{'min':4,'max':15})
    self.assertNotIn('api_key',json.dumps(exported))
   other=Library(root/'other');restored=other.project(restore_project(other,archive))
   self.assertEqual(settings(restored.state()),settings(state))
 def test_production_uses_project_defaults_and_keeps_them_in_snapshot(self):
  case=fixture.ProductionTests();case.setUp();self.addCleanup(case.doCleanups)
  state=case.store.state();spec=next(e for e in state['entities'] if e['kind']=='project_settings')
  case.store.apply(state['project']['revision'],[{'type':'update','id':spec['id'],'patch':{'format':{'aspect_ratio':'16:9','prompt_language':'en','target_seconds_per_episode':45}}}])
  prepared=case.production.prepare(case.project,'prompt','fixture',{})
  self.assertEqual(prepared['preview']['parameters']['ratio'],'16:9')
  self.assertEqual(prepared['preview']['parameters']['prompt_language'],'en')
  snapshot=json.loads((case.store.root/prepared['workspace']/'short-drama.json').read_text(encoding='utf8'))
  self.assertEqual(snapshot['format']['target_seconds_per_episode'],45)

if __name__=='__main__':unittest.main()
