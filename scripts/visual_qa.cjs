/* Offline browser QA: serve the real local files through Playwright routing.
   No authenticated browser, network request, dependency install or live mutation. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const runtime = process.env.PLAYWRIGHT_MODULE || 'C:/Users/askgs/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright';
const {chromium} = require(runtime);
const root = path.resolve(process.argv[2] || '.');
const label = process.argv[3] || 'after';
const output = path.resolve('receipts/visual-recovery');
fs.mkdirSync(output,{recursive:true});
const mime = {'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'application/javascript; charset=utf-8','.jpg':'image/jpeg','.webp':'image/webp','.png':'image/png'};
(async()=>{
  const browser = await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe', headless:true});
  try {
    const context = await browser.newContext();
    const missing=[], errors=[], rows=[];
    await context.route('**/*', async route=>{
      const url = new URL(route.request().url());
      if (url.hostname !== 'local.verveliving.test') return route.abort();
      let file=path.resolve(root,'.'+decodeURIComponent(url.pathname));
      if (!file.startsWith(root+path.sep) && file!==root) return route.abort();
      if(fs.existsSync(file) && fs.statSync(file).isDirectory()) file=path.join(file,'index.html');
      if(!fs.existsSync(file)){missing.push(url.pathname);return route.fulfill({status:404,body:'Missing local file'});}
      await route.fulfill({status:200,contentType:mime[path.extname(file)]||'application/octet-stream',body:fs.readFileSync(file)});
    });
    const page=await context.newPage();
    page.on('pageerror',e=>errors.push(e.message));
    async function loaded(){
      await page.locator('img').evaluateAll(async images=>{
        images.forEach(i=>i.loading='eager');
        await Promise.all(images.map(i=>i.decode().catch(()=>{})));
      });
      return page.evaluate(()=>({images:[...document.images].map(i=>({src:new URL(i.src).pathname,loaded:i.complete&&i.naturalWidth>0,w:i.naturalWidth,h:i.naturalHeight})),overflow:document.documentElement.scrollWidth>innerWidth,cards:document.querySelectorAll('.product-tile').length,buy:document.querySelectorAll('[data-checkout-product],#quantity').length}));
    }
    for(const width of [320,390,768,1440]){
      await page.setViewportSize({width,height:900});
      await page.goto('https://local.verveliving.test/');
      const row={route:'/',width,...await loaded()}; rows.push(row);
      assert(!row.overflow,`Overflow at ${width}`);
      assert(row.images.every(i=>i.loaded),'Unloaded homepage image');
      if(label==='after'){assert.equal(row.cards,13);assert.equal(row.buy,0);}
      if(width!==320){
        await page.screenshot({path:path.join(output,`${label}-home-${width}.png`),fullPage:true});
        await page.locator('.hero').screenshot({path:path.join(output,`${label}-hero-${width}.png`)});
        if(label==='after')await page.locator('#kitchen-innovations').screenshot({path:path.join(output,`${label}-gallery-${width}.png`)});
      }
    }
    if(label==='after'){
      const catalog=JSON.parse(fs.readFileSync(path.join(root,'data/catalog.json')));
      await page.setViewportSize({width:390,height:844});
      for(const p of catalog.products){
        const route=`/products/${p.slug}/`;
        await page.goto('https://local.verveliving.test'+route);
        const row={route,width:390,...await loaded()};rows.push(row);
        assert(!row.overflow,`Overflow ${route}`);
        assert(row.images.every(i=>i.loaded)); assert.equal(row.buy,0);
        assert.equal(await page.locator('meta[name="robots"]').getAttribute('content'),'noindex,follow');
        assert(await page.getByText('Buying unavailable', {exact:false}).count());
        if(p.images.length)assert(row.images.length>=1);
        if(p.id==='furoff')await page.screenshot({path:path.join(output,'after-furoff-390.png'),fullPage:true});
      }
      for(const category of ['kitchen-innovations','home-organization','smart-cleaning-tools']){
        await page.goto('https://local.verveliving.test/categories/'+category+'/');
        const row={route:'/categories/'+category+'/',width:390,...await loaded()}; rows.push(row);
        assert(!row.overflow);assert(row.images.every(i=>i.loaded));
        await page.locator('[data-product-search]').fill('unmatchedquery');
        assert.equal(await page.locator('.product-tile:visible').count(),0);
        await page.locator('[data-product-search]').fill('');
        assert.equal(await page.locator('.product-tile:visible').count(),row.cards);
      }
    }
    assert.deepEqual(missing,[]);assert.deepEqual(errors,[]);
    const report={mode:'LOCAL_FILES_OFFLINE_BROWSER_ROUTING',browser:await browser.version(),label,rows,missing,errors,screenshots:'Real Chrome headless renders, no Lighthouse run'};
    fs.writeFileSync(path.join(output,label+'-browser.json'),JSON.stringify(report,null,2)+'\n');
    console.log(JSON.stringify({label,checks:rows.length,missing,errors,homeCards:rows[0].cards}));
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
