import json, os, ssl, time, urllib.request, urllib.error
ev = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'evidence')

def load_jwt():
    import re
    for f in ['token.txt', 'their_token.txt']:
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), f)
        if os.path.exists(p):
            t = open(p, encoding='utf-8', errors='ignore').read()
            m = re.search(r'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}', t)
            if m: return m.group(0)
    return None
TOKEN = load_jwt()

def req(url, method='GET', headers=None, data=None, timeout=25):
    h = {'User-Agent': 'Mozilla/5.0 Chrome/131.0', 'Accept': 'application/json,*/*'}
    h.update(headers or {})
    r = urllib.request.Request(url, headers=h, method=method, data=data)
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(r, timeout=timeout, context=ctx) as resp:
            return resp.status, resp.read(8000).decode('utf-8', 'replace'), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(8000).decode('utf-8', 'replace'), dict(e.headers)
    except Exception as e:
        return None, str(e), {}

JOB = '1778112266686'
tests = [
    ('GET', f'https://onlyfakeai.ru/api/status/{JOB}', None, {}),
    ('GET', 'https://onlyfakeai.ru/api/status/1/test', None, {}),
    ('GET', f'https://api.onlyfakeai.ru/status/{JOB}', None, {}),
    ('POST', 'https://onlyfakeai.ru/api/process/1', b'{}', {'Content-Type': 'application/json'}),
    ('GET', 'https://onlyfakeai.ru/api/process/1', None, {}),
    ('GET', f'https://onlyfakeai.ru/api/no-watermark/{JOB}', None, {'Authorization': 'Bearer ' + (TOKEN or '')}),
    ('GET', 'https://onlyfakeai.ru/_next/static/S2HurGa5cGUpA5514zy3f/_buildManifest.js', None, {}),
]
out = {}
for method, url, data, hdrs in tests:
    st, body, h = req(url, method=method, data=data, headers=hdrs)
    keep = {k: v for k, v in h.items() if k.lower() in ('content-type','content-length','x-nextjs-cache','cf-cache-status','set-cookie','location','x-powered-by','server')}
    out[f'{method} {url}'] = {'status': st, 'headers': keep, 'body': body[:3000]}
    print(f'{method} {url} -> {st} | {json.dumps(keep)[:200]}')
    print('   ', body[:500].replace('\n', ' '))
    time.sleep(1.2)

json.dump(out, open(os.path.join(ev, 'main_worker_proxy_probe.json'), 'w'), indent=1, ensure_ascii=False)
print('saved')
