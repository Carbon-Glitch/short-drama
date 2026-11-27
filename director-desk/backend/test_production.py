import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from library import Library
from production import Production


class ProductionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name);self.library=Library(root/'library')
        self.project=self.library.create('生产联调');self.store=self.library.project(self.project)
        ep=next(e for e in self.store.state()['entities'] if e['kind']=='episode')
        self.store.apply(1,[{'type':'create','id':'doc','kind':'document','data':{'name':'图片提示词.md','parent_id':ep['id'],'structured':True}},
            {'type':'create','id':'prompt','kind':'image_prompt','data':{'name':'测试图','code':'IMG-TEST','parent_id':ep['id'],'document_id':'doc','text':'- 参考：无\n\n### 可复制提示词\n> 一束窗光落在木桌上。'}}])
        adapter=root/'fixture.py'
        adapter.write_text('''import json,sys,base64
from pathlib import Path
job=json.load(sys.stdin.buffer)
file=Path(job['output_root'])/'output.png'
file.write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j2ioAAAAASUVORK5CYII='))
print(json.dumps({'provider_job_id':'local-contract-fixture','outputs':[{'target':job['outputs'][0],'source':str(file)}]}))
''',encoding='utf8')
        config=root/'adapters.json';config.write_text(json.dumps({'adapters':{'fixture':{'command':[sys.executable,str(adapter)],'timeout_seconds':30}}}),encoding='utf8')
        self.production=Production(self.library,config)

    def test_existing_prepare_confirm_run_protocol_registers_real_output(self):
        prepared=self.production.prepare(self.project,'prompt','fixture',{})
        self.assertEqual(prepared['status'],'prepared')
        result=self.production.submit(self.project,prepared['id'],asynchronous=False)
        self.assertNotIn('error',result,result)
        self.assertEqual(self.production.list(self.project)[0]['status'],'succeeded')
        self.assertTrue(self.library.file(self.project,result['media'][0]).read_bytes().startswith(b'\x89PNG'))
        with self.assertRaises(ValueError):self.production.submit(self.project,prepared['id'],asynchronous=False)

    def test_service_change_after_preview_requires_new_preview(self):
        prepared=self.production.prepare(self.project,'prompt','fixture',{})
        config=json.loads(self.production.config.read_text());config['adapters']['fixture']['timeout_seconds']=45
        self.production.config.write_text(json.dumps(config))
        with self.assertRaisesRegex(ValueError,'配置已改变'):
            self.production.submit(self.project,prepared['id'],asynchronous=False)
        self.assertEqual(self.production.list(self.project)[0]['status'],'prepared')

    def test_confirmed_job_uses_frozen_service_configuration(self):
        prepared=self.production.prepare(self.project,'prompt','fixture',{})
        with patch.object(self.production,'execute',return_value={'status':'deferred'}):
            self.production.submit(self.project,prepared['id'],asynchronous=False)
        self.production.config.write_text(json.dumps({'adapters':{'fixture':{'command':['missing-command']}}}))
        result=self.production.execute(self.project,prepared['id'])
        self.assertNotIn('error',result,result)
        self.assertEqual(self.production.list(self.project)[0]['status'],'succeeded')
        snapshot=self.library.home/'state/service-snapshots'/prepared['id']/'adapters.json'
        self.assertTrue(snapshot.is_file());self.assertFalse(snapshot.is_relative_to(self.store.root))

    def test_modified_source_requires_new_preview(self):
        prepared=self.production.prepare(self.project,'prompt','fixture',{})
        self.store.apply(self.store.state()['project']['revision'],[{'type':'update','id':'prompt','patch':{'text':'改变了'}}])
        with self.assertRaises(ValueError):self.production.submit(self.project,prepared['id'],asynchronous=False)
        self.assertEqual(self.production.list(self.project)[0]['status'],'prepared')

    def test_collect_uses_frozen_design_and_coverage_after_live_edit(self):
        state=self.store.state();ep=next(e for e in state['entities'] if e['kind']=='episode')
        ops=[{'type':'create','id':'scene','kind':'scene','data':{'parent_id':ep['id'],'code':'EP001-SC001'}},
             {'type':'create','id':'visual','kind':'document','data':{'parent_id':ep['id'],'name':'视觉设定.md','structured':True}},
             {'type':'create','id':'design','kind':'design','data':{'parent_id':ep['id'],'document_id':'visual','code':'DESIGN-001','name':'先证据','text':'先见车票再接手'}},
             *[{'type':'create','id':i,'kind':'shot','data':{'parent_id':'scene','design_intent':'DESIGN-001' if i=='a' else ''}} for i in ('a','b')],
             {'type':'update','id':'prompt','patch':{'shot_ids':['a'],'text':'- 设计承接：DESIGN-001\n- 参考：无\n### 可复制提示词\n> A hand passes a ticket.'}},
             {'type':'bind','source':'a','target':'prompt','fields':['action']}]
        self.store.apply(state['project']['revision'],ops)
        prepared=self.production.prepare(self.project,'prompt','fixture',{})
        context_path=self.store.root/prepared['preview']['creative_context']['path']
        frozen=context_path.read_bytes()
        self.assertIn('先见车票再接手',frozen.decode('utf8'))
        with patch.object(self.production,'execute',return_value={'status':'deferred'}):
            self.production.submit(self.project,prepared['id'],asynchronous=False)
        state=self.store.state();self.store.apply(state['project']['revision'],[
            {'type':'update','id':'prompt','patch':{'shot_ids':['b']}},
            {'type':'update','id':'design','patch':{'text':'新决定'}}])
        result=self.production.execute(self.project,prepared['id'])
        self.assertNotIn('error',result,result)
        state=self.store.state();media=next(e for e in state['entities'] if e['id']==result['media'][0])
        self.assertEqual(media['data']['shot_id'],'a')
        self.assertEqual(media['data']['production']['shot_ids'],['a'])
        self.assertEqual(context_path.read_bytes(),frozen)
        with self.assertRaisesRegex(ValueError,'不能覆盖'):
            self.store.apply(state['project']['revision'],[{'type':'update','id':media['id'],'patch':{'production':{}}}])

    def test_missing_explicit_design_is_not_silently_omitted(self):
        state=self.store.state();entry=next(e for e in state['entities'] if e['id']=='prompt')
        self.store.apply(state['project']['revision'],[{'type':'update','id':'prompt','patch':{'text':'- 设计承接：DESIGN-MISSING\n'+entry['data']['text']}}])
        with self.assertRaisesRegex(ValueError,'设计承接未找到'):
            self.production.prepare(self.project,'prompt','fixture',{})
        self.assertEqual(self.production.list(self.project),[])


if __name__=='__main__':unittest.main()
