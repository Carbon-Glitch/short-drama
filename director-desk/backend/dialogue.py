"""Derived dialogue identities and exact-line dependencies behind the scene editor."""
from collections import Counter
from difflib import SequenceMatcher
import re
from uuid import uuid4


def lines(text):
    result=[]
    for index,line in enumerate(text.splitlines(keepends=True)):
        raw=line.rstrip('\r\n');match=re.match(r'^([^:：\n]{1,32})[:：][ \t]*(.+)$',raw)
        if not match or raw.startswith(('#','[','-','*')):continue
        speaker=match[1].strip()
        if speaker in {'时间','地点','场景','备注','作者备注','转场'}:continue
        name=re.split('[（(]',speaker,maxsplit=1)[0].strip()
        result.append({'raw':raw,'speaker':name,'delivery':speaker[len(name):], 'text':match[2],'line_index':index})
    return result


def sync_dialogue(before,state,revision,changes):
    entities={e['id']:e for e in state['entities']};old={e['id']:e for e in before['entities']}
    for scene in list(entities.values()):
        if scene['kind']!='scene':continue
        text=scene['data'].get('text','')
        previous=sorted([e for e in entities.values() if e['kind']=='dialogue' and e['data'].get('parent_id')==scene['id'] and e['data'].get('derived_from_scene') and e['data'].get('present',True)],key=lambda e:e['data']['order'])
        parsed=lines(text);mapped={}
        matcher=SequenceMatcher(a=[e['data']['raw'] for e in previous],b=[p['raw'] for p in parsed],autojunk=False)
        for tag,a,b,c,d in matcher.get_opcodes():
            if tag in ('equal','replace'):
                for source,target in zip(range(a,b),range(c,d)):mapped[target]=previous[source]['id']
        active=[]
        for order,line in enumerate(parsed):
            identity=mapped.get(order) or str(uuid4())
            data={**line,'name':line['speaker'],'order':order,'parent_id':scene['id'],'derived_from_scene':True,'present':True}
            existing=entities.get(identity)
            if existing:
                changed={k for k,v in data.items() if existing['data'].get(k)!=v}
                if changed:
                    existing['data'].update(data);existing['revision']=revision
                    changes.setdefault(identity,set()).update(changed)
            else:entities[identity]={'id':identity,'kind':'dialogue','data':data,'revision':revision,'stale':False}
            active.append(entities[identity])
        active_ids={e['id'] for e in active}
        for removed in previous:
            if removed['id'] not in active_ids:
                removed['data']['present']=False;removed['revision']=revision
                changes.setdefault(removed['id'],set()).add('present')
        raw_lines=text.splitlines(keepends=True)
        for entry in active:
            index=entry['data']['line_index'];ending='\n' if raw_lines[index].endswith('\n') else ''
            raw_lines[index]='<dialogue:'+entry['id']+'>'+ending
        action_text=''.join(raw_lines)
        if scene['data'].get('action_text')!=action_text:
            scene['data']['action_text']=action_text
            if scene['id'] in old and 'action_text' in old[scene['id']]['data']:
                changes.setdefault(scene['id'],set()).add('action_text')
        # Narrow only when the shot names an exact, unique line. Otherwise retain broad coverage.
        counts=Counter(e['data']['text'] for e in active)
        for shot in [e for e in entities.values() if e['kind']=='shot' and e['data'].get('parent_id')==scene['id']]:
            if any(d['target']==shot['id'] and entities.get(d['source'],{}).get('kind')=='dialogue' for d in state['dependencies']):continue
            fields=shot['data'].get('fields',{})
            explicit='\n'.join(str(fields.get(k,'')) for k in ('对白','台词','原句'))
            source=shot['data'].get('source_text','')+'\n'+shot['data'].get('sound','')
            references=[e for e in active if counts[e['data']['text']]==1 and (
                e['data']['raw'] in explicit or e['data']['text'] in explicit or
                any(q+e['data']['text']+end in source for q,end in [('“','”'),('"','"')]))]
            if not references:continue
            for dep in state['dependencies']:
                if dep['source']==scene['id'] and dep['target']==shot['id'] and dep['fields']==['text']:dep['fields']=['action_text']
            for entry in references:
                state['dependencies'].append({'source':entry['id'],'target':shot['id'],
                    'fields':['text','speaker','delivery','present'],'source_revision':entry['revision']})
    state['entities']=list(entities.values())
