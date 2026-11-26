import test from 'node:test';
import assert from 'node:assert/strict';
import {arrangeGraph} from './layoutGraph.js';
test('ELK adapter preserves objects and places reference before output',async()=>{
 const nodes=[{id:'ref',position:{x:1,y:2},data:{kind:'media'}},{id:'task',position:{x:1,y:2},data:{kind:'image_prompt'}},{id:'free',position:{x:1,y:2},data:{kind:'media'}}];
 const before=JSON.stringify(nodes);const result=await arrangeGraph(nodes,[{source:'ref',target:'task'}]);
 assert.equal(JSON.stringify(nodes),before);
 assert.deepEqual(result.map(n=>n.id),nodes.map(n=>n.id));
 assert.ok(result.find(n=>n.id==='ref').position.x<result.find(n=>n.id==='task').position.x);
 assert.ok(result.every(n=>Number.isFinite(n.position.x)&&Number.isFinite(n.position.y)));
});
