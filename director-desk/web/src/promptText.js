// UI authors prompt text; the compiler retains the existing canonical document envelope.
function section(text){
 const marker=/^###\s+可复制(?:通用)?提示词\s*$/m.exec(text);
 if(!marker)return null;
 const start=marker.index+marker[0].length;
 const next=/^#{2,3}\s+/m.exec(text.slice(start));
 return {start,end:next?start+next.index:text.length};
}
export function promptText(text=''){
 const bounds=section(text);if(!bounds)return text;
 return text.slice(bounds.start,bounds.end).replace(/^\r?\n/,'').trimEnd().split('\n').map(line=>line.replace(/^>[ \t]?/,'')).join('\n');
}
export function withPromptText(text='',prompt='',kind='image_prompt'){
 const quoted=prompt.split('\n').map(line=>'> '+line).join('\n');
 const bounds=section(text);
 if(bounds)return text.slice(0,bounds.start)+'\n'+quoted+'\n\n'+text.slice(bounds.end);
 const metadata=kind==='image_prompt'?'- 参考：无':'- 生成方式：全能参考\n- 输入参考图：无\n- 参考音频：无';
 return metadata+'\n\n### 可复制提示词\n'+quoted+'\n';
}
