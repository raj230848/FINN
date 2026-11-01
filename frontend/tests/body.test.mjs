import test from 'node:test';
import assert from 'node:assert/strict';
import {readSmallJson,BodyReadError} from '../lib/request-body.ts';

test('sign-in accepts a small JSON object',async()=>{
  const request=new Request('http://finn.local/api/session',{method:'POST',body:'{"access_code":"test-only"}'});
  assert.equal((await readSmallJson(request)).access_code,'test-only');
});
test('malformed JSON and non-object bodies are 400',async()=>{
  for(const body of ['{bad','null','[]','"text"'])await assert.rejects(readSmallJson(new Request('http://finn.local/',{method:'POST',body})),e=>e instanceof BodyReadError&&e.status===400);
});
test('oversized declared body is 413',async()=>{
  await assert.rejects(readSmallJson(new Request('http://finn.local/',{method:'POST',headers:{'content-length':'9999'},body:'{}'})),e=>e.status===413);
});
test('chunked body is bounded even without Content-Length',async()=>{
  const stream=new ReadableStream({start(c){c.enqueue(new Uint8Array(1500));c.enqueue(new Uint8Array(1500));c.close();}});
  const request=new Request('http://finn.local/',{method:'POST',body:stream,duplex:'half'});
  await assert.rejects(readSmallJson(request),e=>e.status===413);
});
