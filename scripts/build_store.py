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
REQUIRED = set('id slug title category price_usd compare_at_usd supplier_cost_usd shipping_us_usd shipping_uk_usd net_margin_usd cj_sku cj_variant_id cj_product_url warehouse_origin eta_us_days eta_uk_days images short_problem_solved features specs verified_for_checkout'.split())
POLICIES = {
    'shipping': ('Shipping Policy', '''<p>Our initial delivery markets are the United States and United Kingdom. Online ordering is currently paused while supplier availability, carrier pricing and delivery estimates are verified.</p><h2>Before you pay</h2><p>Each available product will display its delivery estimate, origin and total shipping charge. An estimate is not a guaranteed arrival date. We will not advertise a carrier, prepaid duties or express delivery without confirmation for that product and destination.</p><h2>Processing and tracking</h2><p>Once an order is accepted, we will provide its processing estimate and tracking information when available. Customs checks, remote destinations and carrier delays can affect delivery. Contact us if your shipment is late or missing.</p><h2>Duties and taxes</h2><p>Any known charges collected by the store will be disclosed before payment. Import charges collected by local authorities or carriers will be described where applicable. We do not currently promise duties-paid delivery.</p>'''),
    'refunds': ('Refund & Return Policy', '''<p>Online ordering is currently paused. For an existing order, contact support with the order number, delivery date and the reason for your request.</p><h2>Requesting a return</h2><p>Please contact us within 30 days after delivery to request a return for an unused item in its original condition. Obtain the correct return instructions and destination before sending anything. Do not send a return to a parcel's dispatch address without confirmation.</p><h2>Damaged, faulty or incorrect items</h2><p>Contact us promptly with photographs and your order details so we can assess a replacement or refund. This policy does not limit mandatory consumer rights that apply to your purchase.</p><h2>Costs and refunds</h2><p>For a change-of-mind return, the customer normally pays return shipping unless applicable law requires otherwise. For a confirmed faulty or incorrect item, we will provide an appropriate remedy and explain any return costs before you send it. Approved refunds are returned to the original payment method; processing time depends on the payment provider.</p>'''),
    'privacy': ('Privacy Policy', '''<p>VerveLiving is the storefront operated under Askoure Systems. Contact support for privacy questions or requests.</p><h2>Information we use</h2><p>When ordering is available, we need your name, email, delivery address, ordered items and payment reference to process and support your order. PayPal handles payment credentials. Do not send card details by email.</p><h2>Sharing and storage</h2><p>Information necessary for fulfilment may be shared with the supplier, carrier and payment provider. Order records belong in a restricted server database, not browser local storage or public catalogue files. Service providers may process data outside your country.</p><h2>Website services</h2><p>This website is hosted through GitHub Pages and Cloudflare. Their services may process request logs for security and delivery. Fonts are requested from Google Fonts. The store does not set advertising cookies or store customer order details in browser local storage.</p><h2>Your choices</h2><p>Contact support to ask about access, correction or deletion, subject to applicable recordkeeping duties. Order and security records are retained only for operational, dispute and legal needs. This notice describes intended store operations; no certification of compliance is implied.</p>'''),
    'terms': ('Terms of Service', '''<p>These terms cover use of VerveLiving at shop.askouresystems.com. The current catalogue includes a product preview and collections under development. A preview is not an invitation to submit payment.</p><h2>Products and orders</h2><p>Product details, stock, destination eligibility and delivery terms must be confirmed before checkout is enabled. Prices are in US dollars. The final amount must be shown before payment. A payment redirection alone is not an order confirmation.</p><h2>Payments</h2><p>Where enabled, payments are processed by PayPal. PayPal Buyer Protection may apply to eligible transactions under PayPal's terms; coverage is determined by PayPal and is not guaranteed by this store.</p><h2>Use of the site</h2><p>Do not misuse the site, attempt unauthorized access or submit fraudulent orders. We may correct inaccurate listings before accepting an order and will contact you if a confirmed order cannot be fulfilled.</p><h2>Consumer rights</h2><p>Our shipping and return policies form part of these terms. Nothing here excludes mandatory consumer rights. Contact support if anything about an offer is unclear before placing an order.</p>'''),
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
    return bool(match and 0 < int(match[1]) <= int(match[2]) <= 14)

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
    for p in products:
        missing = REQUIRED - p.keys()
        if missing:
            raise ValueError(f"Missing catalog fields for {p['id']}: {sorted(missing)}")
        if type(p['verified_for_checkout']) is not bool or not isinstance(p['images'],list) or not isinstance(p['features'],list) or not isinstance(p['specs'],dict):
            raise ValueError(f"Invalid catalog types: {p['id']}")
        for value in p['images']:
            if not isinstance(value,str) or not value.startswith('/assets/') or '..' in value or not (root / value.lstrip('/')).is_file():
                raise ValueError(f"Images must be existing local assets: {p['id']}")
        if not p['verified_for_checkout']:
            continue
        for key in ('price_usd','supplier_cost_usd','shipping_us_usd','shipping_uk_usd','net_margin_usd'):
            if not number(p[key], positive=key=='price_usd'):
                raise ValueError(f"Verified product requires numeric {key}: {p['id']}")
            if Decimal(str(p[key])) * 100 != (Decimal(str(p[key])) * 100).to_integral_value():
                raise ValueError(f"Money must use at most two decimal places: {key}")
        for key in ('cj_sku','cj_variant_id','cj_product_url','warehouse_origin','supplier_verified_at','stock_status','shipping_us_line','shipping_uk_line'):
            if not p.get(key) or not isinstance(p[key],str):
                raise ValueError(f"Verified product requires {key}: {p['id']}")
        url = urlparse(p['cj_product_url'])
        if url.scheme != 'https' or not (url.hostname == 'cjdropshipping.com' or (url.hostname or '').endswith('.cjdropshipping.com')):
            raise ValueError('Verified supplier must be CJ HTTPS URL')
        verified = datetime.fromisoformat(p['supplier_verified_at'].replace('Z','+00:00'))
        if verified.tzinfo is None or not 0 <= (now - verified).total_seconds() <= 7*86400 or p['stock_status'] != 'in_stock':
            raise ValueError('Verified supplier stock evidence must be no older than 7 days')
        if not p['images'] or not eta_valid(p['eta_us_days']) or not eta_valid(p['eta_uk_days']):
            raise ValueError('Verified product requires images and US/UK delivery <=14 days')
        if not number(p['specs'].get('weight_g'),positive=True) or p['specs']['weight_g'] >= 500 or any(p['specs'].get(key) is not False for key in ('contains_lithium','contains_liquid','medical')):
            raise ValueError('Verified product requires under-500g weight and confirmed safe specification')
        for key in ('customer_shipping_us_usd','customer_shipping_uk_usd'):
            if not number(p.get(key)):
                raise ValueError('Customer shipping must be explicit and numeric')
            if Decimal(str(p[key])) * 100 != (Decimal(str(p[key])) * 100).to_integral_value():
                raise ValueError('Customer shipping must use at most two decimal places')
        for destination in ('us','uk'):
            landed = p['supplier_cost_usd'] + p[f'shipping_{destination}_usd']
            margin = p['price_usd']*0.955 - landed
            if p['price_usd'] < landed*3 and margin < 12:
                raise ValueError('Product fails both minimum markup and contribution rules')
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
    paths = {'kitchen':'<path d="M26 20v29c0 10 8 16 18 16h5v28M16 20v22M36 20v22M63 20v73M63 20c20 7 23 32 0 32"/>', 'organize':'<path d="M17 28h66v61H17zM13 28l13-15h48l13 15M17 49h66M17 69h66M43 39h15M43 59h15M43 79h15"/>','cleaning':'<path d="M65 14L40 57M35 51l23 13-20 31-24-14zM22 74l24 14M29 63l25 14M66 12l9 6M75 49v17M67 57h17M17 23v12M11 29h12"/>'}
    return '<svg viewBox="0 0 100 110" aria-hidden="true">'+paths[kind]+'</svg>'

def build(root=ROOT, output=None):
    root, output = Path(root), Path(output or root).resolve()
    catalog = json.loads((root/'data/catalog.json').read_text(encoding='utf-8'))
    settings = json.loads((root/'data/settings.json').read_text(encoding='utf-8'))
    products = validate(catalog,settings,root)
    site = settings['site_url'].rstrip('/')
    email = settings['support_email']
    visible = [p for p in products if not p.get('draft_slot')]
    approved = [p for p in products if p['verified_for_checkout']]
    merchant_products = approved if settings['checkout_enabled'] else []
    generated = {}
    links = ''.join(f'<a href="/categories/{key}/">{enc(value[0])}</a>' for key,value in CATEGORIES.items())
    nav = f'<a class="skip" href="#main">Skip to content</a><div class="announcement">CONSIDERED TOOLS. EVERYDAY POSSIBILITIES. &nbsp; · &nbsp; ONLINE CHECKOUT CURRENTLY PAUSED</div><header class="header"><nav class="nav" aria-label="Main navigation"><a class="wordmark" href="/">Verve<span>Living</span><sup style="font:9px Arial;vertical-align:top;letter-spacing:0">™</sup></a><div class="nav-links">{links}</div><a class="nav-contact" href="/policies/contact/">Contact &amp; order lookup ↗</a></nav></header>'
    footer = f'<footer class="footer"><div class="wrap"><div class="footer-grid"><div class="footer-brand"><a class="wordmark" href="/">Verve<span>Living</span></a><p>Smart Everyday Problem Solvers.<br>Thoughtfully selected for your kitchen, your home, and your everyday.</p><p>A storefront by Askoure Systems.</p></div><div><h4>Explore</h4>{links}</div><div><h4>Good to know</h4><a href="/policies/shipping/">Shipping policy</a><a href="/policies/refunds/">Refund &amp; return policy</a><a href="/policies/privacy/">Privacy policy</a><a href="/policies/terms/">Terms of service</a><a href="/policies/contact/">Contact &amp; order lookup</a></div></div><div class="footer-bottom"><span>© 2026 VerveLiving · Askoure Systems</span><span>Product availability is being verified. No payments are currently accepted.</span></div></div></footer>'
    public_settings = {key:settings[key] for key in ('checkout_enabled','api_base','paypal_environment')}
    def page(title, description, path, body, schema=None, image=None, noindex=False):
        og_image = f'<meta property="og:image" content="{enc(site+image)}">' if image else ''
        ld = f'<script type="application/ld+json">{json_script(schema)}</script>' if schema else ''
        return f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{enc(title)} | VerveLiving</title><meta name="description" content="{enc(description)}"><link rel="canonical" href="{enc(site+path)}"><meta name="robots" content="{"noindex,follow" if noindex else "index,follow"}"><meta property="og:type" content="{"product" if schema else "website"}"><meta property="og:title" content="{enc(title)}"><meta property="og:description" content="{enc(description)}"><meta property="og:url" content="{enc(site+path)}">{og_image}<meta property="og:site_name" content="VerveLiving"><link rel="stylesheet" href="/assets/store.css">{ld}</head><body>{nav}<main id="main" class="wrap">{body}</main>{footer}<script type="application/json" id="store-config">{json_script(public_settings)}</script><script src="/assets/store.js" defer></script></body></html>\n'
    def category_card(key):
        name, subtitle, description, kind = CATEGORIES[key]
        return f'<a class="category-card" href="/categories/{key}/"><div class="category-art {kind}">{icon(kind)}</div><h3>{enc(name)}<span class="arrow">↗</span></h3><p>{enc(description)}</p></a>'
    def card(p):
        image = f'<img src="{enc(p["images"][0])}" alt="{enc(p["title"])}" loading="lazy" width="500" height="500">' if p['images'] else ''
        price = f'${p["price_usd"]:.2f}' if number(p['price_usd']) else 'Pricing to be confirmed'
        return f'<article class="product-tile" data-product-title="{enc(p["title"])}">{image}<span class="pill">{"Available" if p["verified_for_checkout"] else "Product preview"}</span><h3><a href="/products/{p["slug"]}/">{enc(p["title"])}</a></h3><p class="muted">{enc(p["short_problem_solved"])}</p><div class="price">{price} <small>USD · {"item price" if p["verified_for_checkout"] else "indicative item price"}</small></div><a class="text-link" href="/products/{p["slug"]}/">Explore the details ↗</a></article>'
    fur = next(p for p in products if p['id']=='furoff')
    home = f'<section class="hero"><div class="hero-copy"><span class="eyebrow">A little less effort. A little more living.</span><h1>A thoughtful home.<br>An <em>easier everyday.</em></h1><p>Small, practical discoveries for the spaces you love. Explore a considered collection for cooking, organizing, and keeping things fresh.</p><a class="button" href="#collections">Explore our collections <span>↗</span></a></div><div class="hero-art"><img src="/assets/furoff-pro.jpg" alt="FurOff cleaning roller product preview" width="650" height="650"><span class="image-label">FurOff · Product preview</span><div class="hero-stamp"><strong>Less fuss.<br>More everyday ease.</strong>Our first collection is taking shape.</div></div></section><div class="benefits"><div class="benefit">{icon("kitchen")}<div><b>Practical by design</b><small>Tools with a clear everyday purpose</small></div></div><div class="benefit">{icon("organize")}<div><b>Clear before checkout</b><small>Product and delivery details come first</small></div></div><div class="benefit">{icon("cleaning")}<div><b>Here when you need us</b><small>Contact and order lookup in one place</small></div></div></div><section id="collections"><div class="section-head"><div><span class="eyebrow">Three ways to simplify your day</span><h2>Find your everyday essentials.</h2></div><p>One cohesive home collection.<br>Useful ideas, thoughtfully considered.</p></div><div class="category-grid">'+''.join(category_card(key) for key in CATEGORIES)+'</div></section>'
    home += f'<section class="curated"><div class="curated-copy"><span class="eyebrow">A closer look</span><h2>Meet the first<br>of the collection.</h2><p>Our cleaning-tool preview is here to explore. We are confirming supplier details and delivery options before accepting orders.</p><a class="text-link" href="/categories/smart-cleaning-tools/">Discover cleaning tools ↗</a></div><div class="product-feature"><img src="/assets/furoff-pro.jpg" alt="FurOff reusable household roller preview" loading="lazy" width="400" height="400"><div><span class="pill">Product preview</span><h3>FurOff Pro</h3><p>A household roller concept for lifting loose hair and lint from suitable fabrics.</p><div class="price">$34.99 <small>USD · indicative</small></div><a class="text-link" href="/products/{fur["slug"]}/">Take a closer look ↗</a></div></div></section><section class="promise"><span class="eyebrow">Thoughtful from the start</span><h2>Good things deserve<br>clear information.</h2><p>Our collections are being prepared. We are checking exact product specifications, supplier availability, and shipping to the US and UK before opening checkout. Explore at your own pace; no payment is requested.</p><a class="text-link" href="/policies/shipping/">Read about delivery &amp; returns ↗</a></section>'
    if approved:
        home += '<section><div class="section-head"><div><span class="eyebrow">Considered for your everyday</span><h2>Explore the collection.</h2></div></div><div class="product-list">'+''.join(card(p) for p in approved[:6])+'</div></section>'
    generated['index.html'] = page('Smart Everyday Problem Solvers','Considered tools for your kitchen, home organization and everyday cleaning. Explore VerveLiving.', '/', home, image='/assets/furoff-pro.jpg')
    sitemap_paths = ['/']
    for key, (name,subtitle,desc,kind) in CATEGORIES.items():
        members = [p for p in visible if p['category']==key]
        body = f'<div class="page-heading"><span class="eyebrow">The VerveLiving collections</span><h1>{enc(name)}</h1><p>{enc(subtitle)} {enc(desc)}</p></div><div class="filter"><label for="product-search" class="muted">Find a product</label><input type="search" id="product-search" data-product-search placeholder="Search this collection" aria-label="Search this collection"><span data-search-result aria-live="polite">{len(members)} product preview{"s" if len(members)!=1 else ""}</span></div>'
        body += '<div class="product-list">'+''.join(card(p) for p in members)+'</div>' if members else '<section class="empty"><span class="eyebrow">Coming together</span><h2>A thoughtful collection takes care.</h2><p>We are sourcing and checking products for this collection. There are no products available to buy here yet. Please explore our other collections or contact us with a question.</p><a class="text-link" href="/">Back to the collections ↗</a></section>'
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
        if p.get('draft_slot'):
            body = breadcrumb+'<section class="empty"><span class="eyebrow">Collection in progress</span><h1>Details coming after verification.</h1><p>This page reserves a place in our collection. It is not a product offer, and no payment is available.</p><a class="text-link" href="/">Explore VerveLiving ↗</a></section>'
        else:
            active = p['verified_for_checkout'] and settings['checkout_enabled']
            delivery = ''
            if p['verified_for_checkout']:
                delivery = '<section class="notice"><strong>Delivery options</strong><p>' + '<br>'.join(f'{country}: {enc(p[f"eta_{dest}_days"])} · ${p[f"customer_shipping_{dest}_usd"]:.2f} USD shipping per item · ${p["price_usd"]+p[f"customer_shipping_{dest}_usd"]:.2f} USD total for one item' for country,dest in [('United States','us'),('United Kingdom','uk')])+'</p></section>'
            checkout = delivery + (f'<label for="country">Deliver to</label><select id="country"><option value="US">United States</option><option value="GB">United Kingdom</option></select>' if active else '')
            checkout += f'<div class="product-actions"><label class="muted" for="quantity">Quantity</label><input id="quantity" type="number" min="1" max="10" value="1" {"" if active else "disabled"}><button class="button" type="button" {"data-checkout-product="+enc(p["id"]) if active else "disabled"}>{"Continue to PayPal" if active else "Checkout not available yet"}</button></div><p data-checkout-message role="status"></p>'
            features = ''.join(f'<li>{enc(feature)}</li>' for feature in p['features'])
            specs_text = ' · '.join(enc(label)+': '+enc(p['specs'][key]) for key,label in [('dimensions','Dimensions'),('weight_g','Weight (g)'),('materials','Materials')] if p['specs'].get(key) is not None) or 'Dimensions, weight, materials and compatibility will be published after the exact supplier variant has been verified.'
            enquiry_subject = quote('Product enquiry: '+p['title'], safe='')
            body = breadcrumb+f'<section class="product-layout"><div class="product-image"><img src="{enc(p["images"][0])}" alt="{enc(p["title"])} product preview" width="650" height="650"></div><div class="product-copy"><span class="eyebrow">{enc(CATEGORIES[p["category"]][0])}</span><h1>{enc(p["title"])}</h1><p class="lead">{enc(p["short_problem_solved"])}</p><div class="price">${p["price_usd"]:.2f} <small>USD · {"item price" if p["verified_for_checkout"] else "indicative item price"}</small></div><span class="pill">{"Details confirmed" if p["verified_for_checkout"] else "Details being confirmed"}</span><ul>{features}</ul><div class="notice">{"Delivery estimates and any charges are shown before payment." if p["verified_for_checkout"] else "This is a product preview. Exact specifications, supplier stock, delivery timing and shipping costs are being confirmed. No payment is requested."}</div>{checkout}<a class="text-link" href="mailto:{enc(email)}?subject={enc(enquiry_subject)}">Ask us about this product ↗</a><details><summary>Product details</summary><p>{specs_text}</p></details><details><summary>Delivery &amp; returns</summary><p>Initial markets: United States and United Kingdom. Confirmed product-specific delivery estimates will appear when ordering opens. <a href="/policies/shipping/">Shipping policy</a> · <a href="/policies/refunds/">Return policy</a>.</p></details><details><summary>Secure payments</summary><p>Online payments are currently paused. When enabled, PayPal will process payment; Buyer Protection may apply to eligible transactions under PayPal’s terms.</p></details></div></section>'
        generated[f'products/{p["slug"]}/index.html'] = page(p['title'],p['short_problem_solved'],path,body,schema if not p.get('draft_slot') else None,p['images'][0] if p['images'] else None,noindex=not p['verified_for_checkout'])
    for slug,(title,content) in POLICIES.items():
        path = f'/policies/{slug}/'
        body = f'<article class="prose"><span class="eyebrow" style="padding-top:40px">Clear information, from the start</span><h1>{title}</h1>{content}<h2>Contact</h2><p>Email <a href="mailto:{enc(email)}">{enc(email)}</a>. Please include your order number if your question concerns an order.</p><p><small>Last updated: 3 November 2026.</small></p></article>'
        generated[f'policies/{slug}/index.html'] = page(title,title+' for VerveLiving.',path,body)
        sitemap_paths.append(path)
    body = f'<article class="prose"><h1>Here to help.</h1><p>Questions about a product, delivery or an existing order? Email <a href="mailto:{enc(email)}">{enc(email)}</a>. Please include your order number if you have one. Do not send payment-card details.</p><h2>Look up an order</h2><p>Use your order number and the email address used at checkout to request its current status and tracking information.</p><form id="order-lookup" class="lookup"><label>Order number<input name="order_id" required maxlength="100" autocomplete="off"></label><label>Email address<input name="email" required type="email" maxlength="254" autocomplete="email"></label><button class="button" type="submit">Look up order ↗</button><p class="lookup-output" id="lookup-result" role="status" aria-live="polite"></p></form><p>We are currently preparing the collection and are not accepting online payments.</p></article>'
    generated['policies/contact/index.html'] = page('Contact & Order Lookup','Contact VerveLiving or check your order status.','/policies/contact/',body)
    sitemap_paths.append('/policies/contact/')
    for return_path in ('checkout/','checkout/return/','checkout/cancel/'):
        generated[return_path+'index.html'] = page('Payment confirmation','Secure payment confirmation.','/'+return_path,'<article class="prose checkout-status"><h1>Payment confirmation</h1><p id="capture-status" role="status"></p><a href="/policies/contact/">Contact &amp; order lookup</a></article>',noindex=True)
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
    for name in ('store.css','store.js'): generated['assets/'+name]=(root/'static'/name).read_text(encoding='utf-8')
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
    worker=output/'workers/order-gateway/catalog.generated.json'
    worker.parent.mkdir(parents=True,exist_ok=True)
    worker.write_text(json.dumps({'products':products},ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    receipt={'step':1,'result':'BUILT_CHECKOUT_PAUSED' if not settings['checkout_enabled'] else 'BUILT_CHECKOUT_CONFIGURED','catalog_records':len(products),'verified_products':len(approved),'draft_slots':sum(bool(p.get('draft_slot')) for p in products),'category_counts':dict(Counter(p['category'] for p in products)),'product_pages':len(products),'merchant_feed_items':len(merchant_products),'merchant_feed_gate':'verified_for_checkout AND global checkout_enabled','checkout_enabled':settings['checkout_enabled'],'real_sandbox_tested':False,'files':{path:hashlib.sha256(content.encode()).hexdigest() for path,content in sorted(generated.items())}}
    (output/'build-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8',newline='\n')
    return receipt

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    result=build(output=args.output)
    print(json.dumps({key:value for key,value in result.items() if key!='files'},indent=2))
