import tempfile,unittest
from pathlib import Path
from library import Library
from entries import update_entry
from transfer import project_markdown
from document_contract import SHOT_FIELDS

class StoryboardContractTests(unittest.TestCase):
 def test_full_roundtrip_and_downstream_invalidation(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);source=root/'source';source.mkdir()
   (source/'剧本.md').write_text('## EP001-SC001 内 · 车站 · 夜\n甲：等等。',encoding='utf8')
   (source/'视觉设定.md').write_text('## 人物 · 甲\n灰衣。\n## 场面设计 · EP001-SC001\n先见手指松开再听车门合拢。',encoding='utf8')
   values={key:'内容-'+label for key,label in SHOT_FIELDS.items()}
   values.update(source_excerpt='EP001-SC001',visual_basis='人物「甲」（袖口接冷光、车票由甲右手持有）',action='松手，听者伸手接住。')
   body='## SHOT-001 · 松手\n'+'\n'.join('- '+label+'：'+values[key] for key,label in SHOT_FIELDS.items())+'\n- 作者批注：保留原话\n自由正文也保留。'
   body=body.replace('- 动作与表演：','- 唯一动作：')
   (source/'分镜.md').write_text(body,encoding='utf8')
   (source/'视频提示词.md').write_text('## GROUP-001 · 场面\n- 分镜：SHOT-001\n### 可复制提示词\n> 车票交接。',encoding='utf8')
   lib=Library(root/'library');store=lib.project(lib.import_project(source));state=store.state()
   shot=next(e for e in state['entities'] if e['kind']=='shot');self.assertTrue(shot['data']['design_refs'])
   for key,value in values.items():self.assertEqual(shot['data'][key],value,key)
   state=update_entry(store,'SHOT-001',state['project']['revision'],{'fields':{'听者与反馈':'乙先迟疑再接住。'}})
   self.assertTrue(next(e for e in state['entities'] if e['kind']=='submission')['stale'])
   out=root/'export';out.mkdir();project_markdown(out,state)
   text=(out/'剧集/EP001/分镜.md').read_text(encoding='utf8')
   for fragment in [values['visual_basis'],'作者批注：保留原话','自由正文也保留。']:self.assertIn(fragment,text)
   restored=lib.project(lib.import_project(out)).state();final=next(e for e in restored['entities'] if e['kind']=='shot')['data']
   for key,value in values.items():self.assertEqual(final[key],'乙先迟疑再接住。' if key=='reaction' else value,key)
   self.assertEqual((source/'分镜.md').read_text(encoding='utf8'),body)
if __name__=='__main__':unittest.main()

class DesignDecisionTests(unittest.TestCase):
 def test_stable_decision_reaches_only_consumers_and_unlinks(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);source=root/'source';source.mkdir()
   (source/'剧本.md').write_text('## EP001-SC001 内 · 车站 · 夜\n甲：等等。',encoding='utf8')
   (source/'视觉设定.md').write_text('## DESIGN-EP001-001 · 先证据后反应\n- 场次：EP001-SC001\n车票先可读，乙才伸手。',encoding='utf8')
   (source/'分镜.md').write_text('## SHOT-001 · 车票\n- 来源：EP001-SC001\n- 设计承接：DESIGN-EP001-001，票先可读\n## SHOT-002 · 空镜\n- 来源：EP001-SC001\n- 动作与表演：车灯掠过',encoding='utf8')
   (source/'视频提示词.md').write_text('## GROUP-001 · 接票\n- 分镜：SHOT-001\n> 接票\n## GROUP-002 · 车灯\n- 分镜：SHOT-002\n> 车灯',encoding='utf8')
   lib=Library(root/'library');store=lib.project(lib.import_project(source));state=store.state()
   decision=next(e for e in state['entities'] if e['data'].get('code')=='DESIGN-EP001-001')
   for kind in ('design','scene','shot','submission'):
    for entity in list(state['entities']):
     if entity['kind']==kind and entity['stale']:state=store.review(entity['id'],state['project']['revision'])
   before=state
   state=store.apply(state['project']['revision'],[{'type':'update','id':decision['id'],'patch':{'name':'新名字','text':'车票先翻面，乙看清再接。'}}])
   stale={e['data'].get('code') for e in state['entities'] if e['stale']}
   self.assertIn('SHOT-001',stale);self.assertIn('GROUP-001',stale);self.assertNotIn('SHOT-002',stale);self.assertNotIn('GROUP-002',stale)
   self.assertEqual(next(e for e in before['entities'] if e['id']==decision['id'])['data']['name'],'先证据后反应')
   state=update_entry(store,'SHOT-001',state['project']['revision'],{'fields':{'设计承接':''}})
   shot=next(e for e in state['entities'] if e['data'].get('code')=='SHOT-001')
   self.assertFalse(any(d['source']==decision['id'] and d['target']==shot['id'] for d in state['dependencies']))
