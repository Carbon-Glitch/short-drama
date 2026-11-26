"""Visual reference selection compiles through the existing Skill binding grammar."""
import re
from store import Conflict
from reference_media import resolve

PURPOSES={
 '身份':('主体外观、身份','背景、姿态、表情'),
 '造型':('服装、配饰、材质','人物身份、动作、背景'),
 '场景':('空间结构、环境材质、光源位置','人物身份、动作、机位'),
 '风格':('色彩、影调、媒介肌理','主体身份、剧情'),
 '构图':('景别、布局、机位','主体身份、材质'),
 '细节':('指定局部形制与材质','整体构图、其他部位'),
}
class PromptReferences:
 def __init__(self,library,tool):self.library=library;self.tool=tool
 def context(self,project,identity):
  store=self.library.project(project);state=store.state();entry=next((e for e in state['entities'] if e['id']==identity and e['kind'] in ('image_prompt','submission')),None)
  if not entry:raise ValueError('请选择图片创作条目')
  images=[e for e in state['entities'] if e['kind']=='media' and e['data'].get('type')=='image']
  text=entry['data'].get('text','');field='参考' if entry['kind']=='image_prompt' else '输入参考图';line=re.search(r'^- '+field+r'：([^\n]*)$',text,re.M);old={}
  for match in self.tool.REFERENCE_LINE_RE.finditer(line[1] if line else ''):
   image=resolve(state,match[3],entry['data'].get('references',[]))
   if image:
    purpose=re.search(r'用途：([^；）]+)',match[0]);purpose=purpose[1] if purpose else '自定义'
    old[image['id']]={'raw':match[0],'purpose':purpose if purpose in (*PURPOSES,'起始帧','结束帧') else '自定义'}
  return store,state,entry,images,old
 def describe(self,project,identity):
  _,state,_,images,old=self.context(project,identity)
  return {'revision':state['project']['revision'],'choices':[{'media_id':identity,'purpose':v['purpose']} for identity,v in old.items()],
          'images':[{'id':e['id'],'name':e['data']['name']} for e in images],'purposes':list(PURPOSES)}
 def update(self,project,identity,choices,revision):
  store,state,entry,images,old=self.context(project,identity)
  if entry['kind']!='image_prompt':raise ValueError('请使用视频参考选择入口')
  if state['project']['revision']!=revision:raise Conflict(state)
  if not isinstance(choices,list):raise ValueError('参考选择无效')
  selected=[];lines=[]
  for order,choice in enumerate(choices,1):
   mid=choice['media_id'];purpose=choice.get('purpose','身份')
   image=next((e for e in images if e['id']==mid),None)
   if not image or mid in selected:raise ValueError('参考图片不存在或重复')
   self.library.file(project,mid);selected.append(mid)
   if mid in old and purpose==old[mid]['purpose']:
    lines.append(re.sub(r'（顺序：\d+）',f'（顺序：{order}）',old[mid]['raw'],count=1));continue
   if purpose not in PURPOSES:raise ValueError('请选择参考图用途')
   control,excluded=PURPOSES[purpose]
   name=re.sub(r'[《》\r\n]',' ',image['data']['name']).strip() or '参考图'
   if not re.search(r'[\u3400-\u9fff]',name):name='参考图 '+name
   slot='REF-'+re.sub(r'[^A-Za-z0-9-]','',mid).upper()
   lines.append(f'{slot}（顺序：{order}）· {image["data"]["path"]}《{name}》（用途：{purpose}；控制：{control}；不得控制：{excluded}）')
  declaration='- 参考：'+('；'.join(lines) if lines else '无')
  text=entry['data'].get('text','')
  if re.search(r'^- 参考：',text,re.M):text=re.sub(r'^- 参考：[^\n]*',lambda _:declaration,text,count=1,flags=re.M)
  else:text=declaration+'\n\n'+(text if text else '### 可复制提示词\n> ')
  operations=[{'type':'update','id':identity,'patch':{'text':text,'references':selected}}]
  for dep in state['dependencies']:
   if dep['target']==identity and dep['source'] in old and dep['source'] not in selected:
    operations.append({'type':'unbind','source':dep['source'],'target':identity})
  for mid in selected:
   if not any(d['source']==mid and d['target']==identity for d in state['dependencies']):operations.append({'type':'bind','source':mid,'target':identity,'fields':['sha256']})
  return store.apply(revision,operations,actor='reference-selection')
