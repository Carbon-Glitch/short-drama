import React,{useEffect,useRef,useState} from 'react';

// Artplayer owns playback controls and settings; this wrapper owns React lifetime only.
export default function ReviewPlayer({src,label}){
 const container=useRef(null);const [fallback,setFallback]=useState(false);
 useEffect(()=>{
  let alive=true,player;
  setFallback(false);
  // Do not leave a gallery preview sounding behind the review dialog.
  document.querySelectorAll('video').forEach(video=>video.pause());
  import('artplayer').then(({default:Artplayer})=>{
   if(!alive||!container.current)return;
   player=new Artplayer({container:container.current,url:src,lang:'zh-cn',theme:'#b65b48',
    autoplay:false,playsInline:true,setting:true,playbackRate:true,pip:true,
    fullscreen:true,fullscreenWeb:true,hotkey:true,mutex:true,
    moreVideoAttr:{preload:'metadata'}});
   player.video.setAttribute('aria-label',label||'回片播放器');
  }).catch(()=>{if(alive)setFallback(true);});
  return ()=>{alive=false;if(player){player.pause();player.destroy(false);}};
 },[src]);
 return fallback?<video className="review-player-fallback" src={src} aria-label={label||'回片播放器'} controls preload="metadata"/>:<div className="review-player" ref={container}/>;
}
