import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";
import {THEME_BOOTSTRAP,THEME_CANVAS,validTheme} from "../lib/theme.ts";

test("stored theme initializes before hydration; invalid or blocked storage falls back safely",()=>{
  for(const [stored,expected] of [["light","light"],["dark","dark"],["invalid","light"],[null,"light"]]){
    const root={dataset:{},style:{}},meta={content:""};
    vm.runInNewContext(THEME_BOOTSTRAP,{localStorage:{getItem:()=>stored},document:{documentElement:root,querySelector:()=>meta}});
    assert.equal(validTheme(stored),expected);
    assert.equal(root.dataset.theme,expected);assert.equal(root.style.colorScheme,expected);
    assert.equal(meta.content,THEME_CANVAS[expected]);
  }
  const root={dataset:{},style:{}};
  vm.runInNewContext(THEME_BOOTSTRAP,{localStorage:{getItem:()=>{throw Error("blocked");}},document:{documentElement:root,querySelector:()=>null}});
  assert.equal(root.dataset.theme,"light");
});

const css=fs.readFileSync(new URL("../app/themes.css",import.meta.url),"utf8");
function luminance(hex){const values=[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);return values[0]*.2126+values[1]*.7152+values[2]*.0722;}
function contrast(a,b){const x=luminance(a),y=luminance(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);}
for(const theme of ["dark","light"]){
  test(`${theme} theme text and control boundaries meet defined AA contrast checks`,()=>{
    const section=css.match(new RegExp(`html\\[data-theme="${theme}"\\]\\s*\\{([^}]+)\\}`))[1];
    const tokens=Object.fromEntries([...section.matchAll(/--([\w-]+):\s*(#[\da-fA-F]{6})/g)].map(m=>[m[1],m[2]]));
    for(const [fg,bg] of [["text","canvas"],["text","surface"],["text-muted","surface"],["primary","primary-soft"],["positive","positive-soft"],["negative","negative-soft"],["info","info-soft"],["warning","warning-soft"],["on-primary","primary"]])assert.ok(contrast(tokens[fg],tokens[bg])>=4.5,`${fg} on ${bg}: ${contrast(tokens[fg],tokens[bg])}`);
    assert.ok(contrast(tokens["border-strong"],tokens.control)>=3,"Interactive border contrast");
    if(theme==="dark")for(const fg of ["text","text-secondary","text-muted"]){
      for(const bg of ["canvas","surface","surface-raised","control"])assert.ok(contrast(tokens[fg],tokens[bg])>=7,`${fg} must remain easy to read on ${bg}: ${contrast(tokens[fg],tokens[bg])}`);
    }
    if(theme==="light")for(const fg of ["text-secondary","text-muted","primary","info"]){
      for(const bg of ["canvas","gradient-warm"])assert.ok(contrast(tokens[fg],tokens[bg])>=4.5,`${fg} on the deeper ${bg}: ${contrast(tokens[fg],tokens[bg])}`);
    }
  });
}
