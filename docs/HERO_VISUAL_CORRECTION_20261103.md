# Local photo-led homepage correction ? 2026-11-03

The text-only hero and icon-only categories are replaced with exact existing CJ product photography. Desktop uses a 55/45 text/photo grid; mobile stacks the headline and a prominent uncropped photo. The featured green FurOff roller uses its canonical gallery image 01, linked to its existing detail page. Category photography maps fruit-colander to Kitchen Innovations, folding-hanger to Home Organization & Storage, and furoff to Smart Cleaning Tools. All images use contain sizing and product-specific alt text.

The announcement and preview disclosure are compact. Mobile navigation is a single horizontal scroll row; contact and cart retain legible 44px targets. Preview cards show Price under verification and an unobtrusive 4/5 supplier photo count. Detail pages keep their existing Price being verified wording and native disabled Buy now with the explicit reason.

Sources changed for this correction: scripts/build_store.py, static/store.css, scripts/acceptance_qa.cjs, tests/test_pricing_visibility.py. Generated pages, CSS and receipt were rebuilt. Existing dirty work, canonical media, catalog, provenance and sourcing records are preserved. No stage, commit or publication was attempted.

Validation: 39 Python and 31 Node tests pass. Local installed Chrome QA covers 320/390/768/1440, validates decoded hero dimensions and placement, exact category/product/image mappings, navigation touch heights, 13 preview cards, all disabled detail buttons, galleries, no document overflow, missing images, external requests or JavaScript errors. Final browser evidence is browser.json in the directory below.

Screenshots and browser evidence: C:/Users/askgs/AppData/Local/Temp/VerveLiving-acceptance-20261103. home-{width}.png shows the opening viewport; home-full-{width}.png shows the complete page; categories-{width}.png shows the photographed category tiles.

Local verification only. Checkout remains false; 15 details, 13 pictured previews with 61 gallery WebPs, two visual holds, zero qualified products and an empty merchant feed remain. Real sandbox acceptance and production verification are not claimed. Manager review, integration and publication remain pending, alongside existing supplier and commerce qualification requirements.
