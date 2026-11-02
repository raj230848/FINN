/** Give bounded PDF imports time to download and index without slowing other APIs. */
export function backendTimeoutMs(method:string,path:readonly string[]):number {
  return method==="POST"&&path.length===1&&path[0]==="documents"?180000:55000;
}
