import json, os, ssl, socket, re, time, urllib.request, urllib.error
ev = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'evidence')
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36',
      'Accept': 'text/html,application/json,*/*'}

def req(url, timeout=15, method='GET'):
    ctx = ssl.create_default_context()
    r = urllib.request.Request(url, headers=UA, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout, context=ctx) as resp:
            body = resp.read(8192)
            return {'url': url, 'status': resp.status, 'headers': dict(resp.headers), 'body': body.decode('utf-8', 'replace'), 'final': resp.geturl()}
    except urllib.error.HTTPError as e:
        body = e.read(8192)
        return {'url': url, 'status': e.code, 'headers': dict(e.headers), 'body': body.decode('utf-8', 'replace')}
    except Exception as e:
        return {'url': url, 'error': str(e)}

def summarize(r):
    h = r.get('headers', {})
    keep = {k: v for k, v in h.items() if k.lower() in ('server','x-powered-by','content-type','location','via','cf-ray','x-frame-options','strict-transport-security','x-minio-version','x-amz-request-id','set-cookie','x-served-by','www-authenticate','x-nextjs-cache')}
    title = ''
    m = re.search(r'<title[^>]*>(.*?)</title>', r.get('body', ''), re.I | re.S)
    if m: title = re.sub(r'\s+', ' ', m.group(1)).strip()[:120]
    return f"{r.get('url')} -> {r.get('status') or r.get('error')} | {json.dumps(keep)[:400]} | title={title!r} | body={ (r.get('body') or '')[:160]!r}"

targets = [
    ('https://mail.onlyfakeai.ru/', 'GET'),
    ('https://mail.onlyfakeai.ru/SOGo/', 'GET'),
    ('https://mail.onlyfakeai.ru/webmail', 'GET'),
    ('https://mail.onlyfakeai.ru/api/v1/get/status/containers', 'GET'),
    ('https://ftp.onlyfakeai.ru/', 'GET'),
    ('https://s3.onlyfakeai.ru/', 'GET'),
    ('https://s3.onlyfakeai.ru/?list-type=2', 'GET'),
    ('https://s3.onlyfakeai.ru/minio/health/live', 'GET'),
    ('https://s1.onlyfakeai.ru/', 'GET'),
    ('https://s2.onlyfakeai.ru/', 'GET'),
    ('https://onlyfakeai.ru/robots.txt', 'GET'),
    ('https://onlyfakeai.ru/sitemap.xml', 'GET'),
]
res = {}
for url, method in targets:
    r = req(url, method=method)
    res[url] = r
    print(summarize(r))
    time.sleep(1.0)
json.dump(res, open(os.path.join(ev, 'service_probes.json'), 'w'), indent=1, ensure_ascii=False)
print('saved')
