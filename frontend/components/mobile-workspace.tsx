"use client";
import {Select} from "@/components/select";

import { useEffect, useRef, useState } from "react";
import {
  ArrowUpRight,
  Bookmark,
  ChevronDown,
  RefreshCw,
  SlidersHorizontal,
  Sparkles,
  X,
} from "lucide-react";
import { Dashboard, Company, label, money, pct, Quote } from "@/lib/api";

export function MobileWatchlist({
  companies,
  quotes,
  onInspect,
  onToggle,
}: {
  companies: Company[];
  quotes: Quote[];
  onInspect: (ticker: string) => void;
  onToggle: (company: Company) => void;
}) {
  return (
    <div className="phone-watchlist">
      {companies.map((c) => {
        const quote = quotes.find((q) => q.ticker === c.ticker);
        return (
          <article key={c.ticker} onClick={event => {
            if (event.target instanceof Element && !event.target.closest("button, a")) {
              event.currentTarget.querySelector("button")?.focus({ preventScroll: true });
              onInspect(c.ticker);
            }
          }}>
            <button
              className="phone-watch-company"
              aria-haspopup="dialog"
              onClick={() => onInspect(c.ticker)}
            >
              <span className="mover-mark">{c.ticker.slice(0, 2)}</span>
              <span>
                <b>{c.ticker}</b>
                <small>{c.name}</small>
              </span>
              <ArrowUpRight size={17} />
            </button>
            <div className="phone-watch-quote">
              <div>
                <strong>{money(quote?.close ?? null)}</strong>
                <span>{quote?.date || "No cached sessions"}</span>
              </div>
              <div>
                <b
                  className={
                    (quote?.change_pct || 0) >= 0 ? "positive" : "negative"
                  }
                >
                  {pct(quote?.change_pct ?? null)}
                </b>
                <span>
                  {quote?.volume_ratio == null
                    ? "Volume unavailable"
                    : `${quote.volume_ratio.toFixed(2)}× volume`}
                </span>
              </div>
            </div>
            <footer>
              <span>{c.sector}</span>
              <button
                aria-label={`${c.watched ? "Remove" : "Add"} ${c.ticker} ${c.watched ? "from" : "to"} watchlist`}
                aria-pressed={c.watched}
                onClick={() => onToggle(c)}
              >
                <Bookmark
                  size={15}
                  fill={c.watched ? "currentColor" : "none"}
                />
                {c.watched ? "Watching" : "Watch"}
              </button>
            </footer>
          </article>
        );
      })}
    </div>
  );
}

export function MobileBrief({
  dashboard,
  focus,
  onFocus,
  onSaved,
  onPriority,
  onAlerts,
  onWatchlist,
  onRefresh,
  refreshing,
  savedCount,
}: {
  dashboard: Dashboard | null;
  focus: "brief" | "market";
  onFocus: (focus: "brief" | "market") => void;
  onSaved: () => void;
  onPriority: () => void;
  onAlerts: () => void;
  onWatchlist: () => void;
  onRefresh: () => void;
  refreshing: boolean;
  savedCount: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const stats = dashboard?.stats;
  return (
    <section className="phone-brief" aria-label="Your daily brief">
      <div className="phone-greeting">
        <div>
          <span>
            YOUR DAILY BRIEF ·{" "}
            {dashboard
              ? new Date(dashboard.as_of).toLocaleDateString("en-IN", {
                  day: "numeric",
                  month: "short",
                  timeZone: "Asia/Kolkata",
                })
              : "TODAY"}
          </span>
          <h1>Your portfolio</h1>
        </div>
        <button
          className="phone-refresh"
          aria-label={dashboard?.mode==="demo"?"Replay example":"Refresh sources"}
          disabled={refreshing}
          onClick={onRefresh}
        >
          <RefreshCw size={19} className={refreshing ? "spin" : ""} />
        </button>
      </div>
      <div className="phone-counts">
        <button onClick={onPriority}>
          <strong>
            {stats?.high_priority ?? "—"}
            <i />
          </strong>
          <span>Priority signals</span>
        </button>
        <button onClick={onAlerts}>
          <strong>
            {(stats?.price_alerts || 0) + (stats?.volume_alerts || 0)}
            <ArrowUpRight size={16} />
          </strong>
          <span>Market alerts</span>
        </button>
        <button onClick={onWatchlist}>
          <strong>
            {stats?.companies ?? "—"}
            <ArrowUpRight size={16} />
          </strong>
          <span>Companies</span>
        </button>
      </div>
      <div className={`phone-digest ${expanded ? "expanded" : ""}`}>
        <div className="phone-digest-label">
          <Sparkles size={14} />
          <span>Daily summary</span>
          {dashboard?.mode === "demo" && <small>SIMULATED</small>}
        </div>
        <p>{dashboard?.digest || "Preparing your portfolio brief…"}</p>
        <button onClick={() => setExpanded(!expanded)} aria-expanded={expanded}>
          {expanded ? "Less detail" : "Read the brief"}
          <ChevronDown size={14} />
        </button>
      </div>
      <div className="phone-view-switch" aria-label="Overview view">
        <button
          aria-pressed={focus === "brief"}
          onClick={() => onFocus("brief")}
        >
          My brief
        </button>
        <button
          aria-pressed={focus === "market"}
          onClick={() => onFocus("market")}
        >
          The market
        </button>
        <button onClick={onSaved}>
          <Bookmark size={14} />
          Saved <small>{savedCount}</small>
        </button>
      </div>
    </section>
  );
}

export function MobileMovers({
  quotes,
  onInspect,
}: {
  quotes: Quote[];
  onInspect: (ticker: string) => void;
}) {
  return (
    <section className="phone-movers">
      <div>
        <h2>Daily movers</h2>
        <span>Largest daily moves · EOD</span>
      </div>
      {[...quotes]
        .filter((q) => q.change_pct !== null)
        .sort((a, b) => Math.abs(b.change_pct!) - Math.abs(a.change_pct!))
        .slice(0, 6)
        .map((q) => (
          <button key={q.ticker} onClick={() => onInspect(q.ticker)}>
            <span className="mover-mark">{q.ticker.slice(0, 2)}</span>
            <span>
              <b>{q.ticker}</b>
              <small>{q.name}</small>
            </span>
            <span>
              <b>{money(q.close)}</b>
              <small
                className={(q.change_pct || 0) >= 0 ? "positive" : "negative"}
              >
                {pct(q.change_pct)}
              </small>
            </span>
            <ArrowUpRight size={16} />
          </button>
        ))}
    </section>
  );
}

export type FeedFilters = {
  ticker: string;
  category: string;
  priority: string;
  window: string;
  start: string;
  end: string;
};
export function FilterSheet({
  initial,
  companies,
  categories,
  savedOnly,
  onClose,
  onApply,
}: {
  initial: FeedFilters;
  companies: Company[];
  categories: string[];
  savedOnly: boolean;
  onClose: () => void;
  onApply: (filters: FeedFilters) => void;
}) {
  const [draft, setDraft] = useState(initial);
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    ref.current?.querySelector<HTMLButtonElement>("button")?.focus();
    const handle = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "Tab") {
        const items = ref.current?.querySelectorAll<HTMLElement>(
          "button:not(:disabled),select:not(:disabled),input:not(:disabled)",
        );
        if (!items?.length) return;
        const first = items[0],
          last = items[items.length - 1];
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
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handle);
      previous?.focus();
    };
  }, [onClose]);
  function field(key: keyof FeedFilters, value: string) {
    setDraft((d) => ({ ...d, [key]: value }));
  }
  return (
    <div
      className="filter-backdrop"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="feed-filter-sheet"
        role="dialog"
        aria-modal="true"
        aria-labelledby="filter-title"
        ref={ref}
      >
        <div className="sheet-handle" />
        <header>
          <div>
            <h2 id="filter-title">
              <SlidersHorizontal size={20} />
              Filter your brief
            </h2>
          </div>
          <button onClick={onClose} aria-label="Close filters">
            <X size={21} />
          </button>
        </header>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            onApply(draft);
          }}
        >
          <label>
            Time window
            <Select
              value={draft.window}
              disabled={savedOnly}
              onChange={(e) => field("window", e.target.value)}
            >
              <option value="24h">Last 24 hours</option>
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="custom">Custom dates</option>
            </Select>
          </label>
          {savedOnly && (
            <p className="sheet-note">Saved insights include all dates.</p>
          )}
          {draft.window === "custom" && !savedOnly && (
            <div className="sheet-dates">
              <label>
                From
                <input
                  required
                  type="date"
                  value={draft.start}
                  onChange={(e) => field("start", e.target.value)}
                />
              </label>
              <label>
                To
                <input
                  required
                  type="date"
                  min={draft.start}
                  value={draft.end}
                  onChange={(e) => field("end", e.target.value)}
                />
              </label>
            </div>
          )}
          <label>
            Company
            <Select
              value={draft.ticker}
              onChange={(e) => field("ticker", e.target.value)}
            >
              <option value="">All watched companies</option>
              {companies
                .filter((c) => c.watched)
                .map((c) => (
                  <option key={c.ticker} value={c.ticker}>
                    {c.ticker} · {c.name}
                  </option>
                ))}
            </Select>
          </label>
          <label>
            Announcement type
            <Select
              value={draft.category}
              onChange={(e) => field("category", e.target.value)}
            >
              <option value="">All categories</option>
              {categories.map((c) => (
                <option key={c} value={c}>
                  {label(c)}
                </option>
              ))}
            </Select>
          </label>
          <label>
            Priority
            <Select
              value={draft.priority}
              onChange={(e) => field("priority", e.target.value)}
            >
              <option value="">All priorities</option>
              <option value="high">High priority</option>
              <option value="medium">Medium priority</option>
              <option value="low">Low priority</option>
            </Select>
          </label>
          <footer>
            <button
              type="button"
              onClick={() =>
                setDraft({
                  ...initial,
                  ticker: "",
                  category: "",
                  priority: "",
                  window: "24h",
                })
              }
            >
              Reset
            </button>
            <button className="btn primary" type="submit">
              Apply filters
              <ArrowUpRight size={16} />
            </button>
          </footer>
        </form>
      </div>
    </div>
  );
}
