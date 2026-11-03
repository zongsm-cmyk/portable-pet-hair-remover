'use strict';
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
function endpoint(path) { return settings.api_base.replace(/\/$/, '') + path; }
async function api(path, body) {
  const response = await fetch(endpoint(path), {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),credentials:'omit',cache:'no-store'});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'The service is temporarily unavailable. Please contact support.');
  return result;
}
document.querySelectorAll('[data-checkout-product]').forEach(button => {
  button.addEventListener('click', async () => {
    const status = document.querySelector('[data-checkout-message]');
    if (!settings.checkout_enabled || !settings.api_base) { status.textContent='Online checkout is not available yet.'; return; }
    const qty = Number(document.querySelector('#quantity').value);
    if (!Number.isInteger(qty) || qty < 1 || qty > 10) { status.textContent='Choose a quantity between 1 and 10.'; return; }
    button.disabled = true;
    try {
      const result = await api('/api/orders/create', {items:[{id:button.dataset.checkoutProduct,quantity:qty}],country:document.querySelector('#country').value});
      const approval = new URL(result.approval_url);
      if (!['https://www.paypal.com','https://www.sandbox.paypal.com'].includes(approval.origin)) throw new Error('Payment approval destination could not be verified.');
      window.location.assign(approval.href);
    } catch (error) { status.textContent=error.message;button.disabled=false; }
  });
});
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
      captureStatus.textContent=`Payment confirmed. Your order number is ${result.order_id}. Keep this number for order lookup.`;
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
