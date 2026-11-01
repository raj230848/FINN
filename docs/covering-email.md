To: assessment@enam.com
Subject: ENAM - IIT screening - 2027

Dear ENAM team,

Please find my FINN prototype, a mobile-first investment intelligence workspace that connects a prioritised portfolio digest with primary-source company research.

Prototype: https://finn-investment-desk.justfrog26.chatgpt.site (public interactive demo; live ingestion/document imports require the full Python app)
Repository: https://github.com/raj230848/FINN (public)
AI build history: attached AI_BUILD_HISTORY_REDACTED.md (actual saved user/assistant messages; private/internal/tool content excluded)

FINN monitors an 18-company NSE portfolio, explains disclosure priorities, and lets the investor configure end-of-day price and volume alerts. Research preserves the original document, period and page behind each passage. Its accountability view compares four revisions of Infosys's FY25 revenue guidance with the reported outcome, avoiding the misleading treatment of revisions as independent promises.

I used Next.js/TypeScript for the responsive desk and FastAPI/SQLAlchemy/SQLite for a small, traceable backend. Financial arithmetic, scoring, deduplication and threshold evaluation are deterministic. Page-preserving retrieval and caching reduce model cost; structured AI synthesis is optional, while no-key operation transparently returns source extracts.

I prioritised the digest-to-evidence workflow and explicitly separated sourced data from synthetic demonstration scenarios. Reviewed tables cover Infosys, TCS and five current Wipro quarters. Guidance comparisons cover Infosys revisions and distinct Wipro quarterly targets; the document/research engine accepts unseen NSE tickers where sources are available. I deliberately excluded trading, intraday tick monitoring, multi-user accounts, OCR and broker commentary. Opt-in Web Push and a separate claim-support review are implemented, with live device delivery and Gemini authentication still awaiting private configuration. Wider accounting-table extraction and durable hosted background jobs remain next steps.

Setup, reproducible demonstration scenarios and verified limitations are documented in the repository. Thank you for reviewing my submission.

Regards,
[YOUR NAME]
[YOUR CONTACT DETAILS]
