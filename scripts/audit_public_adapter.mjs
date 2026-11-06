import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createDemoStore,validateSnapshot} from '../public-site/lib/hosted-api.ts';

const snapshot=validateSnapshot(JSON.parse(await readFile(new URL('../public-site/public/data/snapshot-sourced.json',import.meta.url),'utf8')));
const store=createDemoStore(snapshot);
const cases=[];
async function check(path,verify){
  try {const result=await store(path);verify?.(result);cases.push({path,status:'passed'});return result;}
  catch(error){cases.push({path,status:'failed',message:error.message});}
}
const dashboard=await check('/dashboard',data=>assert.equal(data.stats.companies,snapshot.companies.filter(c=>c.watched).length));
await check('/companies',data=>assert.equal(data.length,snapshot.companies.length));
await check('/company-search?q=infosys',data=>assert.equal(data.items[0].ticker,'INFY'));
await check('/companies?has_guidance=true',data=>assert.equal(data.length,Object.values(snapshot.guidance).filter(group=>group.items.length).length));
await check('/preferences');
await check('/notifications',data=>assert.ok(data.items.every(item=>item.mode==='sourced'&&item.source_url)));
await check('/alerts',data=>assert.ok(data.every(item=>item.mode==='sourced'&&item.source_url)));
for(const window of ['24h','7d','30d']) await check('/announcements?window='+window+'&include_routine=true&limit=300',data=>{
  assert.equal(data.items.length,data.total);assert.ok(data.items.every(item=>item.mode==='sourced'&&item.source_url));
});
for(const company of snapshot.companies){
  const ticker=company.ticker;
  await check(`/companies/${ticker}/documents`,data=>assert.ok(data.every(row=>row.ticker===ticker&&row.source_url.startsWith('https://'))));
  await check(`/companies/${ticker}/guidance`,data=>assert.ok(data.items.every(row=>row.ticker===ticker)));
  const financials=await check(`/companies/${ticker}/financials`);
  for(const period of financials?.periods||[]) await check(`/companies/${ticker}/financials?period=${period}`,data=>assert.equal(data.current_period,period));
}
for(const filing of snapshot.announcements) await check(`/announcements/${filing.id}/context`,data=>assert.match(data.message,/original NSE filing/));
for(const quote of dashboard?.companies||[]){
  const raw=snapshot.quotes.find(row=>row.ticker===quote.ticker),last=raw.history.at(-1),prior=raw.history.at(-2);
  assert.equal(quote.close,last?.close??null);assert.equal(quote.volume,last?.volume??null);
  if(quote.change_pct!==null) assert.ok(Math.abs(quote.change_pct-(last.close-prior.close)/Math.abs(prior.close)*100)<1e-9);
  if(quote.volume_ratio!==null){
    const baseline=raw.history.slice(0,-1).slice(-snapshot.preferences.lookback);
    assert.ok(Math.abs(quote.volume_ratio-last.volume/(baseline.reduce((sum,row)=>sum+row.volume,0)/baseline.length))<1e-9);
  }
}
const report={checked_at:new Date().toISOString(),target:'Public application adapter using actual sourced feed; not HTTP backend deployment',
  cases,passed:cases.filter(row=>row.status==='passed').length,failed:cases.filter(row=>row.status==='failed').length,
  observations:snapshot.quotes.reduce((sum,quote)=>sum+quote.history.length,0),filings:snapshot.announcements.length,
  calculation_checks:'Every current quote, daily price change and non-null volume ratio independently recalculated.'};
const out=new URL('../artifacts/audit-2026-11-06/adapter-audit.json',import.meta.url);
await mkdir(new URL('.',out),{recursive:true});await writeFile(out,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:report.passed,failed:report.failed,observations:report.observations,filings:report.filings}));
if(report.failed)process.exitCode=1;
