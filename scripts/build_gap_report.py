"""Generate the verification-gap change report from recorded current evidence."""
from collections import Counter
from datetime import datetime, timezone
from html import escape
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'artifacts/verification-gaps'


def read(name):return json.loads((E/name).read_text(encoding='utf-8-sig'))


def main():
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,TableStyle,Spacer,PageBreak
    backend=list(ET.parse(E/'backend-tests.xml').iter('testcase'))
    frontend=list(ET.parse(E/'frontend-tests.xml').iter('testcase'))
    assert all(t.find('failure') is None and t.find('error') is None for t in backend+frontend)
    coverage=read('coverage.json')['totals'];restart=read('restart.json');resilience=read('resilience.json');ci=read('ci.json');container=read('container-acceptance.json');mobile=read('mobile-browser.json')
    assert restart['passed'] and resilience['passed'] and container['summary']['failed']==0
    assert all(v=='success' for v in ci['jobs'].values())
    operations=[re.fullmatch(r'test_all_business_endpoints\[(\w+) (.+)\]',t.attrib['name']) for t in backend]
    operations=[m.groups() for m in operations if m]
    assert set(operations)=={(r['method'],r['path']) for r in container['operation_inventory']}
    subprocess.run(['git','diff','--exit-code',ci['implementation_commit'],'--','backend/app','frontend/app','frontend/components','frontend/lib','frontend/public','Dockerfile','scripts/start_hosted.py','scripts/verify_hosted.py'],cwd=ROOT,check=True,capture_output=True)
    digest=hashlib.sha256();paths=[]
    for root in ('backend/app','frontend/app','frontend/components','frontend/lib','frontend/public'):
        paths.extend(p for p in (ROOT/root).rglob('*') if p.is_file() and p.suffix in {'.py','.ts','.tsx','.css','.json','.js','.svg','.webmanifest'} and '__pycache__' not in p.parts)
    for p in sorted(paths,key=lambda p:p.relative_to(ROOT).as_posix()):digest.update(p.relative_to(ROOT).as_posix().encode()+b'\0'+p.read_bytes().replace(b'\r\n',b'\n')+b'\0')
    ignored=subprocess.run(['git','check-ignore','-q','.env'],cwd=ROOT).returncode==0
    assert ignored
    known=[]
    for line in (ROOT/'.env').read_text(encoding='utf-8-sig').splitlines():
        name,sep,value=line.partition('=');value=value.strip().strip('\"\'')
        if sep and name.strip().endswith(('_KEY','_TOKEN','_SECRET')) and len(value)>=16:known.append(value.encode())
    names=set(subprocess.check_output(['git','ls-files','-co','--exclude-standard'],cwd=ROOT,text=True).splitlines())
    assert not [n for n in names if (ROOT/n).is_file() and any(k in (ROOT/n).read_bytes() for k in known)]
    security={'implementation_sha256':digest.hexdigest(),'application_files_hashed':len(paths),'hash_convention':'Sorted relative POSIX path + NUL + CRLF-normalized bytes + NUL; application roots only.','exact_secret_matches':0,'env_ignored':ignored}
    (E/'security.json').write_text(json.dumps(security,indent=2)+'\n',encoding='utf-8')
    gaps=[
        ['P0.1 / public stack','Code + container verified; public host pending','Root Dockerfile/Render Blueprint host both services on one origin, persistent disk and one worker. Backend is loopback-only. Real host account/URL not provided.'],
        ['P0.2 / deployed operations','Checker + CI verified; target HTTPS pending','Same-origin sign-in, cookie flags, schema fields, saved side effects, renewal/logout and 25-operation inventory. CI: 35 checks pass; 20 operations exercised; 5 explicitly not verified.'],
        ['P0.3 / actual phone','Browser checks pass; physical device pending','New panel checked at 360px/390px without horizontal overflow. Physical Android/iOS, slow network and installed PWA runbook/template supplied.'],
        ['P0.4 / key rotation','Account-owner action pending','Exposed-key rotation is not confirmed. Current secret remains private. Earlier four real Gemini calls remain historical evidence; no post-rotation call is claimed.'],
        ['P0.5 / submission','Package/repo/draft ready; final details pending','Matching full ZIP, manifest/checksum, raw evidence and actual redacted visible-chat export. Actual hosted URL, owner/contact and email submission remain unfinished. No email sent.'],
        ['P1 / browser push','Private local setup + code tests; device pending','VAPID pair generated privately; public-key configuration available locally. Key mismatch replaces an old subscription only on user opt-in; failed unsubscribe stops replacement. Permission-denial recovery text added.'],
        ['P1 / durability','Local processes + CI volume verified','Seven real SQLite restart checks pass. Unfinished jobs become interrupted with partial data retained. CI container restart retains saved preference. Target-host disk test still required.'],
        ['P1 / monitoring','Implemented and tested','Protected operations endpoint and mobile status panel: source age/session/coverage, last sync, bounded model latency/token/outcome metadata, auth/rate counters, push outbox counts. Counters reset per process.'],
        ['P1 / security','Code/controlled/local checks; target-host pending','Trusted public origin for TLS-terminating proxy and Secure cookie selection; readiness returns no desk/internal data. Existing SSRF/resource/origin/rate guards retained. Public HTTPS/egress/load acceptance remains.'],
        ['P2 / broader accounting','Deferred scoped enhancement','Keep 11 reviewed financial rows, explicit units/PAT bases and unavailable EBITDA. No unreviewed general extraction or invented metrics added.'],
        ['P2 / broad classifier score','Not claimed','Existing synthetic integration checks and deterministic regression cases retained; no expert-adjudicated precision/recall dataset or broad accuracy claim.'],
        ['P2 / parser scale','Existing limits retained; more hardening future','Bounded downloads/pages, unsupported PDF failure and private-address/redirect checks remain tested. No new OCR, parser sandbox or large-volume guarantee claimed.'],
    ]
    summary={'backend_tests_passed':len(backend),'frontend_tests_passed':len(frontend),'backend_operations_controlled':len(operations),'local_restart_checks_passed':sum(restart['checks'].values()),'local_resilience_checks_passed':sum(resilience['checks'].values()),'container_checks_passed':container['summary']['passed'],'container_operations_exercised':len(operations)-container['summary']['operations_not_verified'],'container_operations_not_verified':container['summary']['operations_not_verified'],'statement_coverage_percent':coverage['percent_statements_covered'],'branch_coverage_percent':coverage['percent_branches_covered'],'production_build':'passed locally and in CI','typecheck':'passed locally and in CI','public_full_stack_deployed':False,'physical_device_verified':False,'post_rotation_gemini_verified':False,'real_push_display_verified':False}
    report={'title':'FINN - Verification Gap Resolution','generated_at':datetime.now(timezone.utc).isoformat(),'reviewed_document':'FINN_Verification_Gaps_and_Required_Changes_2026-11-01.pdf (6 pages)','implementation_commit':ci['implementation_commit'],'security':security,'summary':summary,'gap_matrix':[dict(zip(('item','status','resolution'),row)) for row in gaps],'api_inventory':container['operation_inventory'],'local_restart':restart,'local_resilience':resilience,'ci':ci,'container_acceptance':container,'mobile_browser':mobile,'test_groups':dict(Counter(t.attrib['classname'] for t in backend)),'historical_evidence':'docs/comprehensive-audit.json belongs to previous ea67269 revision; original live provider data is preserved, not re-labelled as hosted verification.'}
    blocks=[]
    def page(title,sub):blocks.append(('page',title,sub))
    def p(text):blocks.append(('p',text))
    def table(head,rows,widths):blocks.append(('table',head,rows,widths))
    page('01 / Changes and verified results','FINN | Verification-gap response | 1 November 2026')
    p('The review correctly separated a working local prototype from unproven public/device acceptance. This update closes code and reproducibility gaps, validates a real full-stack container, and retains explicit external gates. It does not claim that every edge case or a public production deployment is proven.')
    table(['Check','Current evidence'],[
        ['Backend suite',f'{len(backend)} passing tests, 0 failed; all {len(operations)} registered business operations covered by the controlled inventory test.'],
        ['Frontend',f'{len(frontend)} passing Node tests; TypeScript and production build passed locally and in GitHub Actions.'],
        ['Coverage',f"{coverage['percent_statements_covered']:.1f}% statements ({coverage['covered_lines']}/{coverage['num_statements']}); {coverage['percent_branches_covered']:.1f}% branches ({coverage['covered_branches']}/{coverage['num_branches']})."],
        ['Real local durability','7 checks passed across actual FastAPI process stop/start; saved preferences/watchlist/read history/documents/chunks/completed sync retained.'],
        ['Real local resilience','9 checks passed: production proxy detects lost backend, returns recoverable 503, recovers existing sessions and isolates logout between two HTTP cookie jars.'],
        ['Full-stack Docker CI','Root image built and ran on Ubuntu; 35 protected-app checks passed, 0 failed. Container restart retained the saved QA preference marker.'],
        ['Mobile browser view','360px and 390px emulation: no horizontal document overflow in new operational panel. Temporary viewport restored; physical phone remains unverified.'],
    ],[132,391])
    p('Implementation: a combined Next.js/FastAPI hosting image and supervisor; public minimal readiness; protected source/model/outbox status and mobile panel; interrupted-refresh recovery; trusted public-origin and Secure-cookie handling; push subscription key-rotation guard; automated host/device acceptance tools and updated submission runbooks.')
    p('CI evidence: https://github.com/raj230848/FINN/actions/runs/41323904107 . Backend, frontend and full-stack-container jobs all completed successfully for implementation commit '+ci['implementation_commit']+'. No paid Gemini or browser-push calls were made by the container check.')

    page('02 / Item-by-item disposition','P0 acceptance gates first; P1 improvements verified within scope; P2 expansion remains conditional')
    table(['Review item','Status','Change / remaining requirement'],gaps,[104,134,285])
    p('The existing portfolio, sourced digest/threshold rules, provenance, financial comparability and guidance views are retained. The earlier 227-test report is preserved as history. The matching updated ZIP now includes raw current tests, coverage, actual restart/resilience results and the exact downloaded container-acceptance JSON, addressing the review\'s missing-bytes concern.')

    page('03 / Complete current API inventory','Original 24 business operations plus GET /api/operations; frontend adds public GET /api/ready')
    table(['Method','Registered backend path','Controlled','Docker CI'],[[r['method'],r['path'],'PASS','PASS' if r['status']=='passed' else 'not verified'] for r in container['operation_inventory']],[43,309,65,106])
    p('CI deliberately omitted real source refresh/sync polling, new-company discovery/import and genuine browser subscription. Those five operations remain not verified in that environment; they are not 200-only substitutes. Earlier live Yahoo/NSE/Gemini/HCLTECH results remain attached as historical evidence. The new host checker can run refresh/Gemini/new-issuer paths with explicit QA flags when the actual target is available.')
    p('GET /api/ready is the only new public frontend status route. It returns a minimal readiness result and does not bypass authentication for desk data. Public-mode proxy/session protections remain; an external HTTPS host must still verify Secure cookies on its actual domain.')

    page('04 / Process evidence and safeguards','Actual local service processes; bounded controlled model/security tests; independent CI container')
    table(['Restart / retained state','Observed'],[[k.replace('_',' '),'PASS'] for k in restart['checks']],[430,93])
    table(['Production proxy / sessions','Observed'],[[k.replace('_',' '),'PASS'] for k in resilience['checks']],[430,93])
    p('The restart test retained 18 companies, 11 bundled documents, 3,071 chunks and 10 event records in its fresh disposable database. It preserved the completed sync and retained a successful partial price result while marking the unfinished run interrupted. The main private runtime database was backed up before its upgrade; QA tests did not target it.')
    p('Operational metrics accept fixed component/outcome names and bounded integer token/latency metadata only. They do not store questions, provider bodies, cookies, API tokens, client IPs or push subscriptions. Source fetch age is calculated from each watched company\'s latest available session, so old retained history does not falsely label a newly fetched series stale; missing companies remain partial.')
    p('The new trusted-origin tests cover TLS termination with an internal HTTP request, malicious origins and insecure remote configuration. Push tests cover matching key reuse, key replacement order, failed unsubscribe and malformed keys. Existing malformed-provider/citation/numeric/SSRF/resource/partial-sync tests remain passing. These are finite checks, not semantic model proof or a penetration-test certificate.')

    page('05 / External acceptance and delivery','Do not turn local/CI results into a public-host or physical-device claim')
    table(['Acceptance area','Current disposition'],[
        ['A. Source / secrets','Matching full source ZIP, checksum and evidence provided. .env ignored; exact configured-secret scan found 0 source matches. Account-owner Gemini revocation/rotation remains unconfirmed.'],
        ['B. Backend','Container and local persistence verified. Actual public HTTPS service, host disk/restart and all routes on the target evaluator desk remain pending hosting access.'],
        ['C. Frontend / phone','Build, origin controls, proxy outage and two sessions verified within local/CI scope. Physical Android/iOS, public TLS cookies, PWA and slow mobile network still need observation.'],
        ['D / E. Digest / market','Existing sourced rules and provenance retained. Earlier actual-provider results preserved. Repeat on the public target to establish its network access and source freshness.'],
        ['F / G. Gemini / new issuer','Earlier genuine calls and HCLTECH workflow are history, not post-rotation/hosted proof. Use --qa --gemini --ticker on the target and inspect primary pages manually.'],
        ['H. Optional push','Private VAPID configuration and subscription guards ready. Actual browser permission, background receive, device display, expired subscription and opt-out need the real device.'],
        ['I. Submission','Covering draft now separates the actual full-stack URL from the static demo. Owner/contact/verified URL and final email remain pending. No email sent.'],
    ],[120,403])
    p('Next steps: connect the prepared Render Blueprint (one paid service with persistent disk), set a rotated Gemini key and private VAPID values, run scripts/verify_hosted.py against a separate QA frontend with --qa --refresh --gemini --ticker HCLTECH, then complete docs/hosted-acceptance.md on a physical phone. Never put the desk code or replacement key in command arguments, the report or ZIP.')
    p('Package includes both the historical full audit and this current change report. RELEASE_MANIFEST.json records the final committed source revision. The application-source digest identifies the tested implementation independently of report-only commits: '+security['implementation_sha256']+'.')
    p(f"Digest scope: {len(paths)} application files; sorted relative POSIX path + NUL + CRLF-normalized content + NUL. Private .env, databases, new full issuer PDFs and installed dependencies are excluded from distribution. Remaining multi-day scheduling, real-world classifier evaluation, arbitrary accounting/OCR and production load/egress tests are explicitly not claimed.")

    (ROOT/'docs/verification-gap-resolution.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    md=['# FINN - Verification Gap Resolution','','Current implementation: `'+ci['implementation_commit']+'`. Latest raw evidence and release identity are in the ZIP manifest.','']
    for b in blocks:
        if b[0]=='page':md.extend(['## '+b[1],'',b[2],''])
        elif b[0]=='p':md.extend([b[1],''])
        else:
            md.extend(['| '+' | '.join(b[1])+' |','| '+' | '.join('---' for _ in b[1])+' |'])
            md.extend('| '+' | '.join(str(v).replace('|','/') for v in row)+' |' for row in b[2]);md.append('')
    (ROOT/'docs/verification-gap-resolution.md').write_text('\n'.join(md),encoding='utf-8')
    title=ParagraphStyle('title',fontName='Helvetica-Bold',fontSize=20,leading=24,textColor=colors.HexColor('#17213b'),spaceAfter=10)
    sub=ParagraphStyle('sub',fontName='Helvetica',fontSize=9,leading=12,textColor=colors.HexColor('#59647c'),spaceAfter=15)
    body=ParagraphStyle('body',fontName='Helvetica',fontSize=9,leading=12.5,textColor=colors.HexColor('#24304a'),spaceAfter=10)
    cell=ParagraphStyle('cell',fontName='Helvetica',fontSize=7.9,leading=10.3,textColor=colors.HexColor('#24304a'))
    head=ParagraphStyle('head',parent=cell,fontName='Helvetica-Bold',textColor=colors.white)
    story=[]
    for b in blocks:
        if b[0]=='page':
            if story:story.append(PageBreak())
            story.extend([Paragraph(escape(b[1]),title),Paragraph(escape(b[2]),sub)])
        elif b[0]=='p':story.append(Paragraph(escape(b[1]),body))
        else:
            data=[[Paragraph(escape(str(v)),head) for v in b[1]]]+[[Paragraph(escape(str(v)),cell) for v in row] for row in b[2]]
            t=Table(data,colWidths=b[3],repeatRows=1,hAlign='LEFT')
            t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#332568')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#f1f4fa'),colors.white]),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,0),2,colors.HexColor('#2ac8ce'))]))
            story.extend([t,Spacer(1,10)])
    def footer(canvas,doc):
        canvas.saveState();canvas.setStrokeColor(colors.HexColor('#d9dfeb'));canvas.line(36,34,A4[0]-36,34);canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#59647c'));canvas.drawString(36,22,'FINN | Verification-gap resolution | 01 Nov 2026');canvas.drawRightString(A4[0]-36,22,str(doc.page));canvas.restoreState()
    output=ROOT/'artifacts/FINN-Verification-Gap-Resolution.pdf'
    SimpleDocTemplate(str(output),pagesize=A4,leftMargin=36,rightMargin=36,topMargin=36,bottomMargin=47,title=report['title']).build(story,onFirstPage=footer,onLaterPages=footer)
    print(json.dumps({'summary':summary,'pdf':str(output),'implementation_sha256':digest.hexdigest()},indent=2))


if __name__=='__main__':main()
