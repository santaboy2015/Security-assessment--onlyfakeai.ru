import json, os, ssl, time, urllib.request, urllib.error
ev = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'evidence')
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36',
      'Accept': 'application/json,text/html,*/*'}

def req(url, method='GET', data=None, headers=None, timeout=20):
    h = dict(UA); h.update(headers or {})
    body = None
    if data is not None:
        body = data if isinstance(data, bytes) else json.dumps(data).encode()
    r = urllib.request.Request(url, headers=h, method=method, data=body)
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(r, timeout=timeout, context=ctx) as resp:
            b = resp.read(6000)
            return {'url': url, 'method': method, 'status': resp.status, 'headers': dict(resp.headers),
                    'body': b.decode('utf-8', 'replace'), 'ct': resp.headers.get('content-type')}
    except urllib.error.HTTPError as e:
        b = e.read(6000)
        return {'url': url, 'method': method, 'status': e.code, 'headers': dict(e.headers),
                'body': b.decode('utf-8', 'replace'), 'ct': e.headers.get('content-type')}
    except Exception as e:
        return {'url': url, 'method': method, 'error': str(e)}

def show(r):
    h = r.get('headers', {})
    keep = {k: v for k, v in h.items() if k.lower() in ('content-type','server','x-powered-by','allow','access-control-allow-origin','access-control-allow-methods','access-control-allow-headers','x-nextjs-cache','cf-ray','set-cookie')}
    body = (r.get('body') or '').replace('\n', ' ')[:400]
    print(f"{r.get('method')} {r.get('url')} -> {r.get('status') or r.get('error')} | {json.dumps(keep)[:250]}")
    print('    body:', body)

B = 'https://s1.onlyfakeai.ru'
tests = [
    ('GET', B + '/', None),
    ('GET', B + '/health', None),
    ('GET', B + '/status', None),
    ('GET', B + '/status/1778112266686', None),
    ('GET', B + '/status/nonexistent', None),
    ('OPTIONS', B + '/status/1', None),
    ('GET', B + '/process', None),
    ('POST', B + '/process', b'{}'),
    ('POST', B + '/process', b'{bad json'),
    ('GET', B + '/env', None),
    ('GET', B + '/debug', None),
    ('GET', B + '/metrics', None),
    ('GET', B + '/api', None),
    ('GET', B + '/package.json', None),
    ('GET', B + '/server-info', None),
    ('GET', B + '/version', None),
    ('GET', B + '/info', None),
    # main-site style proxy path on worker? and ops worker endpoints
    ('GET', B + '/no-watermark/1778112266686', None),
]
out = {}
for method, url, data in tests:
    r = req(url, method=method, data=data)
    out[f'{method} {url}'] = r
    show(r)
    time.sleep(0.8)

json.dump(out, open(os.path.join(ev, 'worker_s1_probe.json'), 'w'), indent=1, ensure_ascii=False)
print('saved')
