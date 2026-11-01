"""Package committed source and private submission/audit artifacts, never secrets."""
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
assert not subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip(), 'Commit reviewed source before packaging.'
commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
report = json.loads((ROOT / 'docs/verification-gap-resolution.json').read_text())
historical = json.loads((ROOT / 'docs/comprehensive-audit.json').read_text())
target = ROOT / 'artifacts/FINN-full-updated-project.zip'
temporary = target.with_suffix('.zip.tmp')
preview = ROOT / 'artifacts/screenshots/finn-mobile-financials.jpg'
preview_bytes = preview.read_bytes() if preview.exists() else None
if preview_bytes is None and target.exists():
    with ZipFile(target) as previous:
        preview_bytes = previous.read('submission/finn-mobile-preview.jpg')
subprocess.run(['git', 'archive', '--format=zip', '--output', str(temporary), 'HEAD'], check=True)
manifest = {
    'source_commit': commit,
    'created_at': datetime.now(timezone.utc).isoformat(),
    'source_repository': 'https://github.com/raj230848/FINN',
    'full_source': True,
    'implementation_sha256': report['security']['implementation_sha256'],
    'independently_tested_implementation_commit': report['implementation_commit'],
    'validation': report['summary'],
    'report': 'audit/FINN-Verification-Gap-Resolution.pdf',
    'historical_report': 'audit/FINN-Full-Audit-Report.pdf',
    'historical_validation': historical['summary'],
    'ci_url': report['ci']['url'],
    'start_with': 'START_HERE.md',
    'unverified_external_gates': [
        'Full Python public hosting, HTTPS and persistent restart/second-device acceptance',
        'Physical phone acceptance',
        'Actual push-service/device display after VAPID setup and opt-in',
        'Account-owner Gemini credential rotation and post-rotation provider acceptance',
        'Owner completion and sending of covering email',
    ],
    'excluded': ['Private .env files and keys', 'Runtime SQLite databases', 'Installed dependencies', 'Internal instructions, reasoning and tool output', 'New full Wipro source reports'],
    'included_private_submission_export': 'submission/AI_BUILD_HISTORY_REDACTED.md',
}
with ZipFile(temporary, 'a', compression=ZIP_DEFLATED) as archive:
    archive.write(ROOT / 'artifacts/submission/AI_BUILD_HISTORY_REDACTED.md', 'submission/AI_BUILD_HISTORY_REDACTED.md')
    if preview_bytes is not None:
        archive.writestr('submission/finn-mobile-preview.jpg', preview_bytes)
    archive.write(ROOT / 'artifacts/FINN-Full-Audit-Report.pdf', 'audit/FINN-Full-Audit-Report.pdf')
    archive.write(ROOT / 'artifacts/FINN-Verification-Gap-Resolution.pdf', 'audit/FINN-Verification-Gap-Resolution.pdf')
    for name in ('backend-tests.xml', 'before.xml', 'feed-before.xml', 'coverage.json', 'live-http.json', 'frontend-http.json', 'gemini.json', 'security.json', 'final-runtime-smoke.json'):
        archive.write(ROOT / 'artifacts/comprehensive-audit' / name, 'audit/' + name)
    for name in ('backend-tests.xml','frontend-tests.xml','coverage.json','restart.json','resilience.json','ci.json','container-acceptance.json','mobile-browser.json','security.json','mobile-service-status.png'):
        archive.write(ROOT / 'artifacts/verification-gaps' / name, 'audit/verification-gaps/' + name)
    archive.writestr('RELEASE_MANIFEST.json', json.dumps(manifest, indent=2) + '\n')
known = []
for env_path in (ROOT / '.env', ROOT / 'frontend/.env.local'):
    if not env_path.exists():
        continue
    for line in env_path.read_text(encoding='utf-8-sig').splitlines():
        name, sep, value = line.partition('=')
        value = value.strip().strip('\"\'')
        if sep and name.strip().endswith(('_KEY', '_TOKEN', '_SECRET')) and len(value) >= 16:
            known.append(value.encode())
with ZipFile(temporary) as archive:
    assert archive.testzip() is None
    for item in archive.infolist():
        name = Path(item.filename).name
        assert name not in ('.env', '.env.local') and not name.endswith(('.db', '.pem', '.key')), 'Private file in ZIP.'
        content = archive.read(item)
        assert not any(secret in content for secret in known), 'Credential in ZIP; do not distribute.'
        if item.filename.lower().endswith('.pdf'):
            with pymupdf.open(stream=content, filetype='pdf') as pdf:
                text = '\n'.join(page.get_text() for page in pdf).encode()
                assert not any(secret in text for secret in known), 'Credential in PDF; do not distribute.'
    count = len(archive.infolist())
os.replace(temporary, target)
sha = hashlib.sha256(target.read_bytes()).hexdigest()
target.with_suffix('.zip.sha256').write_text(sha + '  ' + target.name + '\n', encoding='ascii')
print(json.dumps({'zip': str(target), 'files': count, 'bytes': target.stat().st_size, 'source_commit': commit, 'sha256': sha, 'exact_secret_matches': 0}, indent=2))
