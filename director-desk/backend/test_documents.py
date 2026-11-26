from pathlib import Path
import tempfile
import unittest
from store import ProjectStore
from documents import materialize,render_document
from transfer import project_markdown


class DocumentTests(unittest.TestCase):
    def test_repeated_codes_across_episodes_link_only_within_own_episode(self):
        with tempfile.TemporaryDirectory() as temp:
            store=ProjectStore.create(Path(temp)/'p','多集');ops=[]
            for number in (1,2):
                ep=f'ep{number}';scene=f'scene{number}';shot=f'shot{number}'
                ops.extend([{'type':'create','id':ep,'kind':'episode','data':{'name':ep}},
                            {'type':'create','id':scene,'kind':'scene','data':{'name':scene,'parent_id':ep}},
                            {'type':'create','id':shot,'kind':'shot','data':{'name':shot,'parent_id':scene,'code':'SHOT-001','action':'等待'}},
                            {'type':'create','id':f'doc{number}','kind':'document','data':{'name':'视频提示词.md','parent_id':ep,'original':'## MOTION-001 · 段落\n- 分镜：SHOT-001\n> 转身。'}}])
            store.apply(0,ops);state=materialize(store)
            units={e['data']['parent_id']:e for e in state['entities'] if e['kind']=='submission'}
            self.assertEqual(units['ep1']['data']['shot_ids'],['shot1']);self.assertEqual(units['ep2']['data']['shot_ids'],['shot2'])
            for unit in units.values():store.review(unit['id'],store.state()['project']['revision'])
            state=store.apply(store.state()['project']['revision'],[{'type':'update','id':'shot1','patch':{'action':'回头'}}])
            self.assertEqual({e['id'] for e in state['entities'] if e['stale']},{units['ep1']['id']})

    def test_ambiguous_or_missing_shot_code_is_not_guessed(self):
        from documents import link_shots
        state={'entities':[{'id':'scene','kind':'scene','data':{'parent_id':'ep'}},
                           *[{'id':identity,'kind':'shot','data':{'parent_id':'scene','code':'SHOT-001'}} for identity in ('a','b')]]}
        links,unresolved=link_shots(state,'ep',{'SHOT-001','SHOT-404'})
        self.assertEqual(links,[]);self.assertEqual(unresolved,['SHOT-001','SHOT-404'])

    def test_entity_rename_keeps_references_and_content_changes_only_dirty_dependents(self):
        with tempfile.TemporaryDirectory() as temp:
            store=ProjectStore.create(Path(temp)/'p','结构')
            store.apply(0,[
                {'type':'create','id':'ep','kind':'episode','data':{'name':'一','code':'EP001'}},
                {'type':'create','id':'scene','kind':'scene','data':{'parent_id':'ep','name':'内 · 房间 · 夜','text':'你好'}},
                {'type':'create','id':'doc','kind':'document','data':{'parent_id':'ep','name':'视觉设定.md','original':'# 设计\n## 人物 · 林岚\n灰色外套。\n## 地点 · 房间\n清冷窗光。'}},
                {'type':'create','id':'video','kind':'document','data':{'parent_id':'ep','name':'视频提示词.md','original':'# 视频\n## MOTION-EP001-001 · 回望\n- 分镜：SHOT-EP001-001\n> 她回望。'}},
                {'type':'create','id':'shot','kind':'shot','data':{'parent_id':'scene','name':'回望','code':'SHOT-EP001-001','fields':{'视觉依据':'《视觉设定.md》·人物「林岚」'}}},
                {'type':'create','id':'other','kind':'shot','data':{'parent_id':'scene','name':'空镜','code':'SHOT-EP001-002','fields':{}}},
            ])
            state=materialize(store)
            self.assertEqual(materialize(store),state)
            person=next(e for e in state['entities'] if e['kind']=='character')
            submission=next(e for e in state['entities'] if e['kind']=='submission')
            store.review('shot',state['project']['revision']);store.review(submission['id'],store.state()['project']['revision'])
            state=store.apply(store.state()['project']['revision'],[{'type':'update','id':person['id'],'patch':{'name':'林青'}}])
            self.assertFalse(next(e for e in state['entities'] if e['id']=='shot')['stale'])
            self.assertEqual(next(e for e in state['entities'] if e['id']=='shot')['data']['design_refs'],[person['id']])
            visual=next(e for e in state['entities'] if e['id']=='doc')
            self.assertIn('人物 · 林青',render_document(state,visual))
            project_markdown(store.root,state)
            self.assertIn('人物「林青」',(store.root/'剧集/EP001/分镜.md').read_text(encoding='utf8'))
            state=store.apply(state['project']['revision'],[{'type':'update','id':person['id'],'patch':{'text':'红色外套。'}}])
            self.assertEqual({e['id'] for e in state['entities'] if e['stale']},{'shot',submission['id']})
            with self.assertRaises(ValueError):store.apply(state['project']['revision'],[{'type':'update','id':'doc','patch':{'original':'不可覆盖实体'}}])


if __name__=='__main__':unittest.main()
