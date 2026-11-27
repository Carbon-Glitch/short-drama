import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from library import Library
from editing import Editing
from store import Conflict

@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe') and shutil.which('node'),'local media tools required')
class EditingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        source=self.root/'fixture.mp4'
        subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=blue:s=160x240:r=24','-t','1','-c:v','libx264','-pix_fmt','yuv420p',str(source)],check=True,capture_output=True)
        self.library=Library(self.root/'library');self.project=self.library.create('初剪测试');self.store=self.library.project(self.project)
        state=self.store.state();self.episode=next(e['id'] for e in state['entities'] if e['kind']=='episode');scene=next(e['id'] for e in state['entities'] if e['kind']=='scene')
        self.store.apply(state['project']['revision'],[{'type':'create','id':'shot1','kind':'shot','data':{'name':'第一镜','parent_id':scene,'code':'SHOT-1','order':0,'duration':'99s'}},
            {'type':'create','id':'shot2','kind':'shot','data':{'name':'第二镜','parent_id':scene,'code':'SHOT-2','order':1}}])
        self.library.add_media(self.project,[source],self.store.state()['project']['revision'],'shot1')
        media=next(e['id'] for e in self.store.state()['entities'] if e['kind']=='media')
        self.media=media;self.library.adopt(self.project,'shot1',media,self.store.state()['project']['revision'])
        self.editing=Editing(self.library)
    def test_plan_uses_actual_duration_and_ignores_unadopted_shots(self):
        plan=self.editing.plan(self.project,self.episode)
        self.assertEqual(len(plan['entries']),1);self.assertEqual(plan['missing'],1);self.assertAlmostEqual(plan['duration'],1,places=1)
    def test_multishot_unit_appears_only_once(self):
        self.store.apply(self.store.state()['project']['revision'],[{'type':'create','id':'unit','kind':'submission','data':{'name':'整组','parent_id':self.episode,'code':'MOTION-1','shot_ids':['shot1','shot2'],'adopted_media':self.media}}])
        plan=self.editing.plan(self.project,self.episode)
        self.assertEqual(len(plan['entries']),1);self.assertEqual(plan['missing'],0);self.assertEqual(plan['entries'][0]['shot_codes'],['SHOT-1','SHOT-2'])
    def test_mixed_valid_and_foreign_coverage_is_not_silently_trimmed(self):
        self.store.apply(self.store.state()['project']['revision'],[{'type':'create','id':'unit','kind':'submission','data':{'name':'旧关联','parent_id':self.episode,'shot_ids':['shot1','another-episode-shot'],'adopted_media':self.media}}])
        with self.assertRaisesRegex(ValueError,'重新关联分镜'):self.editing.plan(self.project,self.episode)
    def test_changed_plan_cannot_initialize(self):
        plan=self.editing.plan(self.project,self.episode)
        self.store.apply(plan['revision'],[{'type':'update','id':'shot1','patch':{'name':'已更新'}}])
        with self.assertRaises(Conflict):self.editing.create(self.project,self.episode,plan['revision'])
        self.assertFalse((self.store.root/'editing').exists())

    def test_initialization_receives_project_framing(self):
        spec=next(e for e in self.store.state()['entities'] if e['kind']=='project_settings')
        self.store.apply(self.store.state()['project']['revision'],[{'type':'update','id':spec['id'],'patch':{'format':{'aspect_ratio':'16:9','fps':30}}}])
        plan=self.editing.plan(self.project,self.episode)
        self.assertEqual(plan['format'],{'width':240,'height':136,'fps':30})
        received=[]
        def initialize(folder,seed):
            received.append(seed);(folder/'film.html').write_text('<html></html>')
        with patch.object(self.editing,'initialize',side_effect=initialize):self.editing.create(self.project,self.episode,plan['revision'])
        self.assertEqual(received[0]['fps'],30)
        self.assertEqual(received[0]['film']['stage'],{'w':240,'h':136})
    def test_native_openfilm_initialization_and_no_overwrite(self):
        runtime=Path.home()/'Documents/Codex/tools/short-drama-openfilm-0.4.1/node_modules/openfilm/package.json'
        if not runtime.is_file():self.skipTest('installed OpenFilm runtime required')
        state=self.editing.create(self.project,self.episode,self.store.state()['project']['revision'])
        episode=next(e for e in state['entities'] if e['id']==self.episode)
        film=self.store.root/episode['data']['film_path'];before=film.read_bytes()
        self.assertIn(b'data-shot-id="SHOT-1"',before)
        self.assertTrue((film.parent/'.short-drama/project.json').exists())
        self.assertEqual(len(list((film.parent/'assets').glob('*.mp4'))),1)
        self.editing.create(self.project,self.episode,state['project']['revision'])
        self.assertEqual(film.read_bytes(),before)

    def test_design_reaches_timeline_and_source_changes_are_detected(self):
        state=self.store.state();doc={'id':'visual'}
        state=self.store.apply(state['project']['revision'],[{'type':'create','id':'visual','kind':'document','data':{'parent_id':self.episode,'name':'视觉设定.md','structured':True}}])
        state=self.store.apply(state['project']['revision'],[
            {'type':'create','id':'decision','kind':'design','data':{'parent_id':self.episode,'document_id':doc['id'],'code':'DESIGN-001','name':'先证据','text':'先读票再接手'}},
            {'type':'update','id':'shot1','patch':{'design_intent':'DESIGN-001','reaction':'等门铃才伸手'}}])
        runtime=Path.home()/'Documents/Codex/tools/short-drama-openfilm-0.4.1/node_modules/openfilm/package.json'
        if not runtime.is_file():self.skipTest('installed OpenFilm runtime required')
        state=self.editing.create(self.project,self.episode,state['project']['revision'])
        ep=next(e for e in state['entities'] if e['id']==self.episode);film=self.store.root/ep['data']['film_path'];frozen=film.read_bytes()
        self.assertIn('DESIGN-001',film.read_text(encoding='utf8'))
        self.assertIn('先读票再接手',(film.parent/'视觉设定.md').read_text(encoding='utf8'))
        from skill_paths import skills_root
        helper=skills_root()/'short-drama/scripts/managed_sources.py'
        def check():
            return json.loads(subprocess.check_output([__import__('sys').executable,str(helper),str(film.parent)],env={**__import__('os').environ,'PYTHONIOENCODING':'utf-8'},text=True,encoding='utf8'))
        self.assertTrue(check()['current'])
        handoff=skills_root()/'short-drama-edit/scripts/openfilm/handoff.mjs'
        script='import {collect} from '+json.dumps(handoff.as_uri())+';const s=await collect(process.argv[1]);console.log(JSON.stringify({current:s.managedSource.current,codes:s.requirements.filter(r=>r.designCode).map(r=>r.designCode)}));'
        result=json.loads(subprocess.check_output(['node','--input-type=module','-e',script,str(film.parent)],text=True,encoding='utf8'))
        self.assertEqual(result,{'current':True,'codes':['DESIGN-001']})
        state=self.store.apply(state['project']['revision'],[{'type':'update','id':'decision','patch':{'text':'先翻票再响铃'}}])
        self.assertFalse(check()['current'])
        self.assertTrue(next(e for e in state['entities'] if e['kind']=='cut_binding')['stale'])
        self.editing.sync_documents(self.project,self.episode,film.parent)
        self.assertTrue(check()['current']);self.assertEqual(film.read_bytes(),frozen)
        self.assertIn('先翻票再响铃',(film.parent/'视觉设定.md').read_text(encoding='utf8'))
        draft=film.parent/'分镜.md';draft.write_text('用户手工改过的镜头',encoding='utf8')
        with self.assertRaisesRegex(ValueError,'手工修改'):self.editing.sync_documents(self.project,self.episode,film.parent)
        self.assertEqual(draft.read_text(encoding='utf8'),'用户手工改过的镜头')

if __name__=='__main__':unittest.main()
