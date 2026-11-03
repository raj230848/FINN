import test from "node:test";
import assert from "node:assert/strict";
import {backendTimeoutMs, guestAllows} from "../lib/proxy-policy.ts";

test("complete PDF imports have a bounded three-minute proxy window",()=>{
  assert.equal(backendTimeoutMs("POST",["documents"]),180000);
});
test("other operations retain their shorter timeout",()=>{
  for(const [method,path] of [["GET",["documents"]],["POST",["research"]],["POST",["companies","INFY","discover"]],["POST",["documents","other"]],["GET",["dashboard"]]])assert.equal(backendTimeoutMs(method,path),55000);
});

test("anonymous preview permits read paths and bounded research but cannot mutate the shared desk", () => {
  for (const path of [["dashboard"], ["company-search"], ["companies", "M&M", "documents"], ["announcements", "20", "context"]]) {
    assert.equal(guestAllows("GET", path), true);
  }
  assert.equal(guestAllows("POST", ["research"]), true);
  for (const [method, path] of [
    ["POST", ["documents"]], ["POST", ["sync"]], ["PATCH", ["companies", "INFY"]],
    ["PUT", ["preferences"]], ["POST", ["notifications", "read-all"]], ["POST", ["push", "subscribe"]],
    ["GET", ["operations"]], ["GET", ["companies", "..", "documents"]], ["GET", ["companies/INFY", "documents"]],
  ]) {
    assert.equal(guestAllows(method, path), false, `${method} ${path.join("/")}`);
  }
});
