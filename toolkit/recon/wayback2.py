import ssl, json, urllib.request, urllib.error, time

ctx = ssl.create_default_context()

def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return r.status, r.read()
    except Exception as e:
        return 0, str(e).encode()

# wayback CDX for all urls under the domain
for dom in ["onlyfakeai.ru", "ops.onlyfakeai.ru", "cdn.onlyfakeai.ru"]:
    st, b = fetch(
        f"https://web.archive.org/cdx/search/cdx?url={dom}&matchType=domain"
        f"&output=json&fl=timestamp,original,statuscode,mimetype&limit=200&collapse=urlkey")
    print("=" * 10, dom, st, len(b))
    if st == 200:
        try:
            rows = json.loads(b)
            for r in rows[1:40]:
                print("  ", r)
        except Exception as e:
            print("   raw:", b[:300])
    time.sleep(3)
