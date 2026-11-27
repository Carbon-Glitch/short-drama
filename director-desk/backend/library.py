"""Managed local projects and non-destructive import of creator-first documents."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from uuid import uuid4

from store import ProjectStore
from document_contract import split_fields, check_headings, SHOT_FIELDS
from filesystem import io_path
from project_settings import from_config

DOCS = ("剧本.md", "视觉设定.md", "分镜.md", "图片提示词.md", "视频提示词.md")
MEDIA = {".png", ".jpg", ".jpeg", ".webp", ".mp4", ".mov", ".webm", ".wav", ".mp3", ".m4a"}


def sections(text):
    headings = list(re.finditer(r"^##\s+(.+)$", text, re.M))
    return [(m[1].strip(), text[m.end():headings[i+1].start() if i+1 < len(headings) else None].strip())
            for i, m in enumerate(headings)]


def parse_script(text,code):
    matches=list(re.finditer(r"^##[ \t]+((?:[A-Za-z0-9]+-)*EP\d+-SC\d+)[ \t]*(.*)$",text,re.M))
    if not matches:return [{'code':code+'-SC001','name':'剧本草稿' if text else '第一场','text':text,'order':0}]
    result=[]
    for order,match in enumerate(matches):
        body=text[match.end():matches[order+1].start() if order+1<len(matches) else None].strip()
        if order==0:
            preamble=re.sub(r"\A[ \t]*#[ \t]+[^\n]*\n?", "",text[:match.start()]).strip()
            if preamble:body=preamble+"\n\n"+body
        result.append({'code':match[1],'name':match[2].strip() or f'第{order+1}场','text':body,'order':order})
    if len({item['code'] for item in result})!=len(result):raise ValueError('剧本场次编号重复，无法确定对应关系')
    return result


def fields(text):
    return split_fields(text)[0]


class Library:
    def __init__(self, home=None):
        self.home = Path(home or os.environ.get("DIRECTOR_DESK_HOME", Path.home()/".short-drama/director-desk")).resolve()
        self.projects = self.home / "projects"
        self.projects.mkdir(parents=True, exist_ok=True)
        self._hashes = {}

    def project(self, identity):
        if not re.fullmatch(r"[a-f0-9]{32}", identity or ""):
            raise ValueError("项目不存在")
        root = self.projects / identity
        if not (root/".short-drama/state/project.sqlite").is_file():
            raise ValueError("项目不存在")
        store=ProjectStore(root)
        from documents import materialize
        materialize(store)
        return store

    def list(self):
        result = []
        for folder in self.projects.iterdir():
            if not re.fullmatch(r"[a-f0-9]{32}", folder.name):
                continue
            try:
                state = self.project(folder.name).state()
                entities = state["entities"]
                cover = next((e["id"] for e in entities if e["kind"] == "media" and e["data"].get("type") == "image"), None)
                result.append({"id": folder.name, "title": state["project"]["title"],
                               "revision": state["project"]["revision"], "cover": cover,
                               "scenes": sum(e["kind"] == "scene" for e in entities)})
            except (ValueError, OSError):
                continue
        return result

    def create(self, title):
        identity = uuid4().hex
        store = ProjectStore.create(self.projects/identity, title)
        ep, scene = str(uuid4()), str(uuid4())
        store.apply(0, [
            {"type":"create","id":str(uuid4()),"kind":"project_settings","data":from_config({"format":{"aspect_ratio":"9:16","prompt_language":"en"}})},
            {"type": "create", "id": ep, "kind": "episode", "data": {"name": "第一集", "code": "EP001", "order": 0}},
            {"type": "create", "id": scene, "kind": "scene", "data": {"name": "第一场", "parent_id": ep, "order": 0, "text": ""}},
        ])
        return identity

    def add_episode(self, project_id, title, expected_revision):
        if not isinstance(title,str):raise ValueError('剧集名称无效')
        store=self.project(project_id);state=store.state()
        episodes=[e for e in state['entities'] if e['kind']=='episode']
        numbers=[int(match[1]) for e in episodes if (match:=re.fullmatch(r'EP(\d+)',e['data'].get('code','')))]
        number=max(numbers,default=0)+1;code=f'EP{number:03}';identity=str(uuid4());scene=str(uuid4())
        state=store.apply(expected_revision,[{'type':'create','id':identity,'kind':'episode','data':{'name':title.strip() or f'第{number}集','code':code,'order':max((e['data'].get('order',0) for e in episodes),default=-1)+1}},
            {'type':'create','id':scene,'kind':'scene','data':{'name':'第一场','code':code+'-SC001','parent_id':identity,'order':0,'text':''}}])
        return {'episode':identity,'state':state}

    def import_script(self, source):
        source=Path(source)
        if source.suffix.lower() not in ('.md','.txt'):raise ValueError('请选择 Markdown 或 TXT 剧本')
        if source.stat().st_size>4*1024*1024:raise ValueError('剧本超过4MB，请按集拆分导入')
        try:text=source.read_text(encoding='utf-8-sig')
        except UnicodeDecodeError:raise ValueError('请将剧本保存为 UTF-8 编码后导入')
        if not text.strip():raise ValueError('剧本内容为空')
        title=source.stem
        if title in ('剧本','script'):
            heading=re.search(r'^#[ \t]+(.+)$',text,re.M)
            if heading:title=heading[1].strip()
        cache=self.home/'cache';cache.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache,prefix='script-') as temporary:
            root=Path(temporary)
            (root/'short-drama.json').write_text(json.dumps({'title':title},ensure_ascii=False),encoding='utf8')
            (root/'剧本.md').write_text(text,encoding='utf8')
            return self.import_project(root)

    def import_project(self, source):
        source = Path(source).expanduser().resolve(strict=True)
        if not source.is_dir():
            raise ValueError("请选择项目文件夹")
        for doc in source.rglob('*.md'):
            if doc.name in DOCS and '制作成果' not in doc.parts and '.short-drama' not in doc.parts:
                check_headings(doc.name,doc.read_text(encoding='utf-8-sig'))
        if source == self.projects or self.projects in source.parents:
            raise ValueError("此项目已经在资料库中")
        config = source/"short-drama.json"
        title = source.name
        project_config=json.loads(config.read_text(encoding="utf-8-sig")) if config.is_file() else {}
        title=project_config.get("title") or title
        episodes_root = source/"剧集"
        if not episodes_root.is_dir():
            episodes_root = source/"episodes"
        episodes = sorted(p for p in episodes_root.iterdir() if p.is_dir()) if episodes_root.is_dir() else [source]
        episodes = [p for p in episodes if any((p/name).is_file() for name in DOCS)]
        if not episodes and any((source/name).is_file() for name in DOCS):
            episodes=[source]
        if not episodes:
            raise ValueError("没有找到剧本或分镜。请选择包含创作文档的项目。")
        identity = uuid4().hex
        staging = self.projects/(identity+".importing")
        store = ProjectStore.create(staging, title)
        ops, entities, media_by_path = [], {}, {}

        def add(kind, data, key=None):
            uid = str(uuid4())
            ops.append({"type": "create", "id": uid, "kind": kind, "data": data})
            if key:
                entities[key] = uid
            return uid

        def media(path):
            resolved = path.resolve()
            if not resolved.is_relative_to(source) or not resolved.is_file() or resolved.suffix.lower() not in MEDIA:
                return None
            relative = resolved.relative_to(source).as_posix()
            if relative in media_by_path:
                return media_by_path[relative]
            target = staging/"source"/relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(resolved, target)
            with target.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            kind = "image" if target.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"} else "video" if target.suffix.lower() in {".mp4", ".mov", ".webm"} else "audio"
            uid = add("media", {"name": target.stem, "path": "source/"+relative, "type": kind, "sha256": digest})
            media_by_path[relative] = uid
            return uid

        add("project_settings",from_config(project_config))
        try:
            for ep_order, ep_path in enumerate(episodes):
                code = ep_path.name if re.fullmatch(r"EP\d+", ep_path.name) else f"EP{ep_order+1:03}"
                ep_id = add("episode", {"name": code, "code": code, "order": ep_order})
                scene_map = {}
                script_text = ""
                for name in DOCS:
                    path = ep_path/name
                    if not path.is_file():
                        continue
                    text = path.read_text(encoding="utf-8-sig")
                    add("document", {"name": name, "parent_id": ep_id, "original": text, "source_path": path.relative_to(source).as_posix()})
                    for reference in re.findall(r"·\s*([^·；\n《》]+?\.(?:png|jpg|jpeg|webp|wav|mp3|m4a|mp4|webm|mov))《", text, re.I):
                        media(source/reference.strip())
                    if name == "剧本.md":
                        script_text=text
                        for item in parse_script(text,code):
                            scene_id=add("scene", {**item,"parent_id":ep_id})
                            scene_map[item['code']]=scene_id
                if not scene_map:
                    scene_map[code+"-SC001"] = add("scene", {"name": "剧本草稿" if script_text else "第一场", "code": code+"-SC001", "parent_id": ep_id, "order": 0, "text": script_text})
                storyboard = ep_path/"分镜.md"
                if storyboard.exists():
                    storyboard_sections=sections(storyboard.read_text(encoding="utf-8-sig"))
                    for heading,body in storyboard_sections:
                        if heading.startswith(('场景站位','生成安排')):
                            scene_code=next((code for code in scene_map if code in heading),None)
                            if scene_code:
                                pattern=r'^- (生成安排|导演体验审读)：([\s\S]*?)(?=^- (?:生成安排|导演体验审读)：|\Z)'
                                info={m[1]:m[2].strip() for m in re.finditer(pattern,body,re.M)}
                                patch={'blocking':re.sub(pattern,'',body,flags=re.M).strip()} if heading.startswith('场景站位') else {'generation_plan':body}
                                if info.get('生成安排'):patch['generation_plan']=info['生成安排']
                                if info.get('导演体验审读'):patch['director_review']=info['导演体验审读']
                                ops.append({'type':'update','id':scene_map[scene_code],'patch':patch})
                    for order, (heading, body) in enumerate(storyboard_sections):
                        match = re.match(r"(SHOT-[A-Za-z0-9-]+)(?:\s*·\s*)?(.*)", heading)
                        if not match:
                            continue
                        f = fields(body)
                        parent = next((v for k,v in scene_map.items() if k in f.get("来源", "")), next(iter(scene_map.values())))
                        refs = []
                        for ref in re.findall(r"·\s*([^·；\n《》]+?\.(?:png|jpg|jpeg|webp))《", f.get("输入参考图", ""), re.I):
                            media_id = media(source/ref.strip())
                            if media_id:
                                refs.append(media_id)
                        shot_id = add("shot", {"name": match[2] or match[1], "code": match[1], "parent_id": parent,
                            "order": order, **{key:f.get(label, "") for key,label in SHOT_FIELDS.items()},
                            "references": refs, "source_text": body, "fields": f}, match[1])
                        ops.append({"type": "bind", "source": parent, "target": shot_id, "fields": ["text"]})
                        for ref_id in refs:
                            ops.append({"type": "bind", "source": ref_id, "target": shot_id, "fields": ["sha256"]})
                # Keep actual outputs separate from adoption. Never infer acceptance from the newest filename.
                outputs = ep_path/"制作成果"
                if outputs.exists():
                    for path in sorted(outputs.rglob("*")):
                        if path.is_file() and path.suffix.lower() in MEDIA:
                            media(path)
                # Preserve the existing editable timeline and its local HTML/VTT assets.
                for path in ep_path.rglob("*"):
                    if path.is_file() and path.suffix.lower() in {".html", ".vtt", ".srt", ".css"} and ".film" not in path.parts:
                        relative = path.relative_to(source)
                        target = staging/"source"/relative
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(path, target)
                film = ep_path/"film.html"
                if film.exists():
                    next(o for o in ops if o.get("id") == ep_id)["data"]["film_path"] = "source/"+film.relative_to(source).as_posix()
                    for name in ("project.json", "bindings.json"):
                        original = ep_path/".short-drama"/name
                        if original.is_file():
                            target = staging/"source"/original.relative_to(source)
                            target.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(original, target)
            store.apply(0, ops, actor="import")
            store.freeze("导入原稿")
            staging.rename(self.projects/identity)
            return identity
        except BaseException:
            # Keep failed imports recoverable, but they are never listed as projects.
            raise

    def file(self, project_id, media_id):
        store = self.project(project_id)
        entity = next((e for e in store.state()["entities"] if e["id"] == media_id and e["kind"] == "media"), None)
        if entity is None:
            raise ValueError("素材不存在")
        path = (store.root/entity["data"]["path"]).resolve(strict=True)
        if not path.is_relative_to(store.root):
            raise ValueError("素材不在项目中")
        stamp = (path.stat().st_mtime_ns, path.stat().st_size)
        cached = self._hashes.get(str(path))
        if not cached or cached[0] != stamp:
            with io_path(path).open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            self._hashes[str(path)] = (stamp, digest)
        if self._hashes[str(path)][1] != entity["data"]["sha256"]:
            raise ValueError("素材文件发生变化，请作为新版本导入")
        return io_path(path)

    def add_media(self, project_id, paths, expected_revision, shot_id=None, *, production=None):
        store = self.project(project_id)
        state = store.state()
        if expected_revision != state["project"]["revision"]:
            from store import Conflict
            raise Conflict(state)
        shot = next((e for e in state["entities"] if e["id"] == shot_id and e["kind"] in ('shot','submission','image_prompt')), None)
        if shot_id and not shot:
            raise ValueError("镜头不存在")
        operations, added = [], []
        for source in paths:
            source = Path(source).resolve(strict=True)
            if not source.is_file() or source.suffix.lower() not in MEDIA:
                raise ValueError("请选择图片、视频或音频文件")
            identity = str(uuid4())
            target = store.root/"media"/(identity+source.suffix.lower())
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            with target.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            media_type = "image" if target.suffix in {".png", ".jpg", ".jpeg", ".webp"} else "video" if target.suffix in {".mp4", ".mov", ".webm"} else "audio"
            operations.append({"type": "create", "id": identity, "kind": "media", "data": {
                "name": source.stem, "path": target.relative_to(store.root).as_posix(),
                "type": media_type, "sha256": digest, "origin": "generation" if production else "import", "shot_id": shot_id, **({"production":production} if production else {})}})
            added.append(identity)
        if not operations:
            return state
        if shot:
            operations.append({"type": "update", "id": shot_id, "patch": {
                "candidate_media": list(dict.fromkeys(shot["data"].get("candidate_media", [])+added))}})
        return store.apply(expected_revision, operations, actor="media-import")

    def adopt(self, project_id, shot_id, media_id, expected_revision):
        store = self.project(project_id)
        state = store.state()
        entity = next((e for e in state["entities"] if e["id"] == media_id and e["kind"] == "media"), None)
        shot = next((e for e in state["entities"] if e["id"] == shot_id and e["kind"] in ('shot','submission','image_prompt','character','look','location','prop')), None)
        if entity is None or shot is None:
            raise ValueError("请选择镜头和实际素材")
        if entity["data"]["type"] not in {"video", "image"}:
            raise ValueError("镜头画面需要图片或视频，音频请放入声音轨道")
        if shot["kind"]=="submission" and entity["data"]["type"]!="video":raise ValueError("视频生成单元只能采用视频回片")
        if shot["kind"] in ("image_prompt","character","look","location","prop") and entity["data"]["type"]!="image":raise ValueError("图片条目只能采用图片")
        self.file(project_id, media_id)
        operations=[{"type": "update", "id": shot_id, "patch": {
            "adopted_media": media_id,
            "candidate_media": list(dict.fromkeys(shot["data"].get("candidate_media", [])+[media_id]))}}]
        if shot['kind'] in ('character','look','location','prop'):
            for target in state['entities']:
                if target['kind']=='shot' and shot_id in target['data'].get('design_refs',[]):
                    dependency=next((d for d in state['dependencies'] if d['source']==shot_id and d['target']==target['id']),None)
                    if dependency is None or (dependency['fields'] and 'adopted_media' not in dependency['fields']):
                        fields=list(dict.fromkeys((dependency['fields'] if dependency else ['text'])+['adopted_media']))
                        operations.append({'type':'bind','source':shot_id,'target':target['id'],'fields':fields})
        return store.apply(expected_revision,operations,actor="adopt")
