export function createContractCheck(version,fetcher=fetch){
 let checked;
 return async function check(){
  if(!checked)checked=(async()=>{
   const response=await fetcher('/api/document-contract');
   if(response.status===404)throw new Error('导演台服务还是旧版本。请保存当前工作，完成正在处理的导入或任务，再重新打开导演台。');
   if(!response.ok)throw new Error('暂时无法核对导演台版本，请稍后重试。');
   const contract=await response.json();
   if(contract.version!==version)throw new Error('导演台界面与服务版本不同，请保存当前工作并重新打开导演台。');
  })().catch(error=>{checked=undefined;throw error;});
  return checked;
 };
}
