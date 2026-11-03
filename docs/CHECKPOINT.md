# VerveLiving expansion checkpoint — 2026-11-03

Owner scope: single code writer Codex; Dropshipping chat owns supplier qualification. No paid subscriptions, no new billing, no fabricated supplier evidence, no payment enablement without qualification and real Sandbox validation.

## Implemented in this change

- Central catalog with the three approved categories and 15 structured positions; FurOff remains an unverified $34.99 preview. Missing commercial inputs are null, never invented.
- Static generator for category/product/policy pages, eligible-product RSS, sitemap and robots. Retired neck/knee products no longer appear in generated storefront content.
- Cloudflare Worker with D1, server-priced payment creation/capture, unique capture reconciliation and replay recovery, private lookup, bearer-protected CSV and fulfillment update.
- Both storefront and Worker global checkout gates remain disabled. Catalog draft entries cannot be purchased even if a caller bypasses the UI.

## Deployment facts to consult

See `receipts/` for actual test and deployment results. Source files or a successful mocked test are not proof of a provider Sandbox or real order.

Cloudflare account `92605d871882fd9e88679cd2ff3e761e`, free D1 `verveliving-orders` (`9b063c58-8396-40f8-bc61-5d7928450b91`, WEUR) was created and migration `0001_orders.sql` applied. Configuration routes only `shop.askouresystems.com/api/*`; no other project service is part of this work.

## Required before selling

1. Obtain 14 fully qualified products and verify FurOff (5/5/5 total), actual CJ SKU/variant/stock/weight/safety and fresh US/UK quotes.
2. Replace catalog nulls with evidenced data. Refresh qualification within seven days. Check profitability per market and quantity, including fixed payment fees, duties, returns and currency assumptions.
3. Sign into PayPal Developer in the authorized browser. Store Sandbox app credentials as Worker secrets, validate create/approve/capture/replay/storage/export with a real Sandbox buyer. No live financial purchase is authorized by a test request.
4. Download the current account-specific CJ CSV template and verify the mapping; export fails closed until then. Test an import without submitting a paid CJ purchase.
5. Verify commercial account limitations/holds and establish the $15–$25 operating float with owner evidence; no float has been funded by this work.
6. Verify support inbox delivery, returns operations, and shipment handoff. Manual authenticated tracking updates exist; email/CJ submission/PayPal tracking automation is not implemented or claimed.
7. Only then consider live secrets and enablement. Merchant Center/Pinterest submission follows real approved inventory and buyer-ready pages, not a 0-item feed.

## Recovery

Prior local mobile/text fixes were backed up under `C:\Users\askgs\Documents\dropshipping\backups\pre-expansion-20261103` and committed before reconciling `origin/main`. Do not force-push or reset over newer work. To stop commerce keep `CHECKOUT_ENABLED=false`; the catalog and static pages alone cannot accept a payment. Never re-create a payment when capture outcome is uncertain; recover the original PayPal order ID.
