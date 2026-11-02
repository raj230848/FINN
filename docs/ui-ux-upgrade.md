# FINN UI, name search and freshness upgrade — 2 November 2026

This implements the mandatory P0 and P1 work in the supplied FINN UI/UX Enhanced Name Search Theme Plan. The optional P2 workflow additions are not part of this release. The earlier audit PDFs remain historical evidence for their recorded revisions.

## What changed

- **Midnight Orchid and Warm Ivory:** a visible theme switch, persisted before first paint, shared semantic colors across cards, charts, dialogs, notifications and native selects. Page glows are CSS only. Controls have visible focus, explicit chevrons and 44px minimum button targets; reduced-motion preferences are supported. Canonical tokens live in `frontend/app/themes.css`, imported by the root layout after legacy styles.
- **Name-first NSE search:** both header and Research use a bounded, debounced, keyboard-accessible autocomplete backed by protected `GET /api/company-search`. The bundled official directory contains 2,635 entries, retrieved on 2 November 2026. Names, legal suffixes, punctuation and ticker prefixes are normalized; ambiguous names require a choice. A selected issuer opens its Source library. Unknown names never become guessed symbols. Sector appears only where locally known.
- **Directory maintenance:** the verified exchange CSV is cached locally, refreshed after seven days, with one-hour retry suppression on failure. Cached results remain usable while a network refresh runs outside the directory lock. Source dates and stale/failure warnings remain visible. Responses are bounded to 20 entries and queries to 100 characters; public-mode requests are rate-limited.
- **Sourced-first launch:** sourced data is the initial and hard-reload mode. Demo is explicit and never persisted. Changing modes clears rows and counts from the other mode. Demo's action is “Replay example” and makes no ingestion request.
- **Controlled refresh:** cached SQLite data appears before background ingestion. Tabs share a persisted run and a reservation lock in the supported single-worker backend. Announcement checks follow the configured cadence (60 minutes by default). Failed/partial runs retry after 5, 10, 20 and 40 minutes, bounded by the normal interval. Manual refresh joins an active run. Actual market session dates are preserved; a post-18:30 IST check is limited by the last fetch, and catch-up is bounded to 31 days. An unexpected ingestion failure now completes as failed rather than leaving an endless spinner.
- **Research and trust:** zero-document issuers show Discover → review link → Import → indexed pages → Ask. Filing and alert research actions preserve ticker and question context without implying causality. Volume alerts explain the actual previous-session sample, mean, ratio and configured threshold. Reviewed financial source/basis labels and unavailable EBITDA remain intact.
- **Mobile and speed:** full-width mobile autocomplete, shared native selects, scrollable short-screen navigation, solid reading surfaces and lazy-loaded chart/research modules. Existing cached data remains visible during same-mode failures.

Official directory source: [NSE securities available for trading](https://www.nseindia.com/static/market-data/securities-available-for-trading), [equity directory CSV](https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv). An exchange-directory match verifies symbol identity, not the completeness or freshness of research coverage.

## Running this release

Open http://127.0.0.1:3000 after the normal setup/start scripts. Use the header theme button and search “HCL Technologies”, “HCLTECH”, “Info” or “Google”. The full application has 26 protected business operations, including the new directory search; existing readiness/session routes are separate.

The current local private `.env` enables `ENABLE_SCHEDULER=true` with one backend worker. Distributed environment examples keep scheduling opt-in. Set it true for an unattended single-worker installation; do not run independent schedulers against the same database. The frontend's freshness check works independently on app open. Automatic ingestion does not invoke paid Gemini classification.

## Acceptance evidence

| PDF ID | Result and evidence |
|---|---|
| A01–A03 | Browser verified sourced launch, explicit Demo and sourced hard reload; theme preference survives but Demo does not. Mode transitions clear old rows/counts. |
| A04 | Existing SQLite snapshot paints before the asynchronous freshness check. Same-mode errors retain the snapshot. |
| A05–A06 | Real local automatic refresh completed with a displayed timestamp. Tests verify concurrent reservations from separate database sessions reuse one run; fresh requests skip and manual requests reuse an active run. This is a single-worker guarantee. |
| A07 | Automated provider-failure, cooldown, cached-directory and fatal-run tests pass; prior resilience tests also pass. No claim of inducing a live provider 429. |
| A08 | Automated completed-session/EOD cutoff and existing calendar/session regressions pass. The live browser correctly shows 30 October market data on 2 November before the cutoff. No multi-day observation was performed. |
| A09 | Both themes and persisted light reload verified in browser; bootstrap/storage-failure tests pass. |
| A10 | Shared native selects used across filters, research, preferences and market controls; visible chevrons and 44px height inspected. |
| A11–A13 | Actual HCL name/ticker searches agree; Google has a useful empty state; CERA zero-document onboarding inspected. HCLTECH already has an imported annual report in this local database. |
| A14 | Existing citation, retrieval, support-review, refusal and extractive-fallback tests pass. Reviewed INFY quarters/basis/unavailable EBITDA inspected. No new paid Gemini call was made: credential rotation remains unconfirmed. |
| A15 | Filing/alert actions pass ticker and explicit contextual question into research. Browser context check recorded with screenshots/evidence. Actual physical-device push delivery remains an external gate. |
| A16 | Browser viewports of 360px, 390px and desktop inspected; no document horizontal overflow in recorded checks. This is emulation, not physical-phone acceptance. |
| A17 | Both palettes' defined text/status pairs meet 4.5:1 and control-boundary pairs 3:1 in automated checks. Visible keyboard focus inspected. This is not a formal full WCAG certification. |
| A18 | 272 backend tests and 14 frontend tests pass, including authorization, proxy/session regressions and the updated 26-operation inventory. Production build includes type checking. |
| N01–N02 | Actual 2,635-entry directory search verified HCL name/ticker and out-of-watchlist issuers; automated fixtures also cover them. |
| N03 | Normalized names/prefixes and bounded ranking tests pass; browser “Info” Enter leaves ambiguous choices open. |
| N04 | Unknown/foreign names return no invented listing. Failed refresh retains cached identities with warnings; invalid/incomplete files are rejected. |
| N05 | Selected results open Source library, with explicit discovery/import path for zero documents. |
| N06 | Research continues using the selected verified ticker, existing primary-source guards and protected APIs. No new live Gemini acceptance is asserted. |
| T01–T03 | Dark/light desktop/mobile inspections, persisted-theme tests, keyboard selection, ambiguous Enter and native select checks are recorded in the release evidence. |

## Validation and limits

Current evidence is included in the ZIP under `audit/ui-ux/`: backend/frontend JUnit, live search responses, browser checks, production build result and screenshots. The release manifest identifies the exact committed source. Earlier audit PDFs and their metrics are explicitly historical.

The supplied PDF excludes new hosting and credentials. This release does not change the separate static ChatGPT Sites demonstration. No credential, runtime database, installed dependency, confidential input PDF or build cache belongs in the ZIP. Account-owner credential rotation, fresh live Gemini acceptance, physical phone/push-service delivery and public full-stack hosting remain unverified external checks.
