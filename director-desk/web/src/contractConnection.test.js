import test from 'node:test';
import assert from 'node:assert/strict';
import {createContractCheck} from './contractConnection.js';
test('old server is rejected before editing and a later upgraded server can be used',async()=>{
 let version=1,calls=0;const check=createContractCheck(2,async()=>{calls++;return {ok:true,json:async()=>({version})};});
 await assert.rejects(check(),/版本不同/);version=2;await check();await check();assert.equal(calls,2);
});
test('pre-contract servers show an actionable message',async()=>{
 const check=createContractCheck(2,async()=>({ok:false,status:404}));await assert.rejects(check(),/服务还是旧版本/);
});
