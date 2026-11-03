"""Incident regressions against actual publishable files, not documentation."""
import json
from pathlib import Path
import tempfile
import unittest
from html.parser import HTMLParser
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
from test_build_store import module

ROOT = Path(__file__).resolve().parents[1]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        self.urls.extend(v for k, v in attrs if k in ('href', 'src') and v)


class StoreQualityTests(unittest.TestCase):
    def test_published_files_equal_generator_including_worker_catalog(self):
        with tempfile.TemporaryDirectory() as temp:
            module.build(output=Path(temp))
            for path in Path(temp).rglob('*'):
                if path.is_file():
                    target = ROOT / path.relative_to(temp)
                    self.assertTrue(target.is_file(), str(target))
                    self.assertEqual(path.read_bytes(), target.read_bytes(), str(target))

    def test_every_public_route_is_paused_and_has_no_false_claims(self):
        forbidden = ('order confirmed', 'verified buyer', '4.9/5', 'paypal.me',
                     'submitorder', 'opencheckoutmodal', 'confirm order &',
                     'medical-grade', '3 years', 'countdown', 'priority air',
                     '7-12 business days', 'marcus b', 'david l', 'elena r')
        for path in ROOT.rglob('*.html'):
            html = path.read_text(encoding='utf-8')
            self.assertIn('ONLINE CHECKOUT CURRENTLY PAUSED', html, str(path))
            self.assertIn('"checkout_enabled":false', html, str(path))
            for marker in forbidden:
                self.assertNotIn(marker, html.lower(), str(path))
            self.assertNotIn('data-checkout-product=', html)
            self.assertNotIn('id="checkoutForm"', html)

    def test_fifteen_unqualified_slots_with_two_honest_previews(self):
        products = json.loads((ROOT/'data/catalog.json').read_text())['products']
        module.validate({'products': products}, json.loads((ROOT/'data/settings.json').read_text()))
        self.assertEqual(len(products), 15)
        self.assertEqual(len(list((ROOT/'products').glob('*/index.html'))), 15)
        self.assertFalse(any(p['verified_for_checkout'] for p in products))
        for p in products:
            for key in ('rating', 'review_count', 'compare_at_usd', 'eta_us_days',
                        'eta_uk_days', 'supplier_verified_at', 'cj_variant_id',
                        'shipping_us_usd', 'shipping_uk_usd'):
                self.assertIsNone(p.get(key), (p['id'], key))
        by_id = {p['id']: p for p in products}
        self.assertEqual(by_id['furoff']['price_usd'], 34.99)
        self.assertEqual(by_id['freshseal']['price_usd'], 24.99)
        self.assertTrue(by_id['freshseal']['specs']['contains_lithium'])

    def test_all_local_links_and_sitemap_routes_exist(self):
        for path in ROOT.rglob('*.html'):
            parser = Links(); parser.feed(path.read_text(encoding='utf-8'))
            for url in parser.urls:
                parsed = urlsplit(url)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                target = ROOT / parsed.path.lstrip('/')
                if target.is_dir(): target /= 'index.html'
                self.assertTrue(target.is_file(), (str(path), url))
        for loc in ET.parse(ROOT/'sitemap.xml').iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
            target = ROOT / urlsplit(loc.text).path.lstrip('/') / 'index.html'
            self.assertTrue(target.is_file(), loc.text)
        self.assertEqual(ET.parse(ROOT/'feed.xml').findall('./channel/item'), [])

    def test_paused_sandbox_configuration_and_no_legacy_script(self):
        settings = json.loads((ROOT/'data/settings.json').read_text())
        self.assertFalse(settings['checkout_enabled'])
        self.assertEqual(settings['paypal_environment'], 'sandbox')
        config = (ROOT/'workers/order-gateway/wrangler.toml').read_text()
        self.assertIn('CHECKOUT_ENABLED = "false"', config)
        self.assertIn('PAYPAL_ENV = "sandbox"', config)
        script = (ROOT/'assets/store.js').read_text(encoding='utf-8')
        for marker in ('submitOrder', 'paypal.me', "fetch('/api/orders'", 'Math.random', 'localStorage'):
            self.assertNotIn(marker, script)

    def test_payment_pages_have_safe_text_without_javascript(self):
        for route in ('checkout', 'checkout/return', 'checkout/cancel'):
            html = (ROOT/route/'index.html').read_text(encoding='utf-8')
            self.assertIn('Checkout is paused.', html)
            self.assertIn('does not confirm an order', html)

    def test_unsupported_claim_fields_rejected(self):
        catalog = json.loads((ROOT/'data/catalog.json').read_text())
        settings = json.loads((ROOT/'data/settings.json').read_text())
        for key, value in [('rating', 4.9), ('review_count', 10), ('countdown', 30), ('savings_pct', 42)]:
            with self.subTest(key=key):
                product = catalog['products'][0]; product[key] = value
                with self.assertRaises(ValueError): module.validate(catalog, settings)
                product[key] = None
