/* Real installed Chrome, isolated profile, local publishable files only. */
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'C:/Users/askgs/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'..');
const output=path.resolve(process.env.VISUAL_QA_OUTPUT || path.join(os.tmpdir(),'VerveLiving-pricing-20261103'));
assert(output!==root&&!output.startsWith(root+path.sep),'Evidence must be outside repository');
fs.mkdirSync(output,{recursive:true});
const products=JSON.parse(fs.readFileSync(path.join(root,'data/catalog.json'))).products;
const receipt=JSON.parse(fs.readFileSync(path.join(root,'build-receipt.json')));
const routes=Object.keys(receipt.files).filter(p=>p.endsWith('index.html')).map(p=>'/'+p.replace(/index.html$/,''));
const mime={'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.webp':'image/webp'};
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 const report={scope:'LOCAL_REAL_CHROME_NO_LIVE_PUBLICATION',browser:await browser.version(),rows:[],missing:[],errors:[],external:[],screenshots:[]};
 try{
  const context=await browser.newContext({reducedMotion:'reduce'});
  await context.route('**/*',async route=>{
   const url=new URL(route.request().url());
   if(url.hostname!=='local.verveliving.test'){report.external.push(url.origin+url.pathname);return route.abort();}
   let file=path.resolve(root,'.'+decodeURIComponent(url.pathname));
   assert(file.startsWith(root+path.sep)||file===root);
   if(fs.existsSync(file)&&fs.statSync(file).isDirectory())file=path.join(file,'index.html');
   if(!fs.existsSync(file)){report.missing.push(url.pathname);return route.fulfill({status:404,body:'Missing'});}
   return route.fulfill({contentType:mime[path.extname(file)]||'application/octet-stream',body:fs.readFileSync(file)});
  });
  const page=await context.newPage();page.on('pageerror',e=>report.errors.push(e.message));
  for(const width of [320,390,1440]){
   await page.setViewportSize({width,height:900});
   for(const route of routes){
    await page.goto('https://local.verveliving.test'+route);
    await page.locator('img').evaluateAll(async images=>{images.forEach(i=>i.loading='eager');await Promise.all(images.map(i=>i.decode()));});
    const row={width,route,...await page.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth,images:[...document.images].every(i=>i.complete&&i.naturalWidth>0),prices:[...document.querySelectorAll('.target-price-amount')].map(el=>{
     const s=getComputedStyle(el),r=el.getBoundingClientRect();return {text:el.textContent,fontSize:s.fontSize,color:s.color,weight:s.fontWeight,width:r.width,clipped:el.scrollWidth>el.clientWidth||r.left<0||r.right>innerWidth};
    }),buyButtons:document.querySelectorAll('[data-add-cart]').length,offers:document.querySelectorAll('script[type="application/ld+json"]').length}))};
    assert(!row.overflow&&row.images&&!row.buyButtons&&!row.offers,JSON.stringify(row));
    const p=products.find(p=>route===`/products/${p.slug}/`);
    const expected=route==='/'?13:route.startsWith('/categories/')?products.filter(p=>p.images.length&&route===`/categories/${p.category}/`).length:p&&!p.visual_hold?1:0;
    assert.equal(row.prices.length,expected,route);
    for(const price of row.prices){assert(!price.clipped,JSON.stringify(price));assert(parseFloat(price.fontSize)>=30);assert.equal(price.color,'rgb(41, 46, 41)');}
    // Scrolling a card to its photo keeps the entire price and status in the viewport.
    for(const card of await page.locator('.product-tile').all()){
     await card.evaluate(el=>el.scrollIntoView({block:'start',behavior:'instant'}));
     const fit=await card.locator('.target-price').evaluate(el=>{const r=el.getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight;});
     assert(fit,`Card price below fold: ${width} ${route}`);
     const id=await card.getAttribute('data-product-id');
     assert.equal((await card.locator('.target-price-amount').innerText()).replace(/\s+/g,' ').trim(),`$${products.find(p=>p.id===id).target_launch_price_usd.toFixed(2)} USD`);
    }
    report.rows.push(row);
    if([390,1440].includes(width)&&(route==='/'||route==='/products/three-layer-cable-organizer/')){
     const target=page.locator(route==='/'?'.product-tile':'.target-price-detail').first();
     await target.evaluate(el=>el.scrollIntoView({block:'start',behavior:'instant'}));
     const file=path.join(output,`${route==='/'?'home-prices':'detail-price'}-${width}.png`);
     await page.screenshot({path:file});report.screenshots.push(file);
    }
   }
  }
  assert.deepEqual(report.missing,[]);assert.deepEqual(report.errors,[]);assert.deepEqual(report.external,[]);
  fs.writeFileSync(path.join(output,'pricing-browser.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({checks:report.rows.length,priceChecks:report.rows.reduce((n,r)=>n+r.prices.length,0),browser:report.browser,evidence:output,missing:report.missing,errors:report.errors}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
