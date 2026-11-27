import test from 'node:test';
import assert from 'node:assert/strict';
import {suggestTerm} from './termEditing.js';
const size={id:'size',label:'景别',items:[{label:'特写'},{label:'近景'},{label:'中近景'}]};
test('replace only size and preserve direction light and performance',()=>{
 assert.equal(suggestTerm('中近景，低机位，侧光，等待回头',size,{label:'特写'}).text,'特写，低机位，侧光，等待回头');
});
test('ambiguous text is not silently overwritten',()=>{
 const value='从近景逐渐到特写';assert.equal(suggestTerm(value,size,{label:'中近景'}).text,value);
 assert.ok(suggestTerm(value,size,{label:'中近景'}).warning);
});
test('explicit property replaced without erasing prose',()=>{
 assert.equal(suggestTerm('景别：近景；光线：侧光',size,{label:'特写'}).text,'景别：特写；光线：侧光');
});
test('motion sequence preserves original action',()=>{
 assert.match(suggestTerm('固定等待回头',{id:'motion'},{label:'缓推'},true).text,/固定等待回头 → 缓推/);
});
