"""Discover new stage documents only beside an episode's registered sources."""
from pathlib import PurePosixPath
from uuid import uuid5,NAMESPACE_URL
from documents import SUPPORTED
from transfer import inside

def new_sources(state,root):
 if root is None:return []
 docs=[e for e in state['entities'] if e['kind']=='document'];folders={}
 for doc in docs:
  path=doc['data'].get('source_path')
  if path:folders.setdefault(doc['data']['parent_id'],set()).add(str(PurePosixPath(path).parent))
 result=[]
 for episode,locations in folders.items():
  if len(locations)!=1:continue
  folder=next(iter(locations))
  for name in sorted(SUPPORTED|{'分镜.md'}):
   matching=[d for d in docs if d['data'].get('parent_id')==episode and d['data'].get('name')==name]
   if len(matching)>1 or (matching and matching[0]['data'].get('source_path')):continue
   relative=(PurePosixPath(folder)/name).as_posix()
   try:
    if not inside(root,relative).is_file():continue
   except ValueError:continue
   existing=matching[0] if matching else None
   identity=existing['id'] if existing else str(uuid5(NAMESPACE_URL,episode+':source-document:'+name))
   data={**(existing['data'] if existing else {'name':name,'parent_id':episode,'original':'','structured':True,'preamble':''}),
         'source_path':relative,'source_baseline':''}
   result.append({'id':identity,'kind':'document','data':data,'_new_source':True,'_create':not bool(existing)})
 return result
