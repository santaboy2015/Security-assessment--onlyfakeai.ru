import json, os, ssl, time, urllib.request, urllib.error, random
ev = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'evidence')
PUB = '<publishable-key>'
UA = {'User-Agent': 'Mozilla/5.0 Chrome/131.0', 'Content-Type': 'application/json', 'apikey': PUB, 'Accept': 'application/json'}

def req(url, method='GET', headers=None, data=None, timeout=20):
    h = dict(UA); h.update(headers or {})
    r = urllib.request.Request(url, headers=h, method=method, data=data)
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(r, timeout=timeout, context=ctx) as resp:
            return resp.status, resp.read(8000).decode('utf-8', 'replace'), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(8000).decode('utf-8', 'replace'), dict(e.headers)
    except Exception as e:
        return None, str(e), {}

email = f'infra-probe-{int(time.time())}@dropmail.me'
pw = 'Probe-Infra-2026!'
st, body, h = req('https://cdn.onlyfakeai.ru/auth/v1/signup', method='POST',
                  data=json.dumps({'email': email, 'password': pw}).encode())
print('SIGNUP', st, body[:300])
tok = None
try:
    j = json.loads(body); tok = j.get('access_token')
except Exception:
    j = {}
if not tok:
    st, body, h = req('https://cdn.onlyfakeai.ru/auth/v1/token?grant_type=password', method='POST',
                      data=json.dumps({'email': email, 'password': pw}).encode())
    print('LOGIN', st, body[:300])
    try: tok = json.loads(body).get('access_token')
    except Exception: pass
print('TOKEN len', len(tok) if tok else None)
open(os.path.join(ev, 'fresh_token.json'), 'w').write(json.dumps({'email': email, 'password': pw, 'token': tok}))

if tok:
    # verify token
    st, body, h = req('https://cdn.onlyfakeai.ru/auth/v1/user', headers={'Authorization': 'Bearer ' + tok})
    print('USER', st, body[:200])
    # worker tests with fresh token
    for u in ['https://s1.onlyfakeai.ru/status/1778112266686', 'https://s1.onlyfakeai.ru/health']:
        st, body, h = req(u, headers={'Authorization': 'Bearer ' + tok})
        print('WORKER', u, st, body[:250])
        time.sleep(0.8)
    st, body, h = req('https://s1.onlyfakeai.ru/process', method='POST',
                      headers={'Authorization': 'Bearer ' + tok}, data=b'{}')
    print('WORKER POST /process', st, body[:300])
    time.sleep(0.8)
    # main site endpoints with fresh token
    for u in ['https://onlyfakeai.ru/api/no-watermark/1778112266686',
              'https://onlyfakeai.ru/api/auth/verify',
              'https://ops.onlyfakeai.ru/api/auth/verify']:
        st, body, h = req(u, headers={'Authorization': 'Bearer ' + tok})
        print('MAIN', u, st, body[:250])
        time.sleep(1.0)
