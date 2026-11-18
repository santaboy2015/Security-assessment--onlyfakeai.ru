import json, os, ssl, time, urllib.request, urllib.error
ev = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'evidence')

def load_token():
    for f in ['token.txt', 'their_token.txt']:
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), f)
        if os.path.exists(p):
            t = open(p, encoding='utf-8', errors='ignore').read()
            import re
            m = re.search(r'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}', t)
            if m:
                return m.group(0), f
    return None, None

TOKEN, TOKF = load_token()
print('token file:', TOKF, 'len:', len(TOKEN) if TOKEN else None)
PUB = '<publishable-key>'

def req(url, method='GET', headers=None, data=None, timeout=20):
    h = {'User-Agent': 'Mozilla/5.0 Chrome/131.0'}
    h.update(headers or {})
    r = urllib.request.Request(url, headers=h, method=method, data=data)
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(r, timeout=timeout, context=ctx) as resp:
            return resp.status, resp.read(3000).decode('utf-8', 'replace'), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(3000).decode('utf-8', 'replace'), dict(e.headers)
    except Exception as e:
        return None, str(e), {}

B = 'https://s1.onlyfakeai.ru'
variants = [
    ('none', {}),
    ('bearer-user-jwt', {'Authorization': 'Bearer ' + (TOKEN or '')}),
    ('bearer-anon-key', {'Authorization': 'Bearer ' + PUB}),
    ('authorization-raw-jwt', {'Authorization': (TOKEN or '')}),
    ('x-worker-secret-jwt', {'X-Worker-Secret': (TOKEN or '')}),
    ('x-api-key-pub', {'X-API-Key': PUB}),
    ('x-forwarded-user-jwt', {'X-Forwarded-Authorization': 'Bearer ' + (TOKEN or '')}),
]
for name, hdrs in variants:
    st, body, h = req(B + '/status/1778112266686', headers=hdrs)
    print(f'{name}: status={st} body={body[:200]!r}')
    time.sleep(0.6)

# process with jwt
if TOKEN:
    st, body, h = req(B + '/process', method='POST',
                      headers={'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json'},
                      data=b'{}')
    print('POST /process with jwt:', st, body[:300])
    time.sleep(0.6)

# full health body (header echo)
st, body, h = req(B + '/health')
print('\nHEALTH status', st)
try:
    j = json.loads(body)
    print(json.dumps(j, indent=1)[:2500])
except Exception:
    print(body[:1500])
