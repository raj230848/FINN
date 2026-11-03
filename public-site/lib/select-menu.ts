export type MenuOption = { value:string; label:string; disabled:boolean; group?:string };
export function nextEnabled(options:MenuOption[],current:number,direction:1|-1):number {
  if(!options.length)return -1;
  const start=current<0?(direction===1?-1:0):current;
  for(let step=1;step<=options.length;step++){
    const i=((start+direction*step)%options.length+options.length)%options.length;
    if(!options[i].disabled)return i;
  }
  return -1;
}
export function matchingOption(options:MenuOption[],query:string,current:number):number {
  const q=query.trim().toLocaleLowerCase();if(!q)return -1;
  const matches=(o:MenuOption)=>!o.disabled&&(o.label.toLocaleLowerCase().startsWith(q)||o.value.toLocaleLowerCase().startsWith(q));
  if(q.length>1&&options[current]&&matches(options[current]))return current;
  for(let step=1;step<=options.length;step++){
    const i=(current+step+options.length)%options.length;if(matches(options[i]))return i;
  }
  return -1;
}
export function menuPlacement(rect:{left:number;top:number;bottom:number;width:number},viewport:{width:number;height:number;top?:number}) {
  const edge=12,gap=6,minY=(viewport.top||0)+edge,maxY=(viewport.top||0)+viewport.height-edge;
  const width=Math.min(Math.max(rect.width,240),420,Math.max(1,viewport.width-edge*2));
  const left=Math.max(edge,Math.min(rect.left,viewport.width-width-edge));
  const below=Math.max(0,maxY-rect.bottom-gap),above=Math.max(0,rect.top-minY-gap),up=below<180&&above>below;
  const maxHeight=Math.max(1,Math.min(320,up?above:below));
  return {left,width,maxHeight,top:up?rect.top-gap:Math.max(minY,Math.min(rect.bottom+gap,maxY-maxHeight)),transform:up?"translateY(-100%)":undefined};
}
