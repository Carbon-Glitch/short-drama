/** Read-only join review of the native rendered film, not a second renderer. */
import {readFile} from 'node:fs/promises';
import {dirname,basename,join,relative,resolve} from 'node:path';
import * as sd from './core.mjs';

export function joinWindows(film,kindOf,{fps=24,handle=1.5}={}){
  const clips=[];
  for(const [trackIndex,track] of film.tracks.entries()){
    if(track.hidden)continue;
    for(const clip of track.clips){
      if(clip.disabled||!['video','still','page'].includes(kindOf(clip)))continue;
      const speed=clip.speed||1,start=clip.at||0;
      const end=start+(clip.time[1]-clip.time[0])/speed;
      if(!Number.isFinite(end)||end<=start)continue;
      clips.push({id:clip.id,src:clip.src,track:trackIndex,start,end,source:clip.time,speed,
        shot:clip.attrs?.['data-shot-id']||clip.attrs?.['data-motion-id']||'',intent:clip.attrs?.['data-sd-intent']||''});
    }
  }
  const duration=Math.max(0,...clips.map(c=>c.end));
  const boundaries=[...new Set(clips.flatMap(c=>[Math.round(c.start*fps),Math.round(c.end*fps)]))]
    .filter(f=>f>0&&f<Math.round(duration*fps)).sort((a,b)=>a-b);
  return {fps,duration,clips,windows:boundaries.map(frame=>{
    const at=frame/fps;
    return {frame,at,start:Math.max(0,at-handle),end:Math.min(duration,at+handle),
      ending:clips.filter(c=>Math.round(c.end*fps)===frame).map(c=>c.id),
      starting:clips.filter(c=>Math.round(c.start*fps)===frame).map(c=>c.id),
      spanning:clips.filter(c=>c.start<at-.5/fps&&c.end>at+.5/fps).map(c=>c.id)};
  })};
}

const escape=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
export function reviewHtml(data,video){
  const serialized=JSON.stringify(data).replaceAll('<','\\u003c');
  return `<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>接点回看 · ${escape(data.label)}</title><style>
body{background:#131820;color:#edf0f5;font:16px system-ui;margin:24px auto;max-width:1100px;padding:0 18px}h1{font-size:26px}main{display:grid;grid-template-columns:minmax(240px,1fr) minmax(300px,1fr);gap:24px}video{width:100%;max-height:70vh;background:black}button{background:#253246;color:inherit;border:1px solid #56657a;border-radius:7px;padding:10px;margin:4px;cursor:pointer}button:focus{outline:2px solid #78d9c6}.active{border-color:#78d9c6}p,li{line-height:1.6}small{color:#aab9cb}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:13px system-ui}#list{max-height:45vh;overflow:auto}details{margin:20px 0}@media(max-width:720px){main{grid-template-columns:1fr}}
</style><h1>接点回看</h1><p>先正常速度看动作与声音，再逐帧定位。标记为画面层边界候选，叠层/叠化并不自动代表剪错。</p>
<small>导出快照 ${escape(data.identity.slice(0,12))} · 修改工程后重新预览，本页不会自动更新。</small>
<main><section><video id="video" controls preload="metadata" src="${escape(video)}"></video><div><button id="replay">重看本接点</button><button id="prev">前一帧</button><button id="next">后一帧</button><label><input id="loop" type="checkbox" checked>循环本窗口</label></div><p id="status"></p></section><section><div id="list"></div><pre id="detail"></pre></section></main>
<details><summary>上游参考、设计与接镜</summary><pre id="notes"></pre></details>
<p><small>观察：动作/运镜是否重启、视线方向、重复或冻帧、光色跳变、声音断裂。结论写既有制作记录；源窗仍在 film.html 修改。本页不自动判定审美通过。</small></p>
<script>const data=${serialized};
const video=document.getElementById('video'),list=document.getElementById('list'),detail=document.getElementById('detail'),status=document.getElementById('status');let selected=null;
function show(w){selected=w;video.currentTime=w.start;video.play().catch(()=>{});detail.textContent=JSON.stringify({at:w.at,ending:w.ending,starting:w.starting,spanning:w.spanning,clips:data.clips.filter(c=>[...w.ending,...w.starting,...w.spanning].includes(c.id))},null,2);for(const b of list.children)b.classList.toggle('active',Number(b.dataset.frame)===w.frame);}
for(const w of data.windows){const b=document.createElement('button');b.dataset.frame=w.frame;b.textContent=w.at.toFixed(3)+'s · '+(w.ending.join(', ')||'叠层中')+' → '+(w.starting.join(', ')||'图层结束');b.onclick=()=>show(w);list.appendChild(b);}
if(!data.windows.length)list.textContent='本次画面层没有内部接点。';
document.getElementById('notes').textContent=data.productionNotes.map(n=>n.document+' / '+n.section+' / '+n.field+'：'+n.text).join(String.fromCharCode(10,10))||'上游未写生成安排或接镜；按实际素材判断。';
document.getElementById('replay').onclick=()=>{if(selected)show(selected);};
for(const [id,delta] of [['prev',-1],['next',1]])document.getElementById(id).onclick=()=>{video.pause();video.currentTime=Math.max(0,Math.min(video.duration||data.duration,Math.round(video.currentTime*data.fps)/data.fps+delta/data.fps));};
video.ontimeupdate=()=>{status.textContent=video.currentTime.toFixed(3)+'s'+(selected?' · 接点 '+selected.at.toFixed(3)+'s':'');if(selected&&!video.paused&&document.getElementById('loop').checked&&video.currentTime>=selected.end)video.currentTime=selected.start;};
video.onended=()=>{if(selected&&document.getElementById('loop').checked){video.currentTime=selected.start;video.play().catch(()=>{});}};
video.onloadedmetadata=()=>{if(data.windows.length){selected=data.windows[0];video.currentTime=selected.start;}};
</script></html>`;
}

export async function writeReview(root,receipt){
  const snapshot=await sd.snapshot(root);
  if(snapshot.identity!==receipt.inputs.identity)throw Error('Project changed; render a current preview before reviewing joins');
  if(sd.hash(await readFile(receipt.output))!==receipt.outputHash)throw Error('Rendered media changed; render a current preview');
  const current=await sd.read(root),api=await sd.native('src/film-doc.mjs');
  const settings=await sd.readJson(join(root,'.short-drama/project.json'),{fps:24});
  const {collect}=await import('./handoff.mjs');const upstream=await collect(root);
  const data={...joinWindows(current.value,api.kindOf,{fps:settings.fps||24}),
    identity:snapshot.identity,outputHash:receipt.outputHash,label:basename(root),productionNotes:upstream.productionNotes||[]};
  const output=resolve(receipt.output),stem=output.replace(/\.[^/.\\]+$/,'')+'-接点';
  const html=stem+'.html',json=stem+'.json';
  const media=relative(dirname(html),output).split(/[/\\]/).map(encodeURIComponent).join('/');
  await sd.saveJson(json,data);await sd.atomic(html,reviewHtml(data,media));
  return {html,json,candidates:data.windows.length,artisticAccepted:false};
}
