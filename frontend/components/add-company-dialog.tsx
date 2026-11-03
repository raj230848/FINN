"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowRight, Building2, Check, Loader2, Plus, X } from "lucide-react";
import { CompanyLookup, type CompanyMatch } from "@/components/company-lookup";
import type { Company } from "@/lib/api";

export function AddCompanyDialog({ companies, onAdd, onClose }: {
  companies: Company[];
  onAdd: (company: CompanyMatch) => Promise<void>;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [selected, setSelected] = useState<CompanyMatch | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const watched = companies.some(company => company.ticker === selected?.ticker && company.watched);

  useEffect(() => {
    const element = dialog.current;
    if (element && !element.open) {
      element.showModal();
      element.querySelector("input")?.focus();
    }
  }, []);

  async function confirm() {
    if (!selected || saving || watched) return;
    setSaving(true);
    setError("");
    try {
      await onAdd(selected);
      dialog.current?.close();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <dialog ref={dialog} id="add-company-dialog" className="add-company-dialog" aria-labelledby="add-company-title"
      onClose={onClose}
      onCancel={event => { if (saving) event.preventDefault(); }}
      onClick={event => { if (event.target === event.currentTarget && !saving) dialog.current?.close(); }}>
      <div className="add-company-content">
        <header className="add-company-heading">
          <span className="add-company-icon"><Building2 size={23} aria-hidden="true" /></span>
          <div>
            <h2 id="add-company-title">Add company</h2>
            <p>Search the NSE directory to add a company to your watchlist.</p>
          </div>
          <button type="button" className="icon-button" aria-label="Close add company" disabled={saving} onClick={() => dialog.current?.close()}><X size={20} /></button>
        </header>
        {selected ? (
          <>
            <div className="add-company-selection">
              <div>
                <span className="ticker-chip">{selected.ticker} · {selected.exchange}</span>
                <h3>{selected.name}</h3>
                <p>{selected.sector || "NSE-listed equity"}</p>
              </div>
              {watched && <span className="add-company-watched"><Check size={15} /> On watchlist</span>}
            </div>
            {error && <p className="search-error" role="alert">{error}</p>}
            <div className="add-company-actions">
              <button type="button" className="btn" disabled={saving} onClick={() => { setSelected(null); setError(""); }}>Change company</button>
              {watched
                ? <button autoFocus type="button" className="btn primary" onClick={() => dialog.current?.close()}>Done <ArrowRight size={16} /></button>
                : <button autoFocus type="button" className="btn primary" disabled={saving} onClick={() => void confirm()}>{saving ? <Loader2 size={16} className="spin" /> : <Plus size={16} />}{saving ? "Adding…" : "Add to watchlist"}</button>}
            </div>
          </>
        ) : <CompanyLookup companies={companies} addToWatchlist onSelect={setSelected} />}
      </div>
    </dialog>
  );
}
