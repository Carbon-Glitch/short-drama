// ELK handles ranks and disconnected component packing; the app retains stable identities.
let engine;
export async function arrangeGraph(nodes,edges){
 if(!engine){const {default:ELK}=await import('elkjs/lib/elk.bundled.js');engine=new ELK();}
 const ids=new Set(nodes.map(n=>n.id));
 const graph=await engine.layout({id:'canvas',layoutOptions:{
  'elk.algorithm':'layered','elk.direction':'RIGHT','elk.aspectRatio':'1.8',
  'elk.separateConnectedComponents':'true','elk.spacing.componentComponent':'50',
  'elk.spacing.nodeNode':'45','elk.layered.spacing.nodeNodeBetweenLayers':'90',
 },children:nodes.map(n=>({id:n.id,width:n.measured?.width||250,height:n.measured?.height||250})),
 edges:edges.filter(e=>ids.has(e.source)&&ids.has(e.target)&&e.source!==e.target).map((e,i)=>({id:'edge-'+i,sources:[e.source],targets:[e.target]}))});
 const placed=new Map(graph.children.map(n=>[n.id,n]));
 return nodes.map(node=>({...node,position:{x:placed.get(node.id).x,y:placed.get(node.id).y}}));
}
