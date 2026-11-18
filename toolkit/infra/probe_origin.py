import socket, ssl, json, time, urllib.request, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import doh

IP = '2.59.219.71'
EVID = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'evidence')
os.makedirs(EVID, exist_ok=True)
out = {}

# 1) PTR
rev = '.'.join(reversed(IP.split('.'))) + '.in-addr.arpa'
rec = doh.query(rev, 'PTR')
doh.log(rec, 'origin_ptr')
out['ptr'] = rec
print('PTR:', doh.summarize(rec))

# 2) ipinfo
for url in [f'https://ipinfo.io/{IP}/json', f'https://ipinfo.io/{IP}/json?token=']:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'infra-audit/1.0'})
        j = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())
        out['ipinfo'] = j
        print('IPINFO:', json.dumps(j))
        break
    except Exception as e:
        print('ipinfo err', e)
    time.sleep(1)

# 3) TCP port checks (single connect each, no payload except TLS/banner read)
ports = [22, 25, 80, 443, 465, 587, 993, 3000, 3001, 4000, 5000, 5432, 6543, 8000, 8080, 8443, 9000, 9090, 10000]
open_ports = []
for p in ports:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    try:
        r = s.connect_ex((IP, p))
        if r == 0:
            open_ports.append(p)
            banner = b''
            if p in (25, 587, 465, 993):
                try:
                    s.settimeout(2)
                    banner = s.recv(256)
                except Exception:
                    pass
            print(f'PORT {p} OPEN banner={banner[:120]!r}')
    except Exception as e:
        pass
    finally:
        try: s.close()
        except: pass
    time.sleep(0.15)
out['open_ports'] = open_ports

# 4) TLS cert for a few SNI names
cert_info = {}
for sni in ['onlyfakeai.ru', 'ops.onlyfakeai.ru', 'cdn.onlyfakeai.ru', 'mail.onlyfakeai.ru', None]:
    key = sni or '<none>'
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with socket.create_connection((IP, 443), timeout=6) as sock:
            with ctx.wrap_socket(sock, server_hostname=sni) as ss:
                der = ss.getpeercert(binary_form=True)
                cert = ss.getpeercert()
        cert_info[key] = {'subject': cert.get('subject'), 'issuer': cert.get('issuer'),
                          'subjectAltName': cert.get('subjectAltName'),
                          'notBefore': cert.get('notBefore'), 'notAfter': cert.get('notAfter'),
                          'der_len': len(der) if der else 0}
        print(f'TLS[{key}] issuer={cert.get("issuer")} SAN={cert.get("subjectAltName")} notAfter={cert.get("notAfter")}')
    except Exception as e:
        cert_info[key] = {'error': str(e)}
        print(f'TLS[{key}] ERROR {e}')
    time.sleep(0.5)
out['tls'] = cert_info

# 5) HTTP checks with Host header
http_res = {}
def http_get(url, host=None, verify=False):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36',
               'Accept': 'text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8'}
    if host:
        headers['Host'] = host
    req = urllib.request.Request(url, headers=headers)
    try:
        r = urllib.request.urlopen(req, timeout=12, context=ctx)
        body = r.read(3000)
        return {'url': url, 'host_header': host, 'status': r.status, 'headers': dict(r.headers), 'body_head': body[:1500].decode('utf-8', 'replace')}
    except urllib.error.HTTPError as e:
        body = e.read(2000)
        return {'url': url, 'host_header': host, 'status': e.code, 'headers': dict(e.headers), 'body_head': body[:1500].decode('utf-8', 'replace')}
    except Exception as e:
        return {'url': url, 'host_header': host, 'error': str(e)}

probes = [
    (f'https://{IP}/', None),
    (f'https://{IP}/', 'onlyfakeai.ru'),
    (f'https://{IP}/', 'ops.onlyfakeai.ru'),
    (f'https://{IP}/', 'cdn.onlyfakeai.ru'),
    (f'https://{IP}/', 'www.onlyfakeai.ru'),
]
for url, host in probes:
    r = http_get(url, host)
    http_res[f'{url}|{host}'] = r
    h = r.get('headers', {})
    keep = {k: v for k, v in h.items() if k.lower() in ('server', 'x-powered-by', 'via', 'cf-ray', 'x-vercel-id', 'x-nextjs-cache', 'content-type', 'location', 'set-cookie', 'x-frame-options', 'strict-transport-security', 'x-served-by')}
    print(f'HTTP {url} Host={host} -> status={r.get("status")} err={r.get("error")} hdr={json.dumps(keep)} body={ (r.get("body_head") or "")[:200]!r}')
    time.sleep(1.0)
out['http'] = http_res

with open(os.path.join(EVID, 'origin_probe.json'), 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=1, ensure_ascii=False, default=str)
print('saved', os.path.join(EVID, 'origin_probe.json'))
