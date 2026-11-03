# Pricing visibility receipt ? 3 November 2026

## Delivered tree and boundary

Populated numeric **nonbinding launch targets** on all 13 photographed home cards, their three category collections and all 13 detail pages. Two visual holds remain unpriced. English disclosure appears above page content; card labels say ?Planned launch price? and ?Not available to order?; details say ?Provisional launch target ? not a payable price?. Card prices are 30?32 px and detail prices 42?46 px, with dark high-contrast text.

All 15 actual `price_usd` values remain null; qualification remains false, stock unknown, checkout false and PayPal sandbox. No add-to-cart buttons, Product/Offer rich snippets or feed items are emitted. Targets never enter cart configuration, and even future enabled-build Worker exports strip both preview fields. No Worker/D1 configuration, supplier photographs, billing or provider payment was changed.

This is **locally verified release-ready source and generated output**, not a proven public deployment or commercial launch. Local HEAD and cached origin/main: `6b1ea32f51a0eb6a7e1a0d16f0a5ae1923e695bf`. `git ls-remote origin refs/heads/main` failed to connect to github.com:443; current remote main could not be verified. No push was attempted. Preserve the pre-existing untracked visual-recovery images and source-handoff ZIP.

## Source and exact targets

Owner file: `C:\Users\askgs\Documents\dropshipping\VERVELIVING_PRICING_CANDIDATES_NONBINDING_20261103.json`.

Source SHA-256: `88d3f059fb86b22d365f227bbe888e6b79516f1f4e822ebe4b314879de550454`.

Only ID/target figures were imported. Sample quotes, variant mismatches, factory counts and cost estimates were not imported as qualified terms. US samples exclude unknown duties; UK quotes, exact variants and stock remain unverified. Cable bag, FurOff roller and chopper have competitor price-pressure flags; no competitiveness or margin claim is made. Reevaluate all proposals before any launch.

| Product ID | Proposed USD |
| --- | ---: |
| ice-tray | $29.99 |
| fruit-colander | $54.99 |
| faucet-caddy | $39.99 |
| garlic-press | $34.99 |
| 9hole-hanger | $24.99 |
| cable-organizer | $39.99 |
| folding-hanger | $34.99 |
| foldable-tote | $29.99 |
| furoff | $34.99 |
| drain-snake | $29.99 |
| microfiber-cloth | $29.99 |
| bottle-brush | $29.99 |
| mini-mop | $39.99 |

`cup-drainer` and `vacuum-hook`: null / NOT_EVALUATED.

## Verification

- `scripts/build_store.py`: 15 pages, 13 photographed, 2 holds, 0 qualified, 0 merchant items, checkout paused.
- Python unittest: **35/35 passed**, preserving the original 31 tests; the former blanket ban on `$34.99` was updated to assert its nonbinding disclosure and no offers.
- Node tests: **31/31 passed**, including all prior 29 and two Worker quote isolation regressions. Every preview is rejected for both destinations; an injected preview target never replaces an independent actual price.
- `node --check`: source/generated store JS, Worker module, pricing QA script; passed.
- LF/CRLF asset and entire generated-tree equality: passed. Generator uses normalized UTF-8/LF output; no platform-specific generation was introduced. Linux CI was not run locally.
- Actual installed Chrome `156.0.8078.74`: **87 route/viewport checks** (29 routes ? 320/390/1440), **117 numeric price checks**. No document overflow, clipped prices, broken loaded assets, page errors or external requests. Every card's price/status fits in the 900 px viewport when scrolled to its photograph. Existing Python link checks cover all local link targets.
- Computed price text: `rgb(41, 46, 41)`, ?30 px; screenshot review confirmed mobile home and desktop detail layout.
- `git diff --check`: passed. Protected `workers/`, source images and `data/settings.json` have no diff.

External screenshots and computed-style report: `C:\Users\askgs\AppData\Local\Temp\VerveLiving-pricing-20261103` (`home-prices-{390,1440}.png`, `detail-price-{390,1440}.png`, `pricing-browser.json`).

Browser report SHA-256: `4a436723fd8955d40c8860e1bc7c5a18b6cd97010afc3900bd9bc99c897a7aab`.

Generated `build-receipt.json` SHA-256: `e68e06262f4fe057e2cc8a55da775ac0e3df4ff84f95adb555bf6170c53ec77e`.

## Release handoff

The scoped `git add` failed with `Unable to create .../.git/index.lock: Permission denied`. No commit was created and the index was not changed. No alternate controller, lock removal or retry was used. Changed files remain in the workspace for the manager to commit and publish.

After checking fresh remote main against the expected baseline, commit/publish this exact source and generated tree through the existing static-site pipeline. Do not enable payments or deploy Worker/D1. Read back the public home, all three category collections and the 13 pictured product details after deployment; public acceptance remains outstanding. No force-push or owner-state overwrite.
