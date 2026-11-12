"""Digital-only storefront rollout contract and deterministic build verification."""
from pathlib import Path
import importlib.util
import json
import re
from tempfile import TemporaryDirectory
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("storefront", ROOT/"scripts/build_store.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class DigitalStoreTests(unittest.TestCase):
    def test_settings_keep_checkout_disabled(self):
        config=json.loads((ROOT/"data/settings.json").read_text(encoding="utf-8"))
        self.assertEqual(config["site_mode"],"digital")
        self.assertFalse(config["checkout_enabled"])
        self.assertFalse(config["launch_offer_enabled"])
        self.assertEqual(config["paypal_environment"],"sandbox")
    def test_home_is_digital_and_interactive_without_false_checkout(self):
        home=(ROOT/"index.html").read_text(encoding="utf-8")
        for token in ("Askoure Digital","ChatGPT","Canva","Claude","Midjourney","ElevenLabs","Cursor","const products=[","id=\"searchInput\"","id=\"langBtn\"","Request availability"):
            self.assertIn(token,home)
        self.assertIn('"checkout_enabled":false',home)
        self.assertNotIn('href="/checkout/"',home)
        self.assertNotIn("SHOP THE GLOVE DUO",home)
    def test_generator_matches_all_committed_pages(self):
        with TemporaryDirectory() as folder:
            receipt=module.build(output=folder)
            self.assertEqual(receipt["result"],"BUILT_ORIGINAL_DIGITAL_KITS_GUMROAD_CHECKOUT")
            self.assertEqual(receipt["verified_products"],3)
            for path in receipt["files"]:
                self.assertEqual((Path(folder)/path).read_bytes(),(ROOT/path).read_bytes(),path)
            self.assertEqual((Path(folder)/"build-receipt.json").read_bytes(),(ROOT/"build-receipt.json").read_bytes())
    def test_real_original_products_can_be_bought_separately(self):
        inventory=json.loads((ROOT/"data/original-digital-products.json").read_text(encoding="utf-8"))
        offerings=inventory["products"]
        self.assertEqual(inventory["currency"],"USD")
        self.assertEqual(len(offerings),3)
        self.assertEqual(sorted(p["price_usd"] for p in offerings),[9,19,24])
        homepage=(ROOT/"index.html").read_text(encoding="utf-8")
        self.assertIn('id="original-products"',homepage)
        self.assertEqual(homepage.count('class="own-card '),3)
        self.assertEqual(homepage.count("stock:'out_of_stock'"),12)
        for item in offerings:
            self.assertEqual(item["status"],"available")
            self.assertEqual(item["buy_url"],"https://mhamedasskoure.gumroad.com/l/"+item["slug"])
            detail=(ROOT/"digital-products"/item["slug"]/"index.html").read_text(encoding="utf-8")
            self.assertIn(item["buy_url"],detail)
            self.assertIn("$"+str(item["price_usd"]),detail)
            self.assertIn(item["buy_url"],homepage)
            self.assertIn("https://shop.askouresystems.com/digital-products/"+item["slug"]+"/",(ROOT/"sitemap.xml").read_text(encoding="utf-8"))

    def test_previous_store_routes_are_retired_not_live_products(self):
        paths=["products/home-car-glove-duo/index.html","cart/index.html","checkout/index.html","track-order/index.html","guides/remove-pet-hair-from-sofa/index.html"]
        for path in paths:
            content=(ROOT/path).read_text(encoding="utf-8")
            self.assertIn('noindex,follow',content)
            self.assertIn('AI tools and digital products catalog',content)
            self.assertNotIn('data-launch-buy',content)
        sitemap=(ROOT/"sitemap.xml").read_text(encoding="utf-8")
        self.assertNotIn("/products/home-car-glove-duo/",sitemap)
        self.assertIn("https://shop.askouresystems.com/",sitemap)
if __name__=="__main__": unittest.main()
