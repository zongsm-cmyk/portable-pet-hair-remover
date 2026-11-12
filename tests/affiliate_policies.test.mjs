import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const legacyTest = JSON.parse(readFileSync(new URL('../data/settings.json',import.meta.url),'utf8')).site_mode === 'digital' ? test.skip : test;
const policy = (name) => readFileSync(new URL(`../policies/${name}/index.html`, import.meta.url), 'utf8');
const contact = () => readFileSync(new URL('../policies/contact/index.html', import.meta.url), 'utf8');

legacyTest('VerveLiving editorial pages clarify the external merchant relationship', () => {
  const shipping = policy('shipping');
  const refunds = policy('refunds');
  const terms = policy('terms');
  const privacy = policy('privacy');
  const support = contact();
  assert.match(shipping, /We do not accept orders on this site/);
  assert.match(shipping, /retailer handles delivery updates/i);
  assert.match(refunds, /retailer you purchased from handles returns and refunds/i);
  assert.match(terms, /We do not accept orders or payments/);
  assert.match(privacy, /We do not collect payment or delivery details from purchases made at linked retailers/);
  assert.match(support, /Contact that retailer for delivery, cancellation or refund requests/);
  for (const document of [shipping, refunds, terms, privacy, support]) {
    assert.match(document, /<link rel="canonical" href="https:\/\/shop\.askouresystems\.com\//);
    assert.match(document, /"checkout_enabled":false/);
  }
});

legacyTest('Legacy order support stays available without falsely implying new checkout', () => {
  assert.match(policy('refunds'), /historical order placed directly with VerveLiving/);
  assert.match(contact(), /older VerveLiving order/);
  assert.doesNotMatch(policy('terms'), /PayPal processes payments in USD/);
  assert.doesNotMatch(policy('refunds'), /We will confirm next steps and the appropriate destination/);
});
