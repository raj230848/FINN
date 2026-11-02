# FINN typography update

FINN now uses **Manrope** for headings and **Inter** for body text, controls, research passages and financial figures. Both are locally bundled variable fonts, with the original license notices and provenance in `frontend/app/fonts/`. The two WOFF2 assets total 73,092 bytes; separate files per weight and runtime font-CDN requests are unnecessary.

The update replaces inconsistent Georgia/system-font declarations with shared reading and display tokens. Heading weights, spacing and line height are consistent across both themes. Research answers use a more comfortable line height. Financial figures retain tabular, lining numerals so prices and table columns are easier to scan. Mobile heading sizes and the library header adapt to narrow screens.

`frontend/app/typography.css` owns the typography rules. `next/font/local` loads the files with swap behavior and system fallbacks; the existing theme/bootstrap and component behavior are retained. Fontsource package versions, source URLs and asset hashes are recorded in `frontend/app/fonts/sources.json`.

Validation includes the 20 frontend regression tests, a production build/type validation, and browser inspections at mobile/desktop widths in both themes. Current screenshots and font-loading evidence are included under `audit/typography/` in the release ZIP. The unchanged backend's 299-test PDF import verification remains at `docs/pdf-import-verification.md` and `audit/pdf-import-fix/`.

Font sources: [Inter](https://fontsource.org/fonts/inter), [Manrope](https://fontsource.org/fonts/manrope). Full SIL OFL 1.1 notices are bundled alongside the unmodified assets.
