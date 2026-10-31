"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  Activity,
  ArrowRight,
  ArrowUpRight,
  Bell,
  Bookmark,
  BookOpen,
  Check,
  ChevronDown,
  ChevronRight,
  CircleHelp,
  Clock3,
  ExternalLink,
  FileText,
  FlaskConical,
  LayoutDashboard,
  ListFilter,
  Loader2,
  Menu,
  Plus,
  Radar,
  RefreshCw,
  Search,
  Settings2,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Target,
  TrendingUp,
  X,
} from "lucide-react";
import {
  api,
  Alert,
  Company,
  Dashboard,
  Filing,
  label,
  Mode,
  money,
  pct,
  Prefs,
  shortDate,
  SyncRun,
} from "@/lib/api";
import { PriceChart, Sparkline } from "@/components/charts";
import { ResearchWorkspace } from "@/components/research";
import {
  CompanyDrawer,
  CompanySearch,
  MarketExplorer,
} from "@/components/market-explorer";

type View = "home" | "signals" | "research" | "watchlist";
const navigation = [
  { id: "home" as View, title: "Overview", icon: LayoutDashboard },
  { id: "signals" as View, title: "Signals & alerts", icon: Radar },
  { id: "research" as View, title: "Research desk", icon: BookOpen },
  { id: "watchlist" as View, title: "My watchlist", icon: Activity },
];
const filterCategories = [
  "results",
  "management_change",
  "M&A",
  "litigation",
  "fund_raise",
  "credit_rating",
  "dividend",
  "capex",
  "earnings_call",
  "press_release",
  "unclassified",
];

function CompanyMark({ ticker }: { ticker: string }) {
  return (
    <span className={`company-logo logo-${ticker.length % 5}`}>
      {ticker.slice(0, 2)}
    </span>
  );
}

function SignalCard({
  filing,
  onResearch,
  saved,
  onSave,
}: {
  filing: Filing;
  onResearch: (t: string) => void;
  saved: boolean;
  onSave: (filing: Filing) => void;
}) {
  const [open, setOpen] = useState(false);
  return (
    <article className={`signal-card priority-${filing.priority}`}>
      <div className="signal-meta">
        <CompanyMark ticker={filing.ticker} />
        <strong>{filing.ticker}</strong>
        <span className="meta-dot">·</span>
        <span>{label(filing.category)}</span>
        <span className="signal-time">
          {shortDate(filing.published_at)} ·{" "}
          {new Date(filing.published_at).toLocaleTimeString("en-IN", {
            hour: "2-digit",
            minute: "2-digit",
            hour12: false,
            timeZone: "Asia/Kolkata",
          })}{" "}
          IST
        </span>
      </div>
      <div className="signal-headline">
        <h3>{filing.title}</h3>
        <span className={`priority-pill ${filing.priority}`}>
          <i />
          {label(filing.priority)}
        </span>
      </div>
      <p className="signal-summary">{filing.summary}</p>
      <div className="why-matters">
        <Sparkles size={13} />
        <p>
          <b>Why it matters</b> {filing.why_matters}
        </p>
      </div>
      <div className="signal-footer">
        <button
          className="text-button subtle"
          onClick={() => setOpen(!open)}
          aria-expanded={open}
        >
          <ListFilter size={13} />
          {open ? "Hide reasoning" : "See the reasoning"}
          <ChevronDown size={12} className={open ? "rotate" : ""} />
        </button>
        <div>
          <button
            className={`save-signal ${saved ? "saved" : ""}`}
            aria-label={`${saved ? "Unsave" : "Save"} ${filing.ticker} signal`}
            aria-pressed={saved}
            onClick={() => onSave(filing)}
          >
            <Bookmark size={14} fill={saved ? "currentColor" : "none"} />
          </button>
          {filing.mode === "demo" ? (
            <span className="fixture-label">
              <FlaskConical size={11} /> Simulated disclosure
            </span>
          ) : (
            filing.source_url && (
              <a
                href={filing.source_url}
                target="_blank"
                rel="noreferrer"
                className="filing-link"
              >
                Original filing
                <ExternalLink size={12} />
              </a>
            )
          )}
          <button
            aria-label={`Research ${filing.ticker}`}
            className="signal-research"
            onClick={() => onResearch(filing.ticker)}
          >
            <ArrowUpRight size={16} />
          </button>
        </div>
      </div>
      {open && (
        <div className="signal-reasoning">
          <b>
            Priority: {filing.score}/100 · {label(filing.priority)}
          </b>
          <ul>
            {filing.factors.map((f, i) => (
              <li key={i}>{f}</li>
            ))}
          </ul>
          <small>
            {filing.analysis_method}. A priority score measures review urgency,
            not expected stock performance.
          </small>
        </div>
      )}
    </article>
  );
}

function Preferences({
  initial,
  companies,
  onClose,
  onSave,
}: {
  initial: Prefs;
  companies: Company[];
  onClose: () => void;
  onSave: () => void;
}) {
  const [prefs, setPrefs] = useState(initial);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const dialog = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement;
    const element = dialog.current;
    element?.querySelector<HTMLButtonElement>("button")?.focus();
    const handle = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "Tab" && element) {
        const els = element.querySelectorAll<HTMLElement>(
          "button:not(:disabled),input,select",
        );
        const first = els[0],
          last = els[els.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener("keydown", handle);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", handle);
      document.body.style.overflow = "";
      previous?.focus();
    };
  }, [onClose]);
  async function save(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await api("/preferences", { method: "PUT", body: JSON.stringify(prefs) });
      onSave();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  }
  function toggle(key: "companies" | "categories", value: string) {
    setPrefs((p) => ({
      ...p,
      [key]: p[key].includes(value)
        ? p[key].filter((x) => x !== value)
        : [...p[key], value],
    }));
  }
  return (
    <div
      className="modal-backdrop"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="settings-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="settings-title"
        ref={dialog}
      >
        <div className="dialog-heading">
          <div>
            <div className="eyebrow">MAKE IT YOUR SIGNAL</div>
            <h2 id="settings-title">Monitoring preferences</h2>
          </div>
          <button
            className="icon-button"
            aria-label="Close preferences"
            onClick={onClose}
          >
            <X size={19} />
          </button>
        </div>
        <p className="section-description">
          You decide what unusual means. FINN watches completed trading
          sessions.
        </p>
        <form onSubmit={save}>
          <label className="setting-input">
            Daily price move{" "}
            <span>Alert when the absolute change reaches this threshold.</span>
            <div>
              <input
                type="number"
                min="0.1"
                max="50"
                step="0.1"
                required
                value={prefs.price_threshold}
                onChange={(e) =>
                  setPrefs({
                    ...prefs,
                    price_threshold: Number(e.target.value),
                  })
                }
              />
              <b>%</b>
            </div>
          </label>
          <label className="setting-input">
            Unusual volume{" "}
            <span>
              Compared with the mean of prior sessions, excluding today.
            </span>
            <div>
              <input
                type="number"
                min="1.1"
                max="20"
                step="0.1"
                required
                value={prefs.volume_multiplier}
                onChange={(e) =>
                  setPrefs({
                    ...prefs,
                    volume_multiplier: Number(e.target.value),
                  })
                }
              />
              <b>×</b>
            </div>
          </label>
          <label className="setting-input">
            Volume lookback{" "}
            <span>
              Minimum number of complete historical sessions required.
            </span>
            <select
              value={prefs.lookback}
              onChange={(e) =>
                setPrefs({ ...prefs, lookback: Number(e.target.value) })
              }
            >
              {[5, 10, 20, 30, 60].map((n) => (
                <option key={n} value={n}>
                  {n} trading sessions
                </option>
              ))}
            </select>
          </label>
          <fieldset>
            <legend>Companies to monitor</legend>
            <p>None selected means all watched companies.</p>
            <div className="setting-chips">
              {companies
                .filter((c) => c.watched)
                .map((c) => (
                  <button
                    key={c.ticker}
                    type="button"
                    className={
                      prefs.companies.includes(c.ticker) ? "active" : ""
                    }
                    onClick={() => toggle("companies", c.ticker)}
                  >
                    {prefs.companies.includes(c.ticker) && <Check size={11} />}{" "}
                    {c.ticker}
                  </button>
                ))}
            </div>
          </fieldset>
          <fieldset>
            <legend>Announcement interests</legend>
            <p>
              Highlights matching material filings. None selected means all
              categories.
            </p>
            <div className="setting-chips">
              {(prefs.available_categories || filterCategories).map((c) => (
                <button
                  key={c}
                  type="button"
                  className={prefs.categories.includes(c) ? "active" : ""}
                  onClick={() => toggle("categories", c)}
                >
                  {label(c)}
                </button>
              ))}
            </div>
          </fieldset>
          {error && (
            <div className="error-banner" role="alert">
              {error}
            </div>
          )}
          <div className="dialog-footer">
            <span>
              <Clock3 size={13} /> End-of-day monitoring
            </span>
            <button className="btn primary" disabled={saving}>
              {saving ? (
                <Loader2 size={15} className="spin" />
              ) : (
                <Check size={15} />
              )}{" "}
              Save preferences
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function Home() {
  const [view, setView] = useState<View>("home");
  const [mode, setMode] = useState<Mode>("demo");
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [filings, setFilings] = useState<Filing[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [prefs, setPrefs] = useState<Prefs | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [windowValue, setWindowValue] = useState("24h");
  const [filterTicker, setFilterTicker] = useState("");
  const [category, setCategory] = useState("");
  const [priority, setPriority] = useState("");
  const [routine, setRoutine] = useState(false);
  const [routineCount, setRoutineCount] = useState(0);
  const [customStart, setCustomStart] = useState("2026-10-01");
  const [customEnd, setCustomEnd] = useState("2026-10-30");
  const [researchTicker, setResearchTicker] = useState("INFY");
  const [researchTab, setResearchTab] = useState("overview");
  const [chartTicker, setChartTicker] = useState("RELIANCE");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [sync, setSync] = useState<SyncRun | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [generation, setGeneration] = useState(0);
  const [mobileNav, setMobileNav] = useState(false);
  const [sourceDetails, setSourceDetails] = useState(false);
  const [watchSearch, setWatchSearch] = useState("");
  const [watchSector, setWatchSector] = useState("");
  const [watchSort, setWatchSort] = useState("ticker");
  const [savedSignals, setSavedSignals] = useState<Filing[]>([]);
  const [savedOnly, setSavedOnly] = useState(false);
  const [selectedCompany, setSelectedCompany] = useState<string | null>(null);
  const [toast, setToast] = useState("");
  const closeCompany = useCallback(() => setSelectedCompany(null), []);
  const reload = useCallback(() => setGeneration((g) => g + 1), []);
  const closeSettings = useCallback(() => setSettingsOpen(false), []);

  useEffect(() => {
    try {
      const stored = JSON.parse(
        localStorage.getItem("finn.saved-signals.v1") || "[]",
      );
      if (Array.isArray(stored))
        setSavedSignals(
          stored.filter(
            (f) =>
              f &&
              Number.isFinite(f.id) &&
              typeof f.title === "string" &&
              ["demo", "sourced"].includes(f.mode),
          ),
        );
    } catch {
      /* A storage restriction must not prevent opening the workspace. */
    }
  }, []);
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(""), 3500);
    return () => clearTimeout(timer);
  }, [toast]);
  useEffect(() => setSelectedCompany(null), [mode]);
  function toggleSaved(filing: Filing) {
    const exists = savedSignals.some(
      (f) => f.id === filing.id && f.mode === filing.mode,
    );
    const next = exists
      ? savedSignals.filter(
          (f) => !(f.id === filing.id && f.mode === filing.mode),
        )
      : [filing, ...savedSignals];
    setSavedSignals(next);
    try {
      localStorage.setItem("finn.saved-signals.v1", JSON.stringify(next));
      setToast(
        exists ? "Removed from saved signals" : "Signal saved for later",
      );
    } catch {
      setToast("Saved for this session. Browser storage is unavailable.");
    }
  }

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    Promise.all([
      api<Dashboard>(`/dashboard?mode=${mode}`),
      api<Company[]>("/companies"),
      api<Alert[]>(`/alerts?mode=${mode}`),
      api<Prefs>("/preferences"),
    ])
      .then(([d, c, a, p]) => {
        if (!cancelled) {
          setDashboard(d);
          setCompanies(c);
          setAlerts(a);
          setPrefs(p);
          if (d.last_sync) setSync(d.last_sync);
        }
      })
      .catch((e) => {
        if (!cancelled) {
          setError(e.message);
          setDashboard(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [mode, generation]);
  useEffect(() => {
    let cancelled = false;
    const params = new URLSearchParams({
      mode,
      window: windowValue,
      include_routine: String(routine),
    });
    if (filterTicker) params.set("ticker", filterTicker);
    if (category) params.set("category", category);
    if (priority) params.set("priority", priority);
    if (windowValue === "custom") {
      params.set("start", `${customStart}T00:00:00+05:30`);
      params.set("end", `${customEnd}T23:59:59+05:30`);
    }
    api<{ items: Filing[]; routine_count: number }>(`/announcements?${params}`)
      .then((data) => {
        if (!cancelled) {
          setFilings(data.items);
          setRoutineCount(data.routine_count);
        }
      })
      .catch((e) => {
        if (!cancelled) setError(e.message);
      });
    return () => {
      cancelled = true;
    };
  }, [
    mode,
    windowValue,
    filterTicker,
    category,
    priority,
    routine,
    customStart,
    customEnd,
    generation,
  ]);
  useEffect(() => {
    if (!refreshing || !sync?.id) return;
    const timer = setInterval(async () => {
      try {
        const result = await api<SyncRun>(`/sync/${sync.id}`);
        setSync(result);
        if (result.completed_at) {
          setRefreshing(false);
          reload();
        }
      } catch (e) {
        setError((e as Error).message);
        setRefreshing(false);
      }
    }, 2500);
    return () => clearInterval(timer);
  }, [refreshing, sync?.id, reload]);
  async function refresh() {
    setRefreshing(true);
    setError("");
    try {
      const result = await api<{ id: number }>("/sync", { method: "POST" });
      setSync({
        id: result.id,
        started_at: new Date().toISOString(),
        completed_at: null,
        result: { status: "queued" },
      });
    } catch (e) {
      setError((e as Error).message);
      setRefreshing(false);
    }
  }
  function navigate(id: View) {
    setView(id);
    setMobileNav(false);
    setSavedOnly(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
  function research(ticker: string, tab = "overview") {
    setResearchTicker(ticker);
    setResearchTab(tab);
    navigate("research");
  }
  async function toggleWatch(c: Company) {
    try {
      await api(`/companies/${c.ticker}`, {
        method: "PATCH",
        body: JSON.stringify({ watched: !c.watched }),
      });
      reload();
    } catch (e) {
      setError((e as Error).message);
    }
  }
  const chartQuote =
    dashboard?.companies.find((q) => q.ticker === chartTicker) ||
    dashboard?.companies[0];
  const stats = dashboard?.stats;
  const interestFilings = filings.filter(
    (f) =>
      f.priority !== "low" &&
      (!prefs?.categories.length || prefs.categories.includes(f.category)) &&
      (!prefs?.companies.length || prefs.companies.includes(f.ticker)),
  );
  const marketAlerts = alerts;
  const feedItems = savedOnly
    ? savedSignals.filter(
        (f) =>
          f.mode === mode &&
          (!filterTicker || f.ticker === filterTicker) &&
          (!category || f.category === category) &&
          (!priority || f.priority === priority),
      )
    : filings;
  const visibleFilings =
    view === "home" && !routine ? feedItems.slice(0, 4) : feedItems;
  const watchlist = companies
    .filter(
      (c) =>
        (!watchSector || c.sector === watchSector) &&
        (!watchSearch ||
          `${c.ticker} ${c.name} ${c.sector}`
            .toLowerCase()
            .includes(watchSearch.toLowerCase())),
    )
    .sort((a, b) => {
      const qa = dashboard?.companies.find((q) => q.ticker === a.ticker),
        qb = dashboard?.companies.find((q) => q.ticker === b.ticker);
      if (watchSort === "gainers")
        return (qb?.change_pct ?? -Infinity) - (qa?.change_pct ?? -Infinity);
      if (watchSort === "decliners")
        return (qa?.change_pct ?? Infinity) - (qb?.change_pct ?? Infinity);
      if (watchSort === "volume")
        return (
          (qb?.volume_ratio ?? -Infinity) - (qa?.volume_ratio ?? -Infinity)
        );
      return a.ticker.localeCompare(b.ticker);
    });
  const selectedQuote = dashboard?.companies.find(
    (q) => q.ticker === selectedCompany,
  );
  function focusSignals(kind: "high" | "routine" | "market") {
    navigate("signals");
    setPriority(kind === "high" ? "high" : "");
    setRoutine(kind === "routine");
    setFilterTicker("");
    setCategory("");
    if (kind === "market")
      requestAnimationFrame(() =>
        document
          .querySelector(".market-alerts")
          ?.scrollIntoView({ behavior: "smooth", block: "start" }),
      );
  }
  const syncErrors = Object.values(sync?.result.prices || {}).filter(
    (p) => !p.ok,
  );
  const sourcedLabel = mode === "demo" ? "Demo replay" : "Sourced data";

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <aside className={`sidebar ${mobileNav ? "mobile-open" : ""}`}>
        <div className="brand" aria-label="FINN">
          <div className="brand-symbol">
            <i />
            <i />
            <i />
          </div>
          <span>
            finn<span className="brand-dot">.</span>
          </span>
        </div>
        <div className="workspace-label">
          <span className="workspace-initial">P</span>
          <div>
            Personal workspace<small>INVESTMENT INTELLIGENCE</small>
          </div>
          <ChevronDown size={13} />
        </div>
        <div className="nav-section-label">YOUR WORKSPACE</div>
        <nav aria-label="Main navigation">
          {navigation.map((item) => (
            <button
              key={item.id}
              className={view === item.id ? "active" : ""}
              onClick={() => navigate(item.id)}
            >
              <item.icon size={18} />
              <span>{item.title}</span>
              {item.id === "signals" && !!stats?.high_priority && (
                <b>{stats.high_priority}</b>
              )}
              {view === item.id && <span className="active-dot" />}
            </button>
          ))}
        </nav>
        <button
          className={`saved-nav ${savedOnly ? "selected" : ""}`}
          onClick={() => {
            navigate("signals");
            setSavedOnly(true);
            setPriority("");
            setCategory("");
            setFilterTicker("");
          }}
        >
          <Bookmark size={17} />
          <span>Saved for later</span>
          <b>{savedSignals.length}</b>
        </button>
        <div className="sidebar-watch">
          <div className="nav-section-label">
            QUICK RESEARCH{" "}
            <span>{companies.filter((c) => c.watched).length}</span>
          </div>
          {companies
            .filter((c) => c.watched)
            .slice(0, 5)
            .map((c) => (
              <button key={c.ticker} onClick={() => research(c.ticker)}>
                <span className={`ticker-dot dot-${c.ticker.length % 4}`} />
                <span>{c.ticker}</span>
                <ArrowUpRight size={13} />
              </button>
            ))}
          <button className="sidebar-add" onClick={() => research("INFY")}>
            <Plus size={14} /> Research a company
          </button>
        </div>
        <div className="sidebar-bottom">
          <div className="sidebar-promise">
            <span>
              <ShieldCheck size={15} /> Clarity over noise.
            </span>
            <p>
              Every insight has a source.
              <br />
              Every signal has a reason.
            </p>
            <span className="little-line" />
          </div>
          <button
            className="settings-nav"
            onClick={() => setSettingsOpen(true)}
          >
            <SlidersHorizontal size={16} /> Monitoring preferences
          </button>
          <div className="profile">
            <div>ME</div>
            <span>
              My investment desk<small>Personal research workspace</small>
            </span>
            <ChevronDown size={12} />
          </div>
        </div>
      </aside>
      {mobileNav && (
        <button
          className="mobile-scrim"
          aria-label="Close navigation"
          onClick={() => setMobileNav(false)}
        />
      )}
      <div className="app-main">
        <header className="topbar">
          <div className="breadcrumb">
            <button
              className="mobile-menu icon-button"
              aria-label="Toggle navigation"
              onClick={() => setMobileNav(!mobileNav)}
            >
              <Menu size={21} />
            </button>
            <span>Workspace</span>
            <ChevronRight size={12} />
            <b>{navigation.find((n) => n.id === view)?.title}</b>
          </div>
          <CompanySearch companies={companies} onSelect={research} />
          <div className="topbar-actions">
            <span className="eod-label">
              <i /> EOD intelligence
            </span>
            <button
              className="icon-button notification-button"
              aria-label="View signals and alerts"
              onClick={() => navigate("signals")}
            >
              <Bell size={18} />
              {!!alerts.length && <i />}
            </button>
            <span className="avatar">ME</span>
          </div>
        </header>
        <main id="main-content">
          <div className="environment-bar">
            <div className="mode-toggle" aria-label="Data mode">
              <button
                className={mode === "demo" ? "selected" : ""}
                onClick={() => setMode("demo")}
              >
                <FlaskConical size={12} /> Demo replay
              </button>
              <button
                className={mode === "sourced" ? "selected" : ""}
                onClick={() => setMode("sourced")}
              >
                <ShieldCheck size={12} /> Sourced data
              </button>
            </div>
            <span>
              {mode === "demo"
                ? "Simulated signals & prices · 30 Oct 2026 replay"
                : "Original source dates · Completed trading sessions"}
            </span>
            <button
              className="text-button subtle"
              onClick={() => setSourceDetails(!sourceDetails)}
            >
              <CircleHelp size={13} />
              <span>Data notes</span>
            </button>
          </div>
          {sourceDetails && (
            <div className="data-notes">
              <b>Know what you’re looking at.</b>
              <p>
                Demo replay contains synthetic announcements and prices, with no
                claim that these events happened. Sourced data is fetched from
                Yahoo Finance and NSE, retains its original timestamps, and may
                be delayed or unavailable. Research always uses dated primary
                company documents, independently of the dashboard mode. Daily
                market bars are accepted only after 18:30 IST. Prices are
                split/dividend adjusted; they are not live quotes.
              </p>
              <p>
                {dashboard?.ai_configured
                  ? "AI synthesis is configured; each request still requires valid retrieved evidence."
                  : "No AI key is configured. Page-level extractive research works without an API key."}{" "}
                {dashboard?.scheduler_enabled
                  ? "Scheduled source refresh is enabled."
                  : "Source refresh is manual; optional scheduling can be enabled in the backend."}
              </p>
            </div>
          )}
          {error && (
            <div className="error-banner" role="alert">
              <span>{error}</span>
              <button className="text-button" onClick={reload}>
                Retry
                <RefreshCw size={13} />
              </button>
            </div>
          )}
          {view === "research" ? (
            <ResearchWorkspace
              initialTicker={researchTicker}
              initialTab={researchTab}
              companies={companies}
              onChanged={reload}
            />
          ) : (
            <>
              <div className="page-heading">
                <div>
                  <div className="eyebrow">
                    {view === "home"
                      ? "YOUR DAILY ADVANTAGE"
                      : view === "signals"
                        ? "LESS NOISE. MORE CONTEXT."
                        : "YOUR INVESTMENT UNIVERSE"}
                  </div>
                  <h1>
                    {view === "home" ? (
                      <>
                        Your portfolio. In perspective<span>.</span>
                      </>
                    ) : view === "signals" ? (
                      <>
                        The signals that deserve a closer look<span>.</span>
                      </>
                    ) : (
                      <>
                        Keep good companies in sight<span>.</span>
                      </>
                    )}
                  </h1>
                  <p>
                    {view === "home"
                      ? "Know what changed. Understand why it matters. Make your next move informed."
                      : view === "signals"
                        ? "Material developments first. Every priority explained. The source one tap away."
                        : "A cross-sector watchlist, with price moves and activity at a glance."}
                  </p>
                </div>
                <button
                  className="btn refresh-button"
                  disabled={refreshing}
                  onClick={() => void refresh()}
                >
                  <RefreshCw size={14} className={refreshing ? "spin" : ""} />
                  {refreshing ? "Refreshing sources…" : "Refresh sources"}
                </button>
              </div>
              {(refreshing || (mode === "sourced" && sync)) && (
                <div className="sync-banner">
                  <div>
                    <span
                      className={`status-dot ${refreshing ? "working" : ""}`}
                    />
                    <b>
                      {refreshing
                        ? "Fetching market sessions and exchange disclosures"
                        : `Source refresh ${sync?.result.status || "pending"}`}
                    </b>
                    <span>
                      {sync?.completed_at
                        ? new Date(sync.completed_at).toLocaleString("en-IN", {
                            timeZone: "Asia/Kolkata",
                          })
                        : "Results save incrementally. You can continue exploring."}
                    </span>
                  </div>
                  <button
                    className="text-button"
                    onClick={() => setSourceDetails(true)}
                  >
                    Data notes
                    <ArrowRight size={12} />
                  </button>
                  {!refreshing &&
                    (syncErrors.length > 0 ||
                      sync?.result.announcements?.ok === false) && (
                      <p>
                        {syncErrors.length} company feed(s) unavailable.{" "}
                        {sync?.result.announcements?.error ||
                          syncErrors[0]?.error}{" "}
                        Cached results retain their original dates.
                      </p>
                    )}
                </div>
              )}
              {loading && !dashboard ? (
                <div className="loading-state">
                  <Loader2 size={25} className="spin" />
                  <p>Getting your desk ready…</p>
                </div>
              ) : (
                <>
                  {view === "home" && (
                    <>
                      <div className="stats-grid">
                        <button
                          type="button"
                          className="stat-card"
                          onClick={() => navigate("watchlist")}
                        >
                          <span className="stat-icon">
                            <Activity size={18} />
                          </span>
                          <div>
                            <span>Companies on your radar</span>
                            <strong>
                              {stats?.companies ?? "—"}
                              <small>
                                across{" "}
                                {
                                  new Set(
                                    dashboard?.companies.map((c) => c.sector),
                                  ).size
                                }{" "}
                                sectors
                              </small>
                            </strong>
                          </div>
                          <div className="stat-bottom">
                            <span className="neutral-dot" />
                            {stats?.coverage || 0} with{" "}
                            {mode === "demo" ? "simulated" : "sourced"} EOD data
                          </div>
                        </button>
                        <button
                          type="button"
                          className="stat-card material"
                          onClick={() => focusSignals("high")}
                        >
                          <span className="stat-icon">
                            <Radar size={18} />
                          </span>
                          <div>
                            <span>Worth your attention</span>
                            <strong>
                              {stats?.high_priority ?? "—"}
                              <small>high-priority updates</small>
                            </strong>
                          </div>
                          <div className="stat-bottom">
                            <span className="priority-dot" />
                            From {stats?.total_filings || 0} filings in the last
                            24h
                          </div>
                        </button>
                        <button
                          type="button"
                          className="stat-card"
                          onClick={() => focusSignals("market")}
                        >
                          <span className="stat-icon">
                            <TrendingUp size={18} />
                          </span>
                          <div>
                            <span>Unusual market activity</span>
                            <strong>
                              {(stats?.volume_alerts || 0) +
                                (stats?.price_alerts || 0)}
                              <small>threshold crossings</small>
                            </strong>
                          </div>
                          <div className="stat-bottom">
                            <span className="gold-dot" />
                            {stats?.volume_alerts || 0} volume ·{" "}
                            {stats?.price_alerts || 0} price alerts
                          </div>
                        </button>
                        <button
                          type="button"
                          className="stat-card"
                          onClick={() => focusSignals("routine")}
                        >
                          <span className="stat-icon">
                            <ListFilter size={18} />
                          </span>
                          <div>
                            <span>A little less noise</span>
                            <strong>
                              {stats?.routine ?? "—"}
                              <small>routine filings</small>
                            </strong>
                          </div>
                          <div className="stat-bottom">
                            <Check size={11} />
                            Grouped away. Still one tap away.
                          </div>
                        </button>
                      </div>
                      <section className="daily-brief">
                        <span className="brief-icon">
                          <Sparkles size={18} />
                        </span>
                        <div>
                          <div className="brief-label">
                            YOUR INTELLIGENCE BRIEF{" "}
                            <span>
                              {mode === "demo"
                                ? "DEMO SCENARIO"
                                : "RULE-BASED DIGEST"}
                            </span>
                          </div>
                          <p>{dashboard?.digest}</p>
                        </div>
                        <button
                          aria-label="Read the complete digest"
                          onClick={() => navigate("signals")}
                        >
                          <ArrowRight size={19} />
                        </button>
                      </section>
                      <MarketExplorer
                        quotes={
                          dashboard?.mode === mode ? dashboard.companies : []
                        }
                        mode={mode}
                        onInspect={setSelectedCompany}
                      />
                    </>
                  )}
                  {(view === "home" || view === "signals") && (
                    <div className="intelligence-grid">
                      <section className="feed-section">
                        <div className="section-title feed-heading">
                          <div>
                            <h2>
                              {view === "home"
                                ? "Your priority inbox"
                                : savedOnly
                                  ? "Saved for later"
                                  : "Announcements & alerts"}
                              <span className="count-badge">
                                {feedItems.length}
                              </span>
                            </h2>
                            <p>
                              {savedOnly
                                ? "Your saved signals, across all dates. Stored on this device."
                                : "The developments worth a closer look."}
                            </p>
                          </div>
                          <label className="window-select">
                            <Clock3 size={12} />
                            <span className="sr-only">Time window</span>
                            <select
                              value={windowValue}
                              disabled={savedOnly}
                              aria-label="Time window"
                              onChange={(e) => setWindowValue(e.target.value)}
                            >
                              <option value="24h">Last 24 hours</option>
                              <option value="7d">Last 7 days</option>
                              <option value="30d">Last 30 days</option>
                              <option value="custom">Custom dates</option>
                            </select>
                            <ChevronDown size={12} />
                          </label>
                        </div>
                        <div className="feed-filters">
                          <div className="filter-scroll">
                            <button
                              className={
                                !priority && !savedOnly
                                  ? "filter-chip active"
                                  : "filter-chip"
                              }
                              onClick={() => {
                                setPriority("");
                                setSavedOnly(false);
                              }}
                            >
                              All signals
                            </button>
                            <button
                              className={
                                priority === "high"
                                  ? "filter-chip active"
                                  : "filter-chip"
                              }
                              onClick={() =>
                                setPriority(priority === "high" ? "" : "high")
                              }
                            >
                              <span className="priority-dot" /> High priority
                            </button>
                            <button
                              className={`filter-chip ${savedOnly ? "active" : ""}`}
                              onClick={() => setSavedOnly(!savedOnly)}
                              aria-pressed={savedOnly}
                            >
                              <Bookmark size={12} /> Saved{" "}
                              <span>
                                {
                                  savedSignals.filter((f) => f.mode === mode)
                                    .length
                                }
                              </span>
                            </button>
                            <label className="filter-select">
                              <span className="sr-only">Company filter</span>
                              <select
                                value={filterTicker}
                                onChange={(e) =>
                                  setFilterTicker(e.target.value)
                                }
                              >
                                <option value="">All companies</option>
                                {companies
                                  .filter((c) => c.watched)
                                  .map((c) => (
                                    <option key={c.ticker}>{c.ticker}</option>
                                  ))}
                              </select>
                              <ChevronDown size={11} />
                            </label>
                            <label className="filter-select">
                              <span className="sr-only">Category filter</span>
                              <select
                                value={category}
                                onChange={(e) => setCategory(e.target.value)}
                              >
                                <option value="">All categories</option>
                                {filterCategories.map((c) => (
                                  <option key={c} value={c}>
                                    {label(c)}
                                  </option>
                                ))}
                              </select>
                              <ChevronDown size={11} />
                            </label>
                          </div>
                          <button
                            className="icon-button filter-settings"
                            aria-label="Monitoring preferences"
                            onClick={() => setSettingsOpen(true)}
                          >
                            <SlidersHorizontal size={16} />
                          </button>
                        </div>
                        {windowValue === "custom" && (
                          <div className="date-range">
                            <label>
                              From
                              <input
                                type="date"
                                value={customStart}
                                onChange={(e) => setCustomStart(e.target.value)}
                              />
                            </label>
                            <label>
                              To
                              <input
                                type="date"
                                min={customStart}
                                value={customEnd}
                                onChange={(e) => setCustomEnd(e.target.value)}
                              />
                            </label>
                            <span>India Standard Time</span>
                          </div>
                        )}
                        {view === "signals" && !savedOnly && (
                          <div className="market-alerts">
                            <div className="section-title">
                              <h3>
                                Triggered by your rules{" "}
                                <span className="count-badge">
                                  {marketAlerts.length}
                                </span>
                              </h3>
                              <button
                                className="text-button"
                                onClick={() => setSettingsOpen(true)}
                              >
                                Edit rules
                                <Settings2 size={12} />
                              </button>
                            </div>
                            {marketAlerts.length ? (
                              marketAlerts.map((a) => (
                                <details className="market-alert" key={a.id}>
                                  <summary>
                                    <span className="alert-symbol">
                                      {a.kind === "volume" ? (
                                        <Activity size={16} />
                                      ) : (
                                        <TrendingUp size={16} />
                                      )}
                                    </span>
                                    <div>
                                      <b>{a.title}</b>
                                      <span>
                                        {a.date} ·{" "}
                                        {mode === "demo"
                                          ? "Simulated EOD"
                                          : "Sourced EOD"}
                                      </span>
                                    </div>
                                    <ChevronDown size={14} />
                                  </summary>
                                  <p>{a.explanation}</p>
                                  {a.mode === "sourced" && a.source_url && (
                                    <a
                                      href={a.source_url}
                                      target="_blank"
                                      rel="noreferrer"
                                    >
                                      Price history
                                      <ExternalLink size={12} />
                                    </a>
                                  )}
                                </details>
                              ))
                            ) : (
                              <p className="muted">
                                No completed-session crossings for the saved
                                monitoring rules.
                              </p>
                            )}
                            {interestFilings.length > 0 && (
                              <p className="interest-summary">
                                <Bell size={12} />
                                {interestFilings.length} material filings match
                                your announcement interests.
                              </p>
                            )}
                          </div>
                        )}
                        <div className="signal-list">
                          {visibleFilings.map((f) => (
                            <SignalCard
                              filing={f}
                              key={`${mode}-${f.id}`}
                              onResearch={research}
                              saved={savedSignals.some(
                                (saved) =>
                                  saved.id === f.id && saved.mode === f.mode,
                              )}
                              onSave={toggleSaved}
                            />
                          ))}
                          {!visibleFilings.length && (
                            <div className="empty-state">
                              <Radar size={29} />
                              <h3>
                                {savedOnly
                                  ? "Keep a good signal close."
                                  : mode === "sourced"
                                    ? "Your sourced inbox starts here."
                                    : "A quiet corner of your watchlist."}
                              </h3>
                              <p>
                                {savedOnly
                                  ? "Tap the bookmark on any announcement to find it here later. Saved signals are specific to the current data mode."
                                  : mode === "sourced"
                                    ? "Refresh sources to collect NSE filings. Original timestamps and source links stay with every update."
                                    : "No disclosures match these filters. Try a wider window or another category."}
                              </p>
                              {mode === "sourced" && (
                                <button
                                  className="btn"
                                  disabled={refreshing}
                                  onClick={() => void refresh()}
                                >
                                  Refresh sources
                                  <RefreshCw size={13} />
                                </button>
                              )}
                            </div>
                          )}
                        </div>
                        {!savedOnly && (
                          <button
                            className="routine-toggle"
                            onClick={() => setRoutine(!routine)}
                            aria-expanded={routine}
                          >
                            <span className="routine-icon">
                              <FileText size={14} />
                            </span>
                            <div>
                              <b>
                                {routine ? "Showing" : "Tucked away"}:{" "}
                                {routineCount} routine filings
                              </b>
                              <span>
                                Administrative updates, available when you need
                                them
                              </span>
                            </div>
                            <ChevronDown
                              size={16}
                              className={routine ? "rotate" : ""}
                            />
                          </button>
                        )}
                        {view === "home" &&
                          !savedOnly &&
                          filings.length > 4 && (
                            <button
                              className="view-all"
                              onClick={() => navigate("signals")}
                            >
                              See all {filings.length} updates
                              <ArrowRight size={14} />
                            </button>
                          )}
                      </section>
                      <aside className="right-column">
                        <section className="panel radar-panel">
                          <div className="section-title">
                            <h2>Market radar</h2>
                            <span className="small-label">
                              EOD · {sourcedLabel}
                            </span>
                          </div>
                          <div className="radar-subheading">
                            <span>COMPANY</span>
                            <span>DAY CHANGE</span>
                          </div>
                          {dashboard?.companies
                            .slice()
                            .sort(
                              (a, b) =>
                                (b.volume_ratio || 0) - (a.volume_ratio || 0),
                            )
                            .slice(0, 5)
                            .map((q) => (
                              <button
                                className="radar-row"
                                key={q.ticker}
                                onClick={() => {
                                  setChartTicker(q.ticker);
                                  setSelectedCompany(q.ticker);
                                }}
                              >
                                <CompanyMark ticker={q.ticker} />
                                <div>
                                  <b>{q.ticker}</b>
                                  <span>
                                    {q.volume_ratio &&
                                    q.volume_ratio >=
                                      (prefs?.volume_multiplier || 2) ? (
                                      <>
                                        <i className="gold-dot" />
                                        {q.volume_ratio.toFixed(1)}× volume
                                      </>
                                    ) : q.close !== null ? (
                                      money(q.close)
                                    ) : (
                                      "No sourced data"
                                    )}
                                  </span>
                                </div>
                                <Sparkline
                                  data={q.history}
                                  positive={(q.change_pct || 0) >= 0}
                                />
                                <b
                                  className={
                                    (q.change_pct || 0) >= 0
                                      ? "positive"
                                      : "negative"
                                  }
                                >
                                  {pct(q.change_pct)}
                                </b>
                              </button>
                            ))}
                          <button
                            className="text-button"
                            onClick={() => navigate("watchlist")}
                          >
                            View your watchlist
                            <ArrowRight size={13} />
                          </button>
                          <div className="radar-footnote">
                            <Clock3 size={11} /> End-of-day data. No live price
                            claims.
                          </div>
                        </section>
                        <section className="panel chart-panel">
                          <div className="section-title">
                            <label>
                              <span className="sr-only">Chart company</span>
                              <select
                                value={chartQuote?.ticker || chartTicker}
                                onChange={(e) => setChartTicker(e.target.value)}
                              >
                                {dashboard?.companies.map((q) => (
                                  <option key={q.ticker}>{q.ticker}</option>
                                ))}
                              </select>
                            </label>
                            <span className="small-label">
                              {mode === "demo" ? "SIMULATED" : "ADJUSTED CLOSE"}
                            </span>
                          </div>
                          <div className="chart-price">
                            <strong>{money(chartQuote?.close ?? null)}</strong>
                            <span
                              className={
                                (chartQuote?.change_pct || 0) >= 0
                                  ? "positive"
                                  : "negative"
                              }
                            >
                              {pct(chartQuote?.change_pct ?? null)}
                            </span>
                          </div>
                          {chartQuote?.history.length ? (
                            <PriceChart data={chartQuote.history} />
                          ) : (
                            <div className="chart-empty">
                              Refresh sources to see price history.
                            </div>
                          )}
                          <div className="chart-caption">
                            <span>
                              {chartQuote?.date
                                ? `Through ${chartQuote.date}`
                                : "No sessions fetched"}
                            </span>
                            <span>₹ · NSE</span>
                          </div>
                        </section>
                        <section className="guidance-teaser">
                          <div className="teaser-top">
                            <span>
                              <Target size={16} /> THE ACCOUNTABILITY LENS
                            </span>
                            <ArrowUpRight size={18} />
                          </div>
                          <h3>
                            Promises are easy.
                            <br />
                            <em>Delivery is the signal.</em>
                          </h3>
                          <p>
                            Put management’s guidance next to the numbers they
                            actually reported.
                          </p>
                          <div className="teaser-comparison">
                            <div>
                              <span>ORIGINAL FY25 GUIDANCE</span>
                              <b>
                                1–3<span>%</span>
                              </b>
                            </div>
                            <ArrowRight size={18} />
                            <div>
                              <span>REPORTED CC GROWTH</span>
                              <b>
                                4.2<span>%</span>
                              </b>
                            </div>
                          </div>
                          <p className="teaser-source">
                            Infosys · Historical FY25 primary-source example
                          </p>
                          <button onClick={() => research("INFY", "guidance")}>
                            Explore promise vs. reality
                            <ArrowRight size={14} />
                          </button>
                        </section>
                      </aside>
                    </div>
                  )}
                  {view === "watchlist" && (
                    <section className="panel watchlist-panel">
                      <div className="section-title">
                        <div>
                          <h2>
                            My watchlist{" "}
                            <span className="count-badge">
                              {companies.filter((c) => c.watched).length}
                            </span>
                          </h2>
                          <p className="section-description">
                            Monitor across sectors. Research outside the list.
                          </p>
                        </div>
                        <button
                          className="btn primary"
                          onClick={() => research("INFY")}
                        >
                          <Plus size={14} /> Find a company
                        </button>
                      </div>
                      <label className="watch-search">
                        <Search size={15} />
                        <input
                          placeholder="Filter by company, ticker, or sector"
                          value={watchSearch}
                          onChange={(e) => setWatchSearch(e.target.value)}
                        />
                      </label>
                      <div className="watch-controls">
                        <div
                          className="sector-filters"
                          aria-label="Watchlist sector"
                        >
                          <button
                            className={!watchSector ? "active" : ""}
                            onClick={() => setWatchSector("")}
                          >
                            All sectors
                          </button>
                          {Array.from(
                            new Set(companies.map((c) => c.sector)),
                          ).map((sector) => (
                            <button
                              key={sector}
                              className={watchSector === sector ? "active" : ""}
                              onClick={() =>
                                setWatchSector(
                                  watchSector === sector ? "" : sector,
                                )
                              }
                            >
                              {sector}
                            </button>
                          ))}
                        </div>
                        <label className="watch-sort">
                          Sort by
                          <select
                            aria-label="Sort watchlist"
                            value={watchSort}
                            onChange={(e) => setWatchSort(e.target.value)}
                          >
                            <option value="ticker">Company A–Z</option>
                            <option value="gainers">Top gainers</option>
                            <option value="decliners">Top decliners</option>
                            <option value="volume">Unusual volume</option>
                          </select>
                        </label>
                      </div>
                      <div className="table-scroll">
                        <table className="watchlist-table">
                          <thead>
                            <tr>
                              <th>Company</th>
                              <th>Sector</th>
                              <th>Adjusted close</th>
                              <th>Day change</th>
                              <th>Volume</th>
                              <th>Trend</th>
                              <th>Watch</th>
                            </tr>
                          </thead>
                          <tbody>
                            {watchlist.map((c) => {
                              const q = dashboard?.companies.find(
                                (q) => q.ticker === c.ticker,
                              );
                              return (
                                <tr key={c.ticker}>
                                  <td>
                                    <button
                                      className="watch-company"
                                      onClick={() => {
                                        const q = dashboard?.companies.find(
                                          (q) => q.ticker === c.ticker,
                                        );
                                        if (q) setSelectedCompany(c.ticker);
                                        else research(c.ticker);
                                      }}
                                    >
                                      <CompanyMark ticker={c.ticker} />
                                      <span>
                                        <b>{c.ticker}</b>
                                        <small>{c.name}</small>
                                      </span>
                                    </button>
                                  </td>
                                  <td>{c.sector}</td>
                                  <td className="strong">
                                    {money(q?.close ?? null)}
                                    <small>
                                      {q?.date || "No cached sessions"}
                                    </small>
                                  </td>
                                  <td
                                    className={
                                      (q?.change_pct || 0) >= 0
                                        ? "positive"
                                        : "negative"
                                    }
                                  >
                                    {pct(q?.change_pct ?? null)}
                                  </td>
                                  <td>
                                    {q?.volume_ratio
                                      ? `${q.volume_ratio.toFixed(2)}×`
                                      : "—"}
                                  </td>
                                  <td>
                                    <Sparkline
                                      data={q?.history || []}
                                      positive={(q?.change_pct || 0) >= 0}
                                    />
                                  </td>
                                  <td>
                                    <button
                                      className={`watch-toggle ${c.watched ? "watching" : ""}`}
                                      aria-label={`${c.watched ? "Remove" : "Add"} ${c.ticker} ${c.watched ? "from" : "to"} watchlist`}
                                      onClick={() => void toggleWatch(c)}
                                    >
                                      {c.watched ? (
                                        <Check size={15} />
                                      ) : (
                                        <Plus size={15} />
                                      )}
                                    </button>
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                      <p className="method-note">
                        {mode === "demo"
                          ? "Synthetic prices for interaction testing. They are not market observations."
                          : "Yahoo Finance historical adjusted closing prices. Each row retains its last completed session date."}{" "}
                        Volume compares the latest session with the preceding{" "}
                        {prefs?.lookback || 20} sessions.
                      </p>
                    </section>
                  )}
                </>
              )}
            </>
          )}
          <footer className="app-footer">
            <span>
              <div className="footer-mark" />
              Built for perspective.
            </span>
            <p>Research intelligence · Verify the source before acting.</p>
            <span>
              {mode === "demo"
                ? "DEMONSTRATION WORKSPACE"
                : "SOURCE-CONNECTED WORKSPACE"}
            </span>
          </footer>
        </main>
      </div>
      <nav className="mobile-bottom-nav" aria-label="Mobile navigation">
        {navigation.map((n) => (
          <button
            key={n.id}
            className={view === n.id ? "active" : ""}
            onClick={() => navigate(n.id)}
          >
            <n.icon size={19} />
            <span>
              {n.id === "signals"
                ? "Signals"
                : n.id === "research"
                  ? "Research"
                  : n.id === "watchlist"
                    ? "Watchlist"
                    : "Overview"}
            </span>
          </button>
        ))}
      </nav>
      {selectedQuote && (
        <CompanyDrawer
          quote={selectedQuote}
          mode={mode}
          onClose={closeCompany}
          onResearch={(ticker) => {
            closeCompany();
            research(ticker);
          }}
        />
      )}
      {toast && (
        <div className="action-toast" role="status">
          <Check size={16} />
          {toast}
          <button
            aria-label="Dismiss notification"
            onClick={() => setToast("")}
          >
            <X size={14} />
          </button>
        </div>
      )}
      {settingsOpen && prefs && (
        <Preferences
          initial={prefs}
          companies={companies}
          onClose={closeSettings}
          onSave={() => {
            setSettingsOpen(false);
            reload();
          }}
        />
      )}
    </div>
  );
}
