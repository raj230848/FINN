# Open the updated FINN project

This ZIP contains the full source, tests, setup scripts, deployment examples, reviewed facts and audit history. The latest visual report is `docs/typography.md`: locally bundled Manrope/Inter fonts and consistent reading styles. `docs/pdf-import-verification.md` covers the complete-PDF import improvements. Current typography evidence is under `audit/typography/`, with import evidence under `audit/pdf-import-fix/`; see `RELEASE_MANIFEST.json` for the exact source revision.

1. Extract the ZIP into a normal local folder. Python 3.12 and Node.js 22 LTS are required.
2. Open PowerShell in that folder and run `powershell -ExecutionPolicy Bypass -File scripts/setup.ps1`.
3. For Gemini synthesis, save a newly rotated key after `GEMINI_API_KEY=` in the private root `.env`. Never paste it into browser code or Git. Extractive research works without a key.
4. Run `powershell -ExecutionPolicy Bypass -File scripts/start-finn.ps1`.
5. Open [FINN locally](http://127.0.0.1:3000). Sourced data opens by default. Try the header theme switch, search “HCL Technologies” or “HCLTECH”, and Research → WIPRO → Financial snapshot / Promise vs. reality. Demo replay is an explicit simulation.

The source distribution contains no private runtime database. A fresh install seeds the portfolio and reviewed facts; use Refresh sources to fetch actual market/exchange data. New Wipro primary PDFs can be imported from their cited issuer URLs; full new reports are not redistributed.

Read `docs/remaining-plan-audit.md` for every PDF item and its evidence or remaining external dependency. `docs/verification.md` records testing. `docs/deployment.md` covers hosting the full Python app; the public ChatGPT Site is a separate static demonstration.

The historical change report at `audit/history/FINN-Verification-Gap-Resolution.pdf`, with its text copy at `docs/verification-gap-resolution.md`, covers the earlier hosting, restart and monitoring changes. Its 248 backend/11 frontend counts belong to that earlier revision. The current release passes 299 backend and 20 frontend tests. `docs/hosted-acceptance.md` explains public-host/device steps that still require the actual environment.

The earlier full-project report remains at `audit/history/FINN-Full-Audit-Report.pdf` and `docs/comprehensive-audit.md`. Its 227-test/24-operation measurements belong to the earlier source revision. The current backend has 26 protected business operations, including `GET /api/operations` and the new `GET /api/company-search`; the frontend also has public minimal readiness.

The ZIP's `submission/AI_BUILD_HISTORY_REDACTED.md` is an actual saved chat text export, not a fabricated decision log. Review it and the covering-email draft before submitting. No email has been sent.
