import {parseArgs} from 'node:util';
import {readFile,mkdir,copyFile} from 'node:fs/promises';
import {join,resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import * as sd from './core.mjs';

const {values,positionals}=parseArgs({allowPositionals:true,options:{root:{type:'string'},input:{type:'string'},out:{type:'string'},preview:{type:'boolean'},actor:{type:'string'}}});
const command=positionals[0];const root=resolve(values.root||'.');
process.env.OPENFILM_HOME=join(sd.runtimeHome(),'state');
process.env.OPENFILM_SHARED_HOME=join(sd.runtimeHome(),'state');
process.env.OPENFILM_NO_UPDATE_CHECK='1';
process.env.OPENFILM_STUDIO_PORT='4757';
const payload=values.input?JSON.parse(await readFile(values.input,'utf8')):{};
try{
  let result;
  if(command==='desk'){
    const {register}=await import('../../assets/openfilm-plugin/desk-launch.mjs');const id=await register(root,sd);
    const client=await sd.native('studio/client.mjs');let run=await client.ensureStudio();const path='/api/plugins/short-drama/projects/'+id+'/desk';
    const headers={'x-studio-key':run.key};
    const probe=await fetch(run.origin+path,{headers});await probe.arrayBuffer();
    const names=['server.mjs','desk.mjs','desk-live.mjs','desk-launch.mjs','core.mjs','audio.mjs','handoff.mjs','duck_plan.py','music_envelope.py'];
    const dir=join(sd.packageHome(),'plugins/short-drama');const expected=sd.hash(Buffer.concat(await Promise.all(names.map(n=>readFile(join(dir,n))))));
    const loaded=await sd.readJson(join(sd.runtimeHome(),'state/short-drama-loaded.json'),{});
    if(probe.status===404||loaded.build!==expected){run=await client.ensureStudio(undefined,{fresh:true});const verify=await fetch(run.origin+path,{headers:{'x-studio-key':run.key}});if(!verify.ok)throw Error('Studio 正在运行旧插件；结束导出后再打开导演台');}
    result={url:run.origin+path,launch:run.origin+'/open?'+new URLSearchParams({key:run.key,to:path}),project:id};
  }else if(command==='init')result=await sd.init(root,payload);
  else if(command==='state')result=await sd.state(root);
  else if(command==='check')result=await sd.reconcile(root);
  else if(command==='sync'||command==='report')result=await sd.reconcile(root);
  else if(command==='patch')result=await sd.patch(root,payload.ops,{rev:payload.rev,actor:values.actor||'agent'});
  else if(command==='import-asset')result=await sd.importAsset(root,payload.file);
  else if(command==='replace-source')result=await sd.replaceSource(root,payload);
  else if(command==='handoff')result=(await sd.state(root)).handoff;
  else if(command==='seams'){
    const receipt=await sd.readJson(join(root,'.short-drama',values.preview?'preview-result.json':'render-result.json'));
    if(!receipt)throw Error('Render a preview or final film first');
    const {writeReview}=await import('./seams.mjs');result=await writeReview(root,receipt);
  }
  else if(command==='bind-handoff'){
    const {bindHandoff}=await import('./handoff.mjs');const current=await sd.read(root);
    if(payload.filmRev&&payload.filmRev!==current.rev)throw Error('时间线已变化，请读取最新版本后更新交接');
    await bindHandoff(root,current.value,payload);result=await sd.reconcile(root);
  }
  else if(command==='verify'){
    const current=await sd.reconcile(root);if(current.issues.some(i=>i.severity==='error'))throw Error('交接尚有缺项或上游变化: '+JSON.stringify(current.issues));
    const receipt=await sd.readJson(join(root,'.short-drama',values.preview?'preview-result.json':'render-result.json'));
    if(!receipt)throw Error('No export receipt');
    if((await sd.snapshot(root)).identity!==receipt.inputs.identity)throw Error('Project inputs changed after export');
    if(sd.hash(await readFile(receipt.output))!==receipt.outputHash)throw Error('Export file changed');
    result={...receipt,verified:true};
  }
  else if(command==='open'){
    const client=await sd.native('studio/client.mjs');result=await client.openInStudio(root);
  }else if(command==='render'){
    if(!values.preview && (await import('node:fs')).existsSync(join(root,'.short-drama','director.sqlite'))){
      const {execFileSync}=await import('node:child_process');
      execFileSync(process.env.SHORT_DRAMA_PYTHON||'python',['-B','-X','utf8',fileURLToPath(new URL('../../../short-drama/scripts/director_desk.py',import.meta.url)),'gate',root,(await import('node:path')).basename(root),'交付'],{windowsHide:true});
    }
    await sd.reconcile(root);
    const inputs=await sd.snapshot(root);
    const state=await sd.state(root);
    const errors=state.issues.filter(i=>i.severity==='error');if(errors.length&&!values.preview)throw Error(JSON.stringify(errors));
    const settings=await sd.readJson(join(root,'.short-drama/project.json'),{fps:24});
    const out=resolve(values.out||join(root,'制作成果/成片',values.preview?'预览.mp4':'成片.mp4'));
    await mkdir(dirname(out),{recursive:true});
    const renderer=await sd.native('src/render.mjs');
    const options={out,fps:settings.fps,workers:settings.workers||2};
    if(values.preview)options.scale=Math.min(1,540/state.stage.w);
    if(settings.loudness!==undefined)options.loudness=settings.loudness;
    const nativeReport=await renderer.render([root],options);
    if((await sd.snapshot(root)).identity!==inputs.identity)throw Error('Project changed during export; rendered file is stale, no delivery receipt written');
    result={output:out,filmRevision:state.rev,inputs,outputHash:sd.hash(await readFile(out)),engine:'OpenFilm '+sd.VERSION,preview:!!values.preview,issues:state.issues,nativeReport,artisticAccepted:false};
    await sd.saveJson(join(root,'.short-drama',values.preview?'preview-result.json':'render-result.json'),result);
    try{const {writeReview}=await import('./seams.mjs');result.seamReview=await writeReview(root,result);}
    catch(error){result.seamReview={error:String(error.message),purpose:'导出已保存；接点页可用 seams 命令重建'};}
  }else throw Error('Commands: init, state, patch, sync, check, report, import-asset, open, render');
  console.log('SHORT_DRAMA_RESULT='+JSON.stringify(result));
}catch(error){console.error(String(error.stack||error));process.exitCode=1;}
