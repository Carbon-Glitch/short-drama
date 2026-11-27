from creative_context import context_ids, project_context
"""Bridge structured generation entries to the existing production_tool protocol."""
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import threading
import time
from uuid import uuid4

from documents import render_document
from project_settings import to_config,settings,model_presets
from store import encoded
from skill_paths import skills_root
from transfer import inside


def filesystem_path(path):
    path=Path(path).resolve()
    if os.name=='nt' and not str(path).startswith('\\\\?\\'):
        return Path('\\\\?\\'+str(path))
    return path


def production_tool():
    roots=[skills_root()]
    file=next((root/'short-drama-produce/scripts/production_tool.py' for root in roots
               if (root/'short-drama-produce/scripts/production_tool.py').is_file()),None)
    if not file:raise ValueError('未找到短剧生产工具，请完成运行时安装')
    spec=importlib.util.spec_from_file_location('director_production_tool',file)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


class Production:
    def __init__(self,library,adapter_config=None):
        self.library=library
        self.config=Path(adapter_config or os.environ.get('DIRECTOR_ADAPTER_CONFIG',library.home/'adapters.json'))
        self.tool=production_tool()
        self.active=set()
        self.lock=threading.Lock()

    def profiles(self):
        if not self.config.is_file():return []
        config=json.loads(self.config.read_text(encoding='utf-8-sig'))
        return [{'id':name,'name':v.get('name',name),'kind':v.get('kind'),'provider':v.get('provider'),'reference_roles':v.get('reference_roles',[])} for name,v in config.get('adapters',{}).items()]

    def service_details(self,adapter):
        config=json.loads(self.config.read_text(encoding='utf-8-sig'))
        definition=config.get('adapters',{}).get(adapter)
        if not definition:raise ValueError('生成服务配置不可用，请重新选择服务')
        provider=definition.get('provider') or (adapter[9:] if adapter.startswith('director-') else None)
        runtime=self.library.home/'runtime-settings.json'
        settings=json.loads(runtime.read_text(encoding='utf8')).get('providers',{}).get(provider) if runtime.is_file() and provider else None
        if settings and provider in ('seedance','minimax-h3'):
            model='seedance-2.5' if provider=='seedance' else provider
            preset=next((p for p in model_presets() if p['id']==model),None)
            if preset:settings={**settings,'execution_profile':preset['choices']}
        return {'adapter':definition,'provider':provider,'settings':settings}

    @staticmethod
    def service_revision(details):
        return hashlib.sha256(encoded(details).encode('utf8')).hexdigest()

    def freeze_service(self,identity,adapter,expected):
        details=self.service_details(adapter)
        if self.service_revision(details)!=expected:raise ValueError('生成服务或模型配置已改变，请重新查看提交预览')
        folder=self.library.home/'state/service-snapshots'/identity;folder.mkdir(parents=True,exist_ok=True)
        definition=details['adapter'];command=definition.get('command',[])
        if len(command)>=4 and Path(command[1]).name=='runtime_adapter.py':
            if not details['settings']:raise ValueError('服务凭据不可用，请重新配置')
            runtime=folder/'runtime-settings.json'
            runtime.write_text(encoded({'providers':{details['provider']:details['settings']}}),encoding='utf8')
            definition={**definition,'command':[command[0],command[1],str(runtime),*command[3:]]}
        snapshot=folder/'adapters.json';snapshot.write_text(encoded({'adapters':{adapter:definition}}),encoding='utf8')
        return snapshot

    def store(self,project):
        store=self.library.project(project)
        with store.connection() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS generation_job(
                id TEXT PRIMARY KEY,source_id TEXT NOT NULL,basis TEXT NOT NULL,workspace TEXT NOT NULL,
                preview TEXT NOT NULL,status TEXT NOT NULL,result TEXT,error TEXT,created REAL NOT NULL)''')
        return store

    @staticmethod
    def decoded(row):
        return {**dict(row),'basis':json.loads(row['basis']),'preview':json.loads(row['preview']),
                'result':json.loads(row['result']) if row['result'] else None}

    def list(self,project):
        store=self.store(project)
        with store.connection() as db:return [self.decoded(r) for r in db.execute('SELECT * FROM generation_job ORDER BY created DESC')]

    def prepare(self,project,source_id,adapter,parameters):
        if adapter not in {p['id'] for p in self.profiles()}:raise ValueError('请先配置可用的生成服务')
        service=self.service_details(adapter);service_revision=self.service_revision(service)
        store=self.store(project);state=store.state();entities={e['id']:e for e in state['entities']}
        source=entities.get(source_id)
        if not source or source['kind'] not in ('submission','image_prompt'):raise ValueError('请选择图片或视频提示词条目')
        profile=next(p for p in self.profiles() if p['id']==adapter)
        project_profile=settings(state).get('production_profile',{})
        target=project_profile.get('choices',{}).get('target_video_model') if project_profile.get('status')=='accepted' else None
        normalize=lambda model:'seedance' if model in ('seedance','seedance-2.5') else model
        if source['kind']=='submission' and normalize(target) in ('minimax-h3','seedance') and normalize(profile.get('provider')) in ('minimax-h3','seedance') and normalize(target)!=normalize(profile['provider']):
            raise ValueError('生成服务与作品目标模型不一致，请选择匹配服务；切换模型请先更新作品规格与提示词。')
        if profile.get('kind') and profile['kind']!=('image' if source['kind']=='image_prompt' else 'video'):raise ValueError('请选择与素材类型匹配的生成服务')
        if not source['data'].get('code'):raise ValueError('条目还没有生成编号')
        doc=entities.get(source['data'].get('document_id'));ep=entities.get(source['data'].get('parent_id'))
        if not doc or not ep or ep['kind']!='episode':raise ValueError('条目所属剧集或文档不完整')
        code=ep['data'].get('code','EP001')
        if not re.fullmatch(r'EP\d+',code):raise ValueError('剧集编号无效')
        document=render_document(state,doc)
        section=self.tool._markdown_section(document,source['data']['code'])
        inputs=self.tool.entry_inputs(section, field='参考' if source['kind']=='image_prompt' else '输入参考图',
            is_video=source['kind']=='submission', declared=source['data'].get('generation_mode',''),
            provider=profile.get('provider',''), adapter=adapter)
        prompt=inputs['prompt'];bindings=inputs['bindings'];mode=inputs['mode']
        input_scope=context_ids(state,{source_id},'video-prompts' if source['kind']=='submission' else 'production')
        missing=sorted({code for i in input_scope for code in entities[i]['data'].get('unresolved_design_codes',[])})
        if missing:raise ValueError('设计承接未找到：'+', '.join(missing))
        identity=uuid4().hex;workspace_relative='.short-drama/state/production/'+identity
        workspace=filesystem_path(store.root/workspace_relative);workspace.mkdir(parents=True)
        (workspace/'short-drama.json').write_text(encoded(to_config(state)),encoding='utf8')
        from transfer import project_markdown, subset
        project_markdown(workspace,subset(state,ep['id']))
        relative=f'剧集/{code}/{doc["data"]["name"]}'
        target=inside(workspace,relative);target.parent.mkdir(parents=True,exist_ok=True);target.write_text(document,encoding='utf8')
        for binding in bindings:
            live=inside(store.root,binding['path'])
            if not live.is_file():live=inside(store.root,'source/'+binding['path'])
            if not live.is_file():raise ValueError('缺少参考素材：'+binding['label'])
            target=inside(workspace,binding['path']);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(live,target)
        modality='image' if source['kind']=='image_prompt' else 'video'
        parameters=dict(parameters or {})
        specification=settings(state)
        parameters.setdefault('ratio',(specification.get('format',{}).get('aspect_ratio') or '9:16'))
        seedance=profile.get('provider') in ('seedance','seedance-2.5') or adapter=='director-seedance'
        if modality=='video' and seedance:
            parameters.pop('resolution',None)  # This installed adapter does not expose resolution control.
            if mode in ('first_frame','first_last_frame'):parameters['ratio']='adaptive'
        profile_choices=specification.get('production_profile',{}).get('choices',{}) if specification.get('production_profile',{}).get('status')=='accepted' else {}
        parameters.setdefault('prompt_language',profile_choices.get('video_prompt_language') if modality=='video' and profile_choices.get('video_prompt_language') else specification.get('format',{}).get('prompt_language',specification.get('language','zh-CN')))
        if modality=='video' and 'duration' not in parameters:
            duration=re.search(r'^- (?:时长|总时长)：\s*(\d+(?:\.\d+)?)\s*(?:s|秒)',section,re.M)
            if not duration:raise ValueError('请在生成设置中填写时长')
            value=float(duration[1]);parameters['duration']=int(value) if value.is_integer() else value
        output=f'剧集/{code}/制作成果/{modality}/{identity}'+('.png' if modality=='image' else '.mp4')
        job={'schema_version':'1.0','job_id':identity,'modality':modality,'adapter':adapter,'prompt':prompt,
             'source':relative,'source_entry':source['data']['code'],'reference_bindings':bindings,
             'references':[b['path'] for b in bindings],'outputs':[output],'parameters':parameters,'overwrite':False}
        preview=self.tool.prepare_payload(workspace,job)
        if self.service_revision(self.service_details(adapter))!=service_revision:raise ValueError('服务配置在准备期间发生变化，请重新预览')
        preview['service_revision']=service_revision
        preview['service_model']=(service.get('settings') or {}).get('model','')
        preview['reference_mode']=mode
        preview['ratio_from_first_frame']=bool(seedance and mode in ('first_frame','first_last_frame'))
        preview['frame_images_as_references']=inputs['frame_images_as_references']
        related=context_ids(state,{source_id},'video-prompts' if modality=='video' else 'production')
        basis={i:entities[i]['revision'] for i in related}
        context={'schema':1,'source_id':source_id,'source_shot_ids':list(source['data'].get('shot_ids',[])),
                 'basis':basis,'project':project_context(state,related)}
        (workspace/'creative-context.json').write_text(encoded(context),encoding='utf8')
        preview['creative_context']={'path':workspace_relative+'/creative-context.json',
            'shot_ids':context['source_shot_ids'],
            'design_codes':[entities[i]['data']['code'] for i in sorted(related) if entities[i]['kind']=='design' and entities[i]['data'].get('code')]}
        with store.connection() as db:
            db.execute('INSERT INTO generation_job VALUES(?,?,?,?,?,?,?,?,?)',
                (identity,source_id,encoded(basis),workspace_relative,encoded(preview),'prepared',None,None,time.time()))
        return self.list(project)[0]

    def context(self,project,identity):
        job=next((j for j in self.list(project) if j['id']==identity),None)
        if not job:raise ValueError('生成记录不存在')
        path=filesystem_path(self.store(project).root/job['workspace']/'creative-context.json')
        return {'created':job['created'],'status':job['status'],
                'context':json.loads(path.read_text(encoding='utf8')) if path.is_file() else None}

    def submit(self,project,identity,asynchronous=True):
        store=self.store(project)
        with store.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT * FROM generation_job WHERE id=?',(identity,)).fetchone()
            if not row or row['status']!='prepared':raise ValueError('任务已提交或尚未准备')
            job=self.decoded(row);state=store._state(db);entities={e['id']:e for e in state['entities']}
            if job['preview']['adapter'] not in {p['id'] for p in self.profiles()}:raise ValueError('生成服务配置不可用，请先恢复配置')
            if any(i not in entities or entities[i]['revision']!=revision for i,revision in job['basis'].items()):
                raise ValueError('输入内容已经修改，请重新准备任务')
            self.freeze_service(identity,job['preview']['adapter'],job['preview'].get('service_revision'))
            self.tool.confirm_job(filesystem_path(store.root/job['workspace']),job_id=identity,confirmation=job['preview']['confirmation'])
            db.execute("UPDATE generation_job SET status='running' WHERE id=?",(identity,))
        if asynchronous:
            with self.lock:self.active.add(identity)
            threading.Thread(target=self.execute,args=(project,identity),daemon=True).start()
            return {'status':'running'}
        return self.execute(project,identity)

    def execute(self,project,identity,collect=False):
        store=self.store(project);job=next(j for j in self.list(project) if j['id']==identity)
        workspace=filesystem_path(store.root/job['workspace'])
        try:
            snapshot=self.library.home/'state/service-snapshots'/identity/'adapters.json'
            if not snapshot.is_file() and not collect:raise ValueError('本机提交配置已失效，请重新准备任务')
            adapter_config=snapshot if snapshot.is_file() else self.config
            result=(self.tool.collect_job if collect else self.tool.run_job)(workspace,job_id=identity,adapter_config=adapter_config)
            status=self.tool.job_status(workspace,job_id=identity)
            outputs=status.get('latest_run',{}).get('outputs',[])
            state=store.state()
            context_path=workspace/'creative-context.json'
            context=json.loads(context_path.read_text(encoding='utf8')) if context_path.is_file() else {}
            # Legacy jobs have no frozen coverage; do not invent it from a changed live unit.
            original_shots=context.get('source_shot_ids',[])
            shot_ids=[i for i in original_shots if any(e['id']==i for e in state['entities'])]
            paths=[workspace/o['path'] for o in outputs]
            provenance={'job_id':identity,'source_id':job['source_id'],'shot_ids':original_shots,
                'basis':job['basis'],'creative_context':job['preview'].get('creative_context')}
            updated=self.library.add_media(project,paths,state['project']['revision'],shot_ids[0] if len(shot_ids)==1 else None,production=provenance)
            media=[e['id'] for e in updated['entities'] if e['kind']=='media' and e['revision']==updated['project']['revision']]
            result={'media':media,'provider':status.get('latest_run',{}).get('provider_job_id'),'source_id':job['source_id']}
            with store.connection() as db:db.execute("UPDATE generation_job SET status='succeeded',result=?,error=NULL WHERE id=?",(encoded(result),identity))
            return result
        except Exception as error:
            with store.connection() as db:db.execute("UPDATE generation_job SET status='failed',error=? WHERE id=?",(str(error)[:1500],identity))
            return {'error':str(error)}
        finally:
            with self.lock:self.active.discard(identity)

    def collect(self,project,identity):
        job=next((j for j in self.list(project) if j['id']==identity),None)
        if not job or job['status'] not in ('running','failed','collecting'):raise ValueError('没有可取回的任务')
        with self.lock:
            if identity in self.active:raise ValueError('任务仍在执行，无需重复取回')
            self.active.add(identity)
        with self.store(project).connection() as db:db.execute("UPDATE generation_job SET status='collecting' WHERE id=?",(identity,))
        threading.Thread(target=self.execute,args=(project,identity,True),daemon=True).start()
        return {'status':'collecting'}
