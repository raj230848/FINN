import type { Company, Filing, Prefs, Quote, Evidence, Financials, GuidanceItem, SourceDocument, NotificationEvent } from './api';

export type DemoSnapshot = {
  as_of: string; filings_as_of?: string; refresh_status?: {
    checked_at: string; status: 'complete' | 'partial' | 'failed';
    market_last_successful_at?: string | null; filings_last_successful_at?: string | null;
  };
  market_as_of?: string | null; market_sessions: string[]; companies: Company[]; quotes: Quote[]; announcements: Filing[]; preferences: Prefs;
  documents: Record<string, SourceDocument[]>; financials: Record<string, Financials>;
  guidance: Record<string, {items: GuidanceItem[]; note: string}>;
};
type Storage = Pick<globalThis.Storage, 'getItem' | 'setItem'>;
type Passage = Evidence & { ticker: string; topic: string };
const KEY = 'finn.public-demo.v1';
const percent = (a: number | null, b: number | null) => a === null || b === null || !b ? null : (a-b)/Math.abs(b)*100;

const lookbacks = [5, 10, 20, 30, 60];
function validPreferences(value: unknown): value is Prefs {
  if (!value || typeof value !== 'object') return false;
  const p = value as Prefs;
  return typeof p.price_threshold === 'number' && p.price_threshold >= .1 && p.price_threshold <= 50
    && typeof p.volume_multiplier === 'number' && p.volume_multiplier >= 1.1 && p.volume_multiplier <= 20
    && lookbacks.includes(p.lookback)
    && Array.isArray(p.companies) && p.companies.every(ticker => typeof ticker === 'string')
    && Array.isArray(p.categories) && p.categories.every(category => typeof category === 'string');
}

export function matchResearchPassages(ticker: string, question: string, passages: Passage[]) {
  const stop = new Set('the a an and or to of is are was were in for on at with what how do does did company its it this that from have has'.split(' '));
  const words = (value: string) => value.toLowerCase().match(/[a-z0-9]+/g) || [];
  const prompts = new Map([
    ['what does the company do', 'business'],
    ['how strong is cash conversion', 'cash'],
    ['what did management guide for growth', 'guidance'],
    ['what risks does management highlight', 'risk'],
  ]);
  const terms = [...new Set(words(question).filter(word => word.length > 1 && !stop.has(word)))];
  const topic = prompts.get(words(question).join(' '));
  return passages.filter(passage => {
    if (passage.ticker !== ticker || !Number.isInteger(passage.page) || passage.page < 1 || !passage.url.startsWith('https://')) return false;
    if (topic) return passage.topic === topic;
    const excerptWords = new Set(words(passage.excerpt));
    return terms.length > 0 && terms.every(word => excerptWords.has(word));
  }).slice(0, 4);
}

export function createDemoStore(snapshot: DemoSnapshot, storage?: Storage) {
  let companies = structuredClone(snapshot.companies);
  let preferences = structuredClone(snapshot.preferences);
  let events: (NotificationEvent & {key: string})[] = [];
  try {
    const saved = JSON.parse(storage?.getItem(KEY) || 'null');
    if (saved?.watched && Array.isArray(saved.watched)) companies = companies.map(c=>({...c,watched:saved.watched.includes(c.ticker)}));
    if (validPreferences(saved?.preferences)) preferences = {...preferences,...saved.preferences};
    if (Array.isArray(saved?.events)) events = saved.events.filter((e: NotificationEvent & {key: string}) =>
      e && Number.isInteger(e.id) && typeof e.key === 'string' && e.mode === 'sourced' && typeof e.title === 'string'
      && typeof e.source_url === 'string' && /^https:\/\/(finance\.yahoo\.com|nsearchives\.nseindia\.com)\//.test(e.source_url));
  } catch { /* Storage restrictions do not block the public demo. */ }
  function persist() { try { storage?.setItem(KEY,JSON.stringify({watched:companies.filter(c=>c.watched).map(c=>c.ticker),preferences,events})); } catch { /* Session state still works. */ } }
  function quotes(mode: string) {
    return snapshot.quotes.filter(q=>companies.some(c=>c.ticker===q.ticker && c.watched)).map(q=>{
      const history = mode === 'sourced' ? q.history : [];
      const last = history.at(-1), prev = history.at(-2), baseline = history.slice(0,-1).slice(-preferences.lookback);
      const expected = snapshot.market_sessions.slice(0,-1).slice(-preferences.lookback);
      const average = baseline.length === preferences.lookback && baseline.every((point,index)=>point.date===expected[index]) ? baseline.reduce((sum,p)=>sum+p.volume,0)/baseline.length : null;
      const current = !!last && last.date === snapshot.market_as_of;
      return {...q,watched:true,history,close:last?.close??null,volume:last?.volume??null,date:last?.date??null,
        change_pct:current && prev?.date===snapshot.market_sessions.at(-2) ? percent(last.close,prev?.close??null) : null,
        volume_ratio:current && average ? last.volume/average : null};
    });
  }
  function alerts(mode: string) {
    return quotes(mode).filter(q=>!preferences.companies.length || preferences.companies.includes(q.ticker)).flatMap((q,i)=>{
      const result = [];
      if (q.change_pct !== null && Math.abs(q.change_pct) >= preferences.price_threshold) result.push({id:i*2+1,ticker:q.ticker,kind:'price',title:`${q.ticker}: ${q.change_pct>0?'+':''}${q.change_pct.toFixed(2)}% daily move`,explanation:`Completed-session adjusted close changed ${q.change_pct.toFixed(2)}% versus the preceding session. Your threshold is ±${preferences.price_threshold}%.`,value:q.change_pct,threshold:preferences.price_threshold,date:q.date,mode,source_url:q.source_url});
      if (q.volume_ratio !== null && q.volume_ratio >= preferences.volume_multiplier) result.push({id:i*2+2,ticker:q.ticker,kind:'volume',title:`${q.ticker}: ${q.volume_ratio.toFixed(2)}× usual volume`,explanation:`Completed-session volume is ${q.volume_ratio.toFixed(2)} times the mean of the preceding ${preferences.lookback} sessions, excluding the latest session. Your threshold is ${preferences.volume_multiplier}×.`,value:q.volume_ratio,threshold:preferences.volume_multiplier,date:q.date,mode,source_url:q.source_url});
      return result;
    });
  }
  function filings(params: URLSearchParams) {
    const mode = params.get('mode') || 'sourced', window = params.get('window') || '24h';
    const archive = mode === 'sourced';
    const asOf = archive ? snapshot.filings_as_of : snapshot.as_of;
    const end = window === 'custom' ? Date.parse(params.get('end') || '') : Date.parse(asOf || '');
    const start = window==='custom' ? Date.parse(params.get('start') || '') : end-({ '24h':24,'7d':168,'30d':720 }[window] || 24)*3600000;
    const items = snapshot.announcements.filter(f=>f.mode===mode && companies.some(c=>c.ticker===f.ticker && c.watched) && Date.parse(f.published_at)>=start && Date.parse(f.published_at)<=end && (!params.get('ticker') || f.ticker===params.get('ticker')) && (!params.get('category') || f.category===params.get('category')) && (!params.get('priority') || f.priority===params.get('priority'))).sort((a,b)=>b.score-a.score || Date.parse(b.published_at)-Date.parse(a.published_at));
    const filtered=params.get('include_routine')==='true' ? items : items.filter(f=>f.priority!=='low');
    const offset=Math.max(0,Number(params.get('offset'))||0), limit=Math.min(300,Math.max(1,Number(params.get('limit'))||100));
    return {items:filtered.slice(offset,offset+limit),routine_count:items.filter(f=>f.priority==='low').length,total:filtered.length,has_more:offset+limit<filtered.length,next_offset:offset+limit<filtered.length?offset+limit:null,coverage:{kind:archive?'filing_snapshot':'demo_fixture',partial_coverage:archive,message:archive?'Dated NSE filing snapshot. Some filings may be missing.':'No sourced filings for this mode.'},as_of:asOf};
  }
  function recordEvents() {
    const add=(key:string, event: Omit<NotificationEvent,'id'|'read_at'|'created_at'>)=>{
      if (!events.some(e=>e.key===key)) events.push({...event,key,id:Math.max(0,...events.map(e=>e.id))+1,read_at:null,created_at:snapshot.as_of});
    };
    for(const alert of alerts('sourced')) add(`market:${alert.ticker}:${alert.kind}:${alert.date}`,{ticker:alert.ticker,mode:'sourced',kind:alert.kind,severity:'medium',title:alert.title,explanation:alert.explanation,source_url:alert.source_url,occurred_at:`${alert.date}T13:00:00Z`});
    for(const filing of filings(new URLSearchParams({mode:'sourced',window:'24h'})).items.filter(f=>(f.priority==='high'||f.needs_review) && (!preferences.companies.length||preferences.companies.includes(f.ticker)))) add(`filing:${filing.id}`,{ticker:filing.ticker,mode:'sourced',kind:'filing',severity:filing.priority,title:filing.title,explanation:filing.why_matters,source_url:filing.source_url,occurred_at:filing.published_at});
    persist();
  }
  const request = async function request(path: string, options?: RequestInit): Promise<unknown> {
    const url = new URL(path,'https://finn.local');
    const mode = url.searchParams.get('mode') || 'sourced';
    const body = options?.body ? JSON.parse(String(options.body)) : {};
    if (url.pathname.startsWith('/notifications')) {
      recordEvents();
      if(url.pathname==='/notifications/read-all' && options?.method==='POST') {
        events=events.map(e=>e.mode===mode?{...e,read_at:e.read_at||new Date().toISOString()}:e);persist();return {status:'read'};
      }
      const read=url.pathname.match(/^\/notifications\/(\d+)\/read$/);
      if(read && options?.method==='POST') {const event=events.find(e=>e.id===Number(read[1]));if(!event)throw new Error('Notification unavailable.');event.read_at ||= new Date().toISOString();persist();return {...event};}
      const all=events.filter(e=>e.mode===mode).sort((a,b)=>b.id-a.id), filtered=url.searchParams.get('unread_only')==='true'?all.filter(e=>!e.read_at):all;
      const offset=Math.max(0,Number(url.searchParams.get('offset'))||0),limit=Math.min(100,Math.max(1,Number(url.searchParams.get('limit'))||50));
      return {items:structuredClone(filtered.slice(offset,offset+limit)),unread_count:all.filter(e=>!e.read_at).length,total:filtered.length,has_more:offset+limit<filtered.length};
    }
    const match = url.pathname.match(/^\/companies\/([^/]+)(?:\/(\w+))?$/);
    if (url.pathname === '/company-search') {
      const query = (url.searchParams.get('q') || '').trim().toLowerCase().replace(/\.ns$/, '');
      const limit = Math.min(20, Math.max(1, Number(url.searchParams.get('limit')) || 8));
      const items = query.length < 2 ? [] : companies
        .filter(company => `${company.ticker} ${company.name}`.toLowerCase().includes(query))
        .slice(0, limit)
        .map(company => ({...company, exchange: 'NSE', source_date: null}));
      return {items, message: items.length ? 'Choose a company.' : 'No matching company in the covered portfolio.', source_date: null, stale: false};
    }
    if (url.pathname === '/companies') {
      const results = url.searchParams.get('has_guidance') === 'true'
        ? companies.filter(company => snapshot.guidance[company.ticker]?.items.length)
        : companies;
      return structuredClone(results);
    }
    if (url.pathname==='/preferences') {
      if (options?.method==='PUT') {
        if (!validPreferences(body)) throw new Error('Choose valid monitoring thresholds.');
        preferences = {...preferences,...body}; persist();
      }
      return structuredClone(preferences);
    }
    if (url.pathname === '/announcements') return filings(url.searchParams);
    const contextMatch = url.pathname.match(/^\/announcements\/(\d+)\/context$/);
    if (contextMatch) {
      const filing = snapshot.announcements.find(item => item.id === Number(contextMatch[1]));
      return {message: filing?.mode === 'sourced'
        ? 'Open the original NSE filing to read the issuer’s disclosure.'
        : 'No source document is available for this filing.'};
    }
    if (url.pathname==='/alerts') return alerts(mode);
    if (url.pathname==='/dashboard') {
      const qs=quotes(mode), fs=filings(new URLSearchParams({mode:'sourced',window:'24h',include_routine:'true'})), as=alerts(mode);
      const high=fs.items.filter(f=>f.priority==='high').length, volumes=as.filter(a=>a.kind==='volume').length;
      return {mode,as_of:snapshot.filings_as_of || snapshot.as_of,companies:qs,stats:{companies:qs.length,high_priority:high,volume_alerts:volumes,price_alerts:as.filter(a=>a.kind==='price').length,routine:fs.routine_count,total_filings:fs.items.length,coverage:qs.filter(q=>q.close!==null && q.date===snapshot.market_as_of).length},digest:`${high} high-priority disclosures in the NSE snapshot. ${snapshot.market_as_of ? `${volumes} unusual-volume alerts for the market snapshot dated ${snapshot.market_as_of}.` : 'Market data is unavailable.'}`,last_sync:null,ai_configured:false,scheduler_enabled:false};
    }
    if (match) {
      const ticker=decodeURIComponent(match[1]).toUpperCase(), action=match[2], company=companies.find(c=>c.ticker===ticker);
      if (!company) throw new Error('This public demo covers the prepared portfolio. Use the full GitHub application to discover another NSE ticker.');
      if (options?.method==='PATCH') { if (typeof body?.watched !== 'boolean') throw new Error('Choose whether to watch this company.'); companies=companies.map(c=>c.ticker===ticker?{...c,watched:Boolean(body.watched)}:c);persist();return companies.find(c=>c.ticker===ticker); }
      if (action==='documents') return snapshot.documents[ticker] || [];
      if (action==='financials') return snapshot.financials[ticker] || {rows:[]};
      if (action==='guidance') return snapshot.guidance[ticker] || {items:[],note:'No reviewed comparisons available.'};
      if (action==='discover') return {company,documents:[],message:'Prepared source library loaded. New document discovery and imports are available in the full application on GitHub.'};
    }
    if (url.pathname==='/sync' || url.pathname==='/documents') throw new Error('Live refresh and document uploads are available in the full application: github.com/raj230848/FINN. This public site uses dated snapshots.');
    throw new Error('This operation is not included in the public demo.');
  };
  return Object.assign(request, {
    replaceSnapshot(next: DemoSnapshot) {
      const watched = new Map(companies.map(company => [company.ticker, company.watched]));
      companies = next.companies.map(company => ({...company, watched: watched.get(company.ticker) ?? company.watched}));
      snapshot = next;
    },
  });
}


export const PUBLIC_FEED_URL = 'https://raw.githubusercontent.com/raj230848/FINN/main/public-site/public/data/snapshot-sourced.json';
const FEED_POLL_MS = 60_000;
type FeedStatus = {
  checked_at: string | null;
  source_checked_at: string | null;
  status: 'ready' | 'partial' | 'delayed' | 'unavailable';
  message: string;
};

export function validateSnapshot(input: unknown): DemoSnapshot {
  if (!input || typeof input !== 'object') throw new Error('The update feed is not a valid snapshot.');
  const data = input as DemoSnapshot;
  if (!Array.isArray(data.companies) || !data.companies.length || !Array.isArray(data.quotes)
      || !Array.isArray(data.announcements) || !Array.isArray(data.market_sessions)
      || !data.guidance || !data.documents || !data.financials || !validPreferences(data.preferences)) {
    throw new Error('The update feed has missing data.');
  }
  const tickers = new Set(data.companies.map(company => company.ticker));
  if (tickers.size !== data.companies.length || data.quotes.length !== tickers.size) throw new Error('Duplicate or missing companies in the update.');
  const quoteTickers = new Set<string>();
  for (const quote of data.quotes) {
    if (!tickers.has(quote.ticker) || quoteTickers.has(quote.ticker) || !Array.isArray(quote.history)
        || (quote.history.length && quote.source_url !== 'https://finance.yahoo.com/quote/' + quote.ticker + '.NS/history/')) {
      throw new Error('The update contains an unverified market source.');
    }
    quoteTickers.add(quote.ticker);
    for (let i = 0; i < quote.history.length; i++) {
      const point = quote.history[i];
      if (!/^\d{4}-\d{2}-\d{2}$/.test(point.date) || !Number.isFinite(Date.parse(point.date))
          || !Number.isFinite(point.close) || point.close <= 0
          || !Number.isInteger(point.volume) || point.volume < 0
          || (i > 0 && point.date <= quote.history[i - 1].date)) {
        throw new Error('The update contains invalid market observations.');
      }
    }
  }
  for (const filing of data.announcements) {
    if (filing.mode !== 'sourced' || !tickers.has(filing.ticker) || !Number.isFinite(Date.parse(filing.published_at))
        || !/^https:\/\/(nsearchives\.nseindia\.com|archives\.nseindia\.com|www\.nseindia\.com)\//.test(filing.source_url || '')) {
      throw new Error('The update contains an unverified filing.');
    }
  }
  return data;
}

export function createFeedLoader(
  request: typeof fetch = fetch,
  now: () => number = Date.now,
) {
  let current: DemoSnapshot | null = null;
  let checkedAt = 0;
  let pending: Promise<DemoSnapshot> | null = null;
  let error = '';
  async function read(url: string) {
    const response = await request(url, {cache: 'no-store', signal: AbortSignal.timeout(15000)});
    if (!response.ok) throw new Error('Update feed HTTP ' + response.status);
    const text = await response.text();
    if (text.length > 3_000_000) throw new Error('The update feed is too large.');
    return validateSnapshot(JSON.parse(text));
  }
  async function update() {
    try {
      const next = await read(PUBLIC_FEED_URL + '?v=' + Math.floor(now() / FEED_POLL_MS));
      const oldTime = current?.refresh_status?.checked_at || current?.as_of;
      const newTime = next.refresh_status?.checked_at || next.as_of;
      if (oldTime && Date.parse(newTime) < Date.parse(oldTime)) throw new Error('An older feed was returned.');
      current = next;
      error = '';
    } catch {
      error = 'The latest update could not be checked. Showing the last available source data.';
      if (!current) current = await read('/data/snapshot-sourced.json');
    }
    checkedAt = now();
    return current!;
  }
  return {
    async load(force = false) {
      if (pending) return pending;
      if (!force && current && now() - checkedAt < FEED_POLL_MS) return current;
      pending = update().finally(() => { pending = null; });
      return pending;
    },
    status(): FeedStatus {
      const source = current?.refresh_status;
      const age = source ? now() - Date.parse(source.checked_at) : Infinity;
      const local = new Intl.DateTimeFormat('en-GB', {timeZone:'Asia/Kolkata', weekday:'short', hour:'numeric', hourCycle:'h23'}).formatToParts(new Date(now()));
      const weekend = ['Sat','Sun'].includes(local.find(part => part.type === 'weekday')?.value || '');
      const hour = Number(local.find(part => part.type === 'hour')?.value);
      const expected = !weekend && hour >= 10 && hour <= 19;
      const delayed = age > (expected ? 90 * 60_000 : 4 * 86400_000);
      return {
        checked_at: checkedAt ? new Date(checkedAt).toISOString() : null,
        source_checked_at: source?.checked_at || null,
        status: error ? 'unavailable' : source?.status === 'failed' ? 'unavailable'
          : source?.status === 'partial' ? 'partial' : delayed ? 'delayed' : 'ready',
        message: error || (source?.status === 'failed'
          ? 'Sources are unavailable. The last verified records are retained.'
          : source?.status === 'partial' ? 'Some sources could not refresh. Their previous dated records are retained.'
          : delayed ? 'Source updates are delayed. Dates below show the available records.'
          : 'Automatic source checks every 30 minutes on weekdays. Prices use completed trading sessions.'),
      };
    },
  };
}

let store: ReturnType<typeof createDemoStore> | null = null;
let activeSnapshot: DemoSnapshot | null = null;
const feed = createFeedLoader();
let passages: Promise<Passage[]> | null = null;
export async function hostedApi<T>(path: string, options?: RequestInit): Promise<T> {
  options?.signal?.throwIfAborted();
  const checking = path.split('?')[0] === '/sync';
  const snapshot = await feed.load(checking);
  options?.signal?.throwIfAborted();
  if (!store) {
    let storage: Storage | undefined;
    try { storage = window.localStorage; } catch { /* Keep session state when browser storage is blocked. */ }
    store = createDemoStore(snapshot, storage);
    activeSnapshot = snapshot;
  } else if (activeSnapshot !== snapshot) {
    store.replaceSnapshot(snapshot);
    activeSnapshot = snapshot;
  }
  if (checking) {
    const status = feed.status();
    return {id:null, status:status.status, message:status.message} as T;
  }
  if (path==='/research') {
    const input = JSON.parse(String(options?.body || '{}'));
    if (typeof input?.ticker !== 'string' || typeof input?.question !== 'string' || !input.question.trim() || input.question.length > 1000) {
      throw new Error('Choose a company and enter a question of up to 1,000 characters.');
    }
    passages ||= fetch('/data/research.json').then(r=>{if(!r.ok)throw new Error('Source summaries are unavailable.');return r.json();}).catch(error=>{passages=null;throw error;});
    const evidence = matchResearchPassages(input.ticker, input.question, await passages);
    options?.signal?.throwIfAborted();
    return {ticker:input.ticker,question:input.question,answer:evidence.length?'These primary-source excerpts may help with your question. They are historical source passages, not a generated financial conclusion. Open the linked original pages for the full context.':'The limited public source extracts do not establish an answer. Open the source library, or use the full GitHub application to index additional documents.',evidence,method:evidence.length?'extractive':'insufficient_evidence',limitations:['Public demo: only a compact selection of historical primary-source extracts is searched.','No AI model or live data feed is connected. Your monitoring preferences are saved only on this device.'],cached:false} as T;
  }
  const result = await store!(path,options);
  if (path.split('?')[0] === '/dashboard') return {...result as object, source_refresh: feed.status()} as T;
  return result as T;
}
