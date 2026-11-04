'use strict';
// Native disclosure remains usable without JS. Escape closes it and restores focus.
document.querySelectorAll('.mobile-menu').forEach(menu => {
  menu.addEventListener('keydown', event => {
    if (event.key === 'Escape' && menu.open) {
      menu.open = false;
      menu.querySelector('summary').focus();
    }
  });
  menu.querySelectorAll('a').forEach(link => link.addEventListener('click', () => { menu.open = false; }));
  document.addEventListener('click', event => {
    if (menu.open && !menu.contains(event.target)) menu.open = false;
  });
});
document.querySelectorAll('[data-product-search]').forEach(input => {
  input.addEventListener('input', () => {
    const term = input.value.trim().toLowerCase();
    let visible = 0;
    document.querySelectorAll('[data-product-title]').forEach(card => {
      card.hidden = !card.dataset.productTitle.toLowerCase().includes(term);
      if (!card.hidden) visible++;
    });
    const result = document.querySelector('[data-search-result]');
    if (result) result.textContent = visible ? `${visible} product preview${visible === 1 ? '' : 's'}` : 'No matching products.';
  });
});
const config = document.querySelector('#store-config');
const settings = config ? JSON.parse(config.textContent) : {checkout_enabled:false,api_base:''};
const CART_KEY = 'verveliving.cart.v1';
function qualifiedCatalog(products, now = Date.now()) {
  return (Array.isArray(products) ? products : []).filter(p => {
    const timestamp = Date.parse(p.supplier_verified_at);
    return typeof p.id === 'string' && /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(p.id) &&
      Number.isFinite(timestamp) && timestamp <= now && now - timestamp <= 7 * 86400000 &&
      typeof p.supplier_id === 'string' && ['cj','eprolo','hypersku','wiio'].includes(p.supplier_id) &&
      ['price_usd','customer_shipping_us_usd','customer_shipping_uk_usd'].every(key =>
        p[key] === null || (typeof p[key] === 'number' && Number.isFinite(p[key]) && p[key] >= 0 && Number.isSafeInteger(Math.round(p[key]*100)) && Math.abs(p[key]*100-Math.round(p[key]*100)) < 1e-6)) &&
      p.price_usd > 0 && ['customer_shipping_us_usd','customer_shipping_uk_usd'].some(key=>typeof p[key] === 'number');
  });
}
function normalizeCart(value, products) {
  if (!Array.isArray(value)) return [];
  const ids = new Set(products.map(p=>p.id)), seen = new Set(), result=[];
  for (const line of value) {
    if (result.length >= 15) break;
    if (!line || !ids.has(line.id) || seen.has(line.id) || !Number.isInteger(line.quantity) || line.quantity < 1 || line.quantity > 10) continue;
    seen.add(line.id); result.push({id:line.id,quantity:line.quantity});
  }
  return result;
}
function cartEstimate(items, country, products) {
  if (!['US','GB'].includes(country)) throw new Error('Choose the United States or United Kingdom.');
  const clean = normalizeCart(items,products);
  if (JSON.stringify(items) !== JSON.stringify(clean)) throw new Error('Your cart contains unavailable items. Review it before continuing.');
  return clean.reduce((total,line)=>{
    const p=products.find(p=>p.id===line.id);
    const shipping=p[country==='US'?'customer_shipping_us_usd':'customer_shipping_uk_usd'];
    if(typeof shipping !== 'number') throw new Error('A product in your cart does not ship to the selected country.');
    return total+(Math.round(p.price_usd*100)+Math.round(shipping*100))*line.quantity;
  },0);
}
function approvalDestination(value, environment) {
  const url = new URL(value);
  const origin = environment === 'sandbox' ? 'https://www.sandbox.paypal.com' : environment === 'live' ? 'https://www.paypal.com' : '';
  if (url.origin !== origin || url.username || url.password) throw new Error('Payment approval destination could not be verified.');
  return url.href;
}
function readCart() {
  try { return normalizeCart(JSON.parse(window.sessionStorage.getItem(CART_KEY)),qualifiedCatalog(settings.catalog)); }
  catch { return []; }
}
function writeCart(items) {
  const clean=normalizeCart(items,qualifiedCatalog(settings.catalog));
  try { window.sessionStorage.setItem(CART_KEY,JSON.stringify(clean)); }
  catch { throw new Error('Session storage is unavailable. Allow session storage to use the cart.'); }
  document.querySelectorAll('[data-cart-count]').forEach(node=>node.textContent=String(clean.reduce((n,l)=>n+l.quantity,0)));
  return clean;
}
function cartMessage(message) {
  const node=document.querySelector('[data-cart-status]') || document.querySelector('[data-checkout-message]') || document.querySelector('[data-cart-feedback]');
  if(node) node.textContent=message;
}
function renderCart() {
  const container=document.querySelector('[data-cart-items]');
  if (!container) return;
  const products=qualifiedCatalog(settings.catalog), items=readCart();
  container.replaceChildren();
  if (!items.length) {
    const empty=document.createElement('p');empty.textContent='Your cart is empty. Products can be added after supplier validation.';container.append(empty);
  }
  items.forEach(line=>{
    const p=products.find(p=>p.id===line.id), row=document.createElement('div');row.className='cart-line';
    const link=document.createElement('a');link.href='/products/'+p.slug+'/';link.textContent=p.title;
    const label=document.createElement('label');label.textContent='Quantity for '+p.title;
    const input=document.createElement('input');input.type='number';input.min='1';input.max='10';input.step='1';input.value=String(line.quantity);
    input.addEventListener('change',()=>{
      const qty=Number(input.value);
      if (!Number.isInteger(qty)||qty<1||qty>10) {input.value=String(line.quantity);cartMessage('Choose a whole quantity between 1 and 10.');return;}
      try {writeCart(readCart().map(l=>l.id===line.id?{id:l.id,quantity:qty}:l));renderCart();cartMessage('Cart updated.');}catch(error){cartMessage(error.message);}
    });
    label.append(input);
    const remove=document.createElement('button');remove.type='button';remove.textContent='Remove';remove.setAttribute('aria-label','Remove '+p.title);
    remove.addEventListener('click',()=>{try{writeCart(readCart().filter(l=>l.id!==line.id));renderCart();cartMessage('Item removed.');}catch(error){cartMessage(error.message);}});
    row.append(link,label,remove);container.append(row);
  });
  const country=document.querySelector('#cart-country').value;
  const payment=document.querySelector('[data-cart-payment]');payment.replaceChildren();
  let total=0;
  try{total=cartEstimate(items,country,products);}
  catch(error){document.querySelector('[data-cart-total]').textContent='Destination not available for this cart.';cartMessage(error.message);return;}
  document.querySelector('[data-cart-total]').textContent=items.length?`Estimated total: $${(total/100).toFixed(2)} USD (items and listed shipping)`:'No qualified items in your cart.';
  if (!settings.checkout_enabled || !products.length || !settings.api_base) {cartMessage('Checkout is paused while supplier and payment verification are completed. No orders or payments can be created here.');return;}
  if (!items.length) {cartMessage('Add a qualified product before continuing.');return;}
  if(total>200000){cartMessage('This cart exceeds the $2,000 order limit. Reduce quantities before continuing.');return;}
  cartMessage('Review your destination and quantities. PayPal will show the final server-calculated amount.');
  const button=document.createElement('button');button.type='button';button.className='button';button.textContent='Continue to PayPal';
  button.addEventListener('click',async()=>{
    button.disabled=true;
    // Disable edits during creation. Never silently retry an uncertain provider operation.
    container.querySelectorAll('input,button').forEach(node=>node.disabled=true);
    document.querySelector('#cart-country').disabled=true;
    try {
      const current=readCart(), valid=qualifiedCatalog(settings.catalog);
      if(!settings.checkout_enabled || !current.length || cartEstimate(current,country,valid)>200000) throw new Error('Cart is no longer available for checkout.');
      const result=await api('/api/orders/create',{items:current,country});
      window.location.assign(approvalDestination(result.approval_url,settings.paypal_environment));
    }catch(error){cartMessage(`Checkout could not be opened. ${error.message} Do not submit again if an approval or payment may already exist; contact support with the original PayPal reference.`);}
  });
  payment.append(button);
}
document.querySelectorAll('[data-add-cart]').forEach(button=>button.addEventListener('click',()=>{
  const products=qualifiedCatalog(settings.catalog), id=button.dataset.addCart;
  if (!products.some(p=>p.id===id)) {cartMessage('This product is not qualified for ordering.');return;}
  const quantity=Number(document.querySelector('#quantity')?.value || 1), items=readCart(), existing=items.find(l=>l.id===id);
  if(!Number.isInteger(quantity)||quantity<1||quantity>10||(existing?.quantity||0)+quantity>10){cartMessage('Choose a whole quantity; the cart limit is 10 per product.');return;}
  if(!existing && items.length>=15){cartMessage('The cart can hold up to 15 different products.');return;}
  const supplier=products.find(p=>p.id===id).supplier_id;
  if(items.some(line=>products.find(p=>p.id===line.id)?.supplier_id!==supplier)){cartMessage('Products from different fulfillment providers require separate checkouts.');return;}
  if(existing)existing.quantity+=quantity;else items.push({id,quantity});
  try{writeCart(items);cartMessage('Added to your cart. Use the Cart link to review quantities and delivery country.');}catch(error){cartMessage(error.message);}
}));
document.querySelectorAll('[data-cart-count]').forEach(node=>node.textContent=String(readCart().reduce((n,l)=>n+l.quantity,0)));
document.querySelector('#cart-country')?.addEventListener('change',renderCart);
renderCart();
function endpoint(path) { return settings.api_base.replace(/\/$/, '') + path; }
async function api(path, body) {
  const response = await fetch(endpoint(path), {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),credentials:'omit',cache:'no-store'});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'The service is temporarily unavailable. Please contact support.');
  return result;
}
const lookup = document.querySelector('#order-lookup');
if (lookup) lookup.addEventListener('submit', async event => {
  event.preventDefault();
  const output = document.querySelector('#lookup-result');
  if (!settings.api_base) {output.textContent='Online order lookup is not connected yet. Please email support with your order number.';return;}
  output.textContent='Looking up your order…';
  try {
    const result = await api('/api/orders/track',{order_id:lookup.elements.order_id.value.trim(),email:lookup.elements.email.value.trim()});
    output.textContent=`Order: ${result.order_id}\nStatus: ${result.fulfillment_status || result.status}\nTracking: ${result.tracking_number || 'Not yet available'}`;
  } catch(error) {output.textContent=error.message;}
});
const captureStatus = document.querySelector('#capture-status');
if (captureStatus) {
  const token = new URLSearchParams(window.location.search).get('token');
  const cancelled = window.location.pathname.includes('/cancel/') || new URLSearchParams(window.location.search).has('cancelled');
  if (cancelled) captureStatus.textContent='Payment approval was cancelled. No order confirmation has been issued.';
  else if (!token || !settings.checkout_enabled || !settings.api_base) captureStatus.textContent='Online checkout is currently unavailable. If you already made a payment, contact support with your PayPal transaction reference.';
  else {
    captureStatus.textContent='Confirming your payment securely…';
    api('/api/orders/capture',{paypal_order_id:token}).then(result => {
      if (result.payment_status !== 'COMPLETED' || typeof result.order_id !== 'string' || !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(result.order_id)) throw new Error('Verified capture receipt is missing.');
      captureStatus.textContent=`Payment confirmed. Your order number is ${result.order_id}. Keep this number for order lookup.`;
      try {writeCart([]);} catch { /* A confirmed server receipt remains valid if browser storage is unavailable. */ }
      window.history.replaceState({},'',window.location.pathname);
    }).catch(error => {captureStatus.textContent=`We could not confirm the payment here. ${error.message} Please do not pay again; contact support with your PayPal reference.`;});
  }
}

// Keep all preview angles accessible without altering the underlying supplier images.
document.querySelectorAll('[data-gallery-src]').forEach(button => {
  button.addEventListener('click', () => {
    const gallery = button.closest('.product-gallery');
    const image = gallery.querySelector('[data-gallery-main]');
    image.src = button.dataset.gallerySrc;
    image.alt = button.querySelector('img').alt;
    const caption = gallery.querySelector('[data-gallery-caption]');
    if (caption) caption.textContent = image.alt;
    gallery.querySelectorAll('[data-gallery-src]').forEach(other => other.setAttribute('aria-pressed', String(other === button)));
  });
});

document.querySelectorAll('[data-gallery-video]').forEach(button => {
  button.addEventListener('click', () => {
    const gallery=button.closest('.product-gallery');
    const main=gallery.querySelector('.product-image');
    let video=main.querySelector('video');
    if (!video) {
      video=document.createElement('video');
      video.controls=true;video.playsInline=true;video.preload='metadata';
      video.setAttribute('aria-label','Product demonstration');
      video.poster=main.querySelector('[data-gallery-main]').src;
      video.src=button.dataset.galleryVideo;
      main.appendChild(video);
    }
    main.querySelector('[data-gallery-main]').hidden=true;video.hidden=false;
    video.play().catch(()=>{});
    gallery.querySelectorAll('button').forEach(other=>other.setAttribute('aria-pressed',String(other===button)));
  });
});
document.querySelectorAll('[data-gallery-src]').forEach(button=>button.addEventListener('click',()=>{
  const main=button.closest('.product-gallery').querySelector('.product-image');
  const video=main.querySelector('video');if(video){video.pause();video.hidden=true;}
  main.querySelector('[data-gallery-main]').hidden=false;
  button.closest('.product-gallery').querySelectorAll('[data-gallery-video]').forEach(other=>other.setAttribute('aria-pressed','false'));
}));
