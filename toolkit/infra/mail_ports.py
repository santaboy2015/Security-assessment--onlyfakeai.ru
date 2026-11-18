import json, os, time, urllib.request
ev = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'evidence')
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0 Safari/537.36', 'Accept': 'application/json'}

def get(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8', 'replace'))

out = {}
for port, nodes in [(25, 8), (993, 3), (587, 3), (465, 3)]:
    try:
        j = get(f'https://check-host.net/check-tcp?host=2.59.219.71:{port}&max_nodes={nodes}')
        rid = j['request_id']
        time.sleep(10)
        res = get(f'https://check-host.net/check-result/{rid}')
        ok = sum(1 for v in res.values() if isinstance(v, list) and v and v[0].get('address'))
        print(f'port {port}: nodes={len(res)} connected={ok} :: {json.dumps(res, ensure_ascii=False)[:500]}')
        out[port] = {'connected': ok, 'total': len(res), 'raw': res}
    except Exception as e:
        print('port', port, 'ERR', e)
        out[port] = {'error': str(e)}
    time.sleep(3)
json.dump(out, open(os.path.join(ev, 'mail_ports_checkhost.json'), 'w'), indent=1, ensure_ascii=False)
print('saved')
