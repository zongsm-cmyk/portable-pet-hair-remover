import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const html=readFileSync(new URL('../index.html',import.meta.url),'utf8');
test('AI digital catalog includes responsive search and category filters',()=>{for(const id of ['searchInput','categoryGrid','chips','products','langBtn','overlay'])assert.match(html,new RegExp('id="'+id+'"'));assert.match(html,/const products=\[/);assert.match(html,/const translations=/);});
test('No payment or physical affiliate offer is active on new homepage',()=>{assert.match(html, /"checkout_enabled":false/);assert.match(html,/"paypal_environment":"sandbox"/);assert.doesNotMatch(html,/href="\/(checkout|cart|track-order)\//);assert.doesNotMatch(html,/SHOP THE GLOVE DUO/);assert.match(html,/Request availability/);});

test('all twelve catalog entries are out of stock and use a real logo source or the owned Askoure wordmark',()=>{
  const names=['ChatGPT','Canva','Claude','Midjourney','Runway','ElevenLabs','Cursor','Notion AI','Perplexity','CapCut','n8n','AI Prompt & Template Packs'];
  for(const name of names){
    assert.ok(html.includes("name:'"+name+"',stock:'out_of_stock',logoUrl:"), name);
  }
  assert.equal((html.match(/stock:'out_of_stock'/g)||[]).length,12);
  assert.match(html,/class="stock-state"/);
  assert.match(html,/Out of stock/);
  assert.match(html,/function brandImage\(p\)/);
  assert.doesNotMatch(html,/<b>\$\{p\.symbol\}<\/b>/);
  assert.match(html,/dialog-stock-status/);
});

test('inline browser JavaScript parses after brand imagery changes',()=>{
  const scripts=[...html.matchAll(/<script(?:\s+[^>]*)?>([\s\S]*?)<\/script>/g)];
  const executables=scripts.filter(m=>!m[0].includes('type="application/')).map(m=>m[1]);
  assert.ok(executables.length>=1);
  for(const source of executables){assert.doesNotThrow(()=>new Function(source));}
});

test('original Askoure digital kits have real USD prices and external checkout, without restocking third party services',()=>{
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
