"""Import the owner's approved exact-CJ galleries without replacing catalog research."""
from pathlib import Path
import hashlib
import json
from urllib.parse import urlparse
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PICKS = {
    'ice-tray': [1, 2, 3, 5], 'fruit-colander': [1, 2, 3, 4, 5],
    'faucet-caddy': [1, 2, 4, 5], 'garlic-press': [1, 2, 3, 4, 5],
    '9hole-hanger': [1, 2, 3, 4, 5], 'cable-organizer': [1, 2, 3, 4, 5],
    'folding-hanger': [1, 2, 3, 4, 5], 'foldable-tote': [1, 2, 3, 4, 5],
    'furoff': [1, 2, 3, 4], 'drain-snake': [1, 2, 3, 4, 5],
    'microfiber-cloth': [1, 2, 3, 4], 'bottle-brush': [1, 2, 3, 4, 5],
    'mini-mop': [1, 2, 3, 4, 5],
}


def main():
    cache = ROOT.parent/'cj_gallery_candidates_20261103'
    report = cache/'report.json'
    rows = {(r['id'], r['n']): r for r in json.loads(report.read_text(encoding='utf-8'))['results']}
    catalog = json.loads((ROOT/'data/catalog.json').read_text(encoding='utf-8'))
    manifest = json.loads((ROOT/'data/image-provenance.json').read_text(encoding='utf-8'))
    if any(p['verified_for_checkout'] for p in catalog['products']):
        raise ValueError('Preview media import cannot change qualified commercial products')
    assert {p['id'] for p in catalog['products'] if not p['visual_hold']} == set(PICKS)
    # Validate everything before writing any asset or catalog.
    pending, records, hashes, sources = {}, [], set(), set()
    for p in catalog['products']:
        if p['visual_hold']:
            assert p['images'] == []
            continue
        images = []
        for i, n in enumerate(PICKS[p['id']], 1):
            r = rows[p['id'], n]
            url = urlparse(r['url'])
            assert r['status'] == 'DECODED' and url.scheme == 'https'
            assert url.hostname in {'cf.cjdropshipping.com', 'oss-cf.cjdropshipping.com', 'cc-west-usa.oss-accelerate.aliyuncs.com'} and not url.username and not url.password
            source = cache/f"{p['id']}-{n:02}.source"
            webp = cache/f"{p['id']}-{n:02}.webp"
            original, optimized = source.read_bytes(), webp.read_bytes()
            assert hashlib.sha256(original).hexdigest() == r['original_sha256']
            assert hashlib.sha256(optimized).hexdigest() == r['webp_sha256']
            assert len(optimized) == r['webp_bytes'] and len(optimized) < 256000
            with Image.open(source) as im:
                im.load()
                assert list(im.size) == r['dimensions']
                source_format = im.format
            with Image.open(webp) as im:
                im.load()
                assert im.format == 'WEBP' and min(im.size) >= 250
                width, height = im.size
            assert r['original_sha256'] not in sources and r['webp_sha256'] not in hashes
            sources.add(r['original_sha256']); hashes.add(r['webp_sha256'])
            file = f"/assets/products/{p['slug']}-gallery-{i:02}.webp"
            images.append(file); pending[ROOT/file.lstrip('/')] = optimized
            records.append(dict(product_id=p['id'], cj_sku=p['cj_sku'], listing_url=p['cj_product_url'],
                file=file, original_url=r['url'], source_sha256=r['original_sha256'], sha256=r['webp_sha256'],
                source_format=source_format, source_dimensions=r['dimensions'], width=width, height=height,
                bytes=len(optimized), source_bytes=len(original), approved_source_number=n, source_group=r['group'],
                subject_verified=True, variant_verified=False, supplier_authorized=False, distinct_photo_verified=True,
                visual_method='Manager reviewed CJ exact-product contact sheets 1–4; owner approved individual picks 2026-11-03',
                validation='Original and optimized bytes independently SHA256 checked; both decoded; unique sources and optimized hashes',
                license='CJ supplier promotional usage conditional on marketing this specific product; no blanket license grant',
                usage='Only to illustrate this exact CJ product research preview; colors/options illustrative pending selected variant',
                rights_evidence=None, rights_reference='https://blog.cjdropshipping.com/detail/cj-drop-shipping-policy'))
        p['images'] = images
        p['visual_status'] = 'MATCHED_CJ_RESEARCH_GALLERY'
        p['photo_note'] = 'Colors shown for illustration; exact variant to be verified. Pictured accessories and quantities are not a confirmed offer.'
        if p['id'] == 'drain-snake':
            p['photo_note'] += ' Supplier photos show the 60cm option; the earlier 160cm shipping quote does not match this pictured option.'
    manifest['archived_images'] = manifest.get('archived_images', []) + [r for r in manifest['images'] if '-gallery-' not in r['file']]
    if 'acceptance_review' in manifest:
        manifest['previous_acceptance_review'] = manifest.pop('acceptance_review')
    manifest['gallery_review'] = dict(date='2026-11-03', available_cache_images=66, published_images=len(records),
        source='Manager exact CJ product-page downloads and approved contact-sheet picks',
        local_import='Both original source and optimized WEBP decoded and SHA256 verified',
        four_image_minimum_required=4, max_published_images_per_product=5,
        products=[dict(id=p['id'], local_source_matched_photo_count=len(p['images']),
                       four_image_minimum_met=len(p['images']) >= 4, sellable=False) for p in catalog['products']])
    manifest.update(images=records, canonical_media='CJ_MULTIPHOTO_20261103',
        gallery_report_sha256=hashlib.sha256(report.read_bytes()).hexdigest(),
        media_rebuild='Catalog galleries are canonical. Use import_cj_galleries.py with the verified original cache; legacy importer must not replace them.')
    for target, raw in pending.items():
        target.write_bytes(raw)
    for name, data in [('catalog', catalog), ('image-provenance', manifest)]:
        (ROOT/f'data/{name}.json').write_text(json.dumps(data, indent=2, ensure_ascii=False)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps({'products': len(PICKS), 'photos': len(records), 'counts': {k: len(v) for k, v in PICKS.items()}}))


if __name__ == '__main__':
    main()
