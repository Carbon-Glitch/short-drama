import React,{useState,useRef,useEffect} from 'react';
import terms from './cinemaTerms.json';
import {suggestTerm} from './termEditing';
import {designTerm} from './creativeControls';
import './termPicker.css';

function Diagram({category,label}){
 const close=category==='size'&&/特写|近景/.test(label);
 return <svg viewBox="0 0 120 64" aria-hidden="true"><rect x="3" y="3" width="114" height="58" rx="5" fill="none" stroke="currentColor" opacity=".3"/><g transform={close?'translate(-30,-8) scale(1.5)':''}><circle cx="60" cy="22" r="8" fill="currentColor" opacity=".6"/><path d="M44 54 Q44 32 60 32 Q76 32 76 54" fill="currentColor" opacity=".35"/></g>{category==='motion'&&<path d="M12 47 L36 47 M29 40 L36 47 L29 54" fill="none" stroke="currentColor" strokeWidth="3"/>}{category==='angle'&&<path d="M18 15 L45 30 L18 45 Z" fill="none" stroke="currentColor"/>}</svg>;
}

export default function TermPicker({control,current,onApply,onClose}){
 const dialog=useRef(null);const [query,setQuery]=useState('');const advanced=true;
 const groups=terms.categories.filter(c=>control.categories.includes(c.id));
 const design=control.mode==='design',selection=control.mode==='selection',field=control.field;
 const [categoryId,setCategoryId]=useState(groups[0].id);const [selected,setSelected]=useState(null);const [preview,setPreview]=useState(current);const [warning,setWarning]=useState('');const [append,setAppend]=useState(false);const [custom,setCustom]=useState('');
 const [recent,setRecent]=useState(()=>{try{return JSON.parse(localStorage.getItem('director-cinema-recent')||'[]');}catch{return [];}});
 useEffect(()=>{const el=dialog.current;const before=document.activeElement;el.showModal();return()=>{el.close();before?.focus();};},[]);
 const category=groups.find(c=>c.id===categoryId)||groups[0];
 function choose(c,item,sequence=append){setSelected({c,item});const result=design?designTerm(current,c,item):selection?{text:!/[\u3400-\u9fff]/.test(current)&&item.prompt_en?item.prompt_en:item.description||item.label,warning:'替换选中的原句；请保留本片提示词语言和模型语法。'}:suggestTerm(current,c,item,sequence);setPreview(result.text);setWarning(result.warning);}
 function apply(){onApply(preview);if(selected){const ids=[selected.item.id,...recent.filter(id=>id!==selected.item.id)].slice(0,8);localStorage.setItem('director-cinema-recent',JSON.stringify(ids));setRecent(ids);}onClose();}
 return <dialog ref={dialog} className="term-dialog" onCancel={onClose} aria-labelledby="term-title">
  <header><div><small>DIRECTOR'S VOCABULARY</small><h2 id="term-title">{control.label}</h2></div><button type="button" onClick={onClose} aria-label="关闭词库">×</button></header>
  <p className="term-scope">作用范围：{control.scope}{selection?' · 仅替换选中原句':''}</p><div className="term-tools"><input autoFocus placeholder="搜索名称或效果，也可在下方自行写…" aria-label="搜索影视词库" value={query} onChange={e=>setQuery(e.target.value)}/></div>
  {groups.length>1&&<nav aria-label="词库分类">{groups.filter(c=>advanced||!c.advanced).map(c=><button type="button" className={category.id===c.id?'selected':''} key={c.id} onClick={()=>{setCategoryId(c.id);setQuery('');}}>{c.label}</button>)}</nav>}
  {!query&&recent.length>0&&<div className="term-recent"><span>最近：</span>{groups.flatMap(c=>c.items.filter(i=>recent.includes(i.id)).map(i=><button type="button" key={i.id} onClick={()=>choose(c,i)}>{i.label}</button>))}</div>}
  <div className="term-grid">{(query?groups.filter(c=>advanced||!c.advanced):[category]).flatMap(c=>c.items.filter(i=>!query||`${i.label} ${i.description}`.toLowerCase().includes(query.toLowerCase())).map(item=><button type="button" key={item.id} aria-pressed={selected?.item.id===item.id} onClick={()=>choose(c,item)}>{['size','angle','motion'].includes(c.id)&&<Diagram category={c.id} label={item.label}/>}<strong>{item.label}</strong><span>{item.description}</span></button>))}</div>
  {field==='movement'&&<label className="term-sequence"><input type="checkbox" checked={append} onChange={e=>{setAppend(e.target.checked);if(selected)choose(selected.c,selected.item,e.target.checked);}}/>接在现有动作之后（顺序组合）</label>}
  <div className="term-custom"><input value={custom} aria-label="自定义术语" onChange={e=>setCustom(e.target.value)} placeholder="自定义术语或短句"/><button type="button" disabled={!custom.trim()} onClick={()=>choose(category,{id:'custom:'+custom,label:custom.trim(),description:''})}>使用</button></div>
  <label className="term-preview">{selection?'替换后的这一句':'修改后的完整内容'}<textarea aria-label="词库修改预览" value={preview} onChange={e=>setPreview(e.target.value)}/></label>
  {warning&&<p className="term-warning">{warning}</p>}{control.categories.some(c=>['camera','film'].includes(c))&&<p className="term-footnote">器材与胶片名称表达成像意图，不是模型的硬件开关。</p>}
  <footer><button type="button" onClick={onClose}>取消</button><button type="button" className="primary" disabled={preview===current} onClick={apply}>应用到{control.scope}</button></footer>
 </dialog>;
}
