#!/usr/bin/env python3
"""Check exit IP per circuit + limiter key behavior."""
import socket, subprocess, time, json

CTRL=("127.0.0.1",9051); COOKIE="/tmp/tordata/control_auth_cookie"
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36"

def ctrl(cmd):
    s=socket.create_connection(CTRL,timeout=10)
    s.sendall(b"AUTHENTICATE "+open(COOKIE,"rb").read().hex().encode()+b"\r\n"); time.sleep(.15); s.recv(256)
    s.sendall(cmd+b"\r\n"); time.sleep(.2)
    try: return s.recv(1024)
    finally: s.close()

def curl(args, timeout=40):
    p=subprocess.run(["curl","-sS","-k","--socks5-hostname","127.0.0.1:9050","-m",str(timeout),"-A",UA]+args,capture_output=True,text=True)
    return p.stdout.strip()

for i in range(3):
    ctrl(b"SIGNAL NEWNYM"); time.sleep(4)
    ip = curl(["https://api.ipify.org"])
    hdr = curl(["-D","/tmp/h.txt","-o","/tmp/b.bin","-X","POST","-H","Content-Type: application/json",
                "-d", json.dumps({"email":"probe@example.com","password":"x"}), "https://ops.onlyfakeai.ru/api/auth/login"])
    rem=None
    for line in open("/tmp/h.txt",encoding="utf-8",errors="ignore"):
        if line.lower().startswith("ratelimit-remaining"): rem=line.strip()
    print(i, "exit_ip=", ip, "| headers:", rem, "| body:", open("/tmp/b.bin",encoding="utf-8",errors="ignore").read(120))
    time.sleep(1)
