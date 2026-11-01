export function pushKey(publicKey:string):Uint8Array<ArrayBuffer> {
  const encoded=publicKey.replace(/-/g,"+").replace(/_/g,"/");
  const key=Uint8Array.from(atob(encoded+"=".repeat((4-encoded.length%4)%4)),c=>c.charCodeAt(0));
  if(key.length!==65||key[0]!==4)throw new Error("Browser delivery has an invalid server key.");
  return key;
}
export async function ensurePushSubscription(manager:PushManager, publicKey:string) {
  const key=pushKey(publicKey);
  const existing=await manager.getSubscription();
  if(existing){
    const stored=existing.options.applicationServerKey;
    const bytes=stored?new Uint8Array(stored):null;
    const same=bytes?.length===key.length&&bytes.every((v,i)=>v===key[i]);
    if(same)return existing;
    if(!await existing.unsubscribe())throw new Error("The old browser subscription could not be replaced. Try disabling browser alerts first.");
  }
  return manager.subscribe({userVisibleOnly:true,applicationServerKey:key.buffer});
}
