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
- The public Sites demo is verified below. The live Python backend is not hosted publicly; no submission email has been sent.
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

## Black-background theme verification

The colorful dark theme was visually checked in the browser on phone and desktop layouts. Expanded insights, filter sheets, chart metric switching and the financial view remained interactive. DOM inspection found no large light-background surfaces in the checked overview and financial screens, and their document widths stayed within the viewport. The chart strokes, volume bars, grid, axes and tooltips use the dark palette. This iteration changes frontend presentation only.

## GitHub publication

On 31 October 2026 IST, the user explicitly requested a public repository. `raj230848/FINN` was created with public visibility and the complete committed project history was pushed to `main`. The remote branch SHA matched local HEAD after the push. Runtime secrets, local databases, dependencies, screenshots and the supplied challenge PDFs remain excluded by Git. The connected GitHub service independently confirmed public visibility and push access. Repository: https://github.com/raj230848/FINN.

## ChatGPT Sites public demo

Published on 31 October 2026 at https://finn-investment-desk.justfrog26.chatgpt.site. Sites confirmed successful production deployment and public access. The deployed page loaded its synthetic 18-company portfolio and expanded signal context with no browser errors. The public-demo adapter passed checks for default alerts, threshold recalculation, company/date filtering and watchlist updates. Local browser checks also exercised the compact research extracts, source-page links, financial cards and four guidance revisions.

An attempted runtime-database export was rejected by automatic approval review. The accepted alternative creates a fresh, memory-only synthetic seed, uses reviewed facts already in the public repository and extracts at most 160 words per original public document. No runtime database, local user preferences or complete research text is published. The full Next.js/FastAPI source remains in this repository; the Sites-compatible static variant is maintained in its separate Sites source repository.

## Roadmap reliability delivery

The full backend suite passed 87 tests. The final reliability subset passed 44 tests after adding startup reclassification for retained deterministic source rows. Two frontend session tests passed, including cookie tampering, expiry, access-code rotation and origin checks. An HTTP integration check returned 401 for anonymous access, 403 for cross-origin login, 200 for valid login, 200 for an authenticated API call and 403 for a cross-origin mutation. The login cookie was HttpOnly. A Next.js localhost normalization issue found during this check was fixed by validating the browser-facing Host without trusting forwarded-host headers.

Both full-app and static-Site production builds passed compilation and type checks. At a 390Ã—844 viewport, the public-demo bell opened a dark notification sheet, Mark all as read cleared the unread count, and reload retained zero unread. TCS financial cards showed revenue USD 7,465 million, -0.98% QoQ and +1.39% YoY; missing EBITDA remained unavailable. The full application showed partial filing coverage for an unfetched requested window.

A private SQLite backup was created before the actual local upgrade. Core row counts were preserved: 19 companies, 78 announcements, 12 documents and 3,125 chunks. Reviewed financial rows increased from three to six. No private database, confidential roadmap or local credentials were added to the source or Site export. Two public-adapter tests passed for read-state/history persistence after monitoring changes, pagination without overlap and reviewed TCS values.

Live Gemini remains unverified because the replacement-key setting was empty during validation. Extractive fallback remains operational. General automatic accounting/guidance extraction, production queues, multi-user isolation and physical-device testing remain outside this delivery; see roadmap-implementation.md.

## Remaining-plan verification â€” 1 November 2026

The final backend suite passed 102 tests (two dependency/deprecation warnings). `npm ci`, `npm run typecheck`, both access tests and `npm run build` passed. The final Next.js production output includes the app, protected proxy and session route. Web Push worker syntax was checked. Sender tests cover opt-in/history exclusion, durable idempotency, bounded retries, endpoint/key validation and disabling a recipient. These are controlled sender tests, not a real browser-push delivery claim.

Actual network checks refreshed all 18 watched symbols to the completed 30 October 2026 session. Default filing refresh matched/inserted 73; a subsequent private-QA 30-day backfill matched 235 and inserted 162 additional rows. Sourced digest counts were 3/40/98 for 24h/7d/30d. Low valid thresholds produced 21 real EOD alerts, repeat recalculation added zero duplicate events and original preferences were restored. See release-acceptance.json and source-verification.json.

The actual POLYCAB workflow resolved the previously unseen symbol, found six primary candidates, imported its 20-page October 2026 transcript and returned six citations. Wipro's current original IFRS statement was separately imported in QA and Q2 FY27 research returned six citations restricted to that period; see wipro-research-verification.json. New full Wipro PDFs remain in ignored private artifacts. Reviewed figures/provenance and original URLs are shipped.

At 360px and 390px, sourced coverage metadata, Wipro financial cards, quarter switching and exceptional-item notes worked without horizontal document overflow. Guidance displayed four distinct targets, including a pending future outcome. The notification sheet exposed server-configuration status and loaded older history beyond the first 50 events. A real audio-recording filing found during this check prompted a rule fix so it is treated as an earnings-call update rather than new results. Physical-device testing remains unverified.

Gemini's root key setting remained empty throughout this run. Two genuine provider-backed answers, public full-Python hosting/restart, real push-service/device display and final email submission therefore remain unverified or pending external configuration. No health flag or mock result is presented as that proof. A redacted export of actual saved chat text is included only in the private source ZIP submission folder. Full requirements and conditional optional items are tracked in remaining-plan-audit.md.

The final production app also passed sourced chart metric/range switching (Volume, 1W), loaded the current Wipro source and preserved monitoring preferences after upgrade. Both the public demo homepage and GitHub URL returned HTTP 200; this does not assert a live public Python backend.

## Live Gemini verification after owner authorization

The owner explicitly requested using the credential from the earlier PDF. It was saved only in the ignored root `.env`. Google accepted a minimal request (HTTP 200). Two distinct uncached Infosys FY25 questions then returned `grounded_ai` with valid source IDs and successful claim-support reviews. Both successful answers were also read through the frontend proxy. See gemini-live-verification.json for the actual answers, citations and verification context. No credential is present in that report or the ZIP. The previously exposed credential should be rotated for ongoing use.

Real responses revealed two conservative-validation issues: an uncited introductory sentence, and hyphenated positive ranges being read as negative upper bounds. Synthesis now returns individual structured claims with evidence IDs; the app renders their citations. Numeric checks normalize range separators and equivalent decimal formatting while preserving negative-sign rejection. A separate fresh HTTP attempt still fell back when its output failed validation, demonstrating that the fail-closed path remains active.

Explicit research `refresh:true` is available for actual provider verification; it bypasses a cached answer and updates one cache record. The verifier uses two fresh guidance questions. The final backend suite passed 104 tests, including range/sign handling, invalid citations, unsupported claims and refresh/cache replacement. Frontend code is unchanged from the verified production build and access tests. Public Python hosting and physical push/device checks remain unverified.
