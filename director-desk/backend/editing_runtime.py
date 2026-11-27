"""Machine-local OpenFilm setup. No runtime files belong in a creative project."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading
import sys

VERSION='0.4.1'

class EditingRuntime:
    def __init__(self,home):
        self.home=Path(home)
        legacy=Path.home()/f'Documents/Codex/tools/short-drama-openfilm-{VERSION}'
        self.root=Path(os.environ.get('SHORT_DRAMA_OPENFILM_HOME') or (legacy if (legacy/'node_modules/openfilm/package.json').is_file() else self.home/'runtimes'/f'openfilm-{VERSION}'))
        self.lock=threading.Lock();self.thread=None;self.phase='idle';self.error=''

    def environment(self):
        return dict(os.environ,SHORT_DRAMA_OPENFILM_HOME=str(self.root),OPENFILM_HOME=str(self.root/'state'))

    def deploy_plugin(self):
        from skill_paths import skills_root
        if not (self.root/'node_modules/openfilm/package.json').is_file():raise ValueError('请先准备剪辑运行环境')
        script=skills_root()/'short-drama-edit/scripts/openfilm_bridge.py'
        result=subprocess.run([sys.executable,str(script),'setup'],env=self.environment(),capture_output=True,
            text=True,encoding='utf8',timeout=60,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        if result.returncode:raise ValueError('剪辑插件更新未完成，请检查本机运行环境')
        return json.loads(result.stdout)

    def status(self):
        components=[]
        for name,label,args in [('node','剪辑运行引擎',['--version']),('ffmpeg','视频处理',['-version']),('ffprobe','素材读取',['-version'])]:
            path=shutil.which(name);version='';ready=False
            if path:
                try:
                    result=subprocess.run([path,*args],capture_output=True,text=True,timeout=5,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
                    version=result.stdout.splitlines()[0] if result.stdout else ''
                    if name!='node':
                        match=re.match(r'\S+ version (\S+)',version)
                        version=match[1] if match else version
                    ready=result.returncode==0
                    if name=='node':
                        match=re.match(r'v(\d+)\.(\d+)',version)
                        ready=ready and bool(match) and tuple(map(int,match.groups()))>=(22,2)
                except (OSError,subprocess.TimeoutExpired):pass
            components.append({'id':name,'label':label,'ready':ready,'version':version[:100]})
        package=self.root/'node_modules/openfilm'
        try:version=json.loads((package/'package.json').read_text(encoding='utf8')).get('version','')
        except (OSError,ValueError):version=''
        installed=version==VERSION and (package/'studio/client.mjs').is_file() and (package/'studio/ui/dist/index.html').is_file()
        components.append({'id':'openfilm','label':'OpenFilm 剪辑台','ready':installed,'version':version})
        return {'components':components,'ready':all(c['ready'] for c in components),'phase':self.phase,'error':self.error,
                'can_prepare':components[0]['ready'] and bool(self.npm_command()),'folder':str(self.root)}

    @staticmethod
    def npm_command():
        node=shutil.which('node');npm=shutil.which('npm.cmd') or shutil.which('npm')
        if not node or not npm:return None
        if Path(npm).suffix.lower()=='.cmd':
            cli=Path(npm).parent/'node_modules/npm/bin/npm-cli.js'
            return [node,str(cli)] if cli.is_file() else None
        return [npm]

    def prepare(self):
        with self.lock:
            if self.thread and self.thread.is_alive():return self.status()
            if not self.status()['can_prepare']:raise ValueError('请先安装 Node.js 22.2 或更新版本，再重新打开导演台')
            self.phase='installing';self.error=''
            self.thread=threading.Thread(target=self._prepare,daemon=True);self.thread.start()
        return self.status()

    def _prepare(self):
        try:
            self.root.mkdir(parents=True,exist_ok=True)
            log=self.home/'logs/editing-setup.log';log.parent.mkdir(parents=True,exist_ok=True)
            with log.open('ab') as output:
                if not next(c for c in self.status()['components'] if c['id']=='openfilm')['ready']:
                    self._run([*self.npm_command(),'install','--prefix',str(self.root),'--save-exact',f'openfilm@{VERSION}','--no-audit','--no-fund'],output)
                self.phase='browser'
                # Use the exact Playwright version installed by OpenFilm, not a second browser installer.
                cli=self.root/'node_modules/playwright-core/cli.js'
                self._run([shutil.which('node'),str(cli),'install','chromium-headless-shell'],output)
            self.phase='complete'
        except Exception:
            self.error='准备未完成，可重试；详细记录在本机 logs/editing-setup.log。';self.phase='failed'

    def _run(self,args,output):
        result=subprocess.run(args,cwd=self.root,env=self.environment(),stdout=output,stderr=output,timeout=1200,
                              creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        if result.returncode:raise ValueError('runtime setup failed')
