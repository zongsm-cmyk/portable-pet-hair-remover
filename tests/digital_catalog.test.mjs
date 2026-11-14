import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const html=readFileSync(new URL('../index.html',import.meta.url),'utf8');
const js=readFileSync(new URL('../assets/ascorshop.js',import.meta.url),'utf8');
const css=readFileSync(new URL('../assets/ascorshop.css',import.meta.url),'utf8');
test('AscorShop has working search, categories, sorting and selection controls',()=>{
  for(const id of ['searchInput','sortSelect','filters','cards','langBtn','modal','drawer','basketCount'])
    assert.match(html,new RegExp('id="'+id+'"'));
  assert.match(html,/const products=\[/);
  assert.match(js,/function render\(/);
  assert.match(js,/function renderFilters\(/);
  assert.match(js,/function draw\(/);
  assert.match(js,/function availability\(/);
  assert.match(js,/function setLanguage\(/);
  assert.match(css,/\.grid\{display:grid/);
  assert.match(css,/@media\(max-width:650px\)/);
  assert.match(html,/assets\/ascorshop.css/);
  assert.match(html,/assets\/ascorshop.js/);
});
test('No payment or physical affiliate offer is active on the homepage',()=>{
  assert.match(html,/"checkout_enabled":false/);
  assert.match(html,/"paypal_environment":"sandbox"/);
  assert.doesNotMatch(html,/href="\/(checkout|cart|track-order)\//);
  assert.doesNotMatch(html,/SHOP THE GLOVE DUO/);
  assert.match(html,/Request availability/);
});
test('all twelve unqualified subscriptions remain OUT OF STOCK with brand icons or fallback',()=>{
  const names=['ChatGPT','Canva','Claude','Midjourney','Runway','ElevenLabs','Cursor','Notion AI','Perplexity','CapCut','n8n','AI Prompt & Template Packs'];
  for(const name of names) assert.ok(html.includes('name:'+JSON.stringify(name)+",stock:'out_of_stock'"),name);
  assert.equal((html.match(/stock:'out_of_stock'/g)||[]).length,12);
  assert.match(js,/function thirdPartyCard\(p\)/);
  assert.match(js,/class="status out"/);
  assert.match(js,/\.logo/);
  assert.match(js,/<button class="add-btn" disabled>/);
  assert.doesNotMatch(html,/href="\/checkout\//);
});
test('inline data and external browser script parse and are syntactically valid',()=>{
  const scripts=[...html.matchAll(/<script(?:\s+[^>]*)?>([\s\S]*?)<\/script>/g)];
  const executables=scripts.filter(m=>!m[0].includes('type="application/')).map(m=>m[1]);
  assert.ok(executables.length>=1);
  for(const source of [...executables,js]) assert.doesNotThrow(()=>new Function(source));
});
test('three original developer kits retain real prices, routes and separate Gumroad checkout',()=>{
  assert.match(html,/id="original-products"/);
  assert.equal((html.match(/class="own-card /g)||[]).length,3);
  const slugs=['n8n-workflow-preflight-auditor','llm-reliability-rescue-kit','agent-runaway-guard-kit'];
  const prices=[9,19,24];
  for(let i=0;i<slugs.length;i++){
    assert.ok(html.includes('https://mhamedasskoure.gumroad.com/l/'+slugs[i]),slugs[i]);
    assert.ok(html.includes('/digital-products/'+slugs[i]+'/'),slugs[i]);
    assert.ok(html.includes('$'+prices[i]),'price '+prices[i]);
  }
  assert.equal((html.match(/stock:'out_of_stock'/g)||[]).length,12);
  assert.match(html,/"checkout_enabled":false/);
});
