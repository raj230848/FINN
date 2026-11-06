"use client";
import {Select} from "@/components/select";
import { useCallback, useEffect, useId, useRef, useState } from "react";
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
  ApiError,
  FilingFeed,
  NotificationFeed,
  Alert,
  Company,
  CompanyDiscovery,
  Dashboard,
  Filing,
  GuidanceItem,
  label,
  Mode,
  money,
  pct,
  Prefs,
  shortDate,
  SyncRun,
} from "@/lib/api";
import dynamic from "next/dynamic";
import { Sparkline } from "@/components/sparkline";
import {CompanyLookup, type CompanyMatch} from "@/components/company-lookup";
import {AddCompanyDialog} from "@/components/add-company-dialog";
import {ThemeBubbles} from "@/components/theme-bubbles";



import {
  FilterSheet,
  MobileBrief,
  MobileMovers,
  MobileWatchlist,
} from "@/components/mobile-workspace";

import { AccessGate } from "@/components/access-gate";
import { Notifications } from "@/components/notifications";
import { ThemeToggle } from "@/components/theme-toggle";

const PriceChart=dynamic(()=>import("@/components/charts").then(m=>m.PriceChart),{ssr:false});
const MarketExplorer=dynamic(()=>import("@/components/market-explorer").then(m=>m.MarketExplorer),{ssr:false,loading:()=> <div className="panel chart-loading">Loading market history…</div>});
const CompanyDrawer=dynamic(()=>import("@/components/market-explorer").then(m=>m.CompanyDrawer),{ssr:false});
const ResearchWorkspace=dynamic(()=>import("@/components/research").then(m=>m.ResearchWorkspace),{loading:()=> <div className="panel chart-loading">Opening the research desk…</div>});
const PromiseTracker=dynamic(()=>import("@/components/research").then(m=>m.PromiseTracker),{loading:()=> <div className="panel chart-loading">Opening Promise Tracker…</div>});

type View = "home" | "signals" | "research" | "watchlist" | "promises";
const navigation = [
  { id: "home" as View, title: "Overview", icon: LayoutDashboard },
  { id: "signals" as View, title: "Signals & alerts", icon: Radar },
  { id: "research" as View, title: "Research desk", icon: BookOpen },
  { id: "promises" as View, title: "Promise Tracker", icon: Target },
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
  onResearch: (t: string,tab?:string,question?:string) => void;
  saved: boolean;
  onSave: (filing: Filing) => void;
}) {
  const [open, setOpen] = useState(false);
  const insightId = useId();
  const [context,setContext]=useState<{message:string;excerpt?:string;comparison_period?:string}|null>(null);
  useEffect(()=>{
    if(!open || filing.mode!=="sourced" || !["management_change","results"].includes(filing.category))return;
    let cancelled=false;
    api<{message:string;excerpt?:string;comparison_period?:string}>(`/announcements/${filing.id}/context`).then(c=>{if(!cancelled)setContext(c);}).catch(()=>{if(!cancelled)setContext({message:"Source context is unavailable. Use the original filing link."});});
    return()=>{cancelled=true;};
  },[open,filing.id,filing.mode,filing.category]);
  return (
    <article
      className={`signal-card priority-${filing.priority} ${open ? "is-expanded" : ""}`}
      onClick={event => {
        if (event.target instanceof Element && !event.target.closest("button, a")) {
          setOpen(current => !current);
        }
      }}
    >
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
          {filing.needs_review ? "Needs review" : label(filing.priority)}
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
          onClick={() => setOpen(current => !current)}
          aria-expanded={open}
          aria-controls={open ? insightId : undefined}
        >
          <ListFilter size={13} />
          {open ? "Close insight" : "Read insight"}
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
                <span>Original filing · PDF</span>
                <ExternalLink size={14} aria-hidden="true" />
              </a>
            )
          )}
          <button
            aria-label={`Research ${filing.ticker}`}
            className="signal-research"
            onClick={() => onResearch(filing.ticker,"overview",`What do primary sources establish about this ${filing.category.replaceAll("_"," ")} filing: ${filing.title}?`)}
          >
            <ArrowUpRight size={16} />
          </button>
        </div>
      </div>
      {open && (
        <div className="signal-reasoning" id={insightId}>
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
          {context&&<aside className="filing-context"><p>{context.message}</p>{context.excerpt&&<blockquote>{context.excerpt}</blockquote>}{context.comparison_period&&<button className="text-button" onClick={()=>onResearch(filing.ticker)}>Review {context.comparison_period} comparisons</button>}</aside>}
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
            <Select
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
            </Select>
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
  const [mode] = useState<Mode>("sourced");
  const filingMode: Mode = "sourced";
  const [filingsAsOf, setFilingsAsOf] = useState("");
  const [guidanceTeaser, setGuidanceTeaser] = useState<GuidanceItem | null>(null);
  useEffect(() => {
    const request = new AbortController();
    api<{items: GuidanceItem[]}>("/companies/INFY/guidance", {signal: request.signal})
      .then(({items}) => setGuidanceTeaser(items.find(item =>
        item.revision === "Initial outlook" && item.unit === "percent" && item.actual != null
        && item.guidance_url && item.actual_url) ?? null))
      .catch(() => {});
    return () => request.abort();
  }, []);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [filings, setFilings] = useState<Filing[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [prefs, setPrefs] = useState<Prefs | null>(null);
  const [sessionLocked, setSessionLocked] = useState(false);
  const [notificationFeed, setNotificationFeed] = useState<NotificationFeed>({
    items: [],
    unread_count: 0,
    total: 0,
    has_more: false,
  });
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const closeNotifications = useCallback(() => setNotificationsOpen(false), []);
  const [feedMeta, setFeedMeta] = useState<
    Omit<FilingFeed, "items" | "routine_count">
  >({});
  const [loadingMore, setLoadingMore] = useState(false);
  const feedVersion = useRef(0);
  const feedQuery = useRef("");
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [mobileFocus, setMobileFocus] = useState<"brief" | "market">("brief");
  const closeFilters = useCallback(() => setFiltersOpen(false), []);
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
  const [researchQuestion,setResearchQuestion]=useState("");
  const [researchDiscovery,setResearchDiscovery]=useState<CompanyDiscovery|null>(null);
  const [chartTicker, setChartTicker] = useState("RELIANCE");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [sync, setSync] = useState<SyncRun | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [generation, setGeneration] = useState(0);
  const [mobileNav, setMobileNav] = useState(false);
  const [sourceDetails, setSourceDetails] = useState(false);
  const [watchSearch, setWatchSearch] = useState("");
  const [addCompanyOpen, setAddCompanyOpen] = useState(false);
  const [watchSector, setWatchSector] = useState("");
  const [watchSort, setWatchSort] = useState("ticker");
  const [savedSignals, setSavedSignals] = useState<Filing[]>([]);
  const [savedOnly, setSavedOnly] = useState(false);
  const [selectedCompany, setSelectedCompany] = useState<string | null>(null);
  const [toast, setToast] = useState("");
  const closeCompany = useCallback(() => setSelectedCompany(null), []);
  const reload = useCallback(() => setGeneration((g) => g + 1), []);
  const closeSettings = useCallback(() => setSettingsOpen(false), []);
  const autoRequested=useRef(0),displayMode=useRef<Mode>("sourced");
  const [wide,setWide]=useState(false);
  useEffect(()=>{const media=matchMedia("(min-width: 761px)");const changed=()=>setWide(media.matches);changed();media.addEventListener("change",changed);return()=>media.removeEventListener("change",changed);},[]);
  useEffect(()=>{if(wide)setMobileNav(false);},[wide]);
  useEffect(()=>{
    if(!mobileNav||wide)return;
    const menu=document.getElementById("workspace-navigation");
    const previous=document.activeElement as HTMLElement|null;
    const overflow=document.body.style.overflow;
    document.body.style.overflow="hidden";
    const controls=()=>Array.from(menu?.querySelectorAll<HTMLElement>('button:not(:disabled),a[href]')||[]).filter(e=>e.getClientRects().length>0&&getComputedStyle(e).visibility!=="hidden");
    controls()[0]?.focus();
    const key=(event:KeyboardEvent)=>{
      if(event.key==="Escape"){event.preventDefault();setMobileNav(false);}
      if(event.key==="Tab"){
        const items=controls(),first=items[0],last=items.at(-1);
        if(event.shiftKey&&document.activeElement===first){event.preventDefault();last?.focus();}
        else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first?.focus();}
      }
    };
    document.addEventListener("keydown",key);
    return()=>{document.removeEventListener("keydown",key);document.body.style.overflow=overflow;previous?.focus();};
  },[mobileNav,wide]);

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
              f.mode === "sourced" && typeof f.source_url === "string" && f.source_url.startsWith("https://nsearchives.nseindia.com/corporate/"),
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
    if(displayMode.current!==mode){setDashboard(null);setAlerts([]);setFilings([]);setRoutineCount(0);setFeedMeta({});setNotificationFeed({items:[],unread_count:0,total:0,has_more:false});displayMode.current=mode;}
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
          if (e instanceof ApiError && e.code === "SIGN_IN_REQUIRED")
            setSessionLocked(true);
          setError(e.message);
          // Preserve the last good snapshot for this mode during a provider/API outage.
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [mode, generation]);
  useEffect(()=>{
    if(mode!=="sourced"||!dashboard?.freshness||sessionLocked)return;
    if(dashboard.freshness.state==="in_progress"&&dashboard.freshness.run_id){
      setSync({id:dashboard.freshness.run_id,started_at:new Date().toISOString(),completed_at:null,result:{status:"running"}});setRefreshing(true);return;
    }
    if(!dashboard.guest&&dashboard.freshness.should_refresh&&Date.now()-autoRequested.current>60000){autoRequested.current=Date.now();void refresh();}
  },[dashboard,mode,sessionLocked]);
  useEffect(() => {
    const update = () => { if (document.visibilityState === "visible") reload(); };
    const timer = setInterval(update, 60_000);
    window.addEventListener("online", update);
    window.addEventListener("focus", update);
    document.addEventListener("visibilitychange", update);
    return () => {
      clearInterval(timer);
      window.removeEventListener("online", update);
      window.removeEventListener("focus", update);
      document.removeEventListener("visibilitychange", update);
    };
  }, [reload]);
  useEffect(() => {
    let cancelled = false;
    feedVersion.current++;
    setLoadingMore(false);
    const params = new URLSearchParams({
      mode: filingMode,
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
    feedQuery.current = params.toString();
    api<FilingFeed>(`/announcements?${params}`)
      .then((data) => {
        if (!cancelled) {
          setFilings(data.items);
          setFilingsAsOf(data.as_of || "");
          setRoutineCount(data.routine_count);
          setFeedMeta({
            total: data.total,
            has_more: data.has_more,
            next_offset: data.next_offset,
            coverage: data.coverage,
          });
        }
      })
      .catch((e) => {
        if (!cancelled) setError(e.message);
      });
    return () => {
      cancelled = true;
    };
  }, [
    filingMode,
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
          setToast(result.result.status==="complete"?"Sources refreshed. Original session dates are shown.":"Refresh finished with source gaps. Review the status.");
          reload();
        }
      } catch (e) {
        setError((e as Error).message);
        setRefreshing(false);
      }
    }, 2500);
    return () => clearInterval(timer);
  }, [refreshing, sync?.id, reload]);
  useEffect(() => {
    let cancelled = false;
    const update = () =>
      api<NotificationFeed>(`/notifications?mode=${mode}`)
        .then((data) => {
          if (!cancelled) setNotificationFeed(data);
        })
        .catch(() => {
          /* Digest remains usable if notification history is temporarily unavailable. */
        });
    void update();
    const timer = setInterval(() => void update(), 30000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [mode, generation]);
  async function loadMoreFilings() {
    if (loadingMore || feedMeta.next_offset == null) return;
    const version = feedVersion.current;
    setLoadingMore(true);
    const params = new URLSearchParams(feedQuery.current);
    params.set("offset", String(feedMeta.next_offset));
    try {
      const data = await api<FilingFeed>(`/announcements?${params}`);
      if (version === feedVersion.current) {
        setFilings((previous) => [
          ...previous,
          ...data.items.filter((f) => !previous.some((p) => p.id === f.id)),
        ]);
        setFeedMeta({
          total: data.total,
          has_more: data.has_more,
          next_offset: data.next_offset,
          coverage: data.coverage,
        });
      }
    } catch (e) {
      if (version === feedVersion.current) setError((e as Error).message);
    } finally {
      if (version === feedVersion.current) setLoadingMore(false);
    }
  }
  async function refresh() {
    if (refreshing) return;
    setRefreshing(true);
    setError("");
    try {
      const result = await api<{message:string}>("/sync", {method:"POST"});
      reload();
      setToast(result.message);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setRefreshing(false);
    }
  }
  function navigate(id: View) {
    setView(id);
    if (id === "home") setMobileFocus("brief");
    setMobileNav(false);
    setSavedOnly(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
  async function research(ticker: string, tab = "overview",question="") {
    setResearchDiscovery(null);
    if(!companies.some(c=>c.ticker===ticker)){
      const result=await api<CompanyDiscovery>(`/companies/${ticker}/discover`,{method:"POST"});
      setResearchDiscovery(result);reload();
    }
    setResearchTicker(ticker);
    setResearchTab(tab);
    setResearchQuestion(question);
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
  async function addCompany(match: CompanyMatch) {
    const ticker = encodeURIComponent(match.ticker);
    const company = await api<Company>(`/companies/${ticker}?add_if_listed=true`, {
      method: "PATCH",
      body: JSON.stringify({ watched: true }),
    });
    setCompanies(current => [company, ...current.filter(c => c.ticker !== company.ticker)]);
    setWatchSearch("");
    setWatchSector("");
    setToast(`${company.ticker} is on your watchlist.`);
    reload();
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
          (view === "signals" || f.mode === filingMode) &&
          (!filterTicker || f.ticker === filterTicker) &&
          (!category || f.category === category) &&
          (!priority || f.priority === priority),
      )
    : filings.filter(f => f.mode === filingMode);
  const visibleFilings =
    view === "home" && !routine ? feedItems.slice(0, 4) : feedItems;
  const watchQuery = watchSearch.trim().toLowerCase();
  const watchlist = companies
    .filter(
      (c) =>
        (!watchSector || c.sector === watchSector) &&
        (!watchQuery ||
          `${c.ticker} ${c.name} ${c.sector}`
            .toLowerCase()
            .includes(watchQuery)),
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
  const selectedIssuer = companies.find(company => company.ticker === selectedCompany);
  const selectedQuote = dashboard?.companies.find(
    (q) => q.ticker === selectedCompany,
  ) ?? (selectedIssuer && {
    ...selectedIssuer,
    close: null,
    change_pct: null,
    volume_ratio: null,
    volume: null,
    date: null,
    fetched_at: null,
    source_url: null,
    history: [],
  });
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

  if (sessionLocked)
    return (
      <AccessGate
        onCancel={dashboard?.guest ? () => setSessionLocked(false) : undefined}
        onUnlocked={() => {
          setSessionLocked(false);
          setError("");
          reload();
        }}
      />
    );
  return (
    <div className="app-shell" data-view={view} data-mobile-focus={mobileFocus}>
      <ThemeBubbles />
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <aside id="workspace-navigation" role={mobileNav&&!wide?"dialog":undefined} aria-modal={mobileNav&&!wide?true:undefined} aria-label={mobileNav&&!wide?"Navigation":undefined} className={`sidebar ${mobileNav ? "mobile-open" : ""}`}>
        <div className="sidebar-heading">
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
        <button className="sidebar-close icon-button" aria-label="Close menu" onClick={()=>setMobileNav(false)}><X size={20}/></button>
        </div>
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
          <button
            className="settings-nav"
            onClick={() => {setMobileNav(false);setSettingsOpen(true);}}
          >
            <SlidersHorizontal size={16} /> Monitoring preferences
          </button>
        </div>
      </aside>
      {mobileNav && (
        <button
          className="mobile-scrim"
          aria-label="Close navigation"
          onClick={() => setMobileNav(false)}
        />
      )}
      <div className="app-main" inert={mobileNav&&!wide?true:undefined}>
        <header className="topbar">
          <div className="breadcrumb">
            <button
              className="mobile-menu icon-button"
              aria-label="Toggle navigation"
              aria-expanded={mobileNav}
              aria-controls="workspace-navigation"
              aria-haspopup="dialog"
              onClick={() => setMobileNav(!mobileNav)}
            >
              <Menu size={21} />
            </button>
            <span className="phone-wordmark">
              finn<span>.</span>
            </span>
            <b>{navigation.find((n) => n.id === view)?.title}</b>
          </div>
          <CompanyLookup compact companies={companies} onSelect={c=>research(c.ticker,"documents")} />
          <div className="topbar-actions">
            <ThemeToggle />
            <button
              className="icon-button notification-button"
              aria-label={`Notifications, ${notificationFeed.unread_count} unread`}
              onClick={() => setNotificationsOpen(true)}
            >
              <Bell size={18} />
              {notificationFeed.unread_count > 0 && (
                <span className="unread-badge">
                  {notificationFeed.unread_count > 99
                    ? "99+"
                    : notificationFeed.unread_count}
                </span>
              )}
            </button>
          </div>
        </header>
        <main id="main-content">
          {dashboard?.guest && <div className="notice-banner guest-notice">
            <span>Public preview. Browse the desk and ask questions about its source documents.</span>
            <button className="text-button" onClick={() => setSessionLocked(true)}>Desk sign-in</button>
          </div>}
          <div className="environment-bar">
            <strong className="public-demo-label"><ShieldCheck size={14} aria-hidden="true" /> Automatically updated source data</strong>
            <button className="text-button subtle" aria-label="Data notes" aria-expanded={sourceDetails} onClick={() => setSourceDetails(!sourceDetails)}>
              <CircleHelp size={13} /> <span>Data notes</span>
            </button>
          </div>
          {sourceDetails && (
            <div className="data-notes">
              <p>Market history and alerts use Yahoo Finance end-of-day observations. NSE filings have their own source date. Sources are checked automatically on weekdays. This page checks the update feed every minute and when reopened. Prices use completed trading sessions; holidays and provider delays can leave the last session date unchanged. The research desk uses selected historical company reports. Your watchlist and preferences are saved on this device.</p>
              <a href="https://github.com/raj230848/FINN" target="_blank" rel="noreferrer">View the full FINN application on GitHub</a>
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
          {dashboard && <div className="source-freshness" aria-label="Source freshness">
            <span className={`freshness-tag ${dashboard.source_refresh?.status !== "ready" ? "stale" : ""}`}>
              {refreshing ? "Checking for updates…" : dashboard.source_refresh?.status === "ready" ? "Sourced EOD" : "Update delayed"}
            </span>
            <span>Latest completed session <b>{dashboard.companies.map(company => company.date).filter(Boolean).sort().at(-1) || "unavailable"}</b></span>
            <span>Sources checked <b>{dashboard.source_refresh?.source_checked_at ? new Date(dashboard.source_refresh.source_checked_at).toLocaleString("en-IN",{day:"numeric",month:"short",hour:"2-digit",minute:"2-digit",timeZone:"Asia/Kolkata"}) + " IST" : "awaiting first refresh"}</b></span>
            {dashboard.source_refresh?.status !== "ready" && <span role="status">{dashboard.source_refresh?.message}</span>}
            <button className="text-button" disabled={refreshing} onClick={() => void refresh()}><RefreshCw size={14} className={refreshing ? "spin" : ""}/>{refreshing ? "Checking…" : "Check for updates"}</button>
          </div>}
          {view === "promises" ? (
            <PromiseTracker companies={companies} onOpenResearch={ticker => research(ticker, "documents")} />
          ) : view === "research" ? (
            <ResearchWorkspace
              initialTicker={researchTicker}
              initialTab={researchTab}
              initialQuestion={researchQuestion}
              initialDiscovery={researchDiscovery}
              companies={companies}
              onChanged={reload}
            />
          ) : (
            <>
              {view === "home" && (
                <MobileBrief
                  dashboard={dashboard}
                  focus={mobileFocus}
                  onFocus={setMobileFocus}
                  onPriority={() => focusSignals("high")}
                  onAlerts={() => focusSignals("market")}
                  onWatchlist={() => navigate("watchlist")}
                  savedCount={
                    savedSignals.filter((f) => f.mode === mode).length
                  }
                  onSaved={() => {
                    navigate("signals");
                    setSavedOnly(true);
                    setPriority("");
                    setCategory("");
                    setFilterTicker("");
                  }}
                />
              )}
              <div className="page-heading">
                <div>
                  <h1>{view === "home" ? "Your portfolio" : view === "signals" ? "Signals & alerts" : "Watchlist"}</h1>
                </div>
              </div>
              {refreshing && <div className="sync-banner" role="status">
                <Loader2 size={16} className="spin" />
                Checking the latest published source feed…
              </div>}
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
                            <span>Watched companies</span>
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
                            <span>High priority</span>
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
                            <span>Routine filings</span>
                            <strong>
                              {stats?.routine ?? "—"}
                              <small>routine filings</small>
                            </strong>
                          </div>
                          <div className="stat-bottom">
                            <Check size={11} />
                            View routine filings
                          </div>
                        </button>
                      </div>
                      <section className="daily-brief">
                        <span className="brief-icon">
                          <Sparkles size={18} />
                        </span>
                        <div>
                          <div className="brief-label">
                            Daily summary{" "}
                            <span>DATED SOURCE SNAPSHOTS</span>
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
                      <div className="home-market">
                        {(wide||mobileFocus==="market")&&<MarketExplorer
                          quotes={
                            dashboard?.mode === mode ? dashboard.companies : []
                          }
                          mode={mode}
                          onInspect={setSelectedCompany}
                        />}
                        <MobileMovers
                          quotes={
                            dashboard?.mode === mode ? dashboard.companies : []
                          }
                          onInspect={setSelectedCompany}
                        />
                      </div>
                    </>
                  )}
                  {(view === "home" || view === "signals") && (
                    <div className="intelligence-grid">
                      <section className="feed-section">
                        <div className="section-title feed-heading">
                          <div>
                            <h2>
                              {view === "home"
                                ? "Recent NSE filings"
                                : savedOnly
                                  ? "Saved for later"
                                  : "Announcements & alerts"}
                              <span className="count-badge">
                                {feedItems.length}
                              </span>
                            </h2>
                            {savedOnly && <p>Saved on this device · all dates</p>}
                          </div>
                          <button
                            className="phone-feed-actions"
                            aria-label="Filter signals"
                            aria-haspopup="dialog"
                            onClick={() => setFiltersOpen(true)}
                          >
                            <Clock3 size={13} />
                            <span>
                              {savedOnly
                                ? "All saved dates"
                                : windowValue === "24h"
                                  ? "Last 24 hours"
                                  : windowValue === "7d"
                                    ? "Last 7 days"
                                    : windowValue === "30d"
                                      ? "Last 30 days"
                                      : "Custom dates"}
                            </span>
                            <SlidersHorizontal size={16} />
                          </button>
                          <label className="window-select">
                            <Clock3 size={12} />
                            <span className="sr-only">Time window</span>
                            <Select
                              value={windowValue}
                              disabled={savedOnly}
                              aria-label="Time window"
                              onChange={(e) => setWindowValue(e.target.value)}
                            >
                              <option value="24h">Last 24 hours</option>
                              <option value="7d">Last 7 days</option>
                              <option value="30d">Last 30 days</option>
                              <option value="custom">Custom dates</option>
                            </Select>
                            <ChevronDown size={12} />
                          </label>
                        </div>
                        <div className="feed-filters">
                          <div className="filter-scroll">
                            <div className="signal-view-controls" role="group" aria-label="Signal views">
                            <button
                              className={
                                !priority && !savedOnly
                                  ? "filter-chip active"
                                  : "filter-chip"
                              }
                              aria-pressed={!priority && !savedOnly}
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
                              aria-pressed={priority === "high"}
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
                                  savedSignals.filter((f) => view === "signals" || f.mode === filingMode)
                                    .length
                                }
                              </span>
                            </button>
                            </div>
                            <div className="signal-scope-controls">
                            <label className="filter-select">
                              <span className="sr-only">Company filter</span>
                              <Select
                                value={filterTicker}
                                onChange={(e) =>
                                  setFilterTicker(e.target.value)
                                }
                              >
                                <option value="">All companies</option>
                                {companies
                                  .filter((c) => c.watched)
                                  .map((c) => (
                                    <option key={c.ticker} value={c.ticker}>{c.name} · {c.ticker}</option>
                                  ))}
                              </Select>
                              <ChevronDown size={11} />
                            </label>
                            <label className="filter-select">
                              <span className="sr-only">Category filter</span>
                              <Select
                                value={category}
                                onChange={(e) => setCategory(e.target.value)}
                              >
                                <option value="">All categories</option>
                                {filterCategories.map((c) => (
                                  <option key={c} value={c}>
                                    {label(c)}
                                  </option>
                                ))}
                              </Select>
                              <ChevronDown size={11} />
                            </label>
                            </div>
                          </div>
                          <button
                            className="icon-button filter-settings"
                            aria-label="Filter signals"
                            aria-haspopup="dialog"
                            onClick={() => setFiltersOpen(true)}
                          >
                            <SlidersHorizontal size={16} />
                          </button>
                        </div>
                        {windowValue === "custom" && !savedOnly && (
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
                                  <button className="text-button" onClick={()=>void research(a.ticker,"overview",`Review the primary-source business outlook and risks for ${a.ticker} after this ${a.date} completed-session signal: ${a.title}. Do not infer a cause for the market move.`)}>Research this signal<ArrowRight size={14}/></button>
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
                                {dashboard?.stats.coverage ? "No threshold crossings for the saved rules in this snapshot." : "Market alerts are unavailable without verified session data."}
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
                        {!savedOnly && filingMode === "sourced" && (
                          <div className="coverage-summary" role="status">
                            <ShieldCheck size={16} aria-hidden="true" />
                            <p>NSE filing snapshot{filingsAsOf ? ` through ${shortDate(filingsAsOf)}` : ""}. Date ranges end at the latest successful source check.</p>
                          </div>
                        )}
                        <div className="signal-list">
                          {visibleFilings.map((f) => (
                            <SignalCard
                              filing={f}
                              key={`${f.mode}-${f.id}`}
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
                                  ? "No saved signals"
                                  : filingMode === "sourced"
                                    ? "No matching filings"
                                    : "No matching disclosures"}
                              </h3>
                              <p>
                                {savedOnly
                                  ? "Bookmark an announcement to save it in the current data mode."
                                  : filingMode === "sourced"
                                    ? "Try a wider date range or change your filters."
                                    : "No disclosures match these filters. Try a wider window or another category."}
                              </p>
                            </div>
                          )}
                        </div>
                        {!savedOnly &&
                          feedMeta.has_more &&
                          view === "signals" && (
                            <div className="load-more-filings">
                              <p>
                                Showing {filings.length} of {feedMeta.total}{" "}
                                matching filings
                              </p>
                              <button
                                className="btn"
                                disabled={loadingMore}
                                onClick={() => void loadMoreFilings()}
                              >
                                {loadingMore ? (
                                  <Loader2 className="spin" size={15} />
                                ) : (
                                  <Plus size={15} />
                                )}
                                Load more filings
                              </button>
                            </div>
                          )}
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
                              <Select
                                value={chartQuote?.ticker || chartTicker}
                                onChange={(e) => setChartTicker(e.target.value)}
                              >
                                {dashboard?.companies.map((q) => (
                                  <option key={q.ticker} value={q.ticker}>{q.name} · {q.ticker}</option>
                                ))}
                              </Select>
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
                          {wide&&chartQuote?.history.length ? (
                            <PriceChart data={chartQuote.history} />
                          ) : (
                            <div className="chart-empty">
                              Price history is unavailable in this snapshot.
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
                          <h3>Guidance vs. results</h3>
                          {guidanceTeaser && <>
                            <div className="teaser-comparison">
                              <div>
                                <span>ORIGINAL {guidanceTeaser.target_period} GUIDANCE</span>
                                <b>{guidanceTeaser.low}–{guidanceTeaser.high}<span>%</span></b>
                              </div>
                              <ArrowRight size={18} />
                              <div>
                                <span>REPORTED RESULT</span>
                                <b>{guidanceTeaser.actual}<span>%</span></b>
                              </div>
                            </div>
                            <p className="teaser-source">Infosys · {guidanceTeaser.metric} · {guidanceTeaser.target_period}</p>
                          </>}
                          <button onClick={() => navigate("promises")}>
                            Open Promise Tracker
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
                        </div>
                        <button
                          className="btn primary"
                          aria-expanded={addCompanyOpen}
                          aria-haspopup="dialog"
                          aria-controls={addCompanyOpen ? "add-company-dialog" : undefined}
                          onClick={() => setAddCompanyOpen(true)}
                        >
                          <Plus size={14} /> Add company
                        </button>
                      </div>
                      <div className="watch-search-group">
                        <label className="field-label" htmlFor="watchlist-filter">Filter by company, ticker, or sector</label>
                        <div className="watch-search">
                          <Search size={15} aria-hidden="true" />
                          <input
                            id="watchlist-filter"
                            type="search"
                            placeholder="Search watchlist"
                            value={watchSearch}
                            onChange={(e) => setWatchSearch(e.target.value)}
                          />
                        </div>
                      </div>
                      <div className="watch-controls">
                        <label className="phone-sector-filter">
                          Sector
                          <Select value={watchSector} onChange={e=>setWatchSector(e.target.value)}>
                            <option value="">All sectors</option>
                            {Array.from(new Set(companies.map(c=>c.sector))).map(sector=><option key={sector} value={sector}>{sector}</option>)}
                          </Select>
                        </label>
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
                          <Select
                            aria-label="Sort watchlist"
                            value={watchSort}
                            onChange={(e) => setWatchSort(e.target.value)}
                          >
                            <option value="ticker">Company A–Z</option>
                            <option value="gainers">Top gainers</option>
                            <option value="decliners">Top decliners</option>
                            <option value="volume">Unusual volume</option>
                          </Select>
                        </label>
                      </div>
                      <MobileWatchlist
                        companies={watchlist}
                        quotes={dashboard?.companies || []}
                        onInspect={setSelectedCompany}
                        onToggle={(company) => void toggleWatch(company)}
                      />
                      <div className="table-scroll watchlist-desktop-table">
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
                                <tr key={c.ticker} onClick={event => {
                                  if (event.target instanceof Element && !event.target.closest("button, a")) {
                                    event.currentTarget.querySelector("button")?.focus({ preventScroll: true });
                                    setSelectedCompany(c.ticker);
                                  }
                                }}>
                                  <td>
                                    <button
                                      className="watch-company"
                                      aria-haspopup="dialog"
                                      onClick={() => setSelectedCompany(c.ticker)}
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
                      <details className="reading-notes"><summary>Data & calculations</summary><p>
                        {mode === "demo"
                          ? "Synthetic prices for interaction testing. They are not market observations."
                          : "Yahoo Finance historical adjusted closing prices. Each row retains its last completed session date."}{" "}
                        Volume compares the latest session with the preceding{" "}
                        {prefs?.lookback || 20} sessions.
                      </p></details>
                    </section>
                  )}
                </>
              )}
            </>
          )}
        </main>
      </div>
      <nav className="mobile-bottom-nav" aria-label="Mobile navigation" inert={mobileNav&&!wide?true:undefined}>
        {navigation.map((n) => (
          <button
            key={n.id}
            className={view === n.id ? "active" : ""}
            aria-current={view === n.id ? "page" : undefined}
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
                    : n.id === "promises" ? "Promises" : "My brief"}
            </span>
          </button>
        ))}
      </nav>
      {addCompanyOpen && <AddCompanyDialog companies={companies} onAdd={addCompany} onClose={() => setAddCompanyOpen(false)} />}
      {selectedQuote && (
        <CompanyDrawer
          key={selectedQuote.ticker}
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
      {filtersOpen && (
        <FilterSheet
          initial={{
            ticker: filterTicker,
            category,
            priority,
            window: windowValue,
            start: customStart,
            end: customEnd,
          }}
          companies={companies}
          categories={filterCategories}
          savedOnly={savedOnly}
          onClose={closeFilters}
          onApply={(filters) => {
            setFilterTicker(filters.ticker);
            setCategory(filters.category);
            setPriority(filters.priority);
            setRoutine(filters.priority === "low");
            setWindowValue(filters.window);
            setCustomStart(filters.start);
            setCustomEnd(filters.end);
            setFiltersOpen(false);
          }}
        />
      )}
      {notificationsOpen && (
        <Notifications
          feed={notificationFeed}
          mode={mode}
          onClose={closeNotifications}
          onChanged={reload}
          onResearch={research}
        />
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
