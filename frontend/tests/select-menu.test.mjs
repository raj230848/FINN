import test from 'node:test';
import assert from 'node:assert/strict';
import {nextEnabled,matchingOption,menuPlacement} from '../lib/select-menu.ts';
const options=[{value:'INFY',label:'Infosys',disabled:false},{value:'X',label:'Unavailable',disabled:true},{value:'HCLTECH',label:'HCL Technologies Limited',disabled:false},{value:'HDFCBANK',label:'HDFC Bank',disabled:false}];
test('select navigation skips disabled options and wraps both directions',()=>{
 assert.equal(nextEnabled(options,0,1),2);assert.equal(nextEnabled(options,0,-1),3);assert.equal(nextEnabled(options,3,1),0);
 assert.equal(nextEnabled(options,-1,1),0);assert.equal(nextEnabled(options,-1,-1),3);
});
test('empty and entirely disabled menus cannot acquire an active option',()=>{
 assert.equal(nextEnabled([],-1,1),-1);assert.equal(nextEnabled([{value:'x',label:'x',disabled:true}],-1,1),-1);
 assert.equal(matchingOption([],'h',-1),-1);
});
test('typeahead matches ticker or label, cycles and ignores disabled rows',()=>{
 assert.equal(matchingOption(options,'hcl',0),2);assert.equal(matchingOption(options,'infosys',3),0);
 assert.equal(matchingOption(options,'h',2),3);assert.equal(matchingOption(options,'h',3),2);
 assert.equal(matchingOption(options,'unavailable',0),-1);assert.equal(matchingOption(options,'zz',0),-1);
});
test('popup fits a narrow phone and stays inside horizontal viewport edges',()=>{
 for(const width of [200,320,390,768,1440]){
  const p=menuPlacement({left:width-45,top:90,bottom:134,width:170},{width,height:740});
  assert.ok(p.left>=12);assert.ok(p.left+p.width<=width-12+.01);assert.ok(p.maxHeight<=320);
 }
});
test('popup opens above a low trigger without a gap when content is short',()=>{
 const p=menuPlacement({left:30,top:650,bottom:694,width:200},{width:390,height:740});
 assert.equal(p.top,644);assert.equal(p.transform,'translateY(-100%)');assert.ok(p.maxHeight<=638);
});
test('popup respects a reduced visual viewport',()=>{
 const p=menuPlacement({left:10,top:150,bottom:194,width:280},{width:320,height:260,top:40});
 assert.ok(p.maxHeight>0);assert.ok(p.maxHeight<=320);assert.ok(p.top>=52);
});
