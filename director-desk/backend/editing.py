"""Create the first OpenFilm timeline from explicitly adopted video versions."""
import json
import math
import os
import re
from pathlib import Path
import shutil
import subprocess
import threading
from uuid import uuid4
from store import Conflict
from project_settings import edit_format
from skill_paths import skills_root

class Editing:
    def __init__(self,library,runtime=None):
        self.library=library;self.runtime=runtime;self.lock=threading.Lock()

    def probe(self,path):
        executable=shutil.which('ffprobe')
        if not executable:raise ValueError('未找到视频读取工具 ffprobe，请完成本机运行时安装')
        result=subprocess.run([executable,'-v','error','-select_streams','v:0','-show_entries',
            'stream=width,height,avg_frame_rate:format=duration','-of','json',str(path)],
            capture_output=True,text=True,encoding='utf8',timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        if result.returncode:raise ValueError('无法读取已采用视频：'+path.name)
        data=json.loads(result.stdout);stream=next(iter(data.get('streams',[])),{})
        duration=float(data.get('format',{}).get('duration',0))
        if not math.isfinite(duration) or duration<=0 or not stream.get('width') or not stream.get('height'):
            raise ValueError('已采用素材缺少有效视频画面或时长')
        return {'duration':duration,'width':stream['width'],'height':stream['height']}

    def plan(self,project,episode_id):
        store=self.library.project(project);state=store.state();entities={e['id']:e for e in state['entities']}
        episode=entities.get(episode_id)
        if not episode or episode['kind']!='episode':raise ValueError('剧集不存在')
        scenes=sorted([e for e in entities.values() if e['kind']=='scene' and e['data'].get('parent_id')==episode_id],key=lambda e:e['data'].get('order',0))
        shots=[]
        for scene in scenes:
            shots.extend(sorted([e for e in entities.values() if e['kind']=='shot' and e['data'].get('parent_id')==scene['id']],key=lambda e:e['data'].get('order',0)))
        order={e['id']:i for i,e in enumerate(shots)};covered=set();units=[]
        for unit in entities.values():
            if unit['kind']!='submission' or unit['data'].get('parent_id')!=episode_id or not unit['data'].get('adopted_media'):continue
            if any(s not in order for s in unit['data'].get('shot_ids',[])):
                raise ValueError('生成单元含其他集或已移除的镜头，请重新关联分镜：'+unit['data'].get('name',''))
            members=[s for s in unit['data'].get('shot_ids',[]) if s in order]
            if not members:raise ValueError('请先为已采用的生成单元关联分镜：'+unit['data'].get('name',''))
            if covered.intersection(members):raise ValueError('同一镜头被多个采用单元覆盖，请先确定采用版本')
            covered.update(members);units.append((min(order[s] for s in members),unit,members))
        for shot in shots:
            if shot['id'] not in covered and shot['data'].get('adopted_media'):
                units.append((order[shot['id']],shot,[shot['id']]));covered.add(shot['id'])
        entries=[];clock=0
        for _,owner,members in sorted(units,key=lambda row:row[0]):
            media=entities.get(owner['data']['adopted_media'])
            if not media or media['kind']!='media' or media['data'].get('type')!='video':
                raise ValueError('请为镜头采用视频回片：'+owner['data'].get('name',''))
            path=self.library.file(project,media['id']);info=self.probe(path)
            entries.append({'owner':owner['id'],'name':owner['data'].get('name',''),'media':media['id'],
                'shots':members,'shot_codes':[entities[s]['data'].get('code',s) for s in members],
                'motion_code':owner['data'].get('code','') if owner['kind']=='submission' else '',
                'at':round(clock,6),**info})
            clock+=info['duration']
        return {'revision':state['project']['revision'],'episode':episode_id,'entries':entries,
                'format':edit_format(state,entries[0]['width'],entries[0]['height']) if entries else None,
                'duration':round(clock,3),'missing':len(shots)-len(covered),'existing':episode['data'].get('film_path'),
                'code':episode['data'].get('code','EP001')}

    def initialize(self,folder,seed):
        roots=[skills_root()]
        cli=next((r/'short-drama-edit/scripts/openfilm/cli.mjs' for r in roots if (r/'short-drama-edit/scripts/openfilm/cli.mjs').is_file()),None)
        if not cli or not shutil.which('node'):raise ValueError('请先安装短剧剪辑运行时与 Node.js')
        payload=folder/'.short-drama/initial-seed.json';payload.parent.mkdir(parents=True,exist_ok=True)
        payload.write_text(json.dumps(seed,ensure_ascii=False),encoding='utf8')
        result=subprocess.run(['node',str(cli),'init','--root',str(folder),'--input',str(payload)],
            env=self.runtime.environment() if self.runtime else None,
            capture_output=True,text=True,encoding='utf8',errors='replace',timeout=90,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        if result.returncode:
            (folder/'.short-drama/initialization.log').write_text(result.stderr,encoding='utf8')
            raise ValueError('剪辑工程初始化未完成，请检查本机 OpenFilm 运行时')

    def create(self,project,episode_id,revision):
        with self.lock:
            store=self.library.project(project);plan=self.plan(project,episode_id)
            if plan['revision']!=revision:raise Conflict(store.state())
            if plan['existing']:return store.state()
            if not plan['entries']:raise ValueError('先在视频制作中采用至少一个视频版本')
            code=plan['code'] if re.fullmatch(r'EP\d+',plan['code']) else 'EP001'
            folder=store.root/'editing'/uuid4().hex/code;(folder/'assets').mkdir(parents=True)
            clips=[]
            for entry in plan['entries']:
                source=self.library.file(project,entry['media']);relative='assets/'+entry['media']+source.suffix.lower()
                shutil.copy2(source,folder/relative)
                attrs={'data-shot-id':entry['shot_codes'][0],'data-sd-shot-ids':json.dumps(entry['shot_codes']),
                       'data-sd-media-id':entry['media'],'data-sd-intent':'采用素材全长初剪，待按表演精修'}
                if entry['motion_code']:attrs['data-motion-id']=entry['motion_code']
                clips.append({'id':'CUT-'+entry['owner'],'src':relative,'time':[0,entry['duration']],
                              'at':entry['at'],'volume':1,'attrs':attrs})
            format=plan['format']
            self.initialize(folder,{'fps':format['fps'],'film':{'stage':{'w':format['width'],'h':format['height']},'tracks':[{'clips':clips}]}})
            if not (folder/'film.html').is_file():raise ValueError('没有生成有效剪辑工程')
            return store.apply(revision,[{'type':'update','id':episode_id,'patch':{'film_path':(folder/'film.html').relative_to(store.root).as_posix()}}],actor='initial-edit')
