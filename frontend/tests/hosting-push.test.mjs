import test from "node:test";
import assert from "node:assert/strict";
import { browserOrigin,sameOrigin } from "../lib/server-auth.ts";
import { ensurePushSubscription } from "../lib/push-subscription.ts";

test("trusted public origin works behind HTTP proxy and rejects spoofed origins",()=>{
  const old=process.env.FINN_PUBLIC_ORIGIN;
  try{
    process.env.FINN_PUBLIC_ORIGIN="https://finn.example";
    const good=new Request("http://localhost:8080/api/session",{headers:{host:"localhost:8080",origin:"https://finn.example"}});
    assert.equal(browserOrigin(good),"https://finn.example");assert.equal(sameOrigin(good),true);
    assert.equal(sameOrigin(new Request("http://localhost/api/session",{headers:{origin:"https://evil.example","x-forwarded-host":"finn.example"}})),false);
    process.env.FINN_PUBLIC_ORIGIN="http://public.example";
    assert.equal(browserOrigin(good),null);assert.equal(sameOrigin(good),false);
  }finally{if(old===undefined)delete process.env.FINN_PUBLIC_ORIGIN;else process.env.FINN_PUBLIC_ORIGIN=old;}
});

const key=new Uint8Array(65);key[0]=4;key.fill(8,1);
const encoded=Buffer.from(key).toString("base64url");
test("matching browser subscription is reused without another opt-in",async()=>{
  const existing={options:{applicationServerKey:key.buffer}};
  assert.equal(await ensurePushSubscription({getSubscription:async()=>existing,subscribe:()=>{throw new Error("unexpected")}},encoded),existing);
});
test("rotated VAPID key replaces old subscription before subscribing",async()=>{
  const order=[];
  const result=await ensurePushSubscription({getSubscription:async()=>({options:{applicationServerKey:new Uint8Array(65).buffer},unsubscribe:async()=>{order.push("unsubscribe");return true;}}),subscribe:async(options)=>{order.push("subscribe");assert.equal(options.userVisibleOnly,true);return "new";}},encoded);
  assert.equal(result,"new");assert.deepEqual(order,["unsubscribe","subscribe"]);
});
test("failed unsubscribe does not create an additional subscription",async()=>{
  await assert.rejects(()=>ensurePushSubscription({getSubscription:async()=>({options:{},unsubscribe:async()=>false}),subscribe:()=>{throw new Error("unexpected")}},encoded),/could not be replaced/);
});
test("malformed VAPID key never subscribes",async()=>{
  await assert.rejects(()=>ensurePushSubscription({getSubscription:()=>{throw new Error("unexpected")}},"abcd"),/invalid server key/);
});
