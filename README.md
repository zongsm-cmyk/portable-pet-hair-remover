# Shop Askoure Systems — Digital Products & AI Tools

Public domain: https://shop.askouresystems.com/ (GitHub Pages + Cloudflare).

Owner-led pivot on 12 November 2026 replaces the old VerveLiving physical-products editorial site with a digital catalog covering AI software, subscriptions, creative tools and downloadable products. Bilingual responsive catalog with search, filters and inquiries. No activated checkout, unverified sale, or claim of commission.

## Build and test

`python scripts/build_store.py`

`python -m unittest discover -s tests -v`

`node --test tests/*.test.mjs`

`node --test workers/order-gateway/test/*.test.mjs`

The default generator dispatches to `scripts/build_digital_store.py` in digital mode. Re-running it must reproduce committed HTML and `build-receipt.json`. Previous physical product pages stay as noindex retirement pointers for bookmarks and any historical enquiry. The order Worker/D1 database are preserved; checkout remains disabled (`CHECKOUT_ENABLED=false`, `PAYPAL_ENV=sandbox`).

See [migration checklist](docs/ASKOURE_DIGITAL_MIGRATION.md).
