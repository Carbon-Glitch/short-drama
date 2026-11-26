"""Import a legacy edit into a separate, editable OpenFilm episode; originals stay intact."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import html
from pathlib import Path
import edit_tool as legacy
from edit_layered import extensions
from openfilm_bridge import run
from openfilm_dependencies import copy_dependencies
from post_runtime import settings, PALETTES

def duration(path):
    data = subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(path)])
    return float(json.loads(data)['format']['duration'])

def migrate(episode, project, target):
    episode, project, target = map(lambda p: Path(p).resolve(), (episode, project, target))
    if target == episode or target.exists(): raise ValueError('Choose a new destination for migration')
    text = (episode/'剪辑单.md').read_text(encoding='utf-8')
    delivery,cuts,_ = legacy.parse_cut_list(episode/'剪辑单.md')
    extra = extensions(text)
    config = settings(episode)
    unsupported=[]
    master=dict(config.get('master',{}))
    for key in set(master)-{'lufs','duck_music','true_peak_db'}:unsupported.append('master.'+key+' 尚未映射')
    if master.get('true_peak_db',-1)!=-1:unsupported.append('原生输出真峰值目标为 -1 dBTP，需单独映射现有 true_peak_db')
    duck=master.get('duck_music')
    if duck and duck.get('mode')!='envelope':unsupported.append('duck_music 的当前模式需映射，支持现有 envelope 模式')
    if duck:
        for key in set(duck)-{'mode','depth_db','lead','release','merge_gap'}:unsupported.append('duck_music.'+key+' 尚未映射')
    style_config=config.get('subtitles',{})
    theme={**PALETTES[style_config.get('preset','cinema')],**style_config}
    for key in set(style_config)-{'preset','font','size','font_size','outline','bottom','color','accent','bold','fade_ms','cues'}:unsupported.append('subtitles.'+key+' 尚未映射')
    if theme.get('fade_ms'):unsupported.append('字幕 fade_ms 需映射为可编辑动画层')
    for c in cuts:
        x=extra.get(c.cut_id,{})
        if c.move or c.screen_texts or c.picture or c.bed: unsupported.append(c.cut_id+': 运镜/画面文字/调色/环境循环需映射为原生图层')
        for key in ('grade','effects','overlays'):
            if x.get(key): unsupported.append(c.cut_id+': '+key+' 需镜头页映射')
        if x.get('transition_in',{}).get('type','cut') not in ('cut','fade','dissolve'): unsupported.append(c.cut_id+': 转场需镜头页映射')
        if any(a.get('loop') or a.get('until') for a in x.get('audio',[])): unsupported.append(c.cut_id+': 循环音轨需拆成真实源窗')
        for a in x.get('audio',[]):
            for key in set(a)-{'id','file','start','end','at','speed','gain_db','fade_in','fade_out','bus','volume','fx','pan','loop','until','dialogue_expected','ending','reason','language','no_dialogue_basis'}:
                unsupported.append(c.cut_id+': audio.'+key+' 尚未映射')
            for fx in a.get('fx',[]):
                if fx.get('type') not in {'eq','highpass','lowpass'}:unsupported.append(c.cut_id+': fx '+str(fx.get('type'))+' 需保持原处理顺序逐轨映射')
    if delivery.grain: unsupported.append('颗粒需要映射到原生样式')
    if delivery.shot_match and any(not c.untouched for c in cuts): unsupported.append('旧版自动接镜校正需转为明确调色后迁移')
    if unsupported: raise ValueError('\n'.join(unsupported)+'\n先把这些层转为 OpenFilm 镜头页，再以 seed JSON 初始化；尚未创建目标项目。')
    target.mkdir(parents=True)
    for name in ('剧本.md','视觉设定.md','分镜.md','图片提示词.md','视频提示词.md','剪辑单.md'):
        if (episode/name).exists(): shutil.copy2(episode/name,target/name)
    copied_refs=copy_dependencies(episode,project,target)
    if (episode/'后期配置.json').exists():shutil.copy2(episode/'后期配置.json',target/'后期配置.json')
    def asset(written):
        source=legacy._resolve_media(episode,project,written)
        if not source: raise ValueError('Missing source '+written)
        digest=hashlib.sha256(source.read_bytes()).hexdigest()[:12]
        dest=target/'assets'/(digest+'-'+source.name);dest.parent.mkdir(exist_ok=True)
        if not dest.exists(): shutil.copy2(source,dest)
        return dest.relative_to(target).as_posix()
    tracks=[];by_id={};bindings={'schema':1,'events':[],'cues':{}};cursor=0;cues=[];native_sounds=[]
    for c in cuts:
        x=extra.get(c.cut_id,{});overlap=x.get('transition_in',{}).get('duration',0)
        at=cursor-overlap
        clip={'id':c.cut_id,'src':asset(c.media),'time':[c.start,c.end],'at':at,
              'volume':10**(x.get('native_gain_db',0)/20) if x.get('native_audio',True) else 0,
              'attrs':{'data-sd-origin':c.cut_id,'data-motion-id':c.motion,'data-sd-intent':x.get('intent',c.title)}}
        if overlap: clip['overrides']=[{'fade':[overlap,0]}]
        if c.still:clip.pop('volume',None)
        if overlap and native_sounds:
            native_sounds[-1]['overrides'][0]['fade'][1]=overlap
        if clip.get('volume') and not c.still:
            sound_id=c.cut_id+'-native'
            native_sounds.append({'id':sound_id,'src':clip['src'],'sound':True,'time':clip['time'][:],'at':at,'volume':clip['volume'],
                                 'overrides':[{'fade':[overlap,0]}],'attrs':{'data-sd-origin':sound_id,'data-sd-bus':'native','data-sd-follow':json.dumps({'clip':c.cut_id})}})
            clip['volume']=0
        tracks.insert(0,{'clips':[clip]});by_id[c.cut_id]=clip;cursor=at+c.end-c.start
        for event in x.get('anchors',[]): bindings['events'].append({**event,'origin':c.cut_id,'src':clip['src']})
        for i,(start,end,line,words) in enumerate(c.subtitles):
            cues.append({'id':c.cut_id+'-cue-'+str(i),'clip':c.cut_id,'start':c.start+(start or 0),'end':c.start+(c.declared if end is None else end),'text':line,'keys':list(words)})
        if 'captions' in x:
            cues=[v for v in cues if v['clip']!=c.cut_id]
            for i,cue in enumerate(x['captions']):cues.append({'id':c.cut_id+'-cue-'+str(i),'clip':cue.get('audio_id',c.cut_id),**cue})
    tracks.extend({'clips':[s]} for s in native_sounds)
    def point(value):
        if isinstance(value,(int,float)):return float(value)
        owner=by_id[value['clip']]
        source=owner['time'][1] if value.get('edge')=='end' else value.get('source_time',owner['time'][0])
        return owner['at']+(source-owner['time'][0])/owner.get('speed',1)+value.get('offset',0)
    for c in cuts:
        x=extra.get(c.cut_id,{})
        sounds=list(x.get('audio',[]))
        sounds += [{'id':c.cut_id+'-voice-'+str(i),'file':v.path,'start':v.offset,'at':{'clip':c.cut_id,'offset':v.start},'gain_db':v.gain_db,'bus':'dialogue'} for i,v in enumerate(c.voices)]
        sounds += [{'id':c.cut_id+'-sfx-'+str(i),'file':v.path,'start':v.offset,'end':v.offset+v.end-v.start,'at':{'clip':c.cut_id,'offset':v.start},'gain_db':v.gain_db} for i,v in enumerate(c.sound_effects)]
        for sound in sounds:
            if sound.get('loop') or sound.get('until'): raise ValueError('循环声轨需拆为真实源窗后迁移')
            src=asset(sound['file']);link=sound.get('at',{'clip':c.cut_id});start=sound.get('start',0)
            at=point(link)
            clip={'id':sound['id'],'src':src,'sound':Path(src).suffix.lower() in ('.mp4','.mov','.webm'), 'time':[start,sound.get('end',duration(target/src))],'at':at,'speed':sound.get('speed',1),
                  'volume':10**(sound.get('gain_db',0)/20),'attrs':{'data-sd-origin':sound['id']},'overrides':[{'fade':[sound.get('fade_in',0),sound.get('fade_out',0)]}]}
            if not clip['sound']: del clip['sound']
            if isinstance(link,dict):clip['attrs']['data-sd-follow']=json.dumps(link)
            clip['attrs']['data-sd-bus']=sound.get('bus','sfx')
            recipe={'source':src}
            for key in ('fx','pan'):
                if key in sound:recipe[key]=sound[key]
            def timeline_point(value):
                if not isinstance(value,dict):return at+float(value)
                return point(value)
            if sound.get('volume'):recipe['envelopeDb']=[{'time':start+(timeline_point(p['time'])-at)*clip['speed'],'db':p['db']} for p in sound['volume']]
            if len(recipe)>1 or (duck and sound.get('bus')=='music'):clip['attrs']['data-sd-audio']=json.dumps(recipe)
            tracks.append({'clips':[clip]});by_id[clip['id']]=clip
    def stamp(seconds):
        ms=round(seconds*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02}.{ms%1000:03}'
    w,h=delivery.frame_size or (1080,1920)
    size=theme.get('font_size',h*theme['size']);outline=h*theme['outline']
    vtt=f"WEBVTT\n\nSTYLE\n::cue {{ font-family: {json.dumps(theme['font'])}; font-size: {size}px; color: {theme['color']}; font-weight: {'bold' if theme['bold'] else 'normal'}; background-color: transparent; text-shadow: 0 0 {outline}px black; }}\n::cue(.accent) {{ color: {theme['accent']}; }}\n\n"
    if not delivery.burn_subtitles:cues=[]
    for cue_index,cue in enumerate(cues,1):
        owner=by_id[cue['clip']];a=owner['at']+(cue['start']-owner['time'][0])/owner.get('speed',1);b=owner['at']+(cue['end']-owner['time'][0])/owner.get('speed',1)
        style={**theme.get('cues',{}).get(str(cue_index),{}),**cue.get('style',{})}
        if set(style)-{'x','y'}:raise ValueError('cue 样式需进一步映射: '+str(sorted(set(style)-{'x','y'})))
        shown=html.escape(cue['text'],quote=False)
        for word in sorted(set(cue.get('keys',[])),key=len,reverse=True):shown=shown.replace(html.escape(word,quote=False),'<c.accent>'+html.escape(word,quote=False)+'</c>')
        vtt+=f"{cue['id']}\n{stamp(a)} --> {stamp(b)} line:{100*style.get('y',1-theme['bottom']):g}% position:{100*style.get('x',.5):g}% size:82% align:center\n{shown}\n\n"
        bindings['cues']['captions/dialogue.vtt#'+cue['id']]={'clip':cue['clip'],'start':cue['start'],'end':cue['end']}
    if cues:
        (target/'captions').mkdir();(target/'captions/dialogue.vtt').write_text(vtt,encoding='utf-8');tracks.insert(0,{'clips':[],'captions':{'src':'captions/dialogue.vtt','kind':'captions'}})
    seed={'fps':delivery.fps or 24,'loudness':delivery.loudness_lufs if delivery.loudness_lufs is not None else master.get('lufs'),'audioMaster':{'duck_music':duck} if duck else None,'film':{'stage':{'w':w,'h':h},'tracks':tracks},'bindings':bindings}
    seed_path=target/'migration-seed.json';seed_path.write_text(json.dumps(seed,ensure_ascii=False),encoding='utf-8')
    result=run('init',target,payload=seed_path)
    (target/'.short-drama/migration.json').write_text(json.dumps({'source':str(episode),'retainedMedia':True,'review':'核对原工程的外部图层及创作时机，技术导入不是审美验收'},ensure_ascii=False),encoding='utf-8')
    return result

if __name__=='__main__':
    if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('episode');p.add_argument('destination');p.add_argument('--project-root',required=True);a=p.parse_args()
    print(json.dumps(migrate(a.episode,a.project_root,a.destination),ensure_ascii=False,indent=2))
