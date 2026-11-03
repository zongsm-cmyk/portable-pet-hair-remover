# VerveLiving — Smart Everyday Problem Solvers

Storefront: https://shop.askouresystems.com · static GitHub Pages behind Cloudflare.

Three collections: Kitchen Innovations, Home Organization & Storage, Smart Cleaning Tools. This repository publishes a **checkout-disabled preview**, not a qualified 15-product commercial launch. FurOff is an indicative $34.99 preview; fourteen structured positions await sourcing. Missing supplier evidence remains null.

## Build and test

Python standard library; Node 24+ for gateway tests with built-in SQLite:

```powershell
python scripts/build_store.py
python -m unittest discover -s tests -v
node --check assets/store.js
node --test workers/order-gateway/test/*.test.mjs
```

`data/catalog.json` is the source of truth. `data/settings.json` holds public, non-secret settings. The build generates root HTML, three collection pages, fifteen product routes, five policy/contact pages, checkout return/cancel routes, feed, sitemap, robots, assets and Worker catalog. Use `--output <directory>` for an isolated generated preview. The deterministic `build-receipt.json` records counts and hashes.

Never set `verified_for_checkout=true` without actual CJ SKU/variant, fresh stock and US/UK shipping evidence, qualified ETA/weight/safety and profitable landed costs. Validation fails on incomplete qualification. Draft pages are noindex; drafts never enter the feed. Global checkout must also be enabled before feed offers are published.

## Payment and orders

`workers/order-gateway/` contains the Cloudflare Worker, D1 migration and tests. The production route is `shop.askouresystems.com/api/*`. `CHECKOUT_ENABLED=false` and `PAYPAL_ENV=sandbox` are deliberate. Prices are calculated server-side. Capture validates the actual PayPal response and persists an idempotent paid-order record. No PayPal credentials are in this repository or browser code.

The deployed service provides health, disabled order creation/capture, private lookup, protected fulfillment updates, and protected CJ CSV export. Export remains gated until the actual CJ account template is downloaded and mapped. Tests mock PayPal; they do not prove real Sandbox purchase or CJ import.

See [gateway operations](workers/order-gateway/README.md), [checkpoint](docs/CHECKPOINT.md), [backlog](docs/BACKLOG.md) and JSON receipts for current evidence and remaining acceptance work.

## Publication and rollback

GitHub Pages publishes committed root static files from main. The existing Pages build is separate from the validation workflow. Generate and test before committing. Never publish .dev.vars, OAuth state, customer records or CSV exports.

To stop payments keep both storefront and Worker gates false. Preserve newer owner changes and the private database when rolling back. Recover ambiguous captures using the original PayPal order ID; never create a replacement charge.

Free-tier infrastructure has quotas. It does not remove PayPal fees, supplier purchase costs, operating float or returns costs. No paid plan, live purchase or financial transfer was made by this implementation.
