export type Mode = "demo" | "sourced";
export type Company = {
  ticker: string;
  name: string;
  sector: string;
  watched: boolean;
  verified: boolean;
  website: string;
};
export type PricePoint = { date: string; close: number; volume: number };
export type Quote = Company & {
  close: number | null;
  change_pct: number | null;
  volume_ratio: number | null;
  volume: number | null;
  date: string | null;
  fetched_at: string | null;
  source_url: string | null;
  history: PricePoint[];
};
export type Filing = {
  id: number;
  ticker: string;
  title: string;
  published_at: string;
  category: string;
  priority: string;
  score: number;
  factors: string[];
  summary: string;
  why_matters: string;
  source_url: string | null;
  analysis_method: string;
  mode: Mode;
  needs_review?: boolean;
};
export type Alert = {
  id: number;
  ticker: string;
  kind: string;
  title: string;
  explanation: string;
  value: number;
  threshold: number;
  date: string;
  mode: Mode;
  source_url: string | null;
};
export type SyncRun = {
  id: number;
  started_at: string;
  completed_at: string | null;
  result: {
    status?: string;
    message?: string;
    prices?: Record<
      string,
      {
        ok: boolean;
        error?: string;
        sessions?: number;
        latest_session?: string;
      }
    >;
    announcements?: { ok: boolean; error?: string; inserted?: number };
  };
};
export type Dashboard = {
  mode: Mode;
  as_of: string;
  companies: Quote[];
  stats: {
    companies: number;
    high_priority: number;
    volume_alerts: number;
    price_alerts: number;
    routine: number;
    total_filings: number;
    coverage: number;
  };
  digest: string;
  last_sync: SyncRun | null;
  ai_configured: boolean;
  scheduler_enabled: boolean;
};
export type Prefs = {
  price_threshold: number;
  volume_multiplier: number;
  lookback: number;
  companies: string[];
  categories: string[];
  available_categories?: string[];
};
export type SourceDocument = {
  id: number;
  ticker: string;
  title: string;
  period: string;
  kind: string;
  source_url: string;
  page_count: number;
  fetched_at: string;
};
export type Candidate = {
  url: string;
  title: string;
  period: string;
  kind: string;
};
export type Evidence = {
  id: number;
  document_id: number;
  title: string;
  period: string;
  page: number;
  url: string;
  excerpt: string;
  score: number;
};
export type Research = {
  ticker: string;
  question: string;
  answer: string;
  evidence: Evidence[];
  method: string;
  limitations: string[];
  cached: boolean;
};
export type Financials = {
  periods?: string[];
  review_flags?: string[];
  history?: {period: string; basis: string; currency: string; metrics: Record<string, unknown>; source_url: string; page: number}[];
  rows: {
    metric: string;
    current: number | null;
    previous: number | null;
    last_year: number | null;
    qoq: number | null;
    yoy: number | null;
  }[];
  current_period?: string;
  previous_period?: string;
  last_year_period?: string;
  basis?: string;
  currency?: string;
  sources?: { source_url: string; page: number; period: string }[];
  note?: string;
  message?: string;
};
export type GuidanceItem = {
  ticker: string;
  revision: string;
  statement_date: string;
  target_period: string;
  metric: string;
  unit: string;
  low: number;
  high: number;
  actual: number | null;
  statement: string;
  guidance_url: string;
  guidance_page: number;
  actual_url: string | null;
  actual_page: number | null;
  status: string;
  deviation_pp: number | null;
  midpoint_deviation_pp: number | null;
  basis?: string;
};
export type Coverage = {
  unknown_ingestion_dates?: number;
  partial_coverage: boolean;
  kind: string;
  message: string;
  first_observed_at?: string | null;
  last_successful_fetch_at?: string | null;
};
export type FilingFeed = {
  items: Filing[];
  routine_count: number;
  total?: number;
  has_more?: boolean;
  next_offset?: number | null;
  coverage?: Coverage;
};
export type NotificationEvent = {
  id: number;
  ticker: string;
  mode: Mode;
  kind: string;
  severity: string;
  title: string;
  explanation: string;
  source_url: string | null;
  occurred_at: string;
  created_at: string;
  read_at: string | null;
};
export type NotificationFeed = {
  items: NotificationEvent[];
  unread_count: number;
  total: number;
  has_more: boolean;
};
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
  ) {
    super(message);
  }
}
export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  const data = await response.json();
  if (!response.ok)
    throw new ApiError(
      typeof data.detail === "string"
        ? data.detail
        : "The request could not be validated. Check the fields and try again.",
      response.status,
      data.code,
    );
  return data as T;
}
export const money = (value: number | null) =>
  value === null
    ? "—"
    : new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 2,
      }).format(value);
export const number = (value: number | null) =>
  value === null
    ? "—"
    : new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 }).format(
        value,
      );
export const pct = (value: number | null) =>
  value === null ? "—" : `${value > 0 ? "+" : ""}${value.toFixed(2)}%`;
export const label = (value: string) =>
  value === "M&A"
    ? value
    : value.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
export function shortDate(value: string) {
  return new Date(value).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    timeZone: "Asia/Kolkata",
  });
}
