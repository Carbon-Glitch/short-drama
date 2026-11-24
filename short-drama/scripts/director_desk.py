"""Read a director's projection; persist only human decisions and their pinned evidence."""
from contextlib import closing
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote
from hashlib import sha256
from tempfile import NamedTemporaryFile
import json, os, re, shutil, sqlite3, sys, time, uuid
import creator_views as views

DOCS=['剧本.md','视觉设定.md','分镜.md','图片提示词.md','视频提示词.md']
STAGES=['开发','剧本','Design','分镜','资产','投产','回片','剪辑','交付']
MEDIA={'.png':'image','.jpg':'image','.jpeg':'image','.webp':'image','.wav':'audio','.mp3':'audio','.m4a':'audio','.mp4':'video','.mov':'video','.webm':'video','.srt':'caption','.vtt':'caption'}
def digest(b):return sha256(b).hexdigest()
def text(p):return p.read_text(encoding='utf-8-sig') if p.is_file() else ''
def data(p,default):
    return json.loads(text(p)) if p.is_file() else default
def inside(root,p):
    if p.is_symlink() or not p.resolve().is_relative_to(root.resolve()):raise ValueError('路径不属于当前项目')
    return p
def project(ep):
    if ep.parent.name in ('剧集','episodes'):return ep.parent.parent
    return ep
def rel(root,p):return p.relative_to(root).as_posix()
def episodes(base):
    if base.parent.name in ('剧集','episodes'):base=base.parent.parent
    for folder in ('剧集','episodes'):
        q=base/folder
        if q.is_dir():return [p for p in sorted(q.iterdir()) if not p.is_symlink() and p.is_dir() and not p.name.startswith('.')] or [base]
    return [base]
def sections(s):
    parts=re.split(r'(?m)^##\s+',s)
    return [dict(title=z.partition('\n')[0].strip(),body=z.partition('\n')[2].strip()) for z in parts[1:]]
def store(ep,write=False):
    p=inside(ep,ep/'.short-drama/director.sqlite')
    if not write and not p.exists():return {}
    if write:p.parent.mkdir(exist_ok=True)
    with closing(sqlite3.connect(p)) as c, c:
        if write:c.execute('create table if not exists item (key text primary key, value text not null)')
        return {k:json.loads(v) for k,v in c.execute('select key,value from item')}
def put(ep,k,v):
    store(ep,True)
    with closing(sqlite3.connect(inside(ep,ep/'.short-drama/director.sqlite'))) as c, c:
        c.execute('insert or replace into item values (?,?)',(k,json.dumps(v,ensure_ascii=False)))
def media_id(root,p):
    st=p.stat()
    return digest((rel(root,p)+'|'+str(st.st_size)+'|'+str(st.st_mtime_ns)).encode())[:32]
def stage_files(ep):
    root=project(ep); names={s:[] for s in STAGES};m={}
    def add(p,s):
        if not p.is_file() or not p.resolve().is_relative_to(root.resolve()) or p.is_symlink():return
        suffix=p.suffix.lower()
        if suffix not in MEDIA:return
        k=rel(root,p)
        if k in m:return
        v=media_id(root,p);m[k]=dict(path=k,id=v,kind=MEDIA[suffix],name=p.name,stage=s);names[s].append((k,v))
    def tree(q):
        if not q.is_dir():return []
        return [p for p in q.rglob('*') if not any(x.startswith('.') for x in p.relative_to(q).parts)]
    for p in tree(ep/'制作成果')+tree(ep/'assets')+tree(root/'输入')+tree(root/'系列资产'):
        add(p,'交付' if '成片' in p.parts else '回片' if MEDIA.get(p.suffix.lower())=='video' else '资产')
    for p in ep.iterdir():
        if p.is_file():add(p,'交付' if MEDIA.get(p.suffix.lower())=='video' else '资产')
    # Include nonstandard agent output folders without inventing a shot association.
    for parent,dirs,files in os.walk(ep,followlinks=False):
        dirs[:]=[n for n in dirs if not n.startswith('.') and n not in ('node_modules','__pycache__','cache','制作运行','剧集','episodes') and not (Path(parent)/n).is_symlink()]
        for n in files:
            f=Path(parent)/n
            if f.suffix.lower() in MEDIA:add(f,'交付' if '成片' in f.parts else '回片' if MEDIA[f.suffix.lower()]=='video' else '资产')
    for n in DOCS:
        z=text(inside(ep,ep/n))
        for path in re.findall(r'·\s*([^；\n《》]+?\.(?:png|webp|jpe?g|wav|mp3|mp4|m4a))《',z,flags=re.I):
            path=path.strip()
            if Path(path).is_absolute() or '..' in Path(path).parts:continue
            for entry in (root/path,ep/path):
                if entry.is_file():add(entry,'资产');break
    return names,m
class Film(HTMLParser):
    def __init__(self):super().__init__();self.clips=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag not in ('video','audio','img','iframe') or not a.get('src'):return
        src,_,t=a['src'].partition('#t=')
        try:
            start=float(a.get('at',0));speed=float(a.get('speed',1));parts=t.split(',');offset=float(parts[0] or 0)
            end=start+(float(parts[1])-offset)/speed if len(parts)>1 and speed>0 else start+float(a['duration']) if 'duration' in a else None
        except (ValueError,KeyError,ZeroDivisionError):return
        self.clips.append(dict(id=a.get('id'),src=unquote(src),start=start,end=end,offset=offset,speed=speed,shot=a.get('data-shot-id'),motion=a.get('data-motion-id'),kind=tag))
def evidence(ep):
    root=project(ep); stages,m=stage_files(ep);docs={}
    for s,n in zip(['剧本','Design','分镜','资产','投产'],DOCS):
        p=inside(ep,ep/n)
        if p.is_file():
            b=p.read_bytes();v=digest(b);z=b.decode('utf-8-sig').replace('\r\n','\n');docs[n]=dict(name=n,rev=v,text=z,sections=sections(z));stages[s].append((n,v if s!='Design' else digest(re.sub(r'^## 资产实现[^\n]*\n.*?(?=^## |\Z)','',z,flags=re.M|re.S).strip().encode())))
            if s=='Design' and '## 资产实现' in z:stages['资产'].append(('资产实现',digest(z.partition('## 资产实现')[2].encode())))
    extra=[]
    for p in list((root/'项目开发').glob('**/*.md'))+list(ep.glob('*提示词*.txt'))+list(ep.glob('*.srt'))+list((root/'输入').glob('*.md'))+list((root/'输入').glob('*.txt')):
        if p.stat().st_size>2_000_000:continue
        z=text(inside(root,p));stage='开发' if '项目开发' in p.parts else '剧本' if '输入' in p.parts else '交付' if p.suffix=='.srt' else '投产'
        extra.append(dict(path=rel(root,p),stage=stage,text=z));stages[stage].append((rel(root,p),digest(z.encode())))
    for directory,stage in [(ep/'审查','回片'),(ep/'审阅','回片'),(ep/'制作成果/运行记录','回片')]:
        for p in sorted(directory.glob('*.md')):
            if p.stat().st_size<1_000_000:
                z=text(inside(root,p));extra.append(dict(path=rel(root,p),stage=stage,text=z));stages[stage].append((rel(root,p),digest(z.encode())))
    cutlist=inside(ep,ep/'剪辑单.md')
    if cutlist.is_file():extra.append(dict(path=rel(root,cutlist),stage='剪辑',text=text(cutlist)))
    film=Film(); ft=text(inside(ep,ep/'film.html'));film.feed(ft)
    if ft:stages['剪辑'].append(('film.html',digest(ft.encode())))
    for c in film.clips:
        path=(ep/c['src']).resolve()
        c['media']=rel(root,path) if path.is_relative_to(root) else None
        if c['media'] in m:m[c['media']]['used']=True
    jobs=[]; prod=root/'.short-drama/production'
    for p in sorted((prod/'jobs').glob('*.json')):
        j=data(inside(root,p),{}); prefix=rel(root,ep)+'/' if ep!=root else ''
        if prefix and not any(str(x).startswith(prefix) for x in [j.get('source',''),*j.get('outputs',[])]):continue
        runs=[data(inside(root,q),{}) for q in sorted((prod/'runs'/p.stem).glob('*.json'))]
        jobs.append(dict(id=j.get('job_id',p.stem),entry=j.get('source_entry'),source=j.get('source'),prompt=j.get('prompt'),refs=j.get('reference_bindings',[]),outputs=j.get('outputs',[]),params=j.get('parameters',{}),status=runs[-1].get('status') if runs else 'prepared',runs=[{k:v.get(k) for k in ('run_id','status','started_at','finished_at')} for v in runs]))
        src=j.get('source');expected=(j.get('inputs') or {}).get(src) if src else None
        if expected and src:
            q=(root/src).resolve();jobs[-1]['sourceState']='原工作稿一致' if q.is_relative_to(root) and q.is_file() and digest(q.read_bytes())==expected else '来源工作稿已变化'
        stages['投产'].append((p.stem,str(j.get('fingerprint') or digest(p.read_bytes()))))
    # Historical adapter previews: only explicitly recorded node inputs, never infer a SHOT from its filename.
    work=root/'制作运行'
    if len(episodes(root))==1:
        uploads=data(inside(root,work/'uploads.json'),{});by={v:k for k,v in uploads.items() if isinstance(v,str)}
        for p in sorted(work.glob('preview-*.json')):
            j=data(inside(root,p),{});nodes=j.get('nodeInfoList',[])
            if not isinstance(nodes,list):continue
            fields=[dict(slot=str(n.get('nodeId')),type=n.get('fieldName'),value=by.get(str(n.get('fieldValue')),str(n.get('fieldValue','')))) for n in nodes if n.get('fieldName') in ('text','image','audio','video','aspect_ratio','value','seed','megapixels') and n.get('fieldValue') not in ('','None',None)]
            record=data(inside(root,work/p.name.replace('preview-','job-')),{});jobs.append(dict(id=p.stem,entry=None,status='有任务回执' if record.get('taskId') else '有输入预览',workflow=j.get('workflowId'),fields=fields,prompt=next((x['value'] for x in fields if x['type']=='text'),''),refs=[x for x in fields if x['type'] in ('image','audio','video')],outputs=[]));stages['投产'].append((p.name,digest(p.read_bytes())))
    view=views.read_episode(ep.name,{n:d['text'] for n,d in docs.items()},None)
    def normalized(z):return str(z).replace('\r\n','\n').strip()
    for j in jobs:
        if not j.get('entry'):
            opts=[v['id'] for v in view.get('videoPrompts') or [] if normalized(v.get('prompt'))==normalized(j.get('prompt')) and j.get('prompt')]
            if len(opts)==1:j['matchedEntry']=opts[0]
        for ref in j.get('refs') or []:
            if not isinstance(ref,dict):continue
            path=ref.get('path') or ref.get('value')
            cand=[x for x in m.values() if x['path']==path or x['name']==path]
            if len(cand)==1:ref['mediaId']=cand[0]['id']
    receipt=data(inside(ep,ep/'.short-drama/render-result.json'),{})
    frev=digest((ep/'film.html').read_bytes())[:16] if ft else None
    receipt['timelineCurrent']=bool(frev and receipt.get('filmRevision')==frev)
    rp=Path(receipt.get('output') or ''); rh=receipt.get('outputHash')
    if rp.is_file() and rp.resolve().is_relative_to(ep) and rel(root,rp) in m and rh:
        m[rel(root,rp)]['exportCandidate']=True
    stamps={s:digest(json.dumps(sorted(v),ensure_ascii=False).encode()) for s,v in stages.items()}
    # A director's pass is for the precise upstream versions seen, not just the stage's own files.
    revs={s:digest(''.join(stamps[t] for t in STAGES[:i+1]).encode()) for i,s in enumerate(STAGES)}
    differences={}
    target=docs.get(DOCS[0],{}).get('text','')
    if target:
        from difflib import unified_diff
        for x in extra:
            if x['stage']=='剧本':
                differences[x['path']]='\n'.join(unified_diff(x['text'].splitlines(),target.splitlines(),fromfile=x['path'],tofile=DOCS[0],lineterm=''))
    design=data(inside(ep,ep/'.short-drama/design-pass.json'),{})
    source_digest=(design.get('inputs') or {}).get('screenplay')
    design_status='未登记版本' if not source_digest else '剧本来源一致' if source_digest==digest(text(inside(ep,ep/DOCS[0])).encode()) else '设计引用的剧本已更新'
    return dict(designSource=design_status,fps=data(inside(ep,ep/'.short-drama/project.json'),{}).get('fps'),differences=differences,title=view.get('title') if DOCS[0] in docs else ep.name,docs=docs,extra=extra,parsed=view,media=list(m.values()),clips=film.clips,jobs=jobs,stages={s:dict(count=len(v),rev=revs[s]) for s,v in stages.items()},hasFilm=bool(ft),render={k:receipt.get(k) for k in ('filmRevision','outputHash','artisticAccepted','timelineCurrent') if k in receipt},external=not docs and not ft)
def manifest(ep):
    d=evidence(ep);root=project(ep); epcfg=data(inside(root,root/'short-drama.json'),{});profile=epcfg.get('creator_authority',{}).get('production_profile',{});d['productionProfile']=profile if isinstance(profile,str) else {k:v for k,v in (profile or {}).items() if k in ('video_model','model','name','video','provider') and isinstance(v,str)} if isinstance(profile,dict) else None
    d['decisions']=store(ep);d['episode']=ep.name;d['episodes']=[p.name for p in episodes(ep)];d['project']=project(ep).name
    return d
def blocked(ep,target):
    state=store(ep)
    if state:
        for k,v in state.items():
            if k.startswith('lock:') and v and k[5:] in DOCS and digest((ep/k[5:]).read_bytes())!=v:return '锁定工作稿已变化：'+k[5:]
            if k.startswith('line:') and v and v not in text(ep/DOCS[0]):return '锁定原句已变化'
    target=STAGES.index(target)
    keys=[s for s in STAGES[:target] if state.get('hold:'+s)]
    if keys:
        ev=evidence(ep)
        for s in keys:
            if state.get('pass:'+s)!=ev['stages'][s]['rev']:return s
    return None
def gate_job(root,job):
    src=job.get('source') or next(iter(job.get('outputs',[])),'')
    parts=Path(src).parts;ep=root/parts[0]/parts[1] if len(parts)>2 and parts[0] in ('剧集','episodes') else root
    # A configured review hold allows one pilot and blocks the next submission before consumption.
    st=blocked(ep,'回片' if job.get('modality')=='video' else '资产')
    decisions=store(ep)
    if not st and job.get('modality')=='video' and decisions.get('hold:回片'):
        active_before=False
        prod=root/'.short-drama/production'
        for other in (prod/'jobs').glob('*.json'):
            j=data(other,{})
            if j.get('modality')=='video' and j.get('job_id')!=job.get('job_id') and (project(ep)==ep or str(j.get('source') or '').startswith(rel(root,ep)+'/')):
                if any((prod/'runs'/other.stem).glob('*.json')):active_before=True;break
        if active_before or any(x['kind']=='video' for x in stage_files(ep)[1].values() if x['stage']=='回片'):
            st=blocked(ep,'剪辑')
    if st:raise ValueError('导演台等待确认：'+st)
def pin(ep,root,asset):
    p=inside(root,root/asset['path']);dest=inside(ep,ep/'.short-drama/director-media'/ (asset['id']+p.suffix.lower()))
    dest.parent.mkdir(parents=True,exist_ok=True)
    if not dest.exists():
        with NamedTemporaryFile(dir=dest.parent,delete=False) as t:tmp=Path(t.name)
        try:
            shutil.copyfile(p,tmp)
            if media_id(root,p)!=asset['id']:raise ValueError('素材已改变，刷新后重试')
            os.replace(tmp,dest)
        finally:tmp.unlink(missing_ok=True)
def slot_targets(ev,slot):
    if not re.fullmatch(r'REF-[A-Za-z0-9-]+',slot):return []
    pattern=re.compile(re.escape(slot)+r'（顺序：[1-9]\d*）\s*·\s*([^；\n《》]+?)《')
    return [(n,d,pattern) for n,d in ev['docs'].items() if n in DOCS[1:] and pattern.search(d['text'])]
def action(ep,a):
    ev=evidence(ep);s=a.get('stage');kind=a.get('type')
    if kind=='protect-line':
        line=str(a.get('line','')).strip()
        if not line or (a.get('enabled') and line not in ev['docs'].get(DOCS[0],{}).get('text','')) or len(line)>1500:raise ValueError('请从本版剧本原文选择要保留的句子')
        put(ep,'line:'+digest(line.encode()),line if a.get('enabled') else None)
        return store(ep)
    if s not in STAGES:raise ValueError('阶段无效')
    if kind=='hold':put(ep,'hold:'+s,a.get('enabled') is True)
    elif kind=='pass':
        if a.get('rev')!=ev['stages'][s]['rev'] or not ev['stages'][s]['count']:raise ValueError('产物为空或版本已变化，请刷新')
        put(ep,'pass:'+s,a['rev'])
    elif kind=='lock':
        n=a.get('name')
        if n not in ev['docs'] or ev['docs'][n]['rev']!=a.get('rev'):raise ValueError('工作稿版本已变化')
        put(ep,'lock:'+n,a['rev'] if a.get('enabled') else None)
    elif kind=='bind':
        slot=a.get('slot','');asset=next((x for x in ev['media'] if x['id']==a.get('media')),None)
        targets=slot_targets(ev,slot);revs=a.get('revs',{});dec=store(ep)
        if not asset or not targets:raise ValueError('参考槽或媒体不存在')
        for n,d,pattern in targets:
            if dec.get('lock:'+n):raise ValueError('请先解锁 '+n)
            if revs.get(n)!=d['rev']:raise ValueError('文档已更新，请刷新')
            if any(MEDIA.get(Path(old.strip()).suffix.lower())!=asset['kind'] for old in pattern.findall(d['text'])):raise ValueError('媒体类型不同')
        pin(ep,project(ep),asset)
        for n,d,pattern in targets:
            f=inside(ep,ep/n);old=f.read_bytes()
            if digest(old)!=d['rev']:raise ValueError('并行编辑，请刷新后继续')
            new=pattern.sub(lambda m:m.group().replace(m[1],asset['path']),old.decode('utf-8'))
            with NamedTemporaryFile(dir=f.parent,delete=False) as tmp:tmp.write(new.encode());name=tmp.name
            os.replace(name,f)
        put(ep,'adopt:'+slot,dict(asset=asset,slot=slot,stage=s,time=0,at=time.time()))
    elif kind in ('note','adopt','seen','heard'):
        asset=next((x for x in ev['media'] if x['id']==a.get('media')),None)
        if not asset:raise ValueError('媒体版本已变化，请刷新')
        atext=str(a.get('text','')).strip()[:4000];stamp=float(a.get('time',0));end=float(a.get('end',stamp))
        if not 0<=stamp<=end<604800 or (kind=='note' and not atext):raise ValueError('请输入意见和有效时间区间')
        pin(ep,project(ep),asset)
        v=dict(asset=asset,text=atext,time=stamp,end=end,stage=s,at=time.time(),owner=str(a.get('owner',''))[:70],slot=str(a.get('slot') or asset['path'])[:500])
        put(ep,kind+':'+(uuid.uuid4().hex if kind=='note' else v['slot'] if kind=='adopt' else asset['id']),v)
    elif kind=='resolve':
        key=a.get('key','');v=store(ep).get(key)
        if not key.startswith('note:') or not v:raise ValueError('找不到这条意见')
        v['resolved']=a.get('enabled') is True;put(ep,key,v)
    else:raise ValueError('操作无效')
    return store(ep)
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8')
    mode,base,*args=sys.argv[1:];base=Path(base).resolve(strict=True)
    eps=episodes(base);ep=next((p for p in eps if p.name==(args[0] if args else base.name)),eps[0] if not args and eps else None)
    if not ep:raise ValueError('无此集')
    if mode=='state':v=manifest(ep)
    elif mode=='action':v=action(ep,json.loads(sys.stdin.buffer.read()))
    elif mode=='gate':
        stop=blocked(ep,args[1]);v={'waiting':stop}
        if stop:print(json.dumps(v,ensure_ascii=False));print('导演台等待确认：'+stop,file=sys.stderr);sys.exit(3)
    else:raise ValueError('未知命令')
    print(json.dumps(v,ensure_ascii=False,allow_nan=False))
