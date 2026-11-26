"""Three-way script merge from a registered original into the managed project copy."""
import hashlib
from uuid import uuid4
from library import parse_script
from store import Conflict
from transfer import inside
from filesystem import io_path
from documents import SUPPORTED
from document_sync import DocumentSync
from storyboard_sync import StoryboardSync
from source_documents import new_sources
from reference_media import source_info,changed_sources

class ScriptSync:
 def __init__(self,library,discovery):self.library=library;self.discovery=discovery
 def sources(self,project):
  root=self.discovery.source_for(project)
  if root is None:return []
  state=self.library.project(project).state();result=[]
  for doc in state['entities']:
   if doc['kind']!='document' or doc['data'].get('name') not in SUPPORTED|{'剧本.md','分镜.md'} or not doc['data'].get('source_path'):continue
   try:text=io_path(inside(root,doc['data']['source_path'])).read_text(encoding='utf-8-sig')
   except (OSError,ValueError):continue
   baseline=doc['data'].get('source_baseline',doc['data'].get('original',''))
   media_changed=False
   if text==baseline and doc['data']['name']!='剧本.md':
    try:media_changed=bool(changed_sources(state,doc,source_info(state,root,[text],cached=True)))
    except (OSError,ValueError):pass
   if text!=baseline or media_changed:result.append({'id':doc['id'],'name':doc['data']['source_path'],'episode':doc['data']['parent_id'],'media_changed':media_changed})
  result.extend({'id':d['id'],'name':d['data']['source_path'],'episode':d['data']['parent_id'],'new':True} for d in new_sources(state,root))
  return result
 def preview(self,project,document):
  store=self.library.project(project);state=store.state();root=self.discovery.source_for(project)
  state={**state,'entities':state['entities']+new_sources(state,root)}
  if any(e['id']==document and e['data'].get('name')=='分镜.md' for e in state['entities']):
   return StoryboardSync(self.library,self.discovery).preview(project,document)
  if any(e['id']==document and e['data'].get('name') in SUPPORTED for e in state['entities']):
   return DocumentSync(self.library,self.discovery).preview(project,document)
  doc=next((e for e in state['entities'] if e['id']==document and e['kind']=='document' and e['data'].get('name')=='剧本.md'),None)
  if root is None or not doc:raise ValueError('没有可读取的外部剧本来源')
  text=io_path(inside(root,doc['data']['source_path'])).read_text(encoding='utf-8-sig')
  episode=next(e for e in state['entities'] if e['id']==doc['data']['parent_id'])
  code=episode['data'].get('code','EP001')
  base={e['code']:e for e in parse_script(doc['data'].get('source_baseline',doc['data'].get('original','')),code)}
  remote={e['code']:e for e in parse_script(text,code)}
  scenes=[e for e in state['entities'] if e['kind']=='scene' and e['data'].get('parent_id')==episode['id']]
  current={e['data']['code']:e for e in scenes if e['data'].get('code')}
  if len(current)!=sum(bool(e['data'].get('code')) for e in scenes):raise ValueError('当前项目场次编号不明确，请先检查分场')
  changes=[]
  for identity,scene in remote.items():
   existing=current.get(identity);previous=base.get(identity)
   if existing is None:
    if previous==scene:continue
    changes.append({'key':identity+':add','kind':'add','code':identity,'name':scene['name'],'source':scene,'current':None,'conflict':previous is not None});continue
   for field in ('name','text','order'):
    incoming=scene[field];old=previous.get(field) if previous else None;local=existing['data'].get(field)
    if incoming==old or incoming==local:continue
    changes.append({'key':identity+':'+field,'kind':'update','id':existing['id'],'code':identity,'name':scene['name'],
      'field':field,'before':old,'current':local,'source':incoming,'conflict':local!=old})
  for identity in base.keys()-remote.keys():
   if identity in current:changes.append({'key':identity+':removed','kind':'removed','code':identity,'name':current[identity]['data']['name'],'conflict':True})
  return {'revision':state['project']['revision'],'document':document,'episode':episode['id'],'source_hash':hashlib.sha256(text.encode('utf8')).hexdigest(),'changes':changes}
 def apply(self,project,document,revision,source_hash,choices):
  state=self.library.project(project).state()
  candidate=next((d for d in new_sources(state,self.discovery.source_for(project)) if d['id']==document),None)
  if candidate:
   owner=StoryboardSync if candidate['data']['name']=='分镜.md' else DocumentSync
   return owner(self.library,self.discovery).apply(project,document,revision,source_hash,choices)
  if any(e['id']==document and e['data'].get('name')=='分镜.md' for e in self.library.project(project).state()['entities']):
   return StoryboardSync(self.library,self.discovery).apply(project,document,revision,source_hash,choices)
  if any(e['id']==document and e['data'].get('name') in SUPPORTED for e in self.library.project(project).state()['entities']):
   return DocumentSync(self.library,self.discovery).apply(project,document,revision,source_hash,choices)
  preview=self.preview(project,document);store=self.library.project(project)
  if preview['revision']!=revision:raise Conflict(store.state())
  if preview['source_hash']!=source_hash:raise ValueError('外部剧本又有更新，请重新查看差异')
  operations=[]
  for change in preview['changes']:
   choice=choices.get(change['key'],None if change['conflict'] else 'source')
   if choice not in ('current','source'):raise ValueError('请先选择如何处理冲突')
   if change['kind']=='removed':
    if choice!='current':raise ValueError('外部删除的场次需保留现有镜头，请选择保留当前场次')
    continue
   if choice=='current':continue
   if change['kind']=='add':operations.append({'type':'create','id':str(uuid4()),'kind':'scene','data':{**change['source'],'parent_id':preview['episode']}})
   else:operations.append({'type':'update','id':change['id'],'patch':{change['field']:change['source']}})
  root=self.discovery.source_for(project);doc=next(e for e in store.state()['entities'] if e['id']==document)
  text=io_path(inside(root,doc['data']['source_path'])).read_text(encoding='utf-8-sig')
  if hashlib.sha256(text.encode('utf8')).hexdigest()!=source_hash:raise ValueError('外部剧本又有更新，请重新查看差异')
  operations.append({'type':'update','id':document,'patch':{'source_baseline':text}})
  return store.apply(revision,operations,actor='external-script-merge')
