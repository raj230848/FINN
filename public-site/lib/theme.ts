export type Theme="dark"|"light";
export const THEME_KEY="finn.theme.v1";
export const DEFAULT_THEME="light" satisfies Theme;
export const THEME_CANVAS={dark:"#080F1C",light:"#E3C6A5"} as const;
export function validTheme(value:unknown):Theme {return value==="dark"?"dark":DEFAULT_THEME;}
export const THEME_BOOTSTRAP=`(()=>{let t="${DEFAULT_THEME}";try{if(localStorage.getItem("${THEME_KEY}")==="dark")t="dark"}catch{}document.documentElement.dataset.theme=t;document.documentElement.style.colorScheme=t;let m=document.querySelector('meta[name="theme-color"]');if(m)m.content=t==="dark"?"${THEME_CANVAS.dark}":"${THEME_CANVAS.light}"})()`;
