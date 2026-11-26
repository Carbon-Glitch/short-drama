import React,{useEffect,useState} from 'react';
import {Package,Plus,X} from '@phosphor-icons/react';

const categories=[['character','人物'],['look','造型'],['location','地点'],['prop','道具']];
const mediaTypes=[['all','全部素材'],['image','图片'],['video','视频'],['audio','音频']];

export default function AssetWorkspace({assets,media,entities,renderMedia,renderPrompts,renderPlan,onOpen,onImport,onDesign,onPrepareAssets,onPreparePrompts,busy,owner,onCancelSelection,summarize}){
 const [view,setView]=useState('entities'),[category,setCategory]=useState('character'),[type,setType]=useState('all'),[search,setSearch]=useState('');
 useEffect(()=>{if(owner){setView('media');setType('image');setSearch('');}},[owner?.id]);
 const query=search.trim().toLowerCase();
 const displayedAssets=assets.filter(e=>e.kind===category&&e.data.name.toLowerCase().includes(query));
 const displayedMedia=media.filter(e=>(type==='all'||e.data.type===type)&&e.data.name.toLowerCase().includes(query));
 return <section className="asset-workspace">
  <div className="stage-toolbar asset-workspace-toolbar">
   <nav className="view-switch" aria-label="资产工作视图">{[['entities','人物与场景'],['media','素材库'],['prompts','图片提示词']].map(([id,label])=><button key={id} className={view===id?'active':''} aria-current={view===id?'page':undefined} onClick={()=>{setView(id);setSearch('');}}>{label}</button>)}</nav>
   {view==='entities'?<button className="primary" onClick={onPrepareAssets}>整理资产需求</button>:view==='prompts'?<button className="primary" onClick={onPreparePrompts}>编写图片提示词</button>:<button className="primary" onClick={onImport} disabled={busy}><Plus/>导入素材</button>}
  </div>
  {owner&&<div className="asset-selection-context"><span>为「{owner.data.name}」选择形象图片</span><button onClick={onCancelSelection} aria-label="取消选择形象图片"><X/></button></div>}
  {view==='prompts'?renderPrompts():<>
   {view==='entities'&&<details className="asset-plan"><summary>资产实现<span>参考职责与采用安排</span></summary>{renderPlan()}</details>}
   <div className="asset-filterbar">
    {view==='entities'?<div className="asset-kind-filters">{categories.map(([id,label])=><button key={id} className={category===id?'active':''} aria-pressed={category===id} onClick={()=>setCategory(id)}>{label}<span>{assets.filter(e=>e.kind===id).length}</span></button>)}</div>:<select aria-label="素材类型" value={type} onChange={e=>setType(e.target.value)}>{mediaTypes.map(([id,label])=><option key={id} value={id}>{label}</option>)}</select>}
    <input aria-label="搜索素材" placeholder={view==='entities'?'搜索当前分类':'搜索素材名称'} value={search} onChange={e=>setSearch(e.target.value)}/>
   </div>
   {view==='entities'?<div className="entity-asset-grid">{displayedAssets.map(e=>{
    const image=entities.find(m=>m.id===e.data.adopted_media)||entities.find(m=>e.data.references?.includes(m.id)&&m.kind==='media'&&m.data.type==='image');
    return <button key={e.id} className="entity-asset" onClick={()=>onOpen(e)}><div className="entity-symbol">{image?renderMedia(image):<Package size={32}/>}</div><h3>{e.data.name}</h3><p>{summarize(e.data.text)}</p><span>查看与编辑</span></button>;
   })}</div>:<div className="asset-stage-grid">{displayedMedia.map(m=><button key={m.id} onClick={()=>onOpen(m)}>{renderMedia(m)}<strong>{m.data.name}</strong><span>{{image:'图片',video:'视频',audio:'音频'}[m.data.type]}</span></button>)}</div>}
   {(view==='entities'?!displayedAssets.length:!displayedMedia.length)&&<div className="empty-state"><Package size={32}/><h2>{query?'没有找到匹配内容':view==='entities'?'还没有这类资产':'还没有这类素材'}</h2>{query?<button onClick={()=>setSearch('')}>清除搜索</button>:view==='entities'?<button onClick={onDesign}>前往视觉设计添加</button>:<button onClick={onImport} disabled={busy}>导入已有素材</button>}</div>}
  </>}
 </section>;
}
