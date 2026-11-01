"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { ensurePushSubscription } from "@/lib/push-subscription";

const DEVICE_KEY="finn.push.device.v1";
function deviceId() {
  let id=localStorage.getItem(DEVICE_KEY);
  if(!id){id=crypto.randomUUID();localStorage.setItem(DEVICE_KEY,id);}
  return id;
}
export function BrowserPush() {
  const [supported,setSupported]=useState(false),[available,setAvailable]=useState(false);
  const [enabled,setEnabled]=useState(false),[busy,setBusy]=useState(false),[message,setMessage]=useState("");
  useEffect(()=>{
    const capable=window.isSecureContext && "serviceWorker" in navigator && "PushManager" in window && "Notification" in window;
    setSupported(capable);
    if(!capable)return;
    let cancelled=false;
    api<{available:boolean}>("/push/config").then(c=>{if(!cancelled)setAvailable(c.available);}).catch(()=>{});
    const id=localStorage.getItem(DEVICE_KEY);
    if(id)api<{enabled:boolean}>(`/push/status?device_id=${encodeURIComponent(id)}`).then(s=>{if(!cancelled)setEnabled(s.enabled);}).catch(()=>{});
    return()=>{cancelled=true;};
  },[]);
  async function toggle() {
    setBusy(true);setMessage("");
    try {
      const id=deviceId();
      if(enabled){
        // Disable delivery first; a failure to remove browser registration
        // cannot leave this recipient opted in on the server.
        await api("/push/unsubscribe",{method:"POST",body:JSON.stringify({device_id:id})});
        setEnabled(false);
        const registration=await navigator.serviceWorker.getRegistration("/");
        await (await registration?.pushManager.getSubscription())?.unsubscribe();
        setMessage("Browser alerts disabled on this device.");
      } else {
        const permission=await Notification.requestPermission();
        if(permission!=="granted")throw new Error("Notifications are blocked. Enable notifications for this site in browser settings, then try again. In-app history remains available.");
        const config=await api<{available:boolean;public_key:string}>("/push/config");
        if(!config.available)throw new Error("The server has not configured browser push.");
        await navigator.serviceWorker.register("/finn-sw.js",{scope:"/"});
        const registration=await navigator.serviceWorker.ready;
        const subscription=await ensurePushSubscription(registration.pushManager,config.public_key);
        await api("/push/subscribe",{method:"POST",body:JSON.stringify({device_id:id,subscription:subscription.toJSON()})});
        setEnabled(true);setMessage("Enabled for new sourced events that match your monitoring settings. Older events are not sent.");
      }
    } catch(e){setMessage((e as Error).message);} finally{setBusy(false);}
  }
  return <section className="browser-push-settings" aria-label="Browser delivery">
    <div><b>Alerts beyond this tab</b><p>{!supported?"This browser doesn’t support Web Push here. On iPhone, use a supported installed home-screen app.":!available?"Browser delivery needs server-side VAPID configuration. Your in-app history still works.":"Opt in on this device for new sourced filings and completed-session threshold events. No demo alerts are sent."}</p></div>
    {supported && <button className="btn" disabled={busy || (!available&&!enabled)} onClick={()=>void toggle()}>{busy?"Saving…":enabled?"Disable browser alerts":"Enable browser alerts"}</button>}
    {message&&<p role="status">{message}</p>}
  </section>;
}
