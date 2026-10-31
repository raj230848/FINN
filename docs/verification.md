# Verification record

Observed during this build, 31 October 2026 IST. Machine-readable source checks use their actual UTC timestamps. Results describe this environment and time, not a provider guarantee.

## Automated checks

- Backend: **42 tests passed**, including signed price changes, missing/zero/negative bases, complete-session boundaries, unusual-volume baselines, all key classification priorities, meeting-notice downgrading, filing deduplication, 24h/7d/custom date filtering, mode separation, persisted preferences, unseen ticker resolution, provider failures, URL/network guards, malformed PDF handling, page references, content-sensitive caching and invalid model citations.
- Four financial/guidance checks validate actual source-table rows, accounting-basis isolation, missing EBITDA and same-period guidance revisions.
- One regression test uses the observed Screener document class structure and BSE PDF viewer format; secondary links and presentation/audio links are excluded from transcript results.
- Frontend: TypeScript checking and a production Next.js build succeeded. The production build includes the app and same-origin server API proxy.
- The standalone production server was started successfully; the HTML and proxied health endpoint returned HTTP 200, and the proxied sourced dashboard reported coverage for all 18 companies. The local production launcher copies static assets and loads server-only environment settings.
- One upstream deprecation warning remains in the test client (Starlette/httpx); no test fails because of it. yfinance also emitted Pandas deprecation warnings during actual downloads, while the requested price histories loaded successfully.

## Actual source integration

`source-verification.json` records:

- NSE equity master downloaded successfully; all 18 portfolio symbols found among 2,620 listed symbols.
- Yahoo Finance returned 125 completed daily sessions for each of the 18 companies in that run.
- The latest session returned was **29 October 2026**, not a claim of a live 30/31 October quote.
- NSE announcements matched 72 rows across the portfolio and inserted **67** unique disclosures.
- The second refresh, started through `POST /api/sync` in the running API, completed successfully for all 18 price feeds and NSE. It inserted **zero** additional announcements from the same 72 matched rows, demonstrating idempotency.

Original primary documents were successfully downloaded and indexed for INFY, TCS and PERSISTENT. There are eleven bundled original documents (nine Infosys documents, one TCS issuer release and one Persistent annual report). The source catalog records actual checksums and page counts. A TCS request initially returned HTTP 403 and later succeeded through the same ordinary public access path; availability is explicitly best effort.

`research-verification.json` records source-grounded extractive results for all three prepared companies. It additionally records a genuine company outside the demo seed/catalog:

- POLYCAB was resolved through the generic provider adapter.
- Six primary document candidates were discovered after the directory-format fix.
- A 20-page October 2026 BSE-hosted Polycab issuer transcript was imported.
- A research request returned six page-cited passages.
- POLYCAB is not special-cased in the application research code and was not added to the 18-company watchlist.

## Browser checks

The running Next.js frontend was exercised through the in-app browser against the actual local FastAPI service:

- Overview loaded portfolio statistics, synthetic signals, company chart and routine grouping.
- Expanding a management-change signal displayed the score factors and explicit analysis method.
- Seven-day and high-priority filters changed the returned feed.
- Changing volume threshold from 2x to 3.5x reduced volume crossings from three to zero, leaving the two price crossings. Defaults were restored to 5%/2x/20 sessions.
- INFY's financial table displayed the verified revenue/PBT/PAT values, calculated QoQ/YoY and unavailable EBITDA.
- A cash-conversion question returned extractive research, six evidence passages and original source-page links. It explicitly indicated that no model key was configured.
- The four guidance revisions displayed exceeded/exceeded/achieved/missed outcomes, with the last miss -0.3 percentage points.
- Desktop and phone-size viewport overrides were inspected. The phone layout used bottom navigation and a scrollable research tab strip. Document/body widths did not exceed the actual viewport. A wrapped guidance range was corrected into stacked phone rows.
- Review screenshots are saved locally in `artifacts/screenshots`; they are not committed to the source repository.

## Verification limits

- No actual OpenAI model request was made: no user API key was provided. The provider boundary and invalid-citation rejection have automated coverage, while live AI synthesis remains unverified.
- Docker images, hosted deployment and remote CI were not executed; Docker/hosting credentials are not available on this machine. Their configuration is prepared and the exact steps are documented.
- No public URL, remote GitHub repository or sent submission email is claimed. The local repository and covering draft are ready.
- Reviewed numeric tables and guidance extraction are focused on INFY. Other companies use source retrieval until their accounting data is reviewed; no general-purpose extraction accuracy is claimed.
- Source metadata/citations are validated, but semantic model entailment, exhaustive disclosure coverage and production multi-user security are not claimed.

## Interactive UI refresh

The later UI update retained the existing backend and primary sources. The final production build passed after the navy/lime workspace and interactive controls were added; the backend suite again passed all 42 tests. Frontend, backend and proxy responded with HTTP 200. The new `scripts/start-finn.ps1` launcher passed syntax validation and correctly reused both healthy running services.

Browser checks confirmed price/volume switching, 1W/1M/3M chart ranges, selecting another chart company, opening company details and closing with Escape, saving a disclosure, preserving that bookmark after reload, filtering information-technology companies, sorting by daily gainers, and keyboard search for Infosys followed by its four guidance comparisons. Saved view disables date filtering because it explicitly spans all dates.

The final phone check confirmed document width 341 CSS pixels within an actual 355-pixel viewport, with no horizontal page overflow. The full-width company brief and its chart were inspected at the same phone size. Desktop and phone screenshots are kept under `artifacts/screenshots` locally. Browser bookmarks are device-local and are not shared account preferences.

## Mobile-first workflow verification

The phone workflow was checked in the actual browser with requested 390 x 844 and 320 x 740 viewport overrides (actual CSS widths were 355 and 291 because of browser scaling). The document stayed within the viewport on the brief, watchlist, financials and guidance screens. Desktop was also inspected at a requested 1440 x 1000 size; the existing statistics, chart and wider workspace remained visible while phone-only components were hidden. Browser console inspection returned no errors.

The filter sheet applied company, priority, seven-day and custom-date selections to the real API feed. Read insight revealed context and score factors; saving and removing a test bookmark updated Saved. The market switch opened the chart and daily movers, and company details opened as a bottom sheet. A mobile watchlist card successfully removed and re-added BAJFINANCE; the original 18-company monitoring state was restored. INFY financial cards displayed the reviewed revenue/PBT/PAT comparisons, unavailable EBITDA and source-page links. All four guidance revisions remained accessible on the small screen. Saved views do not expose active date controls.

The frontend production build includes compilation and TypeScript checking. The backend is unchanged in this iteration; the existing 42-test result above applies to that unchanged implementation. Phone screenshots are retained under `artifacts/screenshots`.
