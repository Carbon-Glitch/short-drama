"""Merge creative sections without replacing their stable IDs or adopted versions."""
import hashlib
import json
import re
from uuid import uuid4
from documents import section_specs,SUPPORTED,declared_shots,link_shots
from filesystem import io_path
from transfer import inside
from store import Conflict
from source_documents import new_sources
from reference_media import collect,paths,resolve,source_info,changed_sources

class DocumentSync:
 supported=SUPPORTED
 def specs(self,filename,text):return section_specs(filename,text)
 def current_entries(self,state,document):return [e for e in state['entities'] if e['data'].get('document_id')==document]
 def merge_fields(self,section):return ('name','text','order')
 def prepare_operations(self,operations,entities,state,preview):return operations
 def __init__(self,library,discovery):self.library=library;self.discovery=discovery
 def read(self,project,document):
  store=self.library.project(project);state=store.state();root=self.discovery.source_for(project)
  doc=next((e for e in state['entities'] if e['id']==document and e['kind']=='document' and e['data'].get('name') in self.supported),None)
  candidate=next((d for d in new_sources(state,root) if d['id']==document and d['data']['name'] in self.supported),None)
  if candidate:
   doc=candidate;state={**state,'entities':[e for e in state['entities'] if e['id']!=document]+[doc]}
  if root is None or not doc:raise ValueError('没有可读取的外部文档来源')
  text=io_path(inside(root,doc['data']['source_path'])).read_text(encoding='utf-8-sig')
  return store,state,doc,text
 def preview(self,project,document):
  _,state,doc,text=self.read(project,document)
  preamble,remote=self.specs(doc['data']['name'],text)
  old_preamble,base=self.specs(doc['data']['name'],doc['data'].get('source_baseline',doc['data'].get('original','')))
  def index(specs):
   result={s['key']:s for s in specs}
   if len(result)!=len(specs):raise ValueError('外部文档条目编号或标题重复，请先明确对应关系')
   return result
  remote=index(remote);base=index(base)
  current={}
  for entity in self.current_entries(state,document):
   data=entity['data'];key=data.get('code') or data.get('heading') or data.get('name')
   if key in current:raise ValueError('当前文档条目对应关系不明确')
   current[key]=entity
  changes=[]
  source_media=source_info(state,self.discovery.source_for(project),[text])
  changed_media=set(changed_sources(state,doc,source_media))
  for key,section in remote.items():
   existing=current.get(key);previous=base.get(key)
   if existing is None:
    if previous==section:continue
    changes.append({'key':key+':add','kind':'add','code':key,'name':section['data']['name'],'source':section,'current':None,'conflict':previous is not None});continue
   if existing['kind']!=section['kind']:raise ValueError('条目类型变化，请先在文档中区分新旧条目')
   for field in self.merge_fields(section):
    incoming=section['data'][field];old=previous['data'].get(field) if previous else None;local=existing['data'].get(field)
    if incoming==old or incoming==local:continue
    changes.append({'key':key+':'+field,'kind':'update','id':existing['id'],'code':key,'name':section['data']['name'],
                    'field':field,'before':old,'current':local,'source':incoming,'conflict':local!=old})
   field='input_reference_text' if section['kind']=='shot' else 'text'
   body=section['data'].get(field,'')
   local=existing['data'].get(field,'')
   available={m['path'] for m in source_media if m['sha256']}
   updates=changed_media.intersection(paths(body),paths(local),available)
   if updates and not any(c.get('id')==existing['id'] and c.get('field')==field for c in changes):
    local=existing['data'].get(field,'')
    changes.append({'key':key+':media','kind':'update','id':existing['id'],'code':key,'name':section['data']['name'],
                    'field':field,'source':local,'current':local,'conflict':False,'reason':'media','media_paths':sorted(updates)})
  for key in base.keys()-remote.keys():
   if key in current:changes.append({'key':key+':removed','kind':'removed','code':key,'name':current[key]['data']['name'],'conflict':True})
  local=doc['data'].get('preamble','')
  if preamble!=old_preamble and preamble!=local:
   changes.append({'key':'document:preamble','kind':'update','id':document,'name':'文档说明','field':'preamble','source':preamble,'current':local,'before':old_preamble,'conflict':local!=old_preamble})
  bodies=[]
  for change in changes:
   if change['kind']=='add':bodies.extend(change['source']['data'].get(key,'') for key in ('text','input_reference_text'))
   elif change.get('field') in ('text','input_reference_text'):bodies.append(change['source'])
  media=source_info(state,self.discovery.source_for(project),bodies)
  media.extend(m for m in source_media if m['path'] in changed_media and m['status']=='missing' and not any(item['path']==m['path'] for item in media))
  document_hash=hashlib.sha256(text.encode('utf8')).hexdigest()
  fingerprint=hashlib.sha256((document_hash+json.dumps([media,source_media],sort_keys=True)).encode('utf8')).hexdigest()
  return {'revision':state['project']['revision'],'document':document,'episode':doc['data']['parent_id'],
          'source_hash':fingerprint,'document_hash':document_hash,'changes':changes,'media':media,'source_media':source_media}
 def apply(self,project,document,revision,source_hash,choices):
  preview=self.preview(project,document);store,state,doc,text=self.read(project,document)
  if preview['revision']!=revision or state['project']['revision']!=revision:raise Conflict(state)
  if preview['source_hash']!=source_hash or hashlib.sha256(text.encode('utf8')).hexdigest()!=preview['document_hash']:
   raise ValueError('外部文档又有更新，请重新查看差异')
  operations=[];changed={};entities={e['id']:e for e in state['entities']}
  for change in preview['changes']:
   choice=choices.get(change['key'],None if change['conflict'] else 'source')
   if choice not in ('current','source'):raise ValueError('请先选择如何处理冲突')
   if change['kind']=='removed':
    if choice!='current':raise ValueError('请保留当前条目，避免删除已关联素材或镜头')
    continue
   if choice=='current':continue
   if change['kind']=='add':
    identity=str(uuid4());section=change['source'];data={**section['data'],'parent_id':preview['episode'],'document_id':document}
    entity={'id':identity,'kind':section['kind'],'data':data};entities[identity]=entity
    operations.append({'type':'create',**entity})
    if 'text' in data:changed[identity]=data['text']
   else:
    operations.append({'type':'update','id':change['id'],'patch':{change['field']:change['source']}})
    if change['field']=='text':changed[change['id']]=change['source']
  bodies=[]
  for op in operations:
   data=op.get('data',op.get('patch',{}))
   bodies.extend(data[key] for key in ('text','input_reference_text') if isinstance(data.get(key),str))
  state,media_operations=collect(store,state,self.discovery.source_for(project),bodies,{m['path']:m['sha256'] for m in preview['media']})
  for identity,body in changed.items():
   entry=entities[identity];previous=set(entry['data'].get('references',[]));references=[]
   for path in paths(body):
    media=resolve(state,path,previous)
    if media and media['id'] not in references:references.append(media['id'])
   operations.append({'type':'update','id':identity,'patch':{'references':references}})
   for old in previous-set(references):operations.append({'type':'unbind','source':old,'target':identity})
   for mid in references:operations.append({'type':'bind','source':mid,'target':identity,'fields':['sha256']})
   if entry['kind']=='submission':
    codes=declared_shots(body,entry['data'].get('code',''))
    shots,unresolved=link_shots(state,preview['episode'],codes)
    operations.append({'type':'update','id':identity,'patch':{'shot_ids':shots,'unresolved_shot_codes':unresolved}})
    for old in set(entry['data'].get('shot_ids',[]))-set(shots):operations.append({'type':'unbind','source':old,'target':identity})
    for sid in shots:operations.append({'type':'bind','source':sid,'target':identity,'fields':['action','duration','camera','movement','join','source_excerpt','visual_basis','sound','start','end','purpose','references','design_refs']})
  operations=self.prepare_operations(operations,entities,state,preview)
  operations=media_operations+operations
  if doc.get('_create'):operations.insert(0,{'type':'create','id':document,'kind':'document','data':doc['data']})
  patch={'source_baseline':text,'source_media_baseline':{m['path']:m['sha256'] for m in preview['source_media']}}
  if doc.get('_new_source'):patch['source_path']=doc['data']['source_path']
  operations.append({'type':'update','id':document,'patch':patch})
  return store.apply(revision,operations,actor='external-document-merge')
