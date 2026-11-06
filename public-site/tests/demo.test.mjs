import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createDemoStore, matchResearchPassages, createFeedLoader, validateSnapshot } from '../lib/hosted-api.ts';

const snapshot=JSON.parse(await readFile(new URL('../public/data/snapshot-sourced.json',import.meta.url),'utf8'));

test('public notification read state survives reload and threshold recalculation',async()=>{
  const saved=new Map();
  const storage={getItem:k=>saved.get(k)||null,setItem:(k,v)=>saved.set(k,v)};
  const sample=structuredClone(snapshot);
  const guaranteed=sample.quotes[0].history;
  guaranteed.at(-1).close=guaranteed.at(-2).close*1.6;
  const store=createDemoStore(sample,storage);
  const initial=await store('/notifications?mode=sourced');
  assert.ok(initial.unread_count>0);
  await store('/notifications/read-all?mode=sourced',{method:'POST'});
  const prefs=await store('/preferences');
  await store('/preferences',{method:'PUT',body:JSON.stringify({...prefs,price_threshold:50,volume_multiplier:20})});
  const restored=createDemoStore(sample,storage);
  const final=await restored('/notifications?mode=sourced');
  assert.equal(final.unread_count,0);
  assert.equal(final.total,initial.total);
  assert.equal((await restored('/notifications?mode=demo')).total,0);
});

test('public filing pages have no overlap and TCS uses reviewed historical figures',async()=>{
  const store=createDemoStore(snapshot);
  const first=await store('/announcements?window=30d&limit=2');
  const second=await store('/announcements?window=30d&limit=2&offset=2');
  assert.equal(first.items.length,2);
  assert.ok(first.has_more);
  assert.equal(first.coverage.kind,'filing_snapshot');
  assert.ok(second.items.every(f=>!first.items.some(a=>a.id===f.id)));
  const tcs=await store('/companies/TCS/financials');
  assert.equal(tcs.rows.find(r=>r.metric==='revenue').current,7465);
  assert.equal(tcs.rows.find(r=>r.metric==='ebitda').current,null);
});

test('public company search, watchlist and Promise Tracker use the bundled portfolio', async () => {
  const store = createDemoStore(snapshot);
  const byName = await store('/company-search?q=infosys');
  const byTicker = await store('/company-search?q=INFY.NS');
  assert.equal(byName.items[0].ticker, 'INFY');
  assert.equal(byTicker.items[0].ticker, 'INFY');
  assert.deepEqual((await store('/company-search?q=missing-company')).items, []);
  await store('/companies/INFY', {method:'PATCH', body:JSON.stringify({watched:false})});
  assert.equal((await store('/dashboard?mode=sourced')).companies.some(company=>company.ticker==='INFY'), false);
  await store('/companies/INFY?add_if_listed=true', {method:'PATCH', body:JSON.stringify({watched:true})});
  assert.ok((await store('/dashboard?mode=sourced')).companies.some(company=>company.ticker==='INFY'));
  const tracked = await store('/companies?has_guidance=true');
  assert.deepEqual(tracked.map(company=>company.ticker).sort(),
    Object.keys(snapshot.guidance).filter(ticker=>snapshot.guidance[ticker].items.length).sort());
});

test('market data is source-only and incomplete history cannot produce false alerts',async()=>{
  const normal=createDemoStore(snapshot);
  const real=await normal('/dashboard');
  assert.ok(snapshot.announcements.every(f=>f.mode==='sourced' && f.source_url));
  assert.ok(real.companies.every(q=>q.history.length===65 && q.source_url.startsWith('https://finance.yahoo.com/')));
  assert.ok((await normal('/dashboard?mode=demo')).companies.every(q=>q.history.length===0 && q.close===null));
  const incomplete=structuredClone(snapshot);
  const q=incomplete.quotes.find(q=>q.ticker==='RELIANCE');
  q.history.splice(-2,1);
  const missing=incomplete.quotes.find(q=>q.ticker==='INFY');
  missing.history=[];
  const stale=incomplete.quotes.find(q=>q.ticker==='TCS');
  stale.history.pop();
  const store=createDemoStore(incomplete);
  const {companies}=await store('/dashboard');
  const row=(ticker)=>companies.find(q=>q.ticker===ticker);
  assert.equal(row('RELIANCE').change_pct,null);
  assert.equal(row('RELIANCE').volume_ratio,null);
  assert.equal(row('INFY').close,null);
  assert.equal(row('TCS').change_pct,null);
  assert.equal(row('TCS').volume_ratio,null);
  assert.ok((await store('/alerts')).every(a=>!['RELIANCE','INFY','TCS'].includes(a.ticker)));
});

test('research only returns issuer-specific evidence and rejects unsupported questions', async () => {
  const excerpts=JSON.parse(await readFile(new URL('../public/data/research.json',import.meta.url),'utf8'));
  for (const excerpt of excerpts) {
    assert.ok(snapshot.documents[excerpt.ticker].some(doc =>
      (excerpt.url === `${doc.source_url}#page=${excerpt.page}` || (excerpt.page === 1 && excerpt.url === doc.source_url)) && excerpt.page <= doc.page_count));
  }
  const results=matchResearchPassages('INFY','What does the company do?',excerpts);
  assert.ok(results.length>0 && results.every(p=>p.ticker==='INFY' && p.topic==='business'));
  assert.deepEqual(matchResearchPassages('INFY','What risks does the lunar spacecraft launch create?',excerpts),[]);
  assert.deepEqual(matchResearchPassages('UNKNOWN','What does the company do?',excerpts),[]);
});

test('invalid saved state cannot break alerts or restore simulated events',async()=>{
  const stored={preferences:{...snapshot.preferences,price_threshold:-1,companies:null},events:[null,{id:7,key:'demo:test',mode:'demo',title:'Synthetic event'}]};
  const store=createDemoStore(snapshot,{getItem:()=>JSON.stringify(stored),setItem:()=>{}});
  assert.deepEqual(await store('/preferences'),snapshot.preferences);
  assert.ok((await store('/notifications')).items.every(e=>e.mode==='sourced' && e.source_url));
  await assert.rejects(store('/companies/INFY',{method:'PATCH',body:'{"watched":"false"}'}),/watch/);
  await assert.rejects(store('/preferences',{method:'PUT',body:JSON.stringify(stored.preferences)}),/thresholds/);
});

test('new feed replaces market history without changing local watchlist and thresholds', async () => {
  const store = createDemoStore(snapshot);
  await store('/companies/INFY', {method:'PATCH',body:JSON.stringify({watched:false})});
  await store('/preferences', {method:'PUT',body:JSON.stringify({...snapshot.preferences,price_threshold:12})});
  const next = structuredClone(snapshot);
  const reliance = next.quotes.find(q=>q.ticker==='RELIANCE');
  reliance.history.at(-1).close += 7;
  store.replaceSnapshot(next);
  const dashboard = await store('/dashboard');
  assert.equal(dashboard.companies.some(q=>q.ticker==='INFY'),false);
  assert.equal(dashboard.companies.find(q=>q.ticker==='RELIANCE').close,reliance.history.at(-1).close);
  assert.equal((await store('/preferences')).price_threshold,12);
});

test('feed loader deduplicates simultaneous refreshes, recovers offline, and prevents rollback', async () => {
  let requests = 0, online = true, rollback = false;
  let clock = Date.parse('2026-11-06T10:00:00Z');
  const current = structuredClone(snapshot);
  current.refresh_status = {checked_at:'2026-11-06T10:00:00Z',status:'complete'};
  const loader = createFeedLoader(async url => {
    requests++;
    if (!online && String(url).startsWith('https://')) throw new Error('offline');
    const result = String(url).startsWith('/') ? snapshot : structuredClone(current);
    if (rollback) result.refresh_status = {checked_at:'2026-11-01T10:00:00Z',status:'complete'};
    return new Response(JSON.stringify(result));
  }, () => clock);
  await Promise.all([loader.load(),loader.load(),loader.load()]);
  assert.equal(requests,1);
  assert.equal(loader.status().status,'ready');
  online=false;
  clock+=301_000;
  assert.equal((await loader.load()).refresh_status.checked_at,current.refresh_status.checked_at);
  assert.equal(loader.status().status,'unavailable');
  online=true; rollback=true; clock+=301_000;
  assert.equal((await loader.load()).refresh_status.checked_at,current.refresh_status.checked_at);
  rollback=false; clock+=301_000;
  await loader.load();
  assert.equal(loader.status().status,'ready');
});

test('invalid market feed fails closed and first offline load uses bundled records honestly',async()=>{
  const invalid=structuredClone(snapshot);
  invalid.quotes[0].history[0].close=-1;
  assert.throws(()=>validateSnapshot(invalid),/invalid market/);
  const loader=createFeedLoader(async url=>{
    if(String(url).startsWith('https://')) throw new Error('offline');
    return new Response(JSON.stringify(snapshot));
  });
  assert.deepEqual((await loader.load()).quotes,snapshot.quotes);
  assert.equal(loader.status().status,'unavailable');
});


test('GitHub API transport recovers when the raw feed is blocked',async()=>{
  const urls=[];
  const loader=createFeedLoader(async url=>{
    urls.push(String(url));
    if(String(url).includes('raw.githubusercontent.com')) throw new Error('blocked');
    return new Response(JSON.stringify({encoding:'base64',content:Buffer.from(JSON.stringify(snapshot)).toString('base64')}));
  });
  assert.deepEqual((await loader.load()).quotes,snapshot.quotes);
  assert.equal(urls.length,2);
  assert.ok(urls[1].startsWith('https://api.github.com/repos/raj230848/FINN/contents/'));
  assert.notEqual(loader.status().status,'unavailable');
});
