# Hosted and physical-device acceptance

Use this after an actual full-stack HTTPS deployment. Local tests, a Docker CI job, and the static Sites URL are different evidence. The project is one shared desk, not an isolated multi-user account system; create a separate QA service/database before the mutation checks below.

## Automated host verification

Save the evaluator instance's desk code only in your shell's private `FINN_HOSTED_ACCESS_CODE` environment variable. Do not put it in command arguments or screenshots. From the project root:

```powershell
.\.venv\Scripts\python.exe scripts/verify_hosted.py --url https://YOUR_ACTUAL_FRONTEND --out artifacts/hosted-readiness.json
```

This checks public readiness, anonymous blocking, actual login cookie flags, authenticated reads/response fields and logout. Omitting the code records that authentication was not tested. It rejects remote plain HTTP, credential-bearing URLs, paths and query strings.

Only on a disposable evaluator desk, use:

```powershell
.\.venv\Scripts\python.exe scripts/verify_hosted.py --url https://YOUR_QA_FRONTEND --qa --refresh --gemini --ticker HCLTECH --out artifacts/hosted-acceptance.json
```

This performs actual source refresh/discovery/import and an uncached Gemini request, so network availability and model costs apply. It temporarily changes preferences/watch state and restores them, but deliberately marks QA notification history read. It verifies persisted effects with follow-up GET requests and inventories all 25 backend operations. `not_verified` is retained for unavailable samples or a real push subscription; a 200 is not treated as proof of device delivery or source semantics. Review each citation's original page manually. Reports omit access codes, cookies, private subscription details and full provider bodies.

The original `verify_release.py` remains for a two-host backend/frontend layout; the single-origin checker is the primary combined-stack path. A failed response, malformed schema or provider timeout remains a failure/limit rather than a fabricated pass.

## Target-host restart and persistence

1. On the isolated hosted evaluator desk, save a distinctive valid preference, change one watched company, mark one event read, import a primary report and finish a source refresh. Record the values, document ID/page count, event ID/read state and completed sync ID.
2. Restart/redeploy through the hosting dashboard while keeping the mounted disk. Sign in again if necessary and verify every recorded value through the browser and API.
3. For an interrupted sync, restart during a QA refresh. The earlier run must be marked `interrupted` with partial data retained; it must not remain falsely `running` or claim completion. Start a new refresh. Jobs are not automatically resumed.
4. Keep one worker/instance. Confirm migration/cold-start logs and public readiness. Record elapsed startup time and any host error. Do not delete a disk to resolve a deployment issue.

Local reproduction, without providers or user database mutation:

```powershell
.\.venv\Scripts\python.exe scripts/verify_restart.py
.\.venv\Scripts\python.exe scripts/verify_resilience.py
```

The first starts/stops a separate real FastAPI process twice and compares SQLite state. The second uses a production Next.js proxy, two independent session cookie jars, actual backend outage and restart. Both create disposable databases under ignored artifacts. Neither establishes a hosting provider's persistent-disk behavior.

## Physical Android/iOS checklist

Record date, actual HTTPS URL, device/OS, browser version and whether installed as a PWA. Perform each check on the device; browser-width emulation is separate evidence.

| Check | Required observation |
| --- | --- |
| Fresh/incognito login | Access code works; anonymous API blocked; reload retains an appropriate session; renewal succeeds; logout removes this device's access. |
| Touch layout | Brief, filters, research, financial/guidance cards, sheets and bottom navigation scroll without horizontal overflow or unreachable controls. |
| Source links | Original issuer/exchange PDF opens on the cited page; issuer/period/number supports the answer. |
| Sourced workflow | Real refresh displays original session dates, partial failures, stale status and incomplete filing history honestly. |
| Unfamiliar issuer | An out-of-preloaded ticker discovers/imports an accessible primary source and returns an appropriate cited answer. |
| Slow/offline network | A delayed/lost request gives a recoverable message; reconnect and retry recovers; no synthetic or stale value is relabelled live. |
| Independent sessions | Phone and another browser can access the shared desk; logging out one does not invalidate the other's cookie. They still share desk data and public rate limits. |
| Browser push, if claimed | Enable on this actual device, grant permission, observe a new qualifying sourced notification over HTTPS, background/reopen browser, and record displayed time separately from provider acceptance. |
| Permission/key changes | Deny notifications, follow browser settings to re-enable; after VAPID rotation disable/re-enable the subscription; opt-out prevents later eligible sends. |

On iPhone, use a supported installed home-screen app where the browser requires it. Do not grant permissions or claim display on behalf of an untested physical device. Use `physical-device-acceptance.example.json` as a blank evidence record; it intentionally begins `not_verified`.

## Credential and submission gates

The previously exposed Gemini credential cannot be declared rotated by changing application code. The account owner must revoke it and save a newly generated replacement only in private local/host configuration, then run one fresh accepted `grounded_ai` check. Never paste the replacement into the chat or package.

Fill the actual verified full-stack URL, owner name/contact and history attachment in `covering-email.md`. The supplied review states a 1 November 2026 deadline; the document's submission instructions do not authorize this agent to send an email. No submission email is sent by these tools.

References: [Render persistent disk behavior](https://render.com/docs/disks), [Render Blueprint configuration](https://render.com/docs/blueprint-spec).
