import sys, os, json, time, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import doh

ev = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'evidence')

# ---- brand variant domains: which share the owner's CF NS pair (hera/marek)? ----
variants = ['onlyfakeai.ru','onlyfakeai.com','onlyfakeai.net','onlyfakeai.org','onlyfakeai.io',
            'onlyfakeai.co','onlyfakeai.su','onlyfakeai.in','onlyfakeai.me','onlyfakeai.cc',
            'onlyfakeai.biz','onlyfakeai.info','onlyfakeai.pro','onlyfakeai.online','onlyfakeai.site',
            'onlyfakeai.shop','onlyfakeai.store','onlyfakeai.top','onlyfakeai.xyz','onlyfakeai.life',
            'onlyfakeai.world','onlyfakeai.club','onlyfakeai.app','onlyfakeai.dev',
            'onlyfake.org','onlyfake.com','onlyfake.net','onlyfake.io','onlyfake.ai','onlyfake.ru',
            'onlyfake.shop','onlyfake.store','onlyfake.online','onlyfake.cc','onlyfake.su']
print('== NS/A brand variants')
matches = {}
for d in variants:
    rec = doh.query(d, 'NS')
    doh.log(rec, 'brand_variants')
    ns = [a['data'].lower().rstrip('.') for a in rec.get('answers') or []]
    if not ns:
        continue
    same = 'hera.ns.cloudflare.com' in ns and 'marek.ns.cloudflare.com' in ns
    arec = doh.query(d, 'A')
    a = [x['data'] for x in arec.get('answers') or []]
    print(f'{d}: NS={ns} A={a} {">>> SAME CF ACCOUNT" if same else ""}')
    matches[d] = {'ns': ns, 'a': a, 'same_account': same}
    time.sleep(0.05)
json.dump(matches, open(os.path.join(ev, 'brand_variants.json'), 'w'), indent=1)

# ---- supabase gateway headers ----
import ssl, urllib.request
UA = {'User-Agent': 'Mozilla/5.0 Chrome/131.0', 'Accept': 'application/json'}
def head(url):
    req = urllib.request.Request(url, headers=UA)
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
            return r.status, dict(r.headers), r.read(400).decode('utf-8','replace')
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read(400).decode('utf-8','replace')
    except Exception as e:
        return None, {}, str(e)
print('\n== supabase gateway headers')
for u in ['https://cdn.onlyfakeai.ru/rest/v1/', 'https://cdn.onlyfakeai.ru/auth/v1/health',
          'https://<supabase-project-ref>.supabase.co/rest/v1/', 'https://<supabase-project-ref>.supabase.co/auth/v1/health']:
    st, h, b = head(u)
    keep = {k: v for k, v in h.items() if k.lower().startswith(('sb-', 'x-sb', 'server', 'cf-', 'x-powered', 'content-type', 'www-authenticate'))}
    print(u, '->', st, json.dumps(keep)[:400], b[:150])

# ---- favicon mmh3 ----
def murmur3_32(data, seed=0):
    c1 = 0xcc9e2d51; c2 = 0x1b873593
    h = seed
    length = len(data)
    nblocks = length // 4
    for i in range(nblocks):
        k = struct.unpack('<I', data[i*4:i*4+4])[0]
        k = (k * c1) & 0xffffffff
        k = ((k << 15) | (k >> 17)) & 0xffffffff
        k = (k * c2) & 0xffffffff
        h ^= k
        h = ((h << 13) | (h >> 19)) & 0xffffffff
        h = (h * 5 + 0xe6546b64) & 0xffffffff
    k = 0
    tail = data[nblocks*4:]
    if len(tail) >= 3: k ^= tail[2] << 16
    if len(tail) >= 2: k ^= tail[1] << 8
    if len(tail) >= 1:
        k ^= tail[0]
        k = (k * c1) & 0xffffffff
        k = ((k << 15) | (k >> 17)) & 0xffffffff
        k = (k * c2) & 0xffffffff
        h ^= k
    h ^= length
    h ^= h >> 16
    h = (h * 0x85ebca6b) & 0xffffffff
    h ^= h >> 13
    h = (h * 0xc2b2ae35) & 0xffffffff
    h ^= h >> 16
    return h - 0x100000000 if h >= 0x80000000 else h

print('\n== favicon hashes')
for u in ['https://onlyfakeai.ru/favicon.ico', 'https://onlyfakeai.com/favicon.ico']:
    try:
        req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
            raw = r.read()
        import base64, hashlib
        b64 = base64.encodebytes(raw)
        mm = murmur3_32(b64)
        md5 = hashlib.md5(raw).hexdigest()
        print(u, 'len', len(raw), 'mmh3(b64)', mm, 'md5', md5, 'sha256', hashlib.sha256(raw).hexdigest()[:16])
        open(os.path.join(ev, 'favicon_' + u.split('//')[1].split('/')[0] + '.bin'), 'wb').write(raw)
    except Exception as e:
        print(u, 'ERR', e)
