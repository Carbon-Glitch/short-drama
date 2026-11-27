import {watch,existsSync,readFileSync,writeFileSync} from 'node:fs';
import {readFile} from 'node:fs/promises';
import {join,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {routes as deskRoutes} from './desk.mjs';
import * as sd from './core.mjs';

export default studio=>{
  const base=dirname(fileURLToPath(import.meta.url));
  const build=sd.hash(Buffer.concat(['server.mjs','desk.mjs','desk-live.mjs','desk-launch.mjs','core.mjs','audio.mjs','handoff.mjs','duck_plan.py','music_envelope.py'].map(name=>readFileSync(join(base,name)))));
  writeFileSync(join(sd.runtimeHome(),'state/short-drama-loaded.json'),JSON.stringify({pid:process.pid,build}));
  const watchers=new Map();
  function follow(root){
    if(watchers.has(root))return;
    let timer=null,working=false,again=false;
    async function refresh(){
      if(working){again=true;return;}working=true;
      try{const value=await sd.reconcile(root);studio.emit(root,{type:'synced',rev:value.rev,issues:value.issues});}
      catch(error){studio.log.warn(error.message);}
      finally{working=false;if(again){again=false;timer=setTimeout(refresh,180);}}
    }
    const observer=watch(root,{recursive:true},(_,name)=>{
      const file=String(name||'').replaceAll('\\','/');
      if(file==='film.html'||file==='short-drama.json'||file.endsWith('.vtt')||file==='.short-drama/bindings.json'||/^(剧本|视觉设定|分镜|图片提示词|视频提示词)\.md$/.test(file)||(/^assets\//.test(file)&&!/^assets\/treated\//.test(file))){
        clearTimeout(timer);timer=setTimeout(refresh,180);
      }
    });observer.unref();watchers.set(root,observer);
    let parent=root;while(dirname(parent)!==parent&&!existsSync(join(parent,'short-drama.json')))parent=dirname(parent);
    const production=join(parent,'.short-drama/production');
    if(existsSync(production)){
      const jobs=watch(production,{recursive:true},()=>{clearTimeout(timer);timer=setTimeout(refresh,300);});jobs.unref();
    }
  }
  async function rootOf(id){const value=await studio.project(id);follow(value.path);return value.path;}
  return {
    ...deskRoutes(studio),
    'GET /health':async()=>({build,pid:process.pid}),
    'GET /projects/:project/state':async({params})=>sd.state(await rootOf(params.project)),
    'POST /projects/:project/sync':async({params})=>sd.reconcile(await rootOf(params.project)),
    'POST /projects/:project/edit':async({params,req})=>{const body=await studio.readJson(req);return sd.patch(await rootOf(params.project),body.ops,{rev:body.rev,actor:'person'});},
    'PUT /projects/:project/document':async({params,req})=>{const body=await studio.readJson(req);return sd.updateDocument(await rootOf(params.project),body.name,body.text,body.revision);},
  };
};
