// VerveLiving&trade; D2C Storefront Controller
const CATALOG = {"schema_version": 2, "currency": "USD", "store_name": "VerveLiving", "domain": "https://shop.askouresystems.com", "merchant_email": "askgsm@live.fr", "support_email": "support@askouresystems.com", "paypal_me": "https://paypal.me/asskoure", "products": [{"id": "furoff", "slug": "furoff-pro", "title": "FurOff Pro Washable Pet Hair Roller", "short_title": "FurOff Pro", "trademark": "FurOff", "categories": ["smart-cleaning-tools", "home-organization"], "primary_category": "smart-cleaning-tools", "badge": "Viral TikTok Favorite", "rating": 4.9, "review_count": 2810, "headline": "Stop buying disposable tape rolls forever.", "short_problem_solved": "Reusable high-tack silicone cylinder instantly lifts stubborn pet hair and lint from velvet, wool, and car seats. Rinse with tap water to reuse for up to 3 years.", "price_usd": 34.99, "compare_at_usd": 59.99, "savings_pct": 42, "shipping_flat_usd": 4.95, "cj_sku": "CJJT174982701AZ", "warehouse_origin": "YunExpress Priority Air (US / UK / EU Hubs)", "eta_days": "7-12 business days", "video_url": "https://video-cf.cjdropshipping.com/4099ed8dcbb271eea17f6733a78e0102/0be7fbf4fd6f4f0b88a7da643458f83d-b40d303f516990964caca85728b60041-ld.mp4", "images": ["/assets/furoff-pro.jpg", "/assets/furoff-2.jpg", "/assets/furoff-3.jpg", "/assets/furoff-4.jpg", "/assets/furoff-5.jpg"], "bundles": [{"qty": 1, "name": "Starter Pack (1x Roller)", "subtext": "Includes Protective Travel Shell", "price": 34.99, "savings": "Retail \\.99", "free_shipping": false}, {"qty": 2, "name": "Duo Pack (Home & Car - 2x)", "subtext": "Free Priority Air Shipping Included", "price": 54.99, "savings": "Save 20% — Most Popular", "free_shipping": true, "popular": true}, {"qty": 3, "name": "Multi-Pet Master Pack (3x)", "subtext": "Free Priority Air Shipping + Priority Dispatch", "price": 74.99, "savings": "Save 30% — Best Value", "free_shipping": true}], "features": ["Zero Disposable Waste: Reusable for 3+ years, saving money on sticky paper rolls.", "15-Second Water Clean: Rinses 100% clean under warm tap water without touching hair.", "Universal Fabric Safe: Gentle on cashmere, wool, velvet, microfiber, and leather car seats.", "Compact Travel Case: Snaps shut to prevent dust accumulation in your purse or glovebox."], "specs": {"Material": "Medical-grade Thermo-Plastic Rubber (TPR) + ABS casing", "Dimensions": "17 cm x 11.5 cm x 6.5 cm", "Weight": "180 g (featherweight)", "Lifespan": "Up to 3 years with normal household use", "Maintenance": "Rinse under warm water; air dry in 60 seconds"}}, {"id": "freshseal", "slug": "freshseal-pro", "title": "FreshSeal Pro 2-in-1 Magnetic Bag Sealer and Cutter", "short_title": "FreshSeal Pro", "trademark": "FreshSeal", "categories": ["kitchen-innovations", "home-organization"], "primary_category": "kitchen-innovations", "badge": "Pantry & Kitchen Must-Have", "rating": 4.9, "review_count": 1850, "headline": "Lock in crisp freshness in 3 seconds. Never eat stale snacks again.", "short_problem_solved": "Tired of flimsy plastic clips and stale chips? High-temperature micro-heating wire creates an instant airtight, leakproof seal across snack bags, cereal, and frozen foods. Built-in precision cutter slices bags cleanly open.", "price_usd": 24.99, "compare_at_usd": 39.99, "savings_pct": 38, "shipping_flat_usd": 4.95, "cj_sku": "CJJT149810201AZ", "warehouse_origin": "YunExpress Priority Air (US / UK / EU Hubs)", "eta_days": "7-12 business days", "video_url": "/assets/freshseal-demo.mp4", "images": ["/assets/freshseal-pro.jpg", "/assets/freshseal-2.jpg", "/assets/freshseal-3.jpg", "/assets/freshseal-4.jpg", "/assets/freshseal-5.jpg"], "bundles": [{"qty": 1, "name": "Single Pack (1x FreshSeal)", "subtext": "Includes USB-C Fast Charger + Test Bags", "price": 24.99, "savings": "Retail \\.99", "free_shipping": false}, {"qty": 2, "name": "Duo Pack (Kitchen + Travel - 2x)", "subtext": "Free Priority Air Shipping Included", "price": 39.99, "savings": "Save 20% — Most Popular", "free_shipping": true, "popular": true}, {"qty": 3, "name": "Home & Pantry Pack (3x)", "subtext": "Free Priority Air Shipping + Priority Dispatch", "price": 54.99, "savings": "Save 30% — Best Value", "free_shipping": true}], "features": ["100% Airtight & Leakproof: Seals in original crispness, preventing food waste.", "2-in-1 Dual Function: One end heat-seals; reverse end slices bags open with hidden blade.", "Magnetic Fridge Mount: Sticks directly to refrigerator door, always within quick reach.", "Universal Bag Compatibility: Works on foil, coated aluminum, PP, PE, and vacuum bags."], "specs": {"Battery": "800 mAh USB-C rechargeable Lithium battery", "Battery Life": "Up to 3 months of daily use on a single 45-minute charge", "Heating Time": "Instant rapid micro-wire heating (under 3 seconds)", "Weight": "110 g ultra-compact handheld design", "Mount": "High-strength magnetic neodymium base"}}]};
let currentProduct = CATALOG.products[0];
let currentBundle = currentProduct.bundles[1] || currentProduct.bundles[0];

// State
function getProductById(id) {
  return CATALOG.products.find(p => p.id === id) || CATALOG.products[0];
}

// Open Product Modal
function openProductModal(productId) {
  const prod = getProductById(productId);
  currentProduct = prod;
  currentBundle = prod.bundles.find(b => b.popular) || prod.bundles[0];

  document.getElementById('modalBadge').textContent = prod.badge;
  document.getElementById('modalTitle').textContent = prod.title;
  document.getElementById('modalRating').innerHTML = `&#9733;&#9733;&#9733;&#9733;&#9733; ${prod.rating} <span>(${prod.review_count.toLocaleString()}+ Verified Buyers)</span>`;
  document.getElementById('modalHeadline').textContent = prod.headline;
  document.getElementById('modalDesc').textContent = prod.short_problem_solved;

  // Render media
  renderMainMedia('video', prod.video_url, prod.images[0]);
  renderThumbnails(prod);

  // Render bundles
  renderBundles(prod);

  // Render specs & features
  renderSpecs(prod);

  // Update sticky
  updateStickyBar(prod, currentBundle);

  document.getElementById('productModalBackdrop').classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeProductModal() {
  document.getElementById('productModalBackdrop').classList.remove('active');
  document.body.style.overflow = '';
  // pause video
  const vid = document.getElementById('modalMainVideo');
  if (vid) vid.pause();
}

function renderMainMedia(type, src, poster) {
  const container = document.getElementById('modalMediaContainer');
  if (type === 'video') {
    container.innerHTML = `
      <video id="modalMainVideo" autoplay loop muted playsinline poster="${poster}">
        <source src="${src}" type="video/mp4">
      </video>
    `;
  } else {
    container.innerHTML = `<img src="${src}" alt="Product View">`;
  }
}

function renderThumbnails(prod) {
  const row = document.getElementById('modalThumbnailsRow');
  let html = `
    <div class="thumb-item active" onclick="switchMedia('video', '${prod.video_url}', this)">
      <img src="${prod.images[0]}" alt="Video Demo">
      <div class="thumb-video-badge">&#9654;</div>
    </div>
  `;
  prod.images.forEach((img, idx) => {
    html += `
      <div class="thumb-item" onclick="switchMedia('image', '${img}', this)">
        <img src="${img}" alt="Angle ${idx+1}">
      </div>
    `;
  });
  row.innerHTML = html;
}

function switchMedia(type, src, el) {
  document.querySelectorAll('#modalThumbnailsRow .thumb-item').forEach(t => t.classList.remove('active'));
  if (el) el.classList.add('active');
  renderMainMedia(type, src, currentProduct.images[0]);
}

function renderBundles(prod) {
  const container = document.getElementById('modalBundlesContainer');
  let html = '';
  prod.bundles.forEach((b, idx) => {
    const isSelected = (b === currentBundle) || (idx === 1 && !currentBundle);
    html += `
      <div class="bundle-option ${isSelected ? 'selected' : ''}" onclick="selectBundle(${idx})">
        ${b.popular ? '<div class="bundle-badge">Most Popular &bull; Save 20%</div>' : ''}
        <div class="bundle-left">
          <input type="radio" name="product-bundle" class="bundle-radio" ${isSelected ? 'checked' : ''}>
          <div>
            <div class="bundle-name">${b.name}</div>
            <div class="bundle-subtext">${b.subtext}</div>
          </div>
        </div>
        <div class="bundle-price-box">
          <div class="bundle-price">$${b.price.toFixed(2)}</div>
          <div class="bundle-savings">${b.savings}</div>
        </div>
      </div>
    `;
  });
  container.innerHTML = html;
}

function selectBundle(idx) {
  currentBundle = currentProduct.bundles[idx];
  document.querySelectorAll('#modalBundlesContainer .bundle-option').forEach((el, i) => {
    const radio = el.querySelector('input');
    if (i === idx) {
      el.classList.add('selected');
      if (radio) radio.checked = true;
    } else {
      el.classList.remove('selected');
      if (radio) radio.checked = false;
    }
  });
  updateStickyBar(currentProduct, currentBundle);
}

function renderSpecs(prod) {
  const featEl = document.getElementById('modalFeaturesList');
  if (featEl) {
    featEl.innerHTML = prod.features.map(f => `<li>${f}</li>`).join('');
  }
  const specsEl = document.getElementById('modalSpecsList');
  if (specsEl) {
    let sHtml = '';
    for (const [k, v] of Object.entries(prod.specs)) {
      sHtml += `<div><strong>${k}:</strong> ${v}</div>`;
    }
    specsEl.innerHTML = sHtml;
  }
}

function toggleAccordion(headerEl) {
  const body = headerEl.nextElementSibling;
  body.classList.toggle('open');
}

// Sticky Bar
function updateStickyBar(prod, bundle) {
  document.getElementById('stickyImg').src = prod.images[0];
  document.getElementById('stickyName').textContent = prod.short_title;
  document.getElementById('stickyPrice').textContent = `$${bundle.price.toFixed(2)}`;
  document.getElementById('stickyBar').classList.add('show');
}

// Checkout Flow
function openCheckoutModal() {
  const form = document.getElementById('checkoutForm');
  if (form) form.style.display = 'block';
  document.getElementById('orderSuccessScreen').classList.remove('active');

  const shippingCost = currentBundle.free_shipping ? 0 : 4.95;
  const total = currentBundle.price + shippingCost;

  document.getElementById('summaryItemName').textContent = `${currentProduct.short_title} &mdash; ${currentBundle.name}`;
  document.getElementById('summarySubtotal').textContent = `$${currentBundle.price.toFixed(2)}`;
  document.getElementById('summaryShipping').textContent = shippingCost === 0 ? 'FREE (Priority Air)' : `$4.95`;
  document.getElementById('summaryTotal').textContent = `$${total.toFixed(2)} USD`;

  document.getElementById('checkoutModalBackdrop').classList.add('active');
}

function closeCheckoutModal() {
  document.getElementById('checkoutModalBackdrop').classList.remove('active');
}

function submitOrder(event) {
  event.preventDefault();

  const name = document.getElementById('custName').value;
  const email = document.getElementById('custEmail').value;
  const phone = document.getElementById('custPhone').value;
  const address = document.getElementById('custAddress').value;
  const city = document.getElementById('custCity').value;
  const zip = document.getElementById('custZip').value;
  const country = document.getElementById('custCountry').value;
  const payMethod = document.getElementById('payMethod').value;

  const orderNum = 'VL-2026-' + Math.floor(10000 + Math.random() * 90000);
  const shippingCost = currentBundle.free_shipping ? 0 : 4.95;
  const total = (currentBundle.price + shippingCost).toFixed(2);

  // Show Success Screen
  document.getElementById('checkoutForm').style.display = 'none';
  const successEl = document.getElementById('orderSuccessScreen');
  successEl.classList.add('active');

  document.getElementById('confirmedOrderNum').textContent = orderNum;
  document.getElementById('confirmedItem').textContent = `${currentProduct.title} (${currentBundle.name})`;
  document.getElementById('confirmedTotal').textContent = `$${total} USD`;
  document.getElementById('confirmedAddress').textContent = `${name}, ${address}, ${city}, ${zip}, ${country}`;

  // Set PayPal Button link
  const ppBtn = document.getElementById('payNowBtn');
  if (payMethod === 'paypal') {
    ppBtn.href = `${CATALOG.paypal_me}/${total}USD`;
    ppBtn.style.display = 'inline-flex';
  } else {
    ppBtn.style.display = 'none';
  }

  // Send asynchronous intake request
  try {
    fetch('/api/orders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        order_id: orderNum,
        product_id: currentProduct.id,
        bundle_name: currentBundle.name,
        total_usd: total,
        customer_name: name,
        customer_email: email,
        customer_phone: phone,
        shipping_address: address,
        city: city,
        country: country
      })
    }).catch(() => {});
  } catch(e) {}
}

// Filter tabs on home page
function filterCategory(cat, btnEl) {
  document.querySelectorAll('.filter-tab').forEach(b => b.classList.remove('active'));
  if (btnEl) btnEl.classList.add('active');

  const cards = document.querySelectorAll('.product-card');
  cards.forEach(card => {
    const cardCats = card.getAttribute('data-categories') || '';
    if (cat === 'all' || cardCats.includes(cat)) {
      card.style.display = 'flex';
    } else {
      card.style.display = 'none';
    }
  });
}

// Auto-bind hash
window.addEventListener('DOMContentLoaded', () => {
  const hash = window.location.hash.replace('#', '');
  if (['furoff', 'neck', 'knee', 'freshseal'].includes(hash)) {
    openProductModal(hash);
  }
});
