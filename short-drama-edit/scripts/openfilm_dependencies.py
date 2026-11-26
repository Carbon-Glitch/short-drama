"""Keep the existing project-relative REF paths usable in an independent episode copy."""
from pathlib import Path
import re
import shutil
import json
import uuid

DOCUMENTS=('剧本.md','视觉设定.md','分镜.md','图片提示词.md','视频提示词.md')
REF=re.compile(r'(?:·|：)\s*([^·；\n《》]+?\.(?:png|jpe?g|webp|wav|mp3|m4a|mp4|mov|flac|ogg))《',re.I)

def copy_dependencies(episode, project, target):
    episode,project,target=map(lambda p:Path(p).resolve(),(episode,project,target))
    paths=set()
    for name in DOCUMENTS:
        file=episode/name
        if file.exists():
            text=file.read_text(encoding='utf-8');paths.update(m.group(1).strip() for m in REF.finditer(text))
            paths.update(m.group(1).strip() for m in re.finditer(r'声音参考[：:]\s*([^（(\n]+?\.(?:wav|mp3|m4a|flac|ogg))',text,re.I))
    missing=[p for p in paths if not (project/p).is_file()]
    if missing: raise ValueError('前期参考尚未落盘：'+', '.join(missing))
    for path in sorted(paths):
        source=(project/path).resolve();dest=(target/path).resolve()
        if not source.is_relative_to(project) or not dest.is_relative_to(target):raise ValueError('REF 应为项目相对路径: '+path)
        dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists() and dest.read_bytes()!=source.read_bytes():raise ValueError('目标参考与来源不同，请保留目标或另选迁移目录: '+path)
        if not dest.exists():shutil.copy2(source,dest)
    manifest=project/'short-drama.json'
    if manifest.exists() and not (target/'short-drama.json').exists():
        data=json.loads(manifest.read_text(encoding='utf-8-sig'));data['project_id']='SD-'+uuid.uuid4().hex[:12].upper()
        data['postproduction']={'backend':'openfilm','authority':'film.html','report':'剪辑单.md'}
        (target/'short-drama.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    return sorted(paths)
