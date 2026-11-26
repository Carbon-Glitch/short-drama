import {existsSync,readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {join} from 'node:path';

// OpenFilm 0.4.1 mkdtemp does not normalize long Windows prefixes itself.
// Node documents toNamespacedPath: https://nodejs.org/api/path.html#pathtonamespacedpathpath
export function patchWindowsPaths(packageRoot){
 if(process.platform!=='win32')return false;
 const metadata=JSON.parse(readFileSync(join(packageRoot,'package.json'),'utf8'));
 if(metadata.version!=='0.4.1')return false;
 const file=join(packageRoot,'src/render.mjs');let source=readFileSync(file,'utf8');
 const before='audioDir ??= mkdtempSync(join(dirname(work), `.parts-${process.pid}-audio-`));';
 const after='audioDir ??= mkdtempSync(toNamespacedPath(join(dirname(work), `.parts-${process.pid}-audio-`)));';
 if(source.includes(after))return false;
 if(!source.includes(before))throw Error('OpenFilm 渲染器版本与本机适配不匹配');
 const pathImport="import { basename, dirname, extname, join, resolve } from 'node:path';";
 if(!source.includes(pathImport))throw Error('OpenFilm 路径接口已变化');
 const backup=join(packageRoot,'director-desk-backups');mkdirSync(backup,{recursive:true});
 const original=join(backup,'render-0.4.1.mjs');if(!existsSync(original))writeFileSync(original,source);
 source=source.replace(pathImport,"import { basename, dirname, extname, join, resolve, toNamespacedPath } from 'node:path';").replace(before,after);
 writeFileSync(file,source);
 return true;
}
