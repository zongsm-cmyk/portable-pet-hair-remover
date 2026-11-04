"""VerveLiving ULTRA — deterministic verified-only storefront. Payment backend unchanged."""
from pathlib import Path
from decimal import Decimal
from html import escape
from datetime import datetime
import json
import hashlib
import re

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = "/products/home-car-glove-duo/"
GUIDE = "/guides/remove-pet-hair-from-car-seats/"
PHOTO = "/assets/home-car-glove-duo.jpg"
def e(x): return escape(str(x), quote=True)
def usd(x): return "$" + format(Decimal(str(x)), ".2f")

def build(root=ROOT, output=None):
    root = Path(root); output = Path(output or root).resolve()
    config = json.loads((root/"data/settings.json").read_text(encoding="utf-8"))
    catalog = json.loads((root/"data/catalog.json").read_text(encoding="utf-8"))
    offer = json.loads((root/"workers/order-gateway/launch-offer.json").read_text(encoding="utf-8"))
    assert catalog["products"] == [], "Unverified products must be purged"
    assert config["paypal_environment"] == "live" and config["launch_offer_enabled"]
    assert offer["verified_for_checkout"] and offer["stock_status"] == "in_stock"
    assert offer["cj_sku"] and offer["cj_variant_id"] and offer["warehouse_origin"] == "US"
    assert offer["price_usd"] > offer["shipping_us_usd"] + offer["supplier_cost_usd"]
    assert datetime.fromisoformat(offer["supplier_verified_at"].replace("Z","+00:00")).tzinfo
    site=config["site_url"].rstrip("/"); support=e(config["support_email"])
    price=usd(offer["price_usd"])
    css=(root/"static/store.css").read_text(encoding="utf-8")
    js=(root/"static/store.js").read_text(encoding="utf-8")
    cv=hashlib.sha256(css.encode()).hexdigest()[:10]; jv=hashlib.sha256(js.encode()).hexdigest()[:10]
    client={"checkout_enabled":False,"api_base":config["api_base"],"paypal_environment":"live",
            "launch_offer_enabled":True,"catalog":[]}
    client_json=json.dumps(client,separators=(",",":")).replace("<","\\u003c")
    link=PRODUCT+"#home-car-glove-duo"
    img='<img src="'+PHOTO+'" alt="Black mesh pet-hair glove on a hand. Each pack contains two gloves." width="485" height="500" loading="lazy">'
    image_eager=img.replace('loading="lazy"','fetchpriority="high"')
    nav=('<div class="announcement"><span class="announce-dot"></span> Tracked US shipping included on the Home + Car glove duo</div>'
         '<header class="site-header"><div class="wrap nav"><a class="logo" href="/">VERVE<span>LIVING</span><small>®</small></a>'
         '<nav class="nav-links"><a href="'+link+'">Shop gloves</a><a href="/#story">Our approach</a>'
         '<a href="'+GUIDE+'">Care guide</a><a href="/track-order/">Track order</a></nav>'
         '<a class="nav-shop" href="'+link+'">Shop now <span>↗</span></a>'
         '<details class="mobile-menu"><summary>Menu ☰</summary><div class="mobile-menu-panel">'
         '<a href="'+link+'">Shop gloves</a><a href="/#story">Our approach</a>'
         '<a href="'+GUIDE+'">Care guide</a><a href="/track-order/">Track order</a></div></details></div></header>')
    footer=('<footer class="footer"><div class="wrap footer-grid"><div class="footer-about">'
            '<a class="logo" href="/">VERVE<span>LIVING</span></a><h3>Small tools. More room for living.</h3>'
            '<p>Curated home essentials by Askoure Systems.</p></div>'
            '<div><b>Discover</b><a href="'+link+'">The glove duo</a><a href="'+GUIDE+'">Care guide</a>'
            '<a href="/categories/smart-cleaning-tools/">Cleaning essentials</a></div>'
            '<div><b>Customer care</b><a href="/track-order/">Track order</a>'
            '<a href="/policies/shipping/">Shipping</a><a href="/policies/refunds/">Returns</a>'
            '<a href="/policies/contact/">Contact</a></div>'
            '<div><b>Information</b><a href="/policies/privacy/">Privacy</a>'
            '<a href="/policies/terms/">Terms</a><a href="mailto:'+support+'">'+support+'</a></div>'
            '</div><div class="wrap footer-bottom"><span>© 2026 VerveLiving / Askoure Systems</span>'
            '<span>Considered for the everyday.</span></div></footer>')
    def page(title,desc,url,content,noindex=False,product=False):
        ld=""
        if product:
            schema={"@context":"https://schema.org","@type":"Product",
                    "name":"Home + Car Reusable Pet Hair Removal Glove Duo",
                    "description":"Two reusable black mesh pet-hair gloves.",
                    "image":site+PHOTO,"sku":offer["cj_sku"],
                    "offers":{"@type":"Offer","url":site+PRODUCT,"priceCurrency":"USD",
                              "price":str(offer["price_usd"]),"availability":"https://schema.org/InStock"}}
            ld='<script type="application/ld+json">'+json.dumps(schema,separators=(",",":"))+'</script>'
        return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
          '<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#143f39">'
          '<title>'+e(title)+' | VerveLiving</title><meta name="description" content="'+e(desc)+'">'
          '<link rel="canonical" href="'+site+url+'"><meta name="robots" content="'+('noindex,follow' if noindex else 'index,follow')+'">'
          '<meta property="og:title" content="'+e(title)+'"><meta property="og:description" content="'+e(desc)+'">'
          '<meta property="og:image" content="'+site+PHOTO+'"><meta property="og:url" content="'+site+url+'">'
          '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
          '<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">'
          '<link rel="stylesheet" href="/assets/store.css?v='+cv+'">'+ld+'</head><body>'+nav
          +'<main id="main">'+content+'</main>'+footer+'<script type="application/json" id="store-config">'
          +client_json+'</script><script src="/assets/store.js?v='+jv+'" defer></script></body></html>')
    def buybox():
        return ('<section class="buybox" id="home-car-glove-duo" aria-label="Purchase the reusable glove set">'
          '<span class="kicker">THE HOME + CAR ESSENTIAL</span>'
          '<h2>The little fix you will reach for again.</h2>'
          '<p class="intro">Two reusable black mesh gloves designed to collect loose fur from compatible upholstery, carpets and car mats.</p>'
          '<div class="price"><strong>'+price+'</strong><span>USD per pack of two gloves<br>Tracked US shipping included</span></div>'
          '<p class="selector-title">Choose your pack</p><div class="bundle-selector" role="radiogroup" aria-label="Select glove packs">'
          '<label class="bundle"><input type="radio" name="bundle" data-bundle-option value="1" checked><span><b>Everyday duo</b><small>2 gloves · 1 pack</small></span><strong>$10.99</strong></label>'
          '<label class="bundle"><input type="radio" name="bundle" data-bundle-option value="2"><span><b>Home + Car set</b><small>4 gloves · 2 packs</small></span><strong>$21.98</strong></label>'
          '<label class="bundle"><input type="radio" name="bundle" data-bundle-option value="3"><span><b>Whole-home set</b><small>6 gloves · 3 packs</small></span><strong>$32.97</strong></label></div>'
          '<input data-launch-quantity type="hidden" value="1">'
          '<label class="phone-label" hidden>US delivery phone<input data-launch-phone type="tel" autocomplete="tel" inputmode="tel" maxlength="24" placeholder="+1 202 555 0123"></label>'
          '<p class="checkout-status" data-launch-status role="status">Checking live availability…</p>'
          '<button type="button" class="buy-button" data-launch-buy hidden>Continue with PayPal <span>↗</span></button>'
          '<p class="checkout-caption">Review your address and final total at PayPal before approving. No charge is made until you authorize payment.</p>'
          '<div class="trust-points"><span>✓ PayPal checkout</span><span>✓ Tracked delivery</span><span>✓ Order support</span></div>'
          '<p class="shipping-note">Available within the contiguous US. Estimated delivery: 3–10 days including processing; actual delivery may vary.</p></section>')
    questions=('<section class="faq wrap"><div><span class="kicker">GOOD QUESTIONS</span>'
          '<h2>Know exactly what you are getting.</h2>'
          '<p>Clear details make shopping feel easy.</p></div><div class="faq-items">'
          '<details open><summary>What comes in a pack?</summary><p>Two black reusable mesh gloves, as specified for our current US supplier variant.</p></details>'
          '<details><summary>Where can I use them?</summary><p>Test on compatible fabric upholstery, carpets and car mats. Always try a hidden area first; do not use on delicate coatings or leather without confirming suitability.</p></details>'
          '<details><summary>When will my order arrive?</summary><p>The estimated delivery window is 3–10 days including processing. It is not a delivery guarantee. We send tracking details after dispatch.</p></details>'
          '<details><summary>Can I choose multiple packs?</summary><p>Yes. Choose one, two or three two-glove packs. Each pack is priced at $10.99 including standard contiguous-US shipping.</p></details>'
          '<details><summary>What if the product arrives damaged?</summary><p>Email support with your order number and photos. We will review replacement and refund options under our <a href="/policies/refunds/">returns policy</a>.</p></details>'
          '</div></section>')
    benefits=('<section class="benefits wrap"><div><span>01</span><h3>Twice the flexibility.</h3><p>One set, two reusable gloves. Keep them where life happens.</p></div>'
          '<div><span>02</span><h3>For everyday surfaces.</h3><p>Help lift loose hair from compatible fabrics, seats and mats.</p></div>'
          '<div><span>03</span><h3>Nothing complicated.</h3><p>Compact, simple and ready to include in your cleaning routine.</p></div></section>')
    story=('<section class="story" id="story"><div class="wrap story-grid">'
          '<div class="story-visual">'+img+'<span>THE EVERYDAY EDIT / 001</span></div>'
          '<div class="story-copy"><span class="kicker">LESS MESS. MORE LIVING.</span>'
          '<h2>For the places your pet calls home.</h2>'
          '<p>Hair on the sofa. Fur in the car. Those little details are part of life with pets. A reusable tool helps make the reset feel less like a chore.</p>'
          '<div class="story-items"><div><b>01 / Sofa & throws</b><p>Lift loose fur on compatible upholstery.</p></div>'
          '<div><b>02 / Car seats</b><p>A quick pass before the next journey.</p></div>'
          '<div><b>03 / Floor mats</b><p>Help tidy pet-friendly interiors.</p></div></div>'
          '<a class="arrow-link" href="'+link+'">Explore the glove duo ↗</a></div></div></section>')
    hero=('<section class="hero"><div class="wrap hero-grid"><div class="hero-copy">'
          '<span class="kicker kicker-line">THE VERVELIVING EDIT / NO. 001</span>'
          '<h1>A softer home.<br><em>Less pet hair.</em></h1>'
          '<p>Meet the reusable glove duo for the places your pet loves most — from your sofa to your car.</p>'
          '<div class="hero-actions"><a class="cta" href="'+link+'">Shop the glove duo <span>↗</span></a>'
          '<a class="quiet-link" href="'+GUIDE+'">Explore the care guide ↗</a></div>'
          '<div class="hero-foot"><span>Reusable</span><span>Two gloves</span><span>US tracked shipping</span></div>'
          '</div><div class="hero-media"><div class="hero-image">'+image_eager+'</div>'
          '<div class="floating-tag"><small>HOME + CAR</small><b>Made for the little messes.</b></div>'
          '<div class="hero-index">01 — VERVELIVING</div></div></div></section>')
    feature=('<section class="feature wrap" id="shop"><div class="feature-heading">'
          '<span class="kicker">ONE GOOD FIND, MANY USES</span><h2>Considered for <em>real life.</em></h2>'
          '<p>A focused, verified offer instead of an endless catalog of uncertain products.</p></div>'
          '<div class="feature-grid"><div class="feature-media">'+img+'<span>TWO GLOVES / ONE PACK</span></div>'+buybox()+'</div></section>')
    home=(hero+benefits+story+feature+
          '<section class="manifesto"><div class="wrap"><span class="kicker">OUR APPROACH</span>'
          '<h2>Less noise. More of what <em>works.</em></h2>'
          '<p>Useful essentials, clearly explained. Straightforward prices. A secure checkout and support when you need it.</p>'
          '<a href="'+GUIDE+'">Read the pet-hair care guide ↗</a></div></section>'+questions+
          '<section class="end-cta wrap"><div><span class="kicker">READY FOR A RESET?</span><h2>Make room for the good stuff.</h2></div>'
          '<a class="cta" href="'+link+'">Shop the glove duo ↗</a></section>')
    product_page=('<div class="wrap breadcrumbs"><a href="/">Home</a> / <span>Home + Car</span></div>'
                  +'<section class="feature product-page wrap"><div class="feature-grid"><div class="feature-media">'
                  +image_eager+'<span>THE HOME + CAR DUO</span></div>'+buybox()+'</div></section>'+benefits+story+questions)
    guide=('<article class="guide wrap"><span class="kicker">THE CARE NOTES / 001</span>'
           '<h1>How to remove pet hair from car seats.</h1>'
           '<p class="guide-lead">A gentler routine for cleaning loose fur without damaging upholstery.</p>'
           '<div class="guide-content"><div>'+img+'</div><div><h2>Three useful steps.</h2>'
           '<ol><li><b>Test first.</b> Choose a hidden fabric area before working across a visible seat.</li>'
           '<li><b>Lift loose hair.</b> Use gentle, short strokes on compatible materials. Avoid rough scraping.</li>'
           '<li><b>Finish the details.</b> Collect the lifted hair and vacuum where appropriate. Avoid wetting seat electronics.</li></ol>'
           '<p>Follow your vehicle manufacturer’s upholstery care instructions.</p></div></div>'
           '<section id="home-car-glove-duo" class="guide-offer"><div><span class="kicker">THE TOOL WE CHOSE</span>'
           '<h2>Home + Car reusable glove duo</h2><p>Two gloves per pack · '+price+' shipped to the contiguous US.</p></div>'
           '<a href="'+link+'" class="cta">Shop the duo ↗</a></section></article>')
    collection=('<section class="collection-page wrap"><span class="kicker">HOME + CAR ESSENTIALS</span>'
                '<h1>The thoughtful clean.</h1><p>Every product here has a specified supplier variant and a clear checkout total.</p>'
                '<a class="collection-card" href="'+link+'"><div>'+img+'</div><div>'
                '<span class="kicker">VERVELIVING / 001</span><h2>Reusable Pet Hair Removal Gloves</h2>'
                '<p>Two gloves per pack. Tracked contiguous-US shipping included.</p><strong>'+price+'</strong>'
                '<span class="cta">Shop now ↗</span></div></a></section>')
    policies={
      "shipping":("Shipping & Delivery",'<p>The current sellable product is the Home + Car two-glove set for delivery within the contiguous United States.</p><h2>Delivery estimate</h2><p>3–10 days including processing. Carrier and address conditions can affect delivery; this is not a guaranteed arrival date.</p><h2>Tracking and charges</h2><p>Standard shipping is included in the displayed US price. Your address and total are reviewed at PayPal before approval. Tracking is provided after the supplier dispatches the order.</p><p>We do not currently accept checkout for other destinations.</p>'),
      "refunds":("Returns & Refunds",'<p>Contact us with your order number before sending any return. We will confirm next steps and the appropriate destination.</p><h2>Damaged or incorrect items</h2><p>Send photos and your order reference so we can assess an appropriate replacement or refund.</p><h2>Change-of-mind requests</h2><p>Contact support promptly. Eligibility and return shipping costs depend on the circumstances and applicable consumer law. Mandatory consumer rights are not limited.</p><h2>Refund timing</h2><p>Approved refunds return to the original payment method. Payment provider processing times vary.</p>'),
      "privacy":("Privacy Policy",'<p>VerveLiving is operated by Askoure Systems. We process delivery information, customer email, order items, PayPal reference and tracking details to fulfill orders.</p><h2>Third-party services</h2><p>PayPal handles payment credentials. Order records are stored on Cloudflare D1. Shipping information is shared with the supplier and carriers as needed for fulfillment. GitHub Pages and Cloudflare serve the storefront.</p><h2>Requests</h2><p>Contact us to request access, correction or deletion of personal information, subject to required accounting and dispute records. Never email payment card details.</p>'),
      "terms":("Terms of Service",'<p>VerveLiving sells selected physical household-care items. The product page specifies contents, pricing and current shipping markets.</p><h2>Payment</h2><p>PayPal processes payments in USD. An order is confirmed only after the server verifies a completed capture and records the order; leaving PayPal before confirmation is not an accepted order.</p><h2>Support</h2><p>Contact us about damaged or missing deliveries. Statutory consumer rights remain applicable.</p>')
    }
    def policy(slug):
        title,body=policies[slug]
        return '<article class="policy wrap"><span class="kicker">VERVELIVING / CUSTOMER CARE</span><h1>'+title+'</h1>'+body+'<p class="contact-end">Need help? <a href="mailto:'+support+'">'+support+'</a></p></article>'
    contact=('<section class="policy wrap"><span class="kicker">CUSTOMER CARE</span><h1>How can we help?</h1>'
       '<p>Questions about products, orders, shipping or returns? Email <a href="mailto:'+support+'">'+support+'</a>.</p>'
       '<p>Include your order number for order-specific inquiries. Never send payment card details by email.</p>'
       '<a class="arrow-link" href="/track-order/">Look up an existing order ↗</a></section>')
    tracking=('<section class="policy wrap"><span class="kicker">CUSTOMER CARE</span><h1>Track your order.</h1>'
       '<p>Enter your order number and the email address used at checkout to request your latest delivery status.</p>'
       '<form id="order-lookup" class="lookup"><label>Order number<input name="order_id" required maxlength="100" autocomplete="off"></label>'
       '<label>Email address<input name="email" type="email" required maxlength="254" autocomplete="email"></label>'
       '<button class="cta" type="submit">Find my order ↗</button><p id="lookup-result" class="lookup-output" role="status" aria-live="polite"></p></form>'
       '<p>Need help? <a href="mailto:'+support+'">'+support+'</a></p></section>')
    checkout_text=('<section class="policy wrap"><span class="kicker">SECURE CHECKOUT</span><h1>Payment status.</h1>'
       '<p id="capture-status" role="status">Checking payment status. Your order is confirmed only after a completed capture receipt is verified. Please do not pay twice.</p>'
       '<a class="cta" href="/track-order/">Track your order ↗</a></section>')
    cart=('<section class="policy wrap"><span class="kicker">VERVELIVING / YOUR BAG</span><h1>Your everyday essentials.</h1>'
       '<p>The Home + Car glove duo has a dedicated checkout. Choose 1, 2 or 3 packs on the product page.</p>'
       '<a class="cta" href="'+link+'">Choose a glove set ↗</a></section>')
    generated={
      "index.html":page("Everyday essentials for a softer home","Shop a reusable two-glove pet-hair removal set with tracked contiguous-US shipping.","/",home),
      "products/home-car-glove-duo/index.html":page("Home + Car Pet Hair Removal Glove Duo","Two reusable mesh gloves per pack, from $10.99 with shipping included.","/products/home-car-glove-duo/",product_page,product=True),
      "categories/smart-cleaning-tools/index.html":page("Cleaning essentials","Shop verified reusable pet hair-removal gloves.","/categories/smart-cleaning-tools/",collection),
      "guides/remove-pet-hair-from-car-seats/index.html":page("How to remove pet hair from car seats","A practical guide to lifting loose pet hair from compatible upholstery.",GUIDE,guide),
      "policies/contact/index.html":page("Contact VerveLiving","Get support for your VerveLiving order.","/policies/contact/",contact),
      "track-order/index.html":page("Track your order","Check delivery details for an existing order.","/track-order/",tracking,noindex=True),
      "checkout/return/index.html":page("Payment verification","Verify your PayPal order.","/checkout/return/",checkout_text,noindex=True),
      "checkout/cancel/index.html":page("Payment cancelled","Secure PayPal checkout status.","/checkout/cancel/",checkout_text,noindex=True),
      "cart/index.html":page("Choose your set","Shop the VerveLiving glove duo.","/cart/",cart,noindex=True),
      "checkout/index.html":page("Secure checkout","Shop the VerveLiving glove duo.","/checkout/",cart,noindex=True),
      "assets/store.css":css,
      "assets/store.js":js
    }
    for slug,(title,_) in policies.items():
        generated["policies/"+slug+"/index.html"]=page(title,title+" from VerveLiving.","/policies/"+slug+"/",policy(slug))
    indexed=["/","/products/home-car-glove-duo/","/categories/smart-cleaning-tools/",GUIDE]
    indexed+=["/policies/"+slug+"/" for slug in policies]
    indexed+=["/policies/contact/"]
    generated["sitemap.xml"]='<?xml version="1.0" encoding="utf-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+''.join('<url><loc>'+site+x+'</loc></url>\n' for x in indexed)+'</urlset>\n'
    generated["robots.txt"]="User-agent: *\nAllow: /\nDisallow: /checkout/\nDisallow: /api/\nSitemap: "+site+"/sitemap.xml\n"
    generated["feed.xml"]=('<?xml version="1.0" encoding="utf-8"?>\n'
      '<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0"><channel><title>VerveLiving</title>'
      '<link>'+site+'</link><item><g:id>'+offer["id"]+'</g:id>'
      '<g:title>Reusable Pet Hair Glove Duo (2 Gloves)</g:title>'
      '<g:description>Two black reusable mesh gloves.</g:description><g:link>'+site+PRODUCT+'</g:link>'
      '<g:image_link>'+site+PHOTO+'</g:image_link><g:price>10.99 USD</g:price><g:availability>in stock</g:availability>'
      '<g:condition>new</g:condition></item></channel></rss>\n')
    previous=output/"build-receipt.json"
    if previous.exists():
        before=json.loads(previous.read_text(encoding="utf-8"))
        for path in before.get("files",{}):
            if path not in generated and (path.startswith("products/") or path.startswith("categories/")):
                old=output/path
                if old.is_file() and old.resolve().is_relative_to(output):
                    old.unlink()
    for path,contents in generated.items():
        dest=output/path;dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(contents,encoding="utf-8")
    receipt={"version":"ULTRA-20261104","result":"BUILT_VERIFIED_LIVE_OFFER",
      "verified_products":1,"unverified_products":len(catalog["products"]),
      "checkout_environment":"live","payment_executed":False,
      "files":{path:hashlib.sha256(txt.encode()).hexdigest() for path,txt in sorted(generated.items())}}
    (output/"build-receipt.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"result":receipt["result"],"pages":len(generated),"purged":len(catalog["products"])}))
    return receipt
if __name__=="__main__":
    build()
