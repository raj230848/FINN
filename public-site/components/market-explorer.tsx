"use client";
import {Select} from "@/components/select";

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
import {CompanyLookup} from "./company-lookup";

type ChartMetric = "price" | "volume";
const timeRanges = [[5, "1W"], [22, "1M"], [65, "3M"]] as const;

function ChartMetricPicker({ metric, onChange }: { metric: ChartMetric; onChange: (metric: ChartMetric) => void }) {
  return (
    <div className="segmented-control" role="group" aria-label="Chart metric">
      <button aria-pressed={metric === "price"} className={metric === "price" ? "selected" : ""} onClick={() => onChange("price")}>
        <TrendingUp size={13} /> Price
      </button>
      <button aria-pressed={metric === "volume"} className={metric === "volume" ? "selected" : ""} onClick={() => onChange("volume")}>
        <BarChart3 size={13} /> Volume
      </button>
    </div>
  );
}

function ChartTimeRange({ sessions, onChange }: { sessions: number; onChange: (sessions: number) => void }) {
  return (
    <div className="chart-ranges" role="group" aria-label="Chart time range">
      {timeRanges.map(([count, title]) => (
        <button key={count} aria-pressed={sessions === count} className={sessions === count ? "selected" : ""} onClick={() => onChange(count)}>
          {title}
        </button>
      ))}
    </div>
  );
}

function HistoryChart({
  quote,
  sessions,
  metric,
}: {
  quote: Quote;
  sessions: number;
  metric: ChartMetric;
}) {
  const id = useId().replaceAll(":", "");
  const data = quote.history.slice(-sessions);
  const common = { data, margin: { top: 14, right: 16, left: 0, bottom: 0 } };
  const axes = (
    <>
      <CartesianGrid vertical={false} stroke="var(--chart-grid)" strokeDasharray="3 6" />
      <XAxis
        dataKey="date"
        axisLine={false}
        tickLine={false}
        minTickGap={40}
        tick={{ fill: "var(--text-muted)", fontSize: 11 }}
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
        tick={{ fill: "var(--text-muted)", fontSize: 11 }}
        tickFormatter={(v) =>
          metric === "volume"
            ? `${(Number(v) / 1e6).toFixed(1)}M`
            : Number(v).toLocaleString("en-IN", { maximumFractionDigits: 0 })
        }
      />
      <Tooltip
        cursor={{ stroke: "var(--text-muted)", strokeDasharray: "3 3" }}
        contentStyle={{
          border: "1px solid var(--border-strong)",
          borderRadius: 12,
          backgroundColor: "var(--surface-raised)",
          color: "var(--text)",
          boxShadow: "0 10px 32px var(--shadow)",
          fontSize: 12,
        }}
        labelStyle={{ color: "var(--text-secondary)", marginBottom: 6 }}
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
                <stop offset="0%" stopColor="var(--chart-line)" stopOpacity={0.26} />
                <stop offset="100%" stopColor="var(--chart-line)" stopOpacity={0} />
              </linearGradient>
            </defs>
            {axes}
            <Area
              dataKey="close"
              type="linear"
              stroke="var(--chart-line)"
              strokeWidth={2.5}
              fill={`url(#${id})`}
              isAnimationActive={false}
              dot={data.length === 1}
              activeDot={{ r: 5, stroke: "var(--surface)", strokeWidth: 3 }}
            />
          </AreaChart>
        ) : (
          <BarChart {...common}>
            {axes}
            <Bar
              dataKey="volume"
              fill="var(--primary)"
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
  const [metric, setMetric] = useState<ChartMetric>("price");
  const quote = quotes.find((q) => q.ticker === ticker) || quotes[0];
  const windowData = quote?.history.slice(-sessions) || [];
  const first =
    metric === "price" ? windowData[0]?.close : windowData[0]?.volume;
  const last =
    metric === "price" ? windowData.at(-1)?.close : windowData.at(-1)?.volume;
  const change = windowData.length > 1 && first && last != null ? ((last - first) / first) * 100 : null;
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
            <h2>
              Portfolio pulse
              <span className="live-dot" />
            </h2>
          </div>
          <ChartMetricPicker metric={metric} onChange={setMetric} />
        </div>
        <div className="explorer-value">
          <div>
            <label className="explorer-company">
              <span className="sr-only">Explorer company</span>
              <Select
                value={quote?.ticker || ""}
                onChange={(e) => setTicker(e.target.value)}
              >
                {quotes.map((q) => (
                  <option key={q.ticker} value={q.ticker}>
                    {q.name} · {q.ticker}
                  </option>
                ))}
              </Select>
              <ChevronDown size={13} />
            </label>
            <div>
              <strong>
                {metric === "price"
                  ? money(quote?.close ?? null)
                  : quote?.volume != null
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
          <ChartTimeRange sessions={sessions} onChange={setSessions} />
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
            <p>No verified market history is available in this snapshot.</p>
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
        <p>Latest completed sessions</p>
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
  const [metric, setMetric] = useState<ChartMetric>("price");
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
          <strong>{metric === "price" ? money(quote.close) : quote.volume === null ? "—" : number(quote.volume)}</strong>
          <span
            className={(quote.change_pct || 0) >= 0 ? "positive" : "negative"}
          >
            {metric === "price" ? pct(quote.change_pct) : "shares traded"} <small>latest session</small>
          </span>
        </div>
        <div className="drawer-chart-title">
          <h3>{metric === "price" ? "Price history" : "Volume history"}</h3>
          <ChartMetricPicker metric={metric} onChange={setMetric} />
          <ChartTimeRange sessions={sessions} onChange={setSessions} />
        </div>
        {quote.history.length ? (
          <HistoryChart key={metric} quote={quote} sessions={sessions} metric={metric} />
        ) : (
          <div className="notice-banner">
            {quote.watched === false ? "Add this company to your watchlist to display available history." : "No completed market sessions are available yet."}
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
            Open market data source
            <ExternalLink size={13} />
          </a>
        )}
      </div>
    </div>
  );
}

export function CompanySearch({companies,onSelect}:{companies:Company[];onSelect:(ticker:string,tab?:string)=>void|Promise<void>}) {
  return <CompanyLookup compact companies={companies} onSelect={c=>onSelect(c.ticker,"documents")}/>;
}
