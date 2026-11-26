import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.request import Request,urlopen
from urllib.error import HTTPError

from library import Library
from server import AppServer


class BrowserImportTests(unittest.TestCase):
    def test_browser_upload_import_and_restore(self):
        with tempfile.TemporaryDirectory() as temp:
            library=Library(Path(temp)/'app');server=AppServer(('127.0.0.1',0),library)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            origin=f'http://127.0.0.1:{server.server_port}'
            def post(path,body=None,raw=None,file=None):
                headers={'X-Director-Session':server.token,'Origin':origin}
                if file:headers['X-File-Path']=file
                data=raw if raw is not None else json.dumps(body).encode()
                with urlopen(Request(origin+'/api'+path,data=data,headers=headers),timeout=10) as response:return json.load(response)
            try:
                batch=post('/uploads',{'kind':'project'})['id']
                post(f'/uploads/{batch}/file',raw='# EP001\n## EP001-SC001 内 · 房间 · 夜\n甲：你好。'.encode(),file='%E5%89%A7%E6%9C%AC.md')
                project=post(f'/uploads/{batch}/finish',{})['id']
                self.assertEqual(len(library.list()),1)
                result=post(f'/projects/{project}/export',{'mode':'backup'})
                with urlopen(origin+result['download']) as response:
                    archive=response.read();self.assertIn('attachment',response.headers['Content-Disposition'])
                batch=post('/uploads',{'kind':'archive'})['id']
                post(f'/uploads/{batch}/file',raw=archive,file='project.zip')
                restored=post(f'/uploads/{batch}/finish',{})['id']
                self.assertEqual(library.project(project).state(),library.project(restored).state())
                self.assertEqual(len(library.list()),2)
            finally:
                server.shutdown();server.server_close();thread.join()


if __name__=='__main__':unittest.main()
