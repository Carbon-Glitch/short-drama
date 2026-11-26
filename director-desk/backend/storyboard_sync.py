"""Field-level storyboard merges preserve shot IDs, adopted takes and local edits."""
from copy import deepcopy
import re
from document_sync import DocumentSync
from library import sections,fields
from documents import LABELS
from reference_media import paths,resolve

SHOT_FIELDS={'action':'唯一动作','duration':'时长','camera':'景别/机位','sound':'声音','start':'起点','end':'终点',
             'purpose':'目的','movement':'运镜','join':'接镜','source_excerpt':'来源','visual_basis':'视觉依据',
             'image_plan':'图片提示词项','production_split':'制作分工','input_reference_text':'输入参考图'}
PLAN_FIELDS=('blocking','generation_plan','director_review')

def prose(body):return '\n'.join(line for line in body.splitlines() if not re.match(r'^[-*]\s*[^：:\n]+[：:]',line)).strip()

class StoryboardSync(DocumentSync):
 supported={'分镜.md'}
 def specs(self,filename,text):
  records=[];plans={}
  for order,(heading,body) in enumerate(sections(text)):
   if heading.startswith(('场景站位','生成安排')):
    match=re.search(r'(?:[A-Za-z0-9]+-)*EP\d+-SC\d+',heading)
    if not match:raise ValueError('场景站位需要明确的 SC 编号')
    code=match[0];data=plans.setdefault(code,{'code':'SC:'+code,'name':code,**{key:'' for key in PLAN_FIELDS}})
    pattern=r'^- (生成安排|导演体验审读)：([\s\S]*?)(?=^- (?:生成安排|导演体验审读)：|\Z)'
    values={m[1]:m[2].strip() for m in re.finditer(pattern,body,re.M)}
    if heading.startswith('场景站位'):data['blocking']=re.sub(pattern,'',body,flags=re.M).strip()
    else:data['generation_plan']=body
    if values.get('生成安排'):data['generation_plan']=values['生成安排']
    if values.get('导演体验审读'):data['director_review']=values['导演体验审读']
    continue
   match=re.match(r'(SHOT-[A-Za-z0-9-]+)(?:\s*·\s*)?(.*)',heading)
   if not match:continue
   parsed=fields(body)
   data={'code':match[1],'name':match[2] or match[1],'order':order,'source_text':prose(body),
         'extra_fields':{key:value for key,value in parsed.items() if key not in SHOT_FIELDS.values()},
         **{key:parsed.get(label,'') for key,label in SHOT_FIELDS.items()}}
   records.append({'key':match[1],'kind':'shot','data':data})
  records.extend({'key':data['code'],'kind':'scene','data':data} for data in plans.values())
  return '',records
 def current_entries(self,state,document):
  doc=next(e for e in state['entities'] if e['id']==document);episode=doc['data']['parent_id']
  scenes=[e for e in state['entities'] if e['kind']=='scene' and e['data'].get('parent_id')==episode]
  scene_ids={e['id'] for e in scenes};result=[]
  for scene in scenes:
   if not scene['data'].get('code'):continue
   item=deepcopy(scene);item['data']['code']='SC:'+scene['data']['code']
   item['data'].update({key:scene['data'].get(key,'') for key in PLAN_FIELDS});result.append(item)
  for shot in state['entities']:
   if shot['kind']!='shot' or shot['data'].get('parent_id') not in scene_ids:continue
   item=deepcopy(shot);data=item['data'];raw=data.get('fields',{})
   for key,label in SHOT_FIELDS.items():data[key]=data.get(key,raw.get(label,''))
   data['extra_fields']={key:value for key,value in raw.items() if key not in SHOT_FIELDS.values()}
   data['source_text']=prose(data.get('source_text',''));result.append(item)
  return result
 def merge_fields(self,section):
  return PLAN_FIELDS if section['kind']=='scene' else ('name','order','source_text','extra_fields',*SHOT_FIELDS)
 def prepare_operations(self,operations,entities,state,preview):
  scenes={e['data'].get('code'):e['id'] for e in state['entities'] if e['kind']=='scene' and e['data'].get('parent_id')==preview['episode']}
  combined={};created=set()
  for op in operations:
   if op['type']=='create':
    if op['kind']=='scene':raise ValueError('请先同步剧本场次，再同步对应场景站位')
    created.add(op['id']);combined[op['id']]=op['data']
   elif op['type']=='update':combined.setdefault(op['id'],{}).update(op['patch'])
  for identity,patch in combined.items():
   entity=entities[identity]
   if entity['kind']!='shot':continue
   if identity in created:patch.pop('document_id',None)
   data={**entity['data'],**patch};raw=dict(data.get('fields',{}))
   if 'extra_fields' in patch:
    raw={key:value for key,value in raw.items() if key in SHOT_FIELDS.values()};raw.update(patch.pop('extra_fields'))
   for key,label in SHOT_FIELDS.items():
    if key in patch:raw[label]=patch[key]
   patch['fields']=raw
   if identity in created or 'source_excerpt' in patch:
    matches=[sid for code,sid in scenes.items() if code and code in data.get('source_excerpt','')]
    if len(matches)!=1:raise ValueError('镜头来源无法对应唯一场次，请先同步剧本：'+data.get('code',''))
    parent=matches[0];old=entity['data'].get('parent_id');patch['parent_id']=parent
    if old and old!=parent and identity not in created:operations.append({'type':'unbind','source':old,'target':identity})
    operations.append({'type':'bind','source':parent,'target':identity,'fields':['text']})
   if identity in created or 'input_reference_text' in patch:
    body=data.get('input_reference_text','');refs=[]
    for path in paths(body):
     media=resolve(state,path,entity['data'].get('references',[]))
     if media and media['id'] not in refs:refs.append(media['id'])
    patch['references']=refs
    for old in set(entity['data'].get('references',[]))-set(refs):operations.append({'type':'unbind','source':old,'target':identity})
    for mid in refs:operations.append({'type':'bind','source':mid,'target':identity,'fields':['sha256']})
   if identity in created or 'visual_basis' in patch:
    names=re.findall(r'(人物|造型|地点|道具)「([^」]+)」',data.get('visual_basis',''))
    refs=[e['id'] for e in state['entities'] if e['kind'] in LABELS and e['data'].get('parent_id')==preview['episode'] and (LABELS[e['kind']],e['data']['name']) in names]
    patch['design_refs']=refs
    for old in set(entity['data'].get('design_refs',[]))-set(refs):operations.append({'type':'unbind','source':old,'target':identity})
    for did in refs:operations.append({'type':'bind','source':did,'target':identity,'fields':['text']})
  # Collapse patches so internal parse-only fields never enter the canonical entities.
  result=[op for op in operations if op['type'] not in ('update','create')]
  for identity,patch in combined.items():
   patch.pop('extra_fields',None)
   result.insert(0,{'type':'create','id':identity,'kind':entities[identity]['kind'],'data':patch} if identity in created else {'type':'update','id':identity,'patch':patch})
  return result
