# Shop Askoure Systems — AI and Digital Store

Owner decision: 12 November 2026. This replaces the old physical-pet-products affiliate plan on https://shop.askouresystems.com/.

## Implemented in this branch

- New responsive English/Arabic AI and digital-products discovery catalog, searchable and filterable.
- Product-detail dialog with email inquiry about plans, duration, price and delivery.
- Existing website generator dispatches to a deterministic digital-mode builder; no new infrastructure or cost.
- Old physical-shop URLs become noindex informational retirement pages with an exit to the new catalog and a historical-order support contact.
- Sitemap and feed no longer promote physical products; previous payment Worker remains disabled in repository settings.
- Separate digital tests; legacy physical-shop tests intentionally skipped only in digital mode; backend safety regression tests retained.

## Commercial limits

No active subscription offer or price is displayed until a concrete product/plan with delivery is prepared. The catalog shows discovery examples; availability is requested directly. No payment is collected by this website at this stage.

## Publication gate

Run Python unittest discovery, Node tests, and deterministic build comparison in GitHub Actions. Only merge after CI passes, then verify https://shop.askouresystems.com/ and mobile rendering; record outcome, not an assumed sale.
