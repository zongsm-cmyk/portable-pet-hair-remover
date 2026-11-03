import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from test_build_store import module, ROOT
import test_build_store as build_tests


class CommerceTests(unittest.TestCase):
    def test_all_thirteen_galleries_have_approved_canonical_photos(self):
        catalog=json.loads((ROOT/'data/catalog.json').read_text())
        media=json.loads((ROOT/'data/image-provenance.json').read_text())['images']
        self.assertEqual(len(media),61)
        for p in catalog['products']:
            if not p['visual_hold']:
                self.assertIn(len(p['images']),(4,5))
                self.assertEqual(p['images'],[f'/assets/products/{p["slug"]}-gallery-{n:02}.webp' for n in range(1,len(p['images'])+1)])
            self.assertIsNone(p['price_usd'])
        for record in media:
            self.assertTrue(record['original_url'].startswith('https://'))
            self.assertIn('license',record)

    def test_cart_and_lookup_are_discoverable_and_paused(self):
        for route in ('cart','checkout','track-order'):
            html=(ROOT/route/'index.html').read_text(encoding='utf-8')
            self.assertIn('href="/cart/"',html)
            self.assertIn('href="/track-order/"',html)
            self.assertNotIn('data-add-cart=',html)
            self.assertNotIn('Continue to PayPal',html)
        self.assertIn('id="order-lookup"',(ROOT/'track-order/index.html').read_text())

    def test_qualified_fixture_has_reusable_add_cart_but_preview_does_not(self):
        fixture=build_tests.BuildTests();fixture.setUp();fixture.verified();self.addCleanup(fixture.doCleanups)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'source'
            for directory in ('data','assets','static'):
                shutil.copytree(ROOT/directory,root/directory)
            (root/'data/catalog.json').write_text(json.dumps(fixture.catalog))
            module.build(root,Path(temp)/'output')
            home=(Path(temp)/'output/index.html').read_text(encoding='utf-8')
            self.assertEqual(home.count('data-add-cart='),0)
            self.assertIn('"checkout_enabled":false',home)
            detail=(Path(temp)/'output/products/furoff-pro-household-roller/index.html').read_text(encoding='utf-8')
            self.assertEqual(detail.count('data-add-cart='),0)
            self.assertIn('disabled aria-describedby=',detail)
            self.assertNotIn('data-checkout-product=',detail)

    def test_no_exception_for_unqualified_retail_price(self):
        catalog=json.loads((ROOT/'data/catalog.json').read_text())
        next(p for p in catalog['products'] if p['id']=='furoff')['price_usd']=34.99
        with self.assertRaises(ValueError):module.validate(catalog,json.loads((ROOT/'data/settings.json').read_text()))

    @unittest.skipUnless(importlib.util.find_spec('PIL'), 'Pillow is needed only for the optional media importer')
    def test_media_import_rejects_tampering_and_unrelated_source(self):
        from PIL import Image
        import hashlib
        spec=importlib.util.spec_from_file_location('media_import',ROOT/'scripts/import_research_media.py')
        media=importlib.util.module_from_spec(spec);spec.loader.exec_module(media)
        rows=[]
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)
            for identity in sorted(media.SECONDARY_IDS):
                raw=target/(identity+'.raw');photo=target/(identity+'.webp')
                original=Image.new('RGB',(300,300),'white');original.save(raw,format='PNG');original.save(photo,format='WEBP',quality=86,method=6)
                rows.append({'id':identity,'ok':True,'source_url':'https://cf.cjdropshipping.com/test.jpg','file':str(photo),'size':[300,300],'sha256':hashlib.sha256(photo.read_bytes()).hexdigest(),'bytes':photo.stat().st_size})
            receipt=target/'alternative_media_receipt.json'
            receipt.write_text(json.dumps(rows));self.assertEqual(len(media.secondary_media(target)),8)
            saved=rows[0]['source_url'];rows[0]['source_url']='https://unrelated.example/random.jpg'
            receipt.write_text(json.dumps(rows))
            with self.assertRaises(ValueError):media.secondary_media(target)
            rows[0]['source_url']=saved;rows[0]['sha256']='0'*64;receipt.write_text(json.dumps(rows))
            with self.assertRaises(ValueError):media.secondary_media(target)

    def test_manifest_is_unverified_and_covers_fifteen_real_candidates(self):
        manifest=json.loads((ROOT/'data/merchant-evidence.template.json').read_text())
        self.assertEqual(len(manifest['items']),15)
        self.assertTrue(all(item['status']=='UNVERIFIED' for item in manifest['items']))
        self.assertIsNone(manifest['record_template']['source']['variant_vid'])
        self.assertEqual({p['id'] for p in manifest['items']},{p['id'] for p in json.loads((ROOT/'data/catalog.json').read_text())['products']})
