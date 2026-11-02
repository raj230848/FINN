# PDF import fix and verification

The screenshot error came from a hard-coded 600-page check in `backend/app/services/documents.py`. It was a FINN import restriction, not a Gemini error. This release replaces that ceiling with configurable, bounded complete-document indexing and tests the import path through extraction, persistence, retrieval and the browser proxy.

## Changes

- Complete text-readable PDFs up to **3,000 pages / 60,000,000 downloaded bytes** by default. Pages are never silently cut off at 600 or another limit. Failures state the applicable limit and preserve the existing library.
- Additional defaults: 200,000 extracted characters per page; 12,000,000 per document; 20,000 passages; a 90-second extraction budget checked between pages. Configuration has upper bounds and is listed in `.env.example`. Downloading is bounded separately, including redirected responses, declared sizes and streamed bytes.
- PDF imports through Next.js have a 180-second request window. Other APIs retain 55 seconds. A host may impose a shorter limit. A lost response does not cause the client to automatically repeat a POST; the UI tells the user to check Source library first.
- One supported backend worker permits one active import at a time. Concurrent requests get 409 with `Retry-After: 3`. The browser also prevents rapid duplicate submissions and shows progress across every Research tab.
- Identical bytes for the same issuer reuse the existing indexed document, including alternate primary URLs. Changed content at the same URL replaces passages atomically, updates metadata and invalidates that issuer's cached research citations. A failed extraction, issuer check or database batch leaves the previous document and research cache intact.
- Missing/legacy passage indexes are rebuilt. A file with no usable passages cannot claim success. Blank, scanned or very short pages keep their original page positions and are explicitly reported as pages without indexed passages. No OCR is implied.
- Live imports must resolve to PDF bytes. Login/access pages, arbitrary binary files and misleading HTML responses are rejected. Permitted issuer/exchange hosts, public HTTPS/DNS checks, redirect validation and issuer identity checks remain enforced. BSE's public embedded PDF viewer is supported.
- Import success displays page and passage counts. Library entries show readable-page coverage. Network loss, HTML gateway errors and null error responses produce controlled messages instead of JSON/type exceptions.
- Fresh local setup now allows up to 180 seconds for bundled report indexing; a measured fresh initialization on this machine took about 91 seconds.

## HCLTech verification

The company was identified as HCLTECH; an exact failing PDF URL was not supplied. These were the three currently discovered annual-report candidates downloaded from the BSE archive and independently indexed in an isolated database:

| Report | PDF pages | Pages with passages | Passages | Local indexing time |
|---|---:|---:|---:|---:|
| Annual Report 2026 | 485 | 481 | 1,484 | 27.0 s |
| Annual Report 2025 | 470 | 465 | 1,429 | 26.2 s |
| Annual Report 2024 | 385 | 376 | 1,222 | 16.9 s |

Those three files are below the former 600-page ceiling. They verify current HCLTech imports, rather than reproducing the screenshot against an unidentified source URL. The 2026 report was already present in the local library before this fix. Downloaded report checksums, URLs and measured counts are included in the release evidence; full newly downloaded reports are not redistributed in the ZIP.

Extractive HCLTech research returned six original-page citations after the isolated imports. Separately, a **701-page regression PDF** was imported through the API test and queried successfully on **page 701** with a `#page=701` citation. This proves that indexing and retrieval extend beyond the former cutoff.

All three discovered transcript viewer links also imported in the isolated library: October 2026 (26 pages / 51 passages), July 2026 (29 pages / 56 passages), and April 2026 (25 pages / 48 passages). The live browser imported the 2025 annual report successfully into the user's desk; the 2026 report was retained. Repeating the live import reused the same document ID and kept the HCLTech library at two documents. Live extractive research returned six citations.

## Test coverage

**299 backend tests and 20 frontend tests pass.** The backend suite includes the existing 26-operation controlled API inventory, authorization, source identity, session/calendar logic, provider failures, grounding/fallbacks and the following new import cases. This is a concrete regression matrix, not a claim that every possible PDF has been tested.

| Area | Cases verified |
|---|---|
| Large reports | 701-page storage, last-page retrieval/citation, import route count reporting, repeat import without duplicates |
| Boundaries | Configured page limit accepted at the boundary and rejected above it; bytes, per-page text, total text, passage count and extraction deadline |
| Invalid input | Empty, truncated, encrypted, scanned/no-text, unsupported binary and fragment-only documents; existing malformed/source tests retained |
| Source safety | HTTPS/domain/private-address and redirect guards; issuer mismatch; HTML access pages; safe BSE embedded PDF handling |
| Provider failures | HTTP 403, 404, 429, 500; declared and streamed download size; read timeout |
| Persistence | Same URL, identical-content alternate URL, changed content and metadata, issuer-specific cache invalidation, failed replacement, forced failure in the second database batch with document/cache rollback |
| Coverage | BOM-prefixed PDFs, blank first page, original page numbering, readable-page counts and explicit no-OCR notes |
| Concurrency/recovery | Busy import conflict, retry header, lock release after failure, retained documents and client duplicate-submit guard |
| Browser/proxy | Import-only 180-second timeout, other operations unchanged, backend error detail, HTML/null error response handling, interrupted connections without POST retries, autocomplete abort semantics |

Current raw evidence is under `audit/pdf-import-fix/` in the ZIP: JUnit results, production build result, primary-report probes, real-PDF validation, live HTTP checks and browser screenshots. The browser acceptance uses the actual running app; its recorded results distinguish imports, page counts and original sources from mocked regression tests.

## Practical limits

The application still requires a text-readable, correctly identified primary source. OCR, password removal and non-primary sources are not supplied as fallbacks. The extraction budget is cooperative between page calls, not a hard process-level parser sandbox. Very slow or adversarial parsing and hosted platforms with tighter time limits need an isolated durable worker/job design. These limits remain explicit rather than promising unlimited documents.

No new paid Gemini call was required for this fix. Existing model/schema/citation failure tests pass with isolated test transports; a fresh live model request, physical push delivery and public full-stack deployment acceptance are separate checks recorded in earlier reports.
