"""Versioned Markdown boundary shared with the editor and Agent."""
import json
import re
from pathlib import Path

CONTRACT_PATH = Path(__file__).resolve().parents[1] / 'references/document-contract.json'
if not CONTRACT_PATH.is_file(): CONTRACT_PATH = Path(__file__).with_name('document-contract.json')
CONTRACT = json.loads(CONTRACT_PATH.read_text(encoding='utf8'))
SHOT_FIELDS = CONTRACT['shot_fields']
FIELD = re.compile(r'^[-*][ \t]+([^：:\n]+)[：:][ \t]*(.*)$')

def canonical_fields(values):
    """Normalize legacy labels without dropping unknown authored fields."""
    result = {}
    for key, value in values.items():
        label = CONTRACT['aliases'].get(key, key)
        if label in result and result[label] != value:
            raise ValueError('字段重复：' + label + '；请合并内容后导入')
        result[label] = value
    return result


def split_fields(text):
    result, prose, key, fenced = {}, [], None, False
    for line in text.splitlines():
        if line.lstrip().startswith('```'):
            fenced = not fenced
            key = None
        match = FIELD.match(line) if not fenced else None
        if match:
            label = re.sub(r'^(?:\*\*|__|\*|_)(.+?)(?:\*\*|__|\*|_)$', r'\1', match[1].strip())
            key = CONTRACT['aliases'].get(label, label)
            if key in result: raise ValueError('字段重复：' + key + '；请合并内容后导入，原文件未修改')
            result[key] = match[2]
        elif key is not None and (line.startswith((' ', '\t')) or not line.strip()):
            result[key] += '\n' + (line[2:] if line.startswith('  ') else line.lstrip('\t'))
        else:
            key = None
            prose.append(line)
    return {k:v.strip() for k,v in result.items()}, '\n'.join(prose).strip()

def render_fields(values):
    return '\n'.join('- '+k+'：'+str(v).replace('\n','\n  ') for k,v in values.items())

def check_headings(filename, text):
    version = re.search(r'<!-- director-document:(\d+) -->', text)
    if version and int(version[1]) > CONTRACT['version']:
        raise ValueError('文档版本较新，请升级导演台后导入；原文件未修改')
    seen = set()
    for heading in re.findall(r'^##\s+(.+)$',text,re.M):
        match = re.match(r'((?:SHOT|IMG|MOTION|GROUP|DESIGN)-[A-Za-z0-9-]+)(?:\s|$)',heading)
        if match:
            if match[1] in seen: raise ValueError('条目编号重复：'+match[1])
            seen.add(match[1])
        if filename == '分镜.md' and not (re.match(r'SHOT-[A-Za-z0-9-]+(?:\s|$)',heading) or heading.startswith(('场景站位','生成安排'))):
            raise ValueError('无法识别分镜标题「'+heading+'」，请使用 ## SHOT-EP001-001 · 名称；原文已保留')
        if filename in ('图片提示词.md','视频提示词.md'):
            prefix = r'IMG-' if filename=='图片提示词.md' else r'(?:MOTION|GROUP)-'
            if not re.match(prefix+r'[A-Za-z0-9-]+(?:\s|$)',heading):
                raise ValueError('无法识别'+filename+'条目「'+heading+'」；请使用 '+CONTRACT['documents'][filename])

def missing_shot_fields(data):
    return [SHOT_FIELDS[k] for k in CONTRACT['ready_fields'] if not str(data.get(k,canonical_fields(data.get('fields',{})).get(SHOT_FIELDS[k],''))).strip()]

def validate_data(kind, data):
    if not isinstance(data,dict):raise ValueError('条目内容必须是对象')
    text_fields = set(SHOT_FIELDS) | {'name','text','code','parent_id','document_id','blocking','generation_plan','director_review'}
    for key in text_fields & data.keys():
        if not isinstance(data[key],str):raise ValueError('字段 '+key+' 必须是文字')
    for key in ('references','design_refs','shot_ids'):
        if key in data and (not isinstance(data[key],list) or any(not isinstance(v,str) for v in data[key])):
            raise ValueError('字段 '+key+' 必须是 ID 列表')
    if 'order' in data and (type(data['order']) not in (int,float)):
        raise ValueError('排序必须是数字')

def validate_agent_fields(kind, data):
    common={'name','text','code','parent_id','document_id','order'}
    allowed=common | (set(SHOT_FIELDS)|{'references','design_refs','start','end'} if kind=='shot' else {'blocking','generation_plan','director_review'} if kind=='scene' else {'references','shot_ids'} )
    unknown=set(data)-allowed
    if unknown:raise ValueError('Agent 字段不受支持：'+', '.join(sorted(unknown))+'；请沿用当前字段名称')
    validate_data(kind,data)


def patch_fields(body, updates, *, shot=False):
    """Replace only requested field blocks; keep unrelated prose byte-for-byte."""
    if not isinstance(updates,dict) or any(not isinstance(v,str) for v in updates.values()):
        raise ValueError('fields 必须是字段名到文字的映射')
    normalized={}
    for key,value in updates.items():
        label=SHOT_FIELDS.get(key,CONTRACT['aliases'].get(key,key))
        if not isinstance(label,str) or not label or any(c in label for c in '\r\n：:'):
            raise ValueError('字段名称无效')
        if shot and label not in SHOT_FIELDS.values():raise ValueError('未知镜头字段：'+label)
        if label in normalized:raise ValueError('重复更新字段：'+label)
        normalized[label]=value
    split_fields(body)  # Detect ambiguous duplicate source fields before writing.
    lines=body.splitlines(keepends=True);blocks={};i=0;fenced=False
    while i<len(lines):
        if lines[i].lstrip().startswith('```'):fenced=not fenced
        match=FIELD.match(lines[i].rstrip('\r\n')) if not fenced else None
        if not match:i+=1;continue
        start=i;i+=1
        while i<len(lines) and (lines[i].startswith((' ','\t')) or not lines[i].strip()):i+=1
        end=i
        while end>start+1 and not lines[end-1].strip():end-=1
        key=CONTRACT['aliases'].get(match[1].strip(),match[1].strip())
        blocks[key]=(start,end)
    edits=[];extra=[]
    newline='\r\n' if '\r\n' in body else '\n'
    for key,value in normalized.items():
        value=value.replace('\r\n','\n')
        replacement=('- '+key+'：'+value.replace('\n',newline+'  ')+newline)
        if key in blocks:edits.append((*blocks[key],replacement))
        else:extra.append(replacement)
    for start,end,replacement in sorted(edits,reverse=True):lines[start:end]=[replacement]
    result=''.join(lines)
    if extra:
        # Fields precede prompt subsections; never append fields inside a prompt body.
        match=re.search(r'^###\s+',result,re.M)
        at=match.start() if match else len(result)
        result=result[:at]+(newline if at and not result[:at].endswith(newline) else '')+''.join(extra)+result[at:]
    return result


def creative_basis(state, episode):
    """Semantic source fingerprint for a managed episode's readable projection."""
    import hashlib
    entities={e['id']:e for e in state['entities']}
    scenes={e['id'] for e in entities.values() if e['kind']=='scene' and e['data'].get('parent_id')==episode}
    allowed={'scene','shot','design','character','look','location','prop','document','image_prompt','submission'}
    ignored={'candidate_media','adopted_media','source_baseline','source_hash','source_path','source_text','inherited_design_refs','asset_owner_refs','unresolved_design_codes'}
    result={}
    for e in entities.values():
        if e['kind'] not in allowed or e['data'].get('parent_id') not in scenes|{episode}:continue
        data={k:v for k,v in e['data'].items() if k not in ignored}
        result[e['id']]=hashlib.sha256(json.dumps(data,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    return result
