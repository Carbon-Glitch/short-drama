/** Per-source sound treatment only. OpenFilm owns placement, gain, fades and final mixing. */
import {readFile,mkdir} from 'node:fs/promises';
import {existsSync} from 'node:fs';
import {join,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {hash,native,read,readJson} from './core.mjs';

function dbEnvelope(points){
  if(!points?.length)return null;
  if(points.some((p,i)=>!Number.isFinite(p.time)||!Number.isFinite(p.db)||(i&&p.time<=points[i-1].time)))throw Error('Invalid dB envelope');
  let expression=String(points.at(-1).db);
  for(let i=points.length-2;i>=0;i--){const a=points[i],b=points[i+1];expression=`if(lt(t,${b.time}),${a.db}+(${b.db-a.db})*(t-${a.time})/${b.time-a.time},${expression})`;}
  return `volume='pow(10,(if(lt(t,${points[0].time}),${points[0].db},${expression}))/20)':eval=frame`;
}
const numeric=(v,name)=>{if(!Number.isFinite(v))throw Error('Invalid '+name);return v;};

export async function prepareAudio(root){
  const current=await read(root),ops=[];
  const settings=await readJson(join(root,'.short-drama/project.json'),{});const duck=settings.audioMaster?.duck_music;
  let duckPoints=[];
  if(duck){
    const all=current.value.tracks.flatMap(t=>t.hidden||t.muted?[]:t.clips.filter(c=>!c.disabled&&c.volume!==0));
    const duration=Math.max(0,...all.map(c=>(c.at||0)+(c.time[1]-c.time[0])/(c.speed||1)));
    const windows=all.filter(c=>['dialogue','native'].includes(c.attrs?.['data-sd-bus'])).map(c=>[c.at||0,(c.at||0)+(c.time[1]-c.time[0])/(c.speed||1)]);
    const {stdout}=await promisify(execFile)('python',[join(dirname(fileURLToPath(import.meta.url)),'duck_plan.py'),JSON.stringify({config:duck,duration,windows})],{windowsHide:true});duckPoints=JSON.parse(stdout);
  }
  for(const track of current.value.tracks)for(const clip of track.clips){
    const raw=clip.attrs?.['data-sd-audio'];if(!raw||track.locked)continue;
    const recipe=JSON.parse(raw),source=join(root,recipe.source),filters=[];
    const post=[];
    for(const effect of recipe.fx||[]){
      const n=(key,fallback)=>numeric(effect[key]??fallback,key);
      if(effect.type==='eq')post.push(`equalizer=f=${n('hz')}:t=q:w=${n('q',1)}:g=${n('db')}`);
      else if(effect.type==='highpass'||effect.type==='lowpass')post.push(`${effect.type}=f=${n('hz')}`);
      else if(effect.type==='denoise')post.push(`afftdn=nf=${n('noise_floor',-30)}`);
      else if(effect.type==='compressor')post.push(`acompressor=threshold=${n('threshold',.2)}:ratio=${n('ratio',2)}:attack=${n('attack_ms',15)}:release=${n('release_ms',150)}`);
      else if(effect.type==='delay')post.push(`aecho=0.8:0.8:${n('ms',60)}:${n('decay',.15)}`);
      else throw Error('Unmapped sound effect '+effect.type);
    }
    if(recipe.pan!==undefined){const pan=numeric(recipe.pan,'pan');if(Math.abs(pan)>1)throw Error('pan outside -1..1');post.unshift(`pan=stereo|c0=${Math.min(1,1-pan)}*c0|c1=${Math.min(1,1+pan)}*c1`);}
    for(const item of recipe.eq||[]){
      if(![item.frequency,item.width,item.gain].every(Number.isFinite))throw Error('Invalid EQ '+clip.id);
      filters.push(`equalizer=f=${item.frequency}:t=q:w=${item.width}:g=${item.gain}`);
    }
    const points=recipe.envelope||[];
    if(points.length){
      if(points.some((p,i)=>!Number.isFinite(p.t)||!Number.isFinite(p.v)||p.t<0||p.v<0||(i&&p.t<=points[i-1].t)))throw Error('Invalid source-time envelope '+clip.id);
      let expression=String(points.at(-1).v);
      for(let i=points.length-2;i>=0;i--){const a=points[i],b=points[i+1];expression=`if(lt(t,${b.t}),${a.v}+(${b.v-a.v})*(t-${a.t})/${b.t-a.t},${expression})`;}
      expression=`if(lt(t,${points[0].t}),${points[0].v},${expression})`;
      filters.push(`volume='${expression}':eval=frame`);
    }
    const authored=dbEnvelope(recipe.envelopeDb);if(authored)filters.push(authored);
    filters.push(...post);
    if(clip.attrs?.['data-sd-bus']==='music'&&duckPoints.length){
      const points=duckPoints.map(p=>({time:clip.time[0]+(p.time-(clip.at||0))*(clip.speed||1),db:p.db}));
      const filter=dbEnvelope(points);if(filter)filters.push(filter);
    }
    if(!filters.length)continue;
    const key=hash(Buffer.concat([await readFile(source),Buffer.from('pcm-v3'+JSON.stringify({recipe,filters}))])).slice(0,20);
    const src='assets/treated/'+key+'.wav',out=join(root,src);
    if(!existsSync(out)){
      await mkdir(join(root,'assets/treated'),{recursive:true});
      const {stdout}=await promisify(execFile)('ffprobe',['-v','error','-show_entries','format=duration','-of','json',source],{windowsHide:true});
      const length=Number(JSON.parse(stdout).format.duration);
      // AAC decoder delay can make PCM shorter than the source clock by a few samples.
      // Preserve that clock with silence at EOF, without stretching or repeating speech.
      await promisify(execFile)('ffmpeg',['-v','error','-y','-i',source,'-vn','-af',[...filters,'apad'].join(','),'-t',String(length),'-ar','48000','-ac','2','-c:a','pcm_s24le',out],{windowsHide:true});
    }
    if(clip.src!==src)ops.push({op:'fields',clip:clip.id,fields:{src,sound:null}});
  }
  if(ops.length){const api=await native('studio/server/film.mjs');await api.editProjectFilm(root,current.rev,ops);}
}
