import test from 'node:test';
import assert from 'node:assert/strict';
import {controlsFor,upstreamFor,replaceSelection,designTerm} from './creativeControls.js';
const entity=(kind,name='',data={})=>({kind,id:kind,data:{name,...data}});
test('stage menus keep design and prompt decisions out of shot menu',()=>{
 const shot=controlsFor(entity('shot')).flatMap(c=>c.categories);
 assert.ok(shot.includes('size'));assert.ok(!shot.includes('film'));assert.ok(!shot.includes('camera'));assert.ok(!shot.includes('look'));
 assert.deepEqual(controlsFor(entity('submission')).flatMap(c=>c.categories),['action_speed','camera_timing','light_change','audio']);
 assert.ok(controlsFor(entity('image_prompt')).every(c=>c.mode==='selection'));
 assert.equal(controlsFor(entity('design','体验设计')).length,0);
 assert.ok(controlsFor(entity('design','视觉主张与影像风格')).some(c=>c.categories.includes('film')));
 assert.ok(!controlsFor(entity('design','场面设计 · EP001-SC001')).some(c=>c.categories.includes('film')));
});
test('prompt sentence replacement retains model headings and references',()=>{
 const body='summary:\nA shot.\ndetailed_description:\nThe camera moves.\noverall_soundscape:\nQuiet.';
 const text='The camera moves.',start=body.indexOf(text),selection={start,end:start+text.length,text};
 assert.equal(replaceSelection(body,selection,'The camera holds.'),body.replace(text,'The camera holds.'));
 assert.throws(()=>replaceSelection('changed',selection,'new'));
});
test('upstream lookup never mixes episodes',()=>{
 const shot=entity('shot','一镜',{parent_id:'sc'});
 const entities=[shot,{id:'sc',kind:'scene',data:{parent_id:'ep',code:'EP001-SC001'}},
 {id:'global',kind:'design',data:{parent_id:'ep',name:'视觉主张与影像风格'}},
 {id:'other',kind:'design',data:{parent_id:'other-ep',name:'视觉主张与影像风格'}}];
 assert.deepEqual(upstreamFor(shot,entities).map(e=>e.id),['global']);
});
test('same design choice replaces owned line and preserves creative prose',()=>{
 assert.equal(designTerm('保留人物动机\n- 光线：柔光',{label:'光线'},{label:'侧光',description:'从侧面塑造体积'}).text,'保留人物动机\n- 光线：侧光。从侧面塑造体积');
});
