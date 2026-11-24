// One file-system observer per registered project. Events describe files or explicitly named agent reports.
import {watch} from 'node:fs';
import {join,basename,dirname,relative,extname} from 'node:path';
import {realpath,readdir,stat,readFile,mkdir} from 'node:fs/promises';
import {randomUUID} from 'node:crypto';
import * as sd from './core.mjs';
const active=new Map(),docs={'剧本.md':'剧本','视觉设定.md':'Design','分镜.md':'分镜','图片提示词.md':'资产','视频提示词.md':'投产','剪辑单.md':'剪辑','film.html':'剪辑','short-drama.json':'开发'};
function stage(p){
 const n=basename(p),x=extname(n).toLowerCase();
 if(/(^|\/)\.short-drama\/progress\/[0-9a-f]{32}\.json$/.test(p))return '进展';
 if(docs[n])return docs[n];
 if(/(^|\/)项目开发\//.test(p))return '开发';
 if(/(^|\/)(审查|审阅)\//.test(p))return '回片';
 if(/(^|\/)成片\//.test(p)||(!p.includes('/')&&['.mp4','.mov','.webm','.srt','.vtt'].includes(x)))return '交付';
 if(/(^|\/)(\.short-drama\/production|制作运行)\//.test(p)){
   if(x!=='.json'||['workflow.json','uploads.json'].includes(n))return null;
   return /\/(runs|handles)\//.test(p)||/^job-/.test(n)?'回片':'投产';
 }
 if(n==='director.sqlite')return '导演意见';
 if(n==='design-pass.json')return 'Design';
 if(n==='bindings.json')return '剪辑';
 if(n==='render-result.json'||n==='preview-result.json')return '交付';
 if(n==='state.json'&&p.startsWith('.short-drama/'))return '投产';
 if(x==='.txt'&&n.includes('提示词'))return '投产';
 if(/(^|\/)输入\//.test(p)&&['.txt','.md'].includes(x))return '剧本';
 if(['.mp4','.mov','.webm'].includes(x))return '回片';
 if(['.wav','.mp3','.m4a','.png','.jpg','.jpeg','.webp'].includes(x))return '资产';
 if(['.srt','.vtt'].includes(x))return '剪辑';
 return null;
}
function skip(dir){return dir.split('/').some(n=>['.git','.film','node_modules','__pycache__','director-media','runtime','cache'].includes(n)||n.startsWith('.')&&n!=='.short-drama')}
function diff(old='',next=''){
 const a=old.split(/\r?\n/),b=next.split(/\r?\n/);let i=0,j=0;while(i<a.length&&i<b.length&&a[i]===b[i])i++;
 while(j<a.length-i&&j<b.length-i&&a[a.length-1-j]===b[b.length-1-j])j++;
 const left=a.slice(i,a.length-j),right=b.slice(i,b.length-j);
 return {line:i+1,removed:left.slice(0,24).join('\n').slice(0,2400),added:right.slice(0,24).join('\n').slice(0,2400),minus:left.length,plus:right.length};
}
function redact(s){return s.replace(/((?:api[_ -]?key|authorization|access[_ -]?token|secret[_ -]?key)\s*["'：:=是 ]+\s*)[^\s,"'}]+/gi,'$1[已隐藏]')}
async function scan(root,prev){
 const files={};let total=0;
 async function visit(dir){
  for(const f of await readdir(dir,{withFileTypes:true}).catch(()=>[])){
   const path=join(dir,f.name),key=relative(root,path).replaceAll('\\','/');
   if(f.isSymbolicLink()||skip(key))continue;
   if(f.isDirectory()){await visit(path);continue}
   const s=stage(key);if(!s||!f.isFile())continue;
   const st=await stat(path,{bigint:true}).catch(()=>null);if(!st)continue;
   const signature=String(st.mtimeNs)+':'+String(st.size);const was=prev[key];if(was?.signature===signature){files[key]=was;continue}
   const row={signature,stage:s,bytes:Number(st.size)};
   if(/\.(md|txt|srt|vtt)$/i.test(key)&&st.size<=524288n&&total<4_000_000){
    try{const txt=redact(await readFile(path,'utf8'));row.text=txt;total+=txt.length}catch{}
   }
   if(s==='进展'&&st.size<32768n){try{const x=JSON.parse(await readFile(path,'utf8'));if(x.id===basename(path,'.json')&&typeof x.message==='string')row.report={type:'report',reportedAt:x.at,actor:redact(String(x.actor||'未署名')).slice(0,64),stage:String(x.stage||'').slice(0,32),change:String(x.change||'进展').slice(0,40),message:redact(x.message).slice(0,2000),paths:Array.isArray(x.paths)?x.paths.slice(0,20).map(p=>String(p).slice(0,512)):[]}}catch{}}
   files[key]=row;
  }
 }
 await visit(root);return files;
}
function episode(path){return /^(?:剧集|episodes)\/([^/]+)\//.exec(path)?.[1]||null}
export async function observer(input){
 let root=await realpath(input);if(['剧集','episodes'].includes(basename(dirname(root))))root=dirname(dirname(root));
 if(active.has(root))return active.get(root);
 const result=create(root);active.set(root,result);try{return await result}catch(e){active.delete(root);throw e}
}
async function create(root){
 const dir=join(sd.runtimeHome(),'state','director-history'),file=join(dir,sd.hash(root).slice(0,24)+'.json');await mkdir(dir,{recursive:true});
 let history=await sd.readJson(file,{seq:0,events:[],files:null}),clients=new Set(),pending=null,chain=Promise.resolve();
 function queue(fn){const task=chain.then(fn);chain=task.catch(()=>{});return task}
 function event(e){const v={seq:++history.seq,at:new Date().toISOString(),...e};history.events.push(v);if(history.events.length>400)history.events.splice(0,history.events.length-400);return v}
 const send=(res,e)=>res.write('id: '+e.seq+'\ndata: '+JSON.stringify(e)+'\n\n');
 async function commit(list){await sd.saveJson(file,history);for(const e of list)for(const res of clients)if(!res.destroyed)send(res,e)}
 async function sweep(){
  const next=await scan(root,history.files||{});const out=[];
  if(history.files){for(const p of new Set([...Object.keys(next),...Object.keys(history.files)])){
   const a=history.files[p],b=next[p];if(a?.signature===b?.signature)continue;
   if(b?.report){out.push(event({...b.report,episode:episode(p)}));continue}
   out.push(event({type:'file',change:!a?'新增':!b?'删除':'调整',episode:episode(p),path:p,stage:(b||a).stage,bytes:b?.bytes||0,...(a?.text!==undefined||b?.text!==undefined?{diff:diff(a?.text,b?.text)}:{})}));
  }}
  const first=!history.files;if(first){for(const [p,b] of Object.entries(next).sort((a,b)=>String(a[1].report?.reportedAt).localeCompare(String(b[1].report?.reportedAt))))if(b.report)out.push(event({...b.report,episode:episode(p)}))}history.files=next;if(first||out.length)await commit(out);
 }
 await queue(sweep);
 const tick=()=>{if(!pending){pending=setTimeout(()=>{pending=null;queue(sweep)},300);pending.unref()}};
 let watcher;try{watcher=watch(root,{recursive:true},(_,n)=>{if(!n||!skip(String(n).replaceAll('\\','/')))tick()});watcher.on('error',()=>tick());watcher.unref()}catch{}
 const timer=setInterval(tick,2500);timer.unref();
 const api={
  recent(since=0){return {seq:history.seq,events:history.events.filter(e=>e.seq>since),limit:400}},
  report(v){return queue(async()=>{const e=event({type:'report',episode:v.episode||null,stage:String(v.stage||'').slice(0,32),actor:String(v.actor||'Agent').slice(0,64),change:String(v.change||'进展').slice(0,40),message:redact(String(v.message||'')).slice(0,2000)});await commit([e]);return e})},
  stream(req,res,since){res.writeHead(200,{'Content-Type':'text/event-stream; charset=utf-8','Cache-Control':'no-cache','X-Accel-Buffering':'no','Connection':'keep-alive'});res.write(': ready\n\n');for(const e of api.recent(since).events)send(res,e);clients.add(res);const pulse=setInterval(()=>res.write(': alive\n\n'),15000);res.on('close',()=>{clients.delete(res);clearInterval(pulse)})}
 };return api;
}
