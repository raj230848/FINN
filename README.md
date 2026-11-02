# FINN

Public repository: [raj230848/FINN](https://github.com/raj230848/FINN).

Latest full-app update: [PDF import fix and verification](docs/pdf-import-verification.md): bounded 3,000-page imports, atomic indexing, duplicate protection and readable-page coverage. Validated with 298 backend tests and 20 frontend tests. [Neon Aurora / Champagne Bubble themes](docs/theme-change.md) and [full NSE name search with sourced-first refresh](docs/ui-ux-upgrade.md) remain available. The static public demo below is a separate version.

[Open the public interactive demo](https://finn-investment-desk.justfrog26.chatgpt.site). The Sites version uses synthetic market fixtures, historical reviewed financials and compact source extracts; watchlists and preferences are device-local. Live ingestion and document imports use the full Python application.

**Your portfolio. In perspective.** A mobile-first investment intelligence prototype for the ENAM Holdings AI Engineer Build Challenge.

FINN brings the daily workflow into one desk: prioritise disclosures, understand why a filing matters, monitor unusual end-of-day activity, and investigate a company through its own reports and earnings calls.

This is executable Next.js + FastAPI software with persistent SQLite storage. It includes a visibly labelled demo replay and actual market/exchange adapters. It does not place trades.

## Start on Windows

Requirements: Python 3.12, Node.js 22 LTS, npm, and internet access for dependency installation and live-source refreshes. No model API key is required for extractive research.

Open PowerShell in the project folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

This installs the locked Python dependencies and `npm ci`, then copies environment examples only if local files do not already exist. It does not change your machine's execution policy permanently.

Start both services with one command:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-finn.ps1
```

The launcher reuses healthy running FINN services, builds the frontend when needed, and otherwise starts both services in the background. Logs are saved under `artifacts/runtime`. Open **http://127.0.0.1:3000**.

For separate development terminals, use these commands instead:

Terminal 1:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-backend.ps1
```

Terminal 2:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-frontend.ps1
```

Open **http://127.0.0.1:3000**. API health is at **http://127.0.0.1:8000/api/health** and interactive API documentation at **http://127.0.0.1:8000/docs**.

The backend initialises the database, demonstration portfolio, reviewed metrics, and bundled document index automatically. First startup can take longer while full reports are indexed. No manually executed SQL is necessary. Startup is idempotent and preserves watchlist/preferences.

Equivalent manual setup:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.lock.txt
Copy-Item .env.example .env
Copy-Item frontend\.env.example frontend\.env.local
Set-Location frontend
npm.cmd ci --no-audit --no-fund
```

Run the backend from `backend` with `..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000`. Run the frontend from `frontend` with `npm.cmd run dev`. The default database path is absolute and independent of working directory. Environment examples contain no real credentials.

## What to try

1. **Overview / My brief:** the phone opens with an actionable daily brief and priority inbox. Use My brief / The market / Saved to switch tasks. Market exploration includes price/volume ranges, daily movers and company detail sheets. Demo replay is fixed to 30 October 2026 at 18:30 IST and unmistakably synthetic.
2. **Signals & alerts:** switch between 24 hours, seven days, 30 days or a custom IST range. Filter by company/category/priority, tap Read insight for context and the score explanation, save a signal, or inspect routine filings. On phones, the time-window row opens a filter sheet with company/category/priority and custom dates.
3. **Monitoring preferences:** save price threshold, volume multiplier, lookback, company scope and announcement interests. Alerts are recalculated in the backend. Volume baselines exclude the latest session.
4. **Sourced data:** press Refresh sources to download actual EOD histories and NSE disclosures. Partial failures and original session dates remain visible. Cached source data is never relabelled as a current quote.
5. **Research desk:** start with INFY, TCS or PERSISTENT. Ask a question; open the returned document/page evidence. The supplied original documents make those demonstrations usable offline.
6. **Financial snapshot:** INFY and TCS have reviewed three-quarter comparisons. INFY's historical Q4 FY25, Q3 FY25 and Q4 FY24 are compared on the same IFRS consolidated basis. EBITDA remains unavailable. PAT is attributable to owners after minority interests.
7. **Promise vs. reality:** compare four Infosys FY25 revenue-growth guidance revisions with 4.2% actual constant-currency growth. The final revision was missed by 0.3 percentage points even though the initial range was exceeded. Both sides have primary citations.
8. **An unfamiliar ticker:** enter an NSE symbol such as POLYCAB, click Find company, then use Source library → Discover. Import a permitted issuer/exchange PDF and ask a question. There is no demo-company restriction in the research code. Availability depends on the actual provider and document size; absence produces an explicit error.

The full five-scenario evaluator walkthrough is in [docs/demo.md](docs/demo.md).

### Interactive workspace

- **Portfolio pulse:** select a company, switch price/volume, choose 1W/1M/3M, and inspect chart tooltips. Watchlist breadth uses actual latest-session movements from the selected data mode.
- **Company briefs:** open a market-radar or watchlist company for a price chart, trading-volume metrics, source date and a direct research action.
- **Saved signals:** bookmark an announcement and revisit it under Saved for later. Bookmarks persist on this device and remain separated by demonstration/sourced mode.
- **Company search:** use Ctrl+K, search by name or ticker, navigate suggestions with arrow keys and open with Enter.
- **Watchlist exploration:** filter sectors, search company names and sort by gainers, decliners or unusual volume.
- **Actionable overview cards:** jump directly to high-priority disclosures, threshold crossings, routine filings or the watchlist.

## Stack and layout

```text
frontend/                 Next.js 15, React 19, TypeScript, Tailwind 4
  app/                    Mobile workspace and same-origin API proxy
  components/             Research/evidence workspace and Recharts
  lib/                    Typed API contracts and number formatting
backend/
  app/ingestion/          Yahoo market, NSE filings, bounded public HTTP
  app/services/           Documents, retrieval, rules, calculations, alerts, sync
  app/ai/                 Optional structured-output provider client
  app/models.py          SQLAlchemy persistence and traceable source fields
  app/main.py            FastAPI endpoints and application lifecycle
  data/primary/          Original issuer documents, hashes and reviewed manifest
  tests/                 Isolated arithmetic, data integrity and API tests
scripts/                  Windows launchers, document fetches and network checks
docs/                     Requirements, design, demo, verification and submission
compose.yaml              Two-service container deployment
render.yaml               Optional persistent backend hosting blueprint
```

See [docs/architecture.md](docs/architecture.md) for data flow, schema relationships, API contracts and engineering tradeoffs. See [docs/assessment.md](docs/assessment.md) for mandatory versus suggested challenge requirements.

## Sources, AI and integrity

The 18-company cross-sector portfolio was checked against NSE's public equity listing CSV. Yahoo Finance via `yfinance` supplies historical split/dividend-adjusted daily closes and volume. FINN does not have a live tick feed. Current-day candles are conservatively accepted only after 18:30 IST; the latest session returned by the provider may still be older.

NSE's public announcements endpoint is a best-effort web integration, not a contracted SLA. It can change, rate-limit, return unexpected formats or block automated access. FINN records individual failures and retains old data with its original dates. It never bypasses exchange access controls. Respect source terms and permitted use before wider distribution; `yfinance` is an unofficial client and does not grant a market-data redistribution licence.

Primary research evidence comes from the issuer's own reports or exchange-hosted issuer documents. Screener is used solely to discover primary URLs. The document index never treats its standardised financial tables or external commentary as primary research. The source catalog includes original URLs, SHA-256 hashes, periods and physical PDF page counts. Original report copyrights remain with their issuers.

No-key mode returns retrieved excerpts and explicitly labels them **extractive research**. To enable AI synthesis, set `GEMINI_API_KEY` and optionally `GEMINI_MODEL` (default `gemini-3.5-flash-lite`) in the project-root `.env`, then restart the backend. The optional provider client sends only relevant public passages and the research question. The result must validate against Pydantic, cite supplied chunk IDs in each substantive segment, and use only numeric literals present in the excerpts. Requests have bounded retries/timeouts; invalid output falls back to excerpts. Failures fall back to evidence with a visible limitation. Two genuine uncached source-grounded Gemini answers have now been verified with a supplied key (see docs/gemini-live-verification.json); valid citations alone cannot guarantee claim entailment.

Financial arithmetic, scoring, thresholds, deduplication and guidance-range assessment run in deterministic Python. Structured financial tables are reviewed for INFY, TCS and WIPRO (11 rows); guidance covers four INFY revisions and four Wipro quarterly targets, including one pending outcome. Arbitrary PDF table extraction is deliberately not portrayed as solved. Research retrieval generalises to any available NSE issuer documents.

## Verification

The [verification-gap update](docs/verification-gap-resolution.md) adds single-origin full-stack hosting, restart recovery, operational visibility and hosting/push hardening. The current suite passes **248 backend tests** and **11 frontend tests**; actual local process tests verify persistence and two-session proxy outage/recovery. Public hosting, physical-device delivery and credential rotation remain separate acceptance gates. See [the hosted/device runbook](docs/hosted-acceptance.md).

The earlier [full implementation and integration audit](docs/comprehensive-audit.md) records the previous 227-test source revision, all original 24 backend business operations, 18 protected frontend HTTP checks, and four genuine Gemini calls across all three LLM call sites. All 18 watched Yahoo feeds and the NSE adapter worked in that live QA run. These are historical measurements; they are not relabelled as deployed-host results. Raw evidence for both revisions is included in the updated ZIP.

From the project root:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
Set-Location frontend
npm.cmd run test:access
npm.cmd run typecheck
npm.cmd run build
```

Optional network checks, from the project root:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts\probe_sources.py
.\.venv\Scripts\python.exe -X utf8 scripts\fetch_sources.py
.\.venv\Scripts\python.exe -X utf8 scripts\verify_integrations.py
.\.venv\Scripts\python.exe -X utf8 scripts\verify_research.py
```

Network checks deliberately write to the local research/price database and produce availability reports under `docs`. They are separate from the isolated test suite. Results observed during this build, including unverified parts, are in [docs/verification.md](docs/verification.md).

## Scheduling and persistence

Set `ENABLE_SCHEDULER=true` for a bounded interval refresh (default every 60 minutes, minimum 30). Start **one backend worker**. The scheduler is off by default; the UI always supports manual refresh. Market alerts are EOD and do not imply instantaneous intraday monitoring. The SQLite file is `backend/data/finn.db`; preserve it across restarts. A host's ephemeral filesystem is insufficient for persistence.

The prototype is one personal/shared desk. The optional `FINN_API_TOKEN` must match in root `.env` and `frontend/.env.local`. For an internet deployment, set `PUBLIC_DEPLOYMENT=true` on the backend and `FINN_PUBLIC_MODE=true`, `FINN_ACCESS_TOKEN` (at least 16 characters), and `FINN_SESSION_SECRET` (at least 32 characters) on the frontend. The hosted proxy requires an eight-hour signed HttpOnly session from the shared desk access code; credentials remain server-only. Vercel/Render also enable the gate automatically. Do not expose a shared unauthenticated desk as a multi-user product.

## Deploy

The source is published at [raj230848/FINN](https://github.com/raj230848/FINN). The public interactive Sites demo is linked above; the live Python data backend has not been hosted publicly. See [docs/deployment.md](docs/deployment.md) for exact Docker, Vercel, Render and GitHub steps. Docker is optional; its build has not been tested on this machine because Docker is not installed. A persistent Render disk may require a paid plan; the blueprint requests `starter` explicitly and does not claim to be free. Local operation and no-key research avoid hosting/model charges.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| PowerShell blocks `.ps1` | Use the per-invocation `powershell -ExecutionPolicy Bypass -File ...` commands above. |
| `npm` script execution blocked | Use `npm.cmd`, not the PowerShell `npm.ps1` shim. |
| Data service unavailable | Start the backend, verify `/api/health`, and check `BACKEND_URL`. |
| Port 3000/8000 occupied | Stop the old owned server, or change the port and matching proxy/CORS environment variables. |
| Initial compilation is slow | Let the first Next.js build and source-index startup complete. Later requests reuse compiled code. |
| 401 API response | Match the server-only token in both backend and frontend environments, then restart both. |
| Yahoo/NSE 403/429 or empty feed | Inspect the refresh result; retry later. Cached data and demo replay remain clearly distinct. |
| Annual report rejected | Use a direct, text-readable primary PDF for the selected issuer. Defaults: 3,000 pages and 60,000,000 bytes, with bounded extraction/indexing. Check the reported limit or access error; scanned pages require OCR. Existing documents are retained when an import fails. |
| No research conclusion | Import relevant primary documents. Without an API key, inspect the source extracts instead of expecting generated synthesis. |
| No financial snapshot for a ticker | Its numeric table has not been reviewed. Use document research; missing numbers are not inferred. |
| History latest date is yesterday | Provider latency, a trading holiday or incomplete session may explain this. FINN shows the returned date. |

The covering email draft is [docs/covering-email.md](docs/covering-email.md). The decision log is [docs/build-history.md](docs/build-history.md); attach/export the actual coding-agent conversation separately. A decision log is not a fabricated substitute for the required conversation history.

## Phone experience

The challenge PDF explicitly asks for everything to be mobile-first. FINN therefore uses a distinct phone workflow: digest and priority inbox first, optional market exploration, touch-sized bottom navigation, and bottom sheets for filters, preferences and company details. The watchlist becomes individual company cards, and quarterly numbers become metric cards with both QoQ and YoY comparisons. Desktop tables and the wider workspace remain available at larger widths. Saved signals persist on the current device.

The interface uses a black canvas with violet, cyan, lime and pink accents. Charts, menus, source panels and phone sheets share the same dark palette.

## Roadmap implementation

The [implementation record](docs/roadmap-implementation.md) covers Gemini, additive database migration, attachment-aware deduplication, durable notification history, filing coverage/pagination, TCS financial comparisons and hosted access controls. Use the bell to read important filing and threshold events; read state survives recalculation. Coverage describes successful fetch windows and does not guarantee an exhaustive exchange archive.

## Remaining-plan delivery

Start with [START_HERE.md](START_HERE.md) and the [item-by-item audit](docs/remaining-plan-audit.md). This update adds optional [Web Push](docs/browser-push.md), complete notification-history paging, explicit observation/coverage metadata and a 30-day backfill action. WIPRO has five reviewed IFRS quarters with accounting notes and a quarter selector, three completed distinct guidance targets and one pending outcome. Research now filters explicit fiscal periods and applies a separate model support review after citation/numeric checks.

Live Yahoo/NSE and unseen-POLYCAB verification reports are included. `scripts/verify_release.py` reruns acceptance checks and explicitly reports missing model configuration; `scripts/export_build_history.py` exports real saved chat messages into a private submission attachment. The supplied ZIP includes that redacted export. Live Gemini authentication and two source-grounded answers are now verified locally. Full Python hosting and physical push/device verification remain external acceptance steps.
