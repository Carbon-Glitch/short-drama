// Adapted from StoryBored Lightbox.tsx, commit b368140dec0ccb43276b375afa887b2688027b0c.
// Copyright (c) 2026 StoryBored contributors. MIT; see licenses/StoryBored-MIT.txt.
// Local changes: supplied media URLs, existing adoption API, embedded layout,
// Chinese controls, no autoplay, and keyboard events leave media controls alone.
import React,{useEffect} from 'react';
import {ArrowLeft,ArrowRight,Check} from '@phosphor-icons/react';

export default function TakeViewer({takes,index,pickedId,onClose,onNavigate,onPick}){
 const take=takes[index];
 useEffect(()=>{
  const onKey=e=>{
   if(e.defaultPrevented||e.altKey||e.ctrlKey||e.metaKey)return;
   if(e.key==='Escape'){onClose();return;}
   if(e.target.closest('input,textarea,select,video,audio,[contenteditable="true"]'))return;
   if(e.key==='ArrowLeft'&&index>0){e.preventDefault();onNavigate(index-1);}
   if(e.key==='ArrowRight'&&index<takes.length-1){e.preventDefault();onNavigate(index+1);}
  };
  window.addEventListener('keydown',onKey);
  return ()=>window.removeEventListener('keydown',onKey);
 },[index,takes.length,onClose,onNavigate]);
 if(!take)return null;
 const isPicked=take.id===pickedId;
 return <section className="take-viewer" aria-label="逐个浏览版本">
  <div className="take-viewer-heading"><span>{index+1} / {takes.length} · {take.name}</span>
   {onPick&&<button className={isPicked?'':'primary'} disabled={isPicked} onClick={()=>onPick(take.id)}>{isPicked?<><Check/>当前采用</>:'采用这个版本'}</button>}
  </div>
  <div className="take-viewer-stage">
   <button aria-label="上一个版本" disabled={index===0} onClick={()=>onNavigate(index-1)}><ArrowLeft/></button>
   {take.type==='video'?<video key={take.id} src={take.url} controls preload="metadata"/>:<img src={take.url} alt={take.name}/>}
   <button aria-label="下一个版本" disabled={index===takes.length-1} onClick={()=>onNavigate(index+1)}><ArrowRight/></button>
  </div>
 </section>;
}
