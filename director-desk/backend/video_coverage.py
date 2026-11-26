"""Visual shot coverage edits share the canonical submission and dependency graph."""
import re
from store import Conflict
from documents import declared_shots,link_shots

SHOT_DEPENDENCIES=['action','duration','camera','movement','join','source_excerpt','visual_basis','sound','start','end','purpose','references','design_refs']

class VideoCoverage:
 def __init__(self,library):self.library=library
 def context(self,project,identity):
  store=self.library.project(project);state=store.state()
  unit=next((e for e in state['entities'] if e['id']==identity and e['kind']=='submission'),None)
  if not unit:raise ValueError('请选择视频生成条目')
  scenes=sorted([e for e in state['entities'] if e['kind']=='scene' and e['data'].get('parent_id')==unit['data'].get('parent_id')],key=lambda e:e['data'].get('order',0))
  shots=[]
  for scene in scenes:
   shots.extend(sorted([e for e in state['entities'] if e['kind']=='shot' and e['data'].get('parent_id')==scene['id']],key=lambda e:e['data'].get('order',0)))
  return store,state,unit,scenes,shots
 def describe(self,project,identity):
  _,state,unit,scenes,shots=self.context(project,identity);names={e['id']:e['data']['name'] for e in scenes}
  selected=unit['data'].get('shot_ids',[]);valid={s['id'] for s in shots};invalid=any(s not in valid for s in selected)
  if invalid:
   inferred,_=link_shots(state,unit['data']['parent_id'],declared_shots(unit['data'].get('text',''),unit['data'].get('code','')))
   selected=list(dict.fromkeys([s for s in selected if s in valid]+inferred))
  return {'revision':state['project']['revision'],'selected':selected,'invalid_previous':invalid,
          'shots':[{'id':e['id'],'name':e['data']['name'],'scene':names[e['data']['parent_id']],'duration':e['data'].get('duration',''),'action':e['data'].get('action','')} for e in shots]}
 def update(self,project,identity,selected,revision):
  store,state,unit,scenes,shots=self.context(project,identity)
  if state['project']['revision']!=revision:raise Conflict(state)
  if not isinstance(selected,list) or any(not isinstance(s,str) for s in selected) or len(set(selected))!=len(selected):raise ValueError('镜头选择无效')
  if not set(selected)<={e['id'] for e in shots}:raise ValueError('只能选择当前剧集的镜头')
  selected_shots=[e for e in shots if e['id'] in selected];operations=[];codes=[]
  reserved={e['data'].get('code') for e in state['entities'] if e['kind']=='shot'}
  episode=next(e for e in state['entities'] if e['id']==unit['data']['parent_id'])
  epcode=episode['data'].get('code','EP001');number=1
  for shot in selected_shots:
   code=shot['data'].get('code')
   if not code:
    while f'SHOT-{epcode}-{number:03}' in reserved:number+=1
    code=f'SHOT-{epcode}-{number:03}';reserved.add(code)
    operations.append({'type':'update','id':shot['id'],'patch':{'code':code}})
   if code in codes:raise ValueError('当前镜头编号重复，请先整理分镜来源')
   codes.append(code)
  text=unit['data'].get('text','');line='- 分镜：'+('、'.join(codes) if codes else '未关联')
  text=re.sub(r'^- 分镜：[^\n]*',lambda _:line,text,count=1,flags=re.M) if re.search(r'^- 分镜：',text,re.M) else line+'\n'+text
  ordered=[s['id'] for s in selected_shots]
  operations.append({'type':'update','id':identity,'patch':{'shot_ids':ordered,'text':text,'unresolved_shot_codes':[]}})
  old=set(unit['data'].get('shot_ids',[]))
  for sid in old-set(ordered):operations.append({'type':'unbind','source':sid,'target':identity})
  for sid in ordered:
   if not any(d['source']==sid and d['target']==identity and d['fields']==SHOT_DEPENDENCIES for d in state['dependencies']):
    operations.append({'type':'bind','source':sid,'target':identity,'fields':SHOT_DEPENDENCIES})
  return store.apply(revision,operations,actor='video-shot-coverage')
