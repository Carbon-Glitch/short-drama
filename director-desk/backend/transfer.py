"""Portable editable projects and history backups, independent of machine runtime."""
from collections import deque
from contextlib import closing
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import sqlite3
import tempfile
from urllib.parse import unquote, urlsplit
from uuid import uuid4
import zipfile

from store import ProjectStore, encoded
from filesystem import io_path, temporary_directory, walk_files
from project_settings import to_config
from documents import render_document, LABELS
from reference_media import render_paths


def digest(path):
    with io_path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def inside(root, relative):
    part = PurePosixPath(relative)
    if part.is_absolute() or '\\' in relative or any(p in ('..', '.') or ':' in p for p in part.parts):
        raise ValueError('项目路径无效：'+relative)
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('项目路径超出范围')
    return path


class References(HTMLParser):
    def __init__(self):
        super().__init__();self.values=[]

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if value and key in ('src', 'href', 'poster'):
                self.values.append(value)
            elif value and key == 'style':
                self.values.extend(re.findall(r'url\([\'"]?([^\)\'"]+)', value))


def dependencies(root, seeds):
    """Resolve actual timeline files recursively; missing local dependencies stop export."""
    pending=deque(seeds);result=set()
    while pending:
        relative=pending.popleft()
        if relative in result:continue
        path=inside(root,relative)
        if not io_path(path).is_file():raise ValueError('项目缺少文件：'+relative)
        result.add(relative)
        values=[]
        if path.suffix.lower() in {'.html','.htm'}:
            content=io_path(path).read_text(encoding='utf-8-sig')
            parser=References();parser.feed(content);values=parser.values
            values.extend(re.findall(r'url\([\'"]?([^\)\'"]+)',content))
        elif path.suffix.lower()=='.css':
            values=re.findall(r'url\([\'"]?([^\)\'"]+)',io_path(path).read_text(encoding='utf-8-sig'))
        for value in values:
            if value.startswith(('#','data:','blob:')):continue
            url=urlsplit(value)
            if url.scheme or url.netloc or value.startswith('/'):
                raise ValueError('请先将剪辑中的外部素材收进项目：'+relative)
            if not url.path:continue
            target=(path.parent/unquote(url.path)).resolve()
            if not target.is_relative_to(root.resolve()):raise ValueError('剪辑引用了项目外文件：'+relative)
            pending.append(target.relative_to(root).as_posix())
    return result


def subset(state, episode):
    if not episode:return state
    entities={e['id']:e for e in state['entities']}
    if episode not in entities or entities[episode]['kind']!='episode':raise ValueError('剧集不存在')
    included={episode}|{e['id'] for e in state['entities'] if e['kind']=='project_settings'}
    while True:
        children={e['id'] for e in entities.values() if e['data'].get('parent_id') in included}
        if children <= included:break
        included.update(children)
    while True:
        before=set(included)
        for dep in state['dependencies']:
            if dep['target'] in included:included.add(dep['source'])
        for identity in list(included):
            data=entities[identity]['data']
            for key in ('references','candidate_media'):
                included.update(v for v in data.get(key,[]) if v in entities)
            for key in ('adopted_media','parent_id'):
                if data.get(key) in entities:included.add(data[key])
        if included==before:break
    return {**state,'entities':[e for e in state['entities'] if e['id'] in included],
            'dependencies':[d for d in state['dependencies'] if d['source'] in included and d['target'] in included]}


def project_markdown(root,state):
    """Readable projections. Unknown imported prose remains available in source documents."""
    root.mkdir(parents=True,exist_ok=True)
    (root/'short-drama.json').write_text(encoded(to_config(state)),encoding='utf8')
    remap={e['data']['path'][7:]:e['data']['path'] for e in state['entities']
           if e['kind']=='media' and e['data']['path'].startswith('source/')}
    def mapped(text):
        for old,new in remap.items():text=text.replace('· '+old+'《','· '+new+'《')
        return text
    for ep in [e for e in state['entities'] if e['kind']=='episode']:
        code=ep['data'].get('code','EP001')
        if not re.fullmatch(r'EP\d+',code):raise ValueError('剧集编号无效')
        folder=root/'剧集'/code;folder.mkdir(parents=True,exist_ok=True)
        scenes=sorted((e for e in state['entities'] if e['kind']=='scene' and e['data'].get('parent_id')==ep['id']),key=lambda e:e['data'].get('order',0))
        script=[f"# {code} {ep['data']['name']}"]
        storyboard=['# 分镜']
        for i,scene in enumerate(scenes):
            scene_code=scene['data'].get('code',f'{code}-SC{i+1:03}')
            script.append(f"## {scene_code} {scene['data']['name']}\n\n{scene['data'].get('text','')}")
            if any(scene['data'].get(key) for key in ('blocking','generation_plan','director_review')):
                plan='## 场景站位 · '+scene_code+'\n\n'+scene['data'].get('blocking','')
                if scene['data'].get('generation_plan'):plan+='\n- 生成安排：'+scene['data']['generation_plan']
                if scene['data'].get('director_review'):plan+='\n- 导演体验审读：'+scene['data']['director_review']
                storyboard.append(plan)
            shots=sorted((e for e in state['entities'] if e['kind']=='shot' and e['data'].get('parent_id')==scene['id']),key=lambda e:e['data'].get('order',0))
            for j,shot in enumerate(shots):
                data=shot['data'];shot_code=data.get('code',f'SHOT-{code}-{i+1:02}-{j+1:03}')
                fields=dict(data.get('fields',{}))
                for key,label in {'action':'唯一动作','duration':'时长','camera':'景别/机位','sound':'声音','start':'起点','end':'终点','purpose':'目的','movement':'运镜','join':'接镜','source_excerpt':'来源','visual_basis':'视觉依据','image_plan':'图片提示词项','production_split':'制作分工'}.items():
                    if key in data:fields[label]=data[key]
                fields['来源']=data.get('source_excerpt') or fields.get('来源') or scene_code
                if data.get('design_refs'):
                    resolved={e['id']:e for e in state['entities']}
                    fields['视觉依据']='《视觉设定.md》·'+'；'.join(LABELS[resolved[i]['kind']]+'「'+resolved[i]['data']['name']+'」' for i in data['design_refs'] if i in resolved and resolved[i]['kind'] in LABELS)
                body=render_paths('\n'.join(f'- {key}：{value}' for key,value in fields.items()),state,shot)
                source=data.get('source_text','')
                prose='\n'.join(line for line in source.splitlines() if not re.match(r'^[-*]\s*[^：:\n]+[：:]',line))
                storyboard.append(f"## {shot_code} · {data['name']}\n{body}\n{prose}")
        (folder/'剧本.md').write_text('\n\n'.join(script)+'\n',encoding='utf8')
        (folder/'分镜.md').write_text(mapped('\n\n'.join(storyboard))+'\n',encoding='utf8')
        for doc in state['entities']:
            if doc['kind']=='document' and doc['data'].get('parent_id')==ep['id'] and doc['data'].get('name') in ('视觉设定.md','图片提示词.md','视频提示词.md'):
                (folder/doc['data']['name']).write_text(mapped(render_document(state,doc)),encoding='utf8')


def export_project(store,destination,mode='editable',episode=None):
    destination=Path(destination).expanduser().resolve()
    if mode not in ('editable','backup'):raise ValueError('导出类型无效')
    if mode=='backup' and episode:raise ValueError('历史备份包含整个项目')
    if destination.exists():raise ValueError('目标文件已存在，请换一个名字')
    if destination.is_relative_to(store.root):raise ValueError('请选择项目之外的导出位置')
    destination.parent.mkdir(parents=True,exist_ok=True)
    with temporary_directory(destination.parent) as temp:
        bundle=Path(temp)/'bundle';dbfile=bundle/'.short-drama/state/project.sqlite';dbfile.parent.mkdir(parents=True)
        with store.connection() as source,closing(sqlite3.connect(dbfile)) as target:source.backup(target)
        copied=ProjectStore(bundle);state=copied.state();states=[state]
        if mode=='editable':
            state=subset(state,episode);states=[state]
            with copied.connection() as db:
                copied._write(db,state)
                for table in ('event','snapshot','draft','undo_stack','redo_stack'):db.execute('DELETE FROM '+table)
                if db.execute("SELECT name FROM sqlite_master WHERE name='agent_task'").fetchone():db.execute('DELETE FROM agent_task')
                if db.execute("SELECT name FROM sqlite_master WHERE name='generation_job'").fetchone():db.execute('DELETE FROM generation_job')
        else:
            with copied.connection() as db:
                for row in db.execute('SELECT before_state,after_state FROM event'):
                    states.extend(json.loads(s) for s in row)
                states.extend(json.loads(row[0]) for row in db.execute('SELECT content FROM snapshot'))
        seeds=set();expected={}
        if mode=='backup':
            with copied.connection() as db:
                if db.execute("SELECT name FROM sqlite_master WHERE name='generation_job'").fetchone():
                    for row in db.execute('SELECT workspace FROM generation_job'):
                        folder=inside(store.root,row[0])
                        if not folder.is_dir():raise ValueError('生产任务的历史文件缺失')
                        seeds.update(p.relative_to(store.root).as_posix() for p in folder.rglob('*') if p.is_file() and not p.name.endswith(('.tmp','.lock')))
        for version in states:
            for entity in version['entities']:
                data=entity['data']
                if entity['kind']=='media':
                    seeds.add(data['path']);expected[data['path']]=data['sha256']
                if entity['kind']=='episode' and data.get('film_path'):
                    seeds.add(data['film_path'])
                    for name in ('project.json','bindings.json'):
                        path=(Path(data['film_path']).parent/'.short-drama'/name).as_posix()
                        if io_path(inside(store.root,path)).is_file():seeds.add(path)
        for relative in dependencies(store.root,seeds):
            source=inside(store.root,relative);target=inside(bundle,relative);io_path(target.parent).mkdir(parents=True,exist_ok=True)
            shutil.copy2(io_path(source),io_path(target))
            if relative in expected and digest(target)!=expected[relative]:raise ValueError('素材版本已变化：'+relative)
        project_markdown(bundle,state)
        manifest={'format':'director-desk','version':1,'mode':mode,'project_id':state['project']['id'],
                  'revision':state['project']['revision'],'files':{}}
        for path in sorted(walk_files(bundle)):
            if io_path(path).is_file():manifest['files'][path.relative_to(bundle).as_posix()]=digest(path)
        (bundle/'manifest.json').write_text(encoded(manifest),encoding='utf8')
        archive=Path(temp)/'project.zip'
        with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as zipped:
            for path in walk_files(bundle):
                if io_path(path).is_file():zipped.write(io_path(path),path.relative_to(bundle).as_posix())
        # Create exclusively: a file created during export is never overwritten.
        with destination.open('xb') as output,archive.open('rb') as source:shutil.copyfileobj(source,output)
    return {'path':str(destination),'mode':mode,'revision':manifest['revision']}


def restore_project(library,archive):
    identity=uuid4().hex;staging=library.projects/(identity+'.restoring')
    staging.mkdir()
    with zipfile.ZipFile(archive) as zipped:
        manifest=json.loads(zipped.read('manifest.json'))
        if manifest.get('format')!='director-desk' or manifest.get('version')!=1:raise ValueError('不支持的项目包')
        names=zipped.namelist()
        expected=set(manifest['files'])|{'manifest.json'}
        if len(names)!=len(set(names)) or set(names)!=expected:raise ValueError('项目包文件清单不一致')
        for name in names:
            target=inside(staging,name);io_path(target.parent).mkdir(parents=True,exist_ok=True)
            with zipped.open(name) as source,io_path(target).open('xb') as output:shutil.copyfileobj(source,output)
            if name!='manifest.json' and digest(target)!=manifest['files'][name]:raise ValueError('项目包文件损坏：'+name)
    restored=ProjectStore(staging)
    state=restored.state();ProjectStore._validate(state)
    with restored.connection() as db:
        if db.execute("SELECT name FROM sqlite_master WHERE name='agent_task'").fetchone():
            db.execute("UPDATE agent_task SET status='failed',worker=NULL,lease_until=NULL,result=? WHERE status IN ('queued','running')", (encoded({'message':'从备份恢复的未完成任务，请按当前内容重试。'}),))
    staging.rename(library.projects/identity)
    return identity
