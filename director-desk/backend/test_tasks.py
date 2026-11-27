from pathlib import Path
import tempfile
import unittest
from store import ProjectStore,Conflict
from tasks import TaskQueue


class TaskTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=ProjectStore.create(Path(self.temp.name)/'project','任务')
        self.store.apply(0,[{'type':'create','id':'a','kind':'shot','data':{'action':'原动作'}},
                            {'type':'create','id':'b','kind':'shot','data':{'action':'另一镜'}}])
        self.queue=TaskQueue(self.store)

    def test_agent_change_is_scoped_atomic_and_undoable(self):
        task=self.queue.create('只改这一镜',['a']);self.queue.claim(task,'test-agent')
        state=self.queue.finish(task,'test-agent',[{'type':'update','id':'a','patch':{'action':'新动作'}}],'已修改')
        self.assertEqual(self.queue.list()[0]['status'],'completed')
        restored=self.store.undo(state['project']['revision'])
        self.assertEqual(next(e for e in restored['entities'] if e['id']=='a')['data']['action'],'原动作')

    def test_creative_role_survives_retry(self):
        task=self.queue.create('根据分镜写图片提示词',['a'],'image-prompts')
        self.assertEqual(self.queue.claim(task,'agent')['task']['skill'],'image-prompts')
        self.queue.fail(task,'agent','重试')
        retry=self.queue.retry(task)
        self.assertEqual(next(t for t in self.queue.list() if t['id']==retry)['skill'],'image-prompts')
        with self.assertRaises(ValueError):self.queue.create('任务',['a'],'unknown')

    def test_out_of_scope_batch_has_no_partial_side_effect(self):
        task=self.queue.create('修改',['a']);self.queue.claim(task,'agent')
        with self.assertRaises(ValueError):self.queue.finish(task,'agent',[
            {'type':'update','id':'a','patch':{'action':'不能留下'}},
            {'type':'update','id':'b','patch':{'action':'越权'}}])
        self.assertEqual(self.store.state()['project']['revision'],1)
        self.assertEqual(self.queue.list()[0]['status'],'running')

    def test_user_edit_during_agent_work_blocks_stale_result(self):
        task=self.queue.create('修改',['a']);self.queue.claim(task,'agent')
        self.store.apply(1,[{'type':'update','id':'a','patch':{'action':'用户新改稿'}}])
        with self.assertRaises(Conflict):self.queue.finish(task,'agent',[{'type':'update','id':'a','patch':{'action':'旧上下文结果'}}])
        self.assertEqual(self.store.state()['project']['revision'],2)

    def test_cancel_prevents_result_commit(self):
        task=self.queue.create('修改',['a']);self.queue.claim(task,'agent');self.queue.cancel(task)
        with self.assertRaises(ValueError):self.queue.finish(task,'agent',[{'type':'update','id':'a','patch':{'action':'晚到结果'}}])

    def test_script_review_excludes_intent_and_cannot_write(self):
        self.store.apply(1,[{'type':'create','id':'ep','kind':'episode','data':{'name':'第一集','intent':'HIDDEN_EP_INTENT'}},
                            {'type':'create','id':'scene','kind':'scene','data':{'parent_id':'ep','text':'甲：你好。','blocking':'HIDDEN_BLOCKING','director_review':'HIDDEN_OLD_REVIEW'}},
                            {'type':'create','id':'design','kind':'design','data':{'parent_id':'ep','text':'HIDDEN_DESIGN'}},
                            {'type':'bind','source':'design','target':'scene','fields':['text']}])
        task=self.queue.create('首看剧本',['ep'],'review','script_review')
        payload=self.queue.claim(task,'reader')
        import json
        self.assertNotIn('HIDDEN_',json.dumps(payload,ensure_ascii=False))
        self.assertEqual({e['kind'] for e in payload['project']['entities']},{'scene','episode'})
        self.assertNotIn('design',payload['task']['basis'])
        with self.assertRaisesRegex(ValueError,'只返回判断'):
            self.queue.finish(task,'reader',[{'type':'update','id':'scene','patch':{'text':'不应改稿'}}])
        revision=self.store.state()['project']['revision']
        self.queue.finish(task,'reader',[],'能看懂问候，但后续期待不明确。')
        self.assertEqual(self.store.state()['project']['revision'],revision)

    def test_review_rejects_stale_script_and_retry_preserves_mode(self):
        self.store.apply(1,[{'type':'create','id':'scene','kind':'scene','data':{'text':'旧剧本'}}])
        task=self.queue.create('首看',['scene'],'review','script_review');self.queue.claim(task,'reader')
        self.store.apply(2,[{'type':'update','id':'scene','patch':{'text':'新剧本'}}])
        with self.assertRaises(Conflict):self.queue.finish(task,'reader',[],'旧判断')
        self.queue.fail(task,'reader','来源更新')
        retry=self.queue.retry(task)
        self.assertEqual(self.queue.claim(retry,'reader')['task']['mode'],'script_review')

    def test_new_context_child_during_work_requires_rebase(self):
        state=self.store.apply(1,[{'type':'create','id':'ep','kind':'episode','data':{'name':'第一集'}},
            {'type':'create','id':'sc','kind':'scene','data':{'parent_id':'ep','text':'原剧本'}}])
        task=self.queue.create('写分镜',['ep'],'storyboard');self.queue.claim(task,'agent')
        self.store.apply(state['project']['revision'],[{'type':'create','id':'new-design','kind':'design','data':{'parent_id':'ep','text':'用户新增的设计'}}])
        with self.assertRaises(Conflict):self.queue.finish(task,'agent',[],'沿旧设计完成')


if __name__=='__main__':unittest.main()
