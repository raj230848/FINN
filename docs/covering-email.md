To: assessment@enam.com
Subject: ENAM - IIT screening - 2027

Dear ENAM team,

Please find my FINN prototype, a mobile-first investment intelligence workspace that connects a prioritised portfolio digest with primary-source company research.

Prototype: [INSERT VERIFIED DEPLOYED URL]
Repository: [INSERT ACTUAL GITHUB URL AND ACCESS DETAILS]
AI build history: [INSERT REAL CONVERSATION EXPORT OR SHARE LINK]

FINN monitors an 18-company NSE portfolio, explains disclosure priorities, and lets the investor configure end-of-day price and volume alerts. Research preserves the original document, period and page behind each passage. Its accountability view compares four revisions of Infosys's FY25 revenue guidance with the reported outcome, avoiding the misleading treatment of revisions as independent promises.

I used Next.js/TypeScript for the responsive desk and FastAPI/SQLAlchemy/SQLite for a small, traceable backend. Financial arithmetic, scoring, deduplication and threshold evaluation are deterministic. Page-preserving retrieval and caching reduce model cost; structured AI synthesis is optional, while no-key operation transparently returns source extracts.

I prioritised the digest-to-evidence workflow and explicitly separated sourced data from synthetic demonstration scenarios. Reviewed financial tables and guidance pairs are focused on Infosys; the document/research engine accepts unseen NSE tickers where sources are available. I deliberately excluded trading, intraday tick monitoring, multi-user accounts, OCR and broker commentary. Wider accounting-table extraction, stronger claim-entailment evaluation and durable hosted background jobs would be my next improvements.

Setup, reproducible demonstration scenarios and verified limitations are documented in the repository. Thank you for reviewing my submission.

Regards,
[YOUR NAME]
[YOUR CONTACT DETAILS]
