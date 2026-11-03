"""Validate canonical published galleries, including real byte and source identity."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from PIL import Image
from test_build_store import module, ROOT


class CJGalleryTests(unittest.TestCase):
    def setUp(self):
        self.catalog = json.loads((ROOT/'data/catalog.json').read_text(encoding='utf-8'))
        self.settings = json.loads((ROOT/'data/settings.json').read_text())
        self.manifest = json.loads((ROOT/'data/image-provenance.json').read_text(encoding='utf-8'))

    def test_approved_counts_exact_picks_and_decodable_unique_bytes(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('cj_import', ROOT/'scripts/import_cj_galleries.py')
        importer = importlib.util.module_from_spec(spec); spec.loader.exec_module(importer)
        media = {r['file']: r for r in self.manifest['images']}
        hashes, originals, urls = set(), set(), set()
        for p in self.catalog['products']:
            if p['visual_hold']:
                self.assertEqual(p['images'], [])
                continue
            self.assertEqual(len(p['images']), len(importer.PICKS[p['id']]))
            self.assertEqual([media[f]['approved_source_number'] for f in p['images']], importer.PICKS[p['id']])
            for f in p['images']:
                r = media[f]; path = ROOT/f.lstrip('/'); raw = path.read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), r['sha256'])
                self.assertLess(len(raw), 256000)
                with Image.open(path) as image:
                    image.load(); self.assertEqual(image.format, 'WEBP')
                    self.assertEqual(image.size, (r['width'], r['height']))
                self.assertNotIn(r['sha256'], hashes); hashes.add(r['sha256'])
                self.assertNotIn(r['source_sha256'], originals); originals.add(r['source_sha256'])
                self.assertNotIn(r['original_url'], urls); urls.add(r['original_url'])
        self.assertEqual(len(hashes), 61)

    def test_visible_counts_below_four_above_five_and_copied_assets_rejected(self):
        for count in (0, 1, 2, 3, 6):
            c = copy.deepcopy(self.catalog)
            c['products'][0]['images'] = (c['products'][0]['images']*2)[:count]
            with self.subTest(count=count), self.assertRaises(ValueError):
                module.validate(c, self.settings)
        c = copy.deepcopy(self.catalog); c['products'][0]['images'][-1] = c['products'][0]['images'][0]
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            module.validate(c, self.settings)

    def test_missing_provenance_duplicate_source_and_invalid_webp_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for directory in ('assets', 'data'):
                shutil.copytree(ROOT/directory, root/directory)
            path = root/'data/image-provenance.json'
            for key, value in [('original_url', self.manifest['images'][0]['original_url']),
                               ('source_sha256', self.manifest['images'][0]['source_sha256']),
                               ('original_url', 'https://amazon.com/unrelated.jpg')]:
                bad = copy.deepcopy(self.manifest); bad['images'][1][key] = value
                path.write_text(json.dumps(bad), encoding='utf-8')
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    module.validate(self.catalog, self.settings, root)
            bad = copy.deepcopy(self.manifest); bad['images'].pop(0)
            path.write_text(json.dumps(bad), encoding='utf-8')
            with self.assertRaises(ValueError): module.validate(self.catalog, self.settings, root)
            bad = copy.deepcopy(self.manifest); row = bad['images'][0]
            raw = b'not an actual webp'
            (root/row['file'].lstrip('/')).write_bytes(raw)
            row.update(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
            path.write_text(json.dumps(bad), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'WEBP'): module.validate(self.catalog, self.settings, root)
