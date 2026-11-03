# FINN public Site

Mobile-first snapshot release of [FINN](https://finn-investment-desk.bk291269.chatgpt.site/). This directory mirrors Sites source revision `beba39578c555777d1f622a84e40984682c7bfe8` from published version 7.

Market prices and filings are dated snapshots from Yahoo Finance and NSE. Historical financial/guidance facts come from the committed reviewed manifest. Compact primary-source extracts are limited to at most 160 words per original document, with source/page links; no local runtime database, local user preferences or complete research text is exported. Preferences and watchlist edits are device-local. Live ingestion, arbitrary ticker discovery and document uploads are available in the full Python application.

From this directory, install dependencies, run the snapshot regression tests, and build the static site:

```sh
npm ci
node --experimental-strip-types --test tests/demo.test.mjs
npm run build
```

The build writes `out/`. GitHub stores the source and snapshot files. ChatGPT Sites manages publication of the public URL.
