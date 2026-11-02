import test from "node:test";
import assert from "node:assert/strict";
import {backendTimeoutMs} from "../lib/proxy-policy.ts";

test("complete PDF imports have a bounded three-minute proxy window",()=>{
  assert.equal(backendTimeoutMs("POST",["documents"]),180000);
});
test("other operations retain their shorter timeout",()=>{
  for(const [method,path] of [["GET",["documents"]],["POST",["research"]],["POST",["companies","INFY","discover"]],["POST",["documents","other"]],["GET",["dashboard"]]])assert.equal(backendTimeoutMs(method,path),55000);
});
