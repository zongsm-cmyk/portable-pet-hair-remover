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
test('only the qualified US offer has valid live bundle totals',()=>{
  const catalog=[offer];
  for(const [quantity,total] of [[1,1099],[2,2198],[3,3297]]){
    assert.equal(quote([{id:offer.id,quantity}],'US',catalog).total_cents,total);
  }
  assert.throws(()=>quote([{id:offer.id,quantity:1}],'GB',catalog));
});
test('supplier shipping is not added to the customer shipping price again',()=>{
  const q=quote([{id:offer.id,quantity:2}],'US',[offer]);
  assert.equal(q.total_cents,2198);
  assert.equal(q.items[0].supplier_variant_id,offer.cj_variant_id);
});
