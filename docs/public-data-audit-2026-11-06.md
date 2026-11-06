# FINN public-data audit — 6 November 2026

Public URL: https://finn-investment-desk.bk291269.chatgpt.site/

The public app contains sourced records, but its sections have different update coverage. A successful market refresh does **not** make every research extract or financial table current. Prices are adjusted end-of-day observations, not live exchange quotes.

| Section | Verification and freshness | Remaining limits |
| --- | --- | --- |
| Overview, price charts, volume and watchlist | All 1,170 observations for 18 companies matched a fresh Yahoo Finance history fetch. Every displayed daily change and available volume ratio was recalculated. Latest completed session: 5 November 2026. Charts use actual daily points and linear segments. | Provider data can be delayed or revised. A match against Yahoo is not independent exchange certification. |
| Signals and alerts | Every one of the initial 280 stored filings matched NSE. The archive refresh now reconciles 31 days, including ZIP disclosures and announcements without PDF attachments. Original timestamps and source links are retained. | Headline priority is a deterministic review aid; it does not verify financial impact or predict returns. Exchange access can fail. |
| Financial snapshot | Reviewed coverage is Infosys, TCS and Wipro. Eleven quarter records were checked for numeric presence on their cited issuer pages. Wipro now publishes five reviewed quarters through FY27 Q2. Quarter selection uses the correct adjacent fiscal quarter and same-quarter prior year, currency and accounting basis. | Infosys and TCS remain historical FY25 Q4 reviewed coverage. Both issuers have newer FY27 Q2 releases; those tables have not been transcribed and reviewed for this release. The other 15 companies have no reviewed financial tables in the public feed. EBITDA remains unavailable where unreviewed. |
| Promise Tracker | Eight reviewed records: four Infosys FY25 revisions and four Wipro quarterly outlooks. Latest reviewed statement: 15 October 2026. Wipro's unreported December-quarter result stays pending. Selected company persists across refresh. | Reviewed coverage is two companies. New issuer statements are added after source review, not automatically extracted from every filing. Infosys's historical revisions are not its current FY27 outlook. |
| Research desk | All 27 prepared excerpts matched their original cached source-page text and source-file checksums. Coverage is Infosys, TCS and Persistent. Unsupported questions return insufficient evidence. | Historical excerpts, not continuously updated document research. No Gemini model is connected to the public Site. The other 15 companies have no prepared extracts. |
| Source library | Eleven historical source entries across Infosys, TCS and Persistent. Document title, original period, original URL and actual page references are preserved. Financial and guidance cards also link their own issuer sources. | Not a complete or current library of every company filing. Wipro sources are linked from its financial/guidance cards; prepared Wipro research extracts are absent. Arbitrary document imports require the full backend application. |
| Saved items, monitoring and notifications | Watchlist/preferences/read state are device-local. Notifications retain original source dates. Category filters now apply to new filing notifications. Busy filing days no longer stop dashboard totals or event recording at the first 100 rows. | Refreshing on another device does not synchronize personal state. Public notifications are in-app events, not verified background push delivery. |
| Company search | Covered company names and NSE tickers resolve from the prepared 18-company portfolio. Unknown symbols fail clearly. | Arbitrary NSE discovery requires the full backend; the static public Site cannot add live coverage for every ticker. |

## Corrections shipped in this audit

- Republish reviewed financial tables with every cloud data run; include Wipro's five reviewed quarters.
- Honor requested financial quarters and leave missing adjacent-quarter comparisons unavailable.
- Keep historical research and reviewed-quarter coverage explicit in the interface.
- Apply monitoring categories to newly recorded filing notifications.
- Count all matching disclosures on busy filing days, while keeping user-facing pagination.
- Preserve monotonically increasing filing IDs after old archive records expire.
- Reconcile the full rolling 31-day filing window.
- Replace missing attachment placeholders with NSE's genuine announcement page. Distinguish PDF, ZIP and exchange-page links in the interface.
- Reject non-finite financial values and unverified financial source hosts from update payloads.

## Validation and evidence

The audit includes real-provider fetches, source-page checks, public adapter checks, frontend tests, backend tests and a production Site build. Local raw evidence is saved under `artifacts/audit-2026-11-06/`, which is ignored by Git. Public-code tests use isolated data and never consume a Gemini key or send notifications.

The complete backend run passed 313 tests before the four new missing-attachment cases were added; the focused ingestion/publisher run then passed 37 tests. The public regression suite passed 14 tests and the frontend suite passed 27 tests. Final GitHub validation runs the complete suites, builds and isolated full-stack container again. The final live audit matched 284/284 retained filings, 1,170/1,170 market observations and 27/27 source extracts. All 359 public adapter cases passed, including every covered company and reviewed financial period.

Initial live source comparison: 18/18 companies, 1,170/1,170 price/volume observations, 280/280 stored filings and 27/27 research extracts. The provider's larger raw filing response also contained records outside the rolling archive, valid ZIP attachments and a missing-attachment placeholder; raw row counts were not treated as proof of newly published filings.

Original sources for current-release availability: [Infosys FY27 Q2](https://www.infosys.com/investors/reports-filings/quarterly-results/2026-2027/q2.html), [TCS FY27 Q2](https://www.tcs.com/who-we-are/newsroom/press-release/tcs-financial-results-q2-fy-2027), [Wipro FY27 Q2 statements](https://www.wipro.com/content/dam/nexus/en/investor/quarterly-results/2026-2027/q2fy27/consolidated-financial-statement-q2fy27.pdf).

## Conclusion

No simulated records were found in the sourced public feed. Market prices and filings can update automatically; financial, guidance and research coverage remains limited to reviewed sources. The public Site should not be described as complete live research coverage of every company. Automated checks cannot certify every possible future provider failure or every financial interpretation.
