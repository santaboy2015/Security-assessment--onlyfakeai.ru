"""Light watcher: detect when s2/s3 (worker2 / MinIO) tunnels come back.
Polls every 120s for up to 2h; logs transitions with timestamps + response heads.
Rate: 3 requests / 2 min max. Non-destructive GET only.
"""
import json, os, ssl, time, urllib.request, urllib.error

BASE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(BASE, 'watch_tunnels.log')
EV = os.path.join(BASE, 'evidence', 'watcher_states.jsonl')
UA = {'User-Agent': 'Mozilla/5.0 Chrome/131.0'}
HOSTS = ['https://s2.onlyfakeai.ru/', 'https://s3.onlyfakeai.ru/', 'https://s1.onlyfakeai.ru/health']
INTERVAL = 120
MAX_MIN = 120

def get(url):
    req = urllib.request.Request(url, headers=UA)
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
            return r.status, dict(r.headers), r.read(800).decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read(800).decode('utf-8', 'replace')
    except Exception as e:
        return None, {}, str(e)

def classify(st, h, body):
    srv = (h.get('Server') or '').lower()
    if st is None:
        return 'error'
    if st == 530 and 'tunnel' in body.lower():
        return 'tunnel_down'
    if 'minio' in body.lower() or 'x-minio' in {k.lower() for k in h} or srv == 'minio':
        return 'MINIO'
    if 'x-powered-by' in {k.lower() for k in h}:
        return 'express_or_next'
    return f'http_{st}'

start = time.time()
last = {}
with open(LOG, 'a', encoding='utf-8') as lf:
    lf.write(f'\n=== watcher start {time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())} ===\n')
while (time.time() - start) < MAX_MIN * 60:
    for u in HOSTS:
        st, h, body = get(u)
        cls = classify(st, h, body)
        if last.get(u) != cls:
            line = f'{time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())} {u} -> status={st} class={cls} body={body[:200]!r}'
            with open(LOG, 'a', encoding='utf-8') as lf:
                lf.write(line + '\n')
            with open(EV, 'a', encoding='utf-8') as ef:
                ef.write(json.dumps({'ts': time.time(), 'url': u, 'status': st, 'class': cls, 'body': body[:400],
                                     'headers': {k: v for k, v in h.items() if k.lower() in ('server', 'content-type', 'x-powered-by')}}) + '\n')
            last[u] = cls
    time.sleep(INTERVAL)
with open(LOG, 'a', encoding='utf-8') as lf:
    lf.write(f'=== watcher end {time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())} ===\n')
