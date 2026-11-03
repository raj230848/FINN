To: assessment@enam.com
Subject: ENAM - IIT screening - 2027

Dear ENAM team,

Please find my FINN prototype, a mobile-first investment intelligence workspace that connects a prioritised portfolio digest with primary-source company research.

Full-stack prototype: [ADD THE ACTUAL VERIFIED HTTPS FRONTEND URL]
Public site: https://finn-investment-desk.bk291269.chatgpt.site/ (dated Yahoo Finance and NSE snapshots)
Repository: https://github.com/raj230848/FINN (public)
AI build history: attached AI_BUILD_HISTORY_REDACTED.md (actual saved user/assistant messages; private/internal/tool content excluded)

FINN monitors an 18-company NSE portfolio, explains disclosure priorities, and lets the investor configure end-of-day price and volume alerts. Research preserves the original document, period and page behind each passage. Its accountability view compares four revisions of Infosys's FY25 revenue guidance with the reported outcome, avoiding the misleading treatment of revisions as independent promises.

I used Next.js/TypeScript for the responsive desk and FastAPI/SQLAlchemy/SQLite for a small, traceable backend. Financial arithmetic, scoring, deduplication and threshold evaluation are deterministic. Page-preserving retrieval and caching reduce model cost; structured AI synthesis is optional, while no-key operation transparently returns source extracts.

I prioritised the digest-to-evidence workflow and explicitly separated sourced data from synthetic demonstration scenarios. Reviewed tables cover Infosys, TCS and five current Wipro quarters. Guidance comparisons cover Infosys revisions and distinct Wipro quarterly targets; the document/research engine accepts unseen NSE tickers where sources are available. I deliberately excluded trading, intraday tick monitoring, multi-user accounts, OCR and broker commentary. The latest update adds a single-origin deployment configuration, interrupted-refresh recovery and operational status. Live Gemini call sites were verified locally in the earlier audit. Real browser-push display, the rotated-key check and target-host/physical-phone acceptance must be completed and recorded before claiming submission readiness. Wider accounting-table extraction remains future work.

Setup, reproducible demonstration scenarios and verified limitations are documented in the repository. Thank you for reviewing my submission.

Regards,
[YOUR NAME]
[YOUR CONTACT DETAILS]
