/* Web Push only: no application/API cache and no credentials in this worker. */
function receipt(id,remove=false) {
  return new Promise((resolve,reject)=>{
    const request=indexedDB.open("finn-push-receipts",1);
    request.onupgradeneeded=()=>request.result.createObjectStore("events");
    request.onerror=()=>reject(new Error("Notification receipt storage unavailable"));
    request.onsuccess=()=>{
      const db=request.result,tx=db.transaction("events","readwrite"),store=tx.objectStore("events");
      let claimed=false;
      if(remove)store.delete(id);
      else {const get=store.get(id);get.onsuccess=()=>{if(!get.result){store.put(Date.now(),id);claimed=true;}};}
      tx.oncomplete=()=>{db.close();resolve(claimed);};
      tx.onerror=()=>{db.close();reject(new Error("Notification receipt storage unavailable"));};
    };
  });
}
self.addEventListener("push",event=>{
  event.waitUntil((async()=>{
    let payload;try{payload=event.data.json();}catch{return;}
    if(!Number.isInteger(payload.event_id)||typeof payload.title!=="string")return;
    if(!await receipt(payload.event_id))return;
    try{await self.registration.showNotification(payload.title.slice(0,180),{
      body:String(payload.body||"").slice(0,350),
      tag:`finn-event-${payload.event_id}`,renotify:false,
      data:{url:"/",event_id:payload.event_id},
    });}catch(error){await receipt(payload.event_id,true);throw error;}
  })());
});
self.addEventListener("notificationclick",event=>{
  event.notification.close();
  event.waitUntil((async()=>{
    const windows=await clients.matchAll({type:"window",includeUncontrolled:true});
    const existing=windows.find(w=>new URL(w.url).origin===self.location.origin);
    if(existing){await existing.focus();return;}
    await clients.openWindow("/");
  })());
});
