# Deployment and repository publication

Source is published in the public [raj230848/FINN](https://github.com/raj230848/FINN) repository. The [public ChatGPT Sites demo](https://finn-investment-desk.justfrog26.chatgpt.site) is deployed. It preserves the interactive UI using synthetic market fixtures, reviewed historical financial/guidance facts and bounded primary-source extracts. Preferences and watchlists are device-local. Live Python ingestion and new document imports are not hosted by Sites. Docker is not installed on the build machine, so the container configuration has not been executed locally.

## Local production mode

Start the Python backend with the supplied PowerShell script. In a separate terminal:

```powershell
Set-Location frontend
npm.cmd run build
npm.cmd run start
```

For normal development use `npm.cmd run dev`. The checked-in dependency locks capture the versions tested for this prototype.

## Docker Compose

Install Docker Desktop from its official distribution and enable Linux containers. From the project root, after creating `.env` from `.env.example`:

```powershell
docker compose up --build -d
docker compose logs -f backend frontend
```

Open `http://localhost:3000`. `finn-data` stores only the runtime SQLite database; primary documents are baked into the backend image outside the persistent database mount. The backend binds to loopback on the host; the Next.js server calls it over the container network.

The Docker backend uses one worker. The optional scheduler uses a process-local lock and is unsuitable for multiple replicas without a shared job coordinator. Rebuilding an image does not remove the database volume.

## Vercel frontend + persistent Python backend

1. Use the published [FINN repository](https://github.com/raj230848/FINN) as the deployment source.
2. Host the backend using its Dockerfile on a Python/container host. `render.yaml` supplies a Render example with a persistent disk and an explicit `starter` plan, which can incur charges. Review the host's current terms/pricing before creating the service. The public-source adapters are best effort and may be blocked from a data-centre IP even when local tests work.
3. Set `DATABASE_URL=sqlite:////var/lib/finn/finn.db` and mount persistence at `/var/lib/finn`. Keep one worker. Health endpoint: `/api/health`.
4. Set `PUBLIC_DEPLOYMENT=true` and a strong `FINN_API_TOKEN` on the backend (startup refuses a missing token). If using the Render blueprint, it generates a token; copy the resulting value directly into the frontend's server-only environment setting. Never commit it.
5. Optional: set `GEMINI_API_KEY` and `GEMINI_MODEL=gemini-3.5-flash-lite` on the backend. Leave the key empty for extractive-only operation.
6. Import the GitHub repository into Vercel with **Root Directory `frontend`** and the Next.js framework preset. The build command is `npm run build`.
7. Set server-only `BACKEND_URL` to the deployed HTTPS backend origin (no `/api` suffix). Set the matching server-only `FINN_API_TOKEN`. Neither variable uses a `NEXT_PUBLIC_` prefix.
8. Set frontend `FINN_PUBLIC_MODE=true`, `FINN_ACCESS_TOKEN` (at least 16 characters) and `FINN_SESSION_SECRET` (at least 32 random characters). Vercel/Render enable the gate automatically. Anonymous proxy requests return 401; sign-in creates an eight-hour signed HttpOnly cookie. POST/PUT/PATCH require same-origin requests. This protects one shared desk; add individual accounts and per-user storage for a multi-user product. Keep platform deployment protection enabled as an additional control.
9. Verify backend health, open the frontend, switch to Sourced data, refresh, and inspect partial-error handling and source timestamps. Then test a research question and both guidance evidence links.
10. Copy only the **actual successfully verified** URLs into the covering email. A provider dashboard or a configured project is not a deployed-product URL.

The Next.js API proxy has a 55-second request timeout and declares a 60-second route duration. Hosts can impose stricter limits. Large document imports or slow providers may require a durable background-job API for a hosted version; the current source-refresh endpoint already runs ingestion in the backend background. For the first submission, prefer the included bounded documents. Do not silently raise download/page limits.

Configuration references: [Vercel Next.js documentation](https://vercel.com/docs/frameworks/full-stack/nextjs), [Render persistent disks](https://render.com/docs/disks), and [Render Blueprint specification](https://render.com/docs/blueprint-spec). Render's documentation confirms that persistent disks require a paid service and that its default filesystem is ephemeral.

## GitHub publication

The project is published publicly at [raj230848/FINN](https://github.com/raj230848/FINN), as requested by its owner on 31 October 2026. The original local checkout tracks `origin/main`. To obtain a fresh copy:

```powershell
git clone https://github.com/raj230848/FINN.git
Set-Location FINN
```

To publish later committed changes from the configured checkout, run `git push origin main`.

If Git requests credentials, authenticate using your normal GitHub credential flow. Keep credentials outside command-line arguments. `.env`, runtime databases, node_modules, Python environments and local screenshots are ignored. The supplied challenge PDFs are kept locally but ignored by Git. Primary company documents are included for reproducible research; their original copyright belongs to the issuer. Public visibility was explicitly requested by the user.

GitHub Actions are configured to run the isolated backend suite and frontend type/build checks on push/PR. Pushes trigger that workflow automatically. Check the repository Actions page for the current remote result; local results alone do not establish a successful CI run.

## Submission checklist

- Verify the prototype from a phone or narrow viewport.
- Provide the actual working URL and repository access to the evaluator.
- Attach/export the actual AI conversation history; the decision log is supplementary.
- Review and personalise `covering-email.md`, including the real links and your name.
- Send to `assessment@enam.com` with subject `ENAM - IIT screening - 2027` before the stated deadline, 1 November 2026.
- No email is sent automatically by the build scripts.

## Remaining-plan release checks

Run `python scripts/verify_release.py --backend-url https://YOUR_BACKEND --frontend-url https://YOUR_FRONTEND --refresh --gemini --out artifacts/hosted-acceptance.json` after configuring server-only secrets. The script rejects non-HTTPS remote targets and never saves tokens/cookies. Also perform actual access-code login, original source-link, incognito, second-device and restart/persistence checks on that host; HTTP health alone is insufficient. Do not run `--threshold-check` on a shared production desk; it is intended for an isolated QA database.

For optional delivery, add backend VAPID settings as described in browser-push.md. Keep the one-worker scheduler/outbox assumption. New tables are created additively at startup; back up the private database before upgrading. A real hosting account and its configuration are required; this repository does not turn the static Sites demo into a publicly hosted Python backend.
