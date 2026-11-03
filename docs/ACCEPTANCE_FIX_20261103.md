# Owner acceptance fix — 3 November 2026

Photo counts and download blockers below describe the earlier session. Superseded by [CJ_MULTIPHOTO_RELEASE_20261103.md](CJ_MULTIPHOTO_RELEASE_20261103.md): 61 verified local gallery images across 13 previews. Commercial gates remain open.

Local base `main` was verified as `9d48116a8cb36f5b53b07a20e8013573bbac5481` before edits. Pre-existing untracked visual-recovery evidence was preserved. This receipt describes local source and generated files, not a public deployment or a commercial launch.

All 15 detail routes retain their links and now have one prominent native disabled **Buy now** button, a unique accessible reason (`aria-describedby`), the exact ordering-unavailable copy, and **Ask about availability** mailto. Real Add to cart appears only for a qualified product with global checkout enabled; it uses the existing cart/server payment flow. No unverified product can enter cart configuration, merchant feed or Offer schema.

All prior numeric target prices are retired from the live catalog and every generated customer page. Prices say **Price being verified**. Historical proposals remain in `RETIRED_PRICE_PROPOSALS_20261103.json` and the superseded pricing receipt, never as current offers. There are no replacement retail proposals. The primary sales section is empty. Thirteen existing photographed candidates appear separately as research previews; the hero no longer promotes cable bags, FurOff or the overweight colander. Photo-incomplete cards and all detail routes explicitly say **Additional product photos under verification**.

## Photos: actual files versus qualification

No new photographs were downloaded or fabricated. All 21 existing WebP files were preserved byte for byte, decoded, checked against provenance hashes/dimensions and visually inspected on an external contact sheet. Composite supplier artwork remains an entire preview image; no crop or split is counted as an additional photograph.

| Product | Existing local source-matched files | Meets four-photo qualification |
| --- | ---: | --- |
| ice-tray | 2 | No |
| fruit-colander | 2 | No |
| faucet-caddy | 2 | No |
| garlic-press | 2 | No |
| cup-drainer | 0 | No |
| 9hole-hanger | 2 | No |
| cable-organizer | 1 | No |
| folding-hanger | 1 | No |
| vacuum-hook | 0 | No |
| foldable-tote | 1 | No |
| furoff | 2 | No |
| drain-snake | 1 | No |
| microfiber-cloth | 1 | No |
| bottle-brush | 2 | No |
| mini-mop | 2 | No |

The stricter count of distinct photographs with exact selected variant AND supplier authorization verified is **zero for every SKU**. Historical generic CJ promotional-use notes are not a verified exact-variant license grant. The manifest records both counts, original URLs, original/optimized SHA256, dimensions, visual method and a false four-image-minimum flag.

Public CJ pages and gallery links for all 15 products were inspected through the web fallback. Candidate image URLs are in `CJ_GALLERY_DISCOVERY_20261103.json`; they are discoveries, not validated local photographs. Public extraction exposed no gallery links for cable-organizer and foldable-tote; several other image fetches failed. Direct `curl.exe -4` failed to connect to both the CJ listing host and image CDN. The connected browser access host was unavailable, and the chrome-use CLI was missing. Consequently no new original image bytes could be downloaded, hashed, visually checked and authorized. The fail-closed preview fallback is applied throughout.

## Qualification rules

Changing `verified_for_checkout` to true requires at least four distinct reviewed source/optimized hashes and URLs, with subject, exact variant, supplier rights and distinct-photo review. The generator also requires fresh stock evidence, actual US and GB shipping <=12 business days, processing <=48 hours, under 500g, confirmed no liquid/lithium/medical restrictions, supplier QC, a silent 15-second demo, a real problem solved and a Sandbox checkout evidence reference.

For each market, a same-variant competitor delivered-price comparison must be no older than seven days. Customs, taxes, payment fees and refund reserve must be explicitly evidenced along with supplier cost/shipping. The actual retail price must be at least 3x all-in cost; net contribution must be >=$12 and >=60%; delivered price cannot exceed the evidenced competitor price. Catalog margin cannot overstate either destination's calculation. No price or availability is inferred from factory inventory or missing quotes.

The observed 628g fruit-colander variant is held as over the limit. The drain-snake title no longer asserts 60cm; its 60cm provenance SKU and the supplier's 160cm quote are retained as an unresolved mismatch, without relabelling photos or inventing a new variant.

Six additional research records are isolated in `SOURCING_SHORTLIST_20261103.json`, outside the live catalog. They include owner snapshots and additional public CJ discoveries, with null retail prices, explicit blockers and no sellable approvals. One discovered drain filter is rejected under its current 72-hour processing terms. No new live product cards were added.

## Validation and boundary

- Python unit suite: 36 tests, including price removal, every disabled button, gates, media identity, links and deterministic LF/CRLF output.
- Positive qualification fixtures use synthetic evidence and a photo-count test double; separate negative tests verify the actual distinct-photo gate. These fixtures qualify no real product.
- Node suite: 31 tests, including existing Worker rejection, server pricing and mocked Sandbox flows. Mock tests are not a real provider Sandbox transaction.
- Installed Chrome 156.0.8078.74: 58 route/viewport checks at 390 and 1440px, including 30 detail button checks. Zero broken images, page errors, overflow, false numeric prices or external requests; native disabled buttons dispatch no click and trigger no navigation/payment.
- Screenshots, browser JSON and contact sheet: `C:\Users\askgs\AppData\Local\Temp\VerveLiving-acceptance-20261103` (outside git). Repeat using `node scripts/acceptance_qa.cjs`.
- Worker, D1 migrations/configuration, existing secret configuration, generated Worker catalog and sandbox settings remain unchanged. Checkout stays false; zero qualified products, zero feed items. No paid services, purchases, ad spend, payment charge or production publication occurred.

Remaining external work: download and verify 4–5 genuine authorized exact-variant photos; complete both-market supplier, competitiveness, QC and all-in profit evidence; execute an actual PayPal Sandbox lifecycle. Publish only the reviewed local revision through the existing release process; local checks do not prove public deployment.

Git handoff: staging was denied because the sandbox cannot create `.git/index.lock`. No commit or push was attempted after that denial. The manager must stage/commit the reviewed tracked edits plus the new acceptance docs, shortlist, gallery discovery, retired-price history, QA script and validation receipt. Preserve the pre-existing untracked `receipts/visual-recovery` images and ZIP.
