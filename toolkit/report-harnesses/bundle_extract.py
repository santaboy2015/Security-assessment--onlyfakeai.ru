#!/usr/bin/env python3
"""Extract API call context from the onlyfakeai.ru Next.js client bundles.

Minified chunks are single-line; this prints byte-offset + a context window around each
keyword so the exact request/response schema used by the frontend can be reconstructed.
"""
import os

ROOT = "<WORKSPACE>/rehost/src"
FILES = [
    "app/page-bf5f8970043f7336.js",
    "app/8794-9e09a720aa8a0cf1.js",
    "app/8875-e8c048e6d4ba117e.js",
    "app/page-10ca31bf4df29208.js",
    "js/page-7ec00b8de687c57f.js",
    "js/layout-7ad3dad986f259e9.js",
]
KEYWORDS = [
    "submit-photoshop-job",
    "no-watermark",
    "remove-background",
    "verify-recaptcha",
    "telegram-oidc",
    "telegram-webapp",
    "jobId",
    "job_id",
    "signature",
    "generate-signature",
    "portraits/list",
    "auto_delete",
    "secret_key",
    "generations_left",
    "storage/v1",
    "upload(",
    "getPublicUrl",
    "createSignedUrl",
    "download(",
    "broadcast",
    "maintenance-status",
    "x-recaptcha",
    "recaptchaToken",
    "Authorization",
    "status/",
]
WINDOW = 420
MAX_PER_KEYWORD = 6


def main() -> None:
    for rel in FILES:
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            print(f"!! missing {path}")
            continue
        with open(path, "r", errors="replace") as fh:
            text = fh.read()
        print(f"\n################ FILE {rel} ({len(text)} bytes) ################")
        for kw in KEYWORDS:
            idx = 0
            hits = 0
            while True:
                pos = text.find(kw, idx)
                if pos < 0 or hits >= MAX_PER_KEYWORD:
                    break
                start = max(0, pos - WINDOW)
                end = min(len(text), pos + len(kw) + WINDOW)
                print(f"\n--- [{kw}] @byte {pos}")
                print(text[start:end].replace("\n", " "))
                idx = pos + len(kw)
                hits += 1


if __name__ == "__main__":
    main()
