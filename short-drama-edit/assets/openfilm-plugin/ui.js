import {project,blocks,pluginApi,open as show,toast} from 'openfilm/studio';

export default class ShortDrama extends HTMLElement {
  connectedCallback(){
    if(this.active)return;this.active=true;this.drafts=this.drafts||new Set();
    this.projectId=this.getAttribute('project-id');this.owner=this.getAttribute('plugin');
    this.api=pluginApi('short-drama');this.blockHost=blocks.slot(this.owner,'story');
    this.stopBlock=blocks.draw(this.owner,'story');
    this.box=document.createElement('div');this.box.style.cssText='height:100%;overflow:auto;padding:14px;background:var(--bg,#171b23);color:var(--fg,#eee);font:13px system-ui;box-sizing:border-box';
    this.blockHost.replaceChildren(this.box);
    this.stopEvents=this.api.events(this.projectId,()=>this.refresh());
    this.refresh();
  }
  disconnectedCallback(){queueMicrotask(()=>{if(this.isConnected)return;this.active=false;this.stopBlock?.();this.stopEvents?.();this.box?.remove();});}
  element(tag,text){const el=document.createElement(tag);if(text!==undefined)el.textContent=text;return el;}
  async refresh(){
    if(this.dirty)return;
    try{const state=await this.api.get('projects/'+encodeURIComponent(this.projectId)+'/state');this.draw(state);}
    catch(error){this.box.textContent=error.message;}
  }
  draw(state){
    this.box.replaceChildren(this.element('h3','短剧创作台'));
    const summary=this.element('p',`${state.duration.toFixed(2)} 秒 · ${state.clips.length} 个轨道项 · 同一份 film.html`);this.box.append(summary);
    for(const doc of state.documents){
      const details=this.element('details');details.style.marginBottom='10px';details.append(this.element('summary',doc.name));
      const textarea=this.element('textarea');textarea.value=doc.text;textarea.style.cssText='width:100%;min-height:260px;margin:8px 0;background:#202735;color:#eee;border:1px solid #566072;box-sizing:border-box;font:12px/1.6 monospace';
      textarea.oninput=()=>{this.drafts.add(doc.name);this.dirty=true;};
      const save=this.element('button','保存当前文档');save.onclick=async()=>{
        try{const result=await this.api.put('projects/'+encodeURIComponent(this.projectId)+'/document',{name:doc.name,text:textarea.value,revision:doc.revision});doc.revision=result.revision;this.drafts.delete(doc.name);this.dirty=this.drafts.size>0;toast('已保存 '+doc.name);this.refresh();}
        catch(error){toast(error.message,{error:true});}
      };details.append(textarea,save);this.box.append(details);
    }
    this.box.append(this.element('h4','镜头与来源'));
    for(const clip of state.clips){
      const row=this.element('button',`${clip.id}  ${clip.start.toFixed(2)}–${clip.end.toFixed(2)}s`);
      row.style.cssText='display:block;width:100%;margin:5px 0;padding:8px;text-align:left;background:#253448;color:#e6f2ff;border:0;border-radius:5px;cursor:pointer';
      row.title=clip.attrs['data-sd-intent']||clip.attrs['data-shot-id']||clip.src;
      row.onclick=()=>show('film.html#'+encodeURIComponent(clip.id));this.box.append(row);
    }
    if(state.issues.length){const issues=this.element('details');issues.append(this.element('summary',`交接与剪辑待核对 · ${state.issues.length}`));for(const issue of state.issues)issues.append(this.element('p',`${issue.kind}：${issue.purpose||issue.document||issue.clip||issue.cue||issue.id||issue.target||''}`));this.box.append(issues);}
    const assets=this.element('details');assets.append(this.element('summary',`已落盘素材 · ${(state.assets||[]).length}`));
    for(const asset of state.assets||[])assets.append(this.element('p',asset.path));this.box.append(assets);
    if((state.jobs||[]).length){const jobs=this.element('details');jobs.append(this.element('summary',`生产任务 · ${state.jobs.length}`));for(const job of state.jobs)jobs.append(this.element('p',`${job.entry||job.id} · ${job.modality||''} · ${job.status}`));this.box.append(jobs);}
    if(state.production){this.box.append(this.element('h4','生产记录'));this.box.append(this.element('p',`${state.production.lastAction||''} · ${state.production.updatedAt||''}`));
      for(const [id,record] of Object.entries(state.production.artifacts||{}))this.box.append(this.element('p',`${id} · ${record.status||record.state||record.stage||'已登记'}`));}
    const sync=this.element('button','刷新联动与剪辑报告');sync.onclick=async()=>{try{await this.api.post('projects/'+encodeURIComponent(this.projectId)+'/sync',{});this.refresh();}catch(error){toast(error.message,{error:true});}};this.box.append(sync);
  }
}
