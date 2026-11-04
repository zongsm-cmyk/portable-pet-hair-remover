import catalog from '../catalog.generated.json' with { type: 'json' };

import launchOffer from '../launch-offer.json' with { type: 'json' };

const launchStates = new Set('AL AZ AR CA CO CT DE DC FL GA ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split(' '));

class HttpError extends Error {
  constructor(status, code) { super(code); this.status = status; this.code = code; }
}
const fail = (status, code) => { throw new HttpError(status, code); };
const json = (data, status = 200) => new Response(JSON.stringify(data), {status, headers:{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','Referrer-Policy':'no-referrer','X-Content-Type-Options':'nosniff'}});
const cents = n => typeof n === 'number' && Number.isFinite(n) && n >= 0 && Math.abs(n * 100 - Math.round(n * 100)) < 1e-6 ? Math.round(n * 100) : fail(422, 'invalid_catalog_money');
const usd = n => (n / 100).toFixed(2);
const validId = s => typeof s === 'string' && /^[A-Za-z0-9-]{8,80}$/.test(s);
const emailKey = s => typeof s === 'string' ? s.trim().toLowerCase() : '';
const query = (db, sql, ...args) => db.prepare(sql).bind(...args);
const paypalBase = env => env.PAYPAL_ENV === 'live' ? 'https://api-m.paypal.com' : env.PAYPAL_ENV === 'sandbox' ? 'https://api-m.sandbox.paypal.com' : fail(503, 'paypal_environment_unconfigured');

const APPROVED_SUPPLIER_HOSTS = Object.freeze({
  cj: 'cjdropshipping.com',
  eprolo: 'eprolo.com',
  hypersku: 'hypersku.com',
  wiio: 'wiio.io'
});
export function sourceFor(p) {
  // Legacy CJ listings remain supported; new supplier routes require explicit verified fields.
  const raw = p?.fulfillment_provider === undefined
    ? {id:'cj', sku:p?.cj_sku, variant_id:p?.cj_variant_id, product_url:p?.cj_product_url}
    : p.fulfillment_provider;
  if (!raw || typeof raw !== 'object') fail(422, 'product_not_verified');
  const host = APPROVED_SUPPLIER_HOSTS[raw.id];
  let url;
  try { url = new URL(raw.product_url); } catch { /* Invalid supplier link must fail. */ }
  if (!host || !raw.sku || !raw.variant_id || typeof raw.sku !== 'string' ||
      typeof raw.variant_id !== 'string' || url?.protocol !== 'https:' ||
      url.username || url.password ||
      !(url.hostname === host || url.hostname.endsWith('.' + host)))
    fail(422, 'product_not_verified');
  return {id:raw.id,sku:raw.sku,variant_id:raw.variant_id,url:raw.product_url};
}


export function quote(items, country, products = catalog.products) {
  if (!['US','GB'].includes(country) || !Array.isArray(items) || items.length < 1 || items.length > 15) fail(422, 'invalid_cart');
  const seen = new Set();
  let total = 0;
  const lines = items.map(item => {
    if (!item || seen.has(item.id) || !Number.isInteger(item.quantity) || item.quantity < 1 || item.quantity > 10) fail(422, 'invalid_cart');
    seen.add(item.id);
    const p = products.find(p => p.id === item.id);
    if (item.id === launchOffer.id && country !== 'US')
      fail(422, 'launch_offer_us_only');
    const suffix = country === 'US' ? 'us' : 'uk';
    const source = sourceFor(p);
    const verifiedAt = Date.parse(p?.supplier_verified_at);
    if (!p || p.verified_for_checkout !== true || !p.warehouse_origin ||
        !p[`eta_${suffix}_days`] || typeof p[`shipping_${suffix}_usd`] !== 'number' ||
        typeof p.supplier_cost_usd !== 'number' || p.stock_status !== 'in_stock' ||
        !Number.isFinite(verifiedAt) || verifiedAt > Date.now() ||
        Date.now()-verifiedAt > 7*86400000 ||
        !(p.specs?.weight_g > 0 && p.specs.weight_g < 500) ||
        p.specs.contains_lithium !== false ||
        p.specs.contains_liquid !== false || p.specs.medical !== false)
      fail(422, 'product_not_verified');
    cents(p.supplier_cost_usd);
    const eta = /^(\d{1,2})\s*-\s*(\d{1,2})\s+(?:business\s+)?days$/.exec(p[`eta_${suffix}_days`]);
    if (!eta || +eta[1] < 1 || +eta[2] < +eta[1] ||  +eta[2] > 12) fail(422,'delivery_not_qualified');
    cents(p[`shipping_${suffix}_usd`]);
    const unit = cents(p.price_usd);
    const shipping = cents(p[`customer_shipping_${suffix}_usd`] ?? 0);
    if (!unit) fail(422, 'invalid_catalog_money');
    total += (unit + shipping) * item.quantity;
    return {id:p.id, title:p.title, supplier_id:source.id, supplier_sku:source.sku, supplier_variant_id:source.variant_id, cj_sku:source.id==='cj' ? source.sku : null, cj_variant_id:source.id==='cj' ? source.variant_id : null, quantity:item.quantity, unit_cents:unit, shipping_cents:shipping};
  });
  if (new Set(lines.map(line=>line.supplier_id)).size > 1) fail(422, 'mixed_supplier_cart_requires_separate_orders');
  if (total > 200000) fail(422, 'cart_limit_exceeded');
  return {items:lines, country, total_cents:total};
}

async function readBody(request) {
  if (!request.headers.get('Content-Type')?.startsWith('application/json')) fail(415, 'json_required');
  const reader = request.body?.getReader();
  if (!reader) fail(400, 'invalid_json');
  let size = 0, chunks = [];
  while (true) {
    const {done, value} = await reader.read();
    if (done) break;
    size += value.length;
    if (size > 16384) { await reader.cancel(); fail(413,'body_too_large'); }
    chunks.push(value);
  }
  const buffer = new Uint8Array(size); let offset = 0;
  for (const chunk of chunks) { buffer.set(chunk, offset); offset += chunk.length; }
  try { return JSON.parse(new TextDecoder().decode(buffer)); } catch { fail(400, 'invalid_json'); }
}

function checkoutGate(env) {
  if (env.CHECKOUT_ENABLED !== 'true') fail(503, 'checkout_disabled');
  if (!env.DB || !env.PAYPAL_CLIENT_ID || !env.PAYPAL_CLIENT_SECRET || !env.PAYPAL_MERCHANT_ID) fail(503, 'checkout_unconfigured');
  paypalBase(env);
}

async function paypal(env, path, method = 'GET', body, requestId) {
  const transport = env.TEST_FETCH || fetch;
  const tokenResponse = await transport(paypalBase(env) + '/v1/oauth2/token', {
    method:'POST', headers:{Authorization:'Basic ' + btoa(env.PAYPAL_CLIENT_ID + ':' + env.PAYPAL_CLIENT_SECRET),'Content-Type':'application/x-www-form-urlencoded'}, body:'grant_type=client_credentials', signal:AbortSignal.timeout(15000)
  });
  if (!tokenResponse.ok) fail(502, 'paypal_unavailable');
  const token = await tokenResponse.json();
  if (!token.access_token) fail(502, 'paypal_unavailable');
  const response = await transport(paypalBase(env) + path, {method, headers:{Authorization:'Bearer ' + token.access_token, 'Content-Type':'application/json', Prefer:'return=representation', ...(requestId ? {'PayPal-Request-Id':requestId} : {})}, ...(body === undefined ? {} : {body:JSON.stringify(body)}), signal:AbortSignal.timeout(20000)});
  if (!response.ok) fail(502, 'paypal_unavailable');
  return response.json();
}

async function create(request, env, products) {
  checkoutGate(env);
  await rateLimit(request,env,'create',10);
  const body = await readBody(request), cart = quote(body.items, body.country, products);
  const isLaunchOffer = cart.items.some(item => item.id === launchOffer.id);
  const phone = isLaunchOffer ? body.delivery_phone : null;
  if (isLaunchOffer && (typeof phone !== 'string' || !/^\+1[2-9]\d{2}[2-9]\d{6}$/.test(phone)))
    fail(422,'valid_us_delivery_phone_required');
  const id = crypto.randomUUID(), now = new Date().toISOString();
  await query(env.DB, 'INSERT INTO checkout_intents (order_id,country,items_json,total_cents,state,created_at) VALUES (?,?,?,?,?,?)', id, cart.country, JSON.stringify(cart.items), cart.total_cents, 'creating', now).run();
  if (isLaunchOffer) await query(env.DB, 'UPDATE checkout_intents SET delivery_phone=? WHERE order_id=?', phone, id).run();
  const order = await paypal(env, '/v2/checkout/orders', 'POST', {
    intent:'CAPTURE', purchase_units:[{reference_id:id,custom_id:id,invoice_id:id,payee:{merchant_id:env.PAYPAL_MERCHANT_ID},amount:{currency_code:'USD',value:usd(cart.total_cents)}}],
    payment_source:{paypal:{experience_context:{brand_name:'VerveLiving',shipping_preference:'GET_FROM_FILE',user_action:'PAY_NOW',return_url:env.STOREFRONT_ORIGIN + '/checkout/return/',cancel_url:env.STOREFRONT_ORIGIN + '/checkout/cancel/'}}}
  }, id);
  if (!validId(order.id)) fail(502,'paypal_invalid_response');
  await query(env.DB, 'UPDATE checkout_intents SET paypal_order_id=?,state=? WHERE order_id=?', order.id, 'awaiting_approval', id).run();
  const approval = (order.links || []).find(l => ['payer-action','approve'].includes(l.rel))?.href;
  return json({order_id:id,paypal_order_id:order.id,approval_url:approval || null,total_usd:usd(cart.total_cents),currency:'USD'}, 201);
}

export function verifyPayment(order, intent, merchant) {
  if (order.id !== intent.paypal_order_id || order.status !== 'COMPLETED' || order.intent !== 'CAPTURE' || order.purchase_units?.length !== 1) fail(422,'payment_not_completed');
  const unit = order.purchase_units[0], captures = unit.payments?.captures;
  if (unit.custom_id !== intent.order_id || unit.reference_id !== intent.order_id || unit.payee?.merchant_id !== merchant || captures?.length !== 1) fail(422,'payment_reference_mismatch');
  const capture = captures[0];
  if (!capture.id || capture.status !== 'COMPLETED' || capture.amount?.currency_code !== 'USD' || capture.amount?.value !== usd(intent.total_cents) || unit.amount?.currency_code !== 'USD' || unit.amount?.value !== usd(intent.total_cents)) fail(422,'payment_amount_mismatch');
  const shipping = unit.shipping;
  if (shipping?.address?.country_code !== intent.country || !shipping.address.address_line_1 || !shipping.address.admin_area_2 || !shipping.address.postal_code || !shipping.name?.full_name || !emailKey(order.payer?.email_address)) fail(422,'payment_shipping_mismatch');
  return {capture, shipping, email:emailKey(order.payer.email_address)};
}

async function capture(request, env, products) {
  checkoutGate(env);
  const body = await readBody(request);
  if (!validId(body.paypal_order_id)) fail(422,'invalid_paypal_order_id');
  const intent = await query(env.DB, 'SELECT * FROM checkout_intents WHERE paypal_order_id=?', body.paypal_order_id).first();
  if (!intent) fail(404,'checkout_not_found');
  // Replays return the original receipt; they never re-capture or create another order.
  const saved = await query(env.DB, 'SELECT order_id,paypal_capture_id FROM orders WHERE paypal_order_id=?', body.paypal_order_id).first();
  if (saved) return json({order_id:saved.order_id,payment_status:'COMPLETED',already_recorded:true});
  let order = await paypal(env, '/v2/checkout/orders/' + encodeURIComponent(body.paypal_order_id));
  if (order.status === 'APPROVED') {
    if (order.id !== body.paypal_order_id) fail(422,'approval_mismatch');
    if (Date.now()-Date.parse(intent.created_at) > 30*60*1000) fail(409,'checkout_expired');
    const snapshot = JSON.parse(intent.items_json);
    const current = quote(snapshot.map(line=>({id:line.id,quantity:line.quantity})),intent.country,products);
    if (current.total_cents !== intent.total_cents || current.items.some((line,index)=>line.supplier_id!==snapshot[index].supplier_id || line.supplier_sku!==snapshot[index].supplier_sku || line.supplier_variant_id!==snapshot[index].supplier_variant_id || line.unit_cents!==snapshot[index].unit_cents || line.shipping_cents!==snapshot[index].shipping_cents)) fail(409,'checkout_quote_changed');
    // Validate merchant, reference, amount and destination BEFORE capturing funds.
    const unit = order.purchase_units?.[0];
    if (order.intent !== 'CAPTURE' || order.purchase_units?.length !== 1 || unit?.custom_id !== intent.order_id || unit?.reference_id !== intent.order_id || unit?.payee?.merchant_id !== env.PAYPAL_MERCHANT_ID || unit?.amount?.currency_code !== 'USD' || unit?.amount?.value !== usd(intent.total_cents) || unit?.shipping?.address?.country_code !== intent.country) fail(422,'approval_mismatch');
    const address = unit.shipping?.address;
    if (!address?.address_line_1 || !address.admin_area_2 || !address.postal_code || !unit.shipping?.name?.full_name || !emailKey(order.payer?.email_address)) fail(422,'approval_shipping_incomplete');
    if (snapshot.some(item => item.id === launchOffer.id)) {
      if (!launchStates.has(address.admin_area_1) || !/^\d{5}(?:-\d{4})?$/.test(address.postal_code))
        fail(422,'launch_offer_contiguous_us_only');
    }
    await paypal(env, '/v2/checkout/orders/' + encodeURIComponent(body.paypal_order_id) + '/capture', 'POST', {}, 'cap-' + intent.order_id.replaceAll('-',''));
    order = await paypal(env, '/v2/checkout/orders/' + encodeURIComponent(body.paypal_order_id));
  }
  const checked = verifyPayment(order, intent, env.PAYPAL_MERCHANT_ID);
  const items = JSON.parse(intent.items_json), first = items[0];
  await env.DB.batch([
    query(env.DB, `INSERT INTO orders (order_id,paypal_order_id,paypal_capture_id,customer_name,email,shipping_address,items_json,cj_sku,cj_variant_id,quantity,total_paid_usd,payment_status,created_at,supplier_id,supplier_sku,supplier_variant_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(order_id) DO NOTHING`, intent.order_id, body.paypal_order_id, checked.capture.id, checked.shipping.name.full_name, checked.email, JSON.stringify({...checked.shipping.address,...(intent.delivery_phone ? {phone:intent.delivery_phone} : {})}), intent.items_json, first.cj_sku || '', first.cj_variant_id || '', items.reduce((n,i)=>n+i.quantity,0), usd(intent.total_cents), 'COMPLETED', new Date().toISOString(),first.supplier_id,first.supplier_sku,first.supplier_variant_id),
    query(env.DB, 'UPDATE checkout_intents SET state=? WHERE order_id=?', 'paid', intent.order_id)
  ]);
  return json({order_id:intent.order_id,payment_status:'COMPLETED',fulfillment_status:'unfulfilled'});
}

async function admin(request, env) {
  if (!env.ADMIN_TOKEN || env.ADMIN_TOKEN.length < 24) fail(503, 'admin_unconfigured');
  const given = request.headers.get('Authorization') || '';
  const left = new TextEncoder().encode(given), right = new TextEncoder().encode('Bearer ' + env.ADMIN_TOKEN);
  const l = new Uint8Array(await crypto.subtle.digest('SHA-256',left)), r = new Uint8Array(await crypto.subtle.digest('SHA-256',right));
  let diff = 0; for (let i=0;i<l.length;i++) diff |= l[i]^r[i];
  if (diff) fail(401, 'unauthorized');
  if (!env.DB) fail(503,'database_unconfigured');
}

async function fulfillment(request,env) {
  await admin(request,env);
  const body = await readBody(request);
  if (!validId(body.order_id) || !['shipped','delivered'].includes(body.fulfillment_status) || typeof body.tracking_number!=='string' || !/^[A-Za-z0-9][A-Za-z0-9-]{4,99}$/.test(body.tracking_number) || typeof body.tracking_carrier!=='string' || !/^[A-Za-z][A-Za-z0-9 ._-]{1,60}$/.test(body.tracking_carrier)) fail(422,'invalid_fulfillment_update');
  const order = await query(env.DB,"SELECT order_id,fulfillment_status FROM orders WHERE order_id=? AND payment_status='COMPLETED'",body.order_id).first();
  if (!order) fail(404,'paid_order_not_found');
  if (order.fulfillment_status==='delivered' && body.fulfillment_status!=='delivered') fail(409,'fulfillment_regression');
  await query(env.DB,"UPDATE orders SET fulfillment_status=?,tracking_number=?,tracking_carrier=? WHERE order_id=? AND payment_status='COMPLETED'",body.fulfillment_status,body.tracking_number,body.tracking_carrier,body.order_id).run();
  return json({order_id:body.order_id,fulfillment_status:body.fulfillment_status,tracking_number:body.tracking_number,tracking_carrier:body.tracking_carrier,external_notifications_sent:false});
}

async function orderOperations(request, env, url) {
  await admin(request, env);
  const orderId = url.searchParams.get('order_id');
  if (!validId(orderId)) fail(422, 'invalid_order_id');
  const row = await query(env.DB, `SELECT o.order_id,o.paypal_capture_id,o.total_paid_usd,o.fulfillment_status,
    h.claimed_at,h.supplier_reference FROM orders o LEFT JOIN supplier_handoffs h USING(order_id)
    WHERE o.order_id=?`, orderId).first();
  if (!row) fail(404, 'paid_order_not_found');
  return json(row);
}

async function supplierHandoff(request, env) {
  await admin(request, env);
  const body = await readBody(request);
  if (!validId(body?.order_id)) fail(422, 'invalid_order_id');

  if (body.supplier_reference !== undefined) {
    if (typeof body.supplier_reference !== 'string' || !/^[A-Za-z0-9-]{3,80}$/.test(body.supplier_reference)) fail(422, 'invalid_supplier_reference');
    const saved = await query(env.DB, `UPDATE supplier_handoffs SET supplier_reference=?
      WHERE order_id=? AND (supplier_reference IS NULL OR supplier_reference=?) RETURNING supplier_reference`,
      body.supplier_reference, body.order_id, body.supplier_reference).first();
    if (!saved) fail(409, 'supplier_handoff_not_claimed_or_reference_changed');
    return json({order_id:body.order_id, supplier_reference:saved.supplier_reference});
  }

  const claimed = await query(env.DB, `INSERT INTO supplier_handoffs(order_id,claimed_at)
    SELECT order_id,? FROM orders WHERE order_id=? AND payment_status='COMPLETED'
      AND fulfillment_status='unfulfilled' AND supplier_id='cj'
    ON CONFLICT(order_id) DO NOTHING RETURNING order_id`, new Date().toISOString(), body.order_id).first();
  if (!claimed) fail(409, 'supplier_handoff_unavailable');
  return json({order_id:claimed.order_id, supplier_order_created:false}, 201);
}

export function csvCell(value) {
  let str = value == null ? '' : String(value);
  if (/^[\s]*[=+@-]/.test(str)) str = "'" + str;
  return '"' + str.replaceAll('"','""') + '"';
}

async function exportCsv(request, env) {
  await admin(request, env);
  let template;
  try { template = JSON.parse(env.CJ_TEMPLATE_JSON || 'null'); } catch { fail(503,'cj_template_unverified'); }
  const allowed = new Set(['order_id','customer_name','email','address_line_1','address_line_2','city','state','postcode','country','cj_sku','cj_variant_id','quantity','total_paid_usd','phone']);
  if (!template?.verified_at || !template.source_url?.startsWith('https://') || !Array.isArray(template.columns) || !template.columns.length || template.columns.some(c=>typeof c.header!=='string'||!allowed.has(c.field))) fail(503,'cj_template_unverified');
  const result = await query(env.DB, "SELECT * FROM orders WHERE payment_status='COMPLETED' AND fulfillment_status='unfulfilled' AND supplier_id='cj' AND order_id NOT IN (SELECT order_id FROM supplier_handoffs) ORDER BY created_at LIMIT 501").all();
  if (result.results.length > 500) fail(409,'export_batch_too_large');
  const rows = [template.columns.map(c=>csvCell(c.header)).join(',')];
  for (const order of result.results) {
    const address = JSON.parse(order.shipping_address);
    for (const item of JSON.parse(order.items_json)) {
      const record = {...order,...item,address_line_1:address.address_line_1,address_line_2:address.address_line_2,city:address.admin_area_2,state:address.admin_area_1,postcode:address.postal_code,country:address.country_code,phone:address.phone || ''};
      if (template.columns.some(c=>c.required && (record[c.field] == null || String(record[c.field]).trim()===''))) fail(409,'cj_required_data_missing');
      rows.push(template.columns.map(c=>csvCell(record[c.field])).join(','));
    }
  }
  return new Response('\uFEFF' + rows.join('\r\n') + '\r\n', {headers:{'Content-Type':'text/csv; charset=utf-8','Content-Disposition':'attachment; filename="cj-unfulfilled.csv"','Cache-Control':'no-store'}});
}


async function exportSupplierJson(request,env,url) {
  await admin(request,env);
  const provider = url.searchParams.get('provider');
  if (!['cj','eprolo','hypersku','wiio'].includes(provider)) fail(422,'invalid_supplier');
  const result = await query(env.DB, "SELECT * FROM orders WHERE payment_status='COMPLETED' AND fulfillment_status='unfulfilled' AND supplier_id=? AND order_id NOT IN (SELECT order_id FROM supplier_handoffs) ORDER BY created_at LIMIT 501",provider).all();
  if (result.results.length > 500) fail(409,'export_batch_too_large');
  return json({provider,format:'owner_manual_order_entry_v1',orders:result.results.map(o=>({
    order_id:o.order_id,customer_name:o.customer_name,email:o.email,
    shipping_address:JSON.parse(o.shipping_address),
    items:JSON.parse(o.items_json).filter(i=>i.supplier_id===provider),
    total_paid_usd:o.total_paid_usd,fulfillment_status:o.fulfillment_status
  }))});
}

async function rateLimit(request,env,scope,limit) {
  // D1-backed bounded lookup attempts; no plaintext email/IP is retained in rate-limit keys.
  const ip = request.headers.get('CF-Connecting-IP') || 'local';
  const hash = [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(ip)))].map(x=>x.toString(16).padStart(2,'0')).join('');
  const now = Math.floor(Date.now()/1000), key = scope + ':' + hash + ':' + Math.floor(now/600);
  await query(env.DB, 'INSERT INTO lookup_limits(key,count,expires_at) VALUES (?,1,?) ON CONFLICT(key) DO UPDATE SET count=count+1', key, now+600).run();
  const rate = await query(env.DB, 'SELECT count FROM lookup_limits WHERE key=?', key).first();
  if (rate.count > limit) fail(429,scope+'_rate_limited');
}

async function track(request, env, url) {
  if (!env.DB) fail(503,'database_unconfigured');
  await rateLimit(request,env,'lookup',20);
  const body = request.method === 'POST' ? await readBody(request) : Object.fromEntries(url.searchParams);
  const email = emailKey(body.email);
  if (!validId(body.order_id) || !email || email.length > 254) fail(404,'order_not_found');
  const order = await query(env.DB, 'SELECT order_id,fulfillment_status,tracking_number,tracking_carrier FROM orders WHERE order_id=? AND email=?', body.order_id, email).first();
  if (!order) fail(404,'order_not_found');
  return json(order);
}

export function makeWorker(products = [...catalog.products, launchOffer]) {
  return {
    async fetch(request, env) {
      try {
        const url = new URL(request.url);
        const origin = request.headers.get('Origin');
        if (origin && origin !== env.STOREFRONT_ORIGIN) fail(403,'origin_forbidden');
        if (request.method === 'OPTIONS') return new Response(null,{status:204,headers:{'Access-Control-Allow-Origin':env.STOREFRONT_ORIGIN,'Access-Control-Allow-Methods':'GET, POST, OPTIONS','Access-Control-Allow-Headers':'Content-Type, Authorization','Vary':'Origin'}});
        if (url.pathname === '/api/health' && request.method === 'GET') {
          const enabled = env.CHECKOUT_ENABLED === 'true';
          const health = {status:'ok',checkout_enabled:enabled,mode:env.PAYPAL_ENV || 'unconfigured'};
          if (enabled && env.PAYPAL_ENV === 'live' && products.some(product => product.id === launchOffer.id)) {
            const age = Date.now() - Date.parse(launchOffer.supplier_verified_at);
            health.launch_offer_available = age >= 0 && age <= 7 * 86400000 && !!env.DB;
          }
          return json(health);
        }
        if (url.pathname === '/api/orders/create' && request.method === 'POST') return await create(request,env,products);
        if (url.pathname === '/api/orders/capture' && request.method === 'POST') return await capture(request,env,products);
        if (url.pathname === '/api/orders/operations' && request.method === 'GET') return await orderOperations(request,env,url);
        if (url.pathname === '/api/orders/supplier-handoff' && request.method === 'POST') return await supplierHandoff(request,env);
        if (url.pathname === '/api/orders/fulfillment' && request.method === 'POST') return await fulfillment(request,env);
        if (url.pathname === '/api/orders/export-cj-csv' && request.method === 'GET') return await exportCsv(request,env);
        if (url.pathname === '/api/orders/export-supplier-json' && request.method === 'GET') return await exportSupplierJson(request,env,url);
        if (url.pathname === '/api/orders/track' && ['GET','POST'].includes(request.method)) return await track(request,env,url);
        return json({error:'not_found'},404);
      } catch (error) {
        return json({error:error instanceof HttpError ? error.code : 'service_unavailable'}, error instanceof HttpError ? error.status : 503);
      }
    },
    async scheduled(_event,env) { if (env.DB) await query(env.DB,'DELETE FROM lookup_limits WHERE expires_at<?',Math.floor(Date.now()/1000)).run(); }
  };
}
export default makeWorker();
