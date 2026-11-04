"""Deterministic, standard-library-only VerveLiving storefront generator."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
from html import escape
import json
from pathlib import Path
import re
from urllib.parse import quote, urlparse
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = {
    'kitchen-innovations': ('Kitchen Innovations', 'Less prep. More possibility.', 'Thoughtful tools for a smoother rhythm in the kitchen.', 'kitchen'),
    'home-organization': ('Home Organization & Storage', 'A place for the everyday.', 'Small-space solutions for a home that feels a little lighter.', 'organize'),
    'smart-cleaning-tools': ('Smart Cleaning Tools', 'A fresh start, made simpler.', 'Practical tools for the little messes life leaves behind.', 'cleaning'),
}
FIT_NOTES = {
    'ice-tray':'Check freezer clearance and mould capacity against the selected variant. The pictured design is a handheld cylinder, not a storage box.',
    'fruit-colander':'Check bowl capacity and overall diameter for your sink and fridge. Photos show a lidded drain basket; leakproof storage is not established.',
    'faucet-caddy':'Measure your faucet shaft and surrounding clearance. Clamp diameter and compatibility with curved or pull-out taps are not yet confirmed.',
    'garlic-press':'The pictured tool is a manual push-down chopper. Capacity, blade assembly and cleaning instructions need exact-variant confirmation; handle blades carefully.',
    'cup-drainer':'Check cup-base diameter and drainage arrangement. Exact dimensions and material composition remain unconfirmed.',
    '9hole-hanger':'Check rail diameter and vertical drop before choosing a configuration. Nine slots do not establish a tested load rating.',
    'cable-organizer':'Measure your largest adapter and packed cables. Photos do not establish waterproofing or impact protection.',
    'folding-hanger':'Check rail clearance, garment spacing and selected configuration. No tested load rating is available.',
    'vacuum-hook':'Surface texture, moisture and installation affect suction. No 3 kg or other load rating has been independently verified.',
    'foldable-tote':'Check unfolded dimensions, handle length and storage needs. Fabric specification and carrying capacity remain unconfirmed.',
    'furoff':'Test an inconspicuous fabric area first. Exact cleaning instructions and suitability for delicate textiles remain unconfirmed; this is a household tool, not animal grooming equipment.',
    'drain-snake':'Check drain access and trap design. Do not force a tool into inaccessible plumbing; exact length and tip dimensions remain unconfirmed.',
    'microfiber-cloth':'Check care instructions and surface compatibility for the chosen variant. Test delicate coatings first; no scratch-free guarantee is established.',
    'bottle-brush':'Check brush-head diameter against the bottle opening. Photos show several cleaning tools; the exact included pieces require variant confirmation.',
    'mini-mop':'Check head width and clearance for the surface you plan to clean. Replacement-head compatibility and care instructions remain unconfirmed.',
}
REQUIRED = set('id slug title category price_usd compare_at_usd supplier_cost_usd shipping_us_usd shipping_uk_usd net_margin_usd cj_sku cj_variant_id cj_product_url warehouse_origin eta_us_days eta_uk_days images short_problem_solved features specs verified_for_checkout'.split())
REQUIRED.update(('target_launch_price_usd', 'pricing_status'))
PREVIEW_DISCLOSURE = '<aside class="pricing-disclosure" aria-label="Collection preview"><strong>Product previews · Ordering unavailable.</strong><p>Prices, variants, inventory and delivery remain unverified. No payments accepted.</p></aside>'
POLICIES = {
    'shipping': ('Shipping Policy', '''<p>Our initial delivery markets are the United States and United Kingdom. Online ordering is currently paused while supplier availability, carrier pricing and delivery estimates are verified.</p><h2>Before you pay</h2><p>Each available product will display its delivery estimate, origin and total shipping charge. An estimate is not a guaranteed arrival date. We will not advertise a carrier, prepaid duties or express delivery without confirmation for that product and destination.</p><h2>Processing and tracking</h2><p>Once an order is accepted, we will provide its processing estimate and tracking information when available. Customs checks, remote destinations and carrier delays can affect delivery. Contact us if your shipment is late or missing.</p><h2>Duties and taxes</h2><p>Any known charges collected by the store will be disclosed before payment. Import charges collected by local authorities or carriers will be described where applicable. We do not currently promise duties-paid delivery.</p>'''),
    'refunds': ('Refund & Return Policy', '''<p>Online ordering is currently paused. For an existing order, contact support with the order number, delivery date and the reason for your request.</p><h2>Requesting a return</h2><p>Contact us promptly to request return instructions. No additional voluntary return window or money-back guarantee is currently offered while ordering is paused. Obtain the correct return instructions and destination before sending anything. Do not send a return to a parcel's dispatch address without confirmation.</p><h2>Damaged, faulty or incorrect items</h2><p>Contact us promptly with photographs and your order details so we can assess a replacement or refund. This policy does not limit mandatory consumer rights that apply to your purchase.</p><h2>Costs and refunds</h2><p>For a change-of-mind return, the customer normally pays return shipping unless applicable law requires otherwise. For a confirmed faulty or incorrect item, we will provide an appropriate remedy and explain any return costs before you send it. Approved refunds are returned to the original payment method; processing time depends on the payment provider.</p>'''),
    'privacy': ('Privacy Policy', '''<p>VerveLiving is the storefront operated under Askoure Systems. Contact support for privacy questions or requests.</p><h2>Information we use</h2><p>When ordering is available, we need your name, email, delivery address, ordered items and payment reference to process and support your order. PayPal handles payment credentials. Do not send card details by email.</p><h2>Sharing and storage</h2><p>Information necessary for fulfilment may be shared with the supplier, carrier and payment provider. Order records belong in a restricted server database, not browser local storage or public catalogue files. Service providers may process data outside your country.</p><h2>Website services</h2><p>This website is hosted through GitHub Pages and Cloudflare. Their services may process request logs for security and delivery. Typography uses fonts installed on your device. The store does not set advertising cookies. The cart uses session storage for product IDs and quantities only; names, addresses and order details are not saved in browser storage.</p><h2>Your choices</h2><p>Contact support to ask about access, correction or deletion, subject to applicable recordkeeping duties. Order and security records are retained only for operational, dispute and legal needs. This notice describes intended store operations; no certification of compliance is implied.</p>'''),
    'terms': ('Terms of Service', '''<p>These terms cover use of VerveLiving at shop.askouresystems.com. The current catalogue contains researched product previews awaiting supplier qualification. A preview is not an invitation to submit payment.</p><h2>Products and orders</h2><p>Product details, stock, destination eligibility and delivery terms must be confirmed before checkout is enabled. Prices are in US dollars. The final amount must be shown before payment. A payment redirection alone is not an order confirmation.</p><h2>Payments</h2><p>Where enabled, payments are processed by PayPal. PayPal Buyer Protection may apply to eligible transactions under PayPal's terms; coverage is determined by PayPal and is not guaranteed by this store.</p><h2>Use of the site</h2><p>Do not misuse the site, attempt unauthorized access or submit fraudulent orders. We may correct inaccurate listings before accepting an order and will contact you if a confirmed order cannot be fulfilled.</p><h2>Consumer rights</h2><p>Our shipping and return policies form part of these terms. Nothing here excludes mandatory consumer rights. Contact support if anything about an offer is unclear before placing an order.</p>'''),
}

def enc(value):
    return escape(str(value), quote=True)

def json_script(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')

def number(value, positive=False):
    return type(value) in (int, float) and value == value and abs(value) != float('inf') and (value > 0 if positive else value >= 0)

def eta_valid(value):
    if not isinstance(value, str):
        return False
    match = re.fullmatch(r'(\d+)\s*-\s*(\d+) (?:business )?days', value)
    return bool(match and 0 < int(match[1]) <= int(match[2]) <= 12)

SUPPORTED_SUPPLIER_DOMAINS = {
    'cj': 'cjdropshipping.com',
    'eprolo': 'eprolo.com',
    'hypersku': 'hypersku.com',
    'wiio': 'wiio.io'
}
OFFICIAL_IMAGE_DOMAINS = {
    'cj': {'cf.cjdropshipping.com', 'oss-cf.cjdropshipping.com', 'cc-west-usa.oss-accelerate.aliyuncs.com'},
    'eprolo': {'eprolo.com', 'www.eprolo.com'},
    'hypersku': {'hypersku.com', 'www.hypersku.com'},
    'wiio': {'wiio.io', 'www.wiio.io'}
}

def sourcing_identity(p):
    source = p.get('fulfillment_provider')
    if source is None:
        source = {'id': 'cj', 'sku': p.get('cj_sku'),
                  'variant_id': p.get('cj_variant_id'), 'product_url': p.get('cj_product_url')}
    if not isinstance(source, dict):
        raise ValueError('Supplier must be a structured record')
    vendor = source.get('id')
    hostname = SUPPORTED_SUPPLIER_DOMAINS.get(vendor)
    address = urlparse(source.get('product_url') or '')
    if (not hostname or address.scheme != 'https' or address.username or address.password or
            not (address.hostname == hostname or (address.hostname or '').endswith('.'+hostname))):
        raise ValueError('Unapproved supplier site or unsafe sourcing URL')
    return {'id': vendor, 'sku': source.get('sku'), 'variant_id': source.get('variant_id'),
            'url': source['product_url']}

def qualified_photo_count(p, provenance):
    """Count individually reviewed distinct originals, never crops or composites."""
    rows = [provenance[i] for i in p['images']]
    approved = [r for r in rows if all(r.get(k) is True for k in
                ('subject_verified', 'variant_verified', 'supplier_authorized', 'distinct_photo_verified'))
                and r.get('visual_method') and r.get('rights_evidence')
                and r.get('source_sha256') and r.get('original_url')
                and min(r.get('width', 0), r.get('height', 0)) >= 250]
    return min(len({r['source_sha256'] for r in approved}),
               len({r['sha256'] for r in approved}), len({r['original_url'] for r in approved}))

def validate_sellable_evidence(p, provenance):
    if qualified_photo_count(p, provenance) < 4:
        raise ValueError('SELLABLE requires four distinct authorized exact-variant photographs')
    e = p.get('qualification_evidence') or {}
    for key in ('supplier_availability', 'supplier_qc', 'silent_demo_15s', 'problem_solved', 'checkout_sandbox'):
        if not isinstance(e.get(key), dict) or e[key].get('verified') is not True or not e[key].get('reference'):
            raise ValueError('Missing verified evidence: '+key)
    if not number(e.get('processing_hours'), positive=True) or e['processing_hours'] > 48:
        raise ValueError('Verified processing must be <=48 hours')
    margins = []
    active_markets = [(c,d) for c,d in (('US','us'),('GB','uk')) if p.get(f'shipping_{d}_usd') is not None]
    if not active_markets:
        raise ValueError('No verified destination eligible for checkout')
    for country, dest in active_markets:
        market = (e.get('markets') or {}).get(country) or {}
        comparison = market.get('market_competitor') or {}
        if (comparison.get('same_variant_verified') is not True or not comparison.get('reference')
                or not number(comparison.get('delivered_price_usd'), positive=True)
                or not comparison.get('checked_at') or not market.get('landed_cost_reference')):
            raise ValueError('Market comparison and landed-cost evidence required for '+country)
        checked = datetime.fromisoformat(comparison['checked_at'].replace('Z', '+00:00'))
        if checked.tzinfo is None or not 0 <= (datetime.now(timezone.utc)-checked).total_seconds() <= 7*86400:
            raise ValueError('Market comparison must be no older than seven days')
        costs = [market.get(k) for k in ('customs_usd', 'taxes_usd', 'payment_fees_usd', 'refund_reserve_usd')]
        if not all(number(v) for v in costs):
            raise ValueError('Customs, taxes, payment fees and refund reserve must be explicit')
        landed = p['supplier_cost_usd'] + p[f'shipping_{dest}_usd'] + sum(costs)
        revenue = p['price_usd'] + p[f'customer_shipping_{dest}_usd']
        margins.append(revenue-landed)
        if (revenue > comparison['delivered_price_usd'] or p['price_usd'] < 3*landed
                or revenue-landed < 12 or (revenue-landed)/revenue < .60):
            raise ValueError('Fails competitive price, 3x all-in cost or safe net margin')
    if p['net_margin_usd'] > round(min(margins), 2) or p['net_margin_usd'] < 12:
        raise ValueError('Catalog net margin must not overstate either destination margin')

def validate(catalog, settings, root=ROOT):
    if not isinstance(catalog, dict) or not isinstance(catalog.get('products'), list):
        raise ValueError('Catalog must have a products array')
    products = catalog['products']
    if len(products) != 15 or Counter(p.get('category') for p in products) != Counter({key:5 for key in CATEGORIES}):
        raise ValueError('Wave 1 requires exactly 15 records, five per category; drafts are permitted, never purchasable')
    for key in ('id', 'slug'):
        values = [p.get(key) for p in products]
        if len(set(values)) != len(values) or any(not isinstance(v,str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',v) for v in values):
            raise ValueError(f'Unique safe {key} required')
    now = datetime.now(timezone.utc)
    provenance_file = root/'data/image-provenance.json'
    provenance = {i['file']:i for i in json.loads(provenance_file.read_text(encoding='utf-8'))['images']} if provenance_file.is_file() else {}
    published_hashes, published_sources, published_urls = set(), set(), set()
    for p in products:
        if any(p.get(key) is not None for key in ('rating', 'review_count', 'countdown', 'savings_pct')):
            raise ValueError('Unsupported review, urgency or discount claims are prohibited')
        missing = REQUIRED - p.keys()
        if missing:
            raise ValueError(f"Missing catalog fields for {p['id']}: {sorted(missing)}")
        if type(p['verified_for_checkout']) is not bool or not isinstance(p['images'],list) or not isinstance(p['features'],list) or not isinstance(p['specs'],dict):
            raise ValueError(f"Invalid catalog types: {p['id']}")
        if p['target_launch_price_usd'] is not None or p['pricing_status'] != 'PRICE_BEING_VERIFIED':
            raise ValueError('Retired price proposals must stay outside the live catalog')
        for value in p['images']:
            if not isinstance(value,str) or not value.startswith('/assets/') or '..' in value or not (root / value.lstrip('/')).is_file():
                raise ValueError(f"Images must be existing local assets: {p['id']}")
            media = provenance.get(value)
            raw = (root/value.lstrip('/')).read_bytes()
            source_info = sourcing_identity(p)
            media_vendor = media.get('supplier_id', 'cj') if media else None
            media_sku = media.get('supplier_sku', media.get('cj_sku')) if media else None
            if (not media or media['product_id'] != p['id'] or media_vendor != source_info['id']
                    or media_sku != source_info['sku'] or media['listing_url'] != source_info['url']
                    or media['sha256'] != hashlib.sha256(raw).hexdigest()):
                raise ValueError(f"Image must match product-specific provenance and hash: {p['id']}")
            if len(raw) >= 256000 or raw[:4] != b'RIFF' or raw[8:12] != b'WEBP':
                raise ValueError('Preview media must be an optimized real WEBP')
            source = urlparse(media.get('original_url', ''))
            source_domain = source.hostname or ''
            trusted_origins = OFFICIAL_IMAGE_DOMAINS[source_info['id']]
            if (source.scheme != 'https' or (source_domain not in trusted_origins and
                    not (source_info['id'] != 'cj' and source_domain.endswith('.'+SUPPORTED_SUPPLIER_DOMAINS[source_info['id']])))
                    or source.username or source.password or not re.fullmatch(r'[a-f0-9]{64}', media.get('source_sha256', ''))
                    or media.get('bytes') != len(raw) or min(media.get('width', 0), media.get('height', 0)) < 250):
                raise ValueError('Gallery requires exact official CJ source, original SHA and dimensions')
            if media['sha256'] in published_hashes or media['source_sha256'] in published_sources or media['original_url'] in published_urls:
                raise ValueError('Gallery contains duplicate source or optimized photograph')
            published_hashes.add(media['sha256']); published_sources.add(media['source_sha256']); published_urls.add(media['original_url'])
        if not p.get('visual_hold') and not p.get('draft_slot') and not 4 <= len(p['images']) <= 5:
            raise ValueError('A visible product requires four to five distinct authenticated local photographs')
        if p.get('visual_hold') and (p['images'] or p['verified_for_checkout']):
            raise ValueError('Visual holds must remain unpictured and unqualified')
        video = p.get('video')
        if video:
            video_url = urlparse(video.get('url',''))
            evidence = urlparse(video.get('rights_evidence_url') or '')
            if video.get('rights_verified') is not True or video.get('matches_product_verified') is not True or video.get('cj_sku') != p['cj_sku'] or video_url.scheme != 'https' or video_url.hostname != 'video-cf.cjdropshipping.com' or evidence.scheme != 'https' or not evidence.hostname:
                raise ValueError('Video requires verified usage rights, product match and evidence')
        if not p['verified_for_checkout']:
            for key in ('compare_at_usd','cj_variant_id','supplier_cost_usd','shipping_us_usd','shipping_uk_usd','net_margin_usd','eta_us_days','eta_uk_days'):
                if p[key] is not None:
                    raise ValueError(f'Unqualified product requires null commercial terms: {key}')
            if p.get('stock_status') != 'unknown' or p['price_usd'] is not None:
                raise ValueError('Unqualified product cannot claim stock or an unsupported retail price')
            continue
        for key in ('price_usd','supplier_cost_usd','net_margin_usd'):
            if not number(p[key], positive=key=='price_usd'):
                raise ValueError(f"Verified product requires numeric {key}: {p['id']}")
            if Decimal(str(p[key])) * 100 != (Decimal(str(p[key])) * 100).to_integral_value():
                raise ValueError(f"Money must use at most two decimal places: {key}")
        chosen_source = sourcing_identity(p)
        if not chosen_source['sku'] or not isinstance(chosen_source['sku'], str) or not chosen_source['variant_id'] or not isinstance(chosen_source['variant_id'], str):
            raise ValueError('Verified product must specify an exact supplier SKU and variant')
        for key in ('warehouse_origin','supplier_verified_at','stock_status'):
            if not p.get(key) or not isinstance(p[key],str):
                raise ValueError(f"Verified product requires {key}: {p['id']}")
        verified = datetime.fromisoformat(p['supplier_verified_at'].replace('Z','+00:00'))
        if verified.tzinfo is None or not 0 <= (now - verified).total_seconds() <= 7*86400 or p['stock_status'] != 'in_stock':
            raise ValueError('Verified supplier stock evidence must be no older than 7 days')
        if not p['images']:
            raise ValueError('Verified product requires authenticated product images')
        supported = 0
        for dest in ('us', 'uk'):
            fields = (p.get(f'shipping_{dest}_usd'),p.get(f'customer_shipping_{dest}_usd'),
                      p.get(f'eta_{dest}_days'),p.get(f'shipping_{dest}_line'))
            if all(v is None for v in fields):
                continue
            if (any(v is None for v in fields) or not number(fields[0]) or
                    not number(fields[1]) or not eta_valid(fields[2]) or
                    not isinstance(fields[3],str) or not fields[3].strip()):
                raise ValueError('Incomplete or ineligible shipping destination')
            for value in fields[:2]:
                if Decimal(str(value))*100 != (Decimal(str(value))*100).to_integral_value():
                    raise ValueError('Shipping amounts must have at most two decimal places')
            supported += 1
        if supported == 0:
            raise ValueError('Verified product requires at least one serviceable market')
        if not number(p['specs'].get('weight_g'),positive=True) or p['specs']['weight_g'] >= 500 or any(p['specs'].get(key) is not False for key in ('contains_lithium','contains_liquid','medical')):
            raise ValueError('Verified product requires under-500g weight and confirmed safe specification')
        validate_sellable_evidence(p, provenance)
        if p['compare_at_usd'] is not None:
            raise ValueError('Compare-at pricing is disabled until historical-price evidence is implemented')
    if settings.get('checkout_enabled'):
        api = urlparse(settings.get('api_base',''))
        if api.scheme != 'https' or not api.hostname:
            raise ValueError('Enabled checkout requires HTTPS API base')
        if not any(p['verified_for_checkout'] for p in products):
            raise ValueError('Cannot enable checkout without verified products')
    return products

def icon(kind):
    paths = {
        'kitchen':'<path d="M4 3v5a3 3 0 0 0 6 0V3M7 3v18M17 3v18M17 3c5 3 5 9 0 9"/>',
        'organize':'<path d="M4 6h16v15H4zM3 6l3-3h12l3 3M4 11h16M4 16h16M10 8.5h4M10 13.5h4M10 18.5h4"/>',
        'cleaning':'<path d="m16 3-6 10M8 11l6 4-5 7-6-4zM5 16l6 4M17 11v6M14 14h6M4 4v4M2 6h4"/>',
    }
    return '<svg class="icon" xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'+paths[kind]+'</svg>'

def build(root=ROOT, output=None):
    root, output = Path(root), Path(output or root).resolve()
    catalog = json.loads((root/'data/catalog.json').read_text(encoding='utf-8'))
    settings = json.loads((root/'data/settings.json').read_text(encoding='utf-8'))
    products = validate(catalog,settings,root)
    site = settings['site_url'].rstrip('/')
    email = settings['support_email']
    visible = [p for p in products if p['images'] and not p.get('visual_hold') and not p.get('draft_slot')]
    approved = [p for p in products if p['verified_for_checkout']]
    merchant_products = approved if settings['checkout_enabled'] else []
    generated = {}
    links = ''.join(f'<a href="/categories/{key}/">{enc(value[0])}</a>' for key,value in CATEGORIES.items())
    nav = f'<a class="skip" href="#main">Skip to content</a><div class="announcement">CONSIDERED TOOLS. EVERYDAY POSSIBILITIES. &nbsp; · &nbsp; ONLINE CHECKOUT CURRENTLY PAUSED</div><header class="header"><nav class="nav" aria-label="Main navigation"><a class="wordmark" href="/">Verve<span>Living</span><sup style="font:13px Arial;vertical-align:top;letter-spacing:0">™</sup></a><div class="nav-links">{links}</div><a class="nav-contact" href="/policies/contact/">Contact &amp; order lookup ↗</a></nav></header>'
    footer = f'<footer class="footer"><div class="wrap"><div class="footer-grid"><div class="footer-brand"><a class="wordmark" href="/">Verve<span>Living</span></a><p>Smart Everyday Problem Solvers.<br>Thoughtfully selected for your kitchen, your home, and your everyday.</p><p>A storefront by Askoure Systems.</p></div><div><h4>Explore</h4>{links}</div><div><h4>Good to know</h4><a href="/policies/shipping/">Shipping policy</a><a href="/policies/refunds/">Refund &amp; return policy</a><a href="/policies/privacy/">Privacy policy</a><a href="/policies/terms/">Terms of service</a><a href="/policies/contact/">Contact &amp; order lookup</a></div></div><div class="footer-bottom"><span>© 2026 VerveLiving · Askoure Systems</span><span>Product availability is being verified. No payments are currently accepted.</span></div></div></footer>'
    # Native disclosure works with keyboard and without JavaScript; desktop links stay direct.
    nav = nav.replace('<div class="nav-links">', '<div class="nav-links desktop-links">')
    mobile_links = links + '<a href="/policies/contact/">Contact support</a><a href="/track-order/">Track an order</a><a href="/policies/shipping/">Shipping &amp; order information</a>'
    nav = nav.replace('</nav>', '<a class="nav-cart" href="/cart/">Cart <span data-cart-count>0</span></a><details class="mobile-menu"><summary>Menu <span aria-hidden="true">+</span></summary><div class="mobile-menu-panel">'+mobile_links+'</div></details></nav>')
    nav = nav.replace('CONSIDERED TOOLS. EVERYDAY POSSIBILITIES. &nbsp; · &nbsp; ONLINE CHECKOUT CURRENTLY PAUSED', 'THE EVERYDAY EDIT &nbsp; / &nbsp; GOOD DESIGN FOR REAL LIFE')
    footer = footer.replace('<h4>Good to know</h4>', '<h4>Good to know</h4><a href="/cart/">Your cart</a><a href="/track-order/">Track an order</a>')
    public_settings = {key:settings[key] for key in ('checkout_enabled','api_base','paypal_environment')}
    public_settings['catalog'] = [{**{key:p[key] for key in ('id','slug','title','price_usd','images','customer_shipping_us_usd','customer_shipping_uk_usd','supplier_verified_at')}, 'supplier_id':sourcing_identity(p)['id']} for p in approved]
    # Hash the same normalized UTF-8 bytes that we publish, on Windows and Linux.
    static_assets = {name: (root/'static'/name).read_text(encoding='utf-8')
                     for name in ('store.css', 'store.js')}
    style_version = hashlib.sha256(static_assets['store.css'].encode('utf-8')).hexdigest()[:12]
    script_version = hashlib.sha256(static_assets['store.js'].encode('utf-8')).hexdigest()[:12]
    def page(title, description, path, body, schema=None, image=None, noindex=False):
        og_image = f'<meta property="og:image" content="{enc(site+image)}">' if image else ''
        ld = f'<script type="application/ld+json">{json_script(schema)}</script>' if schema else ''
        return f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{enc(title)} | VerveLiving</title><meta name="description" content="{enc(description)}"><link rel="canonical" href="{enc(site+path)}"><meta name="robots" content="{"noindex,follow" if noindex else "index,follow"}"><meta property="og:type" content="{"product" if schema else "website"}"><meta property="og:title" content="{enc(title)}"><meta property="og:description" content="{enc(description)}"><meta property="og:url" content="{enc(site+path)}">{og_image}<meta property="og:site_name" content="VerveLiving"><link rel="stylesheet" href="/assets/store.css?v={style_version}">{ld}</head><body>{nav}<main id="main" class="wrap"><p data-cart-feedback role="status" aria-live="polite"></p>{PREVIEW_DISCLOSURE if not settings["checkout_enabled"] else ""}{body}</main>{footer}<script type="application/json" id="store-config">{json_script(public_settings)}</script><script src="/assets/store.js?v={script_version}" defer></script></body></html>\n'
    # Art direction selects authentic frames, never rewrites the catalog or gallery order.
    preview_frames = {'fruit-colander':4, 'folding-hanger':1, 'garlic-press':5,
                      'bottle-brush':3, 'faucet-caddy':3, 'mini-mop':3,
                      '9hole-hanger':3, 'cable-organizer':4, 'foldable-tote':4,
                      'drain-snake':2}
    def photo(p, lazy=True, cls=''):
        src = p['images'][min(preview_frames.get(p['id'], 1), len(p['images']))-1]
        return f'<img class="{cls}" src="{enc(src)}" alt="{enc(p["title"])} — supplier product photograph; variant unverified" width="900" height="900" '+('loading="lazy" decoding="async"' if lazy else 'fetchpriority="high"')+'>'
    def category_card(key):
        name, subtitle, description, kind = CATEGORIES[key]
        count = sum(p['category']==key for p in visible)
        featured_id = {'kitchen-innovations':'fruit-colander', 'home-organization':'folding-hanger', 'smart-cleaning-tools':'furoff'}[key]
        featured = next(p for p in visible if p['id']==featured_id and p['category']==key)
        return f'<a class="category-card" href="/categories/{key}/" data-featured-product="{enc(featured["id"])}"><div class="category-photo">{photo(featured)}</div><div class="category-shade"></div><div class="category-content"><span class="category-index">{"01" if key=="kitchen-innovations" else "02" if key=="home-organization" else "03"} / Explore</span><h3>{enc(name)}</h3><p>{enc(description)}</p><span class="category-explore">Discover the collection <span aria-hidden="true">↗</span></span></div></a>'
    def card(p):
        price = f'<p class="preview-price">${p["price_usd"]:.2f} USD</p>' if p['verified_for_checkout'] else preview_price(p)
        if p['verified_for_checkout'] and settings['checkout_enabled']:
            price += f'<button class="button" type="button" data-add-cart="{enc(p["id"])}" aria-label="Add {enc(p["title"])} to cart">Add to cart</button>'
        category_label = {'kitchen-innovations':'Kitchen', 'home-organization':'Organization', 'smart-cleaning-tools':'Cleaning'}[p['category']]
        return f'<article class="product-tile" data-product-id="{enc(p["id"])}" data-product-title="{enc(p["title"])}"><a class="card-photo" href="/products/{p["slug"]}/">{photo(p)}</a><div class="card-copy"><span class="card-category">{category_label}</span><h3><a href="/products/{p["slug"]}/">{enc(p["title"])}</a></h3><p class="muted">{enc(p["short_problem_solved"])}</p>{price}<a class="text-link" href="/products/{p["slug"]}/">View product <span aria-hidden="true">↗</span></a></div></article>'
    def preview_price(p, detail=False):
        pending = '<p class="photo-pending">Additional product photos under verification</p>' if len(p['images']) < 4 else ''
        label = 'Price being verified' if detail else 'Price under verification'
        photos = f'<span class="photo-count">{len(p["images"])} supplier photos</span>' if p['images'] and not detail else ''
        return f'<p class="preview-price">{label}</p><p class="buying-status">Research preview · Not available to order</p>'+photos+pending
    def unavailable(p):
        reason_id = 'ordering-unavailable-'+p['id']
        return f'<div class="purchase-unavailable"><button class="button buy-now" type="button" disabled aria-describedby="{reason_id}">Buy now</button><p id="{reason_id}" class="buying-status">Ordering is currently unavailable: product inventory, shipping and checkout not verified</p><a class="text-link" href="mailto:{enc(email)}?subject={quote("Availability: "+p["title"],safe="")}">Ask about availability</a></div>'
    hero_product = next(p for p in visible if p['id']=='fruit-colander')
    hero_path = '/products/'+hero_product['slug']+'/'
    home = (
        '<section class="hero hero-campaign" aria-label="The VerveLiving home edit">'
        '<div class="hero-copy">'
        '<div class="hero-overline"><span class="hero-serial">VERVELIVING / VOL. 01</span><span class="hero-edition">The Everyday Edit</span></div>'
        '<span class="hero-pretitle">Home essentials, reimagined.</span>'
        '<h1>Little things.<br><em>Better living.</em></h1>'
        '<p class="hero-intro">The clever finds that make everyday routines feel a little easier. Discover considered pieces for a home that works beautifully.</p>'
        '<div class="hero-actions"><a class="button" href="#collection">Explore our edit <span aria-hidden="true">↗</span></a>'
        '<a class="hero-quiet-link" href="#collections">Browse by room <span aria-hidden="true">↓</span></a></div>'
        '<div class="hero-baseline"><span class="hero-baseline-rule"></span><span>Kitchen &nbsp;/&nbsp; Organization &nbsp;/&nbsp; Cleaning</span></div>'
        '</div><div class="hero-scene">'
        '<a class="hero-scene-main" href="'+enc(hero_path)+'" aria-label="Explore '+enc(hero_product["title"])+'">'
        +photo(hero_product,lazy=False,cls='hero-cover')+'</a>'
        '<div class="hero-scene-caption"><span>01 / KITCHEN STORIES</span><b>'+enc(hero_product["title"])+'</b></div>'
        '</div></section>'
    )
    home += '<section class="collection sales-collection" aria-label="Available products"><h2>Ordering is paused</h2>'+(''.join(card(p) for p in approved) if settings['checkout_enabled'] and approved else '<p>No qualified products are available to order.</p>')+'</section>'
    home += f'<section id="collections" class="collections"><div class="section-head"><div><span class="eyebrow">Find your next small fix</span><h2>Explore by <em>living space.</em></h2></div><p>Three considered collections, built around the ways you really live.</p></div><div class="category-grid">'+''.join(category_card(key) for key in CATEGORIES)+'</div></section>'
    story_product = next(p for p in visible if p['id']=='mini-mop')
    story_clean = next(p for p in visible if p['id']=='furoff')
    home += ('<section class="story-section" aria-labelledby="story-title"><div class="story-photos">'
             '<div class="story-photo-main">'+photo(story_product)+'</div>'
             '<div class="story-photo-accent">'+photo(story_clean)+'</div>'
             '<span class="story-photos-label">Everyday tools. A more considered space.</span></div>'
             '<div class="story-copy"><span class="eyebrow">A better kind of everyday</span>'
             '<h2 id="story-title">Good design makes room for <em>real life.</em></h2>'
             '<p>No complicated rituals. Just thoughtful objects for the moments that make up your day—from sorting a busy drawer to clearing up after a pet.</p>'
             '<div class="story-points"><span>01 <b>Useful by nature</b></span><span>02 <b>Considered details</b></span><span>03 <b>A calmer routine</b></span></div>'
             '<a class="button button-outline" href="#collection">Discover the collection <span aria-hidden="true">↗</span></a></div></section>')
    home += '<section id="collection" class="collection"><div class="section-head"><div><span class="eyebrow">Curated for the everyday</span><h2>The objects behind <em>the moments.</em></h2></div><p>Explore real product photographs and details. Ordering is not yet open.</p></div><nav class="collection-nav" aria-label="Browse collection categories">'+''.join(f'<a href="#{key}">{enc(value[0])}</a>' for key,value in CATEGORIES.items())+'</nav>'
    for key,(name,subtitle,desc,kind) in CATEGORIES.items():
        members = [p for p in visible if p['category']==key]
        home += f'<section class="collection-group" id="{key}"><div class="group-heading"><h2>{enc(name)}</h2><p>{len(members)} photographed previews / 5 researched candidates</p></div><div class="product-list">'+''.join(card(p) for p in members)+'</div></section>'
    home += '</section><section class="promise"><span class="eyebrow">Considered before it reaches you</span><h2>A clear picture, from the start.</h2><p>We are checking exact variants, stock and delivery costs before opening orders. Photography is provided by the corresponding supplier; pictured colours and configurations may vary. Two additional candidates are held back until matching photography is confirmed.</p><a class="text-link" href="/policies/contact/">A question about the collection? Get in touch ↗</a></section>'
    home = home.replace('<h2>A clear picture, from the start.</h2>', '<h2>A clear picture, from the start.</h2><div class="selection-steps"><p><b>Look at the everyday.</b> We group researched tools around kitchen routines, storage and household cleaning.</p><p><b>Look closer at the product.</b> We retain the supplier photographs and identify specifications that still need checking.</p><p><b>Verify before offering.</b> Exact variants, media rights, supplier checks, costs and checkout evidence must be confirmed before ordering opens.</p></div>')
    generated['index.html'] = page('Practical finds for a thoughtful home','Explore photographed product previews for kitchen rituals, home organization and everyday cleaning.', '/', home, image=hero_product['images'][3])
    sitemap_paths = ['/']
    for key, (name,subtitle,desc,kind) in CATEGORIES.items():
        members = [p for p in visible if p['category']==key]
        body = f'<div class="page-heading"><span class="eyebrow">The VerveLiving collections</span><h1>{enc(name)}</h1><p>{enc(subtitle)} {enc(desc)}</p></div><div class="filter"><label for="product-search" class="muted">Find a product</label><input type="search" id="product-search" data-product-search placeholder="Search this collection" aria-label="Search this collection"><span data-search-result aria-live="polite">{len(members)} product preview{"s" if len(members)!=1 else ""}</span></div>'
        # Native campaign-style category header with real matching supplier photography.
        category_id = {'kitchen-innovations':'fruit-colander','home-organization':'folding-hanger','smart-cleaning-tools':'furoff'}[key]
        category_featured = next(q for q in visible if q['id']==category_id)
        category_intro = ('<section class="collection-landing"><div class="collection-landing-copy">'
            '<span class="eyebrow">THE VERVELIVING EDIT</span>'
            '<h1>'+enc(name)+'</h1><p>'+enc(desc)+'</p>'
            '<a class="collection-landing-link" href="#products">Explore the edit <span aria-hidden="true">&#8595;</span></a></div>'
            '<div class="collection-landing-image">'+photo(category_featured,lazy=False)+'</div></section>')
        body = category_intro + '<div id="products">' + body[body.index('<div class="filter">'):]
        body += '<div class="product-list">'+''.join(card(p) for p in members)+'</div>' if members else '<section class="empty"><span class="eyebrow">Coming together</span><h2>A thoughtful collection takes care.</h2><p>We are sourcing and checking products for this collection. There are no products available to buy here yet. Please explore our other collections or contact us with a question.</p><a class="text-link" href="/">Back to the collections ↗</a></section>'
        body += '</div>'
        generated[f'categories/{key}/index.html'] = page(name,desc,f'/categories/{key}/',body)
        sitemap_paths.append(f'/categories/{key}/')
    for p in products:
        path = f'/products/{p["slug"]}/'
        schema = {'@context':'https://schema.org','@type':'Product','name':p['title'],'description':p['short_problem_solved'],'url':site+path,'sku':p['id']}
        if p['images']: schema['image']=[site+i for i in p['images']]
        if p['verified_for_checkout'] and settings['checkout_enabled']:
            schema['offers']={'@type':'Offer','priceCurrency':'USD','price':f'{p["price_usd"]:.2f}','availability':'https://schema.org/InStock','url':site+path,'itemCondition':'https://schema.org/NewCondition'}
            sitemap_paths.append(path)
        breadcrumb = f'<div class="breadcrumb"><a href="/">Home</a> / <a href="/categories/{p["category"]}/">{enc(CATEGORIES[p["category"]][0])}</a> / {enc(p["title"])}</div>'
        if p.get('visual_hold') or p.get('draft_slot'):
            body = breadcrumb+f'<section class="visual-hold"><span class="eyebrow">Sourcing validation / visual hold</span><h1>{enc(p["title"])}</h1><p>{enc(p["short_problem_solved"])}</p><p>Matching supplier photography has not been confirmed. Buying unavailable — sourcing verification pending.</p><a class="text-link" href="{enc(sourcing_identity(p)["url"])}" rel="nofollow noopener" target="_blank">View sourcing reference</a><p>This external supplier reference is separate from VerveLiving.</p></section>'

        else:
            active = p['verified_for_checkout'] and settings['checkout_enabled']
            delivery = ''
            if p['verified_for_checkout']:
                delivery = '<section class="notice"><strong>Delivery options</strong><p>' + '<br>'.join(f'{country}: {enc(p[f"eta_{dest}_days"])} · ${p[f"customer_shipping_{dest}_usd"]:.2f} USD shipping per item · ${p["price_usd"]+p[f"customer_shipping_{dest}_usd"]:.2f} USD total for one item' for country,dest in [('United States','us'),('United Kingdom','uk')] if p.get(f'shipping_{dest}_usd') is not None)+'</p></section>'
            checkout = unavailable(p)
            if active:
                checkout = delivery + f'<div class="product-actions"><label for="quantity">Quantity</label><input id="quantity" type="number" min="1" max="10" step="1" value="1"><button type="button" class="button" data-add-cart="{enc(p["id"])}">Add to cart</button><a class="text-link" href="/cart/">View cart</a></div><p data-checkout-message role="status"></p>'
            features = ''.join(f'<li>{enc(feature)}</li>' for feature in p['features'])
            specs_text = ' · '.join(enc(label)+': '+enc(p['specs'][key]) for key,label in [('dimensions','Dimensions'),('weight_g','Weight (g)'),('materials','Materials')] if p['specs'].get(key) is not None) or 'Dimensions, weight, materials and compatibility will be published after the exact supplier variant has been verified.'
            enquiry_subject = quote('Product enquiry: '+p['title'], safe='')
            count = len(p['images'])
            def gallery_alt(i):
                return f"{p['title']} - Supplier product image {i} of {count}; color may vary"
            gallery = '<div class="product-gallery"><div class="product-image"><img data-gallery-main src="'+enc(p['images'][0])+'" alt="'+enc(gallery_alt(1))+'" width="650" height="650" aria-describedby="gallery-caption"></div><p id="gallery-caption" data-gallery-caption aria-live="polite">'+enc(gallery_alt(1))+'</p><div class="gallery-thumbnails" role="group" aria-label="Supplier product images">'+''.join('<button type="button" data-gallery-src="'+enc(src)+'" aria-label="View product image '+str(i+1)+' of '+str(count)+'" aria-pressed="'+('true' if i==0 else 'false')+'"><img src="'+enc(src)+'" alt="'+enc(gallery_alt(i+1))+'" width="84" height="84"></button>' for i,src in enumerate(p['images']))+'</div><p class="photo-note">'+enc(p.get('photo_note', 'Colors shown for illustration; exact variant to be verified.'))+'</p></div>'
            video = p.get('video') or {}
            if video.get('rights_verified') is True and video.get('matches_product_verified') is True and video.get('cj_sku') == p['cj_sku']:
                video_button = '<button class="video-thumbnail" type="button" data-gallery-video="'+enc(video['url'])+'" aria-label="Watch product demonstration" aria-pressed="false">▶<span>Watch demo</span></button>'
                gallery = gallery.replace('</div></div>',video_button+'</div></div>')
            display_price = f'${p["price_usd"]:.2f} USD' if p['verified_for_checkout'] else preview_price(p, detail=True)
            body = breadcrumb+f'<section class="product-layout">{gallery}<div class="product-copy"><span class="eyebrow">{enc(CATEGORIES[p["category"]][0])}</span><h1>{enc(p["title"])}</h1><p class="lead">{enc(p["short_problem_solved"])}</p><div class="price">{display_price}</div>{checkout}<span class="pill">{"Details confirmed" if p["verified_for_checkout"] else "Details being confirmed"}</span><ul>{features}</ul><div class="notice">{"Delivery estimates and any charges are shown before payment." if p["verified_for_checkout"] else "This is a product preview. Exact specifications, supplier stock, delivery timing and shipping costs are being confirmed. No payment is requested."}</div><a class="text-link" href="mailto:{enc(email)}?subject={enc(enquiry_subject)}">Ask us about this product ↗</a><details><summary>Product details</summary><p>{specs_text}</p></details><details><summary>Delivery &amp; returns</summary><p>Initial markets: United States and United Kingdom. Confirmed product-specific delivery estimates will appear when ordering opens. <a href="/policies/shipping/">Shipping policy</a> · <a href="/policies/refunds/">Return policy</a>.</p></details><details><summary>Photography &amp; sourcing</summary><p>Supplier photography from the corresponding CJ listing. Pictured options may differ from the final selected variant. No stock or delivery commitment is implied.</p><a href="{enc(sourcing_identity(p)["url"])}" target="_blank" rel="nofollow noopener">View sourcing reference</a><p>The supplier website is separate from VerveLiving.</p></details><details><summary>Secure payments</summary><p>Online payments are currently paused. When enabled, PayPal will process payment; Buyer Protection may apply to eligible transactions under PayPal’s terms.</p></details></div></section>'
        if p.get('visual_hold') or p.get('draft_slot'):
            body = body.replace('</h1>', '</h1><p>Price being verified</p><p>Additional product photos under verification</p>'+unavailable(p), 1)
        faq = f'<section class="product-faq"><h2>Fit &amp; product questions</h2><details open><summary>Will it fit my setup?</summary><p>{enc(FIT_NOTES[p["id"]])}</p></details><details><summary>Which option will I receive?</summary><p>Colours, sizes and pictured accessories may represent different supplier variants. The exact variant and included pieces must be confirmed before a product is offered for sale.</p></details><details><summary>When can it ship?</summary><p>There is no confirmed shipping quote for this preview. Available destinations, shipping charges, import-charge terms and delivery estimates must be established for the selected variant before ordering opens. <a href="/policies/shipping/">Read shipping information</a>.</p></details></section>'
        if p['verified_for_checkout']:
            faq = faq.replace('There is no confirmed shipping quote for this preview. Available destinations, shipping charges, import-charge terms and delivery estimates must be established for the selected variant before ordering opens.', 'Review the product delivery options above and choose US or UK in the cart. Estimates are not guaranteed arrival dates. Check the selected variant and included pieces before ordering.')
        related = [q for q in visible if q['category']==p['category'] and q['id']!=p['id']][:3]
        related_markup = ('<section class="related-edit"><div class="section-head"><div><span class="eyebrow">Keep exploring</span><h2>More for the everyday.</h2></div><a class="text-link" href="/categories/'+enc(p['category'])+'/">Explore this collection ↗</a></div><div class="product-list">'+''.join(card(q) for q in related)+'</div></section>') if related and p['images'] else ''
        generated[f'products/{p["slug"]}/index.html'] = page(p['title'],p['short_problem_solved'],path,body+faq+related_markup,schema if p['verified_for_checkout'] and settings['checkout_enabled'] else None,p['images'][0] if p['images'] else None,noindex=not (p['verified_for_checkout'] and settings['checkout_enabled']))
    for slug,(title,content) in POLICIES.items():
        path = f'/policies/{slug}/'
        body = f'<article class="prose"><span class="eyebrow" style="padding-top:40px">Clear information, from the start</span><h1>{title}</h1>{content}<h2>Contact</h2><p>Email <a href="mailto:{enc(email)}">{enc(email)}</a>. Please include your order number if your question concerns an order.</p><p><small>Last updated: 3 November 2026.</small></p></article>'
        generated[f'policies/{slug}/index.html'] = page(title,title+' for VerveLiving.',path,body)
        sitemap_paths.append(path)
    body = f'<article class="prose"><h1>Here to help.</h1><p>Questions about a product, delivery or an existing order? Email <a href="mailto:{enc(email)}">{enc(email)}</a>. Please include your order number if you have one. Do not send payment-card details.</p><h2>Look up an order</h2><p>Use your order number and the email address used at checkout to request its current status and tracking information.</p><form id="order-lookup" class="lookup"><label>Order number<input name="order_id" required maxlength="100" autocomplete="off"></label><label>Email address<input name="email" required type="email" maxlength="254" autocomplete="email"></label><button class="button" type="submit">Look up order ↗</button><p class="lookup-output" id="lookup-result" role="status" aria-live="polite"></p></form><p>We are currently preparing the collection and are not accepting online payments.</p></article>'
    body = body.replace('<h2>Look up an order</h2>', '<p>Email delivery to this support address has been independently tested. We respond by email; no automated response-time guarantee is offered.</p><h2>Look up an order</h2>')
    generated['policies/contact/index.html'] = page('Contact & Order Lookup','Contact VerveLiving or check your order status.','/policies/contact/',body)
    generated['track-order/index.html'] = page('Track an order','Look up order status and available tracking.','/track-order/',body,noindex=True)
    progress = f'<aside class="notice"><h2>Before ordering opens</h2><p>{len(approved)} of 15 products qualified · {len(visible)} photographed · {15-len(visible)} on visual hold.</p><p>Exact supplier variants, stock, destination quotes, import terms and returns arrangements need verification. Merchant approval and an actual PayPal Sandbox transaction remain unverified.</p><a href="/policies/shipping/">Shipping information</a> · <a href="/policies/contact/">Contact &amp; order lookup</a></aside>'
    cart = '<section class="prose cart"><h1>Your cart</h1><p>Only qualified products can be added. Cart contents are kept for this browser session using product IDs and quantities only.</p><div data-cart-items></div><label for="cart-country">Deliver to</label><select id="cart-country"><option value="US">United States</option><option value="GB">United Kingdom</option></select><div data-cart-total aria-live="polite">No qualified items in your cart.</div><p>Estimates are in USD and include the listed customer shipping charge per item. Any import charges payable separately must be disclosed before ordering. The server recalculates the order amount; PayPal shows the amount before approval.</p><p data-cart-status role="status">Checkout is paused. This page alone does not confirm an order. No payment is requested.</p><div data-cart-payment></div><noscript><p>JavaScript is needed to edit a cart. Checkout remains unavailable without it.</p></noscript><a class="text-link" href="/">Explore the collection</a>'+progress+'</section>'
    generated['cart/index.html'] = page('Your cart','Review qualified products, quantities and destination.','/cart/',cart,noindex=True)
    sitemap_paths.append('/policies/contact/')
    for return_path in ('checkout/return/','checkout/cancel/'):
        return_title = 'Payment approval cancelled' if return_path=='checkout/cancel/' else 'Payment verification'
        generated[return_path+'index.html'] = page(return_title,'Secure payment status.','/'+return_path,'<article class="prose checkout-status"><h1>'+return_title+'</h1><p id="capture-status" role="status">Checkout is paused. Payment is pending verification unless a completed capture receipt is verified by the server. This page alone does not confirm an order. Do not pay again.</p><a class="text-link" href="/cart/">Return to cart</a> · <a class="text-link" href="/track-order/">Contact &amp; order lookup</a></article>',noindex=True)
    generated['checkout/index.html'] = page('Checkout','Review your cart before checkout.','/checkout/',cart,noindex=True)
    ET.register_namespace('g','http://base.google.com/ns/1.0')
    rss = ET.Element('rss',{'version':'2.0'})
    channel=ET.SubElement(rss,'channel')
    for key,value in [('title','VerveLiving'),('link',site),('description','Verified home and kitchen products')]: ET.SubElement(channel,key).text=value
    for p in merchant_products:
        item=ET.SubElement(channel,'item')
        attrs={'id':p['id'],'title':p['title'],'description':p['short_problem_solved'],'link':site+f'/products/{p["slug"]}/','image_link':site+p['images'][0],'availability':'in_stock','price':f'{p["price_usd"]:.2f} USD','condition':'new'}
        if p.get('gtin'): attrs['gtin']=p['gtin']
        if p.get('manufacturer_brand'): attrs['brand']=p['manufacturer_brand']
        if p.get('mpn'): attrs['mpn']=p['mpn']
        if p.get('identifier_exists') is False: attrs['identifier_exists']='no'
        for key,value in attrs.items(): ET.SubElement(item,'{http://base.google.com/ns/1.0}'+key).text=value
        for country,dest in [('US','us'),('GB','uk')]:
            shipping=ET.SubElement(item,'{http://base.google.com/ns/1.0}shipping')
            ET.SubElement(shipping,'{http://base.google.com/ns/1.0}country').text=country
            ET.SubElement(shipping,'{http://base.google.com/ns/1.0}price').text=f'{p[f"customer_shipping_{dest}_usd"]:.2f} USD'
    feed=ET.tostring(rss,encoding='unicode',xml_declaration=True)
    if not merchant_products: feed=feed.replace('<rss version="2.0">','<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0">')
    generated['feed.xml']=feed+'\n'
    ET.register_namespace('','http://www.sitemaps.org/schemas/sitemap/0.9')
    sitemap=ET.Element('{http://www.sitemaps.org/schemas/sitemap/0.9}urlset')
    for path in sitemap_paths:
        node=ET.SubElement(sitemap,'{http://www.sitemaps.org/schemas/sitemap/0.9}url')
        ET.SubElement(node,'{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text=site+path
    generated['sitemap.xml']=ET.tostring(sitemap,encoding='unicode',xml_declaration=True)+'\n'
    generated['robots.txt']=f'User-agent: *\nAllow: /\nDisallow: /checkout/\nDisallow: /api/\nSitemap: {site}/sitemap.xml\n'
    for name, content in static_assets.items(): generated['assets/'+name] = content
    if settings['checkout_enabled']:
        replacements = {
            'ONLINE CHECKOUT CURRENTLY PAUSED':'DELIVERY TO THE US &amp; UK · PAY WITH PAYPAL',
            'Product availability is being verified. No payments are currently accepted.':'Product-specific delivery details are shown before payment.',
            'Online payments are currently paused. When enabled, PayPal will process payment;':'PayPal processes payment;',
            'Online ordering is currently paused while supplier availability, carrier pricing and delivery estimates are verified.':'Available items display verified delivery estimates and shipping charges before payment.',
            'Online ordering is currently paused. For an existing order,':'For an existing order,',
            'We are currently preparing the collection and are not accepting online payments.':'If you need help before ordering, please contact us.',
            'Our collections are being prepared. We are checking exact product specifications, supplier availability, and shipping to the US and UK before opening checkout. Explore at your own pace; no payment is requested.':'Our collection brings together checked product specifications and clear delivery options. Product-specific shipping and return information is available before you pay.',
        }
        for path,content in generated.items():
            if path.endswith('.html'):
                for old,new in replacements.items():content=content.replace(old,new)
                generated[path]=content
    # Only a previous build's named output files may be removed. Never walk or
    # recursively delete directories, and never consider source/catalog/images.
    previous_receipt = output/'build-receipt.json'
    stale_files = []
    if previous_receipt.is_file():
        previous = json.loads(previous_receipt.read_text(encoding='utf-8')).get('files',{})
        for relative,expected_hash in previous.items():
            if relative in generated or not re.fullmatch(r'(?:index\.html|feed\.xml|sitemap\.xml|robots\.txt|assets/store\.(?:css|js)|(?:products|categories|policies)/[a-z0-9-]+/index\.html|checkout/(?:return/|cancel/)?index\.html)',relative):
                continue
            candidate = output/relative
            if not candidate.resolve().is_relative_to(output):
                raise ValueError('Stale output resolves outside the build directory')
            if candidate.is_file():
                if hashlib.sha256(candidate.read_bytes()).hexdigest() != expected_hash:
                    raise ValueError(f'Stale generated file was modified; preserve it before rebuilding: {relative}')
                stale_files.append(candidate)
    for candidate in stale_files:
        candidate.unlink()
    for path,content in generated.items():
        destination=output/path;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(content,encoding='utf-8',newline='\n')
    # A preview build never writes the Worker API deployment catalog.
    if settings['checkout_enabled']:
        worker=output/'workers/order-gateway/catalog.generated.json'
        worker.parent.mkdir(parents=True,exist_ok=True)
        worker_products = [{key:value for key,value in p.items() if key not in ('target_launch_price_usd','pricing_status')} for p in products]
        worker.write_text(json.dumps({'products':worker_products},ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    receipt={'step':1,'result':'BUILT_CHECKOUT_PAUSED' if not settings['checkout_enabled'] else 'BUILT_CHECKOUT_CONFIGURED','catalog_records':len(products),'verified_products':len(approved),'visible_photo_products':len(visible),'visual_hold_products':sum(bool(p.get('visual_hold')) for p in products),'draft_slots':sum(bool(p.get('draft_slot')) for p in products),'category_counts':dict(Counter(p['category'] for p in products)),'product_pages':len(products),'merchant_feed_items':len(merchant_products),'merchant_feed_gate':'verified_for_checkout AND global checkout_enabled','checkout_enabled':settings['checkout_enabled'],'real_sandbox_tested':False,'files':{path:hashlib.sha256(content.encode()).hexdigest() for path,content in sorted(generated.items())}}
    (output/'build-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8',newline='\n')
    return receipt

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    result=build(output=args.output)
    print(json.dumps({key:value for key,value in result.items() if key!='files'},indent=2))
