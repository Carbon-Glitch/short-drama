import React,{useEffect,useState} from 'react';

export default function EditingSetup({api}){
 const [state,setState]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 async function refresh(){try{setState(await api('/editing-runtime'));setError('');}catch(e){setError(e.message);}}
 useEffect(()=>{refresh();},[]);
 const running=['installing','browser'].includes(state?.phase);
 useEffect(()=>{if(!running)return;const timer=setInterval(refresh,3000);return ()=>clearInterval(timer);},[running]);
 async function prepare(){setBusy(true);setError('');try{setState(await api('/editing-runtime',{}));}catch(e){setError(e.message);}finally{setBusy(false);}}
 return <section className="editing-setup"><h3>剪辑环境</h3><p>复用这台电脑已有的组件，为所有作品共用。</p>
  {!state?<p>正在检测…</p>:<><ul>{state.components.map(c=><li key={c.id}><strong>{c.label}</strong><span>{c.ready?'可用':'需要准备'}</span>{c.version&&<small>{c.version}</small>}</li>)}</ul>
   {state.components.some(c=>c.id==='node'&&!c.ready)&&<p>需要 Node.js 22.2 或更新版本。<a href="https://nodejs.org/en/download" target="_blank" rel="noreferrer">打开官方安装页</a>，安装后重新打开导演台。</p>}
   {state.components.some(c=>['ffmpeg','ffprobe'].includes(c.id)&&!c.ready)&&<p>需要视频处理组件。<a href="https://ffmpeg.org/download.html" target="_blank" rel="noreferrer">打开 FFmpeg 官方下载页</a>。</p>}
   <p className="runtime-note">准备会从 npm 下载 OpenFilm 0.4.1，并由它的安装器准备渲染浏览器。仅安装缺少的组件，不生成素材。</p>
   <div className="actions"><button disabled={busy||running||!state.can_prepare} onClick={prepare}>{running?({installing:'正在准备剪辑台…',browser:'正在准备渲染浏览器…'})[state.phase]:'准备剪辑组件'}</button><button disabled={busy||running} onClick={refresh}>重新检测</button></div>
   {state.phase==='complete'&&<p role="status">OpenFilm 与渲染浏览器已准备；上方其他组件也可用后即可进入剪辑。</p>}
   {state.error&&<p role="alert" className="error">{state.error}</p>}
   <details><summary>安装位置</summary><p>{state.folder}</p></details>
  </>}{error&&<p className="error" role="alert">{error}</p>}
 </section>;
}
