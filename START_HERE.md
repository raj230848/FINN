# Open the updated FINN project

This ZIP contains the full source, tests, setup scripts, deployment examples, reviewed facts and the remaining-plan audit.

1. Extract the ZIP into a normal local folder. Python 3.12 and Node.js 22 LTS are required.
2. Open PowerShell in that folder and run `powershell -ExecutionPolicy Bypass -File scripts/setup.ps1`.
3. For Gemini synthesis, save a newly rotated key after `GEMINI_API_KEY=` in the private root `.env`. Never paste it into browser code or Git. Extractive research works without a key.
4. Run `powershell -ExecutionPolicy Bypass -File scripts/start-finn.ps1`.
5. Open [FINN locally](http://127.0.0.1:3000). Try Sourced data, notifications and Research → WIPRO → Financial snapshot / Promise vs. reality.

The source distribution contains no private runtime database. A fresh install seeds the portfolio and reviewed facts; use Refresh sources to fetch actual market/exchange data. New Wipro primary PDFs can be imported from their cited issuer URLs; full new reports are not redistributed.

Read `docs/remaining-plan-audit.md` for every PDF item and its evidence or remaining external dependency. `docs/verification.md` records testing. `docs/deployment.md` covers hosting the full Python app; the public ChatGPT Site is a separate static demonstration.

The latest full-project report is `audit/FINN-Full-Audit-Report.pdf` in the ZIP, with a text copy at `docs/comprehensive-audit.md`. It includes all 24 backend endpoints, every Gemini call site, 227 passing backend tests, coverage, corrected defects and remaining external acceptance checks. Credential-free raw evidence is under `audit/`.

The ZIP's `submission/AI_BUILD_HISTORY_REDACTED.md` is an actual saved chat text export, not a fabricated decision log. Review it and the covering-email draft before submitting. No email has been sent.
