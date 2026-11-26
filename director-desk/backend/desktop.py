"""Desktop startup: one service per library, dynamic port, and reusable healthy sessions."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.request import urlopen,Request
from urllib.error import HTTPError
from app_build import build_id
from editing_runtime import EditingRuntime

ROOT=Path(__file__).resolve().parents[1]
_CHILDREN=[]

def ensure_frontend(home,status=lambda message:None):
    if (ROOT/'web/dist/index.html').is_file():return
    npm=EditingRuntime.npm_command()
    if not npm:raise RuntimeError('首次启动需要 Node.js 和 npm，请安装后重新打开。')
    logs=Path(home)/'logs';logs.mkdir(parents=True,exist_ok=True)
    with (logs/'frontend-build.log').open('ab') as log:
        for args,message in [(['ci'],'首次启动，正在安装界面依赖…'),(['run','build'],'正在准备导演台界面…')]:
            status(message)
            result=subprocess.run([*npm,*args],cwd=ROOT/'web',stdout=log,stderr=log,timeout=600,
                                  creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            if result.returncode:raise RuntimeError('界面准备未完成，请检查网络后重试。详细记录：'+str(logs/'frontend-build.log'))
    if not (ROOT/'web/dist/index.html').is_file():raise RuntimeError('界面构建没有产生入口文件，请检查 frontend-build.log。')

def default_home():
    return Path(os.environ.get('DIRECTOR_DESK_HOME',Path.home()/'.short-drama/director-desk')).resolve()

def running(home):
    try:
        record=json.loads((Path(home)/'desktop-session.json').read_text(encoding='utf8'))
        port=record['port']
        if type(port)!=int or not 0<port<65536:return None
        url=f'http://127.0.0.1:{port}'
        with urlopen(url+'/api/health',timeout=1) as response:health=json.load(response)
        if health.get('app')=='director-desk' and health.get('instance')==record.get('instance'):
            return url
    except (OSError,ValueError,KeyError):pass
    return None

def process_alive(pid):
    if type(pid)!=int or pid<=0:return False
    if os.name=='nt':
        import ctypes
        from ctypes import wintypes
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE
        kernel.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)]
        kernel.CloseHandle.argtypes=[wintypes.HANDLE]
        handle=kernel.OpenProcess(0x1000,False,pid)
        if not handle:return False
        try:
            code=wintypes.DWORD()
            return bool(kernel.GetExitCodeProcess(handle,ctypes.byref(code))) and code.value==259
        finally:kernel.CloseHandle(handle)
    try:os.kill(pid,0);return True
    except OSError:return False

@contextmanager
def startup_lock(home,timeout=45):
    home.mkdir(parents=True,exist_ok=True)
    with (home/'desktop-start.lock').open('a+b') as handle:
        handle.seek(0,2)
        if not handle.tell():handle.write(b'0');handle.flush()
        deadline=time.monotonic()+timeout
        while True:
            try:
                handle.seek(0)
                if os.name=='nt':
                    import msvcrt
                    msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1)
                else:
                    import fcntl
                    fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic()>deadline:raise RuntimeError('另一窗口仍在启动，请稍后重试。')
                time.sleep(.15)
        try:yield
        finally:
            handle.seek(0)
            if os.name=='nt':msvcrt.locking(handle.fileno(),msvcrt.LK_UNLCK,1)
            else:fcntl.flock(handle,fcntl.LOCK_UN)

def ensure_service(home=None,status=lambda message:None):
    home=Path(home or default_home()).resolve()
    with startup_lock(home):
        ensure_frontend(home,status)
        existing=running(home)
        if existing:
            with urlopen(existing+'/api/health',timeout=3) as response:health=json.load(response)
            if health.get('build_id')==build_id(ROOT):return existing
            status('正在切换到当前版本…')
            with urlopen(existing+'/api/session',timeout=3) as response:token=json.load(response)['token']
            request=Request(existing+'/api/shutdown-for-update',data=b'{}',headers={'Origin':existing,'Content-Type':'application/json','X-Director-Session':token})
            try:
                with urlopen(request,timeout=10) as response:json.load(response)
            except HTTPError as error:
                if error.code==404:raise RuntimeError('运行中的早期预览版不支持自动切换，请先关闭旧版服务再打开新版。') from error
                try:message=json.loads(error.read()).get('message')
                except ValueError:message=None
                raise RuntimeError(message or '旧版尚未退出，请稍后重试。') from error
            deadline=time.monotonic()+12
            while running(home) and time.monotonic()<deadline:time.sleep(.2)
            if running(home):raise RuntimeError('旧版仍在保存退出，请稍后再次打开。')
        if not (ROOT/'web/dist/index.html').is_file():
            raise RuntimeError('界面文件尚未准备好，请使用包含 web/dist 的导演台发行包。')
        pending=home/'desktop-pending.json'
        try:pending_pid=json.loads(pending.read_text(encoding='utf8'))['pid']
        except (OSError,ValueError,KeyError):pending_pid=None
        if process_alive(pending_pid):
            raise RuntimeError('导演台仍在启动，请稍后再次打开。')
        status('正在打开作品库…')
        log_dir=home/'logs';log_dir.mkdir(exist_ok=True)
        with (log_dir/'desktop.log').open('ab') as log:
            process=subprocess.Popen([sys.executable,'-X','utf8',str(ROOT/'backend/server.py'),
                '--home',str(home),'--port','0','--desktop'],cwd=ROOT,stdin=subprocess.DEVNULL,
                stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0,
                start_new_session=os.name!='nt')
        _CHILDREN[:]=[child for child in _CHILDREN if child.poll() is None]
        _CHILDREN.append(process)
        pending.write_text(json.dumps({'pid':process.pid}),encoding='utf8')
        deadline=time.monotonic()+30
        while time.monotonic()<deadline:
            url=running(home)
            if url:
                pending.unlink(missing_ok=True)
                return url
            if process.poll() is not None:
                raise RuntimeError('导演台未能启动。详细原因已保存在本机 logs/desktop.log。')
            time.sleep(.2)
        # Do not launch a second process after a slow start; its live handle is authoritative.
        raise RuntimeError('导演台仍在启动，请稍后再次打开；不会重复创建项目。')
