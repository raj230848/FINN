import test from "node:test";
import assert from "node:assert/strict";
import {api,ApiError} from "../lib/api.ts";

test("import errors preserve status and actionable backend detail",async t=>{
  t.mock.method(globalThis,"fetch",async()=>new Response(JSON.stringify({detail:"PDF has 3001 pages; configured limit is 3000."}),{status:422}));
  await assert.rejects(api("/documents"),e=>e instanceof ApiError&&e.status===422&&e.message.includes("3001 pages"));
});
test("reverse-proxy HTML and null errors do not become parser/type crashes",async t=>{
  t.mock.method(globalThis,"fetch",async()=>new Response("<html>Bad gateway</html>",{status:502}));
  await assert.rejects(api("/documents"),e=>e.status===502&&e.code==="INVALID_RESPONSE"&&e.message.includes("Source library"));
  globalThis.fetch=async()=>new Response("null",{status:503});
  await assert.rejects(api("/dashboard"),e=>e.status===503&&e.message.includes("service is unavailable"));
});
test("lost import connection never automatically resends a POST",async t=>{
  let calls=0;t.mock.method(globalThis,"fetch",async()=>{calls++;throw new TypeError("Failed to fetch");});
  await assert.rejects(api("/documents",{method:"POST"}),e=>e.status===0&&e.code==="NETWORK_ERROR"&&e.message.includes("before retrying"));
  assert.equal(calls,1);
});
test("aborted autocomplete requests keep their abort semantics",async t=>{
  const controller=new AbortController();controller.abort();const error=new DOMException("Aborted","AbortError");
  t.mock.method(globalThis,"fetch",async()=>{throw error;});
  await assert.rejects(api("/company-search?q=Info",{signal:controller.signal}),e=>e===error);
});
