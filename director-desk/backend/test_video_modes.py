import json
import unittest
import importlib.util
from pathlib import Path
import test_production as fixture

class VideoModeTests(unittest.TestCase):
 def setUp(self):
  self.case=fixture.ProductionTests();self.case.setUp();self.addCleanup(self.case.doCleanups)
  self.lib=self.case.library;self.store=self.case.store;self.project=self.case.project;self.production=self.case.production
  root=self.lib.home.parent
  picture=root/'start.png';picture.write_bytes(b'frame');sound=root/'voice.wav';sound.write_bytes(b'audio')
  state=self.lib.add_media(self.project,[picture,sound],self.store.state()['project']['revision'])
  self.media={e['data']['name']:e['data']['path'] for e in state['entities'] if e['kind']=='media'}
  episode=next(e['id'] for e in state['entities'] if e['kind']=='episode')
  self.store.apply(state['project']['revision'],[{'type':'create','id':'video-doc','kind':'document','data':{'name':'视频提示词.md','parent_id':episode,'structured':True}},
   {'type':'create','id':'video','kind':'submission','data':{'name':'视频','code':'MOTION-TEST','document_id':'video-doc','parent_id':episode,'text':''}}])
 def content(self,mode='图生视频',audio=False,purpose='起始帧',body='integrated_multimodal_description: a room'):
  reference=f'REF-START（顺序：1）· {self.media["start"]}《起点》（用途：{purpose}；控制：构图；不得控制：后续动作）'
  voice=f'REF-VOICE（顺序：1）· {self.media["voice"]}《音色》（用途：音色；角色：甲；控制：声纹；不得控制：台词）' if audio else '无'
  text=f'- 生成方式：{mode}\n- 时长：5s\n- 输入参考图：{reference}\n- 参考音频：{voice}\n\n### 可复制提示词\n> {body}\n'
  self.store.apply(self.store.state()['project']['revision'],[{'type':'update','id':'video','patch':{'text':text}}])
 def test_explicit_frame_mode_cannot_silently_drop_endpoint_control(self):
  self.content(mode='首帧',audio=True)
  with self.assertRaisesRegex(ValueError,'控制路线'):self.production.prepare(self.project,'video','fixture',{})
  self.assertEqual(self.production.list(self.project),[])
 def test_tail_without_start_is_rejected_before_job_creation(self):
  self.content(purpose='结束帧')
  with self.assertRaisesRegex(ValueError,'起始帧'):self.production.prepare(self.project,'video','fixture',{})
 def test_h3_base_prompt_cannot_run_with_audio_reference(self):
  config=json.loads(self.production.config.read_text());config['adapters']['fixture']['provider']='minimax-h3';self.production.config.write_text(json.dumps(config))
  self.content(audio=True)
  with self.assertRaisesRegex(ValueError,'结构与参考模式'):self.production.prepare(self.project,'video','fixture',{})
 def test_reference_mode_with_voice_remains_explicit(self):
  self.content(audio=True,body='subject_definitions: a speaker')
  preview=self.production.prepare(self.project,'video','fixture',{})['preview']
  self.assertEqual(preview['reference_mode'],'reference')
  self.assertTrue(preview['frame_images_as_references'])
  self.assertEqual([b['role'] for b in preview['reference_bindings']],['reference_image','reference_audio'])
 def test_valid_first_frame_is_visible_in_preview(self):
  self.content()
  preview=self.production.prepare(self.project,'video','fixture',{})['preview']
  self.assertEqual(preview['reference_mode'],'first_frame')
  self.assertEqual(preview['reference_bindings'][0]['role'],'first_frame')
  self.assertFalse(preview['frame_images_as_references'])
 def test_known_provider_cannot_ignore_project_model(self):
  self.content()
  config=json.loads(self.production.config.read_text());config['adapters']['fixture']['provider']='seedance';self.production.config.write_text(json.dumps(config))
  spec=next(e for e in self.store.state()['entities'] if e['kind']=='project_settings')
  self.store.apply(self.store.state()['project']['revision'],[{'type':'update','id':spec['id'],'patch':{'production_profile':{'status':'accepted','choices':{'target_video_model':'minimax-h3'}}}}])
  with self.assertRaisesRegex(ValueError,'目标模型不一致'):self.production.prepare(self.project,'video','fixture',{})
  self.assertEqual(self.production.list(self.project),[])
 def test_seedance_frame_preview_compiles_with_actual_adapter(self):
  self.content(body='人物从静止开始，缓慢回头。')
  config=json.loads(self.production.config.read_text());config['adapters']['fixture']['provider']='seedance';self.production.config.write_text(json.dumps(config))
  prepared=self.production.prepare(self.project,'video','fixture',{'ratio':'16:9','resolution':'768P'})
  self.assertEqual(prepared['preview']['parameters']['ratio'],'adaptive')
  self.assertNotIn('resolution',prepared['preview']['parameters'])
  self.assertTrue(prepared['preview']['ratio_from_first_frame'])
  job=json.loads(self.production.tool._job_path(self.store.root/prepared['workspace'],prepared['id']).read_text(encoding='utf8'))
  self.assertFalse((self.store.root/prepared['workspace']/'job.json').exists())
  spec=importlib.util.spec_from_file_location('seedance_contract_test',Path(self.production.tool.__file__).with_name('provider_adapters.py'))
  adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
  body=adapter.compile_seedance_payload(job,model='fixture-seedance-2.5',reference_urls=['https://example.com/frame.png'],reference_roles=['first_frame'],allowed_ratios={'adaptive'},duration_range=(4,30))
  self.assertEqual(body['ratio'],'adaptive');self.assertEqual(body['content'][1]['role'],'first_frame')
 def test_seedance_reference_preview_keeps_requested_ratio(self):
  self.content(purpose='身份',body='人物转身。')
  config=json.loads(self.production.config.read_text());config['adapters']['fixture']['provider']='seedance';self.production.config.write_text(json.dumps(config))
  preview=self.production.prepare(self.project,'video','fixture',{'ratio':'16:9'})['preview']
  self.assertEqual(preview['parameters']['ratio'],'16:9');self.assertFalse(preview['ratio_from_first_frame'])

if __name__=='__main__':unittest.main()
