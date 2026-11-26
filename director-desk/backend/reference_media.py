"""Resolve source aliases to immutable project media versions."""
import hashlib
import re
import shutil
from pathlib import Path
from uuid import uuid4
from functools import lru_cache

REFERENCE_PATH=re.compile(r'·\s*([^·；\n《》]+?\.(?:png|jpg|jpeg|webp|wav|mp3|m4a|mp4|webm|mov))《',re.I)

def paths(text):return list(dict.fromkeys(m[1].strip() for m in REFERENCE_PATH.finditer(text)))

def matches(media,path):
 data=media['data']
 return data.get('path') in (path,'source/'+path) or data.get('source_reference_path')==path

def resolve(state,path,preferred=()):
 candidates=[e for e in state['entities'] if e['kind']=='media' and matches(e,path)]
 selected=state.get('_source_media',{}).get(path)
 if selected:return next((e for e in candidates if e['id']==selected),None)
 chosen=[e for e in candidates if e['id'] in preferred]
 if len(chosen)==1:return chosen[0]
 if len(candidates)==1:return candidates[0]
 return next((e for e in candidates if e['data']['path'] in (path,'source/'+path)),None)

def render_paths(text,state,entry):
 def replace(match):
  path=match[1].strip();media=resolve(state,path,entry['data'].get('references',[]))
  return match[0].replace(match[1],media['data']['path']) if media else match[0]
 return ''.join(REFERENCE_PATH.sub(replace,line) if re.match(r'^\s*[-*]\s*(?:参考|输入参考图|参考音频|参考视频|资产图)[：:]',line) else line for line in text.splitlines(keepends=True))

@lru_cache(maxsize=256)
def cached_digest(path,stamp):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def source_info(state,root,bodies,cached=False):
 from transfer import inside
 from filesystem import io_path
 result=[]
 for path in dict.fromkeys(path for body in bodies for path in paths(body)):
  source=io_path(inside(root,path));digest=None
  if source.is_file():
   if cached:
    stat=source.stat();digest=cached_digest(str(source),(stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns))
   else:
    with source.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
  candidates=[e for e in state['entities'] if e['kind']=='media' and matches(e,path)]
  result.append({'path':path,'sha256':digest,'status':'existing' if any(e['data']['sha256']==digest for e in candidates) else 'updated' if candidates and digest else 'new' if digest else 'missing'})
 return result

def changed_sources(state,doc,info):
 baseline=doc['data'].get('source_media_baseline',{})
 preferred=[mid for e in state['entities'] if e['data'].get('document_id')==doc['id'] for mid in e['data'].get('references',[])]
 result=[]
 for item in info:
  media=resolve(state,item['path'],preferred)
  old=baseline.get(item['path'],media['data']['sha256'] if media else None)
  if item['sha256']!=old:result.append(item['path'])
 return result

def collect(store,state,source_root,bodies,expected=None):
 from transfer import inside
 from filesystem import io_path
 additions=[];mapping={}
 for path in dict.fromkeys(path for body in bodies for path in paths(body)):
  source=io_path(inside(source_root,path))
  if not source.is_file():
   existing=resolve(state,path)
   if existing:mapping[path]=existing['id'];continue
   raise ValueError('外部文档引用的素材尚未落盘：'+path)
  with source.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
  if expected is not None and path in expected and expected[path]!=digest:raise ValueError('参考素材又有更新，请重新查看差异：'+path)
  existing=next((e for e in state['entities']+additions if e['kind']=='media' and matches(e,path) and e['data']['sha256']==digest),None)
  if existing:mapping[path]=existing['id'];continue
  relative='media/'+digest+source.suffix.lower();target=io_path(store.root/relative);target.parent.mkdir(parents=True,exist_ok=True)
  if not target.is_file():shutil.copy2(source,target)
  with target.open('rb') as stream:
   if hashlib.file_digest(stream,'sha256').hexdigest()!=digest:raise ValueError('素材在复制期间变化，请重新同步：'+path)
  identity=str(uuid4());kind='image' if source.suffix.lower() in ('.png','.jpg','.jpeg','.webp') else 'video' if source.suffix.lower() in ('.mp4','.webm','.mov') else 'audio'
  additions.append({'id':identity,'kind':'media','data':{'name':Path(path).stem,'path':relative,'type':kind,'sha256':digest,'source_reference_path':path,'origin':'external-sync'}})
  mapping[path]=identity
 return {**state,'entities':state['entities']+additions,'_source_media':mapping},[{'type':'create',**e} for e in additions]
