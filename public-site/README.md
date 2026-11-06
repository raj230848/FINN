# FINN public Site

Mobile-first snapshot release of [FINN](https://finn-investment-desk.bk291269.chatgpt.site/). This directory mirrors the public Sites application. GitHub Actions updates its sourced feed independently of frontend publication.

Market history and NSE filings are checked by the Refresh public FINN data workflow every 30 minutes on weekdays, with post-close price checks. The browser checks the shared GitHub feed every minute, on focus/reconnect, or through Check for updates. Price history uses completed trading sessions and retains the original source dates. Provider failures retain the previous verified rows and expose a partial/unavailable status. Historical financial/guidance facts come from the committed reviewed manifest. Compact primary-source extracts are limited to at most 160 words per original document, with source/page links; no local runtime database, local user preferences or complete research text is exported. Preferences and watchlist edits are device-local. Live ingestion, arbitrary ticker discovery and document uploads are available in the full Python application.

From this directory, install dependencies, run the snapshot regression tests, and build the static site:

```sh
npm ci
node --experimental-strip-types --test tests/demo.test.mjs
npm run build
```

The build writes `out/`. GitHub stores the source and snapshot files. ChatGPT Sites manages publication of the public URL.
