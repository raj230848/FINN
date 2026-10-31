# Assessment interpretation and scope

Read against the two supplied ENAM PDFs, not just the larger master prompt.

The main brief was released 27 October 2026 and sets a deadline of Sunday, 1 November 2026. It asks for a mobile-first working prototype, GitHub repository, real AI build history, and a short covering email. The portfolio should contain 15–20 NSE/BSE companies and research must generalise to unseen NSE symbols. Research conclusions must use primary issuer documents, not news or broker commentary.

The brief explicitly treats its eight research categories, management biography enrichment, and particular screen interactions as examples. It rewards creativity, product judgment, architecture and cost efficiency; it prefers a narrow working workflow to a broad broken demo. The reference PDF supplies useful category names and financial definitions; it does not make every category a mandatory feature.

The supplied master prompt asks for a broader implementation. This version prioritises a complete daily workflow: scan a prioritised digest, change monitoring thresholds, inspect an unusual EOD move, then investigate the issuer and its evidence. It implements three real data adapters and a separate deterministic demonstration replay.

Implemented:

- 18-company portfolio spanning 12 sector labels, with symbols checked against NSE's actual listing file.
- Real historical daily prices/volumes and a working NSE announcements adapter, with persistence and provenance.
- Default 24-hour digest, 7/30-day/custom windows, filters, routine grouping, deduplication and priority explanations.
- Persisted price/volume thresholds, lookback, monitored companies and announcement interests.
- Generic company resolution, primary PDF discovery/import, page-preserving extraction, lexical retrieval and optional structured AI analysis.
- Original cached documents for three research demonstrations: INFY, TCS and PERSISTENT.
- Reviewed Infosys and TCS quarterly comparisons and four FY25 guidance revisions matched to the same actual outcome.
- Mobile navigation, desktop workspace, charts, empty/error/loading states, source inspector.

Deliberately constrained:

- Financial tables use reviewed, sourced data for INFY and TCS; guidance pairs remain focused on INFY. The retrieval/indexing engine generalises; automatic extraction of trustworthy accounting tables from arbitrary layouts does not.
- Without a model key, research returns relevant source extracts and explicitly declines to synthesize conclusions. With a key, validated JSON and valid citation IDs are required. A valid ID is not proof that a model claim is entailed; human review still matters.
- No trading, real-time market feed, multi-user accounts, browser notifications, executive profile scraping, OCR, or broker research.
- Deployment configurations are prepared; a public hosting account and repository connection are still needed. No deployment is claimed.

See `architecture.md`, `demo.md`, `verification.md` and the README for implementation details and the exact reproducible commands.
