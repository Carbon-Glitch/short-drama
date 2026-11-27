import json
from pathlib import Path
import tempfile
import unittest
import sys
from unittest.mock import patch
from library import Library
from tasks import TaskQueue
from agent_worker import AgentWorker,TaskInputRequired

class Settings:
    def __init__(self):self.enabled=True
    def read(self):return {'agent_enabled':self.enabled}

class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.lib=Library(self.temp.name);self.pid=self.lib.create('夹具项目');self.store=self.lib.project(self.pid)
        self.store.apply(self.store.state()['project']['revision'],[{'type':'create','id':'fixture-shot','kind':'shot','data':{'name':'旧镜头','action':'旧动作'}}])
        self.queue=TaskQueue(self.store);self.settings=Settings()
    def task(self):return self.queue.create('改动作',['fixture-shot'])
    def result(self):return {'operations_json':json.dumps([{'type':'update','id':'fixture-shot','patch':{'action':'新动作'}}]),'message':'已修改动作'}
    def action(self):return next(e for e in self.store.state()['entities'] if e['id']=='fixture-shot')['data']['action']
    def test_queued_task_commits_and_can_undo(self):
        self.task();worker=AgentWorker(self.lib,self.settings,lambda p,a:self.result())
        self.assertTrue(worker.tick());self.assertEqual(self.action(),'新动作')
        self.assertEqual(self.queue.list()[0]['status'],'completed')
        self.store.undo(self.store.state()['project']['revision']);self.assertEqual(self.action(),'旧动作')
    def test_disabled_worker_does_not_claim(self):
        self.task();self.settings.enabled=False
        worker=AgentWorker(self.lib,self.settings,lambda p,a:self.fail('must not execute'))
        worker.tick();self.assertEqual(self.queue.list()[0]['status'],'queued')
    def test_conflict_keeps_user_edit_and_retry_uses_new_basis(self):
        task=self.task()
        def runner(payload,active):
            self.store.apply(self.store.state()['project']['revision'],[{'type':'update','id':'fixture-shot','patch':{'action':'用户修改'}}])
            return self.result()
        AgentWorker(self.lib,self.settings,runner).tick()
        self.assertEqual(self.action(),'用户修改');failed=self.queue.list()[0]
        self.assertEqual(failed['status'],'failed');self.assertTrue(failed['result']['operations'])
        retry=self.queue.retry(task)
        self.assertNotEqual(task,retry)
        AgentWorker(self.lib,self.settings,lambda p,a:self.result()).tick()
        self.assertEqual(self.action(),'新动作')
    def test_cancelled_result_never_applies(self):
        task=self.task()
        def runner(p,active):
            self.queue.cancel(task);self.assertFalse(active());return self.result()
        AgentWorker(self.lib,self.settings,runner).tick()
        self.assertEqual(self.action(),'旧动作');self.assertEqual(self.queue.list()[0]['status'],'cancelled')
    def test_interrupted_lease_is_not_automatically_resubmitted(self):
        task=self.task();self.queue.claim(task,'director-agent-dead',-1);self.queue.recover()
        self.assertEqual(self.queue.list()[0]['status'],'failed')
    def test_cli_contract_with_local_process_fixture(self):
        self.task()
        executable=Path(self.temp.name)/'fixture_cli.py'
        executable.write_text("import json,sys\nfrom pathlib import Path\nassert '--sandbox' in sys.argv and sys.argv[sys.argv.index('--sandbox')+1]=='read-only'\nassert '--model' not in sys.argv\nassert '<project_context>' in sys.stdin.read()\npayload=json.loads(Path('context.json').read_text(encoding='utf8'))\nassert payload['task']['scope']==['fixture-shot']\noutput=Path(sys.argv[sys.argv.index('--output-last-message')+1])\noutput.write_text(json.dumps({'operations_json':'[]','message':'fixture process completed'}),encoding='utf8')\n",encoding='utf8')
        with patch('agent_worker.codex_command',return_value=[sys.executable,str(executable)]):
            AgentWorker(self.lib,self.settings).tick()
        task=self.queue.list()[0]
        self.assertEqual(task['status'],'completed')
        self.assertEqual(task['result']['message'],'fixture process completed')

    def test_model_reported_failure_is_not_completed(self):
        self.task()
        AgentWorker(self.lib,self.settings,lambda p,a:{'outcome':'failed','operations_json':'[]','message':'资料缺失'}).tick()
        self.assertEqual(self.queue.list()[0]['status'],'failed')
        self.assertEqual(self.queue.list()[0]['result']['message'],'资料缺失')
        self.assertEqual(self.action(),'旧动作')

    def test_noop_finishes_without_revision_change(self):
        self.task();revision=self.store.state()['project']['revision']
        AgentWorker(self.lib,self.settings,lambda p,a:{'operations_json':'[]','message':'无需修改'}).tick()
        self.assertEqual(self.queue.list()[0]['status'],'completed');self.assertEqual(self.store.state()['project']['revision'],revision)

    def test_explicit_role_wins_over_mixed_episode_contents(self):
        skills=Path(self.temp.name)/'skills'
        for role in ('write','design','storyboard','assets','image-prompts','video-prompts','review'):
            path=skills/f'short-drama-{role}/SKILL.md';path.parent.mkdir(parents=True);path.write_text('ROLE:'+role)
        payload={'task':{'scope':['episode','video'],'prompt':'根据分镜整理资产并准备图片提示词','skill':'assets'},'project':{'entities':[{'id':'episode','kind':'episode','data':{}},{'id':'video','kind':'submission','data':{}}]}}
        self.assertIn('ROLE:assets',AgentWorker.knowledge(payload,skills))
        self.assertNotIn('ROLE:video-prompts',AgentWorker.knowledge(payload,skills))
        payload['task'].update(skill='',prompt='通读本集剧本，改稿')
        self.assertIn('ROLE:write',AgentWorker.knowledge(payload,skills))

    def test_video_knowledge_selects_one_dialect_from_task_or_accepted_profile(self):
        skills=Path(self.temp.name)/'dialect-skills'
        files=['SKILL.md','references/minimax-h3.md','references/seedance-2.5.md','references/execution-model-25.md','references/submit-entry-format.md']
        for name in files:
            path=skills/'short-drama-video-prompts'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('FILE:'+name)
        payload={'task':{'scope':['unit'],'skill':'video-prompts','prompt':'准备视频提示词'},'project':{'entities':[
            {'id':'unit','kind':'submission','data':{'text':'历史描述同时提到 MiniMax H3 和 Seedance'}},
            {'id':'spec','kind':'project_settings','data':{'production_profile':{'status':'accepted','choices':{'target_video_model':'minimax-h3'}}}}]}}
        text=AgentWorker.knowledge(payload,skills)
        self.assertIn('FILE:references/minimax-h3.md',text);self.assertNotIn('FILE:references/seedance-2.5.md',text)
        payload['task']['prompt']='按 Seedance 2.5 准备视频提示词'
        text=AgentWorker.knowledge(payload,skills)
        self.assertIn('FILE:references/seedance-2.5.md',text);self.assertIn('FILE:references/execution-model-25.md',text)
        self.assertNotIn('FILE:references/minimax-h3.md',text)
        payload['task']['prompt']='H3 和 Seedance 都写'
        with self.assertRaises(TaskInputRequired):AgentWorker.knowledge(payload,skills)
        payload['task']['prompt']='准备视频提示词';payload['project']['entities'].pop()
        with self.assertRaisesRegex(TaskInputRequired,'注明目标模型'):AgentWorker.knowledge(payload,skills)

    def test_missing_task_input_reports_specific_reason(self):
        self.task()
        def runner(payload,active):raise TaskInputRequired('请注明目标模型')
        AgentWorker(self.lib,self.settings,runner).tick()
        self.assertEqual(self.queue.list()[0]['result']['message'],'请注明目标模型')

    def test_review_process_receives_only_script_and_returns_without_editing(self):
        episode=next(e for e in self.store.state()['entities'] if e['kind']=='episode')
        scene=next(e for e in self.store.state()['entities'] if e['kind']=='scene')
        self.store.apply(self.store.state()['project']['revision'],[
            {'type':'update','id':scene['id'],'patch':{'text':'甲：等一下。','blocking':'PRIVATE_DIRECTION'}},
            {'type':'create','id':'private-design','kind':'design','data':{'parent_id':episode['id'],'text':'PRIVATE_DESIGN'}}])
        self.queue.create('首看剧本',[episode['id']],'review','script_review')
        revision=self.store.state()['project']['revision']
        executable=Path(self.temp.name)/'review_cli.py'
        executable.write_text("import json,sys\nfrom pathlib import Path\nprompt=sys.stdin.read()\nassert 'PRIVATE_DIRECTION' not in prompt and 'PRIVATE_DESIGN' not in prompt\npayload=json.loads(Path('context.json').read_text(encoding='utf8'))\nassert payload['task']['mode']=='script_review'\nassert not Path('reading').exists()\nassert {e['kind'] for e in payload['project']['entities']} <= {'scene','episode'}\nPath(sys.argv[sys.argv.index('--output-last-message')+1]).write_text(json.dumps({'outcome':'completed','operations_json':'[]','message':'fixture script review'}),encoding='utf8')\n",encoding='utf8')
        with patch('agent_worker.codex_command',return_value=[sys.executable,str(executable)]):
            AgentWorker(self.lib,self.settings).tick()
        self.assertEqual(self.queue.list()[0]['status'],'completed')
        self.assertEqual(self.store.state()['project']['revision'],revision)

    def test_creative_stages_receive_self_check_and_early_performance(self):
        from skill_paths import skills_root
        skills=skills_root()
        for stage in ('design','storyboard','video-prompts','review'):
            payload={'task':{'scope':['entry'],'skill':stage,'prompt':'用 Seedance 2.5 处理当前内容','mode':'edit'},'project':{'entities':[{'id':'entry','kind':'shot','data':{}}]}}
            text=AgentWorker.knowledge(payload,skills)
            self.assertEqual(text.count('### short-drama-review/references/director-self-check.md'),1,stage)
            self.assertIn('anti-AI test',text)
            self.assertIn('内层拍段与外层镜长一起核对',text)
            if stage!='review':
                self.assertIn('眼任务指向对手',text)
                self.assertIn('被打断的活是最强重音',text)
        payload['task'].update(skill='review',mode='script_review')
        text=AgentWorker.knowledge(payload,skills)
        self.assertNotIn('### short-drama-review/references/director-self-check.md',text)
        self.assertNotIn('### short-drama-video-prompts/references/performance-direction.md',text)

if __name__=='__main__':unittest.main()
