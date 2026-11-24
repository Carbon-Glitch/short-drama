import {join,resolve,relative,dirname,basename,extname,isAbsolute,sep} from 'node:path';
import {readFile,readdir,realpath,stat,mkdir} from 'node:fs/promises';
import {existsSync,createReadStream} from 'node:fs';
import {createHash} from 'node:crypto';
import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {register} from './desk-launch.mjs';
import {observer} from './desk-live.mjs';
import * as sd from './core.mjs';
const base=dirname(fileURLToPath(import.meta.url)),reg=()=>join(sd.runtimeHome(),'state','director-projects');
async function where(studio,id){return /^desk-[a-f0-9]{24}$/.test(id)?(await sd.readJson(join(reg(),id+'.json'))).root:(await studio.project(id)).path;}
async function child(root,p){const abs=await realpath(p);const d=relative(root,abs);if(d.startsWith('..'+sep)||d==='..'||isAbsolute(d))throw Error('超出项目');return abs;}
function py(mode,root,ep,body){return new Promise((ok,fail)=>{
 const p=spawn(process.env.SHORT_DRAMA_PYTHON||'python',['-B','-X','utf8',join(base,'director_desk.py'),mode,root,...(ep?[ep]:[])],{windowsHide:true,stdio:['pipe','pipe','pipe']});let out='',err='';
 p.stdout.setEncoding('utf8').on('data',s=>out+=s);p.stderr.setEncoding('utf8').on('data',s=>err+=s);p.on('error',fail);p.on('close',c=>{try{if(c)throw Error(err.trim().split('\n').at(-1)||'读取失败');ok(JSON.parse(out))}catch(e){fail(e)}});p.stdin.on('error',()=>{});p.stdin.end(body?JSON.stringify(body):undefined);
});}
const mime={'.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp','.wav':'audio/wav','.mp3':'audio/mpeg','.m4a':'audio/mp4','.mp4':'video/mp4','.webm':'video/webm','.mov':'video/quicktime','.srt':'text/plain; charset=utf-8','.vtt':'text/vtt; charset=utf-8'};
export function routes(studio){
 const map=new Map(), hashes=new Map();
 async function checkHash(p){const st=await stat(p,{bigint:true}),sig=String(st.mtimeNs)+':'+st.size+':'+st.ctimeNs,old=hashes.get(p);if(old?.sig===sig)return old.hash;const h=createHash('sha256');for await(const chunk of createReadStream(p))h.update(chunk);const hash=h.digest('hex');hashes.set(p,{sig,hash});return hash}
 const project=async ctx=>{const root=await realpath(await where(studio,ctx.params.project));return {root,ep:ctx.url.searchParams.get('episode')||''};};
 async function load(ctx){
   const {root,ep}=await project(ctx),d=await py('state',root,ep);const pr=['剧集','episodes'].includes(basename(dirname(root)))?dirname(dirname(root)):root;
   const folder=await child(pr,[join(pr,'剧集',d.episode),join(pr,'episodes',d.episode),root].find(p=>existsSync(p)&&basename(p)===d.episode)||root);
   const files=new Map(d.media.map(m=>[m.id,resolve(pr,m.path)]));
   for(const v of Object.values(d.decisions))if(v?.asset){const a=v.asset,arch=join(folder,'.short-drama/director-media',a.id+extname(a.path).toLowerCase());if(/^[a-f0-9]{32}$/.test(a.id)&&existsSync(arch))files.set(a.id,arch);}
   const k=ctx.params.project+':'+ep;map.set(k,{pr,folder,files});return {d,pr,folder,files};
 }
 const prefix='/projects/:project/desk';
 return {
 ['GET '+prefix+'/projects']:async()=>{const ids=(await readdir(reg()).catch(()=>[])).filter(n=>/^desk-[a-f0-9]{24}\.json$/.test(n));const list=[];for(const n of ids){const v=await sd.readJson(join(reg(),n));if(existsSync(v.root))list.push({id:n.slice(0,-5),name:basename(v.root),path:v.root})}return list},
 ['POST '+prefix+'/register']:async ctx=>{const b=await studio.readJson(ctx.req);if(typeof b.path!=='string'||!isAbsolute(b.path))throw Error('请输入本机项目的完整目录');const path=await realpath(b.path);if(dirname(path)===path)throw Error('请选择项目目录而非整个磁盘');const id=await register(path,sd);await observer(path);return {id}},
 ['GET '+prefix+'/overview']:async()=>{const result=[];for(const n of (await readdir(reg()).catch(()=>[])).filter(x=>/^desk-[a-f0-9]{24}\.json$/.test(x))){const v=await sd.readJson(join(reg(),n));if(!existsSync(v.root))continue;const o=await observer(v.root);result.push({id:n.slice(0,-5),name:basename(v.root),path:v.root,latest:o.recent().events.at(-1)||null})}return result},
 ['GET '+prefix+'/history']:async ctx=>(await observer((await project(ctx)).root)).recent(Number(ctx.url.searchParams.get('since')||0)),
 ['GET '+prefix+'/events']:async ctx=>(await observer((await project(ctx)).root)).stream(ctx.req,ctx.res,Number(ctx.req.headers['last-event-id']||ctx.url.searchParams.get('since')||0)),
 ['POST '+prefix+'/progress']:async ctx=>{const v=await studio.readJson(ctx.req);if(!String(v.message||'').trim())throw Error('进展内容为空');return (await observer((await project(ctx)).root)).report(v)},
 ['GET '+prefix]:async(ctx)=>{const {res}=ctx;await observer((await project(ctx)).root);res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store','Referrer-Policy':'no-referrer','X-Content-Type-Options':'nosniff'});res.end(await readFile(join(base,'desk.html')))},
 ['GET '+prefix+'/data']:async ctx=>(await load(ctx)).d,
 ['POST '+prefix+'/decide']:async ctx=>{const {root,ep}=await project(ctx);return py('action',root,ep,await studio.readJson(ctx.req))},
 ['POST '+prefix+'/write']:async ctx=>{const {folder,d}=await load(ctx),b=await studio.readJson(ctx.req);if(d.decisions["lock:"+b.name])throw Error("文档已锁定，请先解锁");if(b.name==='剧本.md'&&Object.entries(d.decisions).some(([k,v])=>k.startsWith('line:')&&v&&!String(b.text).includes(v)))throw Error('修改影响了锁定原句');if(!d.docs[b.name]||b.rev!==d.docs[b.name].rev||typeof b.text!=='string')throw Error('文档已变化，请刷新');const original=await readFile(join(folder,b.name));if(sd.hash(original)!==b.rev)throw Error('文档已变化');return sd.updateDocument(folder,b.name,b.text,sd.hash(original.toString('utf8')))},
 ['GET '+prefix+'/verify/:id']:async ctx=>{const {d,folder,files,pr}=await load(ctx);const a=d.media.find(x=>x.id===ctx.params.id&&x.exportCandidate);
  if(!a||!d.render.timelineCurrent)return {ok:false,reason:'没有与当前时间线匹配的导出回执'};
  if(await checkHash(await child(pr,files.get(a.id)))!==d.render.outputHash)return {ok:false,reason:'成片已被替换'};
  const receipt=await sd.readJson(join(folder,'.short-drama/render-result.json'));const changed=[];
  for(const [name,expected] of Object.entries(receipt.inputs?.files||{})){try{if(await checkHash(await child(pr,resolve(folder,name)))!==expected)changed.push(name)}catch{changed.push(name)}}
  return {ok:changed.length===0,reason:changed.length?'导出后来源发生变化：'+changed.join('、'):''}},
 ['POST '+prefix+'/timeline']:async ctx=>{const {folder,d}=await load(ctx);if(!d.hasFilm)throw Error('此集还没有剪辑工程');const projects=await sd.native('studio/server/projects.mjs');const p=await projects.openProject(folder,{create:false});return {id:p.id}},
 ['POST '+prefix+'/replace']:async ctx=>{const {d,files,folder,pr}=await load(ctx),b=await studio.readJson(ctx.req),a=d.media.find(x=>x.id===b.media&&x.kind==='video');if(!a||!d.hasFilm||!b.src)throw Error('请选择真实源片和剪辑项');return sd.replaceSource(folder,{clip:b.clip,file:await child(pr,files.get(a.id)),expectedSrc:b.src})},
 ['GET '+prefix+'/file/:id']:async ctx=>{const {req,res,params,url}=ctx,k=params.project+':'+(url.searchParams.get('episode')||'');let m=map.get(k);if(!m?.files.has(params.id))m=await load(ctx);if(!m.files.has(params.id))throw new studio.HttpError(404,'媒体版本不存在');
   let path=await child(m.pr,m.files.get(params.id));const s=await stat(path);const archived=path.includes(sep+'director-media'+sep);
   if(!archived){const id=sd.hash(relative(m.pr,path).split(sep).join('/')+'|'+s.size+'|'+(await stat(path,{bigint:true})).mtimeNs).slice(0,32);if(id!==params.id)throw new studio.HttpError(409,'素材已换版，请刷新');}
   const headers={'Accept-Ranges':'bytes','Content-Type':mime[extname(path).toLowerCase()]||'application/octet-stream','X-Content-Type-Options':'nosniff','Cache-Control':'private, max-age=0'};let lo=0,hi=s.size-1;
   if(req.headers.range){const r=/^bytes=(\d*)-(\d*)$/.exec(req.headers.range);if(!r||(!r[1]&&!r[2])){res.writeHead(416);res.end();return}if(r[1]){lo=Number(r[1]);if(r[2])hi=Math.min(hi,Number(r[2]))}else lo=Math.max(0,s.size-Number(r[2]));if(lo>hi||lo>=s.size){res.writeHead(416,{'Content-Range':'bytes */'+s.size});res.end();return}headers['Content-Range']='bytes '+lo+'-'+hi+'/'+s.size;}
   res.writeHead(req.headers.range?206:200,{...headers,'Content-Length':Math.max(0,hi-lo+1)});if(s.size){const stream=createReadStream(path,{start:lo,end:hi});stream.on('error',()=>res.destroy());res.on('close',()=>stream.destroy());stream.pipe(res)}else res.end()
 }
 };
}
