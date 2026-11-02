# Neon Aurora Glass and Champagne Bubble Light

Implemented 2 November 2026 from the supplied theme-change guide. This supersedes the Midnight Orchid / Warm Ivory visual palette described in `docs/ui-ux-upgrade.md`; the search, freshness and research behavior from that release is retained.

## Visual system

Dark mode uses a deep navy canvas, cyan interactions and price charts, violet ambient glow, solid navy reading surfaces and semantic green/red signals. It follows the Neon Aurora reference while keeping FINN's current layout, controls and research workflow.

Light mode uses the guide's champagne base `#F8EEDF`, pale upper area `#FFF7EC`, peach warmth `#F6C892`, bubble highlights `#FFF9F1`, ivory cards `#FFFCF8`, soft borders `#E7D8C4` and graphite text `#1F2937`. A fixed, non-interactive background layer contains 15 static CSS spheres with rounded rims, pearl highlights and soft peach shading. Their sizes and positions adapt for mobile; the bubbles remain visible around the workspace when scrolling. The layer is hidden from screen readers and disabled in dark mode. There are no added image assets, animated backgrounds, crown/watermark labels or floating decorative buttons. Cards, charts, search suggestions and research text remain on opaque surfaces.

Bronze `#A86A2A` and soft bronze `#D9B48C` define warm borders and highlights. The text/button bronze is slightly darker (`#915A24`) to satisfy the existing 4.5:1 text contrast checks, including selected controls. Green/red text similarly uses accessible darker variants of the recommended semantic colors. Primary buttons have white text and a darker bronze hover; secondary controls are ivory with bronze borders. The sidebar's selected item uses soft peach rather than a filled primary button.

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
