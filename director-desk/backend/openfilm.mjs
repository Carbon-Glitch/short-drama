import {join,resolve} from 'node:path';
import {homedir} from 'node:os';
import {pathToFileURL} from 'node:url';
import {existsSync} from 'node:fs';
import {patchWindowsPaths} from './runtime-patches.mjs';

const runtime=resolve(process.env.SHORT_DRAMA_OPENFILM_HOME||join(homedir(),'Documents/Codex/tools/short-drama-openfilm-0.4.1'));
process.env.OPENFILM_HOME=join(runtime,'state');
const packageRoot=join(runtime,'node_modules/openfilm');
if(!existsSync(join(packageRoot,'studio/client.mjs')))throw Error('请先安装 OpenFilm 运行时');
const runtimePatched=patchWindowsPaths(packageRoot);
const {ensureStudio}=await import(pathToFileURL(join(packageRoot,'studio/client.mjs')));
const {openProject}=await import(pathToFileURL(join(packageRoot,'studio/server/projects.mjs')));
const folder=resolve(process.argv[2]);
if(!existsSync(join(folder,'film.html')))throw Error('这一集还没有剪辑工程');
const run=await ensureStudio(undefined,{fresh:runtimePatched});
const project=await openProject(folder,{create:false});
console.log(JSON.stringify({url:run.origin+'/open?'+new URLSearchParams({key:run.key,to:'/projects/'+project.id})}));
