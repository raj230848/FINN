# Neon Aurora Glass and Champagne Bubble Light

Implemented 2 November 2026 from the supplied theme-change guide. This supersedes the Midnight Orchid / Warm Ivory visual palette described in `docs/ui-ux-upgrade.md`; the search, freshness and research behavior from that release is retained.

## Visual system

Dark mode uses a deep navy canvas, cyan interactions and price charts, violet ambient glow, solid navy reading surfaces and semantic green/red signals. At the user's request, it now includes glossy navy spheres with cyan rims, violet reflections and cool highlights. The mobile heading area exposes the background while KPI and reading cards stay opaque.

Light mode keeps the champagne bubble style with a deeper warm palette requested by the user: base `#E3C6A5`, upper area `#F0DFC9`, bronze warmth `#CDA879`, cream cards `#F6EBDD`, stronger borders `#C6A583` and graphite text `#1F2937`. A fixed, non-interactive background layer contains 15 static CSS spheres with rounded rims and pearl highlights, with shading matched to each theme. Their sizes and positions adapt for mobile; the bubbles remain visible around the workspace when scrolling. The layer is hidden from screen readers and never intercepts input. There are no added image assets, animated backgrounds, crown/watermark labels or floating decorative buttons. Cards, charts, search suggestions and research text remain on opaque surfaces.

Bronze `#8B582B` and soft bronze `#C5A078` define warm borders and highlights. Text/buttons use deeper bronze `#603710`. Helper text, secondary labels, bronze actions and teal source metadata also meet 4.5:1 against the darkest champagne gradient color, rather than being tested only on cards. Green/red text retains accessible semantic colors. Primary buttons have white text and a darker bronze hover; secondary controls are cream with bronze borders. The sidebar's selected item uses warm champagne rather than a filled primary button.

All shared tokens remain centralized in `frontend/app/themes.css`. `frontend/lib/theme.ts` supplies the same canvas colors to initial theme bootstrap, browser metadata and the interactive toggle, so reload and theme switching stay consistent. Theme storage remains `finn.theme.v1`; no preferences are reset by the upgrade.

## Guide acceptance checklist

| Requirement | Implementation and verification |
|---|---|
| Neon Aurora dark theme | Navy/cyan/violet palette and clean chart surfaces; desktop/mobile browser inspection. |
| Champagne Bubble light | Champagne/peach gradient with static translucent background bubbles and bronze controls; desktop/mobile screenshots. |
| Readable KPIs, charts and research | Opaque ivory reading surfaces, graphite headings/numbers, themed axes/tooltips. Palette contrast tests and browser inspection. |
| Obvious dropdowns | Native selects retain bronze borders, chevrons, selected state, focus and 44px minimum control height. Mobile filter dialog inspected. |
| Name and ticker search | Existing full NSE directory autocomplete preserved; HCL Technologies/HCLTECH verified through the local endpoint and menu. |
| Sourced default, optional Demo | Existing mode behavior preserved; sourced hard reload and visible replay controls checked. |
| Automatic/manual refresh | Scheduling, shared reservations, last-good cache and API logic unchanged; backend regressions pass. Manual action remains visible. |
| Mobile theme consistency | 360px and 390px browser emulation plus desktop. Geometry and screenshots saved with no horizontal document overflow in those checks. |
| Calm dense content | Bubbles exist only in the outer page layer; cards, dialogs, popovers and research surfaces are solid. |
| No reference-image UI artifacts | The reference image is not embedded. No crown, image-generation watermark or decorative floating button is added. Existing functional icons retain their purpose. |

## Validation

- 272 backend tests pass, including directory identity, authorization, refresh reservation, cadence and failure cases.
- 14 frontend tests pass, including stored-theme bootstrap, blocked-storage fallback and dark/light contrast checks.
- Next.js production build and type validation pass.
- Current browser evidence and screenshots are included under `audit/neon-aurora-theme/` in the updated ZIP. These are browser viewport checks, not physical-device acceptance.

No backend provider behavior, credentials or hosting configuration changes are part of this theme update. Previous Gemini/provider and physical push-delivery limitations remain documented in the historical reports; no new paid model call was required for this visual change.
