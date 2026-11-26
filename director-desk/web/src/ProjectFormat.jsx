import React,{useState,useEffect} from 'react';
import {X} from '@phosphor-icons/react';

export default function ProjectFormat({spec,revision,project,api,onState,onClose}){
 const original=spec?.data.format||{};
 const profile=spec?.data.production_profile;
 const originalModel=profile?.status==='accepted'?profile.choices?.target_video_model||'':'';
 const [model,setModel]=useState(originalModel),[presets,setPresets]=useState([]);
 const [ratio,setRatio]=useState(original.aspect_ratio||''),[fps,setFps]=useState(original.fps??24),[language,setLanguage]=useState(original.prompt_language||'en');
 const [busy,setBusy]=useState(false),[error,setError]=useState('');
 useEffect(()=>{api('/model-presets').then(setPresets).catch(e=>setError(e.message));},[]);
 async function save(e){
  e.preventDefault();setBusy(true);setError('');
  try{
   const format={...original,aspect_ratio:ratio,fps:Number(fps),prompt_language:language};
   if(!ratio)delete format.aspect_ratio;
   onState(await api(`/projects/${project}/specification`,{revision,format,model}));onClose();
  }catch(e){setError(e.message);}finally{setBusy(false);}
 }
 return <div className="modal-backdrop"><form className="generation-modal" role="dialog" aria-modal="true" aria-label="作品规格" onSubmit={save}>
  <header><h2>作品规格</h2><button type="button" title="关闭作品规格" disabled={busy} onClick={onClose}><X/></button></header>
  <label>目标视频模型<select value={model} disabled={busy} onChange={e=>setModel(e.target.value)}><option value="">尚未选择</option>{presets.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}{originalModel&&!presets.some(p=>p.id===originalModel)&&<option value={originalModel}>{originalModel}</option>}</select></label>
  {model!==originalModel&&<p className="runtime-note">现有分镜与视频提示词将标记待复核，已有素材保留。保存不会发起生成。</p>}
  <label>画幅<select value={ratio} disabled={busy} onChange={e=>setRatio(e.target.value)}>{[...new Set(['','9:16','16:9','1:1','4:3','3:4','21:9','adaptive',ratio])].map(value=><option key={value} value={value}>{value||'沿用素材画幅'}</option>)}</select></label>
  <label>剪辑帧率<input type="number" min="1" max="120" step="any" required value={fps} disabled={busy} onChange={e=>setFps(e.target.value)}/></label>
  <label>图片提示词语言<select value={language} disabled={busy} onChange={e=>setLanguage(e.target.value)}>{[...new Set(['en','zh-CN',language])].map(value=><option key={value} value={value}>{({en:'英文','zh-CN':'中文'})[value]||value}</option>)}</select></label>
  <p className="runtime-note">用于后续生成与新建初剪。已有素材和剪辑工程保持原样；对白语言沿用剧本。</p>
  {error&&<p className="error" role="alert">{error}</p>}
  <button className="primary" disabled={busy}>{busy?'正在保存…':'保存规格'}</button>
 </form></div>;
}
