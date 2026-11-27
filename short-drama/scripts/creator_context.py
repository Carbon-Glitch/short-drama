"""Project complete owned Markdown sections into a read-only creative context."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def sections(path):
    if not path.is_file():return []
    text=path.read_text(encoding='utf-8-sig')
    headings=list(re.finditer(r'^##[ \t]+([^\r\n]+)',text,re.M))
    return [{'document':path.name,'heading':m[1].strip(),'text':text[m.start():headings[i+1].start() if i+1<len(headings) else None].rstrip()} for i,m in enumerate(headings)]


def code_of(record):
    match=re.match(r'(?:SHOT|DESIGN|IMG|MOTION|GROUP)-[A-Za-z0-9-]+',record['heading'])
    return match[0] if match else ''


def build_context(episode, selected, consumer=None):
    episode=Path(episode).resolve();selected=list(dict.fromkeys(selected))
    shots=sections(episode/'分镜.md')
    lookup={code_of(r):r for r in shots if r['heading'].startswith('SHOT-')}
    missing=set(selected)-lookup.keys()
    if missing:raise ValueError('分镜不存在：'+', '.join(sorted(missing)))
    def scene(record):
        m=re.search(r'^- 来源[：:]\s*(.*)',record['text'],re.M)
        ids=re.findall(r'(?:[A-Za-z0-9]+-)*EP\d+-SC\d+',m[1] if m else '')
        return ids[0] if ids else None
    scene_ids={scene(lookup[k]) for k in selected}-{None}
    neighbors=set();ordered=list(lookup)
    for code in selected:
        i=ordered.index(code)
        for j in (i-1,i+1):
            if 0<=j<len(ordered) and scene(lookup[ordered[j]])==scene(lookup[code]):neighbors.add(ordered[j])
    included=set(selected)|neighbors
    records=[{**r,'role':'selected' if code in selected else 'neighbor'} for code,r in lookup.items() if code in included]
    for r in shots:
        if r['heading'].startswith(('场景站位','生成安排')) and any(c in r['heading'] for c in scene_ids):records.append({**r,'role':'scene'})
    for r in sections(episode/'剧本.md'):
        if any(r['heading'].startswith(c) for c in scene_ids):records.append({**r,'role':'script'})
    if consumer is not None:records.append({**consumer,'role':'image_plan'})
    consumed='\n'.join(r['text'] for r in records)
    decisions=set(re.findall(r'DESIGN-[A-Za-z0-9-]+',consumed));found=set()
    for r in sections(episode/'视觉设定.md'):
        code=code_of(r);name=r['heading'].split(' · ',1)[-1]
        relevant=code in decisions or bool(re.search('体验设计|视觉主张|影像风格|全片风格',r['heading'])) or r['heading'].startswith('场面设计') and any(c in r['heading'] for c in scene_ids)
        if r['heading'].startswith(('人物 ·','造型 ·','地点 ·','道具 ·')):relevant='「'+name+'」' in consumed
        if relevant:records.append({**r,'role':'design'})
        if code in decisions:found.add(code)
    if decisions-found:raise ValueError('设计承接未找到：'+', '.join(sorted(decisions-found)))
    image_ids=set(re.findall(r'IMG-[A-Za-z0-9-]+',consumed))
    existing={(r['document'],r['heading']) for r in records}
    records.extend({**r,'role':'image_plan'} for r in sections(episode/'图片提示词.md') if code_of(r) in image_ids and (r['document'],r['heading']) not in existing)
    packet={'schema':1,'selected_shots':selected,'records':records}
    packet['fingerprint']=hashlib.sha256(json.dumps(packet,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    return packet


def for_entry(root,source,entry):
    path=Path(root)/source;records=sections(path)
    record=next((r for r in records if code_of(r)==entry),None)
    if record is None:raise ValueError('提交条目不存在：'+entry)
    if path.name=='图片提示词.md':return build_context(path.parent,[],record)
    match=re.search(r'^- 分镜[：:]\s*([^\n]+)',record['text'],re.M)
    selected=re.findall(r'SHOT-[A-Za-z0-9-]+',match[1]) if match else []
    if not selected and entry.startswith('MOTION-'):
        inferred=entry.replace('MOTION-','SHOT-',1)
        if any(code_of(r)==inferred for r in sections(path.parent/'分镜.md')):selected=[inferred]
    if not selected or not (path.parent/'分镜.md').is_file():return None
    return build_context(path.parent,selected)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('episode',type=Path);parser.add_argument('--shots',nargs='+',required=True)
    args=parser.parse_args();print(json.dumps(build_context(args.episode,args.shots),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
