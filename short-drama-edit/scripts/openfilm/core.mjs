/** Short-drama semantics on OpenFilm's one editable timeline. No generation or second renderer. */
import {readFile, writeFile, mkdir, rename, copyFile, stat,rm,readdir} from 'node:fs/promises';
import {existsSync} from 'node:fs';
import {createHash,randomUUID} from 'node:crypto';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {homedir} from 'node:os';
import {join, resolve, dirname, basename, relative} from 'node:path';
import {pathToFileURL} from 'node:url';

export const VERSION='0.4.1';
export const runtimeHome=()=>process.env.SHORT_DRAMA_OPENFILM_HOME || join(homedir(),'Documents','Codex','tools','short-drama-openfilm-'+VERSION);
export const packageHome=()=>join(runtimeHome(),'node_modules','openfilm');
const modules=new Map();
export async function native(name){
  const key=join(packageHome(),name);
  if(!modules.has(key))modules.set(key,import(pathToFileURL(key).href));
  return modules.get(key);
}
export const hash=x=>createHash('sha256').update(x).digest('hex');
export const readJson=async(file,fallback=null)=>{try{return JSON.parse(await readFile(file,'utf8'));}catch(e){if(e.code==='ENOENT')return fallback;throw e;}};
export async function atomic(file,text){await mkdir(dirname(file),{recursive:true});const tmp=file+'.'+randomUUID()+'.sd-pending';await writeFile(tmp,text,'utf8');await rename(tmp,file);}
export const saveJson=(file,value)=>atomic(file,JSON.stringify(value,null,2)+'\n');
const meta=root=>join(root,'.short-drama');
const millis=n=>Math.round(n*1000)/1000;
const rows=doc=>doc.tracks.flatMap((track,ti)=>track.clips.map(clip=>({clip,track,ti})));
const span=c=>({start:c.at||0,end:(c.at||0)+((c.time?.[1]??0)-(c.time?.[0]??0))/(c.speed||1)});
const cleanCell=s=>String(s??'').replaceAll('|','／').replaceAll('\n',' ');
const probeCache=new Map();
async function resolveDurations(root,value){
  const api=await native('src/film-doc.mjs');
  for(const {clip} of rows(value)){
    if(clip.time?.length===2)continue;
    const kind=api.kindOf(clip);const file=join(root,clip.src);let duration;
    if(kind==='page'){
      const html=await readFile(file,'utf8');
      duration=Number(html.match(/name=["']duration["'][^>]*content=["']([\d.]+)/)?.[1]);
    }else if(kind==='video'||kind==='sound'){
      const s=await stat(file);const key=file+'|'+s.size+'|'+s.mtimeMs;
      if(!probeCache.has(key)){
        const {stdout}=await promisify(execFile)('ffprobe',['-v','error','-show_entries','format=duration','-of','json',file],{windowsHide:true});
        probeCache.set(key,Number(JSON.parse(stdout).format.duration));
      }duration=probeCache.get(key);
    }
    const bounds=api.clipSpan(clip,duration,clip.id);
    // Read-only resolved value, not a second persisted timeline.
    clip.time=[bounds.from,bounds.to];
  }
}

export async function read(root){
  root=resolve(root);
  const film=await native('studio/server/film.mjs');
  const current=await film.settleProjectFilm(root);
  if(!current.value)throw Error(current.problems.join('\n'));
  await resolveDurations(root,current.value);
  return {root,...current};
}
export async function init(root,{stage={w:1080,h:1920},fps=24,loudness=null,audioMaster=null,film=null,bindings=null}={}){
  root=resolve(root);await mkdir(root,{recursive:true});
  if(existsSync(join(root,'film.html')))throw Error('film.html already exists; edit its current revision');
  if(existsSync(join(root,'剪辑单.md'))){
    const archive=join(meta(root),'legacy','剪辑单-'+Date.now()+'.md');await mkdir(dirname(archive),{recursive:true});await copyFile(join(root,'剪辑单.md'),archive);
  }
  const api=await native('src/film-doc.mjs');const value=api.parseFilm(film||{stage,tracks:[]});
  for(const {clip} of rows(value))clip.attrs={...clip.attrs,'data-sd-origin':clip.attrs?.['data-sd-origin']||clip.id};
  await atomic(join(root,'film.html'),api.filmHtml(value));
  await saveJson(join(meta(root),'project.json'),{schema:1,fps,...(loudness===null?{}:{loudness}),...(audioMaster?{audioMaster}:{}),backend:'openfilm',engineVersion:VERSION});
  await saveJson(join(meta(root),'bindings.json'),bindings||{schema:1,events:[],cues:{}});
  await reconcile(root,{initial:true});
  const {bindHandoff,collect}=await import('./handoff.mjs');const adopted=await read(root);
  await bindHandoff(root,adopted.value,{revision:(await collect(root)).revision,items:{}});
  await reconcile(root);
  return state(root);
}

export async function importAsset(root,source){
  source=resolve(source);const bytes=await readFile(source);const digest=hash(bytes);
  const name=digest.slice(0,12)+'-'+basename(source);const target=join(root,'assets',name);
  await mkdir(dirname(target),{recursive:true});if(!existsSync(target))await copyFile(source,target);
  return {src:relative(root,target).replaceAll('\\','/'),sha256:digest};
}

function anchorTime(link,map){
  const owner=map.get(link.clip);if(!owner)return null;
  const c=owner.clip;let at;
  if(link.edge==='end')at=span(c).end;
  else if(link.source_time!==undefined)at=(c.at||0)+(link.source_time-(c.time?.[0]||0))/(c.speed||1);
  else at=c.at||0;
  return millis(at+(link.offset||0));
}

function requiredEvents(bindings,all){
  const problems=[];
  for(const event of bindings.events||[]){
    if(event.required===false||event.disposition==='omitted')continue;
    const matching=all.filter(({clip,track})=>!clip.disabled&&!track.hidden&&
      (event.channel==='audio' ? !track.muted&&clip.volume!==0 : !clip.sound&&!/\.(wav|mp3|m4a|aac|flac|ogg)$/i.test(clip.src))&&
      (clip.attrs?.['data-sd-origin']||clip.id)===event.origin && (!event.src||clip.src===event.src));
    const ranges=matching.map(({clip})=>clip.time||[0,0]).sort((a,b)=>a[0]-b[0]);
    let cursor=event.start;
    for(const [start,end] of ranges){if(start<=cursor+.001)cursor=Math.max(cursor,end);}
    if(cursor<event.end-.001)problems.push({kind:'required_event_missing',id:event.id,origin:event.origin,
      sourceRange:[event.start,event.end],purpose:event.purpose||'',severity:'error'});
  }
  return problems;
}

function cueProjection(link,all){
  const direct=all.find(r=>r.clip.id===link.clip);
  const origin=link.origin||direct?.clip.attrs?.['data-sd-origin']||link.clip;
  const pieces=all.filter(r=>!r.clip.disabled&&!r.track.hidden&&!r.track.muted&&
    (r.clip.attrs?.['data-sd-origin']||r.clip.id)===origin&&
    (!link.src||r.clip.src===link.src)).sort((a,b)=>a.clip.time[0]-b.clip.time[0]);
  let cursor=link.start;const projected=[];
  for(const {clip:c} of pieces){
    if(c.time[1]<=cursor+.001||c.time[0]>cursor+.001)continue;
    const end=Math.min(c.time[1],link.end);
    projected.push({start:(c.at||0)+(cursor-c.time[0])/(c.speed||1),end:(c.at||0)+(end-c.time[0])/(c.speed||1),clip:c});
    cursor=end;if(cursor>=link.end-.001)break;
  }
  if(cursor<link.end-.001||!projected.length)return {error:'cue_speech_trimmed'};
  for(let i=1;i<projected.length;i++)if(Math.abs(projected[i].start-projected[i-1].end)>.025)return {error:'cue_split_discontinuous'};
  return {start:projected[0].start,end:projected.at(-1).end,owner:direct?.clip||projected[0].clip,origin};
}

/** Reproject only declared relationships; keep hand-edited cue text, styles and independent timing. */
export async function reconcile(root,options={}){
  const lock=join(meta(resolve(root)),'sync.lock');await mkdir(dirname(lock),{recursive:true});
  const deadline=Date.now()+15000;
  while(true){try{await mkdir(lock);break;}catch(e){if(e.code!=='EEXIST')throw e;if(Date.now()>deadline)throw Error('Another sync is running; retry when it finishes: '+lock);await new Promise(r=>setTimeout(r,60));}}
  try{return await reconcileLocked(root,options);}finally{await rm(lock,{recursive:true});}
}
async function reconcileLocked(root,{initial=false}={}){
  const {prepareAudio}=await import('./audio.mjs');
  const current=await read(root);root=current.root;
  const bindings=await readJson(join(meta(root),'bindings.json'),{schema:1,events:[],cues:{}});
  const previous=await readJson(join(meta(root),'sync.json'),{clips:{},cues:{}});
  const all=rows(current.value);const map=new Map(all.map(r=>[r.clip.id,r]));
  const operations=[];const issues=[];
  for(const {clip,track} of all)if(!clip.attrs?.['data-sd-origin']&&!track.locked){clip.attrs={...clip.attrs,'data-sd-origin':clip.id};operations.push({op:'fields',clip:clip.id,fields:{attrs:clip.attrs}});}
  // Iterate in dependency order; an audio clip can follow a picture and captions can follow that audio.
  const pending=all.filter(r=>r.clip.attrs?.['data-sd-follow']);const solved=new Set();
  for(let pass=0;pass<=pending.length;pass++){
    let progress=false;
    for(const item of pending){
      const c=item.clip;if(solved.has(c.id))continue;
      let link;try{link=JSON.parse(c.attrs['data-sd-follow']);}catch{issues.push({kind:'invalid_follow',clip:c.id,severity:'error'});solved.add(c.id);continue;}
      const parent=map.get(link.clip);
      if(!parent){issues.push({kind:'follow_target_missing',clip:c.id,target:link.clip,severity:'warning'});solved.add(c.id);continue;}
      if(parent.clip.attrs?.['data-sd-follow']&&!solved.has(parent.clip.id))continue;
      const expected=anchorTime(link,map);const old=previous.clips[c.id];
      if(!initial&&(!old||Math.abs((c.at||0)-(old.at||0))>.001) && Math.abs((c.at||0)-expected)>.001){
        // The person moved this follower too: its new offset is their choice.
        link.offset=millis((link.offset||0)+(c.at||0)-expected);
        if(!item.track.locked){c.attrs={...c.attrs,'data-sd-follow':JSON.stringify(link)};operations.push({op:'fields',clip:c.id,fields:{attrs:c.attrs}});}
      }else if(expected<0){issues.push({kind:'negative_follow',clip:c.id,severity:'error'});
      }else if(Math.abs((c.at||0)-expected)>.001){
        if(item.track.locked)issues.push({kind:'locked_follow_not_updated',clip:c.id,severity:'warning'});
        else{c.at=expected;operations.push({op:'set',clip:c.id,field:'at',value:expected});}
      }
      solved.add(c.id);progress=true;
    }
    if(!progress)break;
  }
  for(const r of pending)if(!solved.has(r.clip.id))issues.push({kind:'follow_cycle',clip:r.clip.id,severity:'error'});
  if(operations.length){
    const api=await native('studio/server/film.mjs');
    const now=await api.readProjectFilm(root);if(now.rev!==current.rev)throw Error('Timeline changed during sync; read the current version again');
    await api.editProjectFilm(root,current.rev,operations);
  }
  await prepareAudio(root);
  const updated=await read(root);const updatedRows=rows(updated.value);const byId=new Map(updatedRows.map(r=>[r.clip.id,r]));
  const captions=await native('src/captions.mjs');const cuesState={};let bindingsChanged=false;
  for(const track of updated.value.tracks){
    if(!track.captions)continue;
    const path=join(root,track.captions.src);const before=await readFile(path,'utf8');const vtt=captions.readVtt(before);let dirty=false;
    for(let i=0;i<vtt.cues.length;i++){
      const cue=vtt.cues[i];if(!cue.id){cue.id='cue-'+hash(cue.text+'|'+i).slice(0,10);dirty=true;}
      const key=track.captions.src+'#'+cue.id;const link=bindings.cues?.[key];
      if(link){
        const projection=cueProjection(link,updatedRows);
        if(projection.error){issues.push({kind:projection.error,cue:cue.id,clip:link.clip,severity:'error'});}
        else if(!track.locked){
          const {owner:c,start,end,origin}=projection;const speed=c.speed||1;const old=previous.cues[key];
          if(!link.origin){link.origin=origin;bindingsChanged=true;}
          if(!initial&&old&&(Math.abs(cue.start-old.start)>.001||Math.abs(cue.end-old.end)>.001)){
            // Keep the user's cue timing and bind that timing to the current source window.
            link.start=(c.time?.[0]||0)+(cue.start-(c.at||0))*speed;
            link.end=(c.time?.[0]||0)+(cue.end-(c.at||0))*speed;bindingsChanged=true;
          }else if(start>=0&&end>start&&(Math.abs(cue.start-start)>.001||Math.abs(cue.end-end)>.001)){
            cue.start=millis(start);cue.end=millis(end);dirty=true;
          }
          const after=cueProjection(link,updatedRows);if(after.error)issues.push({kind:after.error,cue:cue.id,clip:c.id,severity:'error'});
        }
      }
      cuesState[key]={start:cue.start,end:cue.end};
    }
    if(dirty&&!track.locked){if(await readFile(path,'utf8')!==before)throw Error('Captions changed during sync');await atomic(path,captions.writeVtt(vtt));}
  }
  if(bindingsChanged)await saveJson(join(meta(root),'bindings.json'),bindings);
  issues.push(...requiredEvents(bindings,updatedRows));
  const {inspectHandoff}=await import('./handoff.mjs');
  const handoff=await inspectHandoff(root,updated.value,bindings);issues.push(...handoff.issues);
  const final=await read(root);
  await saveJson(join(meta(root),'sync.json'),{schema:1,rev:final.rev,issues,
    clips:Object.fromEntries(rows(final.value).map(({clip})=>[clip.id,{at:clip.at||0,time:clip.time,speed:clip.speed||1}])),cues:cuesState});
  const result=await state(root,{issues});await report(root,result);return result;
}

export async function patch(root,ops,{rev=null,actor='agent'}={}){
  const current=await read(root);
  if(rev&&rev!==current.rev)throw Error('Timeline has changed; read before editing');
  const map=new Map(rows(current.value).map(r=>[r.clip.id,r]));
  if(actor==='agent')for(const op of ops){
    const id=typeof op.clip==='string'?op.clip:null;
    if(id&&map.get(id)?.track.locked)throw Error('Track is locked: '+id);
  }
  const api=await native('studio/server/film.mjs');await api.editProjectFilm(current.root,current.rev,ops);
  return reconcile(root);
}

export async function state(root,{issues=null}={}){
  const current=await read(root);const bindings=await readJson(join(meta(current.root),'bindings.json'),{events:[],cues:{}});
  const sync=await readJson(join(meta(current.root),'sync.json'),{});
  const {inspectHandoff}=await import('./handoff.mjs');const handoff=await inspectHandoff(current.root,current.value,bindings);
  const clips=rows(current.value).map(({clip,track,ti})=>({id:clip.id,src:clip.src,track:ti,...span(clip),
    source:clip.time,speed:clip.speed||1,locked:!!track.locked,disabled:!!clip.disabled,attrs:clip.attrs||{}}));
  const documents=[];
  for(const name of ['剧本.md','视觉设定.md','分镜.md','图片提示词.md','视频提示词.md']){
    try{const text=await readFile(join(current.root,name),'utf8');documents.push({name,text,revision:hash(text)});}catch(e){if(e.code!=='ENOENT')throw e;}
  }
  let projectRoot=current.root;
  while(!existsSync(join(projectRoot,'short-drama.json'))&&dirname(projectRoot)!==projectRoot)projectRoot=dirname(projectRoot);
  if(!existsSync(join(projectRoot,'short-drama.json')))projectRoot=current.root;
  const production=await readJson(join(projectRoot,'.short-drama/state.json'),null);
  const jobs=[];const jobsDir=join(projectRoot,'.short-drama/production/jobs');
  for(const name of (await readdir(jobsDir).catch(()=>[])).filter(n=>n.endsWith('.json'))){
    const job=await readJson(join(jobsDir,name));const id=job.job_id||name.slice(0,-5);
    const runsDir=join(projectRoot,'.short-drama/production/runs',id);const latest=(await readdir(runsDir).catch(()=>[])).filter(n=>n.endsWith('.json')).sort().at(-1);
    const run=latest?await readJson(join(runsDir,latest)):null;
    jobs.push({id,entry:job.source_entry,modality:job.modality,status:run?.status||'prepared',updatedAt:run?.finished_at||run?.started_at||job.prepared_at});
  }
  const assets=[];
  async function list(folder,depth=0){if(depth>4)return;for(const e of await readdir(folder,{withFileTypes:true}).catch(()=>[])){
    if(e.name.startsWith('.'))continue;const file=join(folder,e.name);
    if(e.isDirectory()){if(e.name!=='成片')await list(file,depth+1);}
    else if(/\.(mp4|mov|wav|mp3|m4a|png|jpg|webp)$/i.test(e.name))assets.push({path:relative(current.root,file).replaceAll('\\','/'),bytes:(await stat(file)).size});
  }}
  await list(join(current.root,'制作成果'));await list(join(current.root,'assets'));
  return {root:current.root,rev:current.rev,stage:current.value.stage,clips,documents,
    assets,jobs,productionRoot:projectRoot,production:production?{updatedAt:production.updated_at,lastAction:production.last_action,artifacts:production.artifacts}:null,
    duration:Math.max(0,...clips.filter(c=>!c.disabled).map(c=>c.end)),
    handoff,
    issues:issues||[...(sync.rev===current.rev?(sync.issues||[]).filter(i=>!['handoff_unbound','upstream_changed','upstream_reference_missing','requirement_unbound','requirement_target_missing','required_cue_missing','adopted_layer_missing','adopted_source_changed'].includes(i.kind)):requiredEvents(bindings,rows(current.value))),...handoff.issues],backend:'openfilm'};
}

export async function report(root,value){
  const text='# 剪辑单 · 从当前 OpenFilm 工程生成\n\n当前后期主稿：`film.html`。本报告用于阅读，剪辑修改回到工程。\n\n'+
    `- 工程版本：${value.rev}\n- 成片时长：${value.duration.toFixed(3)} 秒\n\n`+
    '| CUT / 轨道项 | 源区间 | 成片区间 | 来源 / 职责 |\n|---|---|---|---|\n'+
    value.clips.map(c=>`| ${cleanCell(c.id)} | ${(c.source||[]).join('–')} | ${c.start.toFixed(3)}–${c.end.toFixed(3)} | ${cleanCell(c.attrs['data-shot-id']||c.attrs['data-motion-id']||c.attrs['data-sd-intent']||'')} |`).join('\n')+
    '\n\n'+(value.issues.length?'## 当前需处理\n\n'+value.issues.map(i=>'- '+cleanCell(i.kind)+' · '+cleanCell(i.id||i.cue||i.clip||'')).join('\n'):'当前机械映射未发现缺口。表演与情绪由当前Agent结合实际声画判断。')+'\n';
  const file=join(root,'剪辑单.md');const before=await readFile(file,'utf8').catch(()=>null);
  if(before!==text)await atomic(file,text);
}

export async function updateDocument(root,name,text,revision){
  if(!['剧本.md','视觉设定.md','分镜.md','图片提示词.md','视频提示词.md'].includes(name))throw Error('Choose an existing creative document');
  const file=join(root,name);const current=await readFile(file,'utf8').catch(()=> '');
  if(revision&&hash(current)!==revision)throw Error('Document changed; read its current content');
  await atomic(file,text);return {name,revision:hash(text)};
}

/** Fingerprint the actual render graph, including referenced page scripts, CSS, fonts and media. */
export async function snapshot(root){
  root=resolve(root);const seen=new Map();
  async function visit(file){
    file=resolve(file);if(seen.has(file)||!existsSync(file))return;
    const bytes=await readFile(file);seen.set(file,hash(bytes));
    if(/\.(html|css|js|mjs)$/i.test(file)){
      const text=bytes.toString('utf8');
      const refs=[...text.matchAll(/(?:src|href)\s*=\s*["']([^"']+)["']|url\(\s*["']?([^)'"\s]+)|(?:import\s+.*?from\s*|import\s*)["']([^"']+)["']/g)];
      for(const m of refs){const raw=m[1]||m[2]||m[3];if(/^(https?:|data:|#|\/\/)/i.test(raw))continue;await visit(resolve(dirname(file),decodeURIComponent(raw.split(/[?#]/)[0])));}
    }
  }
  await visit(join(root,'film.html'));await visit(join(meta(root),'project.json'));await visit(join(meta(root),'bindings.json'));
  const {documents,collect}=await import('./handoff.mjs');
  for(const document of documents)await visit(join(root,document));
  const upstream=await collect(root);for(const ref of upstream.references)await visit(join(upstream.projectRoot,ref.path));
  await visit(join(upstream.projectRoot,'short-drama.json'));
  const current=await read(root);
  for(const {clip} of rows(current.value))if(clip.attrs?.['data-sd-audio'])await visit(join(root,JSON.parse(clip.attrs['data-sd-audio']).source));
  const files=Object.fromEntries([...seen].sort().map(([file,digest])=>[relative(root,file).replaceAll('\\','/'),digest]));
  return {identity:hash(JSON.stringify(files)),files};
}

export async function replaceSource(root,{clip:id,file,expectedSrc}){
  const current=await read(root);const row=rows(current.value).find(r=>r.clip.id===id);
  if(!row)throw Error('Missing clip '+id);if(row.track.locked)throw Error('Track is locked: '+id);
  if(expectedSrc&&row.clip.src!==expectedSrc)throw Error('Source changed; read it again');
  const asset=await importAsset(root,file);const origin=row.clip.attrs?.['data-sd-origin']||id;
  const affected=rows(current.value).filter(r=>(r.clip.attrs?.['data-sd-origin']||r.clip.id)===origin&&r.clip.src===row.clip.src);
  if(affected.some(r=>r.track.locked))throw Error('A source-linked track is locked');
  const candidate={...current.value,tracks:current.value.tracks.map(t=>({...t,clips:t.clips.map(c=>affected.some(r=>r.clip.id===c.id)?{...c,src:asset.src}:c)}))};
  const {stdout}=await promisify(execFile)('ffprobe',['-v','error','-show_entries','format=duration','-of','json',join(root,asset.src)],{windowsHide:true});
  const length=Number(JSON.parse(stdout).format.duration);
  if(affected.some(r=>r.clip.time[1]>length+.025))throw Error('Replacement is shorter than the retained source windows');
  const api=await native('studio/server/film.mjs');await api.editProjectFilm(root,current.rev,affected.map(r=>({op:'set',clip:r.clip.id,field:'src',value:asset.src})));
  const bindings=await readJson(join(meta(root),'bindings.json'),{events:[],cues:{}});
  for(const event of bindings.events||[])if(event.origin===origin&&event.src===row.clip.src)event.src=asset.src;
  for(const cue of Object.values(bindings.cues||{}))if((cue.origin||cue.clip)===origin&&cue.src===row.clip.src)cue.src=asset.src;
  await saveJson(join(meta(root),'bindings.json'),bindings);
  const result=await reconcile(root);return {...result,sourceReview:'New source windows retained; recheck speech and dramatic events against replacement media.'};
}
