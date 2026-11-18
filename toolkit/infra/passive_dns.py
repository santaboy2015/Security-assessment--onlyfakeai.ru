import json, os, sys, time, urllib.request, urllib.parse
EVID = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'evidence')
os.makedirs(EVID, exist_ok=True)
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
      'Accept': 'application/json,text/plain,*/*'}

def get(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        try:
            return json.loads(raw.decode('utf-8', 'replace'))
        except Exception:
            return raw.decode('utf-8', 'replace')

out = {}
def try_get(key, url):
    try:
        v = get(url)
        out[key] = v
        print(f'== {key} OK')
        s = json.dumps(v, ensure_ascii=False)
        print(s[:1800])
    except Exception as e:
        out[key] = {'error': str(e)}
        print(f'== {key} ERR {e}')
    time.sleep(1.2)

# 1) RIPE RDAP for the IP
try_get('ripe_rdap_ip', 'https://rdap.db.ripe.net/ip/2.59.219.71')
# 2) ip-api (free)
try_get('ipapi', 'https://ip-api.com/json/2.59.219.71?fields=status,country,countryCode,regionName,city,isp,org,as,asname,reverse,mobile,proxy,hosting')
# 3) hackertarget reverse IP
try_get('ht_reverseip', 'https://api.hackertarget.com/reverseiplookup/?q=2.59.219.71')
# 4) mnemonic passive DNS for IP
try_get('mnemonic_ip', 'https://api.mnemonic.no/pdns/v3/2.59.219.71')
# 5) mnemonic passive DNS for domain
try_get('mnemonic_domain', 'https://api.mnemonic.no/pdns/v3/onlyfakeai.ru')
# 6) OTX passive dns domain (may need key)
try_get('otx_domain', 'https://otx.alienvault.com/api/v1/indicators/domain/onlyfakeai.ru/passive_dns')
# 7) OTX for IP
try_get('otx_ip', 'https://otx.alienvault.com/api/v1/indicators/IPv4/2.59.219.71/passive_dns')
# 8) hackertarget hostsearch
try_get('ht_hostsearch', 'https://api.hackertarget.com/hostsearch/?q=onlyfakeai.ru')
# 9) urlscan search domain
try_get('urlscan_domain', 'https://urlscan.io/api/v1/search/?q=domain%3Aonlyfakeai.ru&size=100')
# 10) urlscan search ip
try_get('urlscan_ip', 'https://urlscan.io/api/v1/search/?q=ip%3A%222.59.219.71%22&size=100')

with open(os.path.join(EVID, 'passive_dns.json'), 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
print('saved')
