import React,{useState} from 'react';
import contract from '../../../short-drama/references/document-contract.json';
import './storyboardReading.css';

export function shotValue(shot,key){
 const data=shot.data||{};
 if(data[key]!=null)return data[key];
 const label=contract.shot_fields[key],fields=data.fields||{};
 if(fields[label]!=null)return fields[label];
 const alias=Object.keys(contract.aliases).find(a=>contract.aliases[a]===label&&fields[a]!=null);
 return alias?fields[alias]:'';
}
const reading=['design_intent','purpose','start','action','reaction','sound','sound_cues','timing','end','join'];
export default function StoryboardReading({shots,mode,onOpen}){
 const [group,setGroup]=useState('story');
 const fields=contract.shot_groups.find(g=>g.id===group)?.fields||reading;
 if(mode==='顺序读戏')return <div className="storyboard-reading">{shots.map((shot,i)=><article key={shot.id}><header><div><small>{String(i+1).padStart(2,'0')} · {shot.data.code}</small><h3>{shot.data.name}</h3></div><span>{shotValue(shot,'duration')}</span><button onClick={()=>onOpen(shot)}>编辑镜头</button></header>{shot.stale&&<p className="inline-stale">待复核 · 核对本镜与来源</p>}<dl>{reading.filter(k=>shotValue(shot,k)).map(k=><React.Fragment key={k}><dt>{contract.shot_fields[k]}</dt><dd>{shotValue(shot,k)}</dd></React.Fragment>)}</dl></article>)}</div>;
 return <div className="storyboard-matrix"><div className="matrix-groups" role="group" aria-label="分镜表维度">{contract.shot_groups.map(g=><button key={g.id} aria-pressed={group===g.id} className={group===g.id?'active':''} onClick={()=>setGroup(g.id)}>{g.label}</button>)}</div><div className="matrix-scroll" tabIndex={0} role="region" aria-label="多维分镜表，可横向滚动"><table><thead><tr><th scope="col">镜头</th>{fields.map(k=><th scope="col" key={k}>{contract.shot_fields[k]}</th>)}</tr></thead><tbody>{shots.map(shot=><tr key={shot.id}><th scope="row"><button onClick={()=>onOpen(shot)}>{shot.data.name}</button><small>{shot.data.code}</small>{shot.stale&&<span className="inline-stale">待复核</span>}</th>{fields.map(k=><td key={k}>{shotValue(shot,k)||'—'}</td>)}</tr>)}</tbody></table></div></div>;
}
