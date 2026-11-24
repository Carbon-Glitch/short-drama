import {realpath,stat,mkdir,readdir} from 'node:fs/promises';
import {join,dirname,basename} from 'node:path';
import {existsSync} from 'node:fs';
export async function register(path,sd){
 let root=await realpath(path);if(!(await stat(root)).isDirectory())throw Error('请选择项目目录');
 if(['剧集','episodes'].includes(basename(dirname(root))))root=dirname(dirname(root));
 const id='desk-'+sd.hash(root).slice(0,24),dir=join(sd.runtimeHome(),'state','director-projects');
 await mkdir(dir,{recursive:true});await sd.saveJson(join(dir,id+'.json'),{root});return id;
}
let pending,checked=0;
export async function discover(sd,extra){
 const dir=join(sd.runtimeHome(),'state','director-projects'),file=join(sd.runtimeHome(),'state','director-roots.json');
 await mkdir(dir,{recursive:true});
 if(extra){let roots=await sd.readJson(file,[]);const root=await realpath(extra);if(!(await stat(root)).isDirectory()||dirname(root)===root)throw Error('请选择短剧存放目录');if(!roots.includes(root)){roots.push(root);await sd.saveJson(file,roots)}checked=0;}
 if(pending)return pending;if(Date.now()-checked<4000)return;
 pending=(async()=>{
 const records=await readdir(dir);const roots=new Set(await sd.readJson(file,[]));
 for(const n of records.filter(n=>n.endsWith('.json'))){const v=await sd.readJson(join(dir,n));if(v?.root&&existsSync(v.root))roots.add(dirname(v.root))}
 let visited=0;
 async function scan(root,depth=0){
 if(++visited>6000||depth>5)return;
 const entries=await readdir(root,{withFileTypes:true}).catch(()=>[]);const names=new Set(entries.map(e=>e.name));
 if(names.has('short-drama.json')||names.has('剧本.md')||names.has('视觉设定.md')){await register(root,sd);return}
 for(const e of entries)if(e.isDirectory()&&!e.isSymbolicLink()&&!e.name.startsWith('.')&&!['node_modules','制作成果','制作运行','assets','输入','系列资产','cache','work','outputs'].includes(e.name))await scan(join(root,e.name),depth+1);
 }
 for(const root of roots)await scan(root);
 checked=Date.now();
 })().finally(()=>pending=null);return pending;
}
