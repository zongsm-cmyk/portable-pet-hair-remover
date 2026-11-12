"""Deterministic digital/AI discovery-store renderer for Shop Askoure Systems."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
LEGACY_ROUTES = ["cart/index.html","categories/smart-cleaning-tools/index.html","checkout/cancel/index.html","checkout/index.html","checkout/return/index.html","guides/protect-car-doors-from-dog-scratches/index.html","guides/remove-pet-hair-from-car-seats/index.html","guides/remove-pet-hair-from-sofa/index.html","policies/privacy/index.html","policies/refunds/index.html","policies/shipping/index.html","policies/terms/index.html","products/home-car-glove-duo/index.html","track-order/index.html"]
LEGACY_HTML = "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><meta name=\"robots\" content=\"noindex,follow\"><link rel=\"canonical\" href=\"https://shop.askouresystems.com/\"><title>Page retired — Askoure Digital</title><meta http-equiv=\"refresh\" content=\"0;url=/\"></head><body style=\"font:16px/1.6 system-ui;padding:48px;max-width:760px;margin:auto\"><h1>Askoure Digital</h1><p>This page belongs to our previous physical-products website. Visit our AI tools and digital products catalog instead.</p><p><a href=\"/\">Go to the digital catalog</a> · <a href=\"/policies/contact/\">Contact support about historical orders</a></p></body></html>\n"
CONTACT_HTML = "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><meta name=\"robots\" content=\"index,follow\"><link rel=\"canonical\" href=\"https://shop.askouresystems.com/policies/contact/\"><title>Contact — Shop Askoure Systems</title><meta name=\"description\" content=\"Contact Shop Askoure Systems about AI tools, digital products and previous orders.\"></head><body style=\"font:17px/1.7 system-ui;background:#faf9ff;color:#17172f;max-width:750px;margin:7vh auto;padding:30px\"><a href=\"/\">← Shop Askoure Systems</a><h1>Contact Askoure Digital</h1><p>For digital product availability, subscription details or assistance with a historical order, email <a href=\"mailto:zongsm@gmail.com\">zongsm@gmail.com</a>.</p><p>Online checkout is not active on this website. We will confirm any available plan details individually.</p><p><a href=\"/#catalog\">Explore the digital catalog</a></p><script type=\"application/json\" id=\"site-config\">{\"checkout_enabled\":false,\"paypal_environment\":\"sandbox\",\"site_mode\":\"digital\"}</script></body></html>\n"
ROBOTS = "User-agent: *\nAllow: /\nDisallow: /api/\nDisallow: /checkout/\nSitemap: https://shop.askouresystems.com/sitemap.xml\n"
SITEMAP = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n<url><loc>https://shop.askouresystems.com/</loc></url>\n<url><loc>https://shop.askouresystems.com/policies/contact/</loc></url>\n</urlset>\n"
FEED = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<rss version=\"2.0\"><channel><title>Shop Askoure Systems — Digital Products</title><link>https://shop.askouresystems.com/</link><description>AI tools, subscriptions and digital products. No active checkout.</description></channel></rss>\n"
ASSETS = ["assets/store.css","assets/store.js","assets/vivid.css","assets/vivid.js"]

def build(root=ROOT, output=None):
    root = Path(root)
    output = Path(output or root).resolve()
    config = json.loads((root / "data/settings.json").read_text(encoding="utf-8"))
    assert config.get("site_mode") == "digital"
    assert config.get("checkout_enabled") is False
    assert config.get("paypal_environment") == "sandbox"
    assert config.get("launch_offer_enabled") is False
    html = (root / "static/digital-home.html").read_text(encoding="utf-8")
    assert '"checkout_enabled":false' in html
    assert '"paypal_environment":"sandbox"' in html
    assert 'href="/checkout/"' not in html
    assert 'href="/track-order/"' not in html
    generated = {
        "index.html": html,
        "robots.txt": ROBOTS,
        "sitemap.xml": SITEMAP,
        "feed.xml": FEED,
        "policies/contact/index.html": CONTACT_HTML,
    }
    # Source-of-truth digital catalog: three existing Gumroad-downloadable Askoure products.
    inventory = json.loads((root / "data/original-digital-products.json").read_text(encoding="utf-8"))
    products = inventory["products"]
    assert inventory["currency"] == "USD" and len(products) == 3
    for product in products:
        slug = product["slug"]
        assert slug in ("n8n-workflow-preflight-auditor", "llm-reliability-rescue-kit", "agent-runaway-guard-kit")
        assert product["status"] == "available"
        assert product["price_usd"] > 0
        assert product["buy_url"] == "https://mhamedasskoure.gumroad.com/l/" + slug
        path = "digital-products/" + slug + "/index.html"
        body = (root / "static/original-product-pages" / (slug + ".html")).read_text(encoding="utf-8")
        assert product["buy_url"] in body and "$" + str(product["price_usd"]) in body
        generated[path] = body
    # Include real digital product detail routes in search and the RSS product feed.
    extra_urls = "".join("<url><loc>https://shop.askouresystems.com/digital-products/" + product["slug"] + "/</loc></url>\n" for product in products)
    generated["sitemap.xml"] = SITEMAP.replace("</urlset>", extra_urls + "</urlset>")
    feed_items = "".join(
        "<item><title>" + product["title"] + "</title><link>https://shop.askouresystems.com/digital-products/"
        + product["slug"] + "/</link><description>Original downloadable digital toolkit: USD "
        + str(product["price_usd"]) + " once. Buy through Gumroad.</description></item>"
        for product in products
    )
    generated["feed.xml"] = FEED.replace("</channel>", feed_items + "</channel>")
    for path in LEGACY_ROUTES:
        generated[path] = LEGACY_HTML
    for path in ASSETS:
        generated[path] = (root / path).read_text(encoding="utf-8")
    for path, content in generated.items():
        target = output / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    receipt = {
        "version": "ASKOURE-DIGITAL-20261112-COMMERCE",
        "result": "BUILT_ORIGINAL_DIGITAL_KITS_GUMROAD_CHECKOUT",
        "verified_products": len(products),
        "unverified_products": 12,
        "checkout_environment": "sandbox",
        "payment_executed": False,
        "files": {path: hashlib.sha256(content.encode("utf-8")).hexdigest()
                  for path, content in sorted(generated.items())},
    }
    (output / "build-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": receipt["result"], "pages": len(generated)}))
    return receipt

if __name__ == "__main__":
    build()
