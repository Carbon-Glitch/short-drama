import React,{useState} from 'react';
import contract from '../../../short-drama/references/document-contract.json';
export default function ProductionTrace({api,project,production}){
 const [snapshot,setSnapshot]=useState(null),[error,setError]=useState(''),[loading,setLoading]=useState(false);
 async function load(){if(snapshot||loading)return;setLoading(true);try{setSnapshot(await api(`/projects/${project}/generation-context`,{id:production.job_id}));}catch(e){setError(e.message);}finally{setLoading(false);}}
 const context=snapshot?.context,selected=new Set(context?.source_shot_ids||[]);
 return <details className="production-trace" onToggle={e=>{if(e.currentTarget.open)load();}}><summary>提交时的设计与分镜</summary>{loading&&<p>正在读取提交快照…</p>}{error&&<p role="alert">{error}</p>}{snapshot&&!context&&<p>这份历史回片没有保存创作上下文。</p>}{context&&<><p>以下为生成时保存的版本。</p>{context.project.entities.filter(e=>['design','shot','image_prompt'].includes(e.kind)).map(e=><article key={e.id}><h4>{e.data.code} · {e.data.name}{e.kind==='shot'&&!selected.has(e.id)?' · 邻镜参考':''}</h4><pre style={{whiteSpace:'pre-wrap',font:'inherit'}}>{e.kind==='shot'?Object.entries(contract.shot_fields).filter(([k])=>e.data[k]).map(([k,label])=>label+'：'+e.data[k]).join('\n'):e.data.text}</pre></article>)}</>}</details>;
}
