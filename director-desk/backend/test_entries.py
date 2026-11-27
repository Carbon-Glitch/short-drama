import tempfile
import unittest
from pathlib import Path
from library import Library
from entries import read_entry,update_entry
from store import Conflict

class ManagedEntryTests(unittest.TestCase):
 def test_cli_entry_updates_store_and_dependencies_with_undo(self):
  with tempfile.TemporaryDirectory() as temp:
   lib=Library(Path(temp));pid=lib.create('测试');store=lib.project(pid)
   state=store.state();sc=next(e for e in state['entities'] if e['kind']=='scene')
   state=store.apply(state['project']['revision'],[
    {'type':'create','id':'shot','kind':'shot','data':{'parent_id':sc['id'],'code':'SHOT-001','camera':'近景','movement':'固定','name':'等待'}},
    {'type':'create','id':'motion','kind':'submission','data':{'parent_id':sc['data']['parent_id'],'name':'视频'}},
    {'type':'bind','source':'shot','target':'motion','fields':['camera']}])
   info=read_entry(store,'SHOT-001','EP001','分镜.md')
   after=update_entry(store,'SHOT-001',info['revision'],{'fields':{'景别':'特写'}},'EP001','分镜.md')
   shot=next(e for e in after['entities'] if e['id']=='shot')
   self.assertEqual(shot['data']['camera'],'特写');self.assertEqual(shot['data']['movement'],'固定')
   self.assertTrue(next(e for e in after['entities'] if e['id']=='motion')['stale'])
   with self.assertRaises(Conflict):update_entry(store,'SHOT-001',info['revision'],{'fields':{'camera':'全景'}})
   reverted=store.undo(after['project']['revision'])
   self.assertEqual(next(e for e in reverted['entities'] if e['id']=='shot')['data']['camera'],'近景')

if __name__=='__main__':unittest.main()
