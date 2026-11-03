# Premium storefront rebuild ? 2026-11-03

Local implementation complete; not committed, pushed or deployed.

## Delivered

Source-driven rebuild in `scripts/build_store.py`, `static/store.css` and `static/store.js`; generated output rebuilt. Product-led authentic CJ hero, one primary CTA, category exploration, compact honest preview disclosure, native collapsible mobile menu with Escape/outside-click handling, consistent photography above product information, two-column mobile cards, editorial use situations and selection criteria, support/order/legal footer and reduced-motion-aware interactions. Mobile category photography is now a 112px square at 390px and 92px at 320px; desktop uses 4:3 frames. The cleaning category retains the entire product within its frame. Detail galleries retain all authentic originals and responsive thumbnails. No audio, autoplay, synthetic evidence, fabricated prices or commerce claims were introduced.

The previous 390px receipt shows large white regions and infographic-led categories; the new mobile categories use compact image/text rows and photo-led frames. Desktop categories use equal landscape frames. Compare `receipts/premium-ux/comparison-390.jpg` and `comparison-1440.jpg`; both use the owner's existing `receipts/visual-recovery/after-home-*` as the before state. Original and new screenshots remain independently available.

## Validation

- 39 Python unittest tests passed. Pytest is absent; the repository documents unittest as its runner.
- 31 Node tests passed, including mocked payment/gateway tests. No real Sandbox transaction.
- Installed Chrome 156: 145 route/viewport checks (all 29 generated routes, including all 15 details, at 320/390/768/1024/1440), 75 disabled purchase checks, 305 gallery selections. Zero horizontal overflow, missing images or JavaScript errors. Mobile keyboard menu close/focus, no-JavaScript menu and preview disclosure pass.
- JS syntax and git whitespace checks pass. Existing CI now installs the locally verified Pillow 12.3.0 dependency needed by the pre-existing new gallery tests; no account/billing changes.
- Hash preservation receipt confirms no deleted starting files, no original media/data/Worker changes and unchanged legal policy body content. Earlier uncommitted work remains in place. Starting generator/CSS/JS are backed up in `receipts/premium-ux/source-before.zip`.

## Publication boundary

Local git cannot connect to GitHub. The GitHub connector confirmed remote main still matched local base `9d48116a8cb36f5b53b07a20e8013573bbac5481`, but its first blob-write request was refused: `MCP tool call requires approval, but approval policy is never`. No remote objects, commit or branch update were confirmed. No force push, reset, stash or git index mutation occurred. Live Chrome navigation failed with `ERR_NETWORK_ACCESS_DENIED`; the public URL and deployed asset versions are unverified.

Local CSS version: dae07d99c6f9. Local JS version: 53813cc7de79. See `receipts/premium-ux/validation.json`, `preservation.json`, `live-status.json` and `browser/browser.json`. Screenshot paths: `browser/home-{width}.png`, `browser/home-full-{width}.png`, `browser/categories-{width}.png`, plus representative product/gallery captures.

## Remaining

Publication under a write-capable session and actual deployed HTTP/asset verification. Supplier qualification, exact-variant authorization, US/GB cost/shipping/QC evidence and real Sandbox acceptance remain open. 61 genuine gallery images, 13 photo previews, two visual holds, zero qualified products, empty merchant feed and checkout disabled. Worker/D1/auth/financial configuration unchanged. No paid tools or ad spend.


## Live publication supersession — 2026-11-03

The earlier local-only publication boundary is superseded by [LIVE_DEPLOYMENT_ACCEPTANCE_20261103.md](LIVE_DEPLOYMENT_ACCEPTANCE_20261103.md). Remote main commit c0b245a5681df616145ec49e25e2c2bcd5fc3b95 is live at https://shop.askouresystems.com/. Read-only Chrome public QA passed 61/61 route/viewport checks (320–1440px), with zero broken loaded images, console errors or horizontal overflow. Every one of the 61 published CJ gallery assets returned HTTP 200. Checkout remains disabled; 0 qualified products and no verified Sandbox/real orders.
