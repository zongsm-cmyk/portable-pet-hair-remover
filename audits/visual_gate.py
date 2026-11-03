"""Screenshot evidence and browser geometry checks; screenshots still require human/model review.

Install Playwright separately, or pass --runtime for a task-local installation.
No cookies, account login, purchases, or checkout submissions are used.
"""
from pathlib import Path
import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone

ROUTES = {
    'home':'/',
    'kitchen':'/categories/kitchen-innovations/',
    'organization':'/categories/home-organization/',
    'cleaning':'/categories/smart-cleaning-tools/',
    'product':'/products/furoff-pro-household-roller/',
    'sourcing':'/products/kitchen-innovations-01/',
    'shipping':'/policies/shipping/',
    'refunds':'/policies/refunds/',
    'privacy':'/policies/privacy/',
    'terms':'/policies/terms/',
    'contact':'/policies/contact/',
}

async def capture(args):
    from playwright.async_api import async_playwright
    output = Path(args.output).resolve()
    output.mkdir(parents=True,exist_ok=True)
    results = []
    interactions = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=args.chrome,headless=True)
        for width in (390,768,1440):
            page = await browser.new_page(viewport={'width':width,'height':1000},device_scale_factor=1)
            for name,route in ROUTES.items():
                if args.home_only and name != 'home': continue
                response = await page.goto(args.base.rstrip('/')+route,wait_until='networkidle',timeout=45000)
                await page.evaluate('document.fonts.ready')
                await page.evaluate('''async () => {
                    for (const image of document.images) image.loading='eager';
                    await Promise.all(Array.from(document.images).map(image => image.decode().catch(()=>null)));
                }''')
                await page.screenshot(path=str(output/f'{name}-{width}.png'),full_page=True,animations='disabled')
                metrics = await page.evaluate('''() => ({
                    viewport:innerWidth, documentWidth:document.documentElement.scrollWidth,
                    images:Array.from(document.images).map(i=>({src:i.getAttribute('src'),loaded:i.complete&&i.naturalWidth>0,naturalWidth:i.naturalWidth})),
                    svg:Array.from(document.querySelectorAll('svg')).map(s=>({width:s.getBoundingClientRect().width,height:s.getBoundingClientRect().height,fill:getComputedStyle(s).fill,stroke:getComputedStyle(s).stroke,explicit:['width','height','fill','stroke'].every(k=>s.hasAttribute(k))})),
                    outside:Array.from(document.querySelectorAll('main *,header *,footer *')).filter(e=>{
                        const r=e.getBoundingClientRect(),s=getComputedStyle(e);
                        return r.width>0&&r.height>0&&s.position!=='absolute'&&(r.right>innerWidth+1||r.left< -1);
                    }).slice(0,20).map(e=>({tag:e.tagName,class:e.className.baseVal??e.className})),
                    enabledCheckoutButtons:document.querySelectorAll('[data-checkout-product]:not([disabled])').length,
                    overlap:(()=>{
                        const hit=(a,b)=>{const x=a?.getBoundingClientRect(),y=b?.getBoundingClientRect();return !!(x&&y&&Math.min(x.right,y.right)-Math.max(x.left,y.left)>1&&Math.min(x.bottom,y.bottom)-Math.max(x.top,y.top)>1)};
                        return {heroCaptionOverImage:hit(document.querySelector('.hero-art img'),document.querySelector('.hero-stamp')),benefitIconOverText:Array.from(document.querySelectorAll('.benefit')).some(b=>hit(b.querySelector('svg'),b.querySelector('div')))};
                    })(),
                    mainHeading:document.querySelector('h1')?.textContent
                })''')
                results.append({'page':name,'route':route,'width':width,'status':response.status,'screenshot':f'{name}-{width}.png',**metrics})
                if name == 'home':
                    for selector,label in [('.benefits','benefits'),('.curated','featured'),('.header','navigation'),('.hero','hero')]:
                        if await page.locator(selector).count():
                            await page.locator(selector).screenshot(path=str(output/f'{label}-{width}.png'))
                if name == 'product':
                    await page.locator('.product-layout').screenshot(path=str(output/f'gallery-{width}.png'))
                    if args.interactions:
                        for index in range(await page.locator('[data-gallery-src]').count()):
                            button=page.locator('[data-gallery-src]').nth(index)
                            expected=await button.get_attribute('data-gallery-src')
                            await button.click()
                            await page.locator('[data-gallery-main]').evaluate('(i)=>i.decode()')
                            assert await page.locator('[data-gallery-main]').get_attribute('src') == expected
                            assert await button.get_attribute('aria-pressed') == 'true'
                        video_button=page.locator('[data-gallery-video]')
                        if await video_button.count():
                            await video_button.click()
                            await page.wait_for_function("document.querySelector('.product-image video')?.readyState>=2",timeout=30000)
                            await page.locator('.product-image video').evaluate('(v)=>{v.currentTime=5}')
                            await page.wait_for_function("!document.querySelector('.product-image video').seeking",timeout=20000)
                            await page.locator('.product-layout').screenshot(path=str(output/f'video-{width}.png'))
                            video=await page.locator('.product-image video').evaluate('(v)=>({ready:v.readyState,duration:v.duration,width:v.videoWidth,height:v.videoHeight,error:v.error?.code??null})')
                            await page.locator('[data-gallery-src]').first.click()
                            assert await page.locator('.product-image video').evaluate('(v)=>v.hidden&&v.paused')
                            interactions.append({'width':width,'gallery_photos':3,'video':video,'back_to_photo':True})
                        await page.locator('summary').first.click()
                        assert await page.locator('details').first.get_attribute('open') is not None
            if args.interactions:
                for category in ('kitchen-innovations','home-organization','smart-cleaning-tools'):
                    await page.goto(args.base.rstrip('/')+'/',wait_until='networkidle')
                    await page.locator(f'nav a[href="/categories/{category}/"]').click()
                    assert page.url.endswith('/categories/'+category+'/')
                interactions.append({'width':width,'category_navigation_clicked':3})
            await page.close()
        await browser.close()
    checks = {
        'all_pages_http_200':all(x['status']==200 for x in results),
        'no_horizontal_overflow':all(x['documentWidth']<=x['width'] for x in results),
        'no_clipped_content':all(not x['outside'] for x in results),
        'no_icon_or_caption_overlap':all(not any(x['overlap'].values()) for x in results),
        'all_product_images_loaded':all(i['loaded'] for x in results for i in x['images']),
        'checkout_stays_disabled':all(x['enabledCheckoutButtons']==0 for x in results),
        'svg_explicit_outline':all(s['explicit'] and s['fill']=='none' and s['stroke']!='none' for x in results for s in x['svg']),
    }
    receipt={'observed_at_utc':datetime.now(timezone.utc).isoformat(),'base_url':args.base,'screens':len(results),'widths':[390,768,1440],'checks':checks,'manual_visual_review_required':True,'screenshots':results,'interactions':interactions}
    (output/'browser-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'screens':len(results),'checks':checks,'output':str(output)},indent=2))

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--runtime')
    parser.add_argument('--chrome',default=r'C:\Program Files\Google\Chrome\Application\chrome.exe')
    parser.add_argument('--home-only',action='store_true')
    parser.add_argument('--interactions',action='store_true')
    args=parser.parse_args()
    if args.runtime:sys.path.insert(0,args.runtime)
    asyncio.run(capture(args))
