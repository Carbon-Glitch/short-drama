"""Loopback-only browser service. Project writes share the Agent command model."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import re
import secrets
import subprocess
import threading
from urllib.parse import urlsplit, unquote

from library import Library
from store import Conflict
from transfer import export_project, restore_project
from transfer import inside
from tasks import TaskQueue
from production import Production
from runtime import Runtime
from agent_worker import AgentWorker
from discovery import Discovery
from editing import Editing
from editing_runtime import EditingRuntime
from prompt_references import PromptReferences
from source_sync import ScriptSync
from video_references import VideoReferences
from project_settings import model_presets,update_specification
from video_coverage import VideoCoverage
from app_build import build_id

WEB = Path(__file__).resolve().parents[1]/"web/dist"
PICKER_LOCK = threading.Lock()


def pick_directory():
    import tkinter as tk
    from tkinter import filedialog
    with PICKER_LOCK:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        try:
            return filedialog.askdirectory(title="选择已有短剧项目")
        finally:
            root.destroy()


def pick_media():
    import tkinter as tk
    from tkinter import filedialog
    with PICKER_LOCK:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        try:
            return list(filedialog.askopenfilenames(title="导入素材", filetypes=[
                ("图片、视频和音频", "*.png *.jpg *.jpeg *.webp *.mp4 *.mov *.webm *.wav *.mp3 *.m4a")]))
        finally:
            root.destroy()


def pick_archive(save=False):
    import tkinter as tk
    from tkinter import filedialog
    with PICKER_LOCK:
        root=tk.Tk();root.withdraw();root.attributes('-topmost',True)
        try:
            if save:return filedialog.asksaveasfilename(title='保存项目包',defaultextension='.zip',filetypes=[('导演台项目包','*.zip')])
            return filedialog.askopenfilename(title='打开项目包',filetypes=[('导演台项目包','*.zip')])
        finally:root.destroy()


class AppServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, library):
        self.library = library
        self.token = secrets.token_urlsafe(32)
        self.instance = secrets.token_hex(16)
        self.build_id=build_id();self.lifecycle_lock=threading.Lock();self.active_writes=0;self.draining=False
        self.downloads = {}
        self.uploads = {}
        self.production = Production(library)
        self.runtime = Runtime(library.home)
        self.discovery = Discovery(library)
        self.editing_runtime = EditingRuntime(library.home)
        self.editing = Editing(library,self.editing_runtime)
        self.references = PromptReferences(library,self.production.tool)
        self.video_references = VideoReferences(library,self.production.tool)
        self.script_sync = ScriptSync(library,self.discovery)
        super().__init__(address, Handler)
        self.agent = AgentWorker(library,self.runtime)
        self.agent.start()

    def server_close(self):
        self.agent.stop()
        super().server_close()


class Handler(BaseHTTPRequestHandler):
    def dispatch(self,writing):
        if not writing:return self._dispatch(False)
        with self.server.lifecycle_lock:
            if self.server.draining:return self.respond(409,{'message':'导演台正在切换版本，请稍后重试。'})
            self.server.active_writes+=1
        try:return self._dispatch(True)
        finally:
            with self.server.lifecycle_lock:self.server.active_writes-=1
    def log_message(self, *_):
        pass

    def respond(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self.dispatch(False)

    def do_POST(self):
        self.dispatch(True)

    def _dispatch(self, writing):
        try:
            host = self.headers.get("Host", "")
            if host not in {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}:
                return self.respond(403, {"message": "仅支持本机访问"})
            path = unquote(urlsplit(self.path).path)
            if writing:
                if self.headers.get("Origin") not in {f"http://{host}", None}:
                    return self.respond(403, {"message": "请求来源不匹配"})
                if self.headers.get("X-Director-Session") != self.server.token:
                    return self.respond(403, {"message": "请刷新导演台后重试"})
                size = int(self.headers.get("Content-Length", "0"))
                upload_match=re.fullmatch(r'/api/uploads/([a-f0-9]{32})/file',path)
                if upload_match:
                    upload=self.server.uploads.get(upload_match[1])
                    if not upload:raise ValueError('导入已过期，请重新选择文件')
                    if size<0 or size>4*1024**3:raise ValueError('单个文件超过4GB，请拆分后导入')
                    relative=unquote(self.headers.get('X-File-Path',''))
                    if not relative:raise ValueError('缺少文件名')
                    target=inside(upload['root'],relative)
                    target.parent.mkdir(parents=True,exist_ok=True)
                    temporary=target.with_name(target.name+'.uploading')
                    remaining=size
                    with temporary.open('wb') as output:
                        while remaining:
                            block=self.rfile.read(min(1024*1024,remaining))
                            if not block:raise ValueError('传输中断，请重新导入')
                            output.write(block);remaining-=len(block)
                    temporary.replace(target)
                    upload['files'].add(relative)
                    return self.respond(200,{'saved':True})
                if size > 4*1024*1024:
                    raise ValueError("内容过大，请分段导入")
                body = json.loads(self.rfile.read(size) or b"{}")
            else:
                body = {}
            lib = self.server.library
            if path=='/api/uploads' and writing:
                from uuid import uuid4
                identity=uuid4().hex
                if body.get('kind') not in ('project','media','archive','script'):raise ValueError('导入类型无效')
                root=lib.home/'cache/uploads'/identity;root.mkdir(parents=True)
                self.server.uploads[identity]={'root':root,'files':set(),'kind':body['kind'],
                    'project':body.get('project'),'shot_id':body.get('shot_id')}
                return self.respond(201,{'id':identity})
            upload_match=re.fullmatch(r'/api/uploads/([a-f0-9]{32})/finish',path)
            if upload_match and writing:
                upload=self.server.uploads.get(upload_match[1])
                if not upload or not upload['files']:raise ValueError('没有可导入的文件')
                if upload['kind']=='project':result={'id':lib.import_project(upload['root'])}
                elif upload['kind']=='script':
                    if len(upload['files'])!=1:raise ValueError('每次选择一份剧本')
                    result={'id':lib.import_script(inside(upload['root'],next(iter(upload['files']))))}
                elif upload['kind']=='archive':
                    if len(upload['files'])!=1:raise ValueError('请选择一个项目包')
                    result={'id':restore_project(lib,inside(upload['root'],next(iter(upload['files']))))}
                else:
                    store=lib.project(upload['project'])
                    result=lib.add_media(upload['project'],[inside(upload['root'],p) for p in sorted(upload['files'])],
                        store.state()['project']['revision'],upload['shot_id'])
                del self.server.uploads[upload_match[1]]
                return self.respond(200,result)
            if path.startswith('/api/downloads/') and not writing:
                download=self.server.downloads.get(path.rsplit('/',1)[-1])
                if not download:raise ValueError('下载已过期，请重新导出')
                return self.stream(download,attachment=True)
            if path == '/api/model-presets' and not writing:
                return self.respond(200,model_presets())
            if path == '/api/editing-runtime':
                return self.respond(200,self.server.editing_runtime.prepare() if writing else self.server.editing_runtime.status())
            if path == '/api/runtime':
                if writing:
                    return self.respond(200,self.server.runtime.save(body))
                return self.respond(200,self.server.runtime.public())
            if path == '/api/health' and not writing:
                return self.respond(200,{'app':'director-desk','instance':self.server.instance,'build_id':self.server.build_id})
            if path=='/api/shutdown-for-update' and writing:
                with self.server.lifecycle_lock:
                    busy=self.server.active_writes>1 or bool(self.server.production.active) or bool(self.server.uploads)
                    busy=busy or bool(self.server.editing_runtime.thread and self.server.editing_runtime.thread.is_alive())
                    for project in lib.list():
                        busy=busy or any(t['status'] in ('queued','running') for t in TaskQueue(lib.project(project['id'])).list())
                        busy=busy or any(j['status'] in ('running','collecting') for j in self.server.production.list(project['id']))
                    if busy:return self.respond(409,{'message':'当前还有任务或编辑正在处理，请完成或取消后再打开新版。'})
                    self.server.draining=True
                self.respond(200,{'stopping':True})
                threading.Thread(target=self.server.shutdown,daemon=True).start()
                return
            if path == "/api/session" and not writing:
                return self.respond(200, {"token": self.server.token})
            if path=='/api/generation-profiles' and not writing:
                return self.respond(200,self.server.production.profiles())
            if path == '/api/discovered-projects' and not writing:
                return self.respond(200,self.server.discovery.list())
            if path == '/api/open-discovered' and writing:
                return self.respond(200,{'id':self.server.discovery.open(body['id'])})
            if path == "/api/projects":
                if writing:
                    return self.respond(201, {"id": lib.create(body.get("title", ""))})
                return self.respond(200, lib.list())
            if path == "/api/import" and writing:
                source = body.get("path") or pick_directory()
                return self.respond(200, {"id": lib.import_project(source)} if source else {"cancelled": True})
            if path == "/api/restore" and writing:
                archive=body.get('path') or pick_archive()
                return self.respond(200,{'id':restore_project(lib,archive)} if archive else {'cancelled':True})
            match = re.fullmatch(r"/api/projects/([a-f0-9]{32})(?:/(.*))?", path)
            if match:
                identity, action = match[1], match[2] or "state"
                store = lib.project(identity)
                if action=='specification' and writing:
                    return self.respond(200,update_specification(store,body['revision'],body['format'],body.get('model')))
                if action=='episode-create' and writing:
                    return self.respond(201,lib.add_episode(identity,body.get('title',''),body['revision']))
                if action=='source-changes' and not writing:
                    return self.respond(200,self.server.script_sync.sources(identity))
                if action=='source-preview' and writing:
                    return self.respond(200,self.server.script_sync.preview(identity,body['document']))
                if action=='source-apply' and writing:
                    return self.respond(200,self.server.script_sync.apply(identity,body['document'],body['revision'],body['source_hash'],body['choices']))
                if action=='video-references' and writing:
                    service=self.server.video_references
                    result=service.update(identity,body['source_id'],body['choices'],body['revision'],body['mode'],body.get('voices',[])) if 'choices' in body else service.describe(identity,body['source_id'])
                    return self.respond(200,result)
                if action=='video-shots' and writing:
                    coverage=VideoCoverage(lib)
                    return self.respond(200,coverage.update(identity,body['source_id'],body['selected'],body['revision']) if 'selected' in body else coverage.describe(identity,body['source_id']))
                if action=='image-references' and writing:
                    result=self.server.references.update(identity,body['source_id'],body['choices'],body['revision']) if 'choices' in body else self.server.references.describe(identity,body['source_id'])
                    return self.respond(200,result)
                if action=='generation-jobs' and not writing:
                    return self.respond(200,self.server.production.list(identity))
                if action=='generation-prepare' and writing:
                    return self.respond(200,self.server.production.prepare(identity,body['source_id'],body['adapter'],body.get('parameters',{})))
                if action=='generation-submit' and writing:
                    return self.respond(200,self.server.production.submit(identity,body['id']))
                if action=='generation-collect' and writing:
                    return self.respond(200,self.server.production.collect(identity,body['id']))
                if action=='tasks':
                    queue=TaskQueue(store)
                    if writing:
                        return self.respond(201,{'id':queue.create(body.get('prompt'),body.get('scope'),body.get('skill',''),body.get('mode','edit'))})
                    return self.respond(200,queue.list())
                if action=='task-retry' and writing:
                    return self.respond(201,{'id':TaskQueue(store).retry(body['id'])})
                if action=='task-cancel' and writing:
                    TaskQueue(store).cancel(body['id'])
                    return self.respond(200,{'cancelled':True})
                if action.startswith("media/") and not writing:
                    return self.stream(lib.file(identity, action[6:]))
                if not writing:
                    if action == "state":
                        return self.respond(200, store.state())
                    if action == "drafts":
                        return self.respond(200, store.drafts("user"))
                revision = body.get("revision")
                if writing and action == "export":
                    token=secrets.token_urlsafe(24)
                    destination=body.get('path') or lib.home/'cache/exports'/(token+'.zip')
                    result=export_project(store,destination,body.get('mode','editable'),body.get('episode'))
                    self.server.downloads[token]=Path(destination)
                    return self.respond(200,{'download':'/api/downloads/'+token,'mode':result['mode'],'revision':result['revision']})
                if writing and action == "apply":
                    return self.respond(200, store.apply(revision, body.get("operations"), "user"))
                if writing and action == "media-import":
                    paths = body.get("paths") or pick_media()
                    return self.respond(200, lib.add_media(identity, paths, revision, body.get("shot_id")))
                if writing and action == "adopt":
                    return self.respond(200, lib.adopt(identity, body["shot_id"], body["media_id"], revision))
                if writing and action == 'editing-plan':
                    return self.respond(200,self.server.editing.plan(identity,body['episode']))
                if writing and action == 'editing-create':
                    return self.respond(200,self.server.editing.create(identity,body['episode'],body['revision']))
                if writing and action == "editor":
                    episode = next((e for e in store.state()["entities"]
                                    if e["id"] == body.get("episode") and e["kind"] == "episode"), None)
                    if not episode or not episode["data"].get("film_path"):
                        raise ValueError("这一集还没有剪辑工程")
                    film = (store.root/episode["data"]["film_path"]).resolve(strict=True)
                    if not film.is_relative_to(store.root):
                        raise ValueError("剪辑工程不在项目中")
                    result = subprocess.run(["node", str(Path(__file__).with_name("openfilm.mjs")), str(film.parent)],
                                            env=self.server.editing_runtime.environment(),
                                            capture_output=True, text=True, encoding="utf8", timeout=60,
                                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
                    if result.returncode:
                        raise ValueError("剪辑台未能打开，请检查本机 OpenFilm 运行时")
                    return self.respond(200, json.loads(result.stdout.strip().splitlines()[-1]))
                if writing and action in {"undo", "redo"}:
                    return self.respond(200, getattr(store, action)(revision))
                if writing and action == "review":
                    return self.respond(200, store.review(body["id"], revision))
                if writing and action == "draft":
                    store.save_draft("user", body["id"], revision, body["content"])
                    return self.respond(200, {"saved": True})
                if writing and action == "draft-clear":
                    store.clear_draft("user", body["id"], body["content"])
                    return self.respond(200, {"saved": True})
            if path.startswith("/api/"):
                return self.respond(404, {"message": "功能不存在"})
            if not writing:
                target = (WEB/path.lstrip("/")).resolve()
                if not target.is_relative_to(WEB.resolve()):
                    raise ValueError("路径无效")
                if not target.is_file():
                    target = WEB/"index.html"
                if target.is_file():
                    return self.stream(target)
            return self.respond(404, {"message": "界面尚未构建"})
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            return
        except Conflict as error:
            self.respond(409, {"message": str(error), "current": error.current})
        except (ValueError, KeyError, TypeError, OSError) as error:
            self.respond(400, {"message": str(error)})
        except Exception:
            self.respond(500, {"message": "操作未完成，已保存的内容不会丢失。"})

    def stream(self, path, attachment=False):
        size = path.stat().st_size
        lo, hi = 0, size-1
        header = self.headers.get("Range")
        if header:
            m = re.fullmatch(r"bytes=(\d*)-(\d*)", header)
            if not m or not (m[1] or m[2]):
                return self.respond(416, {"message": "无效播放范围"})
            if m[1]:
                lo = int(m[1])
                if m[2]:
                    hi = min(hi, int(m[2]))
            else:
                lo = max(0, size-int(m[2]))
            if lo > hi or lo >= size:
                return self.respond(416, {"message": "播放范围超出素材"})
        self.send_response(206 if header else 200)
        mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(max(0, hi-lo+1)))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("X-Content-Type-Options", "nosniff")
        if attachment:self.send_header('Content-Disposition','attachment; filename="director-project.zip"')
        if header:
            self.send_header("Content-Range", f"bytes {lo}-{hi}/{size}")
        self.end_headers()
        with path.open("rb") as stream:
            stream.seek(lo)
            remaining = hi-lo+1
            while remaining > 0:
                block = stream.read(min(65536, remaining))
                if not block:
                    break
                self.wfile.write(block)
                remaining -= len(block)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=4768)
    parser.add_argument("--home")
    parser.add_argument("--desktop",action="store_true")
    args = parser.parse_args()
    server = AppServer(("127.0.0.1", args.port), Library(args.home))
    print(f"导演台 http://127.0.0.1:{server.server_port}", flush=True)
    record=server.library.home/'desktop-session.json'
    if args.desktop:
        temporary=record.with_suffix('.tmp')
        temporary.write_text(json.dumps({'port':server.server_port,'pid':os.getpid(),'instance':server.instance}),encoding='utf8')
        temporary.replace(record)
    try:server.serve_forever()
    finally:
        server.server_close()
        if args.desktop and record.is_file():
            try:
                if json.loads(record.read_text(encoding='utf8')).get('instance')==server.instance:record.unlink()
            except (OSError,ValueError):pass
