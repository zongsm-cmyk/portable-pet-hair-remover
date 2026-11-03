import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const source = readFileSync(new URL('../static/store.js', import.meta.url), 'utf8');
async function paymentPage(enabled, receipt) {
  const status = {textContent:''};
  let calls = 0;
  const settings = {checkout_enabled:enabled,api_base:'https://shop.askouresystems.com'};
  const context = {
    document:{querySelectorAll:()=>[],querySelector:selector=>
      selector === '#store-config' ? {textContent:JSON.stringify(settings)} :
      selector === '#capture-status' ? status : null},
    window:{location:{search:'?token=PAYPAL-TEST',pathname:'/checkout/return/'},history:{replaceState(){}}},
    URLSearchParams, URL,
    fetch:async()=>{calls++;return {ok:true,json:async()=>receipt};},
  };
  vm.runInNewContext(source, context);
  await new Promise(resolve=>setImmediate(resolve));
  return {text:status.textContent,calls};
}

test('paused return with a provider token makes no capture request', async()=>{
  const result = await paymentPage(false, {});
  assert.equal(result.calls,0);
  assert.match(result.text,/currently unavailable/);
});

test('pending, missing or malformed capture receipts never display confirmation',async()=>{
  for (const receipt of [{order_id:'12345678-1234-4234-8234-123456789abc',payment_status:'PENDING'},
    {order_id:'12345678-1234-4234-8234-123456789abc'}, {payment_status:'COMPLETED'},
    {order_id:'untrusted',payment_status:'COMPLETED'}]) {
    const result = await paymentPage(true,receipt);
    assert.equal(result.calls,1);
    assert.match(result.text,/could not confirm/);
    assert.doesNotMatch(result.text,/Payment confirmed\./);
  }
});

test('only a completed server capture receipt displays its order number',async()=>{
  const result = await paymentPage(true,{order_id:'12345678-1234-4234-8234-123456789abc',payment_status:'COMPLETED'});
  assert.match(result.text,/Payment confirmed\. Your order number is 12345678-1234-4234-8234-123456789abc/);
});
