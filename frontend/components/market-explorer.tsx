"use client";

import { useEffect, useId, useRef, useState } from "react";
import {
  Activity,
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  BarChart3,
  ChevronDown,
  ExternalLink,
  Search,
  ShieldCheck,
  TrendingUp,
  X,
} from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Company, Mode, Quote, money, number, pct } from "@/lib/api";

function HistoryChart({
  quote,
  sessions,
  metric,
}: {
  quote: Quote;
  sessions: number;
  metric: "price" | "volume";
}) {
  const id = useId().replaceAll(":", "");
  const data = quote.history.slice(-sessions);
  const common = { data, margin: { top: 14, right: 16, left: 0, bottom: 0 } };
  const axes = (
    <>
      <CartesianGrid vertical={false} stroke="#edf0f4" strokeDasharray="3 6" />
      <XAxis
        dataKey="date"
        axisLine={false}
        tickLine={false}
        minTickGap={40}
        tick={{ fill: "#8993a2", fontSize: 11 }}
        tickFormatter={(d) =>
          new Date(`${d}T12:00:00`).toLocaleDateString("en-IN", {
            day: "numeric",
            month: "short",
          })
        }
      />
      <YAxis
        axisLine={false}
        tickLine={false}
        width={62}
        domain={metric === "price" ? ["auto", "auto"] : [0, "auto"]}
        tick={{ fill: "#8993a2", fontSize: 11 }}
        tickFormatter={(v) =>
          metric === "volume"
            ? `${(Number(v) / 1e6).toFixed(1)}M`
            : Number(v).toLocaleString("en-IN", { maximumFractionDigits: 0 })
        }
      />
      <Tooltip
        cursor={{ stroke: "#b7c5d3", strokeDasharray: "3 3" }}
        contentStyle={{
          border: "1px solid #e6eaf0",
          borderRadius: 12,
          boxShadow: "0 10px 32px #0c1c3312",
          fontSize: 12,
        }}
        labelStyle={{ color: "#708095", marginBottom: 6 }}
        formatter={(v) => [
          metric === "price" ? money(Number(v)) : number(Number(v)),
          metric === "price" ? "Adjusted close" : "Shares traded",
        ]}
      />
    </>
  );
  return (
    <div
      className="explorer-chart"
      role="img"
      aria-label={`${quote.ticker} ${metric} over ${data.length} completed sessions`}
    >
      <ResponsiveContainer width="100%" height="100%">
        {metric === "price" ? (
          <AreaChart {...common}>
            <defs>
              <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#a7d858" stopOpacity={0.26} />
                <stop offset="100%" stopColor="#a7d858" stopOpacity={0} />
              </linearGradient>
            </defs>
            {axes}
            <Area
              dataKey="close"
              type="monotone"
              stroke="#4b8055"
              strokeWidth={2.5}
              fill={`url(#${id})`}
              isAnimationActive={false}
              activeDot={{ r: 5, stroke: "white", strokeWidth: 3 }}
            />
          </AreaChart>
        ) : (
          <BarChart {...common}>
            {axes}
            <Bar
              dataKey="volume"
              fill="#92b978"
              radius={[3, 3, 0, 0]}
              isAnimationActive={false}
            />
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}

export function MarketExplorer({
  quotes,
  mode,
  onInspect,
}: {
  quotes: Quote[];
  mode: Mode;
  onInspect: (ticker: string) => void;
}) {
  const [ticker, setTicker] = useState("RELIANCE");
  const [sessions, setSessions] = useState(22);
  const [metric, setMetric] = useState<"price" | "volume">("price");
  const quote = quotes.find((q) => q.ticker === ticker) || quotes[0];
  const windowData = quote?.history.slice(-sessions) || [];
  const first =
    metric === "price" ? windowData[0]?.close : windowData[0]?.volume;
  const last =
    metric === "price" ? windowData.at(-1)?.close : windowData.at(-1)?.volume;
  const change = first && last ? ((last - first) / first) * 100 : null;
  const gainers = quotes.filter(
    (q) => q.change_pct !== null && q.change_pct > 0,
  ).length;
  const decliners = quotes.filter(
    (q) => q.change_pct !== null && q.change_pct < 0,
  ).length;
  const available = quotes.filter((q) => q.change_pct !== null).length;
  return (
    <section
      className="market-explorer"
      aria-label="Interactive market explorer"
    >
      <div className="explorer-main">
        <div className="explorer-heading">
          <div>
            <div className="eyebrow">THE BIGGER PICTURE</div>
            <h2>
              Portfolio pulse
              <span className="live-dot" />
            </h2>
          </div>
          <div className="segmented-control" aria-label="Chart metric">
            {(
              [
                ["price", "Price"],
                ["volume", "Volume"],
              ] as const
            ).map(([id, title]) => (
              <button
                key={id}
                aria-pressed={metric === id}
                className={metric === id ? "selected" : ""}
                onClick={() => setMetric(id)}
              >
                {id === "price" ? (
                  <TrendingUp size={13} />
                ) : (
                  <BarChart3 size={13} />
                )}{" "}
                {title}
              </button>
            ))}
          </div>
        </div>
        <div className="explorer-value">
          <div>
            <label className="explorer-company">
              <span className="sr-only">Explorer company</span>
              <select
                value={quote?.ticker || ""}
                onChange={(e) => setTicker(e.target.value)}
              >
                {quotes.map((q) => (
                  <option key={q.ticker} value={q.ticker}>
                    {q.ticker}
                  </option>
                ))}
              </select>
              <ChevronDown size={13} />
            </label>
            <div>
              <strong>
                {metric === "price"
                  ? money(quote?.close ?? null)
                  : quote?.volume
                    ? `${(quote.volume / 1e6).toFixed(2)}M`
                    : "—"}
              </strong>
              <span
                className={`period-change ${(change || 0) >= 0 ? "up" : "down"}`}
              >
                {(change || 0) >= 0 ? (
                  <ArrowUpRight size={14} />
                ) : (
                  <ArrowDownRight size={14} />
                )}{" "}
                {pct(change)}
                <small>in selected period</small>
              </span>
            </div>
          </div>
          <div className="chart-ranges" aria-label="Chart time range">
            {[
              [5, "1W"],
              [22, "1M"],
              [65, "3M"],
            ].map(([n, title]) => (
              <button
                key={n}
                aria-pressed={sessions === n}
                onClick={() => setSessions(Number(n))}
                className={sessions === n ? "selected" : ""}
              >
                {title}
              </button>
            ))}
          </div>
        </div>
        {quote?.history.length ? (
          <HistoryChart
            key={`${mode}-${quote.ticker}-${metric}`}
            quote={quote}
            sessions={sessions}
            metric={metric}
          />
        ) : (
          <div className="explorer-chart chart-no-data">
            <Activity size={25} />
            <p>No completed sessions yet. Refresh sources to load a chart.</p>
          </div>
        )}
        <div className="explorer-footer">
          <span>
            <ShieldCheck size={12} />
            {mode === "demo"
              ? "Simulated market history"
              : "Yahoo Finance · Adjusted daily closes"}
            {quote?.date && ` · ${quote.date}`}
          </span>
          <button onClick={() => quote && onInspect(quote.ticker)}>
            Company details
            <ArrowUpRight size={13} />
          </button>
        </div>
      </div>
      <aside className="breadth-panel">
        <div className="breadth-heading">
          <span className="breadth-icon">
            <Activity size={18} />
          </span>
          <span>WATCHLIST BREADTH</span>
        </div>
        <h3>
          A feel for
          <br />
          <em>the day’s direction.</em>
        </h3>
        <div className="breadth-numbers">
          <div>
            <b>{gainers.toString().padStart(2, "0")}</b>
            <span>
              <i className="up-dot" /> Advancing
            </span>
          </div>
          <div>
            <b>{decliners.toString().padStart(2, "0")}</b>
            <span>
              <i className="down-dot" /> Declining
            </span>
          </div>
        </div>
        <div
          className="breadth-bar"
          aria-label={`${gainers} advancing and ${decliners} declining`}
        >
          <i
            style={{ width: `${available ? (gainers / available) * 100 : 0}%` }}
          />
          <i
            style={{
              width: `${available ? (decliners / available) * 100 : 0}%`,
            }}
          />
        </div>
        <p>
          Based on the latest available completed session for each watched
          company.
        </p>
        <div className="breadth-bottom">
          <span>
            {available} / {quotes.length} with daily changes
          </span>
          <span>{mode === "demo" ? "DEMO" : "EOD"}</span>
        </div>
      </aside>
    </section>
  );
}

export function CompanyDrawer({
  quote,
  mode,
  onClose,
  onResearch,
}: {
  quote: Quote;
  mode: Mode;
  onClose: () => void;
  onResearch: (ticker: string) => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [sessions, setSessions] = useState(22);
  useEffect(() => {
    const old = document.activeElement as HTMLElement;
    const root = ref.current;
    root?.querySelector<HTMLButtonElement>("button")?.focus();
    function key(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
      if (e.key === "Tab" && root) {
        const elements = root.querySelectorAll<HTMLElement>(
          "button:not(:disabled),a[href]",
        );
        const first = elements[0],
          last = elements[elements.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last?.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first?.focus();
        }
      }
    }
    document.addEventListener("keydown", key);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", key);
      document.body.style.overflow = "";
      old?.focus();
    };
  }, [onClose]);
  return (
    <div
      className="company-backdrop"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={ref}
        role="dialog"
        aria-modal="true"
        aria-labelledby="company-detail-title"
        className="company-drawer"
      >
        <div className="drawer-top">
          <span>
            <span className="live-dot" /> COMPANY BRIEF
          </span>
          <button aria-label="Close company details" onClick={onClose}>
            <X size={20} />
          </button>
        </div>
        <div className="drawer-company-icon">{quote.ticker.slice(0, 2)}</div>
        <div className="eyebrow">{quote.ticker} · NSE</div>
        <h2 id="company-detail-title">{quote.name}</h2>
        <p className="drawer-sector">{quote.sector}</p>
        <div className="drawer-price">
          <strong>{money(quote.close)}</strong>
          <span
            className={(quote.change_pct || 0) >= 0 ? "positive" : "negative"}
          >
            {pct(quote.change_pct)} <small>latest session</small>
          </span>
        </div>
        <div className="drawer-chart-title">
          <h3>Price history</h3>
          <div className="chart-ranges">
            {[
              [5, "1W"],
              [22, "1M"],
              [65, "3M"],
            ].map(([n, title]) => (
              <button
                className={sessions === n ? "selected" : ""}
                aria-pressed={sessions === n}
                onClick={() => setSessions(Number(n))}
                key={n}
              >
                {title}
              </button>
            ))}
          </div>
        </div>
        {quote.history.length ? (
          <HistoryChart quote={quote} sessions={sessions} metric="price" />
        ) : (
          <div className="notice-banner">
            No sourced market sessions are available for this company.
          </div>
        )}
        <div className="drawer-metrics">
          <div>
            <span>Trading volume</span>
            <b>{quote.volume === null ? "—" : number(quote.volume)}</b>
          </div>
          <div>
            <span>Volume vs. baseline</span>
            <b>
              {quote.volume_ratio === null
                ? "—"
                : `${quote.volume_ratio.toFixed(2)}×`}
            </b>
          </div>
          <div>
            <span>Latest session</span>
            <b>{quote.date || "Unavailable"}</b>
          </div>
          <div>
            <span>Data type</span>
            <b>{mode === "demo" ? "Simulated replay" : "Sourced EOD"}</b>
          </div>
        </div>
        <div className="drawer-note">
          <ShieldCheck size={17} />
          <p>
            {mode === "demo"
              ? "This is a simulated price scenario for the demonstration."
              : "Historical adjusted closes from Yahoo Finance, not live quotes."}{" "}
            Research uses company-issued primary documents.
          </p>
        </div>
        <button
          className="btn primary drawer-research"
          onClick={() => onResearch(quote.ticker)}
        >
          Research {quote.ticker}
          <ArrowRight size={16} />
        </button>
        {mode === "sourced" && quote.source_url && (
          <a
            className="drawer-source"
            href={quote.source_url}
            target="_blank"
            rel="noreferrer"
          >
            Open original price history
            <ExternalLink size={13} />
          </a>
        )}
      </div>
    </div>
  );
}

export function CompanySearch({
  companies,
  onSelect,
}: {
  companies: Company[];
  onSelect: (ticker: string) => void;
}) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const input = useRef<HTMLInputElement>(null);
  const results = companies
    .filter((c) =>
      `${c.ticker} ${c.name}`.toLowerCase().includes(query.toLowerCase()),
    )
    .slice(0, 6);
  useEffect(() => {
    function shortcut(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        input.current?.focus();
        setOpen(true);
      }
    }
    document.addEventListener("keydown", shortcut);
    return () => document.removeEventListener("keydown", shortcut);
  }, []);
  function select(t: string) {
    onSelect(t);
    setQuery("");
    setOpen(false);
  }
  return (
    <div
      className="company-search-wrap"
      onBlur={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget as Node)) setOpen(false);
      }}
    >
      <form
        className="global-search"
        onSubmit={(e) => {
          e.preventDefault();
          const match = results[active];
          if (match) select(match.ticker);
          else if (query.trim())
            select(query.trim().toUpperCase().replace(/\.NS$/, ""));
        }}
      >
        <Search size={16} />
        <input
          ref={input}
          aria-label="Search companies"
          aria-expanded={open}
          aria-controls="company-search-results"
          aria-activedescendant={
            open && results[active]
              ? `search-${results[active].ticker}`
              : undefined
          }
          role="combobox"
          autoComplete="off"
          placeholder="Search a company…"
          value={query}
          onFocus={() => setOpen(true)}
          onChange={(e) => {
            setQuery(e.target.value);
            setActive(0);
          }}
          onKeyDown={(e) => {
            if (e.key === "Escape") setOpen(false);
            if (e.key === "ArrowDown") {
              e.preventDefault();
              setActive((i) => Math.min(i + 1, results.length - 1));
            }
            if (e.key === "ArrowUp") {
              e.preventDefault();
              setActive((i) => Math.max(i - 1, 0));
            }
          }}
        />
        <kbd>Ctrl K</kbd>
      </form>
      {open && (
        <div
          className="search-results"
          id="company-search-results"
          role="listbox"
        >
          <div className="search-results-label">
            {query ? "COMPANIES" : "QUICK RESEARCH"}
          </div>
          {results.map((c, i) => (
            <button
              type="button"
              role="option"
              aria-selected={i === active}
              className={i === active ? "active" : ""}
              id={`search-${c.ticker}`}
              key={c.ticker}
              onMouseEnter={() => setActive(i)}
              onClick={() => select(c.ticker)}
            >
              <span className="search-company-icon">
                {c.ticker.slice(0, 2)}
              </span>
              <span>
                <b>{c.ticker}</b>
                <small>{c.name}</small>
              </span>
              <ArrowUpRight size={14} />
            </button>
          ))}
          {!results.length && (
            <button
              type="button"
              className="search-new"
              onClick={() => select(query.trim().toUpperCase())}
            >
              Research “{query}”<ArrowRight size={14} />
            </button>
          )}
          <div className="search-tip">
            ↑ ↓ to navigate <span>↵ to open</span>
          </div>
        </div>
      )}
    </div>
  );
}
