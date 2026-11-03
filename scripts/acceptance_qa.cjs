/* Local installed Chrome; no provider calls, orders or public deployment. */
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'C:/Users/askgs/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'..'),output=path.resolve(process.env.VISUAL_QA_OUTPUT || path.join(root,'receipts/premium-ux/browser'));
fs.mkdirSync(output,{recursive:true});
const products=JSON.parse(fs.readFileSync(path.join(root,'data/catalog.json'))).products;
const routes=Object.keys(JSON.parse(fs.readFileSync(path.join(root,'build-receipt.json'))).files).filter(p=>p.endsWith('index.html')).map(p=>'/'+p.replace(/index.html$/,''));
const mime={'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.webp':'image/webp'};
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 const report={scope:'LOCAL_INSTALLED_CHROME_NOT_PRODUCTION',browser:await browser.version(),rows:[],galleryActions:[],missing:[],errors:[],external:[],screenshots:[]};
 try{
  const context=await browser.newContext({reducedMotion:'reduce'});
  await context.route('**/*',async route=>{
   const url=new URL(route.request().url());
   if(url.hostname!=='local.verveliving.test'){report.external.push(url.origin+url.pathname);return route.abort();}
   let file=path.resolve(root,'.'+decodeURIComponent(url.pathname));assert(file.startsWith(root+path.sep)||file===root);
   if(fs.existsSync(file)&&fs.statSync(file).isDirectory())file=path.join(file,'index.html');
   if(!fs.existsSync(file)){report.missing.push(url.pathname);return route.fulfill({status:404,body:'Missing'});}
   return route.fulfill({contentType:mime[path.extname(file)]||'application/octet-stream',body:fs.readFileSync(file)});
  });
  const page=await context.newPage();page.on('pageerror',e=>report.errors.push(e.message));
  for(const width of [320,390,768,1024,1440]){
   await page.setViewportSize({width,height:900});
   for(const route of routes){
    await page.goto('https://local.verveliving.test'+route);
    await page.locator('img').evaluateAll(async images=>{images.forEach(i=>i.loading='eager');await Promise.all(images.map(i=>i.decode()));});
    const row={width,route,...await page.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth,images:[...document.images].every(i=>i.complete&&i.naturalWidth>0),activeCartButtons:document.querySelectorAll('[data-add-cart]').length,falsePrices:/\$\d/.test(document.body.innerText),offers:document.querySelectorAll('script[type="application/ld+json"]').length}))};
    assert(!row.overflow&&row.images&&!row.activeCartButtons&&!row.falsePrices&&!row.offers,JSON.stringify(row));
    const p=products.find(p=>route===`/products/${p.slug}/`);
    if(p){
     if(!p.visual_hold){
      const thumbs=page.locator('[data-gallery-src]'),main=page.locator('[data-gallery-main]');
      assert([4,5].includes(await thumbs.count()));
      const rendered=new Set();
      for(let i=0;i<p.images.length;i++){
       await thumbs.nth(i).click();
       assert.equal(await main.getAttribute('src'),p.images[i]);
       await main.evaluate(async image=>image.decode());
       assert(await main.isVisible());
       assert.equal(await thumbs.nth(i).getAttribute('aria-pressed'),'true');
       assert.equal(await page.locator('[data-gallery-src][aria-pressed="true"]').count(),1);
       const alt=await main.getAttribute('alt');assert(alt.includes(`image ${i+1} of ${p.images.length}`));
       assert.equal(await page.locator('[data-gallery-caption]').innerText(),alt);
       const pixels=await main.evaluate(image=>{const c=document.createElement('canvas');c.width=64;c.height=64;c.getContext('2d').drawImage(image,0,0,64,64);return c.toDataURL();});
       assert(!rendered.has(pixels),`Duplicate rendered photo: ${p.id}/${i+1}`);rendered.add(pixels);
       report.galleryActions.push({width,id:p.id,image:i+1,loaded:true,distinct:true});
      }
      await thumbs.first().click();
      if(['furoff','cable-organizer','drain-snake'].includes(p.id)){
       const file=path.join(output,`${p.id}-gallery-${width}.png`);
       await page.locator('.product-gallery').screenshot({path:file});report.screenshots.push(file);
      }
     }else assert.equal(await page.locator('[data-gallery-src]').count(),0);
     const buy=page.getByRole('button',{name:'Buy now',exact:true});assert.equal(await buy.count(),1);assert(await buy.isDisabled());
     await buy.scrollIntoViewIfNeeded();
     row.button=await buy.evaluate(el=>{const r=el.getBoundingClientRect(),s=getComputedStyle(el),reason=document.getElementById(el.getAttribute('aria-describedby'));return {disabled:el.disabled,width:r.width,height:r.height,left:r.left,right:r.right,top:r.top,bottom:r.bottom,fontSize:s.fontSize,color:s.color,background:s.backgroundColor,reason:reason?.textContent};});
     assert(row.button.width>=160&&row.button.height>=48&&row.button.left>=0&&row.button.right<=width&&row.button.top>=0&&row.button.bottom<=900);
     assert.equal(row.button.reason,'Ordering is currently unavailable: product inventory, shipping and checkout not verified');
     assert.equal(await page.getByRole('link',{name:'Ask about availability',exact:true}).count(),1);
     assert((await page.getByRole('link',{name:'Ask about availability',exact:true}).getAttribute('href')).startsWith('mailto:'));
     // A native disabled button ignores programmatic click as well as pointer activation.
     const before=page.url();await buy.evaluate(el=>{window.__buyEvents=0;el.addEventListener('click',()=>window.__buyEvents++);el.click();});
     assert.equal(await page.evaluate(()=>window.__buyEvents),0);assert.equal(page.url(),before);
     if(['furoff','cup-drainer','cable-organizer'].includes(p.id)){
      const file=path.join(output,`${p.id}-${width}.png`);await page.screenshot({path:file});report.screenshots.push(file);
     }
    }else if(route==='/'){
     assert.equal(await page.locator('.sales-collection .product-tile').count(),0);
     assert.equal(await page.locator('#collection .product-tile').count(),13);
     const hero=page.locator('.hero-product-photo'),fur=products.find(p=>p.id==='furoff');
     assert.equal(await hero.getAttribute('src'),fur.images[0]);
     await hero.evaluate(i=>i.decode());assert(await hero.isVisible());
     row.hero=await hero.evaluate(i=>{const r=i.getBoundingClientRect();return {width:r.width,height:r.height,top:r.top,bottom:r.bottom,fit:getComputedStyle(i).objectFit};});
     assert(row.hero.width>=240&&row.hero.height>=200&&row.hero.fit==='contain',JSON.stringify(row.hero));
     assert(row.hero.top<650&&row.hero.bottom<=950,JSON.stringify(row.hero));
     assert.equal(await page.locator('.hero-photograph').getAttribute('href'),`/products/${fur.slug}/`);
     const categories={'kitchen-innovations':'fruit-colander','home-organization':'folding-hanger','smart-cleaning-tools':'furoff'};
     for(const [category,id] of Object.entries(categories)){
      const tile=page.locator(`.category-card[href="/categories/${category}/"]`),product=products.find(p=>p.id===id);
      assert.equal(product.category,category);assert.equal(await tile.getAttribute('data-featured-product'),id);
      assert.equal(await tile.locator('img').getAttribute('src'),product.images[id==='fruit-colander'?3:0]);assert(await tile.locator('img').isVisible());
     }
     for(const target of await page.locator('.nav a,.hero a').all()){
      if(!await target.isVisible())continue;
      const box=await target.boundingBox();assert(box&&box.height>=44,JSON.stringify({text:await target.innerText(),box}));
     }
     assert.equal(await page.locator('#collection .photo-count').count(),13);
     assert.equal(await page.locator('#collection .preview-price').filter({hasText:'Price under verification'}).count(),13);
     const categoryFrames=await page.locator('.category-photo').evaluateAll(nodes=>nodes.map(n=>{const r=n.getBoundingClientRect(),i=n.querySelector('img').getBoundingClientRect();return {width:r.width,height:r.height,imageHeight:i.height};}));
     assert(categoryFrames.every(r=>Math.abs(r.imageHeight-r.height)<1));
     if(width<=600)assert(categoryFrames.every(r=>r.height<=112),'Over-tall mobile category');
     row.categoryFrames=categoryFrames;
     assert.equal(await page.locator('audio,video,[autoplay]').count(),0);
     if(width<=850){
      const menu=page.locator('.mobile-menu'),summary=menu.locator('summary');
      await summary.focus();await page.keyboard.press('Enter');assert(await menu.evaluate(n=>n.open));
      assert(await menu.getByRole('link',{name:'Track an order',exact:true}).isVisible());
      assert(!(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)));
      await summary.focus();await page.keyboard.press('Escape');assert(!await menu.evaluate(n=>n.open));
      assert(await summary.evaluate(n=>n===document.activeElement));
      await summary.evaluate(n=>n.blur());
     }
     const file=path.join(output,`home-${width}.png`);await page.screenshot({path:file});report.screenshots.push(file);
     const full=path.join(output,`home-full-${width}.png`);await page.screenshot({path:full,fullPage:true});report.screenshots.push(full);
     const categoryShot=path.join(output,`categories-${width}.png`);await page.locator('#collections').screenshot({path:categoryShot});report.screenshots.push(categoryShot);
    }
    report.rows.push(row);
   }
  }
  const noScript=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:900}});
  await noScript.route('**/*',async route=>{
   const url=new URL(route.request().url());
   if(url.hostname!=='local.verveliving.test')return route.abort();
   let file=path.resolve(root,'.'+decodeURIComponent(url.pathname));
   assert(file.startsWith(root+path.sep)||file===root);
   if(fs.existsSync(file)&&fs.statSync(file).isDirectory())file=path.join(file,'index.html');
   return route.fulfill({contentType:mime[path.extname(file)]||'application/octet-stream',body:fs.readFileSync(file)});
  });
  const fallback=await noScript.newPage();await fallback.goto('https://local.verveliving.test/');
  await fallback.locator('.mobile-menu summary').click();
  assert(await fallback.getByRole('link',{name:'Contact support',exact:true}).isVisible());
  assert(await fallback.getByText('Product previews · Ordering unavailable.',{exact:true}).isVisible());
  report.noJavaScriptNavigation=true;await noScript.close();
  assert.deepEqual(report.missing,[]);assert.deepEqual(report.errors,[]);assert.deepEqual(report.external,[]);
  fs.writeFileSync(path.join(output,'browser.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({checks:report.rows.length,detailButtonChecks:report.rows.filter(r=>r.button).length,galleryActions:report.galleryActions.length,browser:report.browser,evidence:output,missing:report.missing,errors:report.errors}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
