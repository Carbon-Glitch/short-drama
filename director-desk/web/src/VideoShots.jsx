import React,{useEffect,useState} from 'react';
import {X} from '@phosphor-icons/react';

export default function VideoShots({api,project,source,onState,onClose}){
 const [data,setData]=useState(null),[selected,setSelected]=useState([]),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 useEffect(()=>{api(`/projects/${project}/video-shots`,{source_id:source.id}).then(result=>{setData(result);setSelected(result.selected);}).catch(e=>setError(e.message));},[project,source.id]);
 async function save(){setBusy(true);setError('');try{onState(await api(`/projects/${project}/video-shots`,{source_id:source.id,revision:data.revision,selected}));onClose();}catch(e){setError(e.message);}finally{setBusy(false);}}
 return <div className="modal-backdrop"><section className="source-merge video-shot-picker" role="dialog" aria-modal="true" aria-label="关联分镜"><header><div><h2>这段视频覆盖哪些镜头？</h2><p>{source.data.name}</p></div><button title="关闭分镜关联" disabled={busy} onClick={onClose}><X/></button></header>
  <p>按分镜顺序关联。保存后按新范围核对提示词与时长，编号和依赖由系统处理。</p>
  {error&&<p className="error" role="alert">{error}</p>}
  {data?.invalid_previous&&<p className="runtime-note">原关联含其他集或已移除的镜头。已按本集来源匹配，请核对选择后保存。</p>}
  <div className="source-change-list">{!data?<p>正在读取分镜…</p>:data.shots.length?data.shots.map((shot,index)=><label className="video-shot-choice" key={shot.id}><input type="checkbox" disabled={busy} checked={selected.includes(shot.id)} onChange={e=>setSelected(ids=>e.target.checked?[...ids,shot.id]:ids.filter(id=>id!==shot.id))}/><span><strong>{index+1}. {shot.name}</strong><small>{shot.scene}{shot.duration?' · '+shot.duration:''}</small>{shot.action&&<p>{shot.action}</p>}</span></label>):<p>本集还没有分镜，可先在分镜页添加镜头。</p>}</div>
  <footer><span>已选 {selected.length} 镜</span><button className="primary" disabled={busy||!data} onClick={save}>{busy?'正在保存…':'保存关联'}</button></footer>
 </section></div>;
}
