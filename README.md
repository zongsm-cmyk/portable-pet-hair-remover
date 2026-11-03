# VerveLiving — Smart Everyday Problem Solvers

Storefront: https://shop.askouresystems.com · static GitHub Pages behind Cloudflare.

Three collections: Kitchen Innovations, Home Organization & Storage, Smart Cleaning Tools. Current tree: **15 research candidates, 13 authentic pictured previews, eight two-image galleries, two visual holds and zero qualified products**. Unqualified retail prices are null. FreshSeal and anonymous placeholders have been retired. Checkout remains disabled; no actual merchant Sandbox transaction is evidenced.

## Build and test

Python standard library; Node 24+ for gateway tests with built-in SQLite:

```powershell
python scripts/build_store.py
python -m unittest discover -s tests -v
node --check assets/store.js
node --test workers/order-gateway/test/*.test.mjs tests/*.test.mjs
```

`data/catalog.json` is the source of truth. `data/settings.json` holds public, non-secret settings. The build generates root HTML, three collection pages, fifteen product routes, five policy/contact pages, checkout return/cancel routes, feed, sitemap, robots, assets and Worker catalog. Use `--output <directory>` for an isolated generated preview. The deterministic `build-receipt.json` records counts and hashes.

`/cart/` supports qualified products, quantities 1–10, up to 15 distinct IDs, removal, US/GB and integer-cent display estimates. Only IDs/quantities enter session storage; the Worker recalculates every order. No active payment button exists while checkout is disabled. `/track-order/` provides the existing private lookup form. Inbound support delivery and automated email notifications remain unverified/not operational.

The optional `scripts/import_research_media.py` needs Pillow and the owner's external CJ research/cache. It validates all 13 originals and eight secondary images, their exact URLs, hashes, dimensions and reproducibility before writes. Missing/invalid media fails closed; it refuses to overwrite qualified commercial records. A normal site rebuild needs no external cache or Pillow and preserves all galleries. The two visual holds remain unpictured.

See [supplier evidence template](data/merchant-evidence.template.json), [Sandbox acceptance runbook](docs/PAYPAL_SANDBOX_RUNBOOK.md) and [commerce completion evidence](docs/COMMERCE_COMPLETION_20261103.md). `node scripts/commerce_qa.cjs` uses installed Playwright and local Chrome to test actual files plus labelled synthetic cart fixtures; screenshot output is outside this repository and no provider connection is made.

Never set `verified_for_checkout=true` without actual CJ SKU/variant, fresh stock and US/UK shipping evidence, qualified ETA/weight/safety and profitable landed costs. Validation fails on incomplete qualification. Draft pages are noindex; drafts never enter the feed. Global checkout must also be enabled before feed offers are published.

## Payment and orders

`workers/order-gateway/` contains the Cloudflare Worker, D1 migration and tests. The production route is `shop.askouresystems.com/api/*`. `CHECKOUT_ENABLED=false` and `PAYPAL_ENV=sandbox` are deliberate. Prices are calculated server-side. Capture validates the actual PayPal response and persists an idempotent paid-order record. No PayPal credentials are in this repository or browser code.

The Worker code supports health, disabled order creation/capture, private lookup, protected fulfillment updates, and protected CJ CSV export. Current deployment must be independently verified; local tests do not prove the live state. Export remains gated until the actual CJ account template is downloaded and mapped. Tests mock PayPal; they do not prove real Sandbox purchase or CJ import.

See [gateway operations](workers/order-gateway/README.md), [checkpoint](docs/CHECKPOINT.md), [backlog](docs/BACKLOG.md) and JSON receipts for current evidence and remaining acceptance work.

## Publication and rollback

GitHub Pages publishes committed root static files from main. The existing Pages build is separate from the validation workflow. Generate and test before committing. Never publish .dev.vars, OAuth state, customer records or CSV exports.

To stop payments keep both storefront and Worker gates false. Preserve newer owner changes and the private database when rolling back. Recover ambiguous captures using the original PayPal order ID; never create a replacement charge.

Free-tier infrastructure has quotas. It does not remove PayPal fees, supplier purchase costs, operating float or returns costs. No paid plan, live purchase or financial transfer was made by this implementation.

## P0 incident recovery, 3 November 2026

Later commits replaced the gated generator, static controller and catalog with legacy sources while retaining the earlier safety documentation and gateway. The P0 change restores the generator from a485047, preserves both unqualified product previews, and regenerates the actual root pages. CI now compares every generated file (including the Worker catalog) against committed output and tests browser receipt handling. See `docs/P0-INCIDENT-RECEIPT-20261103.json` for execution evidence and publication blockers.
