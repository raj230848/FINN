# Primary-source document provenance

Original company-issued documents are cached here for the reproducible assessment prototype. Copyright remains with the respective issuer. The application code does not grant redistribution rights to these documents; keep the assessment repository private and review the issuer's terms before wider publication.

`catalog.json` records the original URL, ticker, document type, source period, SHA-256 checksum and physical page count for every bundled file. Dates and conclusions are not made current merely by downloading an older report.

`verified.json` contains a small reviewed set of financial and guidance facts, each with an original primary URL and physical page. These are explicitly historical Infosys examples; the research pipeline itself has no restriction to that issuer. Financials were checked against actual downloaded table rows. Their validity does not make arbitrary PDF accounting extraction solved.

Sources:

- [Infosys Q4 FY25 issuer results index](https://www.infosys.com/investors/reports-filings/quarterly-results/2024-2025/q4.html)
- [Infosys annual reports](https://www.infosys.com/investors/reports-filings/annual-report.html)
- [TCS Q4 FY25 issuer results release](https://www.tcs.com/who-we-are/newsroom/press-release/tcs-financial-results-q4-fy-2025)
- [Persistent annual reports](https://www.persistent.com/investors/financial-results-and-reports/annual-reports/)

The files can be re-fetched/indexed with `scripts/fetch_sources.py`. Download failures are reported, not replaced with synthetic reports. Research imports performed after startup are stored in the runtime database; they are not silently added to this reviewed bundle.
