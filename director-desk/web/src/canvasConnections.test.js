import test from 'node:test';
import assert from 'node:assert/strict';
import {referenceConnection,suggestReference} from './canvasConnections.js';

const image={id:'image',kind:'media',data:{type:'image'}},audio={id:'audio',kind:'media',data:{type:'audio'}};
const items=[image,audio,{id:'video',kind:'media',data:{type:'video'}},{id:'picture-task',kind:'image_prompt',data:{}},{id:'video-task',kind:'submission',data:{}}];
test('canvas connections follow supported reference roles',()=>{
 assert.equal(referenceConnection(items,{source:'image',target:'video-task'}).media.id,'image');
 assert.equal(referenceConnection(items,{source:'audio',target:'video-task'}).media.id,'audio');
 for(const pair of [['audio','picture-task'],['video','video-task'],['picture-task','image'],['image','image']])assert.equal(referenceConnection(items,{source:pair[0],target:pair[1]}),null);
});
test('reference suggestion preserves existing references and avoids duplicates',()=>{
 const value={mode:'reference',choices:[{media_id:'earlier',purpose:'场景'}],voices:[]};
 const suggested=suggestReference(value,image,true);
 assert.deepEqual(suggested.choices,[...value.choices,{media_id:'image',purpose:'身份'}]);
 assert.equal(value.choices.length,1);
 assert.equal(suggestReference({...value,choices:suggested.choices},image,true).choices.length,2);
});
test('connection never silently replaces an endpoint or changes text mode',()=>{
 for(const mode of ['first_frame','text']){
  const choices=mode==='first_frame'?[{media_id:'existing',purpose:'起始帧'}]:[];
  const suggested=suggestReference({mode,choices},image,true);
  assert.equal(suggested.mode,mode);assert.deepEqual(suggested.choices,choices);assert.ok(suggested.hint);
 }
 const voice=suggestReference({mode:'reference',choices:[],characters:['甲']},audio,true);
 assert.deepEqual(voice.voices,[{media_id:'audio',character:'甲'}]);
});
