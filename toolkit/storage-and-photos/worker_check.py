import ssl, json, urllib.request, urllib.error

ctx = ssl.create_default_context()

def req(method, url, body=None, token=None):
    h = {"User-Agent": "Mozilla/5.0"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    if body is not None:
        h["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=40, context=ctx) as resp:
            return resp.status, resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, str(e)

tok = json.load(open("token.txt"))["access_token"]

# freshest job id from photos bucket = right now
jobs = ["1794335769597", "1794335700000", "1778112266686"]
for jid in jobs:
    st, txt = req("GET", f"https://onlyfakeai.ru/api/status/{jid}")
    print(f"status/{jid} -> {st} {txt[:300]}")

st, txt = req("GET", "https://onlyfakeai.ru/api/no-watermark/1794335769597", token=tok)
print("no-watermark ->", st, txt[:300])

# signature endpoint alive?
st, txt = req("POST", "https://onlyfakeai.ru/api/generate-signature",
              body={"jobId": "1794335769597"})
print("generate-signature ->", st, txt[:300])

# health of main site
st, txt = req("GET", "https://onlyfakeai.ru/api/health")
print("health ->", st, txt[:200])
