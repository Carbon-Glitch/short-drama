"""Portable project specifications shared by UI, production and Markdown exports."""
from copy import deepcopy
import math
import re
import os
import json
from pathlib import Path
from uuid import uuid4
from skill_paths import skills_root

FORMAT_FIELDS=('aspect_ratio','prompt_language','episode_count','target_seconds_per_episode','pacing','fps','resolution')
MODEL_FIELDS=('target_video_model','video_prompt_dialect','video_prompt_language','native_duration_seconds','supported_generation_modes','audio_generation','multi_shot_containers')

def model_presets(skills=None):
    root=Path(skills) if skills else skills_root()
    result=[]
    for identity,label in [('minimax-h3','MiniMax H3'),('seedance-2.5','Seedance 2.5')]:
        path=root/f'short-drama-video-prompts/references/{identity}.md'
        if not path.is_file():continue
        for block in re.findall(r'```json\s*\n(.*?)\n```',path.read_text(encoding='utf-8-sig'),re.S):
            try:choices=json.loads(block)
            except ValueError:continue
            if isinstance(choices,dict) and choices.get('target_video_model')==identity:
                result.append({'id':identity,'name':label,'choices':{key:choices[key] for key in MODEL_FIELDS if key in choices}});break
    return result

def update_specification(store,revision,format,model=None,skills=None):
    from store import Conflict
    state=store.state()
    if state['project']['revision']!=revision:raise Conflict(state)
    if not isinstance(format,dict):raise ValueError('作品规格无效')
    spec=next((e for e in state['entities'] if e['kind']=='project_settings'),None)
    identity=spec['id'] if spec else str(uuid4());data=settings(state)
    patch={'format':{key:value for key,value in format.items() if key in FORMAT_FIELDS}}
    edit_format({'entities':[{'kind':'project_settings','data':{**data,**patch}}]},1080,1920)
    profile=data.get('production_profile',{});old=profile.get('choices',{}).get('target_video_model','') if profile.get('status')=='accepted' else ''
    changed=model is not None and model!=old
    if changed:
        preset=next((p for p in model_presets(skills) if p['id']==model),None)
        if model and not preset:raise ValueError('所选模型缺少已安装的提示词规范')
        choices=deepcopy(preset['choices']) if preset else {}
        if preset and 'multi_shot_containers' in profile.get('choices',{}):choices['multi_shot_containers']=profile['choices']['multi_shot_containers']
        patch['production_profile']={'status':'accepted' if model else 'unset','choices':choices}
    operations=[{'type':'update','id':identity,'patch':patch}] if spec else [{'type':'create','id':identity,'kind':'project_settings','data':{**data,**patch}}]
    if changed:
        for entity in state['entities']:
            if entity['kind'] not in ('shot','submission'):continue
            dependency=next((d for d in state['dependencies'] if d['source']==identity and d['target']==entity['id']),None)
            fields=[] if dependency and not dependency['fields'] else list(dict.fromkeys((dependency['fields'] if dependency else [])+['production_profile']))
            operations.append({'type':'bind','source':identity,'target':entity['id'],'fields':fields})
    return store.apply(revision,operations,actor='project-specification')

def from_config(config):
    format=config.get('format') or {}
    profile=(config.get('creator_authority') or {}).get('production_profile') or {}
    choices=profile.get('choices') or {}
    return {'language':config.get('language','zh-CN'),
            'format':deepcopy({key:format[key] for key in FORMAT_FIELDS if key in format}),
            'production_profile':{'status':profile.get('status','unset'),'choices':deepcopy({key:choices[key] for key in MODEL_FIELDS if key in choices})}}

def settings(state):
    return next((e['data'] for e in state['entities'] if e['kind']=='project_settings'),{'language':'zh-CN','format':{},'production_profile':{'status':'unset','choices':{}}})


def edit_format(state,width,height):
    """Use accepted project framing; never infer a new creative ratio from a take."""
    format=settings(state).get('format',{})
    fps=format.get('fps',24)
    if isinstance(fps,bool) or not isinstance(fps,(int,float)) or not math.isfinite(fps) or not 1<=fps<=120:
        raise ValueError('项目帧率需要是 1–120 之间的数字')
    ratio=format.get('aspect_ratio','')
    match=re.fullmatch(r'(\d+(?:\.\d+)?):(\d+(?:\.\d+)?)',str(ratio))
    if ratio and ratio!='adaptive' and not match:raise ValueError('请检查项目画幅，例如 16:9 或 9:16')
    if match:
        x,y=map(float,match.groups())
        if min(x,y)<=0:raise ValueError('项目画幅必须大于零')
        long=max(width,height)
        width=max(2,round(long*x/max(x,y)/2)*2)
        height=max(2,round(long*y/max(x,y)/2)*2)
    return {'fps':fps,'width':width,'height':height}

def to_config(state):
    data=settings(state)
    return {'schema_version':'1.0.0-draft','project_id':state['project']['id'],'title':state['project']['title'],
            'language':data.get('language','zh-CN'),'format':deepcopy(data.get('format',{})),
            'creator_authority':{'production_profile':deepcopy(data.get('production_profile',{'status':'unset','choices':{}}))},
            'postproduction':{'backend':'openfilm','authority':'film.html','report':'剪辑单.md'}}
