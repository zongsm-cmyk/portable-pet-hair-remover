# Shop Askoure Systems — Digital Products & AI Tools

Public domain: https://shop.askouresystems.com/ (GitHub Pages + Cloudflare).

**English product comparison and direct Gumroad checkout links:** [Askoure Systems Developer Kits](https://shop.askouresystems.com/offers/?utm_source=github&utm_medium=organic&utm_campaign=readme_developer_kits).

Owner-led pivot on 12 November 2026 replaces the old VerveLiving physical-products editorial site with a digital catalog covering AI software, subscriptions, creative tools and downloadable products. Bilingual responsive catalog with search, filters and inquiries. No activated checkout, unverified sale, or claim of commission.

## Original digital kits — available now

Only these three **original downloadable products** are available for purchase. Checkout and delivery use the seller's external Gumroad pages; local shop checkout is not enabled.

| Product | One-time price | Product details | Gumroad checkout |
| --- | ---: | --- | --- |
| n8n Workflow Preflight Auditor | $9 | [View kit](https://shop.askouresystems.com/digital-products/n8n-workflow-preflight-auditor/?utm_source=github&utm_medium=organic&utm_campaign=shop_source_readme) | [Buy](https://mhamedasskoure.gumroad.com/l/n8n-workflow-preflight-auditor) |
| LLM Reliability Rescue Kit | $19 | [View kit](https://shop.askouresystems.com/digital-products/llm-reliability-rescue-kit/?utm_source=github&utm_medium=organic&utm_campaign=shop_source_readme) | [Buy](https://mhamedasskoure.gumroad.com/l/llm-reliability-rescue-kit) |
| Agent Runaway Guard Kit | $24 | [View kit](https://shop.askouresystems.com/digital-products/agent-runaway-guard-kit/?utm_source=github&utm_medium=organic&utm_campaign=shop_source_readme) | [Buy](https://mhamedasskoure.gumroad.com/l/agent-runaway-guard-kit) |

The 12 third-party AI/software subscription cards remain **out of stock**; prices and links above are product offers, not evidence of received sales.


## Build and test

`python scripts/build_store.py`

`python -m unittest discover -s tests -v`

`node --test tests/*.test.mjs`

`node --test workers/order-gateway/test/*.test.mjs`

The default generator dispatches to `scripts/build_digital_store.py` in digital mode. Re-running it must reproduce committed HTML and `build-receipt.json`. Previous physical product pages stay as noindex retirement pointers for bookmarks and any historical enquiry. The order Worker/D1 database are preserved; checkout remains disabled (`CHECKOUT_ENABLED=false`, `PAYPAL_ENV=sandbox`).

See [migration checklist](docs/ASKOURE_DIGITAL_MIGRATION.md).
