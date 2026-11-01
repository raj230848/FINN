# FINN - Full Implementation and Integration Audit

Audit date: 1 November 2026. Generated from recorded test evidence; no credentials included.

## 01 / Audit outcome

FINN - implementation, API, Gemini and edge-case verification | 1 November 2026

Assessment: the local full application is functional across its implemented workflows. The audit found real failures, added regression coverage and corrected them. This is a tested investment-research prototype; the evidence does not establish that every possible edge case or production deployment is solved.

| Verification | Observed result |
| --- | --- |
| Backend regression suite | 227 passed; 0 failed; 2 dependency/deprecation warnings. |
| Frontend validation | 6 Node tests passed; TypeScript check passed; Next.js production build passed. |
| Backend route inventory | All 24 business method/path operations pass controlled endpoint tests. OpenAPI inventory equality is enforced. |
| Actual backend HTTP | 43 checks passed; 0 failed; 1 configuration-blocked check. 23/24 business operations succeed live; push subscription requires VAPID configuration. |
| Protected frontend HTTP | 18 checks passed across all 6 exported proxy/session operations, including rate limits and authentication. |
| Actual Google Gemini | 4 genuine provider calls across all 3 call sites; synthesis, support review and classification returned schema-valid responses. |
| Failures corrected | 18 initially failing regression cases now pass, spanning 9 defect categories. |
| Measured unit coverage | 91.5% statements; 78.9% branches; 88.6% combined. |

Testing separation: normal tests clear real provider and push credentials, use temporary databases and controlled external responses. Live checks used a separate QA database and a local protected production-mode frontend. Gemini calls used the private configured key; no usable credential appears in this report or distribution.

External acceptance still pending: a public hosted Python backend with HTTPS and persistent storage, actual browser-push delivery, and physical-phone testing. The existing public Sites URL is a separate static demo and does not prove backend deployment.

## 02 / What is implemented

Full-project inventory, including functionality delivered before this audit

| Area | Implemented behavior |
| --- | --- |
| Mobile experience | Colorful black-background Next.js desk; actionable brief, watchlist, price/volume charts, company sheets, search, date/category/priority filters, saved signals and source links. |
| Portfolio / preferences | 18-company cross-sector starting portfolio; persistent watched flags, thresholds, lookback and interests. Bookmarks remain device-local. |
| Market monitoring | Adjusted Yahoo EOD bars; completed-session cutoff at 18:30 IST; deterministic price changes and volume ratios excluding the latest session from the baseline. |
| Filing workflow | Best-effort NSE ingestion; UTC timestamps, attachment/content identity and duplicate suppression; priority factors, routine filtering, context and pagination. |
| Coverage / refresh | 24h/7d/30d/custom windows; first observation, last fetch, missing-history warning; manual/backfill refresh and optional single-worker scheduler; partial sync results retained. |
| Research | NSE issuer resolution, primary-PDF discovery/import, page-preserving chunks, BM25-style retrieval, up to six cited pages, source-aware caching and explicit refresh. |
| Gemini | Structured synthesis, independent support review and selective ambiguous-filing classification. Invalid/unavailable responses fall back to source excerpts or deterministic rules. |
| Quarterly financials | 11 reviewed rows: INFY 3, TCS 3, WIPRO 5. Quarter selection, deterministic QoQ/YoY, explicit currency/accounting basis and Wipro exceptional-item notes. EBITDA stays unavailable. |
| Guidance accountability | 8 records: 4 INFY revisions for one FY25 target; 3 completed Wipro quarterly targets and 1 future pending target. Same metric, period, currency/basis required. |
| Notifications / push | Persistent event/read history; recalculation deduplication; optional opt-in Web Push, durable outbox, retries, opt-out and service worker. Real delivery remains unverified. |
| Access / operations | Server-only provider/backend secrets, shared-desk access code, signed HttpOnly sessions, origin checks, public expensive-route limits, SQLite WAL, additive migrations and Windows launchers. |
| Delivery assets | Public GitHub source, setup/deployment runbooks, Compose/Render configuration, reviewed provenance, evaluator walkthrough and a full source ZIP with a private redacted visible-chat export. |

Architecture: mobile browser -> same-origin Next.js proxy -> FastAPI -> SQLAlchemy/SQLite. Source ingestion and deterministic calculations feed the desk; primary excerpts feed optional Gemini. This is one personal/shared desk, without separate user accounts or trade execution.

## 03 / Every backend business endpoint

Controlled = isolated application test. Live = actual local HTTP with real providers where applicable.

| Method | Registered path | Controlled | Live HTTP |
| --- | --- | --- | --- |
| GET | /api/health | PASS | 200 / pass |
| GET | /api/companies | PASS | 200 / pass |
| PATCH | /api/companies/{ticker} | PASS | 200 / pass |
| GET | /api/dashboard | PASS | 200 / pass |
| GET | /api/announcements | PASS | 200 / pass |
| GET | /api/alerts | PASS | 200 / pass |
| GET | /api/notifications | PASS | 200 / pass |
| GET | /api/push/config | PASS | 200 / pass |
| POST | /api/push/subscribe | PASS | 503 / blocked |
| POST | /api/push/unsubscribe | PASS | 200 / pass |
| GET | /api/push/status | PASS | 200 / pass |
| GET | /api/announcements/{filing_id}/context | PASS | 200 / pass |
| POST | /api/notifications/read-all | PASS | 200 / pass |
| POST | /api/notifications/{event_id}/read | PASS | 200 / pass |
| GET | /api/preferences | PASS | 200 / pass |
| PUT | /api/preferences | PASS | 200 / pass |
| POST | /api/sync | PASS | 202 / pass |
| GET | /api/sync/{run_id} | PASS | 200 / pass |
| POST | /api/companies/{ticker}/discover | PASS | 200 / pass |
| GET | /api/companies/{ticker}/documents | PASS | 200 / pass |
| POST | /api/documents | PASS | 200 / pass |
| POST | /api/research | PASS | 200 / pass |
| GET | /api/companies/{ticker}/financials | PASS | 200 / pass |
| GET | /api/companies/{ticker}/guidance | PASS | 200 / pass |

The route-inventory test compares this matrix with all registered OpenAPI business operations, so an added route cannot silently go untested. 30 parameterized negative endpoint cases also cover invalid bounds, malformed requests, unknown IDs/tickers, dates and filters.

POST /api/push/subscribe succeeds in controlled configuration tests; the real environment returns the expected configuration error (503) because no VAPID keys are configured. No real device subscription or external push was sent. Framework GET pages /docs, /redoc, /openapi.json and /docs/oauth2-redirect also returned 200.

## 04 / Frontend access and proxy checks

Actual protected production-mode Next.js server over local HTTP; not a public HTTPS/device test

| Scenario | Expected / actual |
| --- | --- |
| anonymous proxy blocked | 401 / PASS |
| unsupported session method | 405 / PASS |
| cross-origin sign-in blocked | 403 / PASS |
| wrong access code | 401 / PASS |
| invalid JSON | 400 / PASS |
| oversized sign-in body | 413 / PASS |
| chunked oversized sign-in body | 413 / PASS |
| valid sign-in | 200 / PASS |
| authenticated GET proxy | 200 / PASS |
| authenticated PUT proxy | 200 / PASS |
| authenticated PATCH proxy | 200 / PASS |
| authenticated POST proxy | 200 / PASS |
| backend rate limit and Retry-After through proxy | 429 / PASS |
| cross-origin mutation blocked | 403 / PASS |
| cross-origin logout blocked | 403 / PASS |
| same-origin logout | 200 / PASS |
| cookie invalidated after logout | 401 / PASS |
| failed-login throttle | 429 / PASS |

All six exported handlers were exercised: GET/POST/PUT/PATCH on the proxy and POST/DELETE on the session endpoint. The unsupported session GET correctly returned 405. A valid sign-in produced an HttpOnly, SameSite=Strict cookie; logout prevented the next protected API request.

New hardening: a streamed JSON reader enforces a 2,048-byte sign-in limit even without Content-Length; malformed bodies return 400 and oversized bodies 413. The proxy preserves Retry-After from a backend 429. Inadequately configured access codes cannot validate a session.

The six frontend unit tests cover signed-session/origin behavior and request-body parsing/limits. Type generation, TypeScript and production compilation passed. Earlier 360px/390px browser workflow checks remain documented; no physical phone or new complete visual regression audit is claimed here.

## 05 / Gemini key and all LLM integrations

Actual configured model: gemini-3.5-flash-lite | Private root .env | Four fresh provider calls

| Call site / schema | Live outcome | Latency |
| --- | --- | --- |
| SynthesisOut | Accepted cited synthesis | 2797 ms |
| GroundingReviewOut | Supported: true; 0 unsupported claims | 2265 ms |
| ClassificationOut | M&A / high | 2672 ms |
| ClassificationOut | unclassified / low | 2719 ms |

Research prompt: What FY25 operating margin guidance did management provide? The uncached answer used grounded_ai and reported 20% to 22%, linked to primary Infosys pages. A separate live model support review returned supported=true with zero unsupported claims. The report JSON preserves the actual answer and page URLs.

Classification used two explicitly synthetic public-style fixtures in the disposable QA database, not actual issuer events. An evidence-rich ambiguous restructuring classified as M&A; deterministic medium priority and needs-review remained. A vague filing returned low-confidence unclassified, and the application rejected it into deterministic needs-review fallback. Fixtures were rolled back.

| Additional integration behavior | Observed |
| --- | --- |
| Replay same research | Cached result; 0 further provider calls. |
| No indexed evidence | insufficient_evidence; 0 provider calls. |
| Replay same filing identity | 0 inserted duplicates; 0 additional classifier calls. |
| Normal unit tests | Real Gemini/VAPID secrets cleared automatically; no paid calls or actual notification delivery. |

Controlled faults cover authentication/model/quota/server errors, timeouts, bounded retries, invalid JSON, malformed envelopes, empty/refused/truncated/wrong-schema output, fabricated or wrongly typed citation IDs, unsupported numbers and a false-but-cited claim. Failures return evidence or deterministic review rather than an invented answer.

Limits: a successful key test proves present access, not future quota or uptime. Model support review is probabilistic, not a proof of semantic correctness. Synthetic classification checks integration behavior, not real-world accuracy. The previously exposed credential works but should be rotated before continued/shared operation; it is excluded from Git, ZIP and this report.

## 06 / Defects found and corrected

18 red-before / green-after cases, with regression tests retained in the project

| Defect category | Before | Implemented correction |
| --- | --- | --- |
| Huge database IDs (2) | SQLite overflow -> 500. | Positive signed-64-bit route IDs; invalid values -> 422. |
| Blank question (1) | Whitespace passed minimum length. | Trim before validating meaningful question length. |
| Unknown filing filters (2) | Invalid category/priority accepted. | Reject unsupported values with 422. |
| Malformed URLs (2) | Bad port/IPv6 leaked ValueError. | Translate parsing errors to a clear SourceError. |
| Issuer identity (1) | Generic word services matched wrong issuer. | Require full normalized legal name or explicit ticker identity. |
| Fiscal aliases (4) | FY ranges / compact quarters mapped incorrectly. | Use ending financial year and support FY2024-25, Q2FY25 and FY25Q2. |
| Provider envelope (1) | Non-object choice leaked AttributeError. | Validate choice/message structures; sanitize ProviderError. |
| NSE row shapes (2) | Non-object rows leaked AttributeError. | Reject malformed list elements as a bounded SourceError. |
| Yahoo payload shape (3) | Missing columns, bad numeric/index values leaked exceptions. | Reject invalid source payloads clearly and retain cached data. |

Additional audit hardening: company-filtered coverage no longer counts unrelated issuers; an empty watchlist is explicitly labelled; citation IDs and support booleans require strict types; model filing summaries cannot introduce unsupported numeric literals; URL fragments no longer duplicate the same import; usage logging accepts only bounded numeric metadata; non-ASCII bearer input rejects cleanly.

Resource/security boundaries exercised: HTTPS issuer/exchange allowlist, non-global IPv4/IPv6 rejection, redirect revalidation, download cap, malformed/empty/scanned/encrypted/over-600-page PDFs, source identity mismatch, missing/no evidence, sync lock conflicts, partial provider failures and lock release. Normal tests are isolated from runtime credentials and the real database.

These are finite, named test cases. Passing them does not establish exhaustive input coverage, parser isolation, immunity to DNS rebinding, or a formal security certification. Production egress policy and further security/load testing remain operational work.

## 07 / Source and financial verification

Actual network observations from the disposable QA database on 1 November 2026

| Workflow | Evidence |
| --- | --- |
| Market refresh | 18/18 watched Yahoo symbols succeeded; each returned 126 completed daily sessions. Latest session: 30 October 2026. No live-tick feed is claimed. |
| Exchange refresh | NSE succeeded: 8 matching filings; 2 new records in this QA copy. Response window is best effort and not a completeness guarantee. |
| Sourced digest windows | 24h / 7d / 30d returned 1 / 64 / 66 rows in this QA snapshot. All retained explicit partial-coverage warnings; counts change with source responses and local history. |
| Unknown issuer path | HCLTECH resolved; 6 primary candidates discovered; October 2026 exchange-hosted issuer transcript imported (26 pages); extractive research returned 6 citations. |
| Current Wipro document | Actual issuer financial statement import succeeded in QA; earlier period-restricted Q2 FY27 research is also documented in the project. |
| Events / preferences | Repeated threshold recalculation added 0 duplicate events; read-all left 0 unread events. QA preferences and watch-state were restored. |
| Reviewed tables | INFY 3 + TCS 3 + Wipro 5 = 11 rows. Original document/page, units, reporting basis and provenance retained. |
| Guidance records | INFY 4 revisions = 1 historical target; Wipro 3 completed quarterly targets + 1 pending future target. Do not count every revision as a separate management promise. |

Accounting boundaries tested: unavailable EBITDA stays unavailable; no operating-profit substitution; zero/missing/negative bases are explicit; only comparable consecutive quarters and same currency/accounting basis produce changes. Wipro group PAT including non-controlling interests is distinguished from INFY/TCS owner-attributable PAT. Guidance uses percentage-point range deviations, matching period/metric/basis, and excludes mismatches.

No generic automatic accounting-table extraction or OCR accuracy is claimed. Reviewed rows are deliberately focused. Retrieval can generalize to a newly resolved issuer with accessible primary text, while missing evidence produces an explicit limitation.

Provenance: live-http.json contains the source timestamp, sync response and imported HCLTECH URL. Reviewed numeric sources and hashes are under backend/data/primary. Full newly fetched Wipro reports and runtime databases remain private ignored artifacts. Market/source availability and permitted redistribution depend on their providers.

## 08 / Measured code coverage

coverage.py branch measurement of the isolated backend suite; not an accuracy score

| Module under backend/app | Statements | Branches | Combined |
| --- | --- | --- | --- |
| ai/client.py | 95.1% | 95.8% | 95.3% |
| config.py | 100.0% | n/a | 100.0% |
| database.py | 76.5% | 50.0% | 73.7% |
| ingestion/exchange.py | 100.0% | 100.0% | 100.0% |
| ingestion/http.py | 85.1% | 75.0% | 82.5% |
| ingestion/market.py | 97.4% | 91.7% | 96.1% |
| main.py | 82.2% | 63.4% | 77.6% |
| migrations.py | 88.5% | 75.0% | 84.2% |
| models.py | 100.0% | n/a | 100.0% |
| rate_limit.py | 93.8% | 66.7% | 86.4% |
| schemas.py | 100.0% | 100.0% | 100.0% |
| seed.py | 100.0% | 79.4% | 92.1% |
| services/alerts.py | 100.0% | 100.0% | 100.0% |
| services/calculations.py | 100.0% | 100.0% | 100.0% |
| services/coverage.py | 100.0% | 91.7% | 96.8% |
| services/documents.py | 85.7% | 79.4% | 84.1% |
| services/events.py | 100.0% | 100.0% | 100.0% |
| services/materiality.py | 96.7% | 90.9% | 95.1% |
| services/push.py | 90.9% | 82.1% | 88.6% |
| services/research.py | 94.4% | 82.0% | 90.8% |
| services/sync.py | 86.8% | 65.4% | 82.9% |
| TOTAL | 91.5% | 78.9% | 88.6% |

Statement coverage: 1333/1457 executable statements. Branch coverage: 347/440 branch destinations. Missing: 124 statements and 93 branch destinations. Combined coverage counts both statements and branch destinations.

The independent live HTTP and Google processes are not folded into this measurement. Controlled adapter tests cover supported timestamps, provider restrictions/bad JSON, malformed list rows, missing columns, invalid values, incomplete/non-finite market rows and unverified company metadata. Remaining uncovered branches are visible in the included coverage JSON; no 100% claim is made.

## 09 / Test inventory and reproduction

Retained tests and credential-free evidence allow the findings to be reviewed

| Backend test group | Passing cases |
| --- | --- |
| test_announcements | 14 |
| test_api | 6 |
| test_calculations | 13 |
| test_comprehensive_audit | 100 |
| test_documents_research | 5 |
| test_feed_contracts | 23 |
| test_financials | 5 |
| test_remaining_plan | 17 |
| test_roadmap_reliability | 44 |
| TOTAL | 227 |

The comprehensive-audit group includes the 24 business operation cases, OpenAPI inventory equality, 30 negative endpoint cases, the initial regressions, strict model types, unsupported classifier numbers, source-resource guards, partial-sync behavior and public-startup/authorization checks. Earlier groups retain arithmetic, document provenance, materiality wording, migration/persistence, guidance comparability and push outbox tests.

Run offline validation from the project root:

- .venv\Scripts\python.exe -m pytest backend\tests -q

- From frontend: npm.cmd run test:access; npm.cmd run typecheck; npm.cmd run build

- Optional coverage: install backend/requirements-audit.txt; set COVERAGE_FILE=artifacts/comprehensive-audit/.coverage; run coverage run --branch --source=backend/app -m pytest backend/tests; then coverage json.

Live scripts are separate because they consume provider/network access and change a disposable QA database. Start a protected backend on 127.0.0.1:8002 using a copied SQLite database under artifacts/comprehensive-audit and a disposable API token. scripts/audit_live_integrations.py checks localhost:8002 only. scripts/audit_gemini.py refuses a database URL outside comprehensive-audit. Configure AUDIT_BACKEND_TOKEN, AUDIT_ACCESS_CODE and the QA frontend on localhost:3004 for scripts/audit_frontend_api.py; AUDIT_RATE_CHECK=1 includes proxy rate-limit verification. Never copy a real key into these scripts or command arguments.

Evidence files in the updated ZIP: backend-tests.xml, before.xml, feed-before.xml, coverage.json, live-http.json, frontend-http.json, gemini.json and security.json. Reports: docs/comprehensive-audit.md, docs/comprehensive-audit.json and the PDF under audit/. Databases, installed dependencies and private .env files are intentionally excluded.

## 10 / Remaining acceptance and delivery

What is verified locally, what still needs configuration, and how this report maps to the source

| Item | Current status / next action |
| --- | --- |
| Public full-stack deployment | Pending configured Python hosting, HTTPS, persistent SQLite storage, access secrets and restart checks. Existing Sites URL is a separate static demo. |
| Real Web Push | Implementation and controlled tests pass; actual subscribe path is configuration-blocked. Needs VAPID keys, user opt-in, HTTPS and a real browser/device delivery check. |
| Physical mobile acceptance | Earlier browser width checks passed; physical device, installed PWA and target-host cookie behavior remain unverified. |
| Provider lifecycle | The configured Gemini key works now. Rotate the previously exposed credential; confirm quota/billing and provider availability for ongoing use. |
| Production operations | One backend worker; process-local locks/limits, SQLite and non-resumable background jobs. No production load/penetration test, distributed queue or per-user isolation claimed. |
| Source completeness / rights | NSE history is explicitly partial and best effort. Provider uptime, exhaustive archive completeness and redistribution rights are not established by code tests. |
| General extraction | Arbitrary financial-table extraction, OCR, semantic guarantees and broad classifier accuracy evaluation remain future work. |
| Containers / submission | Compose/Render configuration exists, but Docker execution was not verified here. No email sent; owner identity/contact fields still need completion. |

Implementation identity: the audit began at Git revision 21f98d47a1c06146ee88fe652bdd1718527c5142. The delivered ZIP RELEASE_MANIFEST.json records its final committed revision. The application-source digest below identifies the tested implementation independently of subsequent report-only changes.

SHA-256: b63acf103721fa1e70269eb568b73e4a238b6acb3021a7278b59c5cd26f1b00e

Digest scope: 47 application files; sorted relative POSIX path, NUL, CRLF-normalized content, NUL. Excludes tests, scripts, docs, private configuration and generated artifacts. Exact configured-key scan: 0 matches in publishable source; .env is ignored. ZIP contents are checked separately during packaging.

Review conclusion: all registered business routes have passing controlled tests, all three Gemini call sites have genuine successful provider responses, and the live backend/frontend paths pass within the documented configuration limits. These results support the local prototype; they do not replace the remaining public-host/device acceptance work.
