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
        self.assertTrue(active["verified_for_checkout"])
        self.assertEqual(active["id"],"home-car-glove-duo")
        self.assertEqual(active["cj_variant_id"],"CJYD233200812LO")
        self.assertEqual(active["warehouse_origin"],"US")

    def test_build_is_deterministic(self):
        with TemporaryDirectory() as tmp:
            receipt=ultra.build(output=tmp)
            self.assertEqual(receipt["verified_products"],1)
            self.assertEqual(receipt["unverified_products"],0)
            for name in receipt["files"]:
                self.assertEqual((Path(tmp)/name).read_bytes(),(ROOT/name).read_bytes(),name)

    def test_live_offer_and_bundle_totals(self):
        html=(ROOT/"products/home-car-glove-duo/index.html").read_text()
        self.assertIn('id="home-car-glove-duo"',html)
        self.assertIn('data-launch-buy',html)
        self.assertIn('data-launch-phone',html)
        self.assertIn('data-launch-quantity',html)
        for qty,amount in (("1","$10.99"),("2","$21.98"),("3","$32.97")):
            self.assertIn('value="'+qty+'"',html)
            self.assertIn(amount,html)
        self.assertIn('"paypal_environment":"live"',html)
        self.assertIn('"launch_offer_enabled":true',html)
        self.assertIn('approvalDestination',(ROOT/"assets/store.js").read_text())

    def test_product_page_is_discoverable(self):
        home=(ROOT/"index.html").read_text()
        self.assertIn("/products/home-car-glove-duo/#home-car-glove-duo",home)
        self.assertIn("LOVE THE PET.",home)
        self.assertIn("LOSE THE FUR.",home)
        self.assertIn('data-scene="0"',home)
        self.assertIn('class="color-marquee"',home)
        self.assertIn('/assets/vivid.css?v=',home)
        self.assertIn('/assets/vivid.js?v=',home)
        self.assertIn('class="feature-grid"',home)
        self.assertNotIn("Ordering is paused",home)
        self.assertNotIn("Product previews",home)
        self.assertIn("Home + Car",home)
        self.assertIn("Paypal".lower(),home.lower())

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
        self.assertIn("home-car-glove-duo",feed)
        self.assertNotIn("fruit-colander",feed)
        sitemap=(ROOT/"sitemap.xml").read_text()
        self.assertIn("/products/home-car-glove-duo/",sitemap)
        self.assertNotIn("/products/furoff-",sitemap)

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
