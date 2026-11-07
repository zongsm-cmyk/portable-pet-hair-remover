import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {quote} from '../workers/order-gateway/src/index.mjs';

const products=JSON.parse(fs.readFileSync(new URL('../data/catalog.json',import.meta.url))).products;
const offer=JSON.parse(fs.readFileSync(new URL('../workers/order-gateway/launch-offer.json',import.meta.url)));
test('all unqualified catalog items were purged from sellable source',()=>{
  assert.equal(products.length,0);
  assert.throws(()=>quote([{id:'fruit-colander',quantity:1}],'US',products));
});
test('the published-price US offer fails the 3x landed-cost screen',()=>{
  // The real listing is explicitly revoked; a controlled hypothetical validates the price screen.
  assert.equal(offer.verified_for_checkout,false);
  assert.throws(()=>quote([{id:offer.id,quantity:1}],'US',[offer]),/product_not_verified/);
  const hypothetical={...offer,verified_for_checkout:true,stock_status:'in_stock',supplier_verified_at:new Date().toISOString()};
  assert.throws(()=>quote([{id:offer.id,quantity:1}],'US',[hypothetical]),/insufficient_landed_margin/);
  assert.throws(()=>quote([{id:offer.id,quantity:1}],'GB',[offer]));
});
test('synthetic profitable two-pack quote does not double-charge supplier shipping',()=>{
  // This is a unit-test fixture, not a pricing decision or evidence of a valid supplier quote.
  const hypothetical={...offer,price_usd:20,verified_for_checkout:true,stock_status:'in_stock',supplier_verified_at:new Date().toISOString()};
  const q=quote([{id:offer.id,quantity:2}],'US',[hypothetical]);
  assert.equal(q.total_cents,4000);
  assert.equal(q.items[0].supplier_variant_id,offer.cj_variant_id);
});
