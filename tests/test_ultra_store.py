"""Commercial regression tests for the verified-only VerveLiving ULTRA storefront."""
import importlib.util
import json
from html.parser import HTMLParser
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlparse
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("ultra",ROOT/"scripts/build_store.py")
ultra=importlib.util.module_from_spec(spec)
spec.loader.exec_module(ultra)

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[]
    def handle_starttag(self,tag,attrs):
        self.links.extend(v for k,v in attrs if k in ("href","src") and v)

class UltraTests(unittest.TestCase):
    def test_catalog_has_no_unqualified_products(self):
        self.assertEqual(json.loads((ROOT/"data/catalog.json").read_text())["products"],[])
        self.assertEqual(json.loads((ROOT/"workers/order-gateway/catalog.generated.json").read_text())["products"],[])
        active=json.loads((ROOT/"workers/order-gateway/launch-offer.json").read_text())
        self.assertFalse(active["verified_for_checkout"])
        self.assertEqual(active["id"],"home-car-glove-duo")
        self.assertEqual(active["cj_variant_id"],"CJYD233200812LO")
        self.assertEqual(active["warehouse_origin"],"US")

    def test_build_is_deterministic(self):
        with TemporaryDirectory() as tmp:
            receipt=ultra.build(output=tmp)
            self.assertEqual(receipt["verified_products"],0)
            self.assertEqual(receipt["unverified_products"],1)
            for name in receipt["files"]:
                self.assertEqual((Path(tmp)/name).read_bytes(),(ROOT/name).read_bytes(),name)

    def test_qualified_offer_client_readiness_uses_isolated_fixture_only(self):
        # Pure static build regression: no supplier purchase, PayPal call or deployment.
        from shutil import copy2
        from datetime import datetime, timezone
        with TemporaryDirectory() as tmp:
            root=Path(tmp)/"fixture"
            for p in ("data/settings.json", "data/catalog.json",
                      "workers/order-gateway/launch-offer.json",
                      "static/store.css", "static/store.js", "static/vivid.css",
                      "static/vivid.js"):
                source=ROOT/p
                dest=root/p
                dest.parent.mkdir(parents=True,exist_ok=True)
                copy2(source,dest)
            config_path=root/"data/settings.json"
            config=json.loads(config_path.read_text())
            config.update(checkout_enabled=True, paypal_environment="live",
                          launch_offer_enabled=True)
            config_path.write_text(json.dumps(config))
            offer_path=root/"workers/order-gateway/launch-offer.json"
            offer=json.loads(offer_path.read_text())
            offer.update(price_usd=35.99, verified_for_checkout=True,
                         stock_status="in_stock",
                         supplier_verified_at=datetime.now(timezone.utc).isoformat())
            offer_path.write_text(json.dumps(offer))
            out=root/"generated"
            receipt=ultra.build(root=root,output=out)
            self.assertEqual(receipt["verified_products"],1)
            page=(out/"products/home-car-glove-duo/index.html").read_text()
            self.assertIn('"checkout_enabled":true',page)
            self.assertIn('"paypal_environment":"live"',page)
            self.assertIn('"launch_offer_enabled":true',page)
            self.assertIn('data-launch-buy',page)
            # Disabled/underverified variant must never accidentally expose checkout.
            offer["verified_for_checkout"]=False
            offer_path.write_text(json.dumps(offer))
            blocked=ultra.build(root=root,output=out)
            self.assertEqual(blocked["verified_products"],0)
            paused=(out/"products/home-car-glove-duo/index.html").read_text()
            self.assertIn('"checkout_enabled":false',paused)
            self.assertIn('"launch_offer_enabled":false',paused)
            self.assertNotIn('data-launch-buy',paused)
            self.assertIn("Ordering is paused",paused)

    def test_unverified_offer_is_preview_only(self):
        html=(ROOT/"products/home-car-glove-duo/index.html").read_text()
        self.assertIn('id="home-car-glove-duo"',html)
        self.assertIn("Ordering is paused",html)
        self.assertIn('name="robots" content="noindex,follow"',html)
        self.assertNotIn('data-launch-buy',html)
        self.assertNotIn('application/ld+json',html)
        self.assertNotIn('"paypal_environment":"live"',html)
        self.assertIn('"launch_offer_enabled":false',html)
        self.assertNotIn('InStock',html)
        self.assertNotIn('$10.99',html)

    def test_editorial_home_displays_real_photos_and_original_demos(self):
        home=(ROOT/"index.html").read_text()
        self.assertIn('id="picks"',home)
        self.assertEqual(home.count('class="product-card"'),10)
        self.assertEqual(home.count('class="real-product-photo"'),10)
        self.assertEqual(home.count('class="product-photo"'),10)
        self.assertEqual(home.count('<video'),6)
        self.assertIn("Original manufacturer demonstration",home)
        self.assertIn("LILLY BRUSH",home)
        self.assertIn("FURZAPPER",home)
        self.assertIn("KURGO",home)
        self.assertIn("not affiliate-tracked",home)
        self.assertIn('rel="sponsored noopener noreferrer"',home)
        self.assertIn('name="robots" content="index,follow"',home)
        self.assertNotIn("SHOP THE GLOVE DUO",home)
        self.assertNotIn("/assets/vivid.js",home)
        self.assertNotIn("data-launch-buy",home)
        self.assertNotIn('href="/checkout/"',home)
        self.assertNotIn('href="/track-order/"',home)
        self.assertIn('"checkout_enabled":false',home)
        self.assertIn('"paypal_environment":"sandbox"',home)

    def test_all_generated_internal_paths_exist(self):
        paths=json.loads((ROOT/"build-receipt.json").read_text())["files"]
        for path in paths:
            if not path.endswith(".html"):
                continue
            parser=Links()
            parser.feed((ROOT/path).read_text())
            for u in parser.links:
                if not u.startswith("/") or u.startswith("//"): continue
                route=u.split("#")[0].split("?")[0]
                if not route:continue
                target=ROOT/route.lstrip("/")
                if target.is_dir():target=target/"index.html"
                self.assertTrue(target.is_file(),f"{path}: {u}")

    def test_no_old_catalog_skus_or_dead_routes(self):
        for path in (ROOT/"products").rglob("index.html"):
            self.assertEqual(path.parent.name,"home-car-glove-duo",str(path))
        self.assertEqual([p.parent.name for p in (ROOT/"categories").rglob("index.html")],
                         ["smart-cleaning-tools"])
        feed=(ROOT/"feed.xml").read_text()
        self.assertNotIn("<item>",feed)
        self.assertNotIn("fruit-colander",feed)
        sitemap=(ROOT/"sitemap.xml").read_text()
        self.assertNotIn("/products/home-car-glove-duo/",sitemap)
        self.assertNotIn("/products/furoff-",sitemap)

    def test_sofa_help_article_is_original_indexed_content_not_sale(self):
        page=(ROOT/"guides/remove-pet-hair-from-sofa/index.html").read_text()
        self.assertIn("How to remove pet hair from a sofa",page)
        self.assertIn("Always check the upholstery care label first",page)
        self.assertIn('name="robots" content="index,follow"',page)
        self.assertNotIn('application/ld+json',page)
        self.assertNotIn('data-launch-buy',page)
        self.assertNotIn('schema.org/InStock',page)
        self.assertNotIn('$10.99',page)
        self.assertIn('/guides/remove-pet-hair-from-sofa/',(ROOT/"index.html").read_text())
        sitemap=(ROOT/"sitemap.xml").read_text()
        self.assertIn('/guides/remove-pet-hair-from-sofa/',sitemap)
        self.assertNotIn('/products/home-car-glove-duo/',sitemap)
        rec=json.loads((ROOT/"build-receipt.json").read_text())
        self.assertIn("guides/remove-pet-hair-from-sofa/index.html",rec["files"])

    def test_paused_header_never_promises_shopping(self):
        receipt=json.loads((ROOT/"build-receipt.json").read_text())
        for path in receipt["files"]:
            if path.endswith(".html"):
                html=(ROOT/path).read_text()
                self.assertNotIn("Shop now <span>",html,path)
                self.assertIn('href="/guides/remove-pet-hair-from-car-seats/">Read guide <span>',html,path)
        self.assertFalse(json.loads((ROOT/"data/settings.json").read_text())["checkout_enabled"])

    def test_prelaunch_feedback_is_opt_in_no_checkout_or_marketing_enrollment(self):
        for path in ("index.html",
                     "guides/remove-pet-hair-from-car-seats/index.html",
                     "guides/remove-pet-hair-from-sofa/index.html"):
            html=(ROOT/path).read_text()
            self.assertIn("What is the hardest place to remove pet hair?", html, path)
            self.assertIn("not an order, preorder or marketing subscription", html, path)
            self.assertIn("mailto:zongsm+verveliving@gmail.com?subject=VerveLiving%20pet%20hair%20cleaning%20problem", html, path)
            self.assertNotIn('data-launch-buy',html,path)

    def test_dog_car_door_guide_is_indexed_and_does_not_offer_unverified_product(self):
        html=(ROOT/"guides/protect-car-doors-from-dog-scratches/index.html").read_text()
        self.assertIn("How to protect car doors from dog scratches",html)
        self.assertIn("side-airbag",html)
        self.assertIn("What is the hardest place to remove pet hair?",html)
        self.assertIn('name="robots" content="index,follow"',html)
        self.assertNotIn('data-launch-buy',html)
        self.assertNotIn("schema.org/InStock",html)
        self.assertNotIn("Add to cart",html)
        self.assertIn("/guides/protect-car-doors-from-dog-scratches/",(ROOT/"index.html").read_text())
        self.assertIn("/guides/protect-car-doors-from-dog-scratches/",(ROOT/"sitemap.xml").read_text())
        self.assertIn("guides/protect-car-doors-from-dog-scratches/index.html",
                      json.loads((ROOT/"build-receipt.json").read_text())["files"])

    def test_payment_return_and_tracking_unchanged_contract(self):
        page=(ROOT/"checkout/return/index.html").read_text()
        self.assertIn('id="capture-status"',page)
        page=(ROOT/"track-order/index.html").read_text()
        self.assertIn('id="order-lookup"',page)
        self.assertIn('name="order_id"',page)
        self.assertIn('name="email"',page)
        script=(ROOT/"assets/store.js").read_text()
        self.assertIn("approvalDestination",script)
        self.assertIn("'/api/orders/create'",script)
        self.assertIn("'/api/orders/capture'",script)

if __name__=="__main__":
    unittest.main()
