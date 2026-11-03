import copy
import hashlib
from datetime import datetime, timezone, timedelta
import importlib.util
import json
import shutil
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('build_store', ROOT/'scripts/build_store.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class BuildTests(unittest.TestCase):
    def setUp(self):
        self.catalog=json.loads((ROOT/'data/catalog.json').read_text(encoding='utf-8'))
        self.settings=json.loads((ROOT/'data/settings.json').read_text(encoding='utf-8'))

    def verified(self):
        p=next(p for p in self.catalog['products'] if p['id']=='furoff')
        p.update(price_usd=34.99,verified_for_checkout=True,cj_variant_id='TEST-VARIANT',warehouse_origin='CN',supplier_cost_usd=2,shipping_us_usd=6,shipping_uk_usd=5,net_margin_usd=25,eta_us_days='8-14 business days',eta_uk_days='8-14 business days',supplier_verified_at=datetime.now(timezone.utc).isoformat(),stock_status='in_stock',shipping_us_line='CJPacket Ordinary',shipping_uk_line='CJPacket Ordinary')
        p.update(customer_shipping_us_usd=0,customer_shipping_uk_usd=0)
        p['specs'].update(weight_g=200,contains_lithium=False,contains_liquid=False,medical=False)
        return p

    def test_icons_have_outline_fallback_without_css(self):
        for kind in ('kitchen','organize','cleaning'):
            svg=ET.fromstring(module.icon(kind))
            self.assertEqual(svg.attrib['width'],'36')
            self.assertEqual(svg.attrib['height'],'36')
            self.assertEqual(svg.attrib['fill'],'none')
            self.assertEqual(svg.attrib['stroke'],'currentColor')
            self.assertEqual(svg.attrib['viewBox'],'0 0 24 24')

    def test_matched_cj_photo_without_unverified_video_or_checkout(self):
        with tempfile.TemporaryDirectory() as temp:
            module.build(output=Path(temp))
            html=(Path(temp)/'products/furoff-pro-household-roller/index.html').read_text(encoding='utf-8')
            self.assertEqual(html.count('data-gallery-src='),2)
            self.assertNotIn('data-gallery-video=',html)
            self.assertIn('Buying unavailable',html)
            self.assertNotIn('data-checkout-product=',html)
            self.assertNotIn('freshseal',html.lower())

    def test_video_without_matching_sku_and_rights_is_rejected(self):
        fur=next(p for p in self.catalog['products'] if p['id']=='furoff')
        fur['video']={'url':'https://example.com/different.mp4','rights_verified':True,'matches_product_verified':True}
        with self.assertRaises(ValueError):module.validate(self.catalog,self.settings)

    def test_current_catalog_is_15_researched_candidates_five_per_category(self):
        products=module.validate(self.catalog,self.settings)
        self.assertEqual(len(products),15)
        self.assertFalse(any(p['verified_for_checkout'] for p in products))
        self.assertEqual(sum(bool(p.get('visual_hold')) for p in products),2)
        self.assertEqual(sum(bool(p['images']) for p in products),13)

    def test_flag_alone_cannot_enable_checkout(self):
        self.catalog['products'][0]['verified_for_checkout']=True
        with self.assertRaises(ValueError): module.validate(self.catalog,self.settings)

    def test_verified_requires_recent_real_shipping_and_safe_weight(self):
        p=self.verified()
        module.validate(self.catalog,self.settings)
        for key,value in [('shipping_us_usd',None),('eta_uk_days','15-20 business days'),('cj_product_url','https://cjdropshipping.com.evil.example/product'),('supplier_verified_at',(datetime.now(timezone.utc)-timedelta(days=8)).isoformat())]:
            old=p[key];p[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):module.validate(self.catalog,self.settings)
            p[key]=old
        p['specs']['contains_lithium']=True
        with self.assertRaises(ValueError):module.validate(self.catalog,self.settings)

    def test_unprofitable_verified_product_rejected(self):
        p=self.verified();p['supplier_cost_usd']=25
        with self.assertRaises(ValueError):module.validate(self.catalog,self.settings)

    def test_money_precision_rejected(self):
        p=self.verified();p['price_usd']=34.999
        with self.assertRaises(ValueError):module.validate(self.catalog,self.settings)

    def test_enabled_checkout_requires_https_and_verified_products(self):
        self.settings.update(checkout_enabled=True,api_base='https://api.example.com')
        with self.assertRaises(ValueError):module.validate(self.catalog,self.settings)
        self.verified();self.settings['api_base']='http://api.example.com'
        with self.assertRaises(ValueError):module.validate(self.catalog,self.settings)

    def test_slug_path_traversal_and_duplicate_ids_rejected(self):
        self.catalog['products'][0]['slug']='../../index'
        with self.assertRaises(ValueError):module.validate(self.catalog,self.settings)
        self.catalog['products'][0]['slug']='safe-slug'
        self.catalog['products'][0]['id']=self.catalog['products'][1]['id']
        with self.assertRaises(ValueError):module.validate(self.catalog,self.settings)

    def test_build_is_deterministic_and_drafts_excluded_from_feed_sitemap(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)
            first=module.build(output=out)
            second=module.build(output=out)
            self.assertEqual(first,second)
            self.assertEqual(len(list((out/'products').glob('*/index.html'))),15)
            self.assertEqual(len(list((out/'categories').glob('*/index.html'))),3)
            feed=ET.parse(out/'feed.xml')
            self.assertEqual(feed.findall('./channel/item'),[])
            self.assertNotIn('/products/',(out/'sitemap.xml').read_text())
            for path in (out/'products').glob('*/index.html'):
                self.assertIn('noindex,follow',path.read_text(encoding='utf-8'))
                if path.parent.name not in ('furoff-pro-household-roller','freshseal-pro'):
                    self.assertNotIn('application/ld+json',path.read_text(encoding='utf-8'))
            self.assertTrue((out/'checkout/return/index.html').is_file())
            self.assertTrue((out/'checkout/cancel/index.html').is_file())

    def test_lf_and_crlf_assets_publish_identical_bytes_and_versions(self):
        with tempfile.TemporaryDirectory() as temp:
            snapshots = []
            for label, newline in [('lf', '\n'), ('crlf', '\r\n')]:
                root = Path(temp)/label
                for directory in ('data', 'assets'):
                    shutil.copytree(ROOT/directory, root/directory)
                (root/'static').mkdir()
                for name in ('store.css', 'store.js'):
                    normalized = (ROOT/'static'/name).read_text(encoding='utf-8')
                    raw = normalized.replace('\n', newline).encode('utf-8')
                    (root/'static'/name).write_bytes(raw)
                    self.assertEqual(b'\r\n' in raw, label == 'crlf')
                out = Path(temp)/(label+'-output')
                receipt = module.build(root, out)
                for name in ('store.css', 'store.js'):
                    emitted = (out/'assets'/name).read_bytes()
                    expected = (ROOT/'static'/name).read_text(encoding='utf-8').encode('utf-8')
                    self.assertEqual(emitted, expected)
                    digest = hashlib.sha256(expected).hexdigest()
                    self.assertEqual(receipt['files']['assets/'+name], digest)
                    for page in out.rglob('*.html'):
                        self.assertIn('/assets/'+name+'?v='+digest[:12], page.read_text(encoding='utf-8'))
                snapshots.append({str(p.relative_to(out)): p.read_bytes()
                                  for p in out.rglob('*') if p.is_file()})
            # Includes every page, both assets and build-receipt.json byte for byte.
            self.assertEqual(snapshots[0], snapshots[1])

    def test_removed_products_and_payment_links_not_in_public_pages(self):
        with tempfile.TemporaryDirectory() as temp:
            module.build(output=Path(temp))
            html='\n'.join(path.read_text(encoding='utf-8') for path in Path(temp).rglob('*.html'))
            for marker in ['ThermaRelief','KneeFlex','paypal.me','Verified Buyer','Only 14 units','localStorage']:
                self.assertNotIn(marker,html)
            # Numeric nonbinding targets are now intentional; payment offers remain absent.
            self.assertIn('$34.99',html)
            self.assertIn('Provisional launch target — not a payable price',html)
            self.assertNotIn('"offers"',html)
            self.assertNotIn('data-checkout-product=',html)

    def test_script_and_html_escaping(self):
        attack='</script><img src=x onerror=alert(1)>'
        self.assertNotIn('<',module.json_script({'title':attack}))
        self.assertNotIn('<img',module.enc(attack))

    def test_changed_slot_slug_removes_only_stale_manifest_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'source';out=Path(temp)/'output'
            for directory in ['data','static','assets']:(root/directory).mkdir(parents=True,exist_ok=True)
            for name in ['store.css','store.js']:(root/'static'/name).write_text((ROOT/'static'/name).read_text(encoding='utf-8'),encoding='utf-8')
            for product in self.catalog['products']:
                for image in product['images']:
                    target=root/image.lstrip('/')
                    target.parent.mkdir(parents=True,exist_ok=True)
                    target.write_bytes((ROOT/image.lstrip('/')).read_bytes())
            (root/'data/image-provenance.json').write_bytes((ROOT/'data/image-provenance.json').read_bytes())
            (root/'data/catalog.json').write_text(json.dumps(self.catalog),encoding='utf-8')
            (root/'data/settings.json').write_text(json.dumps(self.settings),encoding='utf-8')
            module.build(root,out)
            old=out/'products'/self.catalog['products'][0]['slug']/'index.html'
            self.assertTrue(old.is_file())
            # Unlisted files and protected source/image paths must never be deleted.
            keep=out/'products/unmanaged/index.html';keep.parent.mkdir(parents=True);keep.write_text('keep')
            (out/'data').mkdir();(out/'data/catalog.json').write_text('keep source')
            (out/'assets/furoff-pro.jpg').write_text('keep image')
            receipt=json.loads((out/'build-receipt.json').read_text())
            receipt['files'].update({'data/catalog.json':'ignored','assets/furoff-pro.jpg':'ignored','../outside.txt':'ignored'})
            (out/'build-receipt.json').write_text(json.dumps(receipt))
            self.catalog['products'][0]['slug']='new-verified-sourcing-slot'
            (root/'data/image-provenance.json').write_bytes((ROOT/'data/image-provenance.json').read_bytes())
            (root/'data/catalog.json').write_text(json.dumps(self.catalog),encoding='utf-8')
            module.build(root,out)
            self.assertFalse(old.exists())
            self.assertTrue((out/'products/new-verified-sourcing-slot/index.html').is_file())
            self.assertEqual(keep.read_text(),'keep')
            self.assertEqual((out/'data/catalog.json').read_text(),'keep source')
            self.assertEqual((out/'assets/furoff-pro.jpg').read_text(),'keep image')

    def test_positive_feed_requires_global_checkout_and_contains_accurate_data(self):
        self.verified()
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'source';out=Path(temp)/'output'
            for directory in ['data','static','assets']:(root/directory).mkdir(parents=True,exist_ok=True)
            for name in ['store.css','store.js']:(root/'static'/name).write_text((ROOT/'static'/name).read_text(encoding='utf-8'),encoding='utf-8')
            for product in self.catalog['products']:
                for image in product['images']:
                    target=root/image.lstrip('/')
                    target.parent.mkdir(parents=True,exist_ok=True)
                    target.write_bytes((ROOT/image.lstrip('/')).read_bytes())
            (root/'data/image-provenance.json').write_bytes((ROOT/'data/image-provenance.json').read_bytes())
            (root/'data/catalog.json').write_text(json.dumps(self.catalog),encoding='utf-8')
            (root/'data/settings.json').write_text(json.dumps(self.settings),encoding='utf-8')
            module.build(root,out)
            self.assertFalse(ET.parse(out/'feed.xml').findall('./channel/item'))
            self.settings['checkout_enabled']=True
            (root/'data/settings.json').write_text(json.dumps(self.settings),encoding='utf-8')
            receipt=module.build(root,out)
            ns={'g':'http://base.google.com/ns/1.0'}
            item=ET.parse(out/'feed.xml').find('./channel/item')
            self.assertIsNotNone(item)
            self.assertEqual(item.find('g:price',ns).text,'34.99 USD')
            self.assertEqual(item.find('g:availability',ns).text,'in_stock')
            self.assertEqual(receipt['merchant_feed_items'],1)
            html=(out/'products/furoff-pro-household-roller/index.html').read_text(encoding='utf-8')
            self.assertIn('8-14 business days',html)
            self.assertIn('USD total for one item',html)
            self.assertIn('data-add-cart="furoff"',html)
            self.assertNotIn('contains_lithium',html)

if __name__=='__main__':unittest.main()
