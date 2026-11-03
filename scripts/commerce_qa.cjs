/* Isolated Chrome QA: local files and explicitly labelled synthetic cart fixtures only. */
const fs=require('node:fs'), path=require('node:path'), os=require('node:os'), assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'C:/Users/askgs/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'..');
const output=path.resolve(process.env.VISUAL_QA_OUTPUT || path.join(os.tmpdir(),'VerveLiving-commerce-20261103'));
if(output===root || output.startsWith(root+path.sep))throw new Error('Screenshots must stay outside the repository');
fs.mkdirSync(output,{recursive:true});
const mime={'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.webp':'image/webp','.png':'image/png'};
const catalog=JSON.parse(fs.readFileSync(path.join(root,'data/catalog.json'))).products;
const receipt=JSON.parse(fs.readFileSync(path.join(root,'build-receipt.json')));
const routes=Object.keys(receipt.files).filter(p=>p.endsWith('index.html')).map(p=>'/'+p.replace(/index.html$/,''));
const fixture={id:'qa-fixture',slug:'furoff-pro-household-roller',title:'SYNTHETIC QA PRODUCT',price_usd:12.25,customer_shipping_us_usd:2.10,customer_shipping_uk_usd:3.45,supplier_verified_at:new Date().toISOString(),images:[]};
(async()=>{
  const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
  const report={mode:'LOCAL_CHROME_ONLY_NO_PROVIDER_CALLS',browser:await browser.version(),rows:[],gallerySwitches:0,syntheticCartChecks:[],missing:[],errors:[],externalRequests:[],screenshots:output};
  try{
    let fixtureMode=false, enabled=false, failCreate=false, creates=[];
    const context=await browser.newContext();
    await context.route('**/*',async route=>{
      const url=new URL(route.request().url());
      if(url.hostname==='www.sandbox.paypal.com' && fixtureMode)return route.fulfill({body:'SYNTHETIC APPROVAL DESTINATION — NO PROVIDER CONNECTION'});
      if(url.hostname!=='local.verveliving.test'){report.externalRequests.push(url.origin+url.pathname);return route.abort();}
      if(url.pathname==='/api/orders/create'){
        if(!fixtureMode)throw new Error('A paused real catalog attempted to create an order');
        creates.push(route.request().postDataJSON());
        return route.fulfill({status:failCreate?503:201,contentType:'application/json',body:JSON.stringify(failCreate?{error:'synthetic_unavailable'}:{approval_url:'https://www.sandbox.paypal.com/checkoutnow?token=SYNTHETIC'})});
      }
      let file=path.resolve(root,'.'+decodeURIComponent(url.pathname));
      if(!file.startsWith(root+path.sep)&&file!==root)return route.abort();
      if(fs.existsSync(file)&&fs.statSync(file).isDirectory())file=path.join(file,'index.html');
      if(!fs.existsSync(file)){report.missing.push(url.pathname);return route.fulfill({status:404,body:'Missing'});}
      let body=fs.readFileSync(file);
      if(fixtureMode && path.extname(file)==='.html'){
        let html=body.toString();
        html=html.replace(/(<script type="application\/json" id="store-config">)[\s\S]*?(<\/script>)/,(_,a,b)=>a+JSON.stringify({checkout_enabled:enabled,api_base:'https://local.verveliving.test',paypal_environment:'sandbox',catalog:[fixture]})+b);
        if(url.pathname.startsWith('/products/'))html=html.replace('</main>','<label>QA quantity<input id="quantity" value="1" type="number"></label><button data-add-cart="qa-fixture" type="button">Add synthetic QA product</button></main>');
        body=Buffer.from(html);
      }
      return route.fulfill({contentType:mime[path.extname(file)]||'application/octet-stream',headers:{'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self'; connect-src 'self'; object-src 'none'"},body});
    });
    const page=await context.newPage();page.on('pageerror',e=>report.errors.push(e.message));
    for(const width of [390,1440]){
      await page.setViewportSize({width,height:900});
      for(const route of routes){
        await page.goto('https://local.verveliving.test'+route);
        await page.locator('img').evaluateAll(async images=>{images.forEach(i=>i.loading='eager');await Promise.all(images.map(i=>i.decode()));});
        const row=await page.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth,images:[...document.images].every(i=>i.complete&&i.naturalWidth>0),smallText:[...document.querySelectorAll('body *')].filter(el=>!['SCRIPT','STYLE'].includes(el.tagName)&&[...el.childNodes].some(n=>n.nodeType===3&&n.textContent.trim())&&el.getClientRects().length&&parseFloat(getComputedStyle(el).fontSize)<12.5).map(el=>el.tagName+':'+getComputedStyle(el).fontSize),smallNavTargets:[...document.querySelectorAll('.nav a,.footer-grid a,button,select,input')].filter(el=>el.getClientRects().length&&el.getBoundingClientRect().height<43.5).map(el=>el.tagName+':'+el.textContent.trim())}));
        report.rows.push({route,width,...row});
        assert(!row.overflow,`Overflow ${route} ${width}`);assert(row.images,`Missing image ${route}`);assert.deepEqual(row.smallText,[],`Small text ${route}`);assert.deepEqual(row.smallNavTargets,[],`Small targets ${route}`);
        assert.equal(await page.locator('[data-add-cart],[data-checkout-product]').count(),0);
        assert.equal(await page.getByRole('button',{name:'Continue to PayPal',exact:true}).count(),0);
        const product=catalog.find(p=>route===`/products/${p.slug}/`);
        if(product?.images.length===2){
          await page.getByRole('button',{name:'View product image 2',exact:true}).click();
          assert.equal(await page.locator('[data-gallery-main]').getAttribute('src'),product.images[1]);
          assert.equal(await page.getByRole('button',{name:'View product image 2',exact:true}).getAttribute('aria-pressed'),'true');
          await page.getByRole('button',{name:'View product image 1',exact:true}).focus();await page.keyboard.press('Enter');
          assert.equal(await page.locator('[data-gallery-main]').getAttribute('src'),product.images[0]);report.gallerySwitches++;
        }
        if(['/','/cart/','/track-order/','/products/furoff-pro-household-roller/'].includes(route))await page.screenshot({path:path.join(output,`actual-${route==='/'?'home':route.split('/').filter(Boolean).join('-')}-${width}.png`),fullPage:true});
      }
    }
    // Synthetic fixture exercises future eligible shopping UX without modifying files or talking to PayPal.
    fixtureMode=true;
    await page.setViewportSize({width:390,height:900});
    await page.goto('https://local.verveliving.test/products/furoff-pro-household-roller/');
    await page.getByRole('button',{name:'Add synthetic QA product',exact:true}).click();
    assert.equal(await page.locator('[data-cart-count]').innerText(),'1');
    assert.deepEqual(await page.evaluate(()=>JSON.parse(sessionStorage.getItem('verveliving.cart.v1'))),[{id:'qa-fixture',quantity:1}]);
    await page.goto('https://local.verveliving.test/cart/');
    assert.equal(await page.locator('[data-cart-payment] button').count(),0);assert.equal(creates.length,0);
    await page.locator('#cart-country').selectOption('GB');assert.match(await page.locator('[data-cart-total]').innerText(),/15\.70/);
    await page.locator('.cart-line input').fill('3');await page.locator('.cart-line input').dispatchEvent('change');assert.match(await page.locator('[data-cart-total]').innerText(),/47\.10/);
    await page.locator('.cart-line input').fill('11');await page.locator('.cart-line input').dispatchEvent('change');assert.equal(await page.locator('.cart-line input').inputValue(),'3');
    await page.reload();assert.equal(await page.locator('.cart-line input').inputValue(),'3');
    await page.getByRole('button',{name:'Remove SYNTHETIC QA PRODUCT'}).click();assert.equal(await page.locator('.cart-line').count(),0);
    report.syntheticCartChecks.push('add, destination estimate, edit, invalid quantity, session reload, remove, paused qualified fixture makes zero create calls');
    await page.goto('https://local.verveliving.test/products/furoff-pro-household-roller/');await page.getByRole('button',{name:'Add synthetic QA product',exact:true}).click();
    enabled=true;failCreate=true;
    await page.goto('https://local.verveliving.test/cart/');await page.getByRole('button',{name:'Continue to PayPal',exact:true}).click();
    await page.waitForFunction(()=>document.querySelector('[data-cart-status]').textContent.includes('synthetic_unavailable'));
    assert(await page.getByRole('button',{name:'Continue to PayPal',exact:true}).isDisabled());assert.equal(creates.length,1);
    assert.deepEqual(creates[0],{items:[{id:'qa-fixture',quantity:1}],country:'US'});
    report.syntheticCartChecks.push('failed create is not automatically retried; payload contains only IDs/quantities/country, no client amount');
    failCreate=false;await page.reload();
    await page.getByRole('button',{name:'Continue to PayPal',exact:true}).click();await page.waitForURL('https://www.sandbox.paypal.com/**');
    assert.equal(creates.length,2);report.syntheticCartChecks.push('enabled synthetic success redirects only to locally intercepted sandbox approval page');
    assert.deepEqual(report.missing,[]);assert.deepEqual(report.errors,[]);assert.deepEqual(report.externalRequests,[]);
    fs.writeFileSync(path.join(output,'commerce-browser.json'),JSON.stringify(report,null,2)+'\n');
    console.log(JSON.stringify({checks:report.rows.length,gallerySwitches:report.gallerySwitches,syntheticCartChecks:report.syntheticCartChecks,missing:[],errors:[],externalRequests:[],evidence:output}));
  }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
