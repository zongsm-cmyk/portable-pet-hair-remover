import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const html=readFileSync(new URL('../index.html',import.meta.url),'utf8');
test('AI digital catalog includes responsive search and category filters',()=>{for(const id of ['searchInput','categoryGrid','chips','products','langBtn','overlay'])assert.match(html,new RegExp('id="'+id+'"'));assert.match(html,/const products=\[/);assert.match(html,/const translations=/);});
test('No payment or physical affiliate offer is active on new homepage',()=>{assert.match(html, /"checkout_enabled":false/);assert.match(html,/"paypal_environment":"sandbox"/);assert.doesNotMatch(html,/href="\/(checkout|cart|track-order)\//);assert.doesNotMatch(html,/SHOP THE GLOVE DUO/);assert.match(html,/Request availability/);});
