# CJ multiphoto local release - 3 November 2026

Supersedes the photo shortage in ACCEPTANCE_FIX_20261103.md. Existing uncommitted pricing, disabled purchase UI, qualification gates and research were preserved. Local source and generated output only; no production publication.

61 approved genuine CJ images now serve 13 research previews. The 66-image owner cache was used directly without scraping. Each selected original `.source` and optimized WebP was decoded and SHA256 checked against the manager report. Every published source URL, original SHA and optimized SHA is globally distinct. Total optimized bytes: 3,666,512; largest file: 163,352 bytes (<256,000). Original dimensions and optimized dimensions, source URL, exact CJ listing/SKU, approved pick and conditional promotional-use terms are in `data/image-provenance.json`. Manager reviewed exact-product contact sheets; this does not establish a purchasable exact variant or a blanket copyright license.

| Product ID | Photos | Approved report picks |
| --- | ---: | --- |
| ice-tray | 4 | 1, 2, 3, 5 |
| fruit-colander | 5 | 1, 2, 3, 4, 5 |
| faucet-caddy | 4 | 1, 2, 4, 5 |
| garlic-press | 5 | 1, 2, 3, 4, 5 |
| cup-drainer | 0 | visual hold |
| 9hole-hanger | 5 | 1, 2, 3, 4, 5 |
| cable-organizer | 5 | 1, 2, 3, 4, 5 |
| folding-hanger | 5 | 1, 2, 3, 4, 5 |
| vacuum-hook | 0 | visual hold |
| foldable-tote | 5 | 1, 2, 3, 4, 5 |
| furoff | 4 | 1, 2, 3, 4 |
| drain-snake | 5 | 1, 2, 3, 4, 5 |
| microfiber-cloth | 4 | 1, 2, 3, 4 |
| bottle-brush | 5 | 1, 2, 3, 4, 5 |
| mini-mop | 5 | 1, 2, 3, 4, 5 |

Four-photo previews: ice-tray, faucet-caddy, furoff, microfiber-cloth. All other displayed products have five. Excluded picks remain excluded: ice-tray #4, faucet-caddy #3, furoff #5/#6, microfiber-cloth #5. No composite was split or duplicate file counted. The 21 historical media files and their provenance are preserved (`archived_images`), while the catalog exclusively references the 61 canonical gallery paths.

Galleries use scroll-snap thumbnails on narrow screens. Each click changes the visible photo, pressed state, descriptive alt and live caption. Every preview explicitly says colors are illustrative and the exact variant remains unverified. Drain-snake explicitly distinguishes pictured 60cm from the prior 160cm quote. The observed 628g colander remains unqualified. Cup-drainer and vacuum-hook remain hidden, unpictured, unpriced and noindex.

All 15 details retain native disabled Buy now, the explicit inventory/shipping/checkout reason, and Ask about availability. No fabricated retail price, stock, testimonial or guarantee was introduced. Checkout false, 0 qualified products, 0 merchant feed items; all product routes remain noindex. Future real Add to cart requires both qualification evidence and global checkout enablement. Worker, D1, PayPal configuration/secrets were untouched.

Canonical media: use `python scripts/build_store.py` to rebuild pages; it preserves the catalog/media. Legacy `import_research_media.py` now refuses to overwrite this canonical catalog. `import_cj_galleries.py` can reproduce the approved galleries from the owner cache without replacing research/commercial fields. The generator rejects visible counts outside 4?5, missing/mismatched media provenance, duplicate sources/optimized hashes/URLs, non-CJ sources and invalid WebP headers/oversize assets. The existing stricter four exact-variant authorized photo activation gate remains.

Validation: 39 Python tests passed (including decoded gallery files, exact picks, duplicate/missing/source/WebP failures, commercial gates and LF/CRLF build determinism); 31 Node tests passed (provider flows mocked only). Installed Chrome 156.0.8078.74 passed 87 route/viewport checks, 45 disabled detail button checks and 183 actual gallery thumbnail actions at 320/390/1440px. Each rendered photo was decoded, visible and distinct by a 64px canvas pixel comparison. Zero missing images, external requests, JS errors or document overflow. Screenshot/browser JSON evidence stays outside git in `%TEMP%/VerveLiving-acceptance-20261103`.

The existing six-item sourcing shortlist stays outside the live catalog. Additional screening reference only: `../VERVELIVING_NEW_PRODUCT_SCREENING_20261103.json`, 11 records (2 rejected / 9 research), SHA256 `8b9709635e3475550477b1ffe4cec426bc3c92d5a754036e7e1e7d8cb229d85d`. No extra catalog slots or product approvals were added.

Remaining: manager publication/production verification; genuine stock, selected variant, US+GB shipping, safe weight, supplier QC, competitive all-in net margin and actual PayPal Sandbox acceptance before any checkout enablement. No paid costs or push attempted.

Git handoff: `git add` was attempted for all reviewed tracked changes, 61 new gallery assets, new scripts/tests and small JSON/Markdown evidence. The sandbox denied creating `.git/index.lock` (Permission denied). No local commit or push was made; manager must stage/commit and publish. Existing screenshots and ZIP receipts were excluded and preserved.
