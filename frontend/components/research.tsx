"use client";
import { useEffect, useRef, useState } from "react";
import {
  ArrowDown,
  ArrowRight,
  BookOpen,
  Check,
  ChevronDown,
  ExternalLink,
  FileText,
  FlaskConical,
  Link2,
  Loader2,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  Target,
} from "lucide-react";
import {
  api,
  Candidate,
  Company,
  Financials,
  GuidanceItem,
  label,
  number,
  pct,
  Research,
  SourceDocument,
} from "@/lib/api";

const questions = [
  "What does the company do?",
  "How strong is cash conversion?",
  "What did management guide for growth?",
  "What risks does management highlight?",
];

export function ResearchWorkspace({
  initialTicker,
  initialTab = "overview",
  companies,
  onChanged,
}: {
  initialTicker: string;
  initialTab?: string;
  companies: Company[];
  onChanged: () => void;
}) {
  const [ticker, setTicker] = useState(initialTicker);
  const [search, setSearch] = useState(initialTicker);
  const [tab, setTab] = useState(initialTab);
  const [docs, setDocs] = useState<SourceDocument[]>([]);
  const [financials, setFinancials] = useState<Financials>({ rows: [] });
  const [guidance, setGuidance] = useState<GuidanceItem[]>([]);
  const [guidanceNote, setGuidanceNote] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<Research | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [importOpen, setImportOpen] = useState(false);
  const [importForm, setImportForm] = useState({
    url: "",
    title: "",
    period: "",
    kind: "annual_report",
  });
  const [generation, setGeneration] = useState(0);
  const [dataLoading, setDataLoading] = useState(true);
  const requestVersion = useRef(0);
  const company = companies.find((c) => c.ticker === ticker);
  const activeTicker = useRef(ticker);
  activeTicker.current = ticker;

  useEffect(() => {
    setTicker(initialTicker);
    setSearch(initialTicker);
  }, [initialTicker]);
  useEffect(() => setTab(initialTab), [initialTab]);
  useEffect(() => {
    let cancelled = false;
    setAnswer(null);
    setCandidates([]);
    setError("");
    setNotice("");
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

  async function discover() {
    const symbol = search.trim().toUpperCase().replace(/\.NS$/, "");
    if (!symbol) return;
    setBusy("discover");
    setError("");
    setNotice("");
    try {
      const result = await api<{
        company: Company;
        documents: Candidate[];
        message: string;
      }>(`/companies/${encodeURIComponent(symbol)}/discover`, {
        method: "POST",
      });
      onChanged();
      setTicker(result.company.ticker);
      setTimeout(() => {
        setCandidates(result.documents);
        setNotice(result.message);
      }, 0);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  function chooseSymbol(symbol: string) {
    setTicker(symbol);
    setSearch(symbol);
  }
  async function ask(value: string) {
    if (!value.trim() || busy) return;
    const version = ++requestVersion.current;
    setQuestion(value);
    setBusy("research");
    setError("");
    try {
      const result = await api<Research>("/research", {
        method: "POST",
        body: JSON.stringify({ ticker, question: value, use_ai: true }),
      });
      if (version === requestVersion.current) setAnswer(result);
    } catch (e) {
      if (version === requestVersion.current) setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  async function importDoc(candidate?: Candidate) {
    const input = candidate || importForm;
    const requestedTicker = ticker;
    setBusy("import");
    setError("");
    try {
      await api("/documents", {
        method: "POST",
        body: JSON.stringify({ ticker, ...input }),
      });
      if (activeTicker.current === requestedTicker) {
        setImportOpen(false);
        setGeneration((g) => g + 1);
        setNotice("Primary document indexed. You can now ask a question.");
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }

  return (
    <div className="research-workspace">
      <div className="page-heading research-heading">
        <div>
          <div className="eyebrow">THE RESEARCH DESK</div>
          <h1>
            Go beyond the headline<span>.</span>
          </h1>
          <p>Ask better questions. Follow every answer to its source.</p>
        </div>
        <span className="source-seal">
          <ShieldCheck size={15} /> Primary sources only
        </span>
      </div>
      <div className="research-search">
        <Search size={19} />
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (companies.some((c) => c.ticker === search.toUpperCase()))
              chooseSymbol(search.toUpperCase());
            else void discover();
          }}
        >
          <label className="sr-only" htmlFor="ticker-search">
            NSE company ticker
          </label>
          <input
            id="ticker-search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Enter any NSE ticker, e.g. INFY or M&M"
            maxLength={24}
          />
          <button className="btn primary" disabled={!!busy}>
            {busy === "discover" ? (
              <Loader2 className="spin" size={15} />
            ) : (
              <Search size={15} />
            )}{" "}
            Find company
          </button>
        </form>
      </div>
      <div className="company-pills">
        {["INFY", "TCS", "PERSISTENT", "WIPRO"].map((t) => (
          <button
            key={t}
            className={ticker === t ? "selected" : ""}
            onClick={() => chooseSymbol(t)}
          >
            {t}
            <ArrowRight size={12} />
          </button>
        ))}
        <span>Or research a ticker outside your portfolio</span>
      </div>
      <div className="company-strip">
        <div className={`company-logo logo-${ticker.length % 5}`}>
          {ticker.slice(0, 2)}
        </div>
        <div>
          <h2>{company?.name || ticker}</h2>
          <p>
            {ticker} <span>·</span> NSE <span>·</span>{" "}
            {company?.sector || "Verify with Discover"}
          </p>
        </div>
        <div className="document-count">
          <FileText size={15} />
          {docs.length} indexed documents
        </div>
      </div>
      <div className="research-tabs" role="tablist" aria-label="Research views">
        {[
          ["overview", "Research & evidence"],
          ["financials", "Financial snapshot"],
          ["guidance", "Promise vs. reality"],
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
      {notice && <div className="notice-banner">{notice}</div>}
      {dataLoading && (
        <div className="research-loading">
          <Loader2 className="spin" size={16} /> Loading the company source
          library…
        </div>
      )}
      {tab === "overview" && (
        <div className="research-grid">
          <section className="panel research-main">
            <div className="section-title">
              <h2>
                <Sparkles size={17} /> A question worth asking
              </h2>
              <span className="small-label">EVIDENCE FIRST</span>
            </div>
            <p className="section-description">
              Research the business, cash quality, outlook, or risks using
              company-issued documents.
            </p>
            <div className="question-chips">
              {questions.map((q) => (
                <button key={q} disabled={!!busy} onClick={() => void ask(q)}>
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
                  disabled={!!busy || question.trim().length < 4}
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
            {busy === "research" && (
              <div className="research-loading">
                <Loader2 size={19} className="spin" />
                <div>
                  Reading the source material
                  <span>
                    Retrieving relevant passages and checking citations
                  </span>
                </div>
              </div>
            )}
            {answer && (
              <div className="answer" aria-live="polite">
                <div className="answer-label">
                  <span>
                    <Sparkles size={13} />
                    {answer.method === "grounded_ai"
                      ? "SOURCE-GROUNDED GEMINI"
                      : answer.method === "extractive"
                        ? "EXTRACTIVE RESEARCH"
                        : "INSUFFICIENT EVIDENCE"}
                  </span>
                  {answer.cached && <span>Cached</span>}
                </div>
                <h3>{answer.question}</h3>
                <p className="answer-text">{answer.answer}</p>
                <div className="limitations">
                  {answer.limitations.map((l, i) => (
                    <p key={i}>{l}</p>
                  ))}
                </div>
                {answer.evidence.length > 0 && (
                  <>
                    <h4>
                      Evidence inspector{" "}
                      <span>{answer.evidence.length} passages</span>
                    </h4>
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
            {!answer && busy !== "research" && (
              <div className="research-empty">
                <BookOpen size={29} />
                <h3>The answer starts with the evidence.</h3>
                <p>
                  Choose a question above, or ask your own. Every passage keeps
                  its document, period, and page reference.
                </p>
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
                  No indexed documents. Discover sources or import a
                  company-issued document.
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
            <div className="research-note">
              <ShieldCheck size={21} />
              <h3>Show your working.</h3>
              <p>
                Company reports and earnings calls. Original dates. Page-level
                evidence. No broker notes or model memory as financial evidence.
              </p>
            </div>
          </aside>
        </div>
      )}
      {tab === "financials" && !dataLoading && (
        <section className="panel financial-panel">
          <div className="section-title">
            <div>
              <div className="eyebrow">THE NUMBERS, IN CONTEXT</div>
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
              <p className="method-note">{financials.note}</p>
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
              <h3>Numbers deserve a source check.</h3>
              <p>{financials.message}</p>
              <button className="btn" onClick={() => setTab("overview")}>
                Research the source documents
                <ArrowRight size={14} />
              </button>
            </div>
          )}
        </section>
      )}
      {tab === "guidance" && !dataLoading && (
        <section className="panel guidance-panel">
          <div className="section-title">
            <div>
              <div className="eyebrow">MANAGEMENT ACCOUNTABILITY</div>
              <h2>What was promised. What was delivered.</h2>
            </div>
            <Target size={24} />
          </div>
          <p className="section-description">
            Quantitative guidance, compared with reported outcomes on the same
            basis.
          </p>
          {guidance.length > 0 ? (
            <>
              <div className="guidance-outcome">
                <div>
                  <span>ACTUAL {guidance[0].target_period} RESULT</span>
                  <strong>
                    {guidance[0].actual.toFixed(1)}
                    <small>%</small>
                  </strong>
                  <p>{guidance[0].metric}</p>
                </div>
                <div className="guidance-outcome-copy">
                  <ShieldCheck size={22} />
                  <h3>One year. Four revisions. A complete picture.</h3>
                  <p>
                    Read each revision in context. Guidance narrowed during the
                    year; the final outcome can exceed the original range and
                    miss the latest one.
                  </p>
                </div>
              </div>
              <div className="guidance-timeline">
                {guidance.map((g, i) => (
                  <div className="guidance-row" key={i}>
                    <div className="timeline-dot">{i + 1}</div>
                    <div className="guidance-revision">
                      <b>{g.revision}</b>
                      <span>{g.statement_date}</span>
                    </div>
                    <div className="guidance-range">
                      <span>GUIDANCE</span>
                      <b>
                        {g.low}–{g.high}%
                      </b>
                      <div className="guidance-track">
                        <i
                          style={{
                            left: `${(g.low / 6) * 100}%`,
                            width: `${Math.max(((g.high - g.low) / 6) * 100, 2)}%`,
                          }}
                        />
                        <em style={{ left: `${(g.actual / 6) * 100}%` }} />
                      </div>
                    </div>
                    <div className="guidance-status">
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
                        {g.deviation_pp > 0 ? "+" : ""}
                        {g.deviation_pp.toFixed(1)} pp from range
                      </small>
                    </div>
                    <details className="guidance-evidence">
                      <summary>
                        <Link2 size={14} /> Evidence
                      </summary>
                      <p>{g.statement}</p>
                      <a
                        href={`${g.guidance_url}#page=${g.guidance_page}`}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Original call · p. {g.guidance_page}
                        <ExternalLink size={12} />
                      </a>
                      <a
                        href={`${g.actual_url}#page=${g.actual_page}`}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Reported result · p. {g.actual_page}
                        <ExternalLink size={12} />
                      </a>
                    </details>
                  </div>
                ))}
              </div>
              <p className="method-note">
                {guidanceNote} Deviation is in percentage points from the
                nearest guidance boundary, not relative percent. No credibility
                score is inferred.
              </p>
            </>
          ) : (
            <div className="empty-state">
              <Target size={30} />
              <h3>A promise needs two sources.</h3>
              <p>
                No reviewed guidance/result pair is indexed for {ticker}. Start
                with INFY to explore the four-revision historical example.
              </p>
              <button className="btn" onClick={() => chooseSymbol("INFY")}>
                Explore Infosys
                <ArrowRight size={14} />
              </button>
            </div>
          )}
        </section>
      )}
      {tab === "documents" && (
        <section className="panel library">
          <div className="section-title">
            <div>
              <div className="eyebrow">THE SOURCE OF TRUTH</div>
              <h2>Primary document library</h2>
            </div>
            <button className="btn" onClick={() => setImportOpen(!importOpen)}>
              <Link2 size={14} /> Import document
            </button>
          </div>
          <p className="section-description">
            Full source documents are indexed by page. Only issuer and exchange
            domains are accepted.
          </p>
          {importOpen && (
            <form
              className="import-form"
              onSubmit={(e) => {
                e.preventDefault();
                void importDoc();
              }}
            >
              <label>
                Primary source URL
                <input
                  type="url"
                  required
                  value={importForm.url}
                  placeholder="https://company.com/investors/report.pdf"
                  onChange={(e) =>
                    setImportForm({ ...importForm, url: e.target.value })
                  }
                />
              </label>
              <div className="form-grid">
                <label>
                  Document title
                  <input
                    required
                    minLength={3}
                    value={importForm.title}
                    onChange={(e) =>
                      setImportForm({ ...importForm, title: e.target.value })
                    }
                  />
                </label>
                <label>
                  Publication period
                  <input
                    required
                    minLength={2}
                    value={importForm.period}
                    placeholder="FY25"
                    onChange={(e) =>
                      setImportForm({ ...importForm, period: e.target.value })
                    }
                  />
                </label>
                <label>
                  Document type
                  <select
                    value={importForm.kind}
                    onChange={(e) =>
                      setImportForm({ ...importForm, kind: e.target.value })
                    }
                  >
                    <option value="annual_report">Annual report</option>
                    <option value="transcript">Earnings-call transcript</option>
                    <option value="results">Financial results</option>
                    <option value="investor_presentation">
                      Investor presentation
                    </option>
                  </select>
                </label>
              </div>
              <button className="btn primary" disabled={!!busy}>
                {busy === "import" ? (
                  <Loader2 className="spin" size={14} />
                ) : (
                  <ArrowRight size={14} />
                )}{" "}
                Download & index
              </button>
            </form>
          )}
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
                <small>
                  Retrieved {new Date(d.fetched_at).toLocaleDateString("en-IN")}
                </small>
              </div>
              <span className="verified-label">
                <ShieldCheck size={12} /> Primary source
              </span>
              <ExternalLink size={16} />
            </a>
          ))}
          {!docs.length && (
            <p className="muted">
              No indexed documents yet. Use Discover to find company-issued
              reports.
            </p>
          )}
          {candidates.length > 0 && (
            <>
              <h3 className="candidate-title">Discovered primary documents</h3>
              {candidates.map((c) => (
                <div className="candidate" key={c.url}>
                  <div>
                    <b>{c.title}</b>
                    <a href={c.url} target="_blank" rel="noreferrer">
                      Review source
                      <ExternalLink size={12} />
                    </a>
                  </div>
                  <button
                    className="btn"
                    disabled={!!busy}
                    onClick={() => void importDoc(c)}
                  >
                    Import
                    <ArrowRight size={13} />
                  </button>
                </div>
              ))}
            </>
          )}
          <button
            className="text-button discover-button"
            disabled={!!busy}
            onClick={() => void discover()}
          >
            {busy === "discover" ? (
              <Loader2 className="spin" size={14} />
            ) : (
              <Search size={14} />
            )}{" "}
            Discover annual reports & transcripts
          </button>
        </section>
      )}
    </div>
  );
}
