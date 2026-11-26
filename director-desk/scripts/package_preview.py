"""Build a portable Windows preview from the current app and shared Skills."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from filesystem import io_path,walk_files

EXCLUDED={'__pycache__','node_modules','.git','.local','site-packages','test','tests','idlelib','ensurepip','venv','turtledemo'}
def copy_tree(source,target):
    for directory,folders,files in os.walk(source):
        folders[:]=[f for f in folders if f not in EXCLUDED and not (Path(directory)/f).is_symlink()]
        for name in files:
            if name.endswith(('.pyc','.pyo')) or name.startswith('.env'):continue
            path=Path(directory)/name
            if path.is_symlink():continue
            dest=target/path.relative_to(source);io_path(dest.parent).mkdir(parents=True,exist_ok=True)
            shutil.copy2(io_path(path),io_path(dest))

def build(output,python_home,skills):
    output=Path(output).resolve();python_home=Path(python_home).resolve();skills=Path(skills).resolve()
    if output.exists():raise ValueError('输出目录已存在，请指定新目录')
    for path in [ROOT/'web/dist/index.html',python_home/'pythonw.exe',python_home/'LICENSE.txt',skills/'short-drama/SKILL.md']:
        if not path.is_file():raise ValueError('缺少打包输入：'+str(path))
    output.mkdir(parents=True);app=output/'director-desk';app.mkdir()
    copy_tree(ROOT/'backend',app/'backend');copy_tree(ROOT/'web/dist',app/'web/dist')
    if (ROOT/'licenses').is_dir():copy_tree(ROOT/'licenses',app/'licenses')
    for name in ('launch.pyw','Start-Director-Desk.cmd'):shutil.copy2(ROOT/name,app/name)
    runtime=app/'runtime/python';runtime.mkdir(parents=True)
    for path in python_home.iterdir():
        if path.is_file() and (path.suffix in ('.dll','.exe') or path.name=='LICENSE.txt'):shutil.copy2(path,runtime/path.name)
    for name in ('Lib','DLLs','tcl'):copy_tree(python_home/name,runtime/name)
    # Keep the exact shared Skill snapshot; no machine credentials, projects or generated media.
    for path in sorted(skills.glob('short-drama*')):
        if path.is_dir() and (path/'SKILL.md').is_file():copy_tree(path,output/path.name)
    (output/'Start.cmd').write_text('@echo off\r\ncall "%~dp0director-desk\\Start-Director-Desk.cmd"\r\n',encoding='ascii')
    (output/'开始使用.txt').write_text('双击 Start.cmd 打开导演台。作品保存在本机用户目录，不在此程序文件夹内。\n\n已包含 Python、导演台界面与短剧 Skills。视频生成需在本机设置连接服务；自动创作需已登录的 Codex。剪辑环境可在“本机设置 → 剪辑环境”检测；已安装 Node.js 后，可在界面准备 OpenFilm 与渲染浏览器。Node.js、FFmpeg 尚需单独安装，本包不包含这些大型依赖。\n',encoding='utf8')
    files={}
    for path in walk_files(output):
        with io_path(path).open('rb') as stream:files[path.relative_to(output).as_posix()]=hashlib.file_digest(stream,'sha256').hexdigest()
    (output/'manifest.json').write_text(json.dumps({'format':'director-desk-portable-preview','python':sys.version.split()[0],'files':files},ensure_ascii=False,indent=2),encoding='utf8')
    archive=output.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as target:
        for relative in ['manifest.json',*sorted(files)]:
            path=output/relative
            if relative!='manifest.json':
                with io_path(path).open('rb') as stream:
                    if hashlib.file_digest(stream,'sha256').hexdigest()!=files[relative]:raise ValueError('打包期间文件发生变化：'+relative)
            target.write(io_path(path),relative)
    return {'folder':str(output),'archive':str(archive),'files':len(files),'bytes':archive.stat().st_size}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('output');parser.add_argument('--python-home',default=sys.base_prefix);parser.add_argument('--skills',default=str(Path.home()/'.agents/skills'))
    args=parser.parse_args();print(json.dumps(build(args.output,args.python_home,args.skills),ensure_ascii=False))
