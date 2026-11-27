import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,writeFile,rm} from 'node:fs/promises';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {collect} from './handoff.mjs';

test('stable design requirements preserve the whole decision and link its shots',async()=>{
 const root=await mkdtemp(join(tmpdir(),'sd-design-'));
 try{
  await writeFile(join(root,'视觉设定.md'),'## DESIGN-EP001-001 · 铃声先到\n- 场次：EP001-SC001\n- 观看结果：门铃响起，听者才转头。\n- 声音重点：远到近。\n\n## 场面设计 · EP001-SC001\n- 调度设计：站在门两侧。\n');
  await writeFile(join(root,'分镜.md'),'## SHOT-EP001-001 · 回头\n- 设计承接：DESIGN-EP001-001\n- 动作与表演：铃响才回头。\n');
  const first=await collect(root),req=first.requirements.find(r=>r.designCode);
  assert.ok(req.text.includes('远到近'));assert.equal(req.role,'experience');
  assert.deepEqual(first.designLinks,[{shot:'SHOT-EP001-001',designs:['DESIGN-EP001-001']}]);
  await writeFile(join(root,'视觉设定.md'),'## DESIGN-EP001-001 · 新名称\n先静默再响铃。');
  const second=await collect(root);
  assert.equal(second.requirements.find(r=>r.designCode).id,req.id);
  assert.notEqual(first.revision,second.revision);
  assert.ok(req.text.includes('门铃响起'));
 }finally{await rm(root,{recursive:true,force:true});}
});
