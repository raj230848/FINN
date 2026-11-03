"use client";
import { useEffect, useRef, useState } from "react";
import { Bell, Check, ExternalLink, X } from "lucide-react";
import { api, Mode, NotificationFeed, NotificationEvent, shortDate } from "@/lib/api";
import { BrowserPush } from "./browser-push";

export function Notifications({
  feed,
  mode,
  onClose,
  onChanged,
  onResearch,
}: {
  feed: NotificationFeed;
  mode: Mode;
  onClose: () => void;
  onChanged: () => void;
  onResearch: (ticker: string,tab?:string,question?:string) => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [extra,setExtra]=useState<NotificationEvent[]>([]);
  const [hasMore,setHasMore]=useState(feed.has_more);
  useEffect(()=>{setExtra([]);setHasMore(feed.has_more);},[feed,mode]);
  async function loadMore(){
    setBusy(true);setError("");
    try{const next=await api<NotificationFeed>(`/notifications?mode=${mode}&offset=${feed.items.length+extra.length}`);setExtra(prev=>[...prev,...next.items.filter(n=>!feed.items.some(f=>f.id===n.id)&&!prev.some(p=>p.id===n.id))]);setHasMore(next.has_more);}
    catch(e){setError((e as Error).message);}finally{setBusy(false);}
  }
  useEffect(() => {
    const previous = document.activeElement as HTMLElement;
    const old = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    ref.current?.querySelector<HTMLButtonElement>("button")?.focus();
    const key = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "Tab") {
        const items = ref.current?.querySelectorAll<HTMLElement>(
          "button:not(:disabled),a[href]",
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
    document.addEventListener("keydown", key);
    return () => {
      document.removeEventListener("keydown", key);
      document.body.style.overflow = old;
      previous?.focus();
    };
  }, [onClose]);
  async function mark(path: string) {
    setBusy(true);
    setError("");
    try {
      await api(path, { method: "POST" });
      onChanged();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div
      className="notification-backdrop"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="notification-sheet"
        ref={ref}
        role="dialog"
        aria-modal="true"
        aria-labelledby="notifications-title"
      >
        <header>
          <div>
            <h2 id="notifications-title">
              <Bell size={21} />
              Notifications <b>{feed.unread_count}</b>
            </h2>
          </div>
          <button onClick={onClose} aria-label="Close notifications">
            <X size={21} />
          </button>
        </header>
        <p>
          First-observed events stay here when monitoring rules change.{" "}
          {mode === "demo"
            ? "These are simulated scenarios."
            : "Original event dates are shown."}
        </p>
        <BrowserPush />
        <button
          className="text-button"
          disabled={busy || !feed.unread_count}
          onClick={() => void mark(`/notifications/read-all?mode=${mode}`)}
        >
          <Check size={15} />
          Mark all as read
        </button>
        {error && (
          <p role="alert" className="error-banner">
            {error}
          </p>
        )}
        {!feed.items.length && (
          <div className="empty-state">
            <Bell size={25} />
            <h3>You’re all caught up.</h3>
            <p>
              New material filings and threshold crossings will appear here.
            </p>
          </div>
        )}
        {[...feed.items,...extra].map((n) => (
          <article key={n.id} className={n.read_at ? "read" : "unread"}>
            <div>
              <span>
                {n.ticker} ·{" "}
                {n.kind === "filing"
                  ? "Disclosure"
                  : n.kind === "volume"
                    ? "Volume alert"
                    : "Price alert"}
              </span>
              <time>{shortDate(n.occurred_at)}</time>
            </div>
            <h3>{n.title}</h3>
            <p>{n.explanation}</p>
            <small>
              Observed {shortDate(n.created_at)} ·{" "}
              {n.read_at ? "Read" : "Unread"}
            </small>
            <footer>
              <button
                className="text-button"
                onClick={() => {
                  onClose();
                  onResearch(n.ticker,"overview",`What do the company's primary sources establish about this signal: ${n.title}? Check the stated period and do not assume causality.`);
                }}
              >
                Research {n.ticker}
              </button>
              {n.source_url && (
                <a href={n.source_url} target="_blank" rel="noreferrer">
                  Source
                  <ExternalLink size={12} />
                </a>
              )}
              {!n.read_at && (
                <button
                  className="text-button"
                  disabled={busy}
                  onClick={() => void mark(`/notifications/${n.id}/read`)}
                >
                  Mark read
                </button>
              )}
            </footer>
          </article>
        ))}
        {hasMore && (
          <p>
            Showing {feed.items.length+extra.length} of {feed.total} events.
            <button className="text-button" disabled={busy} onClick={()=>void loadMore()}>Load earlier events</button>
          </p>
        )}
      </div>
    </div>
  );
}
