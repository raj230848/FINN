"use client";
import {useEffect,useState} from "react";
import {Sun,Moon} from "lucide-react";
import {THEME_KEY,Theme,validTheme} from "@/lib/theme";
export function ThemeToggle(){
  const [theme,setTheme]=useState<Theme>("dark");
  function apply(value:Theme){
    document.documentElement.dataset.theme=value;document.documentElement.style.colorScheme=value;
    const meta=document.querySelector<HTMLMetaElement>('meta[name="theme-color"]');if(meta)meta.content=value==="dark"?"#10121C":"#FCFAF6";
    setTheme(value);
  }
  useEffect(()=>{setTheme(validTheme(document.documentElement.dataset.theme));const changed=(e:StorageEvent)=>{if(e.key===THEME_KEY)apply(validTheme(e.newValue));};window.addEventListener("storage",changed);return()=>window.removeEventListener("storage",changed);},[]);
  return <button className="theme-toggle" title={`Switch to ${theme==="dark"?"Light":"Dark"} theme`} aria-label={`Switch to ${theme==="dark"?"Light":"Dark"} theme`} onClick={()=>{const next=theme==="dark"?"light":"dark";apply(next);try{localStorage.setItem(THEME_KEY,next);}catch{}}}>{theme==="dark"?<Sun size={18}/>:<Moon size={18}/>}<span>{theme==="dark"?"Light":"Dark"}</span></button>;
}
