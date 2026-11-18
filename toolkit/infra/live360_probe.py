import json, os, ssl, time, urllib.request, urllib.error
ev = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'evidence')
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36',
      'Accept': 'application/json,text/html,*/*'}

def req(url, method='GET', headers=None, timeout=18):
    h = dict(UA); h.update(headers or {})
    r = urllib.request.Request(url, headers=h, method=method)
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(r, timeout=timeout, context=ctx) as resp:
            return resp.status, resp.read(6000).decode('utf-8', 'replace'), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(6000).decode('utf-8', 'replace'), dict(e.headers)
    except Exception as e:
        return None, str(e), {}

out = {}
for url in ['https://live360.onlyfakeai.ru/',
            'https://live360.onlyfakeai.ru/health',
            'https://live360.onlyfakeai.ru/status',
            'https://live360.onlyfakeai.ru/api',
            'https://live360.onlyfakeai.ru/api/health',
            'https://s2.onlyfakeai.ru/',
            'https://s3.onlyfakeai.ru/',
            'https://s1.onlyfakeai.ru/health']:
    st, body, h = req(url)
    keep = {k: v for k, v in h.items() if k.lower() in ('content-type','server','x-powered-by','cf-ray','x-nextjs-cache','location','access-control-allow-origin','x-minio-version')}
    print(f'{url} -> {st} | {json.dumps(keep)[:250]}')
    print('   ', body[:250].replace('\n', ' '))
    out[url] = {'status': st, 'headers': keep, 'body': body[:1500]}
    time.sleep(1.0)

json.dump(out, open(os.path.join(ev, 'live360_probe.json'), 'w'), indent=1, ensure_ascii=False)

# subdomain.center retry
for dom in ['onlyfakeai.ru', 'onlyfakeai.com']:
    try:
        r = urllib.request.Request('https://api.subdomain.center/?domain=' + dom, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(r, timeout=30) as resp:
            t = resp.read().decode('utf-8', 'replace')
        print('subdomain.center', dom, '->', t[:2000])
        out['sdc_' + dom] = t
    except Exception as e:
        print('subdomain.center', dom, 'ERR', e)
    time.sleep(2)
json.dump(out, open(os.path.join(ev, 'live360_probe.json'), 'w'), indent=1, ensure_ascii=False)
print('saved')
