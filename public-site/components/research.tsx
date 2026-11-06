"use client";
import {Select} from "@/components/select";
import { useEffect, useRef, useState } from "react";
import {
  BarChart3,
  ArrowDown,
  ArrowRight,
  Check,
  ChevronDown,
  ExternalLink,
  FileText,
  FlaskConical,
  Loader2,
  Send,
  ShieldCheck,
  Sparkles,
  Target,
} from "lucide-react";
import {
  api,
  Company,
  CompanyDiscovery,
  Financials,
  GuidanceItem,
  label,
  number,
  pct,
  Research,
  SourceDocument,
  ApiError,
} from "@/lib/api";
import {CompanyLookup,CompanyMatch} from "./company-lookup";

const questions = [
  "What does the company do?",
  "How strong is cash conversion?",
  "What did management guide for growth?",
  "What risks does management highlight?",
];

export function ResearchWorkspace({
  initialTicker,
  initialTab = "overview",
  initialQuestion = "",
  initialDiscovery = null,
  companies,
  onChanged,
}: {
  initialTicker: string;
  initialTab?: string;
  initialQuestion?: string;
  initialDiscovery?: CompanyDiscovery|null;
  companies: Company[];
  onChanged: () => void;
}) {
  const [ticker, setTicker] = useState(initialTicker);
  const [tab, setTab] = useState(initialTab);
  const [docs, setDocs] = useState<SourceDocument[]>([]);
  const [financials, setFinancials] = useState<Financials>({ rows: [] });
  const [guidance, setGuidance] = useState<GuidanceItem[]>([]);
  const [guidanceNote, setGuidanceNote] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<Research | null>(null);
  const answerPanel = useRef<HTMLDivElement>(null);
  const [questionError, setQuestionError] = useState("");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [generation, setGeneration] = useState(0);
  const [dataLoading, setDataLoading] = useState(true);
  const requestVersion = useRef(0);
  const company = companies.find((c) => c.ticker === ticker);
  const activeTicker = useRef(ticker);
  const quarterRequest = useRef(0);
  const importPending=useRef(false);
  const loadedIssuer=useRef(ticker);
  const discovered=useRef<CompanyDiscovery|null>(initialDiscovery);
  const [selectedName,setSelectedName]=useState("");
  const answerNotes = answer?.evidence.length ? answer.limitations.filter(note =>
    !/^(Only the indexed historical documents|A model support review|The Gemini request|No Gemini key configured)/.test(note)
  ) : [];
  activeTicker.current = ticker;

  useEffect(() => {
    setTicker(initialTicker);
    discovered.current=initialDiscovery;
  }, [initialTicker]);
  useEffect(()=>setQuestion(initialQuestion),[initialQuestion,initialTicker]);
  useEffect(() => setTab(initialTab), [initialTab]);
  useEffect(() => {
    if (answer && answerPanel.current) {
      answerPanel.current.focus({ preventScroll: true });
      answerPanel.current.scrollIntoView({ block: "start" });
    }
  }, [answer]);
  useEffect(() => {
    let cancelled = false;
    quarterRequest.current++;
    setAnswer(null);
    setQuestionError("");
    const discovery=discovered.current?.company.ticker===ticker?discovered.current:null;
    setError("");
    if(discovery)setNotice(discovery.documents.length ? "" : discovery.message);
    else if(loadedIssuer.current!==ticker)setNotice("");
    loadedIssuer.current=ticker;
    setDocs([]);
    setFinancials({ rows: [] });
    setGuidance([]);
    setDataLoading(true);
    Promise.all([
      api<SourceDocument[]>(`/companies/${ticker}/documents`),
      api<Financials>(`/companies/${ticker}/financials`),
      api<{ items: GuidanceItem[]; note: string }>(
        `/companies/${ticker}/guidance`,
      ),
    ])
      .then(([d, f, g]) => {
        if (!cancelled) {
          setDocs(d);
          setFinancials(f);
          setGuidance(g.items);
          setGuidanceNote(g.note);
        }
      })
      .catch((e) => {
        if (!cancelled) setError(e.message);
      })
      .finally(() => {
        if (!cancelled) setDataLoading(false);
      });
    return () => {
      cancelled = true;
      requestVersion.current++;
    };
  }, [ticker, generation]);

  async function chooseQuarter(period: string) {
    const version=++quarterRequest.current;
    const issuer=ticker;
    setBusy("quarter");setError("");
    try {
      const result=await api<Financials>(`/companies/${ticker}/financials?period=${encodeURIComponent(period)}`);
      if(version===quarterRequest.current && issuer===activeTicker.current)setFinancials(result);
    } catch(e){if(version===quarterRequest.current)setError((e as Error).message);}
    finally{if(version===quarterRequest.current)setBusy("");}
  }

  function chooseSymbol(symbol: string) {
    setTicker(symbol);
    setQuestion("");
    setSelectedName("");
  }
  async function chooseCompany(match:CompanyMatch){
    setBusy("opening");setError("");
    try{
      if(!companies.some(c=>c.ticker===match.ticker)){
        const result=await api<CompanyDiscovery>(`/companies/${match.ticker}/discover`,{method:"POST"});
        discovered.current=result;onChanged();
      } else discovered.current=null;
      setSelectedName(match.name);setTicker(match.ticker);setQuestion("");setTab("documents");setGeneration(g=>g+1);
    }finally{setBusy("");}
  }
  async function ask(value: string) {
    if (!value.trim() || busy || dataLoading) return;
    if(!docs.length){setTab("documents");setNotice("Choose a company with reports in the demo library.");return;}
    const version = ++requestVersion.current;
    setQuestion(value);
    setBusy("research");
    setAnswer(null);
    setQuestionError("");
    setError("");
    try {
      const result = await api<Research>("/research", {
        method: "POST",
        body: JSON.stringify({ ticker, question: value, use_ai: true }),
      });
      if (version === requestVersion.current) setAnswer(result);
    } catch (e) {
      if (version === requestVersion.current) setQuestionError((e as Error).message);
    } finally {
      setBusy("");
    }
  }


  return (
    <div className="research-workspace">
      <div className="page-heading research-heading">
        <div>
          <h1>Research desk</h1>
        </div>
        <span className="source-seal">
          <ShieldCheck size={15} /> Primary sources only
        </span>
      </div>
      <div className="research-search name-first-search">
        <CompanyLookup companies={companies} disabled={!!busy} onSelect={chooseCompany}/>
      </div>
      {/* Verified company selection supplies a ticker to the existing APIs. */}
      <div className="company-pills">
        {["INFY", "TCS", "PERSISTENT", "WIPRO"].map((t) => (
          <button
            key={t}
            disabled={!!busy}
            className={ticker === t ? "selected" : ""}
            onClick={() => chooseSymbol(t)}
          >
            {t}
            <ArrowRight size={12} />
          </button>
        ))}
      </div>
      <div className="company-strip">
        <div className={`company-logo logo-${ticker.length % 5}`}>
          {ticker.slice(0, 2)}
        </div>
        <div>
          <h2>{company?.name || selectedName || discovered.current?.company.name || ticker}</h2>
          <p>
            {ticker} <span>·</span> NSE <span>·</span>{" "}
            {company?.sector || "Verify with Discover"}
          </p>
        </div>
        <div className="document-count">
          <FileText size={15} />
          {dataLoading?"Checking source library…":`${docs.length} source document${docs.length===1?"":"s"}`}
        </div>
      </div>
      <div className="research-tabs" role="tablist" aria-label="Research views">
        {[
          ["overview", "Research & evidence"],
          ["financials", "Financial snapshot"],
          ["guidance", "Promise Tracker"],
          ["documents", "Source library"],
        ].map(([id, title]) => (
          <button
            role="tab"
            aria-selected={tab === id}
            key={id}
            onClick={() => setTab(id)}
          >
            {id === "guidance" && <Target size={14} />} {title}
            {id === "guidance" && guidance.length > 0 && (
              <span className="tiny-tag">{guidance.length}</span>
            )}
          </button>
        ))}
      </div>
      {error && (
        <div className="error-banner" role="alert">
          {error}
        </div>
      )}
      {notice && <div className="notice-banner" role="status">{notice}</div>}
      {busy==="import"&&<div className="notice-banner" role="status"><Loader2 className="spin" size={16}/> Adding the document. Large reports may take a few minutes.</div>}
      {dataLoading && (
        <div className="research-loading">
          <Loader2 className="spin" size={16} /> Loading the company source
          library…
        </div>
      )}
      {initialQuestion&&ticker===initialTicker&&<div className="event-research-context"><ShieldCheck size={16}/><p><b>From your signal</b> {initialQuestion} Source evidence is required; a filing does not establish the cause of a price move.</p></div>}
      {tab === "overview" && (
        <div className="research-grid">
          <section className="panel research-main">
            <div className="section-title">
              <h2>
                <Sparkles size={17} /> Ask a question
              </h2>
            </div>
            <div className="question-chips">
              {questions.map((q) => (
                <button key={q} disabled={!!busy || dataLoading} onClick={() => void ask(q)}>
                  {q}
                  <ArrowRight size={13} />
                </button>
              ))}
            </div>
            <form
              className="question-box"
              onSubmit={(e) => {
                e.preventDefault();
                void ask(question);
              }}
            >
              <label className="sr-only" htmlFor="research-question">
                Research question
              </label>
              <textarea
                id="research-question"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder={`What would you like to understand about ${company?.name || ticker}?`}
                maxLength={1200}
                rows={3}
              />
              <div>
                <span>
                  <ShieldCheck size={12} /> Grounded in your source library
                </span>
                <button
                  className="btn primary"
                  disabled={!!busy || dataLoading || question.trim().length < 4}
                >
                  {busy === "research" ? (
                    <Loader2 size={15} className="spin" />
                  ) : (
                    <ArrowRight size={15} />
                  )}{" "}
                  Research
                </button>
              </div>
            </form>
            {questionError && <div className="error-banner" role="alert">{questionError}</div>}
            {busy === "research" && (
              <div className="research-loading" role="status">
                <Loader2 size={19} className="spin" />
                Reading company documents…
              </div>
            )}
            {answer && (
              <div className="answer" ref={answerPanel} tabIndex={-1} aria-label="Research answer" role="region">
                <div className="answer-label">
                  <span>
                    <Sparkles size={13} />
                    {answer.evidence.length ? "Company documents" : "No matching sources"}
                  </span>
                </div>
                <h3>{answer.question}</h3>
                <p className="answer-text">{answer.answer}</p>
                {answerNotes.length > 0 && <details className="reading-notes">
                  <summary>Answer notes</summary>
                  {answerNotes.map((note, i) => <p key={i}>{note}</p>)}
                </details>}
                {answer.evidence.length > 0 && (
                  <>
                    <h4>Sources</h4>
                    {answer.evidence.map((e) => (
                      <details
                        className="evidence"
                        key={e.id}
                        open={e.id === answer.evidence[0].id}
                      >
                        <summary>
                          <FileText size={15} />
                          <div>
                            <b>
                              [{e.id}] {e.title}
                            </b>
                            <span>
                              {e.period} · Page {e.page}
                            </span>
                          </div>
                          <ChevronDown size={14} />
                        </summary>
                        <blockquote>{e.excerpt}</blockquote>
                        <a href={e.url} target="_blank" rel="noreferrer">
                          Open primary document · page {e.page}
                          <ExternalLink size={12} />
                        </a>
                      </details>
                    ))}
                  </>
                )}
              </div>
            )}
          </section>
          <aside className="research-aside">
            <section className="panel source-panel">
              <div className="section-title">
                <h2>On the desk</h2>
                <span className="count-badge">{docs.length}</span>
              </div>
              {docs.length ? (
                docs.slice(0, 5).map((d) => (
                  <a
                    className="source-document"
                    href={d.source_url}
                    target="_blank"
                    rel="noreferrer"
                    key={d.id}
                  >
                    <FileText size={18} />
                    <div>
                      <b>{d.title}</b>
                      <span>
                        {d.period} · {d.page_count} pages
                      </span>
                    </div>
                    <ExternalLink size={12} />
                  </a>
                ))
              ) : (
                <p className="muted">
                  The demo library has no reports for this company.
                </p>
              )}
              <button
                className="text-button"
                onClick={() => setTab("documents")}
              >
                Explore source library
                <ArrowRight size={14} />
              </button>
            </section>
          </aside>
        </div>
      )}
      {tab === "financials" && !dataLoading && (
        <section className="panel financial-panel">
          <div className="section-title">
            <div>
              <h2>Quarterly financial snapshot</h2>
            </div>
            <span className="small-label">
              {financials.currency || "SOURCE REVIEW REQUIRED"}
            </span>
          </div>
          {financials.rows.length > 0 ? (
            <>
              <p className="section-description">
                {financials.basis} · Historical, reviewed source figures.
                Percentages calculated in Python.
              </p>
              {!!financials.periods?.length && <label className="quarter-select">Reviewed quarter
                <Select aria-label="Reviewed quarter" value={financials.current_period} disabled={busy==="quarter"} onChange={e=>void chooseQuarter(e.target.value)}>
                  {financials.periods.map(period=><option key={period} value={period}>{period}</option>)}
                </Select>
                <small>{financials.periods.length} reviewed quarters · fiscal-year ending year</small>
              </label>}
              {!!financials.review_flags?.length && <aside className="review-flags" aria-label="Accounting review notes"><b>Read these numbers in context</b>{financials.review_flags.map(flag=><p key={flag}>{flag}</p>)}</aside>}
              <div className="phone-financials">
                {financials.rows.map((r) => (
                  <article key={r.metric}>
                    <div>
                      <h3>
                        {r.metric === "revenue"
                          ? "Revenue"
                          : r.metric.toUpperCase()}
                      </h3>
                      <span>{financials.current_period}</span>
                    </div>
                    <strong>
                      {number(r.current)}
                      <small>{financials.currency}</small>
                    </strong>
                    {r.current === null && (
                      <p>Not reliably available in the reviewed source.</p>
                    )}
                    <div className="financial-comparisons">
                      <div>
                        <span>vs. {financials.previous_period}</span>
                        <b>{number(r.previous)}</b>
                        <em
                          className={
                            (r.qoq || 0) >= 0 ? "positive" : "negative"
                          }
                        >
                          {pct(r.qoq)} QoQ
                        </em>
                      </div>
                      <div>
                        <span>vs. {financials.last_year_period}</span>
                        <b>{number(r.last_year)}</b>
                        <em
                          className={
                            (r.yoy || 0) >= 0 ? "positive" : "negative"
                          }
                        >
                          {pct(r.yoy)} YoY
                        </em>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
              <div className="table-scroll financial-desktop-table">
                <table>
                  <thead>
                    <tr>
                      <th>Metric</th>
                      <th>{financials.current_period}</th>
                      <th>{financials.previous_period}</th>
                      <th>{financials.last_year_period}</th>
                      <th>QoQ</th>
                      <th>YoY</th>
                    </tr>
                  </thead>
                  <tbody>
                    {financials.rows.map((r) => (
                      <tr key={r.metric}>
                        <td>
                          {r.metric === "revenue"
                            ? "Revenue"
                            : r.metric.toUpperCase()}
                          {r.metric === "ebitda" && r.current === null && (
                            <small>Not reliably available</small>
                          )}
                        </td>
                        <td className="strong">{number(r.current)}</td>
                        <td>{number(r.previous)}</td>
                        <td>{number(r.last_year)}</td>
                        <td
                          className={
                            (r.qoq || 0) >= 0 ? "positive" : "negative"
                          }
                        >
                          {pct(r.qoq)}
                        </td>
                        <td
                          className={
                            (r.yoy || 0) >= 0 ? "positive" : "negative"
                          }
                        >
                          {pct(r.yoy)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <details className="reading-notes"><summary>Calculation notes</summary><p>{financials.note}</p></details>
              <div className="financial-source-links">
                {financials.sources?.map((s, i) => (
                  <a
                    href={`${s.source_url}#page=${s.page}`}
                    target="_blank"
                    rel="noreferrer"
                    key={i}
                  >
                    <FileText size={13} />
                    {s.period} · page {s.page}
                    <ExternalLink size={12} />
                  </a>
                ))}
              </div>
              <div className="notice-banner">
                Operating profit is not EBITDA. Unreported values remain
                unavailable.
              </div>
            </>
          ) : (
            <div className="empty-state">
              <FileText size={28} />
              <h3>No reviewed financials</h3>
              <p>{financials.message}</p>
              <button className="btn" onClick={() => setTab("overview")}>
                Research the source documents
                <ArrowRight size={14} />
              </button>
            </div>
          )}
        </section>
      )}
      {tab === "guidance" && !dataLoading && !error && (
        <GuidanceComparison ticker={ticker} guidance={guidance} guidanceNote={guidanceNote} onExploreInfosys={() => chooseSymbol("INFY")} />
      )}
      {tab === "documents" && (
        <section className="panel library">
          <div className="section-title">
            <div>
              <h2>Primary document library</h2>
            </div>
            <div className="library-actions">
              {docs.length > 0 && <button className="btn primary" disabled={!!busy} onClick={() => setTab("overview")}>
                <Sparkles size={14} /> Ask a question
              </button>}
            </div>
          </div>
          {docs.map((d) => (
            <a
              className="library-row"
              key={d.id}
              href={d.source_url}
              target="_blank"
              rel="noreferrer"
            >
              <span className="file-tile">
                <FileText size={20} />
              </span>
              <div>
                <h3>{d.title}</h3>
                <p>
                  {label(d.kind)} · {d.period} · {d.page_count} pages
                </p>
              </div>
              <span className="verified-label">
                <ShieldCheck size={12} /> Primary source
              </span>
              <ExternalLink size={16} />
            </a>
          ))}
          {!docs.length && (
            <p className="muted">
              The demo library has no reports for this company.
            </p>
          )}
        </section>
      )}
    </div>
  );
}

type GuidanceResponse = { items: GuidanceItem[]; note: string };

export function PromiseTracker({companies, onOpenResearch}: {companies: Company[]; onOpenResearch: (ticker: string) => void}) {
  const [reviewedIssuers, setReviewedIssuers] = useState<Company[] | null>(null);
  const [selectedTicker, setSelectedTicker] = useState("");
  const [comparison, setComparison] = useState<GuidanceResponse | null>(null);
  const [error, setError] = useState("");
  const reviewedTickers = new Set(reviewedIssuers?.map(company => company.ticker));
  const otherIssuers = companies.filter(company => !reviewedTickers.has(company.ticker));
  const ticker = selectedTicker || (reviewedIssuers && (
    reviewedIssuers[0]?.ticker ?? otherIssuers[0]?.ticker
  )) || "";

  useEffect(() => {
    const request = new AbortController();
    api<Company[]>("/companies?has_guidance=true", { signal: request.signal })
      .then(issuers => { if (!request.signal.aborted) setReviewedIssuers(issuers); })
      .catch(e => { if (!request.signal.aborted) setError(e.message); });
    return () => request.abort();
  }, [companies]);

  useEffect(() => {
    if (!ticker) return;
    const request = new AbortController();
    api<GuidanceResponse>(`/companies/${encodeURIComponent(ticker)}/guidance`, { signal: request.signal })
      .then(data => { if (!request.signal.aborted) setComparison(data); })
      .catch(e => { if (!request.signal.aborted) setError(e.message); });
    return () => request.abort();
  }, [ticker, companies]);

  return (
    <div className="research-workspace promise-tracker">
      <div className="page-heading research-heading">
        <div><h1>Promise Tracker</h1></div>
        <span className="source-seal"><ShieldCheck size={15} /> Primary sources only</span>
      </div>
      <p className="section-description">Reviewed guidance and results. New disclosures appear after source review.</p>
      {reviewedIssuers && !!ticker && <div className="promise-tracker-controls">
        <label className="field-label">
          Company
          <Select aria-label="Promise Tracker company" value={ticker} onChange={event => {
            if (event.target.value === ticker) return;
            setError("");
            setComparison(null);
            setSelectedTicker(event.target.value);
          }}>
            {reviewedIssuers.length > 0 && <optgroup label="Reviewed guidance">
              {reviewedIssuers.map(company => <option key={company.ticker} value={company.ticker}>{company.name} ({company.ticker})</option>)}
            </optgroup>}
            {otherIssuers.length > 0 && <optgroup label="No reviewed guidance yet">
              {otherIssuers.map(company => <option key={company.ticker} value={company.ticker}>{company.name} ({company.ticker})</option>)}
            </optgroup>}
          </Select>
        </label>
        <button className="btn" onClick={() => onOpenResearch(ticker)}>Open source library <ArrowRight size={14} /></button>
      </div>}
      {error ? <div className="error-banner" role="alert">{error}</div> :
        reviewedIssuers && !ticker ? <section className="panel empty-state"><Target size={30} /><h2>No companies available</h2><p>Add an NSE company from your watchlist to get started.</p></section> :
        comparison ? <GuidanceComparison ticker={ticker} guidance={comparison.items} guidanceNote={comparison.note} /> :
        <div className="research-loading" role="status"><Loader2 className="spin" size={16} /> Loading reviewed guidance…</div>}
    </div>
  );
}

function GuidanceComparison({
  ticker, guidance, guidanceNote, onExploreInfosys,
}: {
  ticker: string;
  guidance: GuidanceItem[];
  guidanceNote: string;
  onExploreInfosys?: () => void;
}) {
  const targetCount = new Set(guidance.map(item => JSON.stringify([item.target_period, item.metric, item.basis, item.unit]))).size;
  const timeline = targetCount > 1 ? [...guidance].sort((a,b)=>b.statement_date.localeCompare(a.statement_date)) : guidance;
  return (
  <section className="panel guidance-panel">
    <div className="section-title">
      <div>
        <h2>Guidance vs. results</h2>
      </div>
      <Target size={24} />
    </div>
    {guidance.length > 0 ? (
      <>
        <div className="guidance-outcome">
          <div>
            <span>{targetCount===1?`ACTUAL ${guidance[0].target_period} RESULT`:"DISTINCT TARGET PERIODS"}</span>
            <strong>
              {targetCount===1 ? (guidance[0].actual===null?"Pending":guidance[0].actual.toFixed(1)) : targetCount}
            {targetCount > 1 && <small>targets</small>}
            {targetCount === 1 && guidance[0].actual !== null && <small>{guidance[0].unit === "percent" ? "%" : guidance[0].unit}</small>}
            </strong>
            <p>{guidance[0].metric}</p>
          </div>
          <div className="guidance-outcome-copy">
            <ShieldCheck size={22} />
            <h3>{targetCount===1 ? (guidance.length===1 ? "Reviewed comparison" : "Guidance revisions") : "Guidance outcomes"}</h3>
            <p>
              {targetCount===1 && guidance.length>1 ? "All revisions refer to the same target period." : "Compared by matching period, metric and currency."}
            </p>
          </div>
        </div>
        <div className="guidance-timeline">
          {timeline.map((g, i) => (
            <details className="guidance-card" key={`${g.guidance_url}-${g.target_period}-${g.metric}-${i}`}>
            <summary className="guidance-row">
              <span className="timeline-dot" aria-hidden="true">{i + 1}</span>
              <span className="guidance-revision">
                <b>{g.revision}</b>
                <span>{g.statement_date}</span>
                <small>Target: {g.target_period}</small>
              </span>
              <span className="guidance-range">
                <span>GUIDANCE</span>
                <b>
                {g.low}–{g.high}{g.unit === "percent" ? "%" : ` ${g.unit}`}
                </b>
                <span className="guidance-track" aria-hidden="true">
                  <i
                    style={{
                      left: `${((g.low-Math.min(g.low,g.actual??0,0)+0.5)/(Math.max(g.high,g.actual??0,0)-Math.min(g.low,g.actual??0,0)+1))*100}%`,
                      width: `${Math.max(((g.high-g.low)/(Math.max(g.high,g.actual??0,0)-Math.min(g.low,g.actual??0,0)+1))*100,2)}%`,
                    }}
                  />
                  {g.actual!==null && <em style={{left:`${((g.actual-Math.min(g.low,g.actual,0)+0.5)/(Math.max(g.high,g.actual,0)-Math.min(g.low,g.actual,0)+1))*100}%`}} />}
                </span>
              <small>{g.actual===null?"Actual: pending":`Actual: ${g.actual.toFixed(1)}${g.unit === "percent" ? "%" : ` ${g.unit}`}`}</small>
              </span>
              <span className="guidance-status">
                <span className={`outcome ${g.status}`}>
                  {g.status === "achieved" ? (
                    <Check size={12} />
                  ) : g.status === "missed" ? (
                    <ArrowDown size={12} />
                  ) : (
                    <ArrowRight size={12} />
                  )}{" "}
                  {label(g.status)}
                </span>
                <small>
                  {g.deviation_pp===null?"Awaiting reported outcome":`${g.deviation_pp>0?"+":""}${g.deviation_pp.toFixed(1)} pp from range`}
                </small>
              </span>
              <span className="guidance-expand" aria-hidden="true"><ChevronDown size={17} /></span>
            </summary>
              <div className="guidance-sources">
                <p>{g.statement}</p>
                {g.basis && <p>{g.basis}</p>}
                <div className="guidance-source-links">
                  <a className="guidance-source original" href={`${g.guidance_url}#page=${g.guidance_page}`} target="_blank" rel="noreferrer">
                    <FileText size={19} aria-hidden="true" />
                    <span><b>Original guidance</b><small>Open PDF · Page {g.guidance_page}</small></span>
                    <ExternalLink size={15} aria-hidden="true" />
                  </a>
                  {g.actual_url ? (
                    <a className="guidance-source reported" href={g.actual_page ? `${g.actual_url}#page=${g.actual_page}` : g.actual_url} target="_blank" rel="noreferrer">
                      <BarChart3 size={19} aria-hidden="true" />
                      <span><b>Reported result</b><small>Open PDF{g.actual_page ? ` · Page ${g.actual_page}` : ""}</small></span>
                      <ExternalLink size={15} aria-hidden="true" />
                    </a>
                  ) : (
                    <div className="guidance-source pending">
                      <BarChart3 size={19} aria-hidden="true" />
                      <span><b>Reported result</b><small>Awaiting results</small></span>
                    </div>
                  )}
                </div>
              </div>
            </details>
          ))}
        </div>
        <details className="reading-notes"><summary>How comparisons work</summary><p>
          {guidanceNote} Deviation is in percentage points from the
          nearest guidance boundary, not relative percent. No credibility
          score is inferred.
        </p></details>
      </>
    ) : (
      <div className="empty-state">
        <Target size={30} />
        <h3>No matched guidance</h3>
        <p>
          No reviewed guidance or results are indexed for {ticker}.
        </p>
        {onExploreInfosys && ticker !== "INFY" && <button className="btn" onClick={onExploreInfosys}>
          Explore Infosys
          <ArrowRight size={14} />
        </button>}
      </div>
    )}
  </section>
  );
}
