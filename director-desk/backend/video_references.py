"""Video reference choices reuse the same media identities and Skill reference syntax."""
import re
from prompt_references import PromptReferences,PURPOSES
from store import Conflict
from project_settings import settings
from reference_media import resolve

MODES={'text':'文生视频','reference':'全能参考','first_frame':'首帧','first_last_frame':'首尾帧'}
def remap_mentions(text,old,selected,kind):
 old_order={int(re.search(r'（顺序：(\d+)）',value['raw'])[1]):mid for mid,value in old.items()}
 new_order={choice['media_id']:index+1 for index,choice in enumerate(selected)}
 pattern=r'<Picture\s+(\d+)>' if kind=='picture' else r'<Audio\s+(\d+)>'
 local_pattern=r'@图片(\d+)(?!\d)' if kind=='picture' else r'@音频(\d+)(?!\d)'
 def replace(match,local=False):
  number=int(match[1]);mid=old_order.get(number)
  if mid is None:return match[0]
  if mid not in new_order:raise ValueError('视频描述仍引用要移除的'+('画面' if kind=='picture' else '音色')+'，请先更新描述或保留该参考')
  return ('@图片' if kind=='picture' else '@音频')+str(new_order[mid]) if local else '<'+('Picture' if kind=='picture' else 'Audio')+' '+str(new_order[mid])+'>'
 parts=re.split(r'(<d>.*?</d>)',text,flags=re.S)
 for index in range(0,len(parts),2):
  parts[index]=re.sub(pattern,lambda match:replace(match),parts[index])
  parts[index]=re.sub(local_pattern,lambda match:replace(match,True),parts[index])
 return ''.join(parts)

class VideoReferences(PromptReferences):
 def video_context(self,project,identity):
  store,state,entry,images,old=self.context(project,identity)
  if entry['kind']!='submission':raise ValueError('请选择视频创作条目')
  sounds=[e for e in state['entities'] if e['kind']=='media' and e['data'].get('type')=='audio']
  line=re.search(r'^- 参考音频：([^\n]*)$',entry['data'].get('text',''),re.M);voices={}
  for match in self.tool.AUDIO_REFERENCE_LINE_RE.finditer(line[1] if line else ''):
   media=resolve(state,match[3],entry['data'].get('references',[]))
   if media:voices[media['id']]={'raw':match[0],'character':match[5]}
  purposes=[e['purpose'] for e in old.values()]
  mode=entry['data'].get('generation_mode')
  if mode not in MODES:mode='reference' if voices or any(p not in ('起始帧','结束帧') for p in purposes) else 'first_last_frame' if '结束帧' in purposes else 'first_frame' if purposes else 'text' if re.search(r'^- 生成方式：(文生视频|纯文本)',entry['data'].get('text',''),re.M) else 'reference'
  return store,state,entry,images,old,sounds,voices,mode
 def describe(self,project,identity):
  _,state,entry,images,old,sounds,voices,mode=self.video_context(project,identity)
  profile=settings(state).get('production_profile',{});model=profile.get('choices',{}).get('target_video_model') if profile.get('status')=='accepted' else None
  h3=model=='minimax-h3' or bool(re.search(r'(?m)^>\s*(?:subject_definitions|integrated_multimodal_description):',entry['data'].get('text','')))
  return {'revision':state['project']['revision'],'kind':'video','mode':mode,
   'choices':[{'media_id':mid,'purpose':value['purpose']} for mid,value in old.items()],
   'voices':[{'media_id':mid,'character':value['character']} for mid,value in voices.items()],
   'images':[{'id':e['id'],'name':e['data']['name']} for e in images],
   'audio':[{'id':e['id'],'name':e['data']['name']} for e in sounds],
   'characters':[e['data']['name'] for e in state['entities'] if e['kind']=='character' and e['data'].get('parent_id')==entry['data']['parent_id']],
   'voice_requires_image':h3,'purposes':list(PURPOSES)}
 def update(self,project,identity,choices,revision,mode,voices):
  store,state,entry,images,old,sounds,old_voices,_=self.video_context(project,identity)
  if state['project']['revision']!=revision:raise Conflict(state)
  if mode not in MODES:raise ValueError('请选择生成控制方式')
  if mode=='text' and (choices or voices):raise ValueError('纯文本模式不使用参考素材')
  if mode in ('first_frame','first_last_frame'):
   if voices:raise ValueError('首尾帧专用模式不同时使用音色参考')
   if len(choices)!=(1 if mode=='first_frame' else 2):raise ValueError('请选择完整的起始/结束画面')
  if voices and not choices and self.describe(project,identity)['voice_requires_image']:raise ValueError('当前H3模式的音色参考需要画面参考')
  selected=[];picture_lines=[];sound_lines=[]
  for index,choice in enumerate(choices):
   mid=choice['media_id'];media=next((e for e in images if e['id']==mid),None)
   if not media or mid in selected:raise ValueError('画面参考无效或重复')
   self.library.file(project,mid);selected.append(mid)
   purpose=('起始帧' if index==0 else '结束帧') if mode in ('first_frame','first_last_frame') else choice.get('purpose','身份')
   if mid in old and purpose==old[mid]['purpose']:raw=re.sub(r'（顺序：\d+）',f'（顺序：{index+1}）',old[mid]['raw'],count=1)
   else:
    if purpose in ('起始帧','结束帧'):control,excluded='该端点的姿态、构图、光影','未指定的动作过程'
    elif purpose in PURPOSES:control,excluded=PURPOSES[purpose]
    else:raise ValueError('请选择画面用途')
    label=re.sub(r'[《》\r\n]',' ',media['data']['name']);label=label if re.search(r'[\u3400-\u9fff]',label) else '素材 '+label;slot='REF-'+re.sub(r'[^A-Za-z0-9-]','',mid).upper()
    raw=f'{slot}（顺序：{index+1}）· {media["data"]["path"]}《{label}》（用途：{purpose}；控制：{control}；不得控制：{excluded}）'
   picture_lines.append(raw)
  for index,voice in enumerate(voices):
   mid=voice['media_id'];media=next((e for e in sounds if e['id']==mid),None);character=str(voice.get('character','')).strip()
   if not media or mid in selected:raise ValueError('音色参考无效或重复')
   if not character or re.search(r'[；）\r\n]',character):raise ValueError('请填写音色对应的角色')
   self.library.file(project,mid);selected.append(mid)
   if mid in old_voices and character==old_voices[mid]['character']:raw=re.sub(r'（顺序：\d+）',f'（顺序：{index+1}）',old_voices[mid]['raw'],count=1)
   else:
    label=re.sub(r'[《》\r\n]',' ',media['data']['name']);label=label if re.search(r'[\u3400-\u9fff]',label) else '素材 '+label;slot='REF-'+re.sub(r'[^A-Za-z0-9-]','',mid).upper()
    raw=f'{slot}（顺序：{index+1}）· {media["data"]["path"]}《{label}》（用途：音色；角色：{character}；控制：声纹；不得控制：台词、语气、情绪）'
   sound_lines.append(raw)
  text=entry['data'].get('text','') or '### 可复制提示词\n> '
  text=remap_mentions(remap_mentions(text,old,choices,'picture'),old_voices,voices,'audio')
  for field,value in [('生成方式',MODES[mode]),('输入参考图','；'.join(picture_lines) or '无'),('参考音频','；'.join(sound_lines) or '无')]:
   line='- '+field+'：'+value;pattern=r'^- '+field+r'：[^\n]*'
   text=re.sub(pattern,lambda _:line,text,count=1,flags=re.M) if re.search(pattern,text,re.M) else line+'\n'+text
  operations=[{'type':'update','id':identity,'patch':{'text':text,'references':selected,'generation_mode':mode}}]
  for dep in state['dependencies']:
   if dep['target']==identity and dep['source'] in {*old,*old_voices} and dep['source'] not in selected:operations.append({'type':'unbind','source':dep['source'],'target':identity})
  for mid in selected:
   if not any(d['source']==mid and d['target']==identity for d in state['dependencies']):operations.append({'type':'bind','source':mid,'target':identity,'fields':['sha256']})
  return store.apply(revision,operations,actor='video-reference-selection')
