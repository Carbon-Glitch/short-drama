"""Offline tests for editorial decisions, historical media and the actual production gate."""
import json,sys,tempfile,unittest
from pathlib import Path
import director_desk as desk
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'short-drama-produce/scripts'))
import production_tool as production

class DeskTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'project';self.ep=self.root/'剧集/EP001';self.ep.mkdir(parents=True)
        (self.root/'short-drama.json').write_text('{}');(self.ep/'剧本.md').write_text('# EP001 灯\n\n## EP001-SC001 内 · 屋 · 夜\n\n主人：还亮着。\n',encoding='utf8')
    def test_hold_blocks_real_run_without_consuming_confirmation(self):
        f=Path(self.tmp.name)/'job.json';output='剧集/EP001/制作成果/music/cue.wav'
        j={'job_id':'DIRECTOR-TEST-1','modality':'music','adapter':'fixture','prompt':'quiet','references':[],'outputs':[output],'parameters':{},'overwrite':False}
        f.write_text(json.dumps(j));cfg=f.with_name('adapters.json');cfg.write_text(json.dumps({'adapters':{'fixture':{'command':[sys.executable,str(Path(production.__file__).with_name('fixture_adapter.py'))],'timeout_seconds':30}}}))
        preview=production.prepare_job(self.root,f);production.confirm_job(self.root,job_id=j['job_id'],confirmation=preview['confirmation'])
        desk.action(self.ep,{'type':'hold','stage':'剧本','enabled':True})
        with self.assertRaisesRegex(ValueError,'导演台等待确认'):production.run_job(self.root,job_id=j['job_id'],adapter_config=cfg)
        self.assertFalse((self.root/output).exists())
        rev=desk.evidence(self.ep)['stages']['剧本']['rev'];desk.action(self.ep,{'type':'pass','stage':'剧本','rev':rev})
        self.assertEqual(production.run_job(self.root,job_id=j['job_id'],adapter_config=cfg)['state'],'succeeded')
        (self.ep/'剧本.md').write_text('changed');self.assertEqual(desk.blocked(self.ep,'资产'),'剧本')
    def test_review_preserves_overwritten_take_and_scope(self):
        p=self.ep/'制作成果/video/a.mp4';p.parent.mkdir(parents=True);p.write_bytes(b'old take')
        other=self.root/'剧集/EP002';other.mkdir()
        a=desk.manifest(self.ep)['media'][0]
        st=desk.action(self.ep,{'type':'note','stage':'回片','media':a['id'],'time':1,'end':2,'text':'手先动','owner':'分镜'})
        p.write_bytes(b'another take');v=desk.manifest(self.ep);self.assertNotEqual(v['media'][0]['id'],a['id'])
        self.assertEqual((self.ep/'.short-drama/director-media'/(a['id']+'.mp4')).read_bytes(),b'old take')
        self.assertEqual(desk.manifest(other)['decisions'],{});key=next(iter(st));self.assertEqual(st[key]['end'],2)
        self.assertTrue(desk.action(self.ep,{'type':'resolve','key':key,'stage':'回片','enabled':True})[key]['resolved'])
    def test_bind_changes_only_named_slot_and_keeps_old_job(self):
        folder=self.root/'输入';folder.mkdir()
        for n in ('a','b'):(folder/(n+'.png')).write_bytes(n.encode())
        line='REF-A（顺序：1）· 输入/a.png《人物》（用途：身份）'
        for n in ('视觉设定.md','分镜.md','视频提示词.md'):(self.ep/n).write_text(line,encoding='utf8')
        j=self.root/'.short-drama/production/jobs/j.json';j.parent.mkdir(parents=True);j.write_text(json.dumps({'source':'剧集/EP001/视频提示词.md','prompt':'old','references':['输入/a.png']}))
        st=desk.manifest(self.ep);new=next(a for a in st['media'] if a['name']=='b.png')
        revs={n:d['rev'] for n,d in st['docs'].items()};cmd=dict(type='bind',stage='资产',slot='REF-A',media=new['id'],revs=revs)
        desk.action(self.ep,dict(type='lock',stage='Design',name='视觉设定.md',rev=revs['视觉设定.md'],enabled=True))
        with self.assertRaisesRegex(ValueError,'解锁'):desk.action(self.ep,cmd)
        desk.action(self.ep,dict(type='lock',stage='Design',name='视觉设定.md',rev=revs['视觉设定.md'],enabled=False))
        desk.action(self.ep,cmd)
        for n in ('视觉设定.md','分镜.md','视频提示词.md'):self.assertIn('输入/b.png',(self.ep/n).read_text(encoding='utf8'))
        self.assertEqual(json.loads(j.read_text())['references'],['输入/a.png'])
        with self.assertRaisesRegex(ValueError,'更新'):desk.action(self.ep,cmd)
if __name__=='__main__':unittest.main()
