"""Nonbinding numeric prices must never become checkout or merchant prices."""
import copy
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET
from test_build_store import module
import test_build_store as build_tests

ROOT = Path(__file__).resolve().parents[1]
# Exact owner-supplied proposals, independently asserted rather than read back
# from the catalog under test. These are not supplier qualification evidence.
TARGETS = {
    'ice-tray':29.99, 'fruit-colander':54.99, 'faucet-caddy':39.99,
    'garlic-press':34.99, '9hole-hanger':24.99, 'cable-organizer':39.99,
    'folding-hanger':34.99, 'foldable-tote':29.99, 'furoff':34.99,
    'drain-snake':29.99, 'microfiber-cloth':29.99, 'bottle-brush':29.99,
    'mini-mop':39.99,
}


class PricingVisibilityTests(unittest.TestCase):
    def setUp(self):
        self.catalog = json.loads((ROOT/'data/catalog.json').read_text())
        self.settings = json.loads((ROOT/'data/settings.json').read_text())

    def test_exact_proposals_on_every_home_category_card_and_detail(self):
        home = (ROOT/'index.html').read_text(encoding='utf-8')
        self.assertEqual(home.count('class="target-price-amount"'),13)
        for p in self.catalog['products']:
            detail = (ROOT/'products'/p['slug']/'index.html').read_text(encoding='utf-8')
            self.assertFalse(p['verified_for_checkout'])
            self.assertIsNone(p['price_usd'])
            self.assertIn('noindex,follow',detail)
            if p['id'] not in TARGETS:
                self.assertTrue(p['visual_hold'])
                self.assertIsNone(p['target_launch_price_usd'])
                self.assertEqual(p['pricing_status'],'NOT_EVALUATED')
                self.assertNotIn('target-price-amount',detail)
                self.assertNotRegex(detail,r'\$\d')
                continue
            self.assertEqual(p['target_launch_price_usd'],TARGETS[p['id']])
            self.assertEqual(p['pricing_status'],'NONBINDING_PREVIEW_TARGET')
            amount = f'${TARGETS[p["id"]]:.2f} <span>USD</span>'
            for html in (home,(ROOT/'categories'/p['category']/'index.html').read_text(encoding='utf-8')):
                card = re.search(r'<article class="product-tile" data-product-id="'+p['id']+r'".*?</article>',html).group()
                self.assertIn(amount,card)
                self.assertIn('Planned launch price',card)
                self.assertIn('Not available to order',card)
                self.assertIn('Prices shown are proposed launch targets, not offers.',html)
            self.assertIn(amount,detail)
            self.assertIn('Provisional launch target — not a payable price',detail)
            self.assertIn('Exact variant, stock, US/UK shipping, tax and import costs await verification.',detail)

    def test_invalid_missing_and_inconsistent_targets_fail_closed(self):
        for value in (None,True,False,'29.99',0,-1,29.999,float('inf'),float('nan')):
            broken=copy.deepcopy(self.catalog)
            broken['products'][0]['target_launch_price_usd']=value
            with self.subTest(value=value),self.assertRaises(ValueError):
                module.validate(broken,self.settings)
        for key in ('target_launch_price_usd','pricing_status'):
            broken=copy.deepcopy(self.catalog);del broken['products'][0][key]
            with self.subTest(missing=key),self.assertRaises(ValueError):
                module.validate(broken,self.settings)
        for hold in (False,True):
            broken=copy.deepcopy(self.catalog)
            p=next(p for p in broken['products'] if bool(p['visual_hold'])==hold)
            p['pricing_status']='NONBINDING_PREVIEW_TARGET' if hold else 'NOT_EVALUATED'
            with self.assertRaises(ValueError):module.validate(broken,self.settings)
        broken=copy.deepcopy(self.catalog)
        next(p for p in broken['products'] if p['visual_hold'])['target_launch_price_usd']=29.99
        with self.assertRaises(ValueError):module.validate(broken,self.settings)

    def test_targets_cannot_qualify_or_leak_into_commerce(self):
        broken=copy.deepcopy(self.catalog);broken['products'][0]['verified_for_checkout']=True
        with self.assertRaises(ValueError):module.validate(broken,self.settings)
        settings=dict(self.settings,checkout_enabled=True)
        with self.assertRaises(ValueError):module.validate(self.catalog,settings)
        for name in json.loads((ROOT/'build-receipt.json').read_text())['files']:
            if not name.endswith('.html'):continue
            html=(ROOT/name).read_text(encoding='utf-8')
            self.assertNotIn('data-add-cart=',html)
            self.assertNotIn('application/ld+json',html)
            self.assertNotIn('"offers"',html)
            config=json.loads(re.search(r'id="store-config">(.*?)</script>',html).group(1))
            self.assertFalse(config['checkout_enabled'])
            self.assertEqual(config['catalog'],[])
            self.assertNotIn('target_launch_price',json.dumps(config))
        self.assertEqual(ET.parse(ROOT/'feed.xml').findall('./channel/item'),[])
        worker=(ROOT/'workers/order-gateway/catalog.generated.json').read_text()
        self.assertNotIn('target_launch_price_usd',worker)
        self.assertNotIn('NONBINDING_PREVIEW_TARGET',worker)

    def test_future_worker_generation_also_excludes_targets(self):
        fixture=build_tests.BuildTests();fixture.setUp();p=fixture.verified()
        # An independent real price must win over the preview in every payment surface.
        p['target_launch_price_usd']=99.99
        fixture.settings['checkout_enabled']=True
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'source';out=Path(temp)/'out'
            for directory in ('data','assets','static'):shutil.copytree(ROOT/directory,root/directory)
            (root/'data/catalog.json').write_text(json.dumps(fixture.catalog))
            (root/'data/settings.json').write_text(json.dumps(fixture.settings))
            module.build(root,out)
            worker=json.loads((out/'workers/order-gateway/catalog.generated.json').read_text())
            self.assertNotIn('target_launch_price_usd',json.dumps(worker))
            html=(out/'products'/p['slug']/'index.html').read_text(encoding='utf-8')
            config=json.loads(re.search(r'id="store-config">(.*?)</script>',html).group(1))
            self.assertEqual(config['catalog'][0]['price_usd'],34.99)
            self.assertNotIn('target_launch_price_usd',json.dumps(config))
            self.assertEqual(ET.parse(out/'feed.xml').find('./channel/item/{http://base.google.com/ns/1.0}price').text,'34.99 USD')
            self.assertNotIn('$99.99',html)
