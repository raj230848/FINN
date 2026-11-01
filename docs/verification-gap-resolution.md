# FINN - Verification Gap Resolution

Current implementation: `8407d083a048bcfdce1870c81351f2b570790818`. Latest raw evidence and release identity are in the ZIP manifest.

## 01 / Changes and verified results

FINN | Verification-gap response | 1 November 2026

The review correctly separated a working local prototype from unproven public/device acceptance. This update closes code and reproducibility gaps, validates a real full-stack container, and retains explicit external gates. It does not claim that every edge case or a public production deployment is proven.

| Check | Current evidence |
| --- | --- |
| Backend suite | 248 passing tests, 0 failed; all 25 registered business operations covered by the controlled inventory test. |
| Frontend | 11 passing Node tests; TypeScript and production build passed locally and in GitHub Actions. |
| Coverage | 91.7% statements (1389/1514); 79.2% branches (355/448). |
| Real local durability | 7 checks passed across actual FastAPI process stop/start; saved preferences/watchlist/read history/documents/chunks/completed sync retained. |
| Real local resilience | 9 checks passed: production proxy detects lost backend, returns recoverable 503, recovers existing sessions and isolates logout between two HTTP cookie jars. |
| Full-stack Docker CI | Root image built and ran on Ubuntu; 35 protected-app checks passed, 0 failed. Container restart retained the saved QA preference marker. |
| Mobile browser view | 360px and 390px emulation: no horizontal document overflow in new operational panel. Temporary viewport restored; physical phone remains unverified. |

Implementation: a combined Next.js/FastAPI hosting image and supervisor; public minimal readiness; protected source/model/outbox status and mobile panel; interrupted-refresh recovery; trusted public-origin and Secure-cookie handling; push subscription key-rotation guard; automated host/device acceptance tools and updated submission runbooks.

CI evidence: https://github.com/raj230848/FINN/actions/runs/41323904107 . Backend, frontend and full-stack-container jobs all completed successfully for implementation commit 8407d083a048bcfdce1870c81351f2b570790818. No paid Gemini or browser-push calls were made by the container check.

## 02 / Item-by-item disposition

P0 acceptance gates first; P1 improvements verified within scope; P2 expansion remains conditional

| Review item | Status | Change / remaining requirement |
| --- | --- | --- |
| P0.1 / public stack | Code + container verified; public host pending | Root Dockerfile/Render Blueprint host both services on one origin, persistent disk and one worker. Backend is loopback-only. Real host account/URL not provided. |
| P0.2 / deployed operations | Checker + CI verified; target HTTPS pending | Same-origin sign-in, cookie flags, schema fields, saved side effects, renewal/logout and 25-operation inventory. CI: 35 checks pass; 20 operations exercised; 5 explicitly not verified. |
| P0.3 / actual phone | Browser checks pass; physical device pending | New panel checked at 360px/390px without horizontal overflow. Physical Android/iOS, slow network and installed PWA runbook/template supplied. |
| P0.4 / key rotation | Account-owner action pending | Exposed-key rotation is not confirmed. Current secret remains private. Earlier four real Gemini calls remain historical evidence; no post-rotation call is claimed. |
| P0.5 / submission | Package/repo/draft ready; final details pending | Matching full ZIP, manifest/checksum, raw evidence and actual redacted visible-chat export. Actual hosted URL, owner/contact and email submission remain unfinished. No email sent. |
| P1 / browser push | Private local setup + code tests; device pending | VAPID pair generated privately; public-key configuration available locally. Key mismatch replaces an old subscription only on user opt-in; failed unsubscribe stops replacement. Permission-denial recovery text added. |
| P1 / durability | Local processes + CI volume verified | Seven real SQLite restart checks pass. Unfinished jobs become interrupted with partial data retained. CI container restart retains saved preference. Target-host disk test still required. |
| P1 / monitoring | Implemented and tested | Protected operations endpoint and mobile status panel: source age/session/coverage, last sync, bounded model latency/token/outcome metadata, auth/rate counters, push outbox counts. Counters reset per process. |
| P1 / security | Code/controlled/local checks; target-host pending | Trusted public origin for TLS-terminating proxy and Secure cookie selection; readiness returns no desk/internal data. Existing SSRF/resource/origin/rate guards retained. Public HTTPS/egress/load acceptance remains. |
| P2 / broader accounting | Deferred scoped enhancement | Keep 11 reviewed financial rows, explicit units/PAT bases and unavailable EBITDA. No unreviewed general extraction or invented metrics added. |
| P2 / broad classifier score | Not claimed | Existing synthetic integration checks and deterministic regression cases retained; no expert-adjudicated precision/recall dataset or broad accuracy claim. |
| P2 / parser scale | Existing limits retained; more hardening future | Bounded downloads/pages, unsupported PDF failure and private-address/redirect checks remain tested. No new OCR, parser sandbox or large-volume guarantee claimed. |

The existing portfolio, sourced digest/threshold rules, provenance, financial comparability and guidance views are retained. The earlier 227-test report is preserved as history. The matching updated ZIP now includes raw current tests, coverage, actual restart/resilience results and the exact downloaded container-acceptance JSON, addressing the review's missing-bytes concern.

## 03 / Complete current API inventory

Original 24 business operations plus GET /api/operations; frontend adds public GET /api/ready

| Method | Registered backend path | Controlled | Docker CI |
| --- | --- | --- | --- |
| GET | /api/alerts | PASS | PASS |
| GET | /api/announcements | PASS | PASS |
| GET | /api/announcements/{filing_id}/context | PASS | PASS |
| GET | /api/companies | PASS | PASS |
| GET | /api/companies/{ticker}/documents | PASS | PASS |
| GET | /api/companies/{ticker}/financials | PASS | PASS |
| GET | /api/companies/{ticker}/guidance | PASS | PASS |
| GET | /api/dashboard | PASS | PASS |
| GET | /api/health | PASS | PASS |
| GET | /api/notifications | PASS | PASS |
| GET | /api/operations | PASS | PASS |
| GET | /api/preferences | PASS | PASS |
| GET | /api/push/config | PASS | PASS |
| GET | /api/push/status | PASS | PASS |
| GET | /api/sync/{run_id} | PASS | not verified |
| PATCH | /api/companies/{ticker} | PASS | PASS |
| POST | /api/companies/{ticker}/discover | PASS | not verified |
| POST | /api/documents | PASS | not verified |
| POST | /api/notifications/read-all | PASS | PASS |
| POST | /api/notifications/{event_id}/read | PASS | PASS |
| POST | /api/push/subscribe | PASS | not verified |
| POST | /api/push/unsubscribe | PASS | PASS |
| POST | /api/research | PASS | PASS |
| POST | /api/sync | PASS | not verified |
| PUT | /api/preferences | PASS | PASS |

CI deliberately omitted real source refresh/sync polling, new-company discovery/import and genuine browser subscription. Those five operations remain not verified in that environment; they are not 200-only substitutes. Earlier live Yahoo/NSE/Gemini/HCLTECH results remain attached as historical evidence. The new host checker can run refresh/Gemini/new-issuer paths with explicit QA flags when the actual target is available.

GET /api/ready is the only new public frontend status route. It returns a minimal readiness result and does not bypass authentication for desk data. Public-mode proxy/session protections remain; an external HTTPS host must still verify Secure cookies on its actual domain.

## 04 / Process evidence and safeguards

Actual local service processes; bounded controlled model/security tests; independent CI container

| Restart / retained state | Observed |
| --- | --- |
| preference retained | PASS |
| watchlist retained | PASS |
| read state retained | PASS |
| documents and chunks retained | PASS |
| partial refresh marked interrupted | PASS |
| completed sync retained | PASS |
| sqlite wal enabled | PASS |

| Production proxy / sessions | Observed |
| --- | --- |
| not ready without backend | PASS |
| backend outage recovers cleanly | PASS |
| ready after backend start | PASS |
| existing session survives outage | PASS |
| two active sessions | PASS |
| logout is device local | PASS |
| readiness detects lost backend | PASS |
| proxy reports lost backend | PASS |
| same session recovers after restart | PASS |

The restart test retained 18 companies, 11 bundled documents, 3,071 chunks and 10 event records in its fresh disposable database. It preserved the completed sync and retained a successful partial price result while marking the unfinished run interrupted. The main private runtime database was backed up before its upgrade; QA tests did not target it.

Operational metrics accept fixed component/outcome names and bounded integer token/latency metadata only. They do not store questions, provider bodies, cookies, API tokens, client IPs or push subscriptions. Source fetch age is calculated from each watched company's latest available session, so old retained history does not falsely label a newly fetched series stale; missing companies remain partial.

The new trusted-origin tests cover TLS termination with an internal HTTP request, malicious origins and insecure remote configuration. Push tests cover matching key reuse, key replacement order, failed unsubscribe and malformed keys. Existing malformed-provider/citation/numeric/SSRF/resource/partial-sync tests remain passing. These are finite checks, not semantic model proof or a penetration-test certificate.

## 05 / External acceptance and delivery

Do not turn local/CI results into a public-host or physical-device claim

| Acceptance area | Current disposition |
| --- | --- |
| A. Source / secrets | Matching full source ZIP, checksum and evidence provided. .env ignored; exact configured-secret scan found 0 source matches. Account-owner Gemini revocation/rotation remains unconfirmed. |
| B. Backend | Container and local persistence verified. Actual public HTTPS service, host disk/restart and all routes on the target evaluator desk remain pending hosting access. |
| C. Frontend / phone | Build, origin controls, proxy outage and two sessions verified within local/CI scope. Physical Android/iOS, public TLS cookies, PWA and slow mobile network still need observation. |
| D / E. Digest / market | Existing sourced rules and provenance retained. Earlier actual-provider results preserved. Repeat on the public target to establish its network access and source freshness. |
| F / G. Gemini / new issuer | Earlier genuine calls and HCLTECH workflow are history, not post-rotation/hosted proof. Use --qa --gemini --ticker on the target and inspect primary pages manually. |
| H. Optional push | Private VAPID configuration and subscription guards ready. Actual browser permission, background receive, device display, expired subscription and opt-out need the real device. |
| I. Submission | Covering draft now separates the actual full-stack URL from the static demo. Owner/contact/verified URL and final email remain pending. No email sent. |

Next steps: connect the prepared Render Blueprint (one paid service with persistent disk), set a rotated Gemini key and private VAPID values, run scripts/verify_hosted.py against a separate QA frontend with --qa --refresh --gemini --ticker HCLTECH, then complete docs/hosted-acceptance.md on a physical phone. Never put the desk code or replacement key in command arguments, the report or ZIP.

Package includes both the historical full audit and this current change report. RELEASE_MANIFEST.json records the final committed source revision. The application-source digest identifies the tested implementation independently of report-only commits: ca9ebcb79f22b43298872b819a6e0d08c873fee3622f77e3089e4dac857da827.

Digest scope: 51 application files; sorted relative POSIX path + NUL + CRLF-normalized content + NUL. Private .env, databases, new full issuer PDFs and installed dependencies are excluded from distribution. Remaining multi-day scheduling, real-world classifier evaluation, arbitrary accounting/OCR and production load/egress tests are explicitly not claimed.
