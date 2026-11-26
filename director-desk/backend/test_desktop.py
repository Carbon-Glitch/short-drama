import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from urllib.request import urlopen
from desktop import ensure_service,ensure_frontend,process_alive,running,_CHILDREN

class DesktopTests(unittest.TestCase):
    def test_source_first_launch_builds_interface_without_existing_dist(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'app';(root/'web').mkdir(parents=True);calls=[]
            def run(command,**kwargs):
                calls.append(command)
                if command[-2:]==['run','build']:
                    (root/'web/dist').mkdir();(root/'web/dist/index.html').write_text('ready')
                return SimpleNamespace(returncode=0)
            with patch('desktop.ROOT',root),patch('desktop.EditingRuntime.npm_command',return_value=['node','npm-cli.js']),patch('desktop.subprocess.run',side_effect=run):
                ensure_frontend(Path(tmp)/'home');ensure_frontend(Path(tmp)/'home')
            self.assertEqual([command[2:] for command in calls],[['ci'],['run','build']])
    def stop(self,home):
        record=Path(home)/'desktop-session.json'
        if not record.is_file():return
        pid=json.loads(record.read_text())['pid']
        if process_alive(pid):
            if os.name=='nt':subprocess.run(['taskkill','/PID',str(pid),'/T','/F'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                import signal
                os.kill(pid,signal.SIGTERM)
        for process in _CHILDREN:
            if process.pid==pid:process.wait(timeout=5)

    def test_different_build_restarts_idle_service_and_keeps_library(self):
        from library import Library
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp);ensure_service(home);old=json.loads((home/'desktop-session.json').read_text())['pid']
            pid=Library(home).create('保留作品')
            try:
                with patch('desktop.build_id',return_value='different-build'):
                    url=ensure_service(home)
                record=json.loads((home/'desktop-session.json').read_text())
                self.assertNotEqual(record['pid'],old)
                with urlopen(url+'/api/projects') as response:self.assertEqual(json.load(response)[0]['id'],pid)
                self.assertEqual(ensure_service(home),url)
            finally:self.stop(home)

    def test_upgrade_does_not_interrupt_pending_agent_task(self):
        from library import Library
        from tasks import TaskQueue
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp);url=ensure_service(home);lib=Library(home);store=lib.project(lib.create('等待中'))
            scene=next(e['id'] for e in store.state()['entities'] if e['kind']=='scene')
            queue=TaskQueue(store);queue.create('不要中断',[scene])
            try:
                with patch('desktop.build_id',return_value='different-build'):
                    with self.assertRaisesRegex(RuntimeError,'任务'):ensure_service(home)
                self.assertEqual(running(home),url);self.assertEqual(queue.list()[0]['status'],'queued')
            finally:self.stop(home)

    def test_dynamic_port_reuses_service_and_recovers_dead_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp);process_id=None
            # An obsolete port record must not prevent opening the user's library.
            home.joinpath('desktop-session.json').write_text(json.dumps({'port':1,'instance':'obsolete','pid':0}))
            try:
                url=ensure_service(home)
                record=json.loads((home/'desktop-session.json').read_text())
                process_id=record['pid']
                self.assertTrue(process_alive(process_id))
                self.assertEqual(ensure_service(home),url)
                self.assertEqual(json.loads((home/'desktop-session.json').read_text())['pid'],process_id)
                with urlopen(url) as response:self.assertIn('root',response.read().decode('utf8'))
                with urlopen(url+'/api/projects') as response:self.assertEqual(json.load(response),[])
                self.assertEqual(running(home),url)
            finally:
                if process_id and process_alive(process_id):
                    if os.name=='nt':subprocess.run(['taskkill','/PID',str(process_id),'/T','/F'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
                    else:
                        import signal
                        os.kill(process_id,signal.SIGTERM)
                    for process in _CHILDREN:
                        if process.pid==process_id:process.wait(timeout=5)
    def test_live_pending_start_is_not_duplicated(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp);(home/'desktop-pending.json').write_text(json.dumps({'pid':os.getpid()}))
            with self.assertRaisesRegex(RuntimeError,'仍在启动'):ensure_service(home)

if __name__=='__main__':unittest.main()
