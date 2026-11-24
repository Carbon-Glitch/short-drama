import {realpath,stat,mkdir} from 'node:fs/promises';
import {join} from 'node:path';
export async function register(path,sd){
 const root=await realpath(path);if(!(await stat(root)).isDirectory())throw Error('请选择项目目录');
 const id='desk-'+sd.hash(root).slice(0,24),dir=join(sd.runtimeHome(),'state','director-projects');
 await mkdir(dir,{recursive:true});await sd.saveJson(join(dir,id+'.json'),{root});return id;
}