export type Theme="dark"|"light";
export const THEME_KEY="finn.theme.v1";
export const THEME_CANVAS={dark:"#080F1C",light:"#E3C6A5"} as const;
export function validTheme(value:unknown):Theme {return value==="light"?"light":"dark";}
export const THEME_BOOTSTRAP=`(()=>{let t="dark";try{if(localStorage.getItem("${THEME_KEY}")==="light")t="light"}catch{}document.documentElement.dataset.theme=t;document.documentElement.style.colorScheme=t;let m=document.querySelector('meta[name="theme-color"]');if(m)m.content=t==="dark"?"${THEME_CANVAS.dark}":"${THEME_CANVAS.light}"})()`;
