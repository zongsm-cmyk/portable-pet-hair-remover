import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const source=readFileSync(new URL('../static/store.js',import.meta.url),'utf8');
const context=vm.createContext({document:{querySelectorAll:()=>[],querySelector:()=>null},window:{},URL});
vm.runInContext(source,context);
const fixture=Array.from({length:16},(_,i)=>({id:'item-'+i,price_usd:12.25,customer_shipping_us_usd:2.10,customer_shipping_uk_usd:3.45,supplier_verified_at:new Date().toISOString()}));
const normalize=(value)=>JSON.parse(JSON.stringify(context.normalizeCart(value,fixture)));
test('cart strips identity, address and injected properties; preserves only ID and quantity',()=>{
  assert.deepEqual(normalize([{id:'item-0',quantity:2,name:'PRIVATE',address:'PRIVATE',price:0}]),[{id:'item-0',quantity:2}]);
});
test('cart rejects malformed, duplicate, unavailable and out-of-range lines',()=>{
  for(const quantity of [0,-1,11,1.2,'2',null]) assert.deepEqual(normalize([{id:'item-0',quantity}]),[]);
  assert.deepEqual(normalize([{id:'item-0',quantity:2},{id:'item-0',quantity:4},{id:'unknown',quantity:1},null]),[{id:'item-0',quantity:2}]);
  assert.deepEqual(normalize({items:[]}),[]);
});
test('cart enforces maximum 15 distinct products',()=>{
  assert.equal(normalize(fixture.map(p=>({id:p.id,quantity:1}))).length,15);
});
test('display estimate uses integer cents and destination shipping per unit',()=>{
  const items=[{id:'item-0',quantity:3},{id:'item-1',quantity:2}];
  assert.equal(context.cartEstimate(items,'US',fixture),7175);
  assert.equal(context.cartEstimate(items,'GB',fixture),7850);
  assert.throws(()=>context.cartEstimate(items,'CA',fixture));
  assert.throws(()=>context.cartEstimate([{id:'not-qualified',quantity:1}],'US',fixture));
});
test('stale, future, missing and invalid price display records cannot enter cart',()=>{
  for(const patch of [{supplier_verified_at:new Date(Date.now()-8*86400000).toISOString()},{supplier_verified_at:new Date(Date.now()+86400000).toISOString()},{supplier_verified_at:null},{price_usd:0},{price_usd:1.001},{customer_shipping_us_usd:null}]){
    assert.equal(context.qualifiedCatalog([{...fixture[0],...patch}]).length,0);
  }
  assert.equal(context.qualifiedCatalog(fixture).length,16);
});
test('provider redirect requires exact environment domain without embedded credentials',()=>{
  assert.equal(context.approvalDestination('https://www.sandbox.paypal.com/checkoutnow?token=TEST','sandbox'),'https://www.sandbox.paypal.com/checkoutnow?token=TEST');
  for(const value of ['https://www.paypal.com/checkoutnow','https://www.sandbox.paypal.com.evil.test/','javascript:alert(1)','https://name@www.sandbox.paypal.com/','http://www.sandbox.paypal.com/']) assert.throws(()=>context.approvalDestination(value,'sandbox'));
});
