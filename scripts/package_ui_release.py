"""Export committed FINN source plus explicit UI evidence; exclude private runtime data."""
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
assert not subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip(), 'Commit reviewed source first.'
commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
proof = ROOT / 'artifacts/ui-ux-plan'
backend = ET.parse(proof / 'backend-tests.xml').getroot()
frontend = ET.parse(proof / 'frontend-tests.xml').getroot()
assert len(list(backend.iter('testcase'))) == 272
assert len(list(frontend.iter('testcase'))) == 14
assert not list(backend.iter('failure')) + list(backend.iter('error')) + list(frontend.iter('failure')) + list(frontend.iter('error'))
build = json.loads((proof / 'production-build.json').read_text())
browser = json.loads((proof / 'browser-checks.json').read_text())
assert build['exit_code'] == 0 and not browser['productionErrorsSince0905']
manifest = {
    'source_commit': commit, 'created_at': datetime.now(timezone.utc).isoformat(),
    'source_repository': 'https://github.com/raj230848/FINN', 'full_source': True,
    'start_with': 'START_HERE.md', 'current_report': 'docs/ui-ux-upgrade.md',
    'validation': {'backend_tests': 272, 'frontend_tests': 14, 'production_build': 'passed',
                   'business_operations_in_inventory': 26, 'browser_viewport_widths': [360, 390, 1280]},
    'current_evidence': 'audit/ui-ux/',
    'historical_reports': ['audit/history/FINN-Full-Audit-Report.pdf', 'audit/history/FINN-Verification-Gap-Resolution.pdf'],
    'historical_note': 'Earlier PDFs measure their recorded revisions, not this UI release.',
    'remaining_external_checks': ['Rotated Gemini credential and fresh live provider acceptance',
                                  'Physical phone and actual push-service delivery', 'Public full-stack hosting acceptance'],
    'excluded': ['Private environment files and keys', 'Runtime databases', 'Installed dependencies',
                 'Build caches', 'Confidential input PDFs', 'Internal reasoning and tool traces'],
}
target = ROOT / 'artifacts/FINN-full-updated-project.zip'
temporary = target.with_suffix('.zip.tmp')
subprocess.run(['git', 'archive', '--format=zip', '--output', str(temporary), 'HEAD'], check=True)
names = ['backend-tests.xml', 'frontend-tests.xml', 'production-build.json', 'browser-checks.json', 'search-live.json',
         *browser['screenshots']]
with ZipFile(temporary, 'a', compression=ZIP_DEFLATED) as archive:
    for name in names:
        archive.write(proof / name, 'audit/ui-ux/' + name)
    for name in ('FINN-Full-Audit-Report.pdf', 'FINN-Verification-Gap-Resolution.pdf'):
        archive.write(ROOT / 'artifacts' / name, 'audit/history/' + name)
    archive.write(ROOT / 'artifacts/submission/AI_BUILD_HISTORY_REDACTED.md', 'submission/AI_BUILD_HISTORY_REDACTED.md')
    archive.writestr('RELEASE_MANIFEST.json', json.dumps(manifest, indent=2) + '\n')
known = []
for env_path in (ROOT / '.env', ROOT / 'frontend/.env.local'):
    if not env_path.exists():
        continue
    for line in env_path.read_text(encoding='utf-8-sig').splitlines():
        key, sep, value = line.partition('=')
        value = value.strip().strip('\"\'')
        if sep and re.search(r'(?:KEY|TOKEN|SECRET|PASSWORD|ACCESS_CODE)$', key.strip()) and len(value) >= 12:
            known.append(value.encode())
with ZipFile(temporary) as archive:
    assert archive.testzip() is None
    for item in archive.infolist():
        name = Path(item.filename).name
        assert not (name.startswith('.env') and name != '.env.example')
        assert not name.endswith(('.db', '.pem', '.key'))
        content = archive.read(item)
        assert not any(secret in content for secret in known), 'Credential in archive; distribution blocked.'
        assert not re.search(rb'AIza[0-9A-Za-z_-]{30,}|gh[pousr]_[A-Za-z0-9_]{30,}', content), 'Credential-shaped string in archive.'
        if name.lower().endswith('.pdf'):
            with pymupdf.open(stream=content, filetype='pdf') as pdf:
                content = '\n'.join(page.get_text() for page in pdf).encode()
                assert not any(secret in content for secret in known), 'Credential in historical PDF.'
    files = len(archive.infolist())
os.replace(temporary, target)
digest = hashlib.sha256(target.read_bytes()).hexdigest()
target.with_suffix('.zip.sha256').write_text(digest + '  ' + target.name + '\n', encoding='ascii')
result = {'zip': str(target), 'files': files, 'bytes': target.stat().st_size, 'source_commit': commit,
          'sha256': digest, 'exact_secret_matches': 0}
(proof / 'package-check.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
