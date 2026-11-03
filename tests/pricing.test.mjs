import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {quote} from '../workers/order-gateway/src/index.mjs';

const products=JSON.parse(fs.readFileSync(new URL('../data/catalog.json',import.meta.url))).products;
test('every preview target is rejected by Worker quotes in both destinations',()=>{
  for(const p of products){
    for(const country of ['US','GB']){
      assert.throws(()=>quote([{id:p.id,quantity:1}],country,products),/product_not_verified/);
    }
  }
});
test('Worker uses independent actual price even when a target is injected',()=>{
  const p={...products[0],verified_for_checkout:true,cj_variant_id:'SYNTHETIC-TEST',
    warehouse_origin:'CN',stock_status:'in_stock',supplier_verified_at:new Date().toISOString(),
    price_usd:12.25,target_launch_price_usd:99.99,supplier_cost_usd:2,
    shipping_us_usd:3,customer_shipping_us_usd:1,eta_us_days:'8-14 business days',
    specs:{weight_g:100,contains_lithium:false,contains_liquid:false,medical:false}};
  assert.equal(quote([{id:p.id,quantity:1}],'US',[p]).total_cents,1325);
  p.price_usd=null;
  assert.throws(()=>quote([{id:p.id,quantity:1}],'US',[p]),/invalid_catalog_money/);
});
