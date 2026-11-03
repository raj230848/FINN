"use client";
import { useState } from "react";
import { LockKeyhole, ArrowRight, Loader2 } from "lucide-react";

export function AccessGate({ onUnlocked, onCancel }: { onUnlocked: () => void; onCancel?: () => void }) {
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  return (
    <main className="access-gate">
      <section>
        <div className="access-logo">
          finn<span>.</span>
        </div>
        <LockKeyhole size={28} />
        <h1>Your private investment desk.</h1>
        <p>Enter the access code supplied by the desk owner.</p>
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            setError("");
            try {
              const r = await fetch("/api/session", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ access_code: code }),
              });
              const result = await r.json();
              if (!r.ok) throw new Error(result.detail || "Sign-in failed.");
              setCode("");
              onUnlocked();
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          <label htmlFor="access-code">Access code</label>
          <input
            id="access-code"
            type="password"
            autoComplete="current-password"
            required
            maxLength={512}
            value={code}
            onChange={(e) => setCode(e.target.value)}
            autoFocus
          />
          {error && <p role="alert">{error}</p>}
          <button className="btn primary" disabled={busy}>
            {busy ? (
              <Loader2 className="spin" size={17} />
            ) : (
              <ArrowRight size={17} />
            )}
            Open my desk
          </button>
        </form>
        {onCancel && <button className="text-button" onClick={onCancel}>Back to public preview</button>}
      </section>
    </main>
  );
}
