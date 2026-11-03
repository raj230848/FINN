# Mobile interface verification — 2 November 2026

The chart period selector overflowed the market card at phone widths. Research tab labels also shrank below their text width. Both issues were reproduced before changing the layout.

## Changes

- Price and volume retain visible 1W, 1M and 3M controls in their own full-width phone row.
- All four research views use a two-column phone layout with wrapping labels. Sticky tabs clear the 122px mobile search header, and focused controls have scrolling clearance.
- Company names, source counts, research headings and form actions wrap within their cards.
- Custom signal dates remain editable on the page as well as in the filter dialog.
- The watchlist's Find a company button keeps its label width. A labeled phone sector selector exposes the complete sector list without a horizontal chip strip. Desktop sector chips remain available.

## Verification

Responsive browser checks covered widths 320, 360, 390, 430, 760, 768, 1024 and 1440 pixels, both themes, plus compact 320×568 and landscape 844×390 research layouts. Phone market and research controls fit their containers. Desktop sector chips and wide tables retain intentional horizontal scrolling.

Interaction checks changed all six price/volume period combinations and confirmed 5, 22 and 65 completed sessions. Further checks opened every research view, changed the reviewed financial quarter to 2025-Q3, opened the issuer PDF import form, applied custom dates, opened alert preferences and notifications, changed a company drawer to 1W, and selected the Technology watchlist sector to show HCLTECH.

All 20 frontend tests passed. Production build and public-preview acceptance evidence are retained in the ignored `artifacts/mobile-responsive` and `artifacts/mobile-preview` folders. No backend code changed. No paid Gemini request or push notification was sent for these interface checks.

Automated checks use a responsive desktop browser; they do not establish testing on every physical phone, operating system, browser or accessibility setting. Actual phone verification remains a separate user check.

## Copy and dark readability update — 3 November 2026

Removed repeated slogans, promotional subtitles, decorative workspace/profile text and the marketing footer. Page titles and empty states now describe their purpose directly. Financial and guidance calculation details remain available in expandable notes; dates, source links, unavailable-data warnings, errors and all controls remain available.

The dark canvas, cyan/violet accents and bubble positions are retained. Reading surfaces are slightly deeper, text colors are brighter and bubble opacity is reduced to 0.55. The 12 tested combinations of main/secondary/muted text against canvas, surface, raised surface and control backgrounds have a minimum contrast of 8.01:1. This is a palette measurement, not a claim about every composited pixel or image.

All 20 frontend tests passed, including expanded dark contrast checks. Browser checks covered dark layouts at 320, 390, 768 and 1280 pixels and light layouts at 320, 390 and 1280 pixels, with no page overflow or clipped research tab labels. Financial and guidance notes expanded successfully. The light palette was preserved. Evidence is in the ignored `artifacts/mobile-responsive/clarity-*` and `dark-readability-contrast.json` files.

## Mobile menu and market artwork — 3 November 2026

Reproduced Overview being covered by the search header: the sidebar had z-index 40, below the header at 45. On phones the sidebar now uses 90, with an 80 backdrop. It has a close button, safe-area padding, independent vertical scrolling, Escape handling, focus trapping and focus restoration. The main interface becomes inert while the menu is open. Opening preferences closes the menu, and returning to desktop width resets the menu and body scroll lock.

Verified Overview was the actual hit target at 320, 360, 390 and 430px. At 320×568, all four navigation buttons, the close button and preferences were on screen and passed hit-target checks. Verified Overview selection, pointer-click backdrop dismissal, Escape, both ends of the keyboard focus loop, preferences opening/closing and desktop resizing. Both themes were inspected. The 20 frontend tests passed.

Two built-in image_gen illustrations were saved as local WebP assets: stock-market candlesticks and connected global markets. Together they are 44,694 bytes. They are static, aria-hidden, pointer-events-none backgrounds; cards keep opaque reading surfaces. Palette, blend and opacity rules adapt the artwork to dark and light themes. Source prompts and asset details are in `frontend/public/images/market/README.md`; raw originals and browser evidence remain in ignored `artifacts/market-art`.

## Globe replacement and themed dropdowns — 3 November 2026

Removed the separate sphere elements completely. The clean global-market artwork from the supplied reference is now the primary background, with secondary candlestick artwork. Light mode uses dedicated champagne/bronze variants generated with the built-in image_gen tool, rather than faded/inverted dark assets. The new light files total 92,532 bytes. Cards retain opaque reading surfaces.

Single-value Select controls now use themed, rounded popups with selected checkmarks, hover/keyboard highlights, wrapping option labels and 48px phone rows. A hidden native select retains actual change events, form values and validation; existing API callbacks were not rewritten. Multi-select/listbox-size controls retain native behavior (none are currently used for dropdowns). Popups render above cards/dialogs and choose above/below placement within the viewport. They support arrows, Home/End, typeahead, Enter/Space, Escape, Tab and outside clicks. Escape closes an open popup before its parent dialog.

All 26 frontend tests passed, including six new checks covering disabled/empty lists, wrapping keyboard navigation, ticker/name matching and popup positioning at narrow/short viewport edges. Browser checks changed the chart to INFY and HCLTECH, filtered the watchlist to Technology, selected a 2025-Q3 financial quarter, changed the document type, exposed custom-date fields, changed an unsaved monitoring lookback, and verified popup dismissal and parent-dialog Escape behavior. Popup rectangles fit at 320, 390, 768 and 1280px; a short 320×568 dialog popup also fit. Browser inspection confirmed zero old bubble elements and zero visible native single-select menus. Tests did not submit a document or send a Gemini request.
