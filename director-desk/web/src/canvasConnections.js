export function referenceConnection(items,connection){
 const media=items.find(e=>e.id===connection.source),target=items.find(e=>e.id===connection.target);
 if(!media||!target||media.kind!=='media')return null;
 const allowed=media.data.type==='image'&&['image_prompt','submission'].includes(target.kind)||media.data.type==='audio'&&target.kind==='submission';
 return allowed?{media,target}:null;
}

export function suggestReference(value,media,video){
 const choices=[...value.choices],voices=[...(value.voices||[])],mode=value.mode||'reference';let hint='';
 if(!media)return {choices,voices,mode,hint};
 if(media.data.type==='image'&&!choices.some(c=>c.media_id===media.id)){
  if(!video||mode==='reference')choices.push({media_id:media.id,purpose:'身份'});
  else if(mode==='first_frame'&&choices.length<1||mode==='first_last_frame'&&choices.length<2)choices.push({media_id:media.id,purpose:choices.length?'结束帧':'起始帧'});
  else hint='已保留当前控制方式，请调整下方参考或切换模式后加入这张图片。';
 }else if(media.data.type==='audio'&&!voices.some(v=>v.media_id===media.id)){
  if(video&&mode==='reference')voices.push({media_id:media.id,character:value.characters?.length===1?value.characters[0]:''});
  else hint='音色参考需要全能参考模式，请先选择控制方式。';
 }
 return {choices,voices,mode,hint};
}
