"""One native OpenFilm runtime and one postproduction route for short-drama."""
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import sys
import hashlib

VERSION = '0.4.1'
HERE = Path(__file__).resolve().parent

def runtime():
    return Path(os.environ.get('SHORT_DRAMA_OPENFILM_HOME', Path.home() / 'Documents/Codex/tools' / ('short-drama-openfilm-' + VERSION)))

def bootstrap():
    home = runtime()
    package = home / 'node_modules/openfilm'
    if not (package / 'package.json').exists():
        npm = shutil.which('npm.cmd') or shutil.which('npm')
        if not npm: raise RuntimeError('Install Node.js with npm before opening the film workspace')
        subprocess.run([npm, 'install', '--prefix', str(home), '--save-exact', 'openfilm@' + VERSION,
                        '--registry=https://registry.npmjs.org', '--ignore-scripts', '--no-audit', '--no-fund'], check=True)
    if json.loads((package / 'package.json').read_text(encoding='utf-8'))['version'] != VERSION:
        raise RuntimeError('Unexpected OpenFilm version in isolated runtime')
    target = package / 'plugins/short-drama'
    target.mkdir(parents=True, exist_ok=True)
    changed = []
    envelope=HERE.parents[1]/'hypit/scripts/music_envelope.py'
    if not envelope.is_file():envelope=HERE/'openfilm/music_envelope.py'
    for source in [*(HERE.parent / 'assets/openfilm-plugin').iterdir(), HERE / 'openfilm/core.mjs', HERE / 'openfilm/audio.mjs', HERE / 'openfilm/handoff.mjs', HERE / 'openfilm/duck_plan.py', envelope]:
        if source.is_file():
            dest = target / source.name
            if not dest.exists() or dest.read_bytes() != source.read_bytes():
                shutil.copy2(source, dest); changed.append(source.name)
    prefs = home / 'state/prefs.json'; prefs.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(prefs.read_text(encoding='utf-8')) if prefs.exists() else {'language':'zh-CN'}
    data.setdefault('plugins', {})['short-drama'] = True
    prefs.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    build=hashlib.sha256(b''.join((target/name).read_bytes() for name in ('server.mjs','core.mjs','audio.mjs','handoff.mjs','duck_plan.py','music_envelope.py'))).hexdigest()
    loaded_path=home/'state/short-drama-loaded.json';run_path=home/'state/run.json'
    loaded=json.loads(loaded_path.read_text(encoding='utf-8')) if loaded_path.exists() else {}
    running=json.loads(run_path.read_text(encoding='utf-8')) if run_path.exists() else {}
    return {'runtime': str(home), 'version': VERSION, 'deployed': changed,
            'restartStudioIfRunning': bool(running) and (loaded.get('build')!=build or loaded.get('pid')!=running.get('pid'))}

def run(command, root, *, payload=None, out=None, preview=False):
    deployment=bootstrap()
    node = shutil.which('node')
    if not node: raise RuntimeError('Node.js is required')
    args = [node, str(HERE / 'openfilm/cli.mjs'), command, '--root', str(Path(root).resolve())]
    if payload: args += ['--input', str(payload)]
    if out: args += ['--out', str(out)]
    if preview: args += ['--preview']
    result = subprocess.run(args, capture_output=True, encoding='utf-8', errors='replace')
    if result.returncode: raise RuntimeError(result.stderr.strip() or result.stdout)
    lines = result.stdout.splitlines()
    for line in reversed(lines):
        if line.startswith('SHORT_DRAMA_RESULT='):
            value=json.loads(line.split('=',1)[1])
            if deployment['restartStudioIfRunning']:
                value['runtimeRestartRequired']=True
                value['runtimeMessage']='保存当前编辑并重启专用 Studio，使界面与 CLI 使用同一版后端'
            return value
    raise RuntimeError('OpenFilm did not return an execution result')

def main():
    if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['setup','init','state','check','sync','patch','import-asset','replace-source','handoff','bind-handoff','open','render','verify'])
    p.add_argument('root', nargs='?', default='.')
    p.add_argument('--input'); p.add_argument('--out'); p.add_argument('--preview', action='store_true')
    a = p.parse_args()
    result = bootstrap() if a.command == 'setup' else run(a.command, a.root, payload=a.input, out=a.out, preview=a.preview)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__': main()
