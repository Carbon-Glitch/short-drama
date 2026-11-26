import unittest
from pathlib import Path
import test_video_modes as fixture
from video_references import VideoReferences

class VideoReferenceTests(unittest.TestCase):
 def setUp(self):
  self.case=fixture.VideoModeTests();self.case.setUp();self.addCleanup(self.case.doCleanups)
  self.lib=self.case.lib;self.store=self.case.store;self.project=self.case.project;self.service=VideoReferences(self.lib,self.case.production.tool)
  self.case.content(body='A person waits in a quiet room.')
  file=self.lib.home.parent/'end.png';file.write_bytes(b'end-frame')
  self.lib.add_media(self.project,[file],self.store.state()['project']['revision'])
  self.ids={e['data']['name']:e['id'] for e in self.store.state()['entities'] if e['kind']=='media'}
 def update(self,choices,mode,voices=[]):return self.service.update(self.project,'video',choices,self.store.state()['project']['revision'],mode,voices)
 def test_empty_new_entry_requires_reference_or_explicit_text_choice(self):
  self.store.apply(self.store.state()['project']['revision'],[{'type':'update','id':'video','patch':{'text':'### 可复制提示词\n> A quiet room.'}}])
  self.assertEqual(self.service.describe(self.project,'video')['mode'],'reference')
  with self.assertRaisesRegex(ValueError,'参考'):self.case.production.prepare(self.project,'video','fixture',{})
  self.update([],'text')
  self.assertEqual(self.service.describe(self.project,'video')['mode'],'text')
 def test_last_reference_can_be_removed_as_draft_without_switching_to_text(self):
  self.update([{'media_id':self.ids['start'],'purpose':'身份'}],'reference')
  state=self.update([],'reference')
  entry=next(e for e in state['entities'] if e['id']=='video')
  self.assertEqual(entry['data']['generation_mode'],'reference');self.assertEqual(entry['data']['references'],[])
  with self.assertRaisesRegex(ValueError,'参考'):self.case.production.prepare(self.project,'video','fixture',{})
 def test_endpoints_compile_to_actual_first_last_roles(self):
  self.update([{'media_id':self.ids['start']},{'media_id':self.ids['end']}],'first_last_frame')
  preview=self.case.production.prepare(self.project,'video','fixture',{})['preview']
  self.assertEqual([b['role'] for b in preview['reference_bindings']],['first_frame','last_frame'])
  self.assertEqual(preview['reference_mode'],'first_last_frame')
 def test_voice_has_separate_order_and_character(self):
  self.update([{'media_id':self.ids['start'],'purpose':'身份'}],'reference',[{'media_id':self.ids['voice'],'character':'甲'}])
  preview=self.case.production.prepare(self.project,'video','fixture',{})['preview']
  self.assertEqual([b['role'] for b in preview['reference_bindings']],['reference_image','reference_audio'])
  self.assertEqual(preview['reference_bindings'][1]['character'],'甲')
  self.assertEqual(self.service.describe(self.project,'video')['voices'][0]['character'],'甲')
 def test_endpoint_voice_mixture_is_not_saved(self):
  before=self.store.state()
  with self.assertRaises(ValueError):self.update([{'media_id':self.ids['start']}],'first_frame',[{'media_id':self.ids['voice'],'character':'甲'}])
  self.assertEqual(self.store.state(),before)
 def test_reordering_remaps_reference_mentions_without_touching_dialogue(self):
  self.update([{'media_id':self.ids['start'],'purpose':'身份'},{'media_id':self.ids['end'],'purpose':'场景'}],'reference')
  state=self.store.state();entry=next(e for e in state['entities'] if e['id']=='video')
  self.store.apply(state['project']['revision'],[{'type':'update','id':'video','patch':{'text':entry['data']['text'].replace('A person waits in a quiet room.','Person from <Picture 1> in <Picture 2>. <d>[Chinese] <Picture 1></d>')}}])
  state=self.update([{'media_id':self.ids['end'],'purpose':'场景'},{'media_id':self.ids['start'],'purpose':'身份'}],'reference')
  text=next(e for e in state['entities'] if e['id']=='video')['data']['text']
  self.assertIn('Person from <Picture 2> in <Picture 1>. <d>[Chinese] <Picture 1></d>',text)
  with self.assertRaisesRegex(ValueError,'仍引用'):self.update([],'text')

if __name__=='__main__':unittest.main()
