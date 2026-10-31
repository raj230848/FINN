# Roadmap implementation record

The supplied confidential roadmap was used as a requirements reference. Neither it nor its credential appendix is included in this repository. This delivery implements the P0/P1 reliability work; the P2 extraction and production-platform work remains a separate phase.

## Delivered

| Area | Result |
| --- | --- |
| Gemini | Server-only `GEMINI_API_KEY`, default `gemini-3.5-flash-lite`, structured schema validation, bounded request/output sizes, three attempts for transient failures, sanitized errors and extractive fallback. Failed model calls are not cached as successful synthesis. |
| Grounding | Versioned prompts/caches, supplied citation IDs only, citation coverage per substantive segment, and numeric-literal checks against retrieved passages. These checks do not prove semantic entailment. |
| Classification | Expanded wording for directors/CFO/KMP, insider/promoter transactions, schemes, pledges and rating changes. Ambiguous material outcomes and proposed leadership changes remain visible as needs-review. Model classification requires a quoted source substring and confidence; deterministic priority remains authoritative. |
| Identity/migration | Exchange identifier, canonical attachment URL and description checksum replace title-only identity. Different attachments/amendments survive. Additive SQLite migration preserves existing rows and leaves unknown legacy ingestion dates unknown. |
| Notifications | Durable, idempotent in-app filing/threshold events, unread counts, individual/all-read actions and persistent history independent of current alert recalculation. No email or push delivery is claimed. |
| Coverage | Bounded configurable NSE lookback, successful per-company fetch windows, first-observed dates, explicit partial-coverage messages and paginated feeds. Successful fetches are best effort, not proof of an exhaustive exchange archive. |
| Second company | Reviewed TCS Q4 FY25, Q3 FY25 and Q4 FY24 consolidated IFRS revenue/PBT/PAT in USD million. Source URLs, hashes and bounded reviewed table rows are retained. Net income is after non-controlling interests. EBITDA remains unavailable. |
| Hosted protection | Hosted proxy requires an access-code session, signs an eight-hour HttpOnly cookie, checks mutation origins, and keeps the backend token server-only. Public backend startup requires its token and expensive routes are throttled. This is one shared desk, not individual accounts. |
| Mobile | Dark colorful phone layout preserved; notification bottom sheet, coverage notice, pagination and quarterly metric cards work at a 390px viewport. |

## Configuration and operation

Use root `.env` for backend settings and `frontend/.env.local` for frontend settings. Never use a `NEXT_PUBLIC_` variable for credentials. The examples contain no usable credentials. Supply a newly rotated Google AI Studio key locally; never reuse the credential in the confidential appendix.

For a hosted full application, configure backend `PUBLIC_DEPLOYMENT=true` and `FINN_API_TOKEN`. Configure frontend `FINN_PUBLIC_MODE=true`, matching `FINN_API_TOKEN`, `FINN_ACCESS_TOKEN` (minimum 16 characters), `FINN_SESSION_SECRET` (minimum 32 characters), and HTTPS `BACKEND_URL`. Vercel/Render also enable the access gate automatically. Rotate the access code or session secret to invalidate existing sessions. Login throttling and backend route limits are process-local: retain the one-worker deployment assumption.

Before upgrading, stop the backend and make a SQLite backup with Python's SQLite backup API. Startup applies migration version 1 automatically. To roll back, stop both services, restore that private backup and run the previous code revision. Do not commit or publish the backup. Rehearsal on a private copy preserved all 19 companies, 78 announcements, 12 documents and 3,125 chunks; reviewed financial rows increased from 3 to 6.

New endpoints are `GET /api/notifications`, `POST /api/notifications/{id}/read` and `POST /api/notifications/read-all?mode=demo|sourced`. Announcement feeds accept `offset` and `limit` (maximum 300), return `total`, `has_more`, `next_offset` and `coverage`. The UI loads additional pages explicitly.

## Verification and remaining limits

Automated checks cover ambiguous classification, attachment identity, repeat migration, legacy dates, durable event/read behavior, 105-row pagination, coverage gaps, Gemini schema/retry/error boundaries, grounding rejection, transient fallback, backend throttling and signed-session tamper/expiry/rotation/origin rules. Mobile browser checks cover the bell/read-all flow, sourced coverage warning and TCS metric cards.

Live Gemini synthesis remains unverified: the local replacement-key setting was empty during validation. The no-key path remains usable and labelled extractive. No physical-device test, Docker execution or publicly hosted Python backend is claimed. The public ChatGPT Site is a static demonstration with synthetic market fixtures, historical reviewed facts, bounded source excerpts and device-local state; it has no model secret or live exchange feed.

P2 remains: general reviewed financial/guidance extraction across arbitrary documents, semantic claim-entailment evaluation, user accounts and isolated storage, durable hosted job queues and production operations. Source licensing/redistribution rights must be assessed for any wider commercial use; public URLs alone do not grant those rights.

Provider references: [Gemini 3.5 Flash-Lite](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite), [OpenAI-compatible endpoint](https://ai.google.dev/gemini-api/docs/openai), [structured output](https://ai.google.dev/gemini-api/docs/structured-output).
