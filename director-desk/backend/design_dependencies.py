"""Resolve episode defaults and explicitly consumed design decisions by stable code."""
import re
from document_contract import SHOT_DEPENDENCIES


def connect_designs(state):
    entities={e['id']:e for e in state['entities']}
    designs=[e for e in entities.values() if e['kind']=='design']
    for shot in entities.values():
        if shot['kind']!='shot':continue
        data=shot['data'];scene=entities.get(data.get('parent_id'))
        if not scene or scene['kind']!='scene':continue
        declared=set(re.findall(r'DESIGN-[A-Za-z0-9-]+',data.get('design_intent',data.get('fields',{}).get('设计承接',''))))
        matched=set();known=set()
        for design in designs:
            if design['data'].get('parent_id')!=scene['data'].get('parent_id'):continue
            d=design['data'];code=d.get('code');name=d.get('name','')
            if code:known.add(code)
            scenes=re.findall(r'(?:[A-Za-z0-9]+-)*EP\d+-SC\d+',name)
            inherited=not code and (scene['data'].get('code') in scenes if scenes else bool(re.search('视觉主张|影像风格|全片风格',name)))
            if inherited or code in declared:matched.add(design['id'])
        previous=set(data.get('inherited_design_refs',[]))
        removed=previous-matched-set(data.get('design_refs',[]))
        state['dependencies']=[d for d in state['dependencies'] if not (d['target']==shot['id'] and d['source'] in removed)]
        pairs={(d['source'],d['target']) for d in state['dependencies']}
        for identity in sorted(matched):
            if (identity,shot['id']) not in pairs:
                state['dependencies'].append({'source':identity,'target':shot['id'],'fields':['text','name'],'source_revision':entities[identity]['revision']})
        data['inherited_design_refs']=sorted(matched)
        data['unresolved_design_codes']=sorted(declared-known)
    connect_asset_designs(state)
    # Existing projects gain new dimensions without accepting an old source revision.
    for dep in state['dependencies']:
        source=entities.get(dep['source']);target=entities.get(dep['target'])
        if source and target and source['kind']=='shot' and target['kind']=='submission' and dep['fields']:
            dep['fields']=list(dict.fromkeys([*dep['fields'],*SHOT_DEPENDENCIES]))


def sync_design_names(before, state, revision):
    """Rename bound labels, retaining authored responsibilities and qualifiers."""
    labels={'character':'人物','look':'造型','location':'地点','prop':'道具'}
    old={e['id']:e for e in before['entities']};renamed=[]
    for e in state['entities']:
        prior=old.get(e['id'])
        if e['kind'] in labels and prior and prior['data'].get('name')!=e['data'].get('name'):
            label=labels[e['kind']]
            renamed.append((e['id'],label+'「'+prior['data'].get('name','')+'」',label+'「'+e['data'].get('name','')+'」'))
    for shot in state['entities']:
        if shot['kind']!='shot':continue
        data=shot['data'];raw=data.get('fields',{});text=data.get('visual_basis',raw.get('视觉依据',''));original=text
        for identity,source,target in renamed:
            if identity in data.get('design_refs',[]):text=text.replace(source,target)
        if text!=original:
            data['visual_basis']=text
            if '视觉依据' in raw:raw['视觉依据']=text
            shot['revision']=revision


def connect_asset_designs(state):
    entities={e['id']:e for e in state['entities']}
    labels={'character':'人物','look':'造型','location':'地点','prop':'道具'}
    for entry in entities.values():
        if entry['kind']!='image_prompt':continue
        data=entry['data'];body=data.get('text','')
        codes=set(re.findall(r'DESIGN-[A-Za-z0-9-]+',body))
        names=set(re.findall(r'(人物|造型|地点|道具)「([^」]+)」',body))
        matched=set();known=set()
        for source in entities.values():
            d=source['data']
            if d.get('parent_id')!=data.get('parent_id'):continue
            if source['kind']=='design':
                if d.get('code'):known.add(d['code'])
                if d.get('code') in codes or not d.get('code') and re.search('视觉主张|影像风格|全片风格',d.get('name','')):matched.add(source['id'])
            elif source['kind'] in labels and (labels[source['kind']],d.get('name')) in names:matched.add(source['id'])
        previous=set(data.get('inherited_design_refs',[]))
        state['dependencies']=[d for d in state['dependencies'] if not(d['target']==entry['id'] and d['source'] in previous-matched)]
        pairs={(d['source'],d['target']) for d in state['dependencies']}
        for identity in matched:
            if (identity,entry['id']) not in pairs:state['dependencies'].append({'source':identity,'target':entry['id'],'fields':['text','adopted_media'],'source_revision':entities[identity]['revision']})
        data['inherited_design_refs']=sorted(matched);data['unresolved_design_codes']=sorted(codes-known)
    # Consumers of an adopted image follow its creative owner, not historical candidates.
    for target in entities.values():
        if target['kind'] not in ('shot','submission','image_prompt'):continue
        owners={e['id'] for e in entities.values() if e['kind']=='image_prompt' and e['id']!=target['id'] and e['data'].get('adopted_media') in target['data'].get('references',[])}
        previous=set(target['data'].get('asset_owner_refs',[]))
        state['dependencies']=[d for d in state['dependencies'] if not(d['target']==target['id'] and d['source'] in previous-owners)]
        pairs={(d['source'],d['target']) for d in state['dependencies']}
        for identity in owners:
            if (identity,target['id']) not in pairs:state['dependencies'].append({'source':identity,'target':target['id'],'fields':['text','adopted_media'],'source_revision':entities[identity]['revision']})
        target['data']['asset_owner_refs']=sorted(owners)
