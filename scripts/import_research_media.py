"""Import the owner's CJ research and exact-URL download cache; never qualify stock."""
from pathlib import Path
import hashlib
import json
import io
import re
from urllib.parse import urlparse
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]

SECONDARY_IDS = {'ice-tray','faucet-caddy','fruit-colander','garlic-press','9hole-hanger','furoff','mini-mop','bottle-brush'}

def secondary_media(cache):
    rows = json.loads((cache/'alternative_media_receipt.json').read_text(encoding='utf-8'))
    if len(rows) != 8 or {r['id'] for r in rows} != SECONDARY_IDS:
        raise ValueError('Require all eight exact matched secondary photographs')
    result = {}
    for r in rows:
        url = urlparse(r['source_url'])
        target = Path(r['file']).resolve()
        if r.get('ok') is not True or url.scheme != 'https' or url.hostname not in {'cf.cjdropshipping.com','oss-cf.cjdropshipping.com'} or url.username or url.password or not target.is_relative_to(cache.resolve()):
            raise ValueError('Invalid matched media source or cache path')
        raw = target.read_bytes()
        if hashlib.sha256(raw).hexdigest() != r['sha256'] or len(raw) != r['bytes']:
            raise ValueError('Secondary media hash/size mismatch')
        with Image.open(io.BytesIO(raw)) as im:
            im.load()
            expected = list(r['size'])
            scale = min(1, 900 / max(expected))
            expected = [round(d * scale) for d in expected]
            if im.format != 'WEBP' or list(im.size) != expected or min(im.size) < 250 or len(raw) > 256000:
                raise ValueError('Invalid secondary WEBP dimensions or format')
            r = dict(r, optimized_size=list(im.size))
        original_raw = target.with_suffix('.raw').read_bytes()
        with Image.open(io.BytesIO(original_raw)) as original:
            original.load()
            if original.format not in {'JPEG','PNG','WEBP'} or list(original.size) != r['size']:
                raise ValueError('Secondary source format/dimensions mismatch')
            optimized = ImageOps.exif_transpose(original).convert('RGB')
            optimized.thumbnail((900,900))
            buf = io.BytesIO(); optimized.save(buf,format='WEBP',quality=86,method=6)
            if buf.getvalue() != raw:
                raise ValueError('Secondary cache must exactly reproduce from original source')
            r.update(source_sha256=hashlib.sha256(original_raw).hexdigest(),source_format=original.format)
        result[r['id']] = (r, raw)
    return result

def main():
    manifest = ROOT/'data/image-provenance.json'
    if manifest.exists() and json.loads(manifest.read_text(encoding='utf-8')).get('canonical_media') == 'CJ_MULTIPHOTO_20261103':
        raise ValueError('Canonical CJ galleries preserved. Use import_cj_galleries.py; this legacy importer cannot replace final catalog media.')
    existing = ROOT/'data/catalog.json'
    if existing.exists() and any(p.get('verified_for_checkout') for p in json.loads(existing.read_text(encoding='utf-8'))['products']):
        raise ValueError('Research importer cannot overwrite qualified commercial records')
    research_path = ROOT.parent / 'VERVELIVING_CJ_15_CANDIDATES_20261103.json'
    cache = ROOT.parent / 'media_cache_cj'
    research = json.loads(research_path.read_text(encoding='utf-8'))
    for key in ('id','slug'):
        values = [p[key] for p in research['products']]
        if len(values)!=15 or len(set(values))!=15 or any(not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',v) for v in values):
            raise ValueError('Require 15 unique safe research identities')
    receipt = {r['id']: r for r in json.loads((cache/'media_receipt.json').read_text())}
    pictured = {p['id'] for p in research['products']} - {'cup-drainer','vacuum-hook'}
    if {identity for identity,r in receipt.items() if r['status']=='OK'} != pictured:
        raise ValueError('Require all 13 original matched photographs; never collapse a gallery on a partial cache')
    secondary = secondary_media(cache)  # Validate every source before changing any output.
    out = ROOT/'assets/products'
    out.mkdir(parents=True, exist_ok=True)
    records, provenance, pending = [], [], {}
    null_fields = 'price_usd compare_at_usd supplier_cost_usd shipping_us_usd shipping_uk_usd net_margin_usd cj_variant_id warehouse_origin eta_us_days eta_uk_days supplier_verified_at shipping_us_line shipping_uk_line customer_shipping_us_usd customer_shipping_uk_usd rating review_count'.split()
    for candidate in research['products']:
        p = {key: None for key in null_fields}
        p.update({key:candidate[key] for key in ('id','slug','title','category','cj_sku','cj_product_url','short_problem_solved','features')})
        if p['id'] == 'ice-tray':
            p.update(short_problem_solved='Release ice from a handheld cylindrical mould into a glass.',
                     features=['Handheld cylindrical ice mould', 'Press-release design shown in supplier photos'])
        p.update(images=[], specs={key:None for key in ('dimensions','weight_g','materials','contains_lithium','contains_liquid','medical')}, verified_for_checkout=False, stock_status='unknown', draft_slot=False,
                 visual_hold=True, visual_status='VISUAL_HOLD_NO_AUTHENTIC_IMAGE', source_status=candidate['source_status'])
        p.update(target_launch_price_usd=None, pricing_status='PRICE_BEING_VERIFIED', qualification_evidence=None)
        if p['id'] == 'drain-snake':
            p.update(title='Flexible Drain Cleaning Spring', source_status='VARIANT_MISMATCH_60CM_CATALOG_VS_160CM_SUPPLIER_QUOTE_UNRESOLVED')
        if p['id'] == 'fruit-colander':
            p['source_status']='OBSERVED_VARIANT_628G_EXCEEDS_500G_LIMIT_NOT_QUALIFIED'
        r = receipt[p['id']]
        if r['status'] == 'OK':
            url = urlparse(r['source'])
            if r['source'] != candidate['cj_primary_image_url'] or url.scheme != 'https' or url.hostname not in {'cf.cjdropshipping.com','oss-cf.cjdropshipping.com','cc-west-usa.oss-accelerate.aliyuncs.com'} or url.username or url.password:
                raise ValueError('Original photograph must match exact CJ source')
            raw = (cache/(p['slug']+'-source.raw')).read_bytes()
            cached_path = Path(r['target']).resolve()
            if not cached_path.is_relative_to(cache.resolve()):
                raise ValueError('Original cache path outside known directory')
            cached = cached_path.read_bytes()
            if hashlib.sha256(cached).hexdigest() != r['sha256']:
                raise ValueError('Original cache hash mismatch')
            with Image.open(io.BytesIO(raw)) as original:
                original.load()
                if original.format not in ('JPEG','PNG','WEBP') or min(original.size) < 250:
                    raise ValueError('Invalid original format or dimensions')
                source_format = original.format
                source_size = original.size
                im = ImageOps.exif_transpose(original).convert('RGB')
                im.thumbnail((900,900))
                buf = io.BytesIO(); im.save(buf,format='WEBP',quality=85,method=6)
                if buf.getvalue() != cached:
                    raise ValueError('Cached image must exactly reproduce from source')
            target = out/(p['slug']+'.webp')
            pending[target] = cached
            p.update(images=['/assets/products/'+target.name],visual_hold=False,visual_status='MATCHED_CJ_RESEARCH_PHOTO')
            provenance.append(dict(product_id=p['id'],cj_sku=p['cj_sku'],listing_url=p['cj_product_url'],file=p['images'][0],
                original_url=r['source'],source_sha256=hashlib.sha256(raw).hexdigest(),sha256=r['sha256'],
                source_format=source_format,source_dimensions=source_size,width=im.width,height=im.height,bytes=len(cached),
                validation='Decoded original magic and dimensions; exact reproducible WEBP; subject visually inspected by Codex',
                http_status='Cache downloader curl --fail reported success; no response headers retained; no fresh network verification',
                content_type='Original headers not retained; MIME inferred from decoded '+source_format,
                license='CJ product promotional usage only; no independent copyright license grant evidenced',
                usage='Only to promote this exact CJ product; no unrelated reuse',rights_reference='https://blog.cjdropshipping.com/detail/cj-drop-shipping-policy'))
            if p['id'] in secondary:
                extra, photo = secondary[p['id']]
                target2 = out/(p['slug']+'-02.webp')
                pending[target2] = photo
                p['images'].append('/assets/products/'+target2.name)
                provenance.append(dict(product_id=p['id'],cj_sku=p['cj_sku'],listing_url=p['cj_product_url'],file=p['images'][-1],
                    original_url=extra['source_url'],source_sha256=extra['source_sha256'],source_format=extra['source_format'],sha256=extra['sha256'],source_dimensions=extra['size'],width=extra['optimized_size'][0],height=extra['optimized_size'][1],bytes=len(photo),
                    validation='Owner supplied exact CJ URL and visually matched secondary photo; decoded original and exact reproducible WEBP; hash and dimensions checked',
                    license='CJ product promotional usage only; no independent copyright license grant evidenced',
                    usage='Only to promote this exact CJ product; no unrelated reuse',rights_reference='https://blog.cjdropshipping.com/detail/cj-drop-shipping-policy'))
        records.append(p)
    for target, raw in pending.items():
        target.write_bytes(raw)
    (ROOT/'data/catalog.json').write_text(json.dumps(dict(schema_version=1,currency='USD',catalog_status='COLLECTION_PREVIEW_SOURCING_VALIDATION',products=records),indent=2)+'\n',encoding='utf-8',newline='\n')
    (ROOT/'data/image-provenance.json').write_text(json.dumps(dict(research_sha256=hashlib.sha256(research_path.read_bytes()).hexdigest(),images=provenance),indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(candidates=len(records),photos=len(provenance),visual_hold=[p['id'] for p in records if p['visual_hold']])))

if __name__ == '__main__':
    main()
