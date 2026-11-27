// A vocabulary is shared; ownership and editing targets are not.
export function controlsFor(entity){
 const kind=entity.kind,name=entity.data.name||'';
 const control=(id,label,field,categories,scope,mode='field')=>({id,label,field,categories,scope,mode});
 if(kind==='shot')return [
  ...[['size','景别'],['angle','机位角度'],['composition','构图'],['focus','焦点 / 景深'],['lens','镜头透视']].map(([id,label])=>control(id,label,['composition','focus'].includes(id)?'composition':'camera',[id],'本镜')),
  control('motion','运镜','movement',['motion'],'本镜'),
  control('light_change','本镜光线变化','lighting',['light_change'],'本镜')];
 if(kind==='image_prompt')return [control('image-execution','视角与构图','text',['angle','composition'],'本张图片','selection'),control('image-surface','姿态与材质','text',['pose','surface'],'本张图片','selection')];
 if(kind==='submission')return [control('video-action','动作与节奏','text',['action_speed'],'本段视频','selection'),control('video-camera','摄影执行','text',['camera_timing','light_change'],'本段视频','selection'),control('video-sound','声音同步','text',['audio'],'本段视频','selection')];
 if(kind==='location')return [control('scene-light','场景光线','text',['light'],'当前地点','design')];
 if(kind!=='design')return [];
 if(/场面设计/.test(name))return [control('scene-light','本场光线','text',['light'],'本场设计','design'),control('scene-color','本场色彩','text',['color'],'本场设计','design')];
 if(/视觉主张|影像风格|成像|全片风格/.test(name))return [control('world-look','成像质感','text',['look'],'本集默认设计','design'),control('world-color','色彩秩序','text',['color'],'本集默认设计','design'),control('world-hardware','摄影机 / 胶片风格','text',['camera','film'],'本集默认设计','design')];
 return [];
}

export function upstreamFor(entity,entities,dependencies=[]){
 const byId=new Map(entities.map(e=>[e.id,e]));
 const scene=entity.kind==='shot'?byId.get(entity.data.parent_id):null;
 const episode=scene?.data.parent_id||entity.data.parent_id;
 const ids=new Set([...(entity.data.design_refs||[]),...(entity.data.inherited_design_refs||[]),...(entity.data.shot_ids||[]),...dependencies.filter(d=>d.target===entity.id).map(d=>d.source)]);
 const shots=entities.filter(e=>e.kind==='shot'&&ids.has(e.id));
 const sceneCodes=new Set([scene?.data.code,...shots.map(s=>byId.get(s.data.parent_id)?.data.code)].filter(Boolean));
 return entities.filter(e=>e.id!==entity.id&&(ids.has(e.id)||e.kind==='design'&&e.data.parent_id===episode&&(/视觉主张|影像风格|全片风格/.test(e.data.name||'')||[...sceneCodes].some(c=>(e.data.name||'').includes(c))))).filter(e=>['design','character','location','look','prop','shot'].includes(e.kind));
}

export function replaceSelection(body,selection,text){
 if(!selection||selection.start===selection.end||body.slice(selection.start,selection.end)!==selection.text)throw new Error('选中的原句已变化，请重新选择后修改。');
 return body.slice(0,selection.start)+text+body.slice(selection.end);
}

export function designTerm(current,category,item){
 const label=category.label;
 const line=`- ${label}：${item.label}${item.description?'。'+item.description:''}`;
 const escaped=label.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
 const pattern=new RegExp(`^- ${escaped}：.*$`,'m');
 return {text:pattern.test(current)?current.replace(pattern,()=>line):[current,line].filter(Boolean).join('\n'),warning:'只更新当前设计条目；保存后，已关联的下游条目会待复核，素材不会自动重生成。'};
}
