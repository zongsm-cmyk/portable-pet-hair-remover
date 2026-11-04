"""Acceptance regressions: no false prices; explicit disabled purchase; real gates."""
import copy
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from unittest.mock import patch
from test_build_store import module
import test_build_store as build_tests
ROOT=Path(__file__).resolve().parents[1]

class PricingVisibilityTests(unittest.TestCase):
    def setUp(self):
        self.catalog=json.loads((ROOT/'data/catalog.json').read_text())
        self.settings=json.loads((ROOT/'data/settings.json').read_text())

    def test_all_fifteen_detail_buttons_and_no_prices(self):
        for p in self.catalog['products']:
            html=(ROOT/'products'/p['slug']/'index.html').read_text(encoding='utf-8')
            self.assertFalse(p['verified_for_checkout'])
            self.assertIsNone(p['price_usd']);self.assertIsNone(p['target_launch_price_usd'])
            self.assertEqual(p['pricing_status'],'PRICE_BEING_VERIFIED')
            self.assertIn('Price being verified',html);self.assertNotRegex(html,r'\$\d')
            self.assertEqual(html.count('>Buy now</button>'),1)
            self.assertIn('disabled aria-describedby="ordering-unavailable-'+p['id']+'"',html)
            self.assertIn('id="ordering-unavailable-'+p['id']+'"',html)
            self.assertIn('Ordering is currently unavailable: product inventory, shipping and checkout not verified',html)
            self.assertIn('>Ask about availability</a>',html)
            if p['visual_hold']:
                self.assertIn('Additional product photos under verification',html)
            else:
                self.assertNotIn('Additional product photos under verification',html)
            self.assertIn('noindex,follow',html)
        home=(ROOT/'index.html').read_text(encoding='utf-8')
        sales=re.search(r'<section class="collection sales-collection".*?</section>',home).group()
        self.assertNotIn('product-tile',sales)
        self.assertIn('Shop the Home + Car Pet Hair Glove Duo',sales)
        self.assertIn('hero-campaign',home)
        self.assertIn('class="hero-cover"',home)
        self.assertIn('category-shade',home)
        self.assertIn('story-section',home)
        self.assertIn('Price under verification',home)

    def test_retired_proposals_rejected_and_never_in_commerce(self):
        for value in (29.99,True,'29.99',0,-1,float('nan')):
            c=copy.deepcopy(self.catalog);c['products'][0]['target_launch_price_usd']=value
            with self.subTest(value=value),self.assertRaises(ValueError):module.validate(c,self.settings)
        for name in json.loads((ROOT/'build-receipt.json').read_text())['files']:
            if not name.endswith('.html'):continue
            html=(ROOT/name).read_text(encoding='utf-8')
            self.assertNotIn('data-add-cart=',html);self.assertNotIn('target-price-amount',html)
            self.assertNotIn('"offers"',html)
            self.assertNotRegex(html.replace('$10.99',''),r'\$\d')
            config=json.loads(re.search(r'id="store-config">(.*?)</script>',html).group(1))
            self.assertFalse(config['checkout_enabled']);self.assertEqual(config['catalog'],[])
        self.assertNotIn('target_launch_price_usd',(ROOT/'workers/order-gateway/catalog.generated.json').read_text())

    def test_distinct_reviewed_photo_count(self):
        p={'images':['a','b','c','d']}
        rows={key:dict(source_sha256=key,sha256=key,original_url='https://cf.cjdropshipping.com/'+key,
            subject_verified=True,variant_verified=True,supplier_authorized=True,distinct_photo_verified=True,
            visual_method='Contact sheet',rights_evidence='CJ exact product usage',width=800,height=800) for key in p['images']}
        self.assertEqual(module.qualified_photo_count(p,rows),4)
        for flag in ('subject_verified','variant_verified','supplier_authorized','distinct_photo_verified'):
            broken=copy.deepcopy(rows);broken['d'][flag]=False
            self.assertEqual(module.qualified_photo_count(p,broken),3)
        for field in ('source_sha256','sha256','original_url'):
            broken=copy.deepcopy(rows);broken['d'][field]=broken['c'][field]
            self.assertEqual(module.qualified_photo_count(p,broken),3)
        actual={r['file']:r for r in json.loads((ROOT/'data/image-provenance.json').read_text())['images']}
        for p in self.catalog['products']:self.assertLess(module.qualified_photo_count(p,actual),4)

    def test_market_supplier_profit_and_sandbox_required(self):
        fixture=build_tests.BuildTests();fixture.setUp();p=fixture.verified();self.addCleanup(fixture.doCleanups)
        module.validate(fixture.catalog,fixture.settings)
        e=p['qualification_evidence']
        for key in ('supplier_availability','supplier_qc','silent_demo_15s','problem_solved','checkout_sandbox'):
            saved=e.pop(key)
            with self.subTest(key=key),self.assertRaises(ValueError):module.validate(fixture.catalog,fixture.settings)
            e[key]=saved
        for country in ('US','GB'):
            market=e['markets'][country]
            for key in ('customs_usd','taxes_usd','payment_fees_usd','refund_reserve_usd','landed_cost_reference','market_competitor'):
                saved=market[key];market[key]=None
                with self.subTest(country=country,key=key),self.assertRaises(ValueError):module.validate(fixture.catalog,fixture.settings)
                market[key]=saved
            market['market_competitor']['delivered_price_usd']=12
            with self.assertRaises(ValueError):module.validate(fixture.catalog,fixture.settings)
            market['market_competitor']['delivered_price_usd']=35
            market['refund_reserve_usd']=5
            with self.assertRaises(ValueError):module.validate(fixture.catalog,fixture.settings)
            market['refund_reserve_usd']=1
        e['processing_hours']=49
        with self.assertRaises(ValueError):module.validate(fixture.catalog,fixture.settings)
        e['processing_hours']=48
        with patch.object(module,'qualified_photo_count',return_value=3):
            with self.assertRaises(ValueError):module.validate(fixture.catalog,fixture.settings)

    def test_future_enabled_verified_product_has_actual_price_and_cart(self):
        fixture=build_tests.BuildTests();fixture.setUp();p=fixture.verified();self.addCleanup(fixture.doCleanups)
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
            self.assertIn('data-add-cart="furoff"',html)
            self.assertNotIn('>Buy now</button>',html)
            self.assertIn('$34.99 USD',html)
