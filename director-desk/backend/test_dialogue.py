from pathlib import Path
import tempfile
import unittest
from store import ProjectStore

class DialogueTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=ProjectStore.create(Path(self.temp.name)/'project','对白关联')
        self.original='门开了。\n甲：我想留在这里。\n乙：那就别再回头。'
        self.store.apply(0,[{'type':'create','id':'scene','kind':'scene','data':{'name':'场景','text':self.original}},
          {'type':'create','id':'a','kind':'shot','data':{'parent_id':'scene','fields':{'对白':'甲：我想留在这里。'}}},
          {'type':'create','id':'b','kind':'shot','data':{'parent_id':'scene','fields':{'对白':'乙：那就别再回头。'}}},
          {'type':'create','id':'motion-a','kind':'submission','data':{}},
          {'type':'bind','source':'scene','target':'a','fields':['text']},
          {'type':'bind','source':'scene','target':'b','fields':['text']},
          {'type':'bind','source':'a','target':'motion-a','fields':['action']}])
        for identity in ('a','b','motion-a'):
            self.store.review(identity,self.store.state()['project']['revision'])
    def change(self,text):
        return self.store.apply(self.store.state()['project']['revision'],[{'type':'update','id':'scene','patch':{'text':text}}])
    def test_only_the_shot_using_changed_line_becomes_stale(self):
        before=self.store.state();frozen=self.store.freeze('封版')
        old_ids={e['data']['speaker']:e['id'] for e in before['entities'] if e['kind']=='dialogue'}
        after=self.change(self.original.replace('我想留在这里。','我决定留下。'))
        self.assertEqual({e['id'] for e in after['entities'] if e['stale']},{'a','motion-a'})
        self.assertEqual(old_ids,{e['data']['speaker']:e['id'] for e in after['entities'] if e['kind']=='dialogue'})
        self.assertEqual(self.store.snapshot(frozen),before)
        undo=self.store.undo(after['project']['revision']);self.assertEqual(undo['entities'],before['entities'])
    def test_action_change_still_marks_both_shots(self):
        state=self.change(self.original.replace('门开了。','灯突然熄灭。'))
        self.assertTrue({'a','b'}.issubset({e['id'] for e in state['entities'] if e['stale']}))
    def test_unmapped_shot_keeps_broad_dependency(self):
        state=self.store.state();self.store.apply(state['project']['revision'],[{'type':'create','id':'unknown','kind':'shot','data':{'parent_id':'scene'}},{'type':'bind','source':'scene','target':'unknown','fields':['text']}])
        state=self.change(self.original.replace('我想留在这里。','我决定留下。'))
        self.assertTrue(next(e for e in state['entities'] if e['id']=='unknown')['stale'])
    def test_dialogue_projection_cannot_diverge_from_script(self):
        state=self.store.state();line=next(e for e in state['entities'] if e['kind']=='dialogue')
        with self.assertRaises(ValueError):self.store.apply(state['project']['revision'],[{'type':'update','id':line['id'],'patch':{'text':'不应单独改变'}}])
        self.assertEqual(self.store.state(),state)

if __name__=='__main__':unittest.main()
