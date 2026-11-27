export function suggestTerm(current,category,item,append=false){
  if(category.id==='motion')return {text:append&&current?`${current} → ${item.label}（补充触发、方向与停点）`:item.label,warning:current&&!append?'将替换当前运镜；可选“接在现有动作之后”。':''};
  const escape=s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
  const label=category.label;
  const clause=new RegExp(`${escape(label)}：[^；。\\n]*`);
  if(clause.test(current))return {text:current.replace(clause,`${label}：${item.label}`),warning:''};
  const terms=category.items.map(i=>i.label).sort((a,b)=>b.length-a.length);
  const pattern=new RegExp(terms.map(escape).join('|'),'g');
  const matches=[...current.matchAll(pattern)];
  if(matches.length===1)return {text:current.slice(0,matches[0].index)+item.label+current.slice(matches[0].index+matches[0][0].length),warning:''};
  if(matches.length>1)return {text:current,warning:'原文含多处同类描述，请在下方选定要改的短句；未自动替换。'};
  return {text:[current,`${label}：${item.label}`].filter(Boolean).join('；'),warning:current?'请核对原文中的自定义描述是否与新选择冲突。':''};
}
