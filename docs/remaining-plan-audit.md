# Remaining-plan audit and delivery

This is the item-by-item review of the supplied 11-page implementation plan. Existing Next.js/FastAPI components were extended. External verification is distinguished from code implementation; no credential, hosted service, device test or email submission is invented.

## P0 and acceptance gates

| PDF item | Before this update | Result / evidence |
| --- | --- | --- |
| Mobile-first desk; 18-stock portfolio | Implemented | Preserved. Source and financial workflows checked at 360px and 390px; no document overflow in those views. |
| Genuine Gemini setup | Provider boundary implemented; root key empty | Now configured privately from the earlier PDF at the owner’s explicit request. Google returned HTTP 200. The exposed key should be rotated; no usable key is shipped. |
| Two real sourced Gemini answers | Mock-only verification | Now verified: two uncached Gemini 3.5 Flash-Lite answers passed source/citation and claim-support checks, and both were read through the frontend proxy. See `gemini-live-verification.json`. Explicit refresh bypasses cache for provider verification. |
| Wrong model/quota/timeout and fallback | Bounded provider tests existed | Preserved. Expanded checks reject false-but-cited claims, uncited headings and numbers borrowed from an uncited passage. Model failures return extractive evidence. |
| Selective model use | Implemented | Numeric changes, deduplication, feeds and thresholds remain deterministic. Gemini synthesizes and separately reviews claim support. |
| Real Yahoo refresh for all watched tickers | Adapters implemented | Verified for all 18 watched companies; latest completed session 30 October 2026. `source-verification.json` and `release-acceptance.json`. |
| Real exchange ingestion | Adapter implemented | Verified: 73 matching filings on the default window; subsequent 30-day run matched 235, inserting 162 additional rows in the private QA copy. Exact repeat identities collapse. |
| Sourced 24h/7d/30d digests | Implemented; incomplete history labelled | Verified counts 3/40/98 after QA backfill. Requested windows remain best effort; this is not an exhaustive exchange archive. |
| Earliest observation, latest fetch, gaps and paging | Backend metadata existed; UI incomplete | Added explicit first-observed date, unknown legacy observation count, last fetch, loaded/total counts and a 30-day backfill action. |
| Real EOD threshold and repeat-event checks | Implemented | QA low-threshold test produced 21 dated sourced alerts, zero additional duplicate events on recalculation, and restored original preferences. No intraday monitoring is claimed. |
| Frontend install/type/security/build runbook | Earlier production build passed | Reinstalled the lockfile with `npm ci`; type and access tests passed. Final build results are recorded in `verification.md`. |
| Browser-to-backend routing | Implemented | Local full application and private QA API tested; source refresh, financial selectors, guidance and notification history use the same-origin proxy. |
| New issuer import and unseen ticker | Generic flow implemented | Repeated actual POLYCAB discovery, 20-page October 2026 transcript import and six citations. Also imported Wipro's current issuer statement in QA and verified Q2 FY27 retrieval. |
| Live Python hosting, HTTPS, public restart/persistence | Deployment configuration existed | Externally blocked: no configured Python host/account or deployment URL supplied. The public Sites URL remains the separately labelled static demo. No paid service was created. |
| Hosted session/access-code checks | Implemented and locally tested | Preserved signed sessions, server-only backend token, origin guards and public route limits. Target-host incognito/second-device/restart checks remain pending that deployment. |
| Local persistence/migration | Implemented | New push recipient/outbox tables are additive at startup; existing companies, documents, watchlist/preferences and history remain. A private pre-upgrade backup is retained in artifacts. |
| Physical phone demonstration | Browser checks only | Not verified on a physical phone. Width emulation does not establish physical-device or public-backend acceptance. |
| Redistribution rights | Issuer PDFs already bundled | Not established by this implementation. New Wipro full PDFs remain in private review artifacts; the package adds only reviewed numeric rows, provenance and original URLs. Existing issuer copyrights remain with the issuer. |
| GitHub and README | Public repository exists | Updated source, setup, verification and deployment instructions. Actual source revision is in the ZIP's release manifest. |
| Real AI build history | Only a decision log shipped | Added an exporter for actual saved user/assistant messages. A private redacted text export is included under `submission/` in the delivered ZIP; internal instructions, reasoning and tool output are excluded. It is not a raw session trace. |
| Covering email | Draft with placeholders | Updated verified links, actual history attachment and omissions. Name/contact placeholders still need the owner's details. No email was sent: the user's request is to implement and package the project. |

## P1 improvements

| Task | Implementation and acceptance |
| --- | --- |
| P1.1 proactive delivery | Added standards-based opt-in Web Push: device subscription, enable/disable, recipient eligibility, durable outbox, bounded retries, delivery acceptance timestamp and sanitized failures. Only new qualifying sourced events are queued. Service-worker receipts and stable tags suppress repeated display. Controlled sender tests cover idempotency, retry timing, opt-out and history exclusion. **Real push-service/device display remains unverified** until server VAPID keys and a browser opt-in are configured. |
| P1.2 significance and trust | Added contract/letter-of-award examples. A real audio-recording filing found during QA now stays an earnings-call update rather than being labelled new financial results. Ambiguous management changes stay needs-review. Original URLs and rule rationale remain visible. |
| P1.3 filing enrichment | Added source-only executive-background snippets when explicitly present in the filing description, otherwise an identity/review warning. No biography is invented. Results link to a reviewed comparison only for an explicitly matched quarter; unrelated historical figures are not asserted as that filing's results. |
| P1.4 more quarterly analysis | Added WIPRO's five consecutive quarters from Q2 FY26 to Q2 FY27, original IFRS statement page 3 and SHA-256 provenance. INR million and group PAT including non-controlling interests are explicit. EBITDA stays unavailable. Quarter selector and Labour Code exceptional-item notes added. Zero/negative bases, missing quarters and currency/basis mismatches are tested. |
| P1.5 second guidance company | Added Wipro's three completed distinct quarterly CC-growth targets and one pending future target. Each completed comparison has separate original guidance/result links. Nominal USD revenues are not compared to fixed-rate guidance. Units, period, metric and basis must match; mismatches are excluded. Infosys's four revisions remain one target. |
| P1.6 unseen company | Verified live POLYCAB path again; no INFY/TCS hardcoding. Unsupported/unknown tickers return honest errors or insufficient evidence. |

## Conditional P2 work and remaining limits

Period/quarter-aware retrieval and a separate model claim-support review are implemented. Each numeric claim is checked against its own citations. This conservative review can fail closed; it does not prove semantic entailment. Adversarial tests cover a false directional claim with a valid citation and a number present only in another retrieved passage.

General automatic accounting-table extraction from arbitrary reports remains optional future work. The plan explicitly treats it as conditional and prioritizes focused, verified views. No unreviewed model extraction is published as a financial fact. Multi-user accounts, OCR, broker commentary, trading and production job queues are not claimed.

Live Gemini is now verified locally; rotate the previously exposed credential for ongoing use. External acceptance still needs a live Python hosting account/URL, real browser push opt-in, physical-device checks and final submission details. These cannot be established by adding source files or changing a health flag.
