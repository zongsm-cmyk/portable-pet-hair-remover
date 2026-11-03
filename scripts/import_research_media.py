"""Import the owner's CJ research and exact-URL download cache; never qualify stock."""
from pathlib import Path
import hashlib
import json
import io
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]

def main():
    research_path = ROOT.parent / 'VERVELIVING_CJ_15_CANDIDATES_20261103.json'
    cache = ROOT.parent / 'media_cache_cj'
    research = json.loads(research_path.read_text(encoding='utf-8'))
    receipt = {r['id']: r for r in json.loads((cache/'media_receipt.json').read_text())}
    out = ROOT/'assets/products'
    out.mkdir(parents=True, exist_ok=True)
    records, provenance = [], []
    null_fields = 'price_usd compare_at_usd supplier_cost_usd shipping_us_usd shipping_uk_usd net_margin_usd cj_variant_id warehouse_origin eta_us_days eta_uk_days supplier_verified_at shipping_us_line shipping_uk_line customer_shipping_us_usd customer_shipping_uk_usd rating review_count'.split()
    for candidate in research['products']:
        p = {key: None for key in null_fields}
        p.update({key:candidate[key] for key in ('id','slug','title','category','cj_sku','cj_product_url','short_problem_solved','features')})
        p.update(images=[], specs={key:None for key in ('dimensions','weight_g','materials','contains_lithium','contains_liquid','medical')}, verified_for_checkout=False, stock_status='unknown', draft_slot=False,
                 visual_hold=True, visual_status='VISUAL_HOLD_NO_AUTHENTIC_IMAGE', source_status=candidate['source_status'])
        if p['id'] == 'furoff':
            p['price_usd'] = 34.99
        r = receipt[p['id']]
        if r['status'] == 'OK':
            assert r['source'] == candidate['cj_primary_image_url']
            raw = (cache/(p['slug']+'-source.raw')).read_bytes()
            cached = Path(r['target']).read_bytes()
            assert hashlib.sha256(cached).hexdigest() == r['sha256']
            with Image.open(io.BytesIO(raw)) as original:
                original.load()
                assert original.format in ('JPEG','PNG','WEBP') and min(original.size) >= 250
                source_format = original.format
                source_size = original.size
                im = ImageOps.exif_transpose(original).convert('RGB')
                im.thumbnail((900,900))
                buf = io.BytesIO(); im.save(buf,format='WEBP',quality=85,method=6)
                assert buf.getvalue() == cached, 'Cached image must exactly reproduce from source'
            target = out/(p['slug']+'.webp')
            target.write_bytes(cached)
            p.update(images=['/assets/products/'+target.name],visual_hold=False,visual_status='MATCHED_CJ_RESEARCH_PHOTO')
            provenance.append(dict(product_id=p['id'],cj_sku=p['cj_sku'],listing_url=p['cj_product_url'],file=p['images'][0],
                original_url=r['source'],source_sha256=hashlib.sha256(raw).hexdigest(),sha256=r['sha256'],
                source_format=source_format,source_dimensions=source_size,width=im.width,height=im.height,bytes=len(cached),
                validation='Decoded original magic and dimensions; exact reproducible WEBP; subject visually inspected by Codex',
                http_status='Cache downloader curl --fail reported success; no response headers retained; no fresh network verification',
                content_type='Original headers not retained; MIME inferred from decoded '+source_format,
                usage='Only to promote this exact CJ product; no unrelated reuse',rights_reference='https://blog.cjdropshipping.com/detail/cj-drop-shipping-policy'))
        records.append(p)
    (ROOT/'data/catalog.json').write_text(json.dumps(dict(schema_version=1,currency='USD',catalog_status='COLLECTION_PREVIEW_SOURCING_VALIDATION',products=records),indent=2)+'\n',encoding='utf-8')
    (ROOT/'data/image-provenance.json').write_text(json.dumps(dict(research_sha256=hashlib.sha256(research_path.read_bytes()).hexdigest(),images=provenance),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(candidates=len(records),photos=len(provenance),visual_hold=[p['id'] for p in records if p['visual_hold']])))

if __name__ == '__main__':
    main()
