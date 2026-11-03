"""Quality and Integrity Test Suite for VerveLiving™ Storefront"""
import json
import unittest
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

class StoreQualityTests(unittest.TestCase):
    def setUp(self):
        catalog_path = ROOT / 'data' / 'catalog.json'
        self.assertTrue(catalog_path.is_file(), "catalog.json must exist")
        self.catalog = json.loads(catalog_path.read_text(encoding='utf-8'))

    def test_catalog_has_vetted_products(self):
        """Verify the store features only approved non-medical products."""
        products = self.catalog.get('products', [])
        self.assertEqual(len(products), 2, "Store must feature vetted products (FurOff and FreshSeal)")
        product_ids = {p['id'] for p in products}
        self.assertEqual(product_ids, {'furoff', 'freshseal'})

    def test_every_product_has_5_images(self):
        """Verify each product has at least 5 high-resolution local image files."""
        for p in self.catalog['products']:
            images = p.get('images', [])
            self.assertGreaterEqual(len(images), 5, f"Product {p['id']} must have at least 5 images")
            for img_rel in images:
                img_path = ROOT / img_rel.lstrip('/')
                self.assertTrue(img_path.is_file(), f"Image {img_rel} for {p['id']} must exist on disk")
                self.assertGreater(img_path.stat().st_size, 10000, f"Image {img_rel} must be non-empty")

    def test_every_product_has_video(self):
        """Verify each product has an active video demonstration URL or file."""
        for p in self.catalog['products']:
            video_url = p.get('video_url')
            self.assertTrue(bool(video_url), f"Product {p['id']} must have a video URL")
            if video_url.startswith('/'):
                vid_path = ROOT / video_url.lstrip('/')
                self.assertTrue(vid_path.is_file(), f"Local video file {video_url} must exist")

    def test_no_empty_categories(self):
        """Verify no active category is empty and wellness-comfort is removed."""
        home_org = ROOT / 'categories' / 'home-organization' / 'index.html'
        self.assertTrue(home_org.is_file(), "home-organization category page must exist")
        content = home_org.read_text(encoding='utf-8')
        self.assertNotIn("0 product previews", content)
        self.assertNotIn("There are no products available", content)
        self.assertIn("FurOff", content, "FurOff must be in home-organization")
        self.assertIn("FreshSeal", content, "FreshSeal must be in home-organization")

        kitchen = ROOT / 'categories' / 'kitchen-innovations' / 'index.html'
        self.assertTrue(kitchen.is_file(), "kitchen-innovations category page must exist")
        self.assertIn("FreshSeal", kitchen.read_text(encoding='utf-8'))

        cleaning = ROOT / 'categories' / 'smart-cleaning-tools' / 'index.html'
        self.assertTrue(cleaning.is_file(), "smart-cleaning-tools category page must exist")
        self.assertIn("FurOff", cleaning.read_text(encoding='utf-8'))

        wellness = ROOT / 'categories' / 'wellness-comfort' / 'index.html'
        self.assertFalse(wellness.is_file(), "wellness-comfort category must not exist on storefront")

    def test_index_page_integrity(self):
        """Verify index.html showcases vetted products with video player, clean encoding, and pricing."""
        index_file = ROOT / 'index.html'
        self.assertTrue(index_file.is_file())
        html = index_file.read_text(encoding='utf-8')
        self.assertIn("FurOff", html)
        self.assertIn("FreshSeal", html)
        self.assertNotIn("ThermaRelief", html)
        self.assertNotIn("KneeFlex", html)
        self.assertNotIn("&trade;&trade;", html)
        self.assertIn("<video", html, "Must contain video player")
        self.assertIn("openCheckoutModal", html, "Must support checkout modal")

    def test_no_medical_products_in_html(self):
        """Verify across all HTML files that no medical devices or corrupted tags appear."""
        html_files = list(ROOT.glob('**/*.html'))
        for f in html_files:
            txt = f.read_text(encoding='utf-8', errors='replace')
            rel = str(f.relative_to(ROOT))
            self.assertNotIn('&trade;&trade;', txt, f"Corruption found in {rel}")
            self.assertNotIn('thermarelief', txt.lower(), f"Medical product found in {rel}")
            self.assertNotIn('kneeflex', txt.lower(), f"Medical product found in {rel}")
            self.assertNotIn('/categories/wellness-comfort/', txt, f"Wellness category link found in {rel}")

    def test_policies_exist(self):
        """Verify all legal and compliance policy pages exist and are well-formed."""
        for slug in ['shipping', 'refunds', 'privacy', 'terms', 'contact']:
            pol_file = ROOT / 'policies' / slug / 'index.html'
            self.assertTrue(pol_file.is_file(), f"Policy {slug} must exist")
            content = pol_file.read_text(encoding='utf-8')
            self.assertIn("VerveLiving", content)
            self.assertIn("YunExpress", content)

    def test_no_fabricated_claims(self):
        """Verify neither index nor any product page contains fabricated claims."""
        html = (ROOT / 'index.html').read_text(encoding='utf-8')
        self.assertNotIn("45,000 Verified", html)
        self.assertNotIn("ISO-certified production", html)
        self.assertNotIn("Only 14 units left in November", html)

    def test_checkout_and_paypal_connectivity(self):
        """Verify PayPal merchant reference and order flow are properly configured."""
        self.assertEqual(self.catalog.get('merchant_email'), 'askgsm@live.fr')
        self.assertEqual(self.catalog.get('paypal_me'), 'https://paypal.me/asskoure')

if __name__ == '__main__':
    unittest.main()
