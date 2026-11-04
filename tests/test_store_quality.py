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
    def test_homepage_real_photo_cards_and_product_specific_provenance(self):
        import hashlib
        products = json.loads((ROOT/'data/catalog.json').read_text())['products']
        media = {i['file']: i for i in json.loads((ROOT/'data/image-provenance.json').read_text())['images']}
        home = (ROOT/'index.html').read_text(encoding='utf-8')
        visible = [p for p in products if not p['visual_hold']]
        self.assertGreaterEqual(len(visible), 10)
        self.assertEqual(home.count('class="product-tile"'),len(visible))
        for marker in ('sourcing slot','Details coming','freshseal','data-checkout-product','data-gallery-video'):
            self.assertNotIn(marker,home.lower())
        for p in products:
            self.assertFalse(p['verified_for_checkout'])
            self.assertEqual(p['stock_status'],'unknown')
            self.assertNotIn('video',p)
            for key in ('cj_variant_id','supplier_cost_usd','net_margin_usd','shipping_us_usd','shipping_uk_usd','eta_us_days','eta_uk_days'):
                self.assertIsNone(p[key])
            detail = (ROOT/'products'/p['slug']/'index.html').read_text(encoding='utf-8')
            self.assertIn('noindex,follow',detail)
            self.assertIn('View sourcing reference',detail)
            self.assertIn(p['cj_product_url'],detail)
            if p['visual_hold']:
                self.assertNotIn('data-product-id="'+p['id']+'"',home)
                self.assertEqual(p['images'],[])
                continue
            self.assertIn('data-product-id="'+p['id']+'"',home)
            self.assertIn('/products/'+p['slug']+'/',home)
            self.assertTrue(p['images'])
            for image in p['images']:
                record=media[image]; raw=(ROOT/image.lstrip('/')).read_bytes()
                self.assertEqual(record['product_id'],p['id'])
                self.assertEqual(record['listing_url'],p['cj_product_url'])
                self.assertEqual(record['sha256'],hashlib.sha256(raw).hexdigest())
                self.assertEqual(raw[:4],b'RIFF'); self.assertEqual(raw[8:12],b'WEBP')
                self.assertLessEqual(len(raw),250*1024)
                self.assertGreaterEqual(min(record['width'],record['height']),250)
                self.assertIn(image,detail)

    def test_visible_product_missing_photo_or_mismatched_provenance_fails_closed(self):
        import copy
        catalog=json.loads((ROOT/'data/catalog.json').read_text())
        settings=json.loads((ROOT/'data/settings.json').read_text())
        broken=copy.deepcopy(catalog);broken['products'][0]['images']=[]
        with self.assertRaises(ValueError):module.validate(broken,settings)
        broken=copy.deepcopy(catalog);broken['products'][0]['images']=catalog['products'][1]['images']
        with self.assertRaises(ValueError):module.validate(broken,settings)

    def test_publishable_files_equal_generator(self):
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
        for path in (h for h in ROOT.rglob('*.html') if not any(part in {'node_modules','.wrangler','receipts','.git'} for part in h.relative_to(ROOT).parts)):
            html = path.read_text(encoding='utf-8')
            self.assertIn('Product previews · Ordering unavailable.', html, str(path))
            self.assertIn('"checkout_enabled":false', html, str(path))
            for marker in forbidden:
                self.assertNotIn(marker, html.lower(), str(path))
            self.assertNotIn('data-checkout-product=', html)
            self.assertNotIn('id="checkoutForm"', html)

    def test_fifteen_research_candidates_thirteen_photographed_previews(self):
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
        self.assertIsNone(by_id['furoff']['price_usd'])
        self.assertNotIn('freshseal',by_id)
        self.assertEqual(sum(bool(p['images']) for p in products),13)
        self.assertEqual(sum(p['visual_hold'] for p in products),2)
        for p in products:
            if p['id'] != 'furoff': self.assertIsNone(p['price_usd'])

    def test_all_local_links_and_sitemap_routes_exist(self):
        for path in (h for h in ROOT.rglob('*.html') if not any(part in {'node_modules','.wrangler','receipts','.git'} for part in h.relative_to(ROOT).parts)):
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

    def test_catalog_remains_paused_and_only_launch_offer_uses_live_checkout(self):
        settings = json.loads((ROOT/'data/settings.json').read_text())
        self.assertFalse(settings['checkout_enabled'])
        self.assertEqual(settings['paypal_environment'], 'live')
        self.assertTrue(settings['launch_offer_enabled'])
        config = (ROOT/'workers/order-gateway/wrangler.toml').read_text()
        self.assertIn('CHECKOUT_ENABLED = "false"', config)
        self.assertIn('PAYPAL_ENV = "sandbox"', config)
        script = (ROOT/'assets/store.js').read_text(encoding='utf-8')
        for marker in ('submitOrder', 'paypal.me', "fetch('/api/orders'", 'Math.random', 'localStorage'):
            self.assertNotIn(marker, script)

    def test_payment_pages_have_safe_text_without_javascript(self):
        for route in ('checkout', 'checkout/return', 'checkout/cancel'):
            html = (ROOT/route/'index.html').read_text(encoding='utf-8')
            if route == 'checkout':
                self.assertIn('general cart has no orderable products',html)
                self.assertIn('dedicated Home + Car glove duo',html)
            else:
                self.assertIn('Payment is pending verification',html)
                self.assertIn('does not confirm an order',html)

    def test_unsupported_claim_fields_rejected(self):
        catalog = json.loads((ROOT/'data/catalog.json').read_text())
        settings = json.loads((ROOT/'data/settings.json').read_text())
        for key, value in [('rating', 4.9), ('review_count', 10), ('countdown', 30), ('savings_pct', 42)]:
            with self.subTest(key=key):
                product = catalog['products'][0]; product[key] = value
                with self.assertRaises(ValueError): module.validate(catalog, settings)
                product[key] = None
