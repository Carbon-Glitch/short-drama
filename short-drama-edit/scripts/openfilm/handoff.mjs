/** Source requirements point to the one editable film; no duplicate creative document. */
import {readFile,stat} from 'node:fs/promises';
import {existsSync} from 'node:fs';
import {join,dirname,resolve} from 'node:path';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {hash,readJson,saveJson,native} from './core.mjs';

export const documents=['剧本.md','视觉设定.md','分镜.md','图片提示词.md','视频提示词.md'];
const norm=s=>s.normalize('NFKC').toLowerCase().replace(/[^\p{L}\p{N}]/gu,'');
const allRows=film=>film.tracks.flatMap(track=>track.clips.map(clip=>({clip,track})));
const mediaHashes=new Map();
const audioStreams=new Map();
async function hasAudio(root,clip){
  const file=join(root,clip.src),info=await stat(file),key=file+'|'+info.size+'|'+info.mtimeMs;
  if(!audioStreams.has(key)){
    const {stdout}=await promisify(execFile)('ffprobe',['-v','error','-show_entries','stream=codec_type','-of','json',file],{windowsHide:true});
    audioStreams.set(key,JSON.parse(stdout).streams.some(s=>s.codec_type==='audio'));
  }
  return audioStreams.get(key);
}
async function fileHash(path){const info=await stat(path);const key=path+'|'+info.size+'|'+info.mtimeMs;if(!mediaHashes.has(key))mediaHashes.set(key,hash(await readFile(path)));return mediaHashes.get(key);}
async function sourceIdentity(root,target){
  if(!target.clip||!target.roles.includes('audio')&&!/\.(mp4|mov|webm)$/i.test(target.clip.src))return {};
  const raw=target.clip.attrs?.['data-sd-audio'];const src=raw?JSON.parse(raw).source:target.clip.src;
  const path=join(root,src);if(!existsSync(path))return {src,sourceHash:null};
  return {src,sourceHash:await fileHash(path)};
}
export async function collect(root){
  const upstream={},requirements=[],references=[],productionNotes=[];
  let project=root;
  const settings=await readJson(join(root,'.short-drama/project.json'),{});
  if(settings.projectRoot)project=resolve(root,settings.projectRoot);
  else{while(!existsSync(join(project,'short-drama.json'))&&dirname(project)!==project)project=dirname(project);if(!existsSync(join(project,'short-drama.json')))project=root;}
  if(existsSync(join(project,'short-drama.json')))upstream['project:short-drama.json']=hash(await readFile(join(project,'short-drama.json')));
  for(const document of documents){
    let text;try{text=await readFile(join(root,document),'utf8');}catch(e){if(e.code==='ENOENT')continue;throw e;}
    upstream[document]=hash(text);let section='',occurrences=new Map();
    for(const [index,line] of text.split(/\r?\n/).entries()){
      const heading=line.match(/^##\s+([^\s·]+)(?:\s*·)?/);if(heading)section=heading[1];
      if(heading&&document==='视觉设定.md')section=line.replace(/^##\s+/,'').trim();
      let kind=null,content=line.trim(),role;
      if(['分镜.md','视频提示词.md'].includes(document)){
        const note=content.match(/^[-*]\s*(生成安排|接镜)[：:]\s*(.+)$/);
        if(note)productionNotes.push({document,section,line:index+1,field:note[1],text:note[2]});
      }
      if(document==='剧本.md'){
        const tagged=content.match(/^\[(画面文字|SFX|转场|连续性|声音制作)\]\s*(.+)/);
        const dialogue=content.match(/^(?:\[(?:VO|OS)\]\s*)?([\p{L}][\p{L}\p{N}_·-]{0,39})(?:[（(][^）)]*[）)])?[：:]\s*(.+)$/u);
        if(tagged){kind=tagged[1];content=tagged[2];role=['SFX','声音制作'].includes(kind)?'audio':kind==='画面文字'?'graphic':'picture';}
        else if(dialogue&&section){kind='dialogue';content=dialogue[2];role='audio';}
        else if(section&&content&&!/^(#|\*\*|<!--)/.test(content)){kind='action';role='picture';}
      }else if(document==='分镜.md'&&heading&&/^SHOT-/.test(section)){kind='shot';role='picture';}
      else if(document==='视觉设定.md'&&section){
        const design=content.match(/^[-*]\s*(设计重点|声音重点)[：:]\s*(.+)$/);
        if(design){kind='design';role=design[1]==='声音重点'?'audio':'picture';content=design[2];}
      }
      if(kind){const base=document+'|'+section+'|'+kind+'|'+norm(content);const n=occurrences.get(base)||0;occurrences.set(base,n+1);
        requirements.push({id:'REQ-'+hash(base+'|'+n).slice(0,16),document,section,line:index+1,kind,role,text:content});}
      // Existing REF grammar: path before the Chinese reference title.
      for(const match of line.matchAll(/(?:·|：)\s*([^·；\n《》]+?\.(?:png|jpe?g|webp|wav|mp3|m4a|mp4|mov|flac|ogg))《/gi)){
        const path=match[1].trim();references.push({document,line:index+1,path,exists:existsSync(join(project,path))});
      }
      for(const match of line.matchAll(/声音参考[：:]\s*([^（(\n]+?\.(?:wav|mp3|m4a|flac|ogg))/gi)){
        const path=match[1].trim();references.push({document,line:index+1,path,exists:existsSync(join(project,path))});
      }
    }
  }
  for(const ref of references)if(ref.exists)upstream['ref:'+ref.path]=await fileHash(join(project,ref.path));
  return {upstream,revision:hash(JSON.stringify(upstream)),requirements,references,productionNotes,projectRoot:project};
}

async function targetsOf(root,film){
  const api=await native('src/film-doc.mjs'),captions=await native('src/captions.mjs');const targets=new Map();
  for(const {clip,track} of allRows(film)){
    const kind=api.kindOf(clip);const audible=['sound','video'].includes(kind)&&!track.muted&&clip.volume!==0&&await hasAudio(root,clip);
    targets.set('clip:'+clip.id,{clip,track,roles:[...(kind==='sound'?[]:['picture','graphic']),...(audible?['audio']:[])],active:!track.hidden&&!clip.disabled&&!(kind==='sound'&&!audible)});
  }
  for(const track of film.tracks)if(track.captions){
    const vtt=captions.readVtt(await readFile(join(root,track.captions.src),'utf8'));
    for(const cue of vtt.cues)targets.set('cue:'+track.captions.src+'#'+cue.id,{cue,track,roles:['caption'],active:!track.hidden});
  }
  return targets;
}
export async function inspectHandoff(root,film,bindings){
  const source=await collect(root),targets=await targetsOf(root,film),handoff=bindings.handoff||{},issues=[];
  const issue=(kind,detail={})=>issues.push({kind,severity:'error',...detail});
  if(source.requirements.length&&!handoff.upstream)issue('handoff_unbound',{purpose:'将前期交付事项对应到当前工程',count:source.requirements.length});
  if(handoff.upstream)for(const [doc,revision] of Object.entries({...handoff.upstream,...source.upstream})){
    if(handoff.upstream[doc]!==source.upstream[doc])issue('upstream_changed',{document:doc,purpose:'前期内容已变化，核对受影响项'});
  }
  for(const ref of source.references)if(!ref.exists)issue('upstream_reference_missing',ref);
  for(const req of source.requirements){
    const binding=handoff.items?.[req.id];
    if(binding?.disposition==='omitted'&&binding.reason?.trim())continue;
    if(!binding?.targets?.length){issue('requirement_unbound',{id:req.id,document:req.document,line:req.line,purpose:req.text});continue;}
    const resolved=binding.targets.map(key=>targets.get(key));
    if(resolved.some(t=>!t?.active)||!resolved.some(t=>t?.roles.includes(req.role)))issue('requirement_target_missing',{id:req.id,purpose:req.text,targets:binding.targets});
  }
  // Reverse lookup matters: a removed cue never appears in a forward cue traversal.
  for(const key of Object.keys(bindings.cues||{})){
    const disposition=handoff.adopted?.['cue:'+key];
    const omitted=bindings.omissions?.cues?.[key]?.reason?.trim()||(disposition?.disposition==='omitted'&&disposition.reason?.trim());
    if(!targets.get('cue:'+key)?.active&&!omitted)issue('required_cue_missing',{cue:key});
  }
  // Registered adopted layers survive removal from the timeline and can be intentionally omitted.
  for(const [key,record] of Object.entries(handoff.adopted||{})){
    if(record.disposition==='omitted'&&record.reason?.trim())continue;
    if(!targets.get(key)?.active)issue('adopted_layer_missing',{target:key});
    else if(record.sourceHash){const now=await sourceIdentity(root,targets.get(key));if(now.sourceHash!==record.sourceHash||now.src!==record.src)issue('adopted_source_changed',{target:key,purpose:'采用素材版本已变化，核对源窗与表演'});}
  }
  return {...source,issues,items:handoff.items||{},adopted:handoff.adopted||{}};
}

export async function bindHandoff(root,film,payload){
  const source=await collect(root);if(payload.revision!==source.revision)throw Error('前期版本变化，请读取 handoff 后更新映射');
  const path=join(root,'.short-drama/bindings.json'),bindings=await readJson(path,{schema:1,events:[],cues:{}});
  const previous=bindings.handoff||{};const targets=await targetsOf(root,film);
  const items={...(previous.items||{}),...(payload.items||{})};
  for(const [id,item] of Object.entries(payload.items||{})){
    if(!source.requirements.some(r=>r.id===id))throw Error('Unknown source requirement '+id);
    if(item.disposition==='omitted'){if(!item.reason?.trim())throw Error('说明此次省略的创作理由: '+id);}
    else if(!item.targets?.length||item.targets.some(key=>!targets.has(key)))throw Error('采用项需指向实际 clip/cue: '+id);
  }
  const adopted={...(previous.adopted||{})};
  if(payload.adoptCurrent!==false)for(const [key,value] of targets)if(value.active&&(!adopted[key]||payload.refreshSources?.includes(key)))adopted[key]=await sourceIdentity(root,value);
  for(const [key,value] of Object.entries(payload.dispositions||{})){
    if(!adopted[key]&&!targets.has(key))throw Error('Unknown adopted layer '+key);
    if(value.disposition==='omitted'&&!value.reason?.trim())throw Error('说明此次省略的创作理由: '+key);
    adopted[key]=value;
  }
  bindings.handoff={schema:1,upstream:source.upstream,items,adopted};
  if(payload.omissions)bindings.omissions=payload.omissions;
  await saveJson(path,bindings);return inspectHandoff(root,film,bindings);
}
