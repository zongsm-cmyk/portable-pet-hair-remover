"""Read-only storefront checks and non-financial disabled-API probes."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

def request(base, path, payload=None, token=None):
    headers = {'User-Agent':'VerveLiving-Deployment-Verification', 'Cache-Control':'no-cache'}
    if payload is not None:
        headers['Content-Type'] = 'application/json'
    if token:
        headers['Authorization'] = 'Bearer ' + token
    req = Request(base + path, headers=headers, data=None if payload is None else json.dumps(payload).encode())
    try:
        with urlopen(req, timeout=25) as response:
            return response.status, response.read()
    except HTTPError as error:
        return error.code, error.read()

class Headings(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.text = []
        self.feed(html)
    def handle_starttag(self, tag, attrs):
        if tag == 'h1': self.depth += 1
    def handle_endtag(self, tag):
        if tag == 'h1': self.depth -= 1
    def handle_data(self, text):
        if self.depth: self.text.append(text)

def verify(base, token_file=None):
    manifest = json.loads((ROOT/'build-receipt.json').read_text())
    checks = {}
    pages = {}
    def inspect(path):
        route = '/' + path.replace('index.html','') if path.endswith('index.html') else '/' + path
        code, body = request(base, route)
        expected = (ROOT/path).read_bytes()
        if path.endswith('.html'):
            text = body.decode('utf-8')
            match = Headings(text).text == Headings(expected.decode('utf-8')).text
            retired = any(term in text.lower() for term in ('thermarelief','kneeflex','only 14 units','45,000','verified buyer'))
            success = code == 200 and match and not retired
        else:
            success = code == 200 and hashlib.sha256(body).hexdigest() == hashlib.sha256(expected).hexdigest()
        return route, {'status':code,'matches_expected':success}
    with ThreadPoolExecutor(max_workers=4) as pool:
        pages = dict(pool.map(inspect, manifest['files']))
    checks['all_generated_routes_match'] = all(page['matches_expected'] for page in pages.values())
    status, body = request(base,'/feed.xml')
    feed = ET.fromstring(body)
    checks['rss_feed_empty_until_qualified'] = status == 200 and len(feed.findall('./channel/item')) == 0
    status, body = request(base,'/api/health')
    health = json.loads(body)
    checks['worker_live_checkout_disabled_sandbox'] = status == 200 and health.get('checkout_enabled') is False and health.get('mode') == 'sandbox'
    probes = {}
    for path,payload,expected_status,expected_error in [
        ('/api/orders/create',{'items':[{'id':'furoff','quantity':1}],'country':'US'},503,'checkout_disabled'),
        ('/api/orders/capture',{'paypal_order_id':'NON-FINANCIAL-PROBE'},503,'checkout_disabled'),
    ]:
        status, body = request(base,path,payload)
        result = json.loads(body)
        checks[path] = status == expected_status and result.get('error') == expected_error
        probes[path] = {'status':status,'error':result.get('error')}
    status,body = request(base,'/api/orders/export-cj-csv',token='invalid-verification-token')
    checks['admin_export_rejects_unauthorized'] = status == 401
    if token_file:
        token = Path(token_file).read_text().strip()
        status,body = request(base,'/api/orders/export-cj-csv',token=token)
        checks['authenticated_cj_export_requires_real_template'] = status == 503 and json.loads(body).get('error') == 'cj_template_unverified'
    result = {'observed_at_utc':datetime.now(timezone.utc).isoformat(),'result':'PASS' if all(checks.values()) else 'FAIL','url':base,'checks':checks,'routes':pages,'api_probes':probes,'worker_health':health,'real_sandbox_tested':False,'real_payments_performed':0,'commercial_launch_approved':False}
    (ROOT/'receipts').mkdir(exist_ok=True)
    (ROOT/'receipts/PRODUCTION_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('routes',)},indent=2))
    return all(checks.values())

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='https://shop.askouresystems.com')
    parser.add_argument('--admin-token-file', type=Path)
    args = parser.parse_args()
    raise SystemExit(0 if verify(args.base.rstrip('/'),args.admin_token_file) else 1)
