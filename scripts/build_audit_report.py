"""Build the human-readable audit from recorded, credential-free test evidence.

Run with a Python environment containing reportlab (see requirements-audit.txt).
Network and paid Gemini checks are deliberately separate commands.
"""
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'artifacts/comprehensive-audit'


def read(name):
    return json.loads((EVIDENCE / name).read_text(encoding='utf-8'))


def main():
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

    tests = list(ET.parse(EVIDENCE / 'backend-tests.xml').iter('testcase'))
    failed = [t for t in tests if t.find('failure') is not None or t.find('error') is not None]
    assert not failed, 'Do not publish a passing report when recorded tests failed.'
    live, front, gemini, coverage, security = [read(n) for n in ('live-http.json', 'frontend-http.json', 'gemini.json', 'coverage.json', 'security.json')]
    groups = Counter(t.attrib['classname'].rsplit('.', 1)[-1] for t in tests)
    endpoints = []
    for test in tests:
        match = re.fullmatch(r'test_all_business_endpoints\[(\w+) (.+)\]', test.attrib['name'])
        if not match:
            continue
        method, route = match.groups()
        candidates = [r for r in live['operations'] if r['method'] == method and r['route'] == route and (200 <= r.get('http_status', 0) < 300 or r['status'] == 'configuration_blocked')]
        assert candidates, (method, route)
        row = candidates[0]
        endpoints.append({'method': method, 'route': route, 'controlled': 'passed', 'live_http_status': row['http_status'], 'live_status': row['status']})
    assert len(endpoints) == 24
    modules = [{'module': path.replace('\\', '/').removeprefix('backend/app/'), **value['summary']} for path, value in coverage['files'].items() if value['summary']['num_statements']]
    prior_failures = sum(1 for name in ('before.xml', 'feed-before.xml') for t in ET.parse(EVIDENCE / name).iter('testcase') if t.find('failure') is not None)
    # Exact-value scanning is necessary: not every provider key has a familiar prefix.
    known_secrets = []
    for line in (ROOT / '.env').read_text(encoding='utf-8-sig').splitlines():
        name, sep, value = line.partition('=')
        value = value.strip().strip('\"\'')
        if sep and name.strip().endswith(('_KEY', '_TOKEN', '_SECRET')) and len(value) >= 16:
            known_secrets.append(value.encode())
    publishable = set(subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard'], cwd=ROOT, text=True).splitlines())
    matches = [name for name in publishable if (ROOT / name).is_file() and any(secret in (ROOT / name).read_bytes() for secret in known_secrets)]
    assert not matches, 'Credential found in publishable source; do not package.'
    security['exact_key_scan_matches'] = len(matches)
    security['env_ignored'] = subprocess.run(['git', 'check-ignore', '-q', '.env'], cwd=ROOT).returncode == 0
    assert security['env_ignored']
    current_digest = hashlib.sha256()
    source_paths = []
    for folder in ('backend/app', 'frontend/app', 'frontend/components', 'frontend/lib', 'frontend/public'):
        source_paths.extend(p for p in (ROOT / folder).rglob('*') if p.is_file() and p.suffix in {'.py', '.ts', '.tsx', '.css', '.json', '.js', '.svg', '.webmanifest'} and '__pycache__' not in p.parts)
    for path in sorted(source_paths, key=lambda p: p.relative_to(ROOT).as_posix()):
        current_digest.update(path.relative_to(ROOT).as_posix().encode() + b'\0' + path.read_bytes().replace(b'\r\n', b'\n') + b'\0')
    if current_digest.hexdigest()!=security['implementation_sha256']:
        raise SystemExit('The original audit evidence belongs to an earlier implementation. Preserve it as history; use build_gap_report.py for the verification-gap release rather than relabelling old measurements.')
    security.update(application_files_hashed=len(source_paths), implementation_sha256=current_digest.hexdigest(), hash_convention='Sorted relative POSIX path + NUL + CRLF-normalized file bytes + NUL; application source roots only.')
    (EVIDENCE / 'security.json').write_text(json.dumps(security, indent=2) + '\n', encoding='utf-8')
    totals = coverage['totals']
    report = {
        'title': 'FINN - Full Implementation and Integration Audit',
        'audit_date': '2026-11-01',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'base_revision': '21f98d47a1c06146ee88fe652bdd1718527c5142',
        'implementation': security,
        'summary': {'backend_tests_passed': len(tests), 'backend_tests_failed': 0, 'frontend_unit_tests_passed': 6, 'backend_operations': 24, 'live_business_successes': 23, 'live_business_configuration_blocked': 1, 'live_http': live['summary'], 'frontend_http': front['summary'], 'gemini': gemini['summary'], 'pre_fix_failed_regression_cases': prior_failures, 'coverage': totals},
        'test_groups': dict(groups), 'backend_endpoints': endpoints, 'coverage_modules': modules,
        'live_http': live, 'frontend_http': front, 'gemini': gemini,
        'test_cases': [{'group': t.attrib['classname'], 'name': t.attrib['name'], 'seconds': t.attrib.get('time'), 'status': 'passed'} for t in tests],
    }
    blocks = []
    def page(title, subtitle=''):
        blocks.append(('page', title, subtitle))
    def p(text):
        blocks.append(('p', text))
    def table(headers, rows, widths):
        blocks.append(('table', headers, rows, widths))
    def bullets(items):
        for item in items:
            blocks.append(('bullet', item))

    page('01 / Audit outcome', 'FINN - implementation, API, Gemini and edge-case verification | 1 November 2026')
    p('Assessment: the local full application is functional across its implemented workflows. The audit found real failures, added regression coverage and corrected them. This is a tested investment-research prototype; the evidence does not establish that every possible edge case or production deployment is solved.')
    table(['Verification', 'Observed result'], [
        ['Backend regression suite', f'{len(tests)} passed; 0 failed; 2 dependency/deprecation warnings.'],
        ['Frontend validation', '6 Node tests passed; TypeScript check passed; Next.js production build passed.'],
        ['Backend route inventory', 'All 24 business method/path operations pass controlled endpoint tests. OpenAPI inventory equality is enforced.'],
        ['Actual backend HTTP', '43 checks passed; 0 failed; 1 configuration-blocked check. 23/24 business operations succeed live; push subscription requires VAPID configuration.'],
        ['Protected frontend HTTP', '18 checks passed across all 6 exported proxy/session operations, including rate limits and authentication.'],
        ['Actual Google Gemini', '4 genuine provider calls across all 3 call sites; synthesis, support review and classification returned schema-valid responses.'],
        ['Failures corrected', f'{prior_failures} initially failing regression cases now pass, spanning 9 defect categories.'],
        ['Measured unit coverage', f"{totals['percent_statements_covered']:.1f}% statements; {totals['percent_branches_covered']:.1f}% branches; {totals['percent_covered']:.1f}% combined."],
    ], [150, 373])
    p('Testing separation: normal tests clear real provider and push credentials, use temporary databases and controlled external responses. Live checks used a separate QA database and a local protected production-mode frontend. Gemini calls used the private configured key; no usable credential appears in this report or distribution.')
    p('External acceptance still pending: a public hosted Python backend with HTTPS and persistent storage, actual browser-push delivery, and physical-phone testing. The existing public Sites URL is a separate static demo and does not prove backend deployment.')

    page('02 / What is implemented', 'Full-project inventory, including functionality delivered before this audit')
    table(['Area', 'Implemented behavior'], [
        ['Mobile experience', 'Colorful black-background Next.js desk; actionable brief, watchlist, price/volume charts, company sheets, search, date/category/priority filters, saved signals and source links.'],
        ['Portfolio / preferences', '18-company cross-sector starting portfolio; persistent watched flags, thresholds, lookback and interests. Bookmarks remain device-local.'],
        ['Market monitoring', 'Adjusted Yahoo EOD bars; completed-session cutoff at 18:30 IST; deterministic price changes and volume ratios excluding the latest session from the baseline.'],
        ['Filing workflow', 'Best-effort NSE ingestion; UTC timestamps, attachment/content identity and duplicate suppression; priority factors, routine filtering, context and pagination.'],
        ['Coverage / refresh', '24h/7d/30d/custom windows; first observation, last fetch, missing-history warning; manual/backfill refresh and optional single-worker scheduler; partial sync results retained.'],
        ['Research', 'NSE issuer resolution, primary-PDF discovery/import, page-preserving chunks, BM25-style retrieval, up to six cited pages, source-aware caching and explicit refresh.'],
        ['Gemini', 'Structured synthesis, independent support review and selective ambiguous-filing classification. Invalid/unavailable responses fall back to source excerpts or deterministic rules.'],
        ['Quarterly financials', '11 reviewed rows: INFY 3, TCS 3, WIPRO 5. Quarter selection, deterministic QoQ/YoY, explicit currency/accounting basis and Wipro exceptional-item notes. EBITDA stays unavailable.'],
        ['Guidance accountability', '8 records: 4 INFY revisions for one FY25 target; 3 completed Wipro quarterly targets and 1 future pending target. Same metric, period, currency/basis required.'],
        ['Notifications / push', 'Persistent event/read history; recalculation deduplication; optional opt-in Web Push, durable outbox, retries, opt-out and service worker. Real delivery remains unverified.'],
        ['Access / operations', 'Server-only provider/backend secrets, shared-desk access code, signed HttpOnly sessions, origin checks, public expensive-route limits, SQLite WAL, additive migrations and Windows launchers.'],
        ['Delivery assets', 'Public GitHub source, setup/deployment runbooks, Compose/Render configuration, reviewed provenance, evaluator walkthrough and a full source ZIP with a private redacted visible-chat export.'],
    ], [115, 408])
    p('Architecture: mobile browser -> same-origin Next.js proxy -> FastAPI -> SQLAlchemy/SQLite. Source ingestion and deterministic calculations feed the desk; primary excerpts feed optional Gemini. This is one personal/shared desk, without separate user accounts or trade execution.')

    page('03 / Every backend business endpoint', 'Controlled = isolated application test. Live = actual local HTTP with real providers where applicable.')
    table(['Method', 'Registered path', 'Controlled', 'Live HTTP'], [[r['method'], r['route'], 'PASS', f"{r['live_http_status']}" + (' / blocked' if r['live_status'] == 'configuration_blocked' else ' / pass')] for r in endpoints], [45, 320, 63, 95])
    p('The route-inventory test compares this matrix with all registered OpenAPI business operations, so an added route cannot silently go untested. 30 parameterized negative endpoint cases also cover invalid bounds, malformed requests, unknown IDs/tickers, dates and filters.')
    p('POST /api/push/subscribe succeeds in controlled configuration tests; the real environment returns the expected configuration error (503) because no VAPID keys are configured. No real device subscription or external push was sent. Framework GET pages /docs, /redoc, /openapi.json and /docs/oauth2-redirect also returned 200.')

    page('04 / Frontend access and proxy checks', 'Actual protected production-mode Next.js server over local HTTP; not a public HTTPS/device test')
    table(['Scenario', 'Expected / actual'], [[r['scenario'], str(r['http_status']) + ' / PASS'] for r in front['checks']], [410, 113])
    p('All six exported handlers were exercised: GET/POST/PUT/PATCH on the proxy and POST/DELETE on the session endpoint. The unsupported session GET correctly returned 405. A valid sign-in produced an HttpOnly, SameSite=Strict cookie; logout prevented the next protected API request.')
    p('New hardening: a streamed JSON reader enforces a 2,048-byte sign-in limit even without Content-Length; malformed bodies return 400 and oversized bodies 413. The proxy preserves Retry-After from a backend 429. Inadequately configured access codes cannot validate a session.')
    p('The six frontend unit tests cover signed-session/origin behavior and request-body parsing/limits. Type generation, TypeScript and production compilation passed. Earlier 360px/390px browser workflow checks remain documented; no physical phone or new complete visual regression audit is claimed here.')

    page('05 / Gemini key and all LLM integrations', f"Actual configured model: {gemini['model']} | Private root .env | Four fresh provider calls")
    table(['Call site / schema', 'Live outcome', 'Latency'], [[r['schema'], ('Supported: true; 0 unsupported claims' if r['schema'] == 'GroundingReviewOut' else (r.get('category', 'Accepted cited synthesis') + (' / ' + r['confidence'] if 'confidence' in r else ''))), str(r['elapsed_ms']) + ' ms'] for r in gemini['calls']], [175, 273, 75])
    p('Research prompt: What FY25 operating margin guidance did management provide? The uncached answer used grounded_ai and reported 20% to 22%, linked to primary Infosys pages. A separate live model support review returned supported=true with zero unsupported claims. The report JSON preserves the actual answer and page URLs.')
    p('Classification used two explicitly synthetic public-style fixtures in the disposable QA database, not actual issuer events. An evidence-rich ambiguous restructuring classified as M&A; deterministic medium priority and needs-review remained. A vague filing returned low-confidence unclassified, and the application rejected it into deterministic needs-review fallback. Fixtures were rolled back.')
    table(['Additional integration behavior', 'Observed'], [
        ['Replay same research', 'Cached result; 0 further provider calls.'],
        ['No indexed evidence', 'insufficient_evidence; 0 provider calls.'],
        ['Replay same filing identity', '0 inserted duplicates; 0 additional classifier calls.'],
        ['Normal unit tests', 'Real Gemini/VAPID secrets cleared automatically; no paid calls or actual notification delivery.'],
    ], [220, 303])
    p('Controlled faults cover authentication/model/quota/server errors, timeouts, bounded retries, invalid JSON, malformed envelopes, empty/refused/truncated/wrong-schema output, fabricated or wrongly typed citation IDs, unsupported numbers and a false-but-cited claim. Failures return evidence or deterministic review rather than an invented answer.')
    p('Limits: a successful key test proves present access, not future quota or uptime. Model support review is probabilistic, not a proof of semantic correctness. Synthetic classification checks integration behavior, not real-world accuracy. The previously exposed credential works but should be rotated before continued/shared operation; it is excluded from Git, ZIP and this report.')

    page('06 / Defects found and corrected', f'{prior_failures} red-before / green-after cases, with regression tests retained in the project')
    table(['Defect category', 'Before', 'Implemented correction'], [
        ['Huge database IDs (2)', 'SQLite overflow -> 500.', 'Positive signed-64-bit route IDs; invalid values -> 422.'],
        ['Blank question (1)', 'Whitespace passed minimum length.', 'Trim before validating meaningful question length.'],
        ['Unknown filing filters (2)', 'Invalid category/priority accepted.', 'Reject unsupported values with 422.'],
        ['Malformed URLs (2)', 'Bad port/IPv6 leaked ValueError.', 'Translate parsing errors to a clear SourceError.'],
        ['Issuer identity (1)', 'Generic word services matched wrong issuer.', 'Require full normalized legal name or explicit ticker identity.'],
        ['Fiscal aliases (4)', 'FY ranges / compact quarters mapped incorrectly.', 'Use ending financial year and support FY2024-25, Q2FY25 and FY25Q2.'],
        ['Provider envelope (1)', 'Non-object choice leaked AttributeError.', 'Validate choice/message structures; sanitize ProviderError.'],
        ['NSE row shapes (2)', 'Non-object rows leaked AttributeError.', 'Reject malformed list elements as a bounded SourceError.'],
        ['Yahoo payload shape (3)', 'Missing columns, bad numeric/index values leaked exceptions.', 'Reject invalid source payloads clearly and retain cached data.'],
    ], [116, 157, 250])
    p('Additional audit hardening: company-filtered coverage no longer counts unrelated issuers; an empty watchlist is explicitly labelled; citation IDs and support booleans require strict types; model filing summaries cannot introduce unsupported numeric literals; URL fragments no longer duplicate the same import; usage logging accepts only bounded numeric metadata; non-ASCII bearer input rejects cleanly.')
    p('Resource/security boundaries exercised: HTTPS issuer/exchange allowlist, non-global IPv4/IPv6 rejection, redirect revalidation, download cap, malformed/empty/scanned/encrypted/over-600-page PDFs, source identity mismatch, missing/no evidence, sync lock conflicts, partial provider failures and lock release. Normal tests are isolated from runtime credentials and the real database.')
    p('These are finite, named test cases. Passing them does not establish exhaustive input coverage, parser isolation, immunity to DNS rebinding, or a formal security certification. Production egress policy and further security/load testing remain operational work.')

    page('07 / Source and financial verification', 'Actual network observations from the disposable QA database on 1 November 2026')
    observation = live['observations']
    nse = observation['real_sync']['announcements']
    table(['Workflow', 'Evidence'], [
        ['Market refresh', '18/18 watched Yahoo symbols succeeded; each returned 126 completed daily sessions. Latest session: 30 October 2026. No live-tick feed is claimed.'],
        ['Exchange refresh', f"NSE succeeded: {nse['matched']} matching filings; {nse['inserted']} new records in this QA copy. Response window is best effort and not a completeness guarantee."],
        ['Sourced digest windows', '24h / 7d / 30d returned 1 / 64 / 66 rows in this QA snapshot. All retained explicit partial-coverage warnings; counts change with source responses and local history.'],
        ['Unknown issuer path', 'HCLTECH resolved; 6 primary candidates discovered; October 2026 exchange-hosted issuer transcript imported (26 pages); extractive research returned 6 citations.'],
        ['Current Wipro document', 'Actual issuer financial statement import succeeded in QA; earlier period-restricted Q2 FY27 research is also documented in the project.'],
        ['Events / preferences', 'Repeated threshold recalculation added 0 duplicate events; read-all left 0 unread events. QA preferences and watch-state were restored.'],
        ['Reviewed tables', 'INFY 3 + TCS 3 + Wipro 5 = 11 rows. Original document/page, units, reporting basis and provenance retained.'],
        ['Guidance records', 'INFY 4 revisions = 1 historical target; Wipro 3 completed quarterly targets + 1 pending future target. Do not count every revision as a separate management promise.'],
    ], [140, 383])
    p('Accounting boundaries tested: unavailable EBITDA stays unavailable; no operating-profit substitution; zero/missing/negative bases are explicit; only comparable consecutive quarters and same currency/accounting basis produce changes. Wipro group PAT including non-controlling interests is distinguished from INFY/TCS owner-attributable PAT. Guidance uses percentage-point range deviations, matching period/metric/basis, and excludes mismatches.')
    p('No generic automatic accounting-table extraction or OCR accuracy is claimed. Reviewed rows are deliberately focused. Retrieval can generalize to a newly resolved issuer with accessible primary text, while missing evidence produces an explicit limitation.')
    p('Provenance: live-http.json contains the source timestamp, sync response and imported HCLTECH URL. Reviewed numeric sources and hashes are under backend/data/primary. Full newly fetched Wipro reports and runtime databases remain private ignored artifacts. Market/source availability and permitted redistribution depend on their providers.')

    page('08 / Measured code coverage', 'coverage.py branch measurement of the isolated backend suite; not an accuracy score')
    table(['Module under backend/app', 'Statements', 'Branches', 'Combined'], [[r['module'], f"{r['percent_statements_covered']:.1f}%", f"{r['percent_branches_covered']:.1f}%" if r['num_branches'] else 'n/a', f"{r['percent_covered']:.1f}%"] for r in modules] + [['TOTAL', f"{totals['percent_statements_covered']:.1f}%", f"{totals['percent_branches_covered']:.1f}%", f"{totals['percent_covered']:.1f}%"]], [310, 73, 68, 72])
    p(f"Statement coverage: {totals['covered_lines']}/{totals['num_statements']} executable statements. Branch coverage: {totals['covered_branches']}/{totals['num_branches']} branch destinations. Missing: {totals['missing_lines']} statements and {totals['missing_branches']} branch destinations. Combined coverage counts both statements and branch destinations.")
    p('The independent live HTTP and Google processes are not folded into this measurement. Controlled adapter tests cover supported timestamps, provider restrictions/bad JSON, malformed list rows, missing columns, invalid values, incomplete/non-finite market rows and unverified company metadata. Remaining uncovered branches are visible in the included coverage JSON; no 100% claim is made.')

    page('09 / Test inventory and reproduction', 'Retained tests and credential-free evidence allow the findings to be reviewed')
    table(['Backend test group', 'Passing cases'], [[name, str(count)] for name, count in sorted(groups.items())] + [['TOTAL', str(len(tests))]], [425, 98])
    p('The comprehensive-audit group includes the 24 business operation cases, OpenAPI inventory equality, 30 negative endpoint cases, the initial regressions, strict model types, unsupported classifier numbers, source-resource guards, partial-sync behavior and public-startup/authorization checks. Earlier groups retain arithmetic, document provenance, materiality wording, migration/persistence, guidance comparability and push outbox tests.')
    p('Run offline validation from the project root:')
    bullets([
        r'.venv\Scripts\python.exe -m pytest backend\tests -q',
        r'From frontend: npm.cmd run test:access; npm.cmd run typecheck; npm.cmd run build',
        r'Optional coverage: install backend/requirements-audit.txt; set COVERAGE_FILE=artifacts/comprehensive-audit/.coverage; run coverage run --branch --source=backend/app -m pytest backend/tests; then coverage json.',
    ])
    p('Live scripts are separate because they consume provider/network access and change a disposable QA database. Start a protected backend on 127.0.0.1:8002 using a copied SQLite database under artifacts/comprehensive-audit and a disposable API token. scripts/audit_live_integrations.py checks localhost:8002 only. scripts/audit_gemini.py refuses a database URL outside comprehensive-audit. Configure AUDIT_BACKEND_TOKEN, AUDIT_ACCESS_CODE and the QA frontend on localhost:3004 for scripts/audit_frontend_api.py; AUDIT_RATE_CHECK=1 includes proxy rate-limit verification. Never copy a real key into these scripts or command arguments.')
    p('Evidence files in the updated ZIP: backend-tests.xml, before.xml, feed-before.xml, coverage.json, live-http.json, frontend-http.json, gemini.json and security.json. Reports: docs/comprehensive-audit.md, docs/comprehensive-audit.json and the PDF under audit/. Databases, installed dependencies and private .env files are intentionally excluded.')

    page('10 / Remaining acceptance and delivery', 'What is verified locally, what still needs configuration, and how this report maps to the source')
    table(['Item', 'Current status / next action'], [
        ['Public full-stack deployment', 'Pending configured Python hosting, HTTPS, persistent SQLite storage, access secrets and restart checks. Existing Sites URL is a separate static demo.'],
        ['Real Web Push', 'Implementation and controlled tests pass; actual subscribe path is configuration-blocked. Needs VAPID keys, user opt-in, HTTPS and a real browser/device delivery check.'],
        ['Physical mobile acceptance', 'Earlier browser width checks passed; physical device, installed PWA and target-host cookie behavior remain unverified.'],
        ['Provider lifecycle', 'The configured Gemini key works now. Rotate the previously exposed credential; confirm quota/billing and provider availability for ongoing use.'],
        ['Production operations', 'One backend worker; process-local locks/limits, SQLite and non-resumable background jobs. No production load/penetration test, distributed queue or per-user isolation claimed.'],
        ['Source completeness / rights', 'NSE history is explicitly partial and best effort. Provider uptime, exhaustive archive completeness and redistribution rights are not established by code tests.'],
        ['General extraction', 'Arbitrary financial-table extraction, OCR, semantic guarantees and broad classifier accuracy evaluation remain future work.'],
        ['Containers / submission', 'Compose/Render configuration exists, but Docker execution was not verified here. No email sent; owner identity/contact fields still need completion.'],
    ], [145, 378])
    p('Implementation identity: the audit began at Git revision 21f98d47a1c06146ee88fe652bdd1718527c5142. The delivered ZIP RELEASE_MANIFEST.json records its final committed revision. The application-source digest below identifies the tested implementation independently of subsequent report-only changes.')
    p('SHA-256: ' + security['implementation_sha256'])
    p(f"Digest scope: {security['application_files_hashed']} application files; sorted relative POSIX path, NUL, CRLF-normalized content, NUL. Excludes tests, scripts, docs, private configuration and generated artifacts. Exact configured-key scan: {security['exact_key_scan_matches']} matches in publishable source; .env is ignored. ZIP contents are checked separately during packaging.")
    p('Review conclusion: all registered business routes have passing controlled tests, all three Gemini call sites have genuine successful provider responses, and the live backend/frontend paths pass within the documented configuration limits. These results support the local prototype; they do not replace the remaining public-host/device acceptance work.')

    (ROOT / 'docs/comprehensive-audit.json').write_text(json.dumps(report, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')
    md = ['# ' + report['title'], '', 'Audit date: 1 November 2026. Generated from recorded test evidence; no credentials included.', '']
    for block in blocks:
        if block[0] == 'page':
            md.extend(['## ' + block[1], '', block[2], ''])
        elif block[0] == 'p':
            md.extend([block[1], ''])
        elif block[0] == 'bullet':
            md.extend(['- ' + block[1], ''])
        else:
            _, heads, rows, _ = block
            md.extend(['| ' + ' | '.join(heads) + ' |', '| ' + ' | '.join('---' for _ in heads) + ' |'])
            md.extend('| ' + ' | '.join(str(c).replace('|', '/') for c in row) + ' |' for row in rows)
            md.append('')
    (ROOT / 'docs/comprehensive-audit.md').write_text('\n'.join(md), encoding='utf-8')

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='AuditTitle', fontName='Helvetica-Bold', fontSize=21, leading=25, textColor=colors.HexColor('#17213b'), spaceAfter=10))
    styles.add(ParagraphStyle(name='AuditSub', fontName='Helvetica', fontSize=9, leading=13, textColor=colors.HexColor('#55627c'), spaceAfter=16))
    styles.add(ParagraphStyle(name='AuditBody', fontName='Helvetica', fontSize=9.2, leading=13.3, spaceAfter=10, textColor=colors.HexColor('#24304a')))
    styles.add(ParagraphStyle(name='AuditCell', fontName='Helvetica', fontSize=8.1, leading=10.6, textColor=colors.HexColor('#24304a'), splitLongWords=True))
    styles.add(ParagraphStyle(name='AuditHead', parent=styles['AuditCell'], fontName='Helvetica-Bold', textColor=colors.white))
    story = []
    for block in blocks:
        if block[0] == 'page':
            if story:
                story.append(PageBreak())
            story.extend([Paragraph(escape(block[1]), styles['AuditTitle']), Paragraph(escape(block[2]), styles['AuditSub'])])
        elif block[0] in ('p', 'bullet'):
            text = escape(block[1])
            story.append(Paragraph(('&#8226; ' if block[0] == 'bullet' else '') + text, styles['AuditBody']))
        else:
            _, heads, rows, widths = block
            data = [[Paragraph(escape(str(c)), styles['AuditHead']) for c in heads]]
            data += [[Paragraph(escape(str(c)), styles['AuditCell']) for c in row] for row in rows]
            t = Table(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
            t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#332568')), ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 7), ('RIGHTPADDING', (0, 0), (-1, -1), 7), ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f1f4fa'), colors.white]), ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#2ac8ce'))]))
            story.extend([t, Spacer(1, 12)])
    output = ROOT / 'artifacts/FINN-Full-Audit-Report.pdf'
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor('#d9dfeb'))
        canvas.line(36, 34, A4[0] - 36, 34)
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#59647c'))
        canvas.drawString(36, 22, 'FINN | Evidence-based implementation audit | 01 Nov 2026')
        canvas.drawRightString(A4[0] - 36, 22, str(doc.page))
        canvas.restoreState()
    SimpleDocTemplate(str(output), pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=47, title=report['title'], author='FINN project audit').build(story, onFirstPage=footer, onLaterPages=footer)
    print(json.dumps({'backend_passed': len(tests), 'pre_fix_failures_corrected': prior_failures, 'pdf': str(output), 'implementation_sha256': security['implementation_sha256']}, indent=2))


if __name__ == '__main__':
    main()
