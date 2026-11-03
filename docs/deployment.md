# Deployment and repository publication

The [public FINN site](https://finn-investment-desk.bk291269.chatgpt.site/) serves the dated Yahoo Finance and NSE snapshots bundled in [`public-site/`](../public-site/), alongside reviewed financials and cited source excerpts. Preferences and watchlists are stored on the device. The full-stack deployment below runs the Python API for live refresh and document imports.

## Local production mode

Start the Python backend with the supplied PowerShell script. In a separate terminal:

```powershell
Set-Location frontend
npm.cmd run build
npm.cmd run start
```

For normal development use `npm.cmd run dev`. The checked-in dependency locks capture the versions tested for this prototype.

## Recommended full-stack deployment: one Render service

The root `Dockerfile` and `render.yaml` now host the actual Next.js frontend and FastAPI backend together. Only Next.js listens on the public port; Python listens on container loopback. The browser uses same-origin `/api/*` URLs. The supervisor stops both children if either service exits, so the host can restart the stack. On a new mounted disk, it prepares the database-file ownership and drops to the `finn` user before launching either service.

1. Connect this GitHub repository in your Render account and create a Blueprint from `render.yaml`. [Open Render's repository deployment flow](https://render.com/deploy?repo=https://github.com/raj230848/FINN). The configured starter service and persistent disk can incur charges; creating a deployment still requires the account owner's billing/hosting choice.
2. Keep **one instance** and the persistent disk at `/var/lib/finn`. `DATABASE_URL` is set to `sqlite:////var/lib/finn/finn.db`. Start with a fresh evaluator database. Render generates separate backend, desk-access and session-signing secrets. Keep the desk code for operators who manage shared data.
3. Set a newly rotated `GEMINI_API_KEY` in private runtime settings. For optional push, transfer the three VAPID settings directly from the private local `.env` into host secrets. These keys are excluded from the source ZIP.
4. Render's `RENDER_EXTERNAL_URL` supplies the trusted browser origin. For a custom domain or another host, set `FINN_PUBLIC_ORIGIN=https://your-domain.example` explicitly. It must be an origin without a path/query. Origin validation and Secure cookies use this trusted value rather than an arbitrary forwarded header.
5. Use public readiness `/api/ready` for the health check. The blueprint also enables `FINN_GUEST_MODE` for evaluator access. Guests can browse the allowlisted public data and query indexed documents using bounded extractive research. A signed desk session is required to change shared settings, refresh, import documents, use Gemini, or subscribe to push. Set `FINN_GUEST_MODE=false` for a private desk.
6. Run the hosted acceptance and device checklist below on a **separate evaluator/QA instance**, then populate the verified full-stack URL in the covering note.

Render persistent disks are limited to one service instance and disable zero-downtime deploys; plan a brief interruption during updates. See [Render disk behavior](https://render.com/docs/disks) and the [Blueprint specification](https://render.com/docs/blueprint-spec). This repository configures deployment; it does not create a host account or establish a successful public deployment by itself.

GitHub Actions includes a full-stack container job: build the root image, start an isolated named volume, test public readiness and authenticated frontend operations, write a private QA preference marker, restart the container and verify the marker survived. Read the latest actual workflow result before claiming it passed. These checks make no paid Gemini calls and send no push notifications.

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
2. Host the backend using `backend/Dockerfile` on a Python/container host. The root `render.yaml` now deploys the combined stack; use a separate backend service only if you deliberately prefer two hosts. A persistent disk can incur charges. The public-source adapters are best effort and may be blocked from a data-centre IP even when local tests work.
3. Set `DATABASE_URL=sqlite:////var/lib/finn/finn.db` and mount persistence at `/var/lib/finn`. Keep one worker. Health endpoint: `/api/health`.
4. Set `PUBLIC_DEPLOYMENT=true` and a strong `FINN_API_TOKEN` on the backend (startup refuses a missing token). If using the Render blueprint, it generates a token; copy the resulting value directly into the frontend's server-only environment setting. Never commit it.
5. Optional: set `GEMINI_API_KEY` and `GEMINI_MODEL=gemini-3.5-flash-lite` on the backend. Leave the key empty for extractive-only operation.
6. Import the GitHub repository into Vercel with **Root Directory `frontend`** and the Next.js framework preset. The build command is `npm run build`.
7. Set server-only `BACKEND_URL` to the deployed HTTPS backend origin (no `/api` suffix). Set the matching server-only `FINN_API_TOKEN`. Neither variable uses a `NEXT_PUBLIC_` prefix.
8. Set frontend `FINN_PUBLIC_MODE=true`, `FINN_ACCESS_TOKEN` (at least 16 characters) and `FINN_SESSION_SECRET` (at least 32 random characters). Vercel/Render enable the gate automatically. Anonymous proxy requests return 401; sign-in creates an eight-hour signed HttpOnly cookie. POST/PUT/PATCH require same-origin requests. This protects one shared desk; add individual accounts and per-user storage for a multi-user product. Keep platform deployment protection enabled as an additional control.
9. Verify backend health, open the frontend, switch to Sourced data, refresh, and inspect partial-error handling and source timestamps. Then test a research question and both guidance evidence links.
10. Copy only the **actual successfully verified** URLs into the covering email. A provider dashboard or a configured project is not a deployed-product URL.

The Next.js API proxy gives `POST /api/documents` a bounded 180-second window; other operations retain their 55-second timeout. The route declares a 180-second maximum duration. Configure the actual host/proxy to honor that duration; a platform can still impose a shorter limit. Imports accept up to 3,000 pages and 60,000,000 downloaded bytes by default, with explicit extracted-text, passage-count and extraction-time limits documented in `.env.example`. PDF pages are never silently truncated. Extraction's time budget is checked between pages, not enforced by a separate worker process. Very slow hosts or adversarial PDF parsing still require an isolated durable worker/job API. If a connection times out, check Source library before retrying because the server may finish the original import.

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

For the combined stack, prefer `scripts/verify_hosted.py`: it signs into the frontend, checks response fields and cookie flags, verifies persisted preference/watchlist/read-state effects, tests logout, and inventories all 25 backend operations (the original 24 plus protected operational status). It marks unavailable optional operations **not verified**. It never invents a browser subscription. See [hosted and physical-device acceptance](hosted-acceptance.md) for exact commands and remaining manual checks.

For optional delivery, add backend VAPID settings as described in browser-push.md. Keep the one-worker scheduler/outbox assumption. New tables are created additively at startup; back up the private database before upgrading. A real hosting account and its configuration are required; this repository does not turn the static Sites demo into a publicly hosted Python backend.
