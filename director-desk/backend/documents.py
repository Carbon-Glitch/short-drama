"""Structured creative sections; Markdown remains a projection of stable entities."""
import re
from uuid import uuid5, NAMESPACE_URL

from store import Conflict
from reference_media import render_paths

TYPES={'人物':'character','造型':'look','地点':'location','道具':'prop'}
LABELS={v:k for k,v in TYPES.items()}
SUPPORTED={'视觉设定.md','图片提示词.md','视频提示词.md'}

def declared_shots(text,code=''):
    declaration=re.search(r'^- 分镜：([^\n]*)',text,re.M)
    if declaration:return set(re.findall(r'SHOT-[A-Za-z0-9-]+',declaration[1]))
    codes=set(re.findall(r'SHOT-[A-Za-z0-9-]+',text))
    if code.startswith('MOTION-'):codes.add(code.replace('MOTION-','SHOT-',1))
    return codes

def link_shots(state,episode,codes):
    scenes={e['id']:e for e in state['entities'] if e['kind']=='scene' and e['data'].get('parent_id')==episode}
    candidates={code:[] for code in codes}
    for shot in state['entities']:
        code=shot['data'].get('code')
        if shot['kind']=='shot' and shot['data'].get('parent_id') in scenes and code in candidates:candidates[code].append(shot)
    selected=[items[0] for items in candidates.values() if len(items)==1]
    selected.sort(key=lambda e:(scenes[e['data']['parent_id']]['data'].get('order',0),e['data'].get('order',0),e['id']))
    return [e['id'] for e in selected],sorted(code for code,items in candidates.items() if len(items)!=1)


def parts(text):
    matches=list(re.finditer(r'^##\s+(.+)$',text,re.M))
    if not matches:return text,[]
    return text[:matches[0].start()].rstrip(),[(m[1].strip(),text[m.end():matches[i+1].start() if i+1<len(matches) else None].strip()) for i,m in enumerate(matches)]


def section_specs(filename,text):
    prefix,sections=parts(text)
    if not sections and prefix:sections=[('内容',prefix)];prefix=''
    result=[]
    for order,(heading,body) in enumerate(sections):
        kind='design';name=heading;code=None
        match=re.match(r'^(人物|造型|地点|道具)\s*·\s*(.+)$',heading)
        if filename=='视觉设定.md' and match:kind=TYPES[match[1]];name=match[2]
        elif filename=='图片提示词.md':
            match=re.match(r'^(IMG-[A-Za-z0-9-]+)(?:\s*·\s*)?(.*)$',heading)
            if match:kind='image_prompt';code=match[1];name=match[2] or code
        elif filename=='视频提示词.md':
            match=re.match(r'^((?:MOTION|GROUP)-[A-Za-z0-9-]+)(?:\s*·\s*)?(.*)$',heading)
            if match:kind='submission';code=match[1];name=match[2] or code
        data={'name':name,'text':body,'order':order,'heading':heading}
        if code:data['code']=code
        result.append({'key':code or heading,'kind':kind,'data':data})
    return prefix,result


def materialize(store):
    state=store.state()
    docs=[e for e in state['entities'] if e['kind']=='document' and e['data'].get('name') in SUPPORTED and not e['data'].get('structured')]
    if not docs:return state
    operations=[];new=[]
    for doc in docs:
        prefix,specs=section_specs(doc['data']['name'],doc['data'].get('original',''))
        for spec in specs:
            kind=spec['kind'];data={**spec['data'],'parent_id':doc['data']['parent_id'],'document_id':doc['id']}
            order=data['order'];code=data.get('code');body=data['text']
            data['references']=[e['id'] for e in state['entities'] if e['kind']=='media'
                and (e['data']['path'] in body or (e['data']['path'].startswith('source/') and e['data']['path'][7:] in body))]
            if code:data['code']=code
            entity={'id':str(uuid5(NAMESPACE_URL,doc['id']+':section:'+str(order))),'kind':kind,'data':data}
            new.append(entity);operations.append({'type':'create',**entity})
        operations.append({'type':'update','id':doc['id'],'patch':{'structured':True,'preamble':prefix}})
    all_entities=state['entities']+new
    design={}
    for e in all_entities:
        if e['kind'] in LABELS:design[(e['data'].get('parent_id'),LABELS[e['kind']],e['data']['name'])]=e['id']
    for shot in [e for e in state['entities'] if e['kind']=='shot']:
        scene=next((e for e in state['entities'] if e['id']==shot['data'].get('parent_id')),None)
        if not scene:continue
        episode=scene['data'].get('parent_id')
        refs=list(shot['data'].get('design_refs',[]))
        for label,name in re.findall(r'(人物|造型|地点|道具)「([^」]+)」',shot['data'].get('fields',{}).get('视觉依据','')):
            identity=design.get((episode,label,name))
            if identity and identity not in refs:
                refs.append(identity)
                operations.append({'type':'bind','source':identity,'target':shot['id'],'fields':['text']})
        if refs!=shot['data'].get('design_refs',[]):operations.append({'type':'update','id':shot['id'],'patch':{'design_refs':refs}})
    for entry in new:
        if entry['kind']!='submission':continue
        codes=declared_shots(entry['data']['text'],entry['data'].get('code',''))
        links,unresolved=link_shots(state,entry['data']['parent_id'],codes)
        entry['data']['shot_ids']=links
        entry['data']['unresolved_shot_codes']=unresolved
        for identity in links:
            operations.append({'type':'bind','source':identity,'target':entry['id'],
                'fields':['action','duration','camera','movement','join','source_excerpt','visual_basis','sound','start','end','purpose','references','design_refs']})
    try:return store.apply(state['project']['revision'],operations,actor='project-import')
    except Conflict:return store.state()


def render_document(state,document):
    if not document['data'].get('structured'):return document['data'].get('original','')
    sections=sorted((e for e in state['entities'] if e['data'].get('document_id')==document['id']),key=lambda e:e['data'].get('order',0))
    output=[document['data'].get('preamble','')]
    for e in sections:
        data=e['data']
        heading=LABELS[e['kind']]+' · '+data['name'] if e['kind'] in LABELS else data.get('code','')+' · '+data['name'] if data.get('code') else data['name']
        output.append('## '+heading+'\n\n'+render_paths(data.get('text',''),state,e))
    return '\n\n'.join(p for p in output if p).rstrip()+'\n'
