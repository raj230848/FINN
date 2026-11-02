"use client";
import { useEffect,useId,useRef,useState } from "react";
import { Loader2,Search,ShieldCheck,X,ArrowUpRight } from "lucide-react";
import { api,Company } from "@/lib/api";

export type CompanyMatch={ticker:string;name:string;exchange:string;sector:string|null;verified:boolean;source_date:string|null};
type SearchResult={items:CompanyMatch[];message:string;source_date:string|null;stale:boolean;warning?:string|null};
const cache=new Map<string,{at:number;data:SearchResult}>();
function Highlight({text,query}:{text:string;query:string}){
  const index=text.toLowerCase().indexOf(query.toLowerCase());
  if(index<0||!query)return <>{text}</>;
  return <>{text.slice(0,index)}<mark>{text.slice(index,index+query.length)}</mark>{text.slice(index+query.length)}</>;
}
export function CompanyLookup({onSelect,companies=[],compact=false,disabled=false}:{onSelect:(company:CompanyMatch)=>void|Promise<void>;companies?:Company[];compact?:boolean;disabled?:boolean}){
  const [query,setQuery]=useState(""),[open,setOpen]=useState(false),[active,setActive]=useState(-1);
  const [result,setResult]=useState<SearchResult|null>(null),[loading,setLoading]=useState(false),[selecting,setSelecting]=useState(false),[error,setError]=useState("");
  const input=useRef<HTMLInputElement>(null),version=useRef(0),id=useId();
  useEffect(()=>{
    if(!compact)return;
    const key=(e:KeyboardEvent)=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==="k"){e.preventDefault();input.current?.focus();setOpen(true);}};
    document.addEventListener("keydown",key);return()=>document.removeEventListener("keydown",key);
  },[compact]);
  useEffect(()=>{
    const current=++version.current;setActive(-1);setError("");
    const trimmed=query.trim();
    if(trimmed.length<2){setResult(null);setLoading(false);return;}
    const saved=cache.get(trimmed.toLowerCase());
    if(saved&&Date.now()-saved.at<300000){setResult(saved.data);setLoading(false);return;}
    setLoading(true);setResult(null);
    const controller=new AbortController();
    const timer=setTimeout(()=>{
      api<SearchResult>(`/company-search?q=${encodeURIComponent(trimmed)}&limit=8`,{signal:controller.signal})
        .then(data=>{if(current===version.current){setResult(data);cache.set(trimmed.toLowerCase(),{at:Date.now(),data});if(cache.size>60)cache.delete(cache.keys().next().value!);}})
        .catch(e=>{if(current===version.current&&!controller.signal.aborted){
          const local=companies.filter(c=>`${c.ticker} ${c.name}`.toLowerCase().includes(trimmed.toLowerCase()));
          setResult({items:local.slice(0,8).map(c=>({...c,exchange:"NSE",verified:false,source_date:null})),message:"Search is unavailable. Saved portfolio matches only; retry when connected.",source_date:null,stale:true});setError((e as Error).message);
        }})
        .finally(()=>{if(current===version.current)setLoading(false);});
    },300);
    return()=>{clearTimeout(timer);controller.abort();};
  },[query,companies]);
  const items=result?.items||[];
  async function choose(match:CompanyMatch){
    if(selecting)return;setSelecting(true);setError("");
    try{await onSelect(match);setQuery("");setOpen(false);}
    catch(e){setError((e as Error).message);}
    finally{setSelecting(false);}
  }
  return <div className={`nse-search ${compact?"compact":""}`} onBlur={e=>{if(!e.currentTarget.contains(e.relatedTarget as Node))setOpen(false);}}>
    <label className={compact?"sr-only":"field-label"} htmlFor={id}>Search NSE company name or ticker</label>
    <div className="nse-search-field">
      <Search size={18} aria-hidden="true"/>
      <input ref={input} id={id} role="combobox" aria-autocomplete="list" aria-expanded={open} aria-controls={`${id}-list`} aria-activedescendant={open&&items[active]?`${id}-${active}`:undefined} autoComplete="off" spellCheck={false} maxLength={100} placeholder={compact?"Search name or NSE ticker…":"Company name or NSE ticker, e.g. Infosys or INFY"} value={query} disabled={disabled||selecting} onFocus={()=>setOpen(true)} onChange={e=>{setQuery(e.target.value);setOpen(true);}} onKeyDown={e=>{
        if(e.key==="Escape"){setOpen(false);return;}
        if(e.key==="ArrowDown"){e.preventDefault();setOpen(true);setActive(i=>Math.min(i+1,items.length-1));}
        if(e.key==="ArrowUp"){e.preventDefault();setActive(i=>Math.max(i-1,0));}
        if(e.key==="Enter"){
          e.preventDefault();
          const exact=items.filter(c=>c.ticker.toLowerCase()===query.trim().toLowerCase().replace(/\.ns$/i,"")||c.name.toLowerCase()===query.trim().toLowerCase());
          const match=active>=0?items[active]:exact.length===1?exact[0]:null;
          if(match)void choose(match);else setOpen(true);
        }
      }}/>
      {(loading||selecting)?<Loader2 size={17} className="spin" aria-label={selecting?"Opening company":"Searching NSE directory"}/>:query?<button className="search-clear" aria-label="Clear company search" onClick={()=>{setQuery("");input.current?.focus();}}><X size={17}/></button>:compact?<kbd>⌘ K</kbd>:<span className="nse-only">NSE</span>}
    </div>
    {open&&<div className="nse-search-results" id={`${id}-list`} role="listbox" aria-label="NSE company suggestions">
      <div className="search-menu-title">{selecting?"Opening source library…":loading?"Searching the NSE directory…":"FIND YOUR COMPANY"}</div>
      {items.map((c,i)=><button id={`${id}-${i}`} role="option" aria-selected={active===i} key={c.ticker} className={`nse-result ${active===i?"active":""}`} disabled={selecting} onPointerDown={e=>e.preventDefault()} onMouseEnter={()=>setActive(i)} onClick={()=>void choose(c)}>
        <span className="nse-result-icon">{c.ticker.slice(0,2)}</span><span className="nse-result-copy"><b><Highlight text={c.name} query={query.trim()}/></b><small>{c.sector||"NSE-listed equity"} · {c.verified?<><ShieldCheck size={11}/>Directory confirmed</>:"Saved company"}</small></span><span className="ticker-chip"><Highlight text={c.ticker} query={query.trim()}/></span><ArrowUpRight size={14}/>
      </button>)}
      {!loading&&!items.length&&<p className="search-empty">{result?.message||"Type at least two characters. Search by company name or NSE ticker; choose a result to continue."}</p>}
      {error&&<p className="search-error" role="status">{error}</p>}
      {result?.warning&&<p className="search-warning">{result.warning}</p>}
      <div className="search-menu-footer"><span>↑ ↓ choose · Enter open · Esc close</span>{result?.source_date&&<small>Directory checked {new Date(result.source_date).toLocaleDateString("en-IN")}</small>}</div>
    </div>}
  </div>;
}
