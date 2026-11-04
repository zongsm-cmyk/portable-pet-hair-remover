import {test} from 'node:test';
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
import {makeWorker,quote,sourceFor,verifyPayment,csvCell} from '../src/index.mjs';

const product = () => ({id:'furoff',title:'FurOff',price_usd:34.99,verified_for_checkout:true,cj_sku:'CJ-TEST',cj_variant_id:'VARIANT-TEST',cj_product_url:'https://cjdropshipping.com/product/test',warehouse_origin:'CN',supplier_cost_usd:2,shipping_us_usd:5,shipping_uk_usd:6,eta_us_days:'8-12 business days',eta_uk_days:'8-12 business days',stock_status:'in_stock',supplier_verified_at:new Date().toISOString(),specs:{weight_g:301,contains_lithium:false,contains_liquid:false,medical:false}});
const req = (path, body, headers={}) => new Request('https://shop.askouresystems.com'+path,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json',...headers},...(body===undefined?{}:{body:JSON.stringify(body)})});
function db() {
  const sqlite = new DatabaseSync(':memory:');
  sqlite.exec(readFileSync(new URL('../migrations/0001_orders.sql',import.meta.url),'utf8'));
  sqlite.exec(readFileSync(new URL('../migrations/0002_multi_supplier.sql',import.meta.url),'utf8'));
  sqlite.exec(readFileSync(new URL('../migrations/0003_supplier_handoff.sql',import.meta.url),'utf8'));
  sqlite.exec(readFileSync(new URL('../migrations/0004_launch_order_claim.sql',import.meta.url),'utf8'));
  const prepare = (sql) => ({bind(...args){return {async run(){return sqlite.prepare(sql).run(...args);},async first(){return sqlite.prepare(sql).get(...args)||null;},async all(){return {results:sqlite.prepare(sql).all(...args)};},sql,args};}});
  return {sqlite,prepare,async batch(statements){sqlite.exec('BEGIN');try{const result=[];for(const s of statements)result.push(await s.run());sqlite.exec('COMMIT');return result;}catch(e){sqlite.exec('ROLLBACK');throw e;}}};
}
function environment() {
  const env={DB:db(),CHECKOUT_ENABLED:'true',PAYPAL_ENV:'sandbox',STOREFRONT_ORIGIN:'https://shop.askouresystems.com',PAYPAL_CLIENT_ID:'test-id',PAYPAL_CLIENT_SECRET:'test-secret',PAYPAL_MERCHANT_ID:'MERCHANT-TEST',ADMIN_TOKEN:'abcdefghijklmnopqrstuvwxyz0123456789'};
  let order, captureCalls=0, lastCreate, lastCaptureKey;
  env.TEST_FETCH = async (url, options) => {
    if(url.endsWith('/v1/oauth2/token'))return Response.json({access_token:'test-token'});
    if(url.endsWith('/v2/checkout/orders') && options.method==='POST') {
      lastCreate=JSON.parse(options.body);
      order={id:'PAYPAL-ORDER-123',intent:'CAPTURE',status:'APPROVED',purchase_units:lastCreate.purchase_units,payer:{email_address:'Buyer@Example.com'}};
      order.purchase_units[0].shipping={name:{full_name:'Buyer Example'},address:{address_line_1:'1 Main St',admin_area_2:'New York',admin_area_1:'NY',postal_code:'10001',country_code:'US'}};
      return Response.json({...order,links:[{rel:'payer-action',href:'https://www.sandbox.paypal.com/checkoutnow?token=TEST'}]});
    }
    if(url.endsWith('/capture')){
      captureCalls++;lastCaptureKey=options.headers['PayPal-Request-Id'];
      order.status='COMPLETED';order.purchase_units[0].payments={captures:[{id:'CAPTURE-123',status:'COMPLETED',amount:{currency_code:'USD',value:order.purchase_units[0].amount.value}}]};
      return Response.json(order);
    }
    return Response.json(order);
  };
  return {env,get order(){return order;},get captureCalls(){return captureCalls;},get lastCreate(){return lastCreate;},get lastCaptureKey(){return lastCaptureKey;}};
}

test('quote rejects unverified/missing supplier/stale evidence and dangerous products',()=>{
  for(const patch of [{verified_for_checkout:false},{cj_variant_id:null},{cj_product_url:'https://evil.test/cj'},{supplier_verified_at:'2020-01-01'},{stock_status:'unknown'},{specs:{weight_g:500}},{shipping_us_usd:null}])assert.throws(()=>quote([{id:'furoff',quantity:1}],'US',[{...product(),...patch}]));
});
test('quote uses only authoritative product prices; supplier shipping is not double charged',()=>{
  const q=quote([{id:'furoff',quantity:2,price_usd:0.01}],'US',[product()]);assert.equal(q.total_cents,6998);
  assert.equal(quote([{id:'furoff',quantity:1}],'GB',[{...product(),customer_shipping_uk_usd:3}]).total_cents,3799);
});
test('quote rejects fractional/negative quantities, duplicates and unsupported country',()=>{
  for(const quantity of [0,-1,1.1,11,'1'])assert.throws(()=>quote([{id:'furoff',quantity}],'US',[product()]));
  assert.throws(()=>quote([{id:'furoff',quantity:1},{id:'furoff',quantity:1}],'US',[product()]));
  assert.throws(()=>quote([{id:'furoff',quantity:1}],'CA',[product()]));
});
test('global payment gate stays disabled without explicit environment activation',async()=>{
  const response=await makeWorker([product()]).fetch(req('/api/orders/create',{items:[{id:'furoff',quantity:1}],country:'US'}),{});assert.equal(response.status,503);assert.equal((await response.json()).error,'checkout_disabled');
});

test('deployed disabled configuration rejects create and capture before any DB or provider access',async()=>{
  const config = readFileSync(new URL('../wrangler.toml',import.meta.url),'utf8');
  assert.match(config,/CHECKOUT_ENABLED\s*=\s*"false"/);
  assert.match(config,/PAYPAL_ENV\s*=\s*"sandbox"/);
  const products = JSON.parse(readFileSync(new URL('../catalog.generated.json',import.meta.url),'utf8')).products;
  assert.equal(products.length,15);
  assert.ok(products.every(p=>p.verified_for_checkout===false));
  let calls = 0;
  const deny = ()=>{calls++;throw new Error('disabled checkout touched a service');};
  const env = {CHECKOUT_ENABLED:'false',PAYPAL_ENV:'sandbox',DB:{prepare:deny,batch:deny},TEST_FETCH:deny};
  for (const path of ['/api/orders/create','/api/orders/capture']) {
    const response = await makeWorker(products).fetch(req(path,{}),env);
    assert.equal(response.status,503);
    assert.equal((await response.json()).error,'checkout_disabled');
  }
  assert.equal(calls,0);
});
test('untrusted origin and invalid JSON rejected',async()=>{
  const {env}=environment(), worker=makeWorker([product()]);
  assert.equal((await worker.fetch(req('/api/orders/create',{}, {Origin:'https://evil.test'}),env)).status,403);
  assert.equal((await worker.fetch(new Request('https://shop.askouresystems.com/api/orders/create',{method:'POST',body:'broken',headers:{'Content-Type':'application/json'}}),env)).status,400);
});
test('create, approve, capture, persist and replay full mocked flow',async()=>{
  const fixture=environment(),worker=makeWorker([product()]);
  let response=await worker.fetch(req('/api/orders/create',{items:[{id:'furoff',quantity:2}],country:'US'}),fixture.env);assert.equal(response.status,201);const created=await response.json();
  assert.equal(fixture.lastCreate.purchase_units[0].amount.value,'69.98');
  response=await worker.fetch(req('/api/orders/capture',{paypal_order_id:created.paypal_order_id,items:[{id:'cheap-fake',quantity:100}]}),fixture.env);assert.equal(response.status,200);const result=await response.json();assert.equal(result.order_id,created.order_id);
  const row=fixture.env.DB.sqlite.prepare('SELECT * FROM orders').get();assert.equal(row.total_paid_usd,'69.98');assert.equal(row.email,'buyer@example.com');assert.equal(row.cj_sku,'CJ-TEST');assert.equal(row.quantity,2);assert.equal(row.fulfillment_status,'unfulfilled');
  assert.equal(fixture.captureCalls,1);assert.ok(fixture.lastCaptureKey.length<=38);
  response=await worker.fetch(req('/api/orders/capture',{paypal_order_id:created.paypal_order_id}),fixture.env);assert.equal((await response.json()).already_recorded,true);assert.equal(fixture.captureCalls,1);assert.equal(fixture.env.DB.sqlite.prepare('SELECT count(*) AS n FROM orders').get().n,1);
});
test('wrong amount, merchant, destination or reference never captures funds',async()=>{
  for(const mutate of [o=>o.purchase_units[0].amount.value='0.01',o=>o.purchase_units[0].payee.merchant_id='WRONG',o=>o.purchase_units[0].shipping.address.country_code='GB',o=>o.purchase_units[0].custom_id='WRONG']){
    const f=environment(),w=makeWorker([product()]);const created=await (await w.fetch(req('/api/orders/create',{items:[{id:'furoff',quantity:1}],country:'US'}),f.env)).json();mutate(f.order);
    assert.equal((await w.fetch(req('/api/orders/capture',{paypal_order_id:created.paypal_order_id}),f.env)).status,422);assert.equal(f.captureCalls,0);assert.equal(f.env.DB.sqlite.prepare('SELECT count(*) AS n FROM orders').get().n,0);
  }
});
test('top-level completed with pending capture is rejected',()=>{
  assert.throws(()=>verifyPayment({id:'PAYPAL-ORDER-123',intent:'CAPTURE',status:'COMPLETED',purchase_units:[{custom_id:'order-id',reference_id:'order-id',payee:{merchant_id:'MERCHANT'},payments:{captures:[{id:'C',status:'PENDING'}]}}]}, {paypal_order_id:'PAYPAL-ORDER-123',order_id:'order-id',total_cents:3499},'MERCHANT'));
});
test('capture unknown PayPal order refuses before contacting payment service',async()=>{
  const f=environment();f.env.TEST_FETCH=()=>{throw Error('must not call')};assert.equal((await makeWorker([product()]).fetch(req('/api/orders/capture',{paypal_order_id:'NOT-OUR-ORDER'}),f.env)).status,404);
});
test('a completed capture with failed D1 write is recovered without a second capture',async()=>{
  const f=environment(),w=makeWorker([product()]);const created=await (await w.fetch(req('/api/orders/create',{items:[{id:'furoff',quantity:1}],country:'US'}),f.env)).json();
  const original=f.env.DB.batch.bind(f.env.DB);let failOnce=true;
  f.env.DB.batch=async statements=>{if(failOnce){failOnce=false;throw Error('simulated D1 outage');}return original(statements);};
  assert.equal((await w.fetch(req('/api/orders/capture',{paypal_order_id:created.paypal_order_id}),f.env)).status,503);
  assert.equal(f.captureCalls,1);assert.equal(f.env.DB.sqlite.prepare('SELECT count(*) AS n FROM orders').get().n,0);
  assert.equal((await w.fetch(req('/api/orders/capture',{paypal_order_id:created.paypal_order_id}),f.env)).status,200);
  assert.equal(f.captureCalls,1);assert.equal(f.env.DB.sqlite.prepare('SELECT count(*) AS n FROM orders').get().n,1);
});
test('expired approved checkout is rejected without capturing',async()=>{
  const f=environment(),w=makeWorker([product()]);const created=await (await w.fetch(req('/api/orders/create',{items:[{id:'furoff',quantity:1}],country:'US'}),f.env)).json();
  f.env.DB.sqlite.prepare('UPDATE checkout_intents SET created_at=?').run('2020-01-01T00:00:00Z');
  assert.equal((await w.fetch(req('/api/orders/capture',{paypal_order_id:created.paypal_order_id}),f.env)).status,409);assert.equal(f.captureCalls,0);
});
test('approved provider order ID mismatch is rejected before capturing',async()=>{
  const f=environment(),w=makeWorker([product()]);const created=await (await w.fetch(req('/api/orders/create',{items:[{id:'furoff',quantity:1}],country:'US'}),f.env)).json();
  f.order.id='A-DIFFERENT-ORDER';
  assert.equal((await w.fetch(req('/api/orders/capture',{paypal_order_id:created.paypal_order_id}),f.env)).status,422);assert.equal(f.captureCalls,0);
});
test('approved capture requalifies revoked, stale, changed-price and changed-supplier products',async()=>{
  for(const mutation of [p=>p.verified_for_checkout=false,p=>p.supplier_verified_at='2020-01-01',p=>p.price_usd=39.99,p=>p.cj_sku='CHANGED-SKU',p=>p.cj_variant_id='CHANGED-VARIANT']){
    const f=environment(),p=product(),w=makeWorker([p]);const created=await (await w.fetch(req('/api/orders/create',{items:[{id:'furoff',quantity:1}],country:'US'}),f.env)).json();mutation(p);
    const response=await w.fetch(req('/api/orders/capture',{paypal_order_id:created.paypal_order_id}),f.env);assert.ok([409,422].includes(response.status));assert.equal(f.captureCalls,0);
  }
});
test('completed payment recovery persists even after supplier qualification is revoked',async()=>{
  const f=environment(),p=product(),w=makeWorker([p]);const created=await (await w.fetch(req('/api/orders/create',{items:[{id:'furoff',quantity:1}],country:'US'}),f.env)).json();
  const original=f.env.DB.batch.bind(f.env.DB);f.env.DB.batch=async()=>{throw Error('simulated outage')};
  assert.equal((await w.fetch(req('/api/orders/capture',{paypal_order_id:created.paypal_order_id}),f.env)).status,503);
  p.verified_for_checkout=false;f.env.DB.batch=original;
  assert.equal((await w.fetch(req('/api/orders/capture',{paypal_order_id:created.paypal_order_id}),f.env)).status,200);assert.equal(f.captureCalls,1);
});
test('new checkout creation is limited before external API use',async()=>{
  const f=environment(),w=makeWorker([product()]);f.env.TEST_FETCH=()=>{throw Error('must not contact provider')};
  for(let i=0;i<10;i++)assert.equal((await w.fetch(req('/api/orders/create',{items:[],country:'US'}),f.env)).status,422);
  const response=await w.fetch(req('/api/orders/create',{items:[],country:'US'}),f.env);assert.equal(response.status,429);assert.equal((await response.json()).error,'create_rate_limited');
});
test('CJ export requires admin authorization and actual verified template',async()=>{
  const f=environment(),w=makeWorker([product()]);assert.equal((await w.fetch(req('/api/orders/export-cj-csv'),f.env)).status,401);
  const response=await w.fetch(req('/api/orders/export-cj-csv',undefined,{Authorization:'Bearer '+f.env.ADMIN_TOKEN}),f.env);assert.equal(response.status,503);assert.equal((await response.json()).error,'cj_template_unverified');
});
test('verified-template export handles comma, newline and formula injection',async()=>{
  const f=environment(),w=makeWorker([product()]);const created=await (await w.fetch(req('/api/orders/create',{items:[{id:'furoff',quantity:1}],country:'US'}),f.env)).json();await w.fetch(req('/api/orders/capture',{paypal_order_id:created.paypal_order_id}),f.env);
  f.env.DB.sqlite.prepare('UPDATE orders SET customer_name=?').run('=HYPERLINK("evil"),\nName');
  f.env.CJ_TEMPLATE_JSON=JSON.stringify({verified_at:new Date().toISOString(),source_url:'https://cjdropshipping.com/test-template',columns:[{header:'Order',field:'order_id'},{header:'Name',field:'customer_name'},{header:'SKU',field:'cj_sku'}]});
  const response=await w.fetch(req('/api/orders/export-cj-csv',undefined,{Authorization:'Bearer '+f.env.ADMIN_TOKEN}),f.env);assert.equal(response.status,200);const text=await response.text();assert.ok(text.includes('"\'=HYPERLINK(""evil""),\nName"'));assert.ok(text.includes('CJ-TEST'));assert.equal(csvCell('@formula'), '"\'@formula"');
});
test('customer lookup matches email without exposing identity or address, and rate limits',async()=>{
  const f=environment(),w=makeWorker([product()]);const created=await (await w.fetch(req('/api/orders/create',{items:[{id:'furoff',quantity:1}],country:'US'}),f.env)).json();await w.fetch(req('/api/orders/capture',{paypal_order_id:created.paypal_order_id}),f.env);
  assert.equal((await w.fetch(req('/api/orders/track',{order_id:created.order_id,email:'wrong@example.com'}),f.env)).status,404);
  const response=await w.fetch(req('/api/orders/track',{order_id:created.order_id,email:'BUYER@example.com'}),f.env);assert.equal(response.status,200);assert.equal(response.headers.get('Cache-Control'),'no-store');const row=await response.json();assert.equal(row.fulfillment_status,'unfulfilled');assert.equal(row.email,undefined);assert.equal(row.shipping_address,undefined);
  let last;for(let i=0;i<20;i++)last=await w.fetch(req('/api/orders/track',{order_id:created.order_id,email:'wrong@example.com'}),f.env);assert.equal(last.status,429);
});
test('authenticated fulfillment updates tracking for paid orders without external notification',async()=>{
  const f=environment(),w=makeWorker([product()]);const created=await (await w.fetch(req('/api/orders/create',{items:[{id:'furoff',quantity:1}],country:'US'}),f.env)).json();
  const data={order_id:created.order_id,fulfillment_status:'shipped',tracking_number:'TRACK123456',tracking_carrier:'USPS'},headers={Authorization:'Bearer '+f.env.ADMIN_TOKEN};
  assert.equal((await w.fetch(req('/api/orders/fulfillment',data),f.env)).status,401);
  assert.equal((await w.fetch(req('/api/orders/fulfillment',data,headers),f.env)).status,404);
  await w.fetch(req('/api/orders/capture',{paypal_order_id:created.paypal_order_id}),f.env);
  assert.equal((await w.fetch(req('/api/orders/fulfillment',{...data,tracking_number:'<script>'},headers),f.env)).status,422);
  let response=await w.fetch(req('/api/orders/fulfillment',data,headers),f.env);assert.equal(response.status,200);assert.equal((await response.json()).external_notifications_sent,false);
  response=await w.fetch(req('/api/orders/track',{order_id:created.order_id,email:'buyer@example.com'}),f.env);assert.equal((await response.json()).tracking_number,'TRACK123456');
  assert.equal((await w.fetch(req('/api/orders/fulfillment',{...data,fulfillment_status:'delivered'},headers),f.env)).status,200);
  assert.equal((await w.fetch(req('/api/orders/fulfillment',data,headers),f.env)).status,409);assert.equal(f.captureCalls,1);
});

test('approved nonexclusive providers can be quoted without CJ API; unknown and spoofed sources are rejected',()=>{
  const valid = {...product(),fulfillment_provider:{id:'eprolo',sku:'EPROLO-GLOVE-2P',variant_id:'EPROLO-2P-BLACK',product_url:'https://eprolo.com/app/product/example'}};
  const q=quote([{id:'furoff',quantity:1}],'US',[valid]);
  assert.equal(q.items[0].supplier_id,'eprolo');
  assert.equal(q.items[0].supplier_sku,'EPROLO-GLOVE-2P');
  assert.equal(q.items[0].cj_sku,null);
  for(const bad of [
    {id:'eprolo',sku:'X',variant_id:'1',product_url:'https://eprolo.com.evil.test/p'},
    {id:'unknown',sku:'X',variant_id:'1',product_url:'https://eprolo.com/p'},
    {id:'eprolo',sku:'X',variant_id:'1',product_url:'http://eprolo.com/p'},
    {id:'eprolo',sku:'X',variant_id:'1',product_url:'https://user:pw@eprolo.com/p'},
  ])assert.throws(()=>quote([{id:'furoff',quantity:1}],'US',[{...product(),fulfillment_provider:bad}]));
});
test('supplier metadata is persisted, provider-specific export is admin-only, and CJ export excludes non-CJ',async()=>{
  const f=environment(),p={...product(),fulfillment_provider:{id:'hypersku',sku:'HS-GLOVE',variant_id:'HS-2PK',product_url:'https://app.hypersku.com/product/123'}},w=makeWorker([p]);
  let r=await w.fetch(req('/api/orders/create',{items:[{id:'furoff',quantity:1}],country:'US'}),f.env);
  assert.equal(r.status,201);const created=await r.json();
  r=await w.fetch(req('/api/orders/capture',{paypal_order_id:created.paypal_order_id}),f.env);
  assert.equal(r.status,200);
  const row=f.env.DB.sqlite.prepare('SELECT supplier_id,supplier_sku,supplier_variant_id,cj_sku FROM orders').get();
  assert.equal(row.supplier_id,'hypersku');assert.equal(row.supplier_sku,'HS-GLOVE');assert.equal(row.cj_sku,'');
  assert.equal((await w.fetch(req('/api/orders/export-supplier-json?provider=hypersku'),f.env)).status,401);
  r=await w.fetch(req('/api/orders/export-supplier-json?provider=hypersku',undefined,{Authorization:'Bearer '+f.env.ADMIN_TOKEN}),f.env);
  assert.equal(r.status,200);const data=await r.json();assert.equal(data.orders.length,1);assert.equal(data.orders[0].items[0].supplier_sku,'HS-GLOVE');
  assert.equal((await w.fetch(req('/api/orders/export-supplier-json?provider=evil',undefined,{Authorization:'Bearer '+f.env.ADMIN_TOKEN}),f.env)).status,422);
  f.env.CJ_TEMPLATE_JSON=JSON.stringify({verified_at:'2026-11-04',source_url:'https://cjdropshipping.com/export',columns:[{header:'Order',field:'order_id',required:true}]});
  r=await w.fetch(req('/api/orders/export-cj-csv',undefined,{Authorization:'Bearer '+f.env.ADMIN_TOKEN}),f.env);
  assert.equal(r.status,200);assert.equal((await r.text()).trim().split(/\r?\n/).length,1); // Header only; no cross-supplier orders.
});
test('changing an approved supplier route invalidates pending capture before funds',async()=>{
  const f=environment(),p={...product(),fulfillment_provider:{id:'eprolo',sku:'E-PET',variant_id:'E-2',product_url:'https://eprolo.com/app/product/1'}},w=makeWorker([p]);
  const created=await (await w.fetch(req('/api/orders/create',{items:[{id:'furoff',quantity:1}],country:'US'}),f.env)).json();
  p.fulfillment_provider={...p.fulfillment_provider,sku:'DIFFERENT-SKU'};
  assert.equal((await w.fetch(req('/api/orders/capture',{paypal_order_id:created.paypal_order_id}),f.env)).status,409);
  assert.equal(f.captureCalls,0);
});


test('mixed-supplier carts fail closed rather than misrouting an order to the first vendor',()=>{
 const cj=product();
 const eprolo={...product(),id:'other',fulfillment_provider:{id:'eprolo',sku:'E-PET',variant_id:'E-2',product_url:'https://eprolo.com/app/product/1'}};
 assert.throws(()=>quote([{id:'furoff',quantity:1},{id:'other',quantity:1}],'US',[cj,eprolo]));
});


test('only one operator can claim a CJ order and its supplier reference is durable', async () => {
  const {env} = environment();
  const worker = makeWorker([product()]);
  const created = await (await worker.fetch(req('/api/orders/create', {items:[{id:'furoff',quantity:1}],country:'US'}), env)).json();
  assert.equal((await worker.fetch(req('/api/orders/capture', {paypal_order_id:created.paypal_order_id}), env)).status, 200);

  const admin = {Authorization:'Bearer ' + env.ADMIN_TOKEN};
  const order = {order_id:created.order_id};
  const handoff = '/api/orders/supplier-handoff';
  const operations = '/api/orders/operations?order_id=' + created.order_id;
  assert.equal((await worker.fetch(req(handoff, order), env)).status, 401);
  const claims = await Promise.all([1, 2].map(() => worker.fetch(req(handoff, order, admin), env)));
  assert.deepEqual(claims.map(response => response.status).sort(), [201, 409]);
  const queue = await (await worker.fetch(req('/api/orders/export-supplier-json?provider=cj', undefined, admin), env)).json();
  assert.deepEqual(queue.orders, []);
  const record = async reference => worker.fetch(req(handoff, {...order,supplier_reference:reference}, admin), env);
  assert.equal((await record('CJ-TEST-001')).status, 200);
  assert.equal((await record('CJ-TEST-001')).status, 200);
  assert.equal((await record('CJ-TEST-002')).status, 409);
  assert.equal((await worker.fetch(req(operations), env)).status, 401);
  const saved = await (await worker.fetch(req(operations, undefined, admin), env)).json();
  assert.equal(saved.supplier_reference, 'CJ-TEST-001');
  assert.equal(saved.paypal_capture_id, 'CAPTURE-123');
  assert.equal(saved.email, undefined);
});


test('US launch offer accepts repeat orders and multiple packs without capture replay', async () => {
  const f = environment();
  const offer = {...product(),id:'home-car-glove-duo',price_usd:10.99};
  const worker = makeWorker([offer]);
  const cart = {items:[{id:offer.id,quantity:1}],country:'US'};
  assert.equal((await worker.fetch(req('/api/orders/create',cart),f.env)).status,422);
  assert.equal((await worker.fetch(req('/api/orders/create',{...cart,country:'GB',delivery_phone:'+12025550123'}),f.env)).status,422);
  const started = await worker.fetch(req('/api/orders/create',{...cart,delivery_phone:'+12025550123'}),f.env);
  assert.equal(started.status,201);
  const intent = await started.json();
  f.order.purchase_units[0].shipping.address.admin_area_1 = 'HI';
  const capture = () => worker.fetch(req('/api/orders/capture',{paypal_order_id:intent.paypal_order_id}),f.env);
  assert.equal((await capture()).status,422);
  assert.equal(f.captureCalls,0);
  f.order.purchase_units[0].shipping.address.admin_area_1 = 'NY';
  assert.equal((await capture()).status,200);
  assert.equal((await capture()).status,200);
  assert.equal(f.captureCalls,1);
  assert.equal((await worker.fetch(req('/api/orders/create',{...cart,delivery_phone:'+12025550123'}),f.env)).status,201);
  assert.equal((await worker.fetch(req('/api/orders/create',{...cart,items:[{id:offer.id,quantity:2}],delivery_phone:'+12025550123'}),f.env)).status,201);
  const saved = f.env.DB.sqlite.prepare('SELECT shipping_address FROM orders').get();
  assert.equal(JSON.parse(saved.shipping_address).phone,'+12025550123');
});
