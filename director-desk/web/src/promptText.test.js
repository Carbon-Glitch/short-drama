import test from 'node:test';
import assert from 'node:assert/strict';
import {promptText,withPromptText} from './promptText.js';
test('new plain prompt compiles without requiring markdown knowledge',()=>{
 const prompt='A quiet room.\nThe phone says: <d>[Chinese] 今天我先休息。</d>';
 const result=withPromptText('',prompt);
 assert.equal(promptText(result),prompt);
 assert.ok(result.startsWith('- 参考：无\n\n### 可复制提示词\n> '));
});
test('editing prompt retains reference order and non-prompt notes',()=>{
 const original='- 参考：REF-OWNER（顺序：1）· media/owner.png《主人》\n\n### 可复制提示词\n> Old prompt\n\n### 备注\n保留此处。\n';
 const result=withPromptText(original,'New prompt\n### Shot 1');
 assert.equal(promptText(result),'New prompt\n### Shot 1');
 assert.ok(result.startsWith('- 参考：REF-OWNER（顺序：1）· media/owner.png《主人》'));
 assert.ok(result.endsWith('### 备注\n保留此处。\n'));
 assert.equal((result.match(/New prompt/g)||[]).length,1);
});
test('new video entry keeps reference fields distinct',()=>{
 const result=withPromptText('','subject_definitions:\nA phone','submission');
 assert.ok(result.includes('- 生成方式：全能参考'));
 assert.ok(result.includes('- 输入参考图：无\n- 参考音频：无'));
 assert.equal(promptText(result),'subject_definitions:\nA phone');
});
