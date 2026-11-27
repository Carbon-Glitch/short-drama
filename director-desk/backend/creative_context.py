"""Read complete owned records for a creative task; never summarize source prose."""

def context_ids(state, selected, stage=''):
    entities={e['id']:e for e in state['entities']}
    visible=set(selected)
    # Resolve actual inputs, including bindings saved before a dependency edge exists.
    while True:
        needed={d['source'] for d in state['dependencies'] if d['target'] in visible}
        for identity in list(visible):
            e=entities.get(identity,{})
            data=e.get('data',{})
            needed.update(i for key in ('references','design_refs','inherited_design_refs','shot_ids') for i in data.get(key,[]))
            needed.update(data[k] for k in ('parent_id','document_id') if data.get(k) in entities)
        needed &= entities.keys()
        if needed<=visible:break
        visible.update(needed)
    scenes={e['id'] for e in entities.values() if e['kind']=='scene' and e['id'] in visible}
    episodes={e['id'] for e in entities.values() if e['kind']=='episode' and e['id'] in visible}
    # Neighbor records provide real entry/exit states, not an invented continuity summary.
    selected_shots=set(visible)
    for scene in scenes:
        shots=sorted((e for e in entities.values() if e['kind']=='shot' and e['data'].get('parent_id')==scene),key=lambda e:(e['data'].get('order',0),e['id']))
        for n,e in enumerate(shots):
            if e['id'] in selected_shots:
                visible.update(s['id'] for s in shots[max(0,n-1):n+2])
    if stage in ('storyboard','design','assets',''):
        visible.update(e['id'] for e in entities.values() if e['kind'] in ('design','character','look','location','prop') and e['data'].get('parent_id') in episodes)
    visible.update(e['id'] for e in entities.values() if e['kind']=='project_settings')
    while True:
        needed={d['source'] for d in state['dependencies'] if d['target'] in visible}
        if needed<=visible:break
        visible.update(needed)
    return visible & entities.keys()


def project_context(state, visible):
    from document_contract import SHOT_FIELDS, canonical_fields, split_fields
    records=[]
    for entry in state['entities']:
        if entry['id'] not in visible:continue
        data={k:v for k,v in entry['data'].items() if k not in ('source_baseline','source_hash','candidate_media')}
        if entry['kind']=='document' and data.get('structured'):
            data.pop('original',None)
        if entry['kind']=='shot':
            raw=canonical_fields(data.pop('fields',{}))
            for key,label in SHOT_FIELDS.items():
                if key not in data and label in raw:data[key]=raw[label]
            extra={k:v for k,v in raw.items() if k not in SHOT_FIELDS.values()}
            if extra:data['extra_fields']=extra
            if data.get('source_text'):data['source_text']=split_fields(data['source_text'])[1]
        records.append({**entry,'data':data})
    return {**state,'entities':records,
            'dependencies':[d for d in state['dependencies'] if d['source'] in visible and d['target'] in visible]}
