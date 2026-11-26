import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from library import Library


class ImportTests(unittest.TestCase):
    def test_storyboard_scene_and_shot_details_roundtrip(self):
        from transfer import project_markdown
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source=root/'source';ep=source/'剧集/EP001';ep.mkdir(parents=True)
            (ep/'剧本.md').write_text('# EP001\n## EP001-SC001 内 · 客厅 · 夜\n甲：别回头。',encoding='utf8')
            (ep/'分镜.md').write_text('## 场景站位 · EP001-SC001\n甲在门左，乙在门右。\n- 生成安排：全能参考，一次生成。\n保留反应余量。\n- 导演体验审读：保留门外声。\n\n## SHOT-EP001-001 · 回望\n- 来源：EP001-SC001「甲：别回头。」\n- 运镜：缓慢侧移\n- 接镜：切门外反应\n- 起点：低头\n- 终点：回望\n- 视觉依据：冷暖反差\n- 制作分工：后期声桥',encoding='utf8')
            library=Library(root/'library');store=library.project(library.import_project(source))
            out=root/'rendered';out.mkdir();project_markdown(out,store.state())
            restored=library.project(library.import_project(out)).state()
            for kind,keys in [('scene',['blocking','generation_plan','director_review']),('shot',['source_excerpt','movement','join','start','end','visual_basis','production_split'])]:
                before=next(e['data'] for e in store.state()['entities'] if e['kind']==kind)
                after=next(e['data'] for e in restored['entities'] if e['kind']==kind)
                for key in keys:self.assertEqual(before[key],after[key],key)
            self.assertEqual(next(e['data'] for e in restored['entities'] if e['kind']=='scene')['generation_plan'],'全能参考，一次生成。\n保留反应余量。')

    def test_media_versions_adopt_undo_and_file_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            lib = Library(root/'library')
            project = lib.create('版本测试')
            store = lib.project(project)
            scene = next(e for e in store.state()['entities'] if e['kind']=='scene')
            store.apply(1,[{'type':'create','id':'shot','kind':'shot','data':{'parent_id':scene['id']}}])
            first=root/'take.png';first.write_bytes(b'first')
            state=lib.add_media(project,[first],2,'shot')
            a=next(e for e in state['entities'] if e['kind']=='media')
            state=lib.adopt(project,'shot',a['id'],state['project']['revision'])
            first.write_bytes(b'second')
            state=lib.add_media(project,[first],state['project']['revision'],'shot')
            b=next(e for e in state['entities'] if e['kind']=='media' and e['id']!=a['id'])
            state=lib.adopt(project,'shot',b['id'],state['project']['revision'])
            state=store.undo(state['project']['revision'])
            self.assertEqual(next(e for e in state['entities'] if e['id']=='shot')['data']['adopted_media'],a['id'])
            self.assertEqual(lib.file(project,a['id']).read_bytes(),b'first')
            self.assertEqual(lib.file(project,b['id']).read_bytes(),b'second')
            with self.assertRaises(ValueError):
                store.apply(state['project']['revision'],[{'type':'update','id':a['id'],'patch':{'sha256':'replace'}}])
            lib.file(project,a['id']).write_bytes(b'tampered')
            with self.assertRaises(ValueError):lib.file(project,a['id'])

    def test_import_preserves_originals_and_keeps_ids_references_and_unknown_text(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); source=root/'旧项目'; ep=source/'剧集/EP001';ep.mkdir(parents=True)
            (source/'short-drama.json').write_text(json.dumps({'title':'旧项目'}),encoding='utf8')
            (ep/'剧本.md').write_text('# EP001\n## EP001-SC001 内 · 客厅 · 夜\n甲：别回头。',encoding='utf8')
            (ep/'参考.png').write_bytes(b'fixture-image')
            original='## SHOT-EP001-001 · 回望\n- 来源：EP001-SC001\n- 唯一动作：回望\n- 自定义：保留这个字段\n- 输入参考图：REF-A（顺序：1）· 剧集/EP001/参考.png《参考》（用途：身份）\n自由正文'
            (ep/'分镜.md').write_text(original,encoding='utf8')
            library=Library(root/'library');identity=library.import_project(source)
            state=library.project(identity).state();shot=next(e for e in state['entities'] if e['kind']=='shot')
            self.assertEqual(shot['data']['fields']['自定义'],'保留这个字段')
            self.assertIn('自由正文',shot['data']['source_text'])
            self.assertEqual(len(shot['data']['references']),1)
            self.assertEqual(library.file(identity,shot['data']['references'][0]).read_bytes(),b'fixture-image')
            self.assertEqual((ep/'分镜.md').read_text(encoding='utf8'),original)
            self.assertFalse((source/'.short-drama').exists())
            self.assertEqual(library.list()[0]['title'],'旧项目')

    def test_plain_script_is_editable_even_with_empty_episode_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source=root/'原稿';(source/'剧集').mkdir(parents=True)
            original='# 我的故事\n\n清晨。\n甲：等等我。\n\n## 作者备注\n这里留一拍静默。'
            (source/'剧本.md').write_text(original,encoding='utf8')
            library=Library(root/'library');project=library.import_project(source)
            scenes=[e for e in library.project(project).state()['entities'] if e['kind']=='scene']
            self.assertEqual(len(scenes),1);self.assertEqual(scenes[0]['data']['text'],original)
            self.assertEqual((source/'剧本.md').read_text(encoding='utf8'),original)

    def test_unknown_headings_and_preamble_remain_in_editable_scenes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source=root/'原稿';source.mkdir()
            original='# EP001\n先保留这句导演说明。\n## EP001-SC001 内 · 房间 · 日\n甲：等等。\n## 临时补充\n门响了。\n## EP001-SC002 外 · 街边 · 夜\n乙：走吧。'
            (source/'剧本.md').write_text(original,encoding='utf8')
            library=Library(root/'library');project=library.import_project(source)
            scenes=sorted([e for e in library.project(project).state()['entities'] if e['kind']=='scene'],key=lambda e:e['data']['order'])
            self.assertEqual(len(scenes),2)
            self.assertIn('先保留这句导演说明。',scenes[0]['data']['text'])
            self.assertIn('## 临时补充\n门响了。',scenes[0]['data']['text'])
            self.assertEqual(scenes[1]['data']['text'],'乙：走吧。')

    def test_single_script_import_without_renaming(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source=root/'一部手机的独白.txt'
            source.write_text('手机：今天我先休息。',encoding='utf8')
            library=Library(root/'library');project=library.import_script(source)
            state=library.project(project).state()
            self.assertEqual(state['project']['title'],'一部手机的独白')
            self.assertEqual(next(e['data']['text'] for e in state['entities'] if e['kind']=='scene'),'手机：今天我先休息。')
            self.assertEqual(list((library.home/'cache').glob('script-*')),[])

    def test_generation_entries_only_adopt_matching_media_types(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);library=Library(root/'library');project=library.create('采用类型');store=library.project(project)
            image=root/'frame.png';image.write_bytes(b'image');video=root/'take.mp4';video.write_bytes(b'video')
            state=library.add_media(project,[image,video],store.state()['project']['revision'])
            image_id=next(e['id'] for e in state['entities'] if e['kind']=='media' and e['data']['type']=='image')
            video_id=next(e['id'] for e in state['entities'] if e['kind']=='media' and e['data']['type']=='video')
            state=store.apply(state['project']['revision'],[{'type':'create','id':'unit','kind':'submission','data':{}},{'type':'create','id':'picture','kind':'image_prompt','data':{}}])
            with self.assertRaises(ValueError):library.adopt(project,'unit',image_id,state['project']['revision'])
            with self.assertRaises(ValueError):library.adopt(project,'picture',video_id,state['project']['revision'])
            adopted=library.adopt(project,'unit',video_id,state['project']['revision'])
            self.assertEqual(next(e for e in adopted['entities'] if e['id']=='unit')['data']['adopted_media'],video_id)

    def test_asset_adoption_preserves_identity_versions_and_marks_only_related_shot(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);lib=Library(root/'library');pid=lib.create('人物采用');store=lib.project(pid)
            state=store.apply(store.state()['project']['revision'],[{'type':'create','id':'person','kind':'character','data':{'name':'甲'}},
                {'type':'create','id':'related','kind':'shot','data':{'design_refs':['person']}},
                {'type':'create','id':'unrelated','kind':'shot','data':{}}])
            a=root/'a.png';a.write_bytes(b'first');b=root/'b.png';b.write_bytes(b'second')
            state=lib.add_media(pid,[a,b],state['project']['revision'])
            images={e['data']['name']:e['id'] for e in state['entities'] if e['kind']=='media'}
            state=lib.adopt(pid,'person',images['a'],state['project']['revision'])
            store.review('related',state['project']['revision'])
            state=lib.adopt(pid,'person',images['b'],store.state()['project']['revision'])
            self.assertEqual({e['id'] for e in state['entities'] if e['stale']},{'related'})
            person=next(e for e in state['entities'] if e['id']=='person')
            self.assertEqual(person['data']['name'],'甲');self.assertEqual(person['data']['candidate_media'],[images['a'],images['b']])
            state=store.undo(state['project']['revision']);self.assertEqual(next(e for e in state['entities'] if e['id']=='person')['data']['adopted_media'],images['a'])

    def test_add_episode_uses_next_code_and_preserves_existing_content(self):
        with tempfile.TemporaryDirectory() as temp:
            lib=Library(Path(temp)/'library');pid=lib.create('多集');store=lib.project(pid)
            first=next(e for e in store.state()['entities'] if e['kind']=='episode')
            state=store.apply(store.state()['project']['revision'],[{'type':'update','id':first['id'],'patch':{'code':'EP007'}}])
            before={e['id']:e for e in state['entities']}
            result=lib.add_episode(pid,'新的开始',state['project']['revision']);after={e['id']:e for e in result['state']['entities']}
            self.assertEqual(after[result['episode']]['data']['code'],'EP008')
            self.assertTrue(all(after[key]==value for key,value in before.items()))
            self.assertEqual(len([e for e in after.values() if e['data'].get('parent_id')==result['episode']]),1)
            from store import Conflict
            with self.assertRaises(Conflict):lib.add_episode(pid,'不能重复',state['project']['revision'])
            restored=store.undo(result['state']['project']['revision']);self.assertEqual(restored['entities'],state['entities'])

    def test_empty_folder_is_not_imported_as_a_fake_project(self):
        with tempfile.TemporaryDirectory() as temp:
            library=Library(Path(temp)/'library');source=Path(temp)/'empty';source.mkdir()
            with self.assertRaises(ValueError):library.import_project(source)
            self.assertEqual(library.list(),[])


if __name__=='__main__':unittest.main()
