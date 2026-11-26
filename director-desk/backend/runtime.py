"""Machine-local service configuration, never part of a creative project."""
import base64
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import shutil
import sys
from urllib.parse import urlsplit
from project_settings import model_presets

import threading

_LOCK = threading.RLock()


def protect(value, decrypt=False):
    if os.name!='nt':raise ValueError('此系统请通过环境变量提供密钥')
    class Blob(ctypes.Structure):
        _fields_=[('size',wintypes.DWORD),('data',ctypes.POINTER(ctypes.c_ubyte))]
    raw=base64.b64decode(value) if decrypt else value.encode('utf8')
    buffer=ctypes.create_string_buffer(raw);source=Blob(len(raw),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_ubyte)));target=Blob()
    crypt=ctypes.WinDLL('crypt32', use_last_error=True)
    signature=[ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(Blob)]
    crypt.CryptProtectData.argtypes=signature;crypt.CryptProtectData.restype=wintypes.BOOL
    crypt.CryptUnprotectData.argtypes=signature;crypt.CryptUnprotectData.restype=wintypes.BOOL
    kernel=ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.LocalFree.argtypes=[ctypes.c_void_p];kernel.LocalFree.restype=ctypes.c_void_p
    if decrypt:ok=crypt.CryptUnprotectData(ctypes.byref(source),None,None,None,None,0,ctypes.byref(target))
    else:ok=crypt.CryptProtectData(ctypes.byref(source),None,None,None,None,0,ctypes.byref(target))
    if not ok:raise ValueError('无法保存本机密钥')
    try:
        data=ctypes.string_at(target.data,target.size)
        return data.decode('utf8') if decrypt else base64.b64encode(data).decode('ascii')
    finally:kernel.LocalFree(target.data)


def codex_command():
    executable=shutil.which('codex.exe') or shutil.which('codex') or shutil.which('codex.cmd')
    if not executable:return None
    if Path(executable).suffix.lower() in ('.cmd','.ps1'):
        script=Path(executable).parent/'node_modules/@openai/codex/bin/codex.js'
        node=shutil.which('node')
        return [node,str(script)] if script.is_file() and node else None
    return [executable]


class Runtime:
    def __init__(self,home):
        self.home=Path(home);self.file=self.home/'runtime-settings.json'

    def read(self):
        return json.loads(self.file.read_text(encoding='utf8')) if self.file.is_file() else {'agent_enabled':False,'providers':{}}

    def public(self):
        data=self.read()
        return {'agent_available':bool(codex_command()),'agent_enabled':bool(data.get('agent_enabled')),
                'providers':[{k:v for k,v in provider.items() if k!='key'}|{'provider':name,'key_configured':bool(provider.get('key'))}
                             for name,provider in data.get('providers',{}).items()]}

    def save(self,value):
        with _LOCK:
            return self._save(value)

    def _save(self,value):
        data=self.read()
        if 'agent_enabled' in value:
            if not isinstance(value['agent_enabled'],bool):raise ValueError('Agent开关无效')
            if value['agent_enabled'] and not codex_command():raise ValueError('未检测到Codex CLI，请先安装并登录')
            data['agent_enabled']=value['agent_enabled']
        if 'provider' in value:
            name=value['provider']
            if name not in ('minimax-h3','seedance','gpt-image-2'):raise ValueError('不支持的服务')
            previous=data.setdefault('providers',{}).get(name,{})
            model=str(value.get('model','')).strip()
            if name!='gpt-image-2' and not model:raise ValueError('请输入账户可用的模型ID')
            endpoint=str(value.get('base_url','')).strip()
            if endpoint:
                parsed=urlsplit(endpoint)
                if parsed.scheme not in ('https','http') or not parsed.hostname or parsed.username or parsed.password:raise ValueError('API地址无效')
            key=protect(value['api_key']) if value.get('api_key') else previous.get('key')
            if not key:raise ValueError('请输入API密钥')
            data['providers'][name]={'model':model,'base_url':endpoint,'key':key}
        self.home.mkdir(parents=True,exist_ok=True)
        temporary=self.file.with_suffix('.tmp');temporary.write_text(json.dumps(data,ensure_ascii=False),encoding='utf8');temporary.replace(self.file)
        self.write_adapters(data)
        return self.public()

    def write_adapters(self,data):
        path=self.home/'adapters.json'
        config=json.loads(path.read_text(encoding='utf8')) if path.exists() else {'adapters':{}}
        for name in data.get('providers',{}):
            config.setdefault('adapters',{})['director-'+name]={'command':[sys.executable,str(Path(__file__).with_name('runtime_adapter.py')),str(self.file),name],
                'timeout_seconds':3600,'name':{'minimax-h3':'MiniMax H3','seedance':'Seedance','gpt-image-2':'GPT Image'}[name],
                'kind':'image' if name=='gpt-image-2' else 'video','provider':name,
                'reference_roles':['reference_image'] if name=='gpt-image-2' else ['first_frame','last_frame','reference_image','reference_video','reference_audio']}
        temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(config,ensure_ascii=False),encoding='utf8');temporary.replace(path)

    def environment(self,name):
        config=self.read().get('providers',{}).get(name)
        if not config:raise ValueError('服务未配置')
        env=dict(os.environ)
        if name=='minimax-h3':
            duration=config.get('execution_profile',{}).get('native_duration_seconds',{'min':4,'max':15})
            env.update(MINIMAX_API_KEY=protect(config['key'],True),MINIMAX_VIDEO_MODEL=config['model'],
                       MINIMAX_VIDEO_MIN_DURATION=str(duration['min']),MINIMAX_VIDEO_MAX_DURATION=str(duration['max']),MINIMAX_VIDEO_RESOLUTIONS='768P,2K')
            endpoint='MINIMAX_VIDEO_BASE_URL'
        elif name=='seedance':
            env.update(ARK_API_KEY=protect(config['key'],True),SEEDANCE_MODEL=config['model']);endpoint='SEEDANCE_BASE_URL'
            execution_profile=config.get('execution_profile')
            if not execution_profile:
                preset=next((p for p in model_presets() if p['id']=='seedance-2.5'),None)
                if not preset:raise ValueError('缺少已安装的 Seedance 2.5 模型档案')
                execution_profile=preset['choices']
            duration=execution_profile['native_duration_seconds']
            env.update(SEEDANCE_MIN_DURATION=str(duration['min']),SEEDANCE_MAX_DURATION=str(duration['max']),
                       SEEDANCE_ALLOWED_RATIOS='adaptive,1:1,3:4,4:3,9:16,16:9,21:9')
        else:
            env['OPENAI_API_KEY']=protect(config['key'],True);endpoint='OPENAI_BASE_URL'
        if config.get('base_url'):env[endpoint]=config['base_url']
        return env
