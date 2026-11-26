import React,{useState} from 'react';

export default function DependencyReview({entity,state,busy,onOpen,onReview}){
 const [saving,setSaving]=useState(false),[error,setError]=useState('');
 if(!entity?.stale)return null;
 const upstream=state.dependencies.filter(d=>d.target===entity.id).map(d=>state.entities.find(e=>e.id===d.source)).filter(e=>e?.stale);
 const label=['image_prompt','submission'].includes(entity.kind)?'已核对提示词':entity.kind==='shot'?'已核对镜头':'已核对当前内容';
 async function review(){setSaving(true);setError('');try{await onReview(entity);}catch(e){setError(e.message);}finally{setSaving(false);}}
 return <section className="dependency-review"><strong>待复核</strong>{upstream.length?<><p>先核对这些上游内容：</p><div>{upstream.map(source=><button key={source.id} disabled={busy||saving} onClick={()=>onOpen(source,entity)}>{source.data.name||'来源内容'}</button>)}</div></>:<><p>核对当前内容与来源，完成后更新这条记录。</p><button disabled={busy||saving} onClick={review}>{saving?'正在保存…':label}</button></>}{error&&<p className="error" role="alert">{error}</p>}</section>;
}
