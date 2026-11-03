"use client";
import { Children, Fragment, isValidElement, useEffect, useId, useMemo, useRef, useState } from "react";
import type { KeyboardEvent, ReactNode, SelectHTMLAttributes } from "react";
import { createPortal } from "react-dom";
import { Check } from "lucide-react";
import { matchingOption, menuPlacement, nextEnabled } from "@/lib/select-menu";
import type { MenuOption } from "@/lib/select-menu";

function optionText(node:ReactNode):string {
  return Children.toArray(node).map(child=>isValidElement<{children?:ReactNode}>(child)?optionText(child.props.children):String(child)).join("");
}
function optionsFrom(children:ReactNode,group?:string,groupDisabled=false):MenuOption[] {
  return Children.toArray(children).flatMap(child=>{
    if(!isValidElement<{children?:ReactNode;value?:string|number;label?:string;disabled?:boolean}>(child))return [];
    if(child.type===Fragment)return optionsFrom(child.props.children,group,groupDisabled);
    if(child.type==="optgroup")return optionsFrom(child.props.children,child.props.label,groupDisabled||!!child.props.disabled);
    if(child.type!=="option")return [];
    const label=child.props.label||optionText(child.props.children);
    return [{value:String(child.props.value??label),label,disabled:groupDisabled||!!child.props.disabled,group}];
  });
}
/** Themed single-select UI; native select retains form values and change events. */
export function Select(props:SelectHTMLAttributes<HTMLSelectElement>) {
  if(props.multiple||(props.size||0)>1)return <select {...props} className={`finn-select ${props.className||""}`}/>;
  return <ThemedSelect {...props}/>;
}
function ThemedSelect(props:SelectHTMLAttributes<HTMLSelectElement>) {
  const {children,className="",value,defaultValue,disabled,onChange,onInvalid,id,style,...nativeProps}=props;
  const uid=useId().replaceAll(":","");
  const triggerId=id||`finn-select-${uid}`,listId=`${triggerId}-options`;
  const options=useMemo(()=>optionsFrom(children),[children]);
  const [internal,setInternal]=useState(String(defaultValue??options[0]?.value??""));
  const selected=String(value??internal),selectedIndex=options.findIndex(o=>o.value===selected);
  const [open,setOpen]=useState(false),[active,setActive]=useState(-1),[label,setLabel]=useState("");
  const [invalid,setInvalid]=useState(false),[placement,setPlacement]=useState<ReturnType<typeof menuPlacement>|null>(null);
  const positioned=placement!==null;
  const wrapper=useRef<HTMLSpanElement>(null),trigger=useRef<HTMLButtonElement>(null),native=useRef<HTMLSelectElement>(null),popup=useRef<HTMLDivElement>(null);
  const typeahead=useRef({text:"",at:0}),blocked=disabled||!options.some(o=>!o.disabled);
  useEffect(()=>{
    const parent=wrapper.current?.closest("label");
    if(parent)setLabel(Array.from(parent.childNodes).filter(n=>n!==wrapper.current).map(n=>n.textContent||"").join(" ").replace(/\s+/g," ").trim());
  },[]);
  useEffect(()=>{if(value===undefined&&native.current)setInternal(native.current.value);},[value,children]);
  useEffect(()=>{if(blocked)setOpen(false);},[blocked]);
  useEffect(()=>{if(open&&(!options[active]||options[active].disabled))setActive(nextEnabled(options,-1,1));},[open,active,options]);
  useEffect(()=>{
    if(!open)return;
    function position(){
      if(!trigger.current)return;
      const visual=window.visualViewport;
      const bounds=trigger.current.getBoundingClientRect();
      if(bounds.bottom<0||bounds.top>window.innerHeight){setOpen(false);return;}
      setPlacement(menuPlacement(trigger.current.getBoundingClientRect(),{width:window.innerWidth,height:visual?.height||window.innerHeight,top:visual?.offsetTop||0}));
    }
    function outside(event:PointerEvent){const target=event.target as Node;if(!wrapper.current?.contains(target)&&!popup.current?.contains(target))setOpen(false);}
    position();document.addEventListener("pointerdown",outside,true);
    window.addEventListener("resize",position);window.addEventListener("scroll",position,true);
    window.visualViewport?.addEventListener("resize",position);window.visualViewport?.addEventListener("scroll",position);
    const observer=new ResizeObserver(position);if(trigger.current)observer.observe(trigger.current);
    return()=>{document.removeEventListener("pointerdown",outside,true);window.removeEventListener("resize",position);window.removeEventListener("scroll",position,true);window.visualViewport?.removeEventListener("resize",position);window.visualViewport?.removeEventListener("scroll",position);observer.disconnect();};
  },[open]);
  useEffect(()=>{if(open&&active>=0)popup.current?.querySelector<HTMLElement>(`[data-option-index="${active}"]`)?.scrollIntoView({block:"nearest"});},[open,active,positioned]);
  function reveal(index=selectedIndex){
    if(blocked)return;
    setPlacement(null);setActive(index>=0&&!options[index]?.disabled?index:nextEnabled(options,-1,1));typeahead.current={text:"",at:0};setOpen(true);
  }
  function choose(index:number){
    const option=options[index];if(!option||option.disabled||!native.current)return;
    native.current.value=option.value;native.current.dispatchEvent(new Event("change",{bubbles:true}));
    setInvalid(false);setOpen(false);trigger.current?.focus({preventScroll:true});
  }
  function key(event:KeyboardEvent<HTMLButtonElement>){
    if(event.key==="Tab"){setOpen(false);return;}
    if(event.key==="Escape"&&open){event.preventDefault();event.stopPropagation();event.nativeEvent.stopImmediatePropagation();setOpen(false);return;}
    if(event.key==="Enter"||event.key===" "){event.preventDefault();if(open)choose(active);else reveal();return;}
    if(["ArrowDown","ArrowUp","Home","End"].includes(event.key)){
      event.preventDefault();
      const i=event.key==="Home"?nextEnabled(options,-1,1):event.key==="End"?nextEnabled(options,-1,-1):open?nextEnabled(options,active,event.key==="ArrowDown"?1:-1):selectedIndex>=0?selectedIndex:nextEnabled(options,-1,event.key==="ArrowDown"?1:-1);
      if(!open)reveal(i);else setActive(i);return;
    }
    if(event.key.length===1&&!event.ctrlKey&&!event.altKey&&!event.metaKey){
      event.preventDefault();const now=Date.now(),buffer=now-typeahead.current.at<600?typeahead.current.text+event.key:event.key;
      const query=buffer.split("").every(c=>c===buffer[0])?buffer[0]:buffer;
      const i=matchingOption(options,query,open?active:selectedIndex);
      if(!open)reveal(i);else if(i>=0)setActive(i);
      typeahead.current={text:buffer,at:now};
    }
  }
  const accessibleLabel=props["aria-label"]||label||props.title||"Select option";
  return <span ref={wrapper} className={`finn-select-shell ${open?"is-open":""}`}>
    <button ref={trigger} id={triggerId} type="button" role="combobox" className={`finn-select ${className}`} style={style}
      aria-label={accessibleLabel} aria-labelledby={props["aria-labelledby"]} aria-describedby={[props["aria-describedby"],invalid?`${triggerId}-error`:""].filter(Boolean).join(" ")||undefined}
      aria-haspopup="listbox" aria-expanded={open} aria-controls={open?listId:undefined} aria-activedescendant={open&&active>=0?`${listId}-${active}`:undefined}
      aria-required={props.required||undefined} aria-invalid={props["aria-invalid"]||invalid||undefined} disabled={blocked}
      onKeyDown={key} onClick={()=>open?setOpen(false):reveal()} onBlur={()=>{setTimeout(()=>{if(!popup.current?.contains(document.activeElement)&&document.activeElement!==trigger.current)setOpen(false);},0);}}>
      <span className="finn-select-value">{options[selectedIndex]?.label||"Select an option"}</span>
    </button>
    <select {...nativeProps} ref={native} id={`${triggerId}-native`} hidden aria-hidden="true" tabIndex={-1} disabled={disabled} value={value===undefined?internal:value}
      onChange={event=>{if(value===undefined)setInternal(event.target.value);setInvalid(false);onChange?.(event);}}
      onInvalid={event=>{event.preventDefault();setInvalid(true);trigger.current?.focus();onInvalid?.(event);}}>{children}</select>
    {invalid&&<span className="finn-select-error" id={`${triggerId}-error`} role="alert">Choose an option.</span>}
    {open&&placement&&createPortal(<div ref={popup} id={listId} className="finn-select-popup" role="listbox" aria-label={accessibleLabel} style={placement} onClick={event=>event.stopPropagation()}>
      {options.map((option,i)=><div id={`${listId}-${i}`} key={`${option.value}-${i}`} data-option-index={i} role="option" aria-selected={option.value===selected} aria-disabled={option.disabled||undefined}
        className={`finn-select-option ${active===i?"is-active":""} ${option.value===selected?"is-selected":""}`}
        onPointerMove={event=>{if(event.pointerType!=="touch"&&!option.disabled)setActive(i);}} onPointerDown={event=>{if(event.pointerType!=="touch")event.preventDefault();}} onClick={()=>choose(i)}>
        <span>{option.group&&<small>{option.group}</small>}{option.label}</span>{option.value===selected&&<Check size={17} aria-hidden="true"/>}
      </div>)}
    </div>,document.body)}
  </span>;
}
