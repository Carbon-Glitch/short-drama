import json
import os
from pathlib import Path
import tempfile
import unittest
import zipfile

from library import Library
from filesystem import io_path, temporary_directory
from tasks import TaskQueue
from transfer import export_project,restore_project


class TransferTests(unittest.TestCase):
    def test_backup_restore_history_drafts_and_bytes_without_cache(self):
        with temporary_directory() as temp:
            root=Path(temp);library=Library(root/'a');identity=library.create('可搬迁作品');store=library.project(identity)
            scene=next(e for e in store.state()['entities'] if e['kind']=='scene')
            image=root/'image.png';image.write_bytes(b'image-version')
            state=library.add_media(identity,[image],1)
            media=next(e for e in state['entities'] if e['kind']=='media')
            store.save_draft('user',scene['id'],2,{'text':'草稿'})
            frozen=store.freeze('历史版本')
            original_snapshot=store.snapshot(frozen)
            state=store.apply(2,[{'type':'update','id':scene['id'],'patch':{'text':'当前内容'}}])
            cache=store.root/'.short-drama/cache/private.tmp';cache.parent.mkdir();cache.write_text('not exported')
            archive=root/'backup.zip';export_project(store,archive,mode='backup')
            other=Library(root/'another-machine');restored=other.project(restore_project(other,archive))
            self.assertEqual(restored.snapshot(frozen),original_snapshot)
            self.assertEqual(restored.drafts('user')[0]['content'],{'text':'草稿'})
            self.assertEqual((restored.root/media['data']['path']).read_bytes(),b'image-version')
            self.assertFalse((restored.root/'.short-drama/cache').exists())
            restored.undo(state['project']['revision'])
            self.assertEqual(next(e for e in restored.state()['entities'] if e['id']==scene['id'])['data']['text'],'')

    def test_editable_episode_export_includes_timeline_dependency_closure(self):
        with temporary_directory() as temp:
            root=Path(temp);library=Library(root/'a');identity=library.create('单集');store=library.project(identity)
            ep=next(e for e in store.state()['entities'] if e['kind']=='episode')
            folder=store.root/'source/剧集/EP001';folder.mkdir(parents=True)
            (folder/'film.html').write_text('<iframe src="scenes/title.html"></iframe>',encoding='utf8')
            (folder/'scenes').mkdir();(folder/'scenes/title.html').write_text('<img src="../shared.png">',encoding='utf8')
            (folder/'shared.png').write_bytes(b'shared')
            store.apply(1,[{'type':'update','id':ep['id'],'patch':{'film_path':'source/剧集/EP001/film.html'}},
                           {'type':'create','id':'ep2','kind':'episode','data':{'name':'不要带走','code':'EP002'}}])
            archive=root/'single.zip';export_project(store,archive,episode=ep['id'])
            other=Library(root/'b');restored=other.project(restore_project(other,archive))
            self.assertFalse(any(e['id']=='ep2' for e in restored.state()['entities']))
            self.assertEqual((restored.root/'source/剧集/EP001/shared.png').read_bytes(),b'shared')
            self.assertTrue((restored.root/'剧集/EP001/剧本.md').is_file())
            with restored.connection() as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM event').fetchone()[0],0)

    @unittest.skipUnless(os.name=='nt','Windows long paths')
    def test_restore_long_timeline_path_and_no_auto_replay(self):
        with temporary_directory() as temp:
            root=Path(temp);library=Library(root/'a');pid=library.create('长路径');store=library.project(pid)
            state=store.state();ep=next(e for e in state['entities'] if e['kind']=='episode');scene=next(e for e in state['entities'] if e['kind']=='scene')
            relative='editing/'+('nested-'*15)+'/assets/'+('video-'*15)+'.mp4'
            target=store.root/relative;io_path(target.parent).mkdir(parents=True)
            io_path(target).write_bytes(b'video bytes')
            film=store.root/'film.html';film.write_text('<video src="'+relative+'"></video>')
            store.apply(state['project']['revision'],[{'type':'update','id':ep['id'],'patch':{'film_path':'film.html'}}])
            TaskQueue(store).create('不要自动重放',[scene['id']])
            archive=root/'project.zip';export_project(store,archive,'backup')
            other=Library(root/('deeper-'*8));restored=other.project(restore_project(other,archive))
            self.assertGreater(len(str(restored.root/relative)),260)
            self.assertEqual(io_path(restored.root/relative).read_bytes(),b'video bytes')
            self.assertEqual(TaskQueue(restored).list()[0]['status'],'failed')

    def test_missing_timeline_file_blocks_export_without_partial_destination(self):
        with temporary_directory() as temp:
            root=Path(temp);lib=Library(root/'a');pid=lib.create('缺失');store=lib.project(pid)
            ep=next(e for e in store.state()['entities'] if e['kind']=='episode')
            (store.root/'film.html').write_text('<video src="missing.mp4"></video>')
            store.apply(1,[{'type':'update','id':ep['id'],'patch':{'film_path':'film.html'}}])
            with self.assertRaises(ValueError):export_project(store,root/'bad.zip')
            self.assertFalse((root/'bad.zip').exists())


if __name__=='__main__':unittest.main()
