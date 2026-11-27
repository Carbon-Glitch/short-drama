"""CLI entry edits use the browser's entity store, revisions and dependency graph."""
from pathlib import PurePosixPath
from document_contract import CONTRACT, SHOT_FIELDS, patch_fields, validate_data
from store import Conflict

def find_entry(state, entry, episode=None, document=None):
    entities={e['id']:e for e in state['entities']}
    candidates=[]
    for entity in entities.values():
        data=entity['data']
        if entry not in (entity['id'],data.get('code'),data.get('name')):continue
        if entity['kind'] not in ('shot','scene','design','character','look','location','prop','image_prompt','submission'):continue
        parent=entities.get(data.get('parent_id'),{})
        ep=entities.get(parent.get('data',{}).get('parent_id'),{}) if parent.get('kind')=='scene' else parent
        if episode and episode not in (ep.get('id'),ep.get('data',{}).get('code')):continue
        if document:
            doc=entities.get(data.get('document_id'),{})
            name='分镜.md' if entity['kind']=='shot' else doc.get('data',{}).get('name')
            if name!=PurePosixPath(document).name:continue
        candidates.append(entity)
    if len(candidates)!=1:raise ValueError('条目不存在或不唯一，请指定 --episode 和 --document')
    return candidates[0]

def read_entry(store,entry,episode=None,document=None):
    state=store.state();entity=find_entry(state,entry,episode,document)
    return {'revision':state['project']['revision'],'entity':entity}

def update_entry(store,entry,expected,patch,episode=None,document=None,actor='agent'):
    state=store.state()
    if expected is None:raise ValueError('修改需要当前项目版本')
    if expected!=state['project']['revision']:raise Conflict(state)
    entity=find_entry(state,entry,episode,document)
    if not isinstance(patch,dict) or set(patch) not in ({'fields'},{'text'}):raise ValueError('提交 text 或 fields 中的一种')
    if entity['kind']=='shot':
        if 'text' in patch:raise ValueError('镜头请按 fields 修改，保留编号与关联')
        values=patch['fields']
        if not isinstance(values,dict):raise ValueError('fields 必须是对象')
        reverse={v:k for k,v in SHOT_FIELDS.items()};updates={}
        for key,value in values.items():
            key=reverse.get(CONTRACT['aliases'].get(key,key),key)
            if key not in SHOT_FIELDS:raise ValueError('未知镜头字段：'+key)
            if key in updates:raise ValueError('重复镜头字段：'+key)
            updates[key]=value
    else:
        updates={'text':patch['text'] if 'text' in patch else patch_fields(entity['data'].get('text',''),patch['fields'])}
    validate_data(entity['kind'],updates)
    operations=[{'type':'update','id':entity['id'],'patch':updates}]
    if entity['kind']=='shot':
        from storyboard_sync import StoryboardSync
        entities={e['id']:e for e in state['entities']}
        scene=entities[entity['data']['parent_id']]
        operations=StoryboardSync(None,None).prepare_operations(operations,entities,state,{'episode':scene['data']['parent_id']})
    return store.apply(expected,operations,actor)
