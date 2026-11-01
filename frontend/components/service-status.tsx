"use client";
import { useState } from "react";
import { api } from "@/lib/api";

type Status = {
  metrics: {counts:Record<string,number>};
  sources: {status:string; latest_market_session:string|null; covered_companies:number; watched_companies:number};
  last_sync: {result:{status?:string;message?:string}}|null;
  push: {configured:boolean; delivery_counts:Record<string,number>};
};
export function ServiceStatus() {
  const [data,setData]=useState<Status|null>(null),[error,setError]=useState(""),[busy,setBusy]=useState(false);
  async function load(){
    setBusy(true);setError("");
    try{setData(await api<Status>("/operations"));}catch(e){setError((e as Error).message);}finally{setBusy(false);}
  }
  const counts=data?.metrics.counts||{};
  const failures=Object.entries(counts).filter(([k])=>k.startsWith("gemini.")&&!k.endsWith(".success")).reduce((n,[,v])=>n+v,0);
  return <details className="service-status" onToggle={e=>{if(e.currentTarget.open&&!data&&!busy)void load();}}>
    <summary>Service status and recent failures</summary>
    <button className="text-button" disabled={busy} onClick={()=>void load()}>{busy?"Checking…":"Update status"}</button>
    {error&&<p role="alert">{error}</p>}
    {data&&<div>
      <p><b>Market sources:</b> {data.sources.status.replaceAll("_"," ")} · {data.sources.covered_companies}/{data.sources.watched_companies} watched companies. Latest session: {data.sources.latest_market_session||"not fetched"}.</p>
      <p><b>Last refresh:</b> {data.last_sync?.result.status||"not started"}. {data.last_sync?.result.message}</p>
      <p><b>Gemini:</b> {counts["gemini.success"]||0} completed requests; {failures} unavailable or rejected requests. Evidence fallback remains available.</p>
      <p><b>Request protection:</b> {counts["api.rate_limited"]||0} rate-limited; {counts["api.unauthorized"]||0} unauthorized.</p>
      <p><b>Browser delivery:</b> {data.push.configured?"configured":"not configured"}. {data.push.delivery_counts.sent||0} accepted by the push provider; {(data.push.delivery_counts.pending||0)+(data.push.delivery_counts.retry||0)} pending. Provider acceptance does not confirm device display.</p>
      <small>Request counters cover the current service process and reset after restart. Market session dates and filing-coverage warnings remain authoritative.</small>
    </div>}
  </details>;
}
