"""Compile the existing Markdown edit to the installed local finishing engine.

The generated JSON is disposable; all editable source windows remain in Markdown.
"""
from __future__ import annotations
import hashlib
import html
import json
import os
from pathlib import Path
import re
import shutil
import sys

from post_runtime import digest, save, settings, StageCache


def engine():
    folder=Path(__file__).resolve().parents[2]/'hypit/scripts'
    if not (folder/'finish_drama.py').is_file():
        raise ValueError('Layered finishing uses the installed hypit/scripts/finish_drama.py helper')
    if str(folder) not in sys.path:sys.path.insert(0,str(folder))
    import post_timeline, finish_drama
    return post_timeline,finish_drama


def extensions(text):
    result={}
    for block in re.split(r'(?m)(?=^## CUT-)',text):
        heading=re.match(r'## (CUT-[^\s·]+)',block)
        if not heading:continue
        match=re.search(r'### 后期执行\s*\n```json\s*\n(.*?)\n```',block,re.S)
        value=json.loads(match.group(1)) if match else {}
        if not isinstance(value,dict):raise ValueError('后期执行 must be a JSON object')
        allowed={'native_audio','dialogue_expected','no_dialogue_basis','anchors','transition_in',
                 'audio','captions','overlays','grade','effects','native_music','native_gain_db','intent'}
        if set(value)-allowed:raise ValueError('Unknown 后期执行 fields: '+str(sorted(set(value)-allowed)))
        reason=re.search(r'^- 取舍：(.+)$',block,re.M)
        if reason:value.setdefault('intent',reason.group(1))
        result[heading.group(1)]=value
    return result


def build(episode, project_root, api, *, burn_subtitles=True):
    source=episode/'剪辑单.md';config=settings(episode)
    delivery,cuts,unused=api.parse_cut_list(source)
    findings=api.check_cuts(episode,cuts,project_root,probe=True,unused=unused,delivery=delivery,listen=True,conform_specs=True)
    if findings:raise ValueError('\n'.join(findings))
    extra=extensions(source.read_text(encoding='utf-8'))
    folder=episode/api.OUTPUT_DIRECTORY/'.execution';folder.mkdir(parents=True,exist_ok=True)
    def path(written):
        actual=api._resolve_media(episode,project_root,written)
        if actual is None:raise ValueError('Missing edit media: '+written)
        return os.path.relpath(actual,folder).replace('\\','/')
    plan={'version':1,'clips':[],'audio':[],'captions':[],'overlays':[],
          'caption_style':config.get('subtitles',{'preset':'cinema'}),
          'master':dict(config.get('master',{})),
          'pacing':config.get('pacing',{}),'expected_lines':[]}
    fps=api._film_fps(episode,project_root,cuts,delivery,probe=True)
    first=api.probe_stream(api._resolve_media(episode,project_root,cuts[0].media))
    dimensions=delivery.frame_size or (first['width'],first['height'])
    plan['canvas']={'width':dimensions[0],'height':dimensions[1],'fps':fps}
    if delivery.loudness_lufs is not None:plan['master'].setdefault('lufs',delivery.loudness_lufs)
    if delivery.grain is not None:plan['master'].setdefault('grain',delivery.grain)
    source_map=[]
    spans=api._film_spans(cuts,fps)
    eases=api._move_ease(cuts,api._scene_keys(episode,cuts))
    for index,cut in enumerate(cuts):
        x=extra.get(cut.cut_id,{})
        still_file=None
        if cut.still:
            image=api._resolve_media(episode,project_root,cut.media)
            still_file=folder/(cut.cut_id+'-still.mp4')
            binary=api._require('ffmpeg')
            args=api._still_command(binary,image,cut,delivery,(48000,'stereo'),api._shot_match_filter(cut),spans[index],eases[index])
            args+=['-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac',str(still_file)]
            cache=StageCache(folder/'.stills',binary,[Path(__file__),Path(api.__file__)])
            cache.run(cut.cut_id,args,[image],api._run)
        if cut.screen_texts:raise ValueError('Use explicit overlays for layered screen text; native Remotion screen-text fields are not silently dropped')
        row={'id':cut.cut_id,'file':path(cut.media),'start':cut.start,'end':cut.end,
             'native_audio':x.get('native_audio',True),'reason':cut.title}
        for key in ('dialogue_expected','no_dialogue_basis','anchors','transition_in','grade','effects','native_music','native_gain_db'):
            if key in x:row[key]=x[key]
        if cut.picture:
            if 'warmth' in cut.picture:raise ValueError('Layered color uses explicit grade; translate the chosen warmth correction first')
            row.setdefault('grade',{}).update(cut.picture)
        if still_file:
            row.update(file=still_file.name,start=0,end=spans[index],native_audio=False)
            row.pop('grade',None)
            if row.get('anchors'):
                row['anchors']=[{**a,'start':a['start']*spans[index]/cut.declared,'end':a['end']*spans[index]/cut.declared} for a in row['anchors']]
        plan['clips'].append(row)
        source_map.append({'cut':cut.cut_id,'source_id':cut.motion,'source_window':[cut.start,cut.end],
                           'intent':x.get('intent',''),'anchors':x.get('anchors',[]),
                           'source_sha256':digest(api._resolve_media(episode,project_root,cut.media))})
        for raw in x.get('audio',[]):
            audio=dict(raw);audio['file']=path(audio['file'])
            audio.setdefault('at',{'clip':cut.cut_id,'edge':'start'})
            plan['audio'].append(audio)
        for n,sound in enumerate(cut.sound_effects,1):
            plan['audio'].append({'id':f'{cut.cut_id}-sfx-{n}','bus':'sfx','file':path(sound.path),
                'start':sound.offset,'end':sound.offset+sound.end-sound.start,
                'at':{'clip':cut.cut_id,'edge':'start','offset':sound.start},'gain_db':sound.gain_db})
        for n,voice in enumerate(cut.voices,1):
            plan['audio'].append({'id':f'{cut.cut_id}-voice-{n}','bus':'dialogue','file':path(voice.path),
                'start':voice.offset,'at':{'clip':cut.cut_id,'edge':'start','offset':voice.start},'gain_db':voice.gain_db})
        if cut.bed and cut.bed.path:
            following=next((other for other in cuts[index+1:] if other.bed),None)
            until={'clip':following.cut_id,'edge':'start','offset':following.bed.start} if following else {'clip':cuts[-1].cut_id,'edge':'end'}
            plan['audio'].append({'id':cut.cut_id+'-ambience','bus':'ambience','file':path(cut.bed.path),
                'start':cut.bed.offset,'at':{'clip':cut.cut_id,'edge':'start','offset':cut.bed.start},
                'until':until,'loop':True,'gain_db':cut.bed.gain_db,'fade_in':.3,'fade_out':.3})
        if burn_subtitles and delivery.burn_subtitles:
            if 'captions' in x:
                for cue in x['captions']:
                    cue=dict(cue)
                    if not cue.get('audio_id'):cue.setdefault('clip',cut.cut_id)
                    plan['captions'].append(cue)
            else:
                for start,end,text,words in cut.subtitles:
                    # Markdown cue times are CUT-relative. Engine clip cues use SOURCE seconds.
                    factor=spans[index]/cut.declared if cut.still else 1
                    plan['captions'].append({'clip':cut.cut_id,'start':cut.start+(start or 0)*factor,
                        'end':cut.start+(cut.declared if end is None else end)*factor,'text':text,'keys':list(words),
                        'timing':'locked'})
        for raw in x.get('overlays',[]):
            overlay=dict(raw)
            for key in ('file','font_file'):
                if key in overlay:overlay[key]=path(overlay[key])
            overlay.setdefault('at',{'clip':cut.cut_id,'edge':'start'})
            plan['overlays'].append(overlay)
    screenplay=(episode/'剧本.md').read_text(encoding='utf-8') if (episode/'剧本.md').exists() else ''
    for cue in plan['captions']:
        if screenplay and api._normalize(cue['text']) not in api._normalize(screenplay):
            raise ValueError('Caption text is not in the current screenplay: '+cue['text'])
    key=hashlib.sha256((source.read_text(encoding='utf-8')+json.dumps(config,sort_keys=True)+str(burn_subtitles)).encode()).hexdigest()[:16]
    target=folder/f'edit-{key}.json';save(target,plan)
    compiler,_=engine();compiled=compiler.compile_plan(target)
    # A mechanical speech repair is a proposal to the author, never a silent new CUT.
    for cut,rendered in zip(cuts,compiled['clips']):
        selected=rendered['segments']
        if len(selected)!=1 or abs(selected[0]['start']-cut.start)>.001 or abs(selected[0]['end']-(round(cut.end*fps)/fps if cut.still else cut.end))>.001:
            raise ValueError(f'{cut.cut_id}: speech/action protection requires {selected}; update the Markdown source window before rendering')
    compiled['implementation']={'bridge':digest(Path(__file__)),'native':digest(Path(api.__file__))}
    compiled['post_settings_sha256']=digest(episode/'后期配置.json') if (episode/'后期配置.json').exists() else None
    known={item['file'] for item in compiled['inputs']}
    for cut in cuts:
        actual=api._resolve_media(episode,project_root,cut.media)
        if str(actual) not in known:
            compiled['inputs'].append({'file':str(actual),'sha256':digest(actual)});known.add(str(actual))
    compiled['editorial_sources']=source_map
    compiled['storyboard_conform']=api.conform_report(episode,cuts,delivery,unused,fps=fps)
    compiled['markdown_source']={'path':os.path.relpath(source,folder),'sha256':digest(source)}
    save(folder/f'compiled-{key}.json',compiled)
    return target,compiled


def preview_page(episode, compiled, media):
    rows=[]
    for row in compiled['clips']:
        name=html.escape(row['id']);start=row['at'];end=row['end_at']
        rows.append(f'<tr><td><button data-at="{start:.4f}">{name}</button></td><td>{start:.3f}–{end:.3f}s</td><td>{html.escape(row.get("reason",""))}</td></tr>')
    page=episode/'制作成果/成片/剪辑预览.html'
    uri=os.path.relpath(media,page.parent).replace('\\','/')
    page.write_text('<!doctype html><meta charset="utf-8"><title>剪辑预览</title><style>body{font:16px system-ui;background:#15181c;color:#eee;max-width:1000px;margin:30px auto}video{max-height:70vh;max-width:100%}td{padding:12px;border-bottom:1px solid #444}button{cursor:pointer}</style><h1>连续剪辑预览</h1><video id="film" controls src="'+html.escape(uri,quote=True)+'"></video><p>点击镜号跳到实际成片位置；看听反应、声音交接与字幕。此页不修改剪辑决定。</p><table>'+''.join(rows)+'</table><pre>'+html.escape(json.dumps(compiled['issues'],ensure_ascii=False,indent=2))+'</pre><script>document.querySelectorAll("button[data-at]").forEach(b=>b.onclick=()=>{film.currentTime=Number(b.dataset.at);film.play()});</script>',encoding='utf-8')
    return page


def execute(command,episode,project_root,api,*,burn_subtitles=True):
    if command=='verify':
        receipt=episode/api.OUTPUT_DIRECTORY/'layered-latest.json'
        if not receipt.exists():raise ValueError('No layered render receipt')
        record=json.loads(receipt.read_text(encoding='utf-8'))
        if record['markdown_sha256']!=digest(episode/'剪辑单.md'):raise ValueError('Rendered file belongs to an older Markdown edit')
        config=episode/'后期配置.json'
        if record.get('settings_sha256')!=(digest(config) if config.exists() else None):raise ValueError('Post settings changed after rendering')
        if record['sha256']!=digest(record['file']):raise ValueError('Rendered file changed after export')
        for source in record.get('inputs',[]):
            if not Path(source['file']).exists() or digest(source['file'])!=source['sha256']:
                raise ValueError('Source changed after rendering: '+source['file'])
        _,finisher=engine()
        actual=finisher.metadata(record['file'],finisher.ffmpeg_path(None))
        return {'actual':actual,'expected_seconds':record['duration'],'issues':record['issues']}
    target,compiled=build(episode,project_root,api,burn_subtitles=burn_subtitles)
    identity=hashlib.sha256(json.dumps(compiled,sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:16]
    if command in {'plan','check','conform'}:
        return {'plan':str(target),'duration':compiled['duration'],'clips':compiled['clips'],
                'editorial_sources':compiled['editorial_sources'],'issues':compiled['issues']}
    _,finisher=engine();root=episode/api.OUTPUT_DIRECTORY
    preview=command=='preview'
    output=root/f'{"预览" if preview else "成片"}-{identity}.mp4'
    report=finisher.render(target,output,preview=preview)
    if digest(episode/'剪辑单.md')!=compiled['markdown_source']['sha256']:
        raise ValueError('Markdown changed during rendering; export belongs to the previous plan')
    config=episode/'后期配置.json'
    if (digest(config) if config.exists() else None)!=compiled['post_settings_sha256']:
        raise ValueError('Post settings changed during rendering')
    current=root/('预览.mp4' if preview else '成片.mp4')
    pending=current.with_suffix('.pending.mp4');shutil.copy2(output,pending);pending.replace(current)
    if not preview:save(root/'layered-latest.json',{'file':str(current),'sha256':digest(current),'markdown_sha256':digest(episode/'剪辑单.md'),'compiled_identity':identity,
        'settings_sha256':compiled['post_settings_sha256'],
        'inputs':compiled['inputs'],'duration':compiled['duration'],'issues':compiled['issues']})
    page=preview_page(episode,compiled,current)
    return {'file':str(current),'preview_page':str(page),'duration':compiled['duration'],'issues':report['issues'],
            'source_plan':str(target),'artistic_accepted':False}
