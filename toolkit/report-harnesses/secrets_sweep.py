#!/usr/bin/env python3
"""Hunt 9: secrets sweep over the rehosted JS/source artifacts of onlyfakeai.ru.

Minified chunks are single-line, so we report byte offset + context snippet instead of line numbers.
Outputs found values with enough context to locate them (grep -bo '<value>' <file>).
"""
import os
import re

ROOT = "<WORKSPACE>/rehost/src"

PATTERNS = {
    "telegram_bot_token": re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{35}\b"),
    "jwt_any": re.compile(r"eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"),
    "supabase_secret_key": re.compile(r"sb_secret_[A-Za-z0-9_-]{10,}"),
    "supabase_publishable": re.compile(r"sb_publishable_[A-Za-z0-9_-]{10,}"),
    "google_api_key": re.compile(r"AIza[0-9A-Za-z_-]{35}"),
    "recaptcha_site_key": re.compile(r"6L[0-9A-Za-z_-]{38}"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "discord_webhook": re.compile(r"https://(?:ptb\.|canary\.)?discord(?:app)?\.com/api/webhooks/\d+/[A-Za-z0-9_-]+"),
    "webhook_site": re.compile(r"https://webhook\.site/[A-Za-z0-9-]+"),
    "private_key_block": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "yandex_maps_key": re.compile(r"NEXT_PUBLIC_YANDEX[A-Z_]*[\"']?\s*[:=]\s*[\"']([^\"']{10,})[\"']"),
    "env_assignments": re.compile(r"(?:NEXT_PUBLIC|VITE)_[A-Z0-9_]+"),
    "bot_token_var": re.compile(r"(?:TELEGRAM_BOT_TOKEN|telegramBotToken|BOT_TOKEN)[^,;{}]{0,120}"),
    "smtp_or_mail": re.compile(r"(?:smtp|mailgun|sendgrid|resend)[A-Za-z0-9_.:/@-]{0,80}", re.IGNORECASE),
    "openai_key": re.compile(r"sk-[A-Za-z0-9]{20,}"),
    "cloudflare_token": re.compile(r"(?:CLOUDFLARE|CF)_[A-Z_]*TOKEN[^,;{}]{0,100}"),
    "s3_url": re.compile(r"https://[A-Za-z0-9._-]*s3[A-Za-z0-9._-]*\.?[A-Za-z0-9._-]*/[^\s\"'`]{2,120}"),
    "internal_hosts": re.compile(r"https?://(?:localhost|127\.0\.0\.1|0\.0\.0\.0|[A-Za-z0-9_-]+\.internal)[:/][^\s\"'`]{0,80}"),
    "admin_route": re.compile(r"/api/[A-Za-z0-9_-]*(?:admin|internal|debug|test|secret)[A-Za-z0-9_/-]*"),
}

MAX_HITS_PER_PATTERN = 40


def main() -> None:
    files = []
    for dirpath, _dirnames, filenames in os.walk(ROOT):
        for fn in filenames:
            files.append(os.path.join(dirpath, fn))
    files.sort()
    print(f"scanned files: {len(files)}")
    for label, rx in PATTERNS.items():
        print(f"\n===== {label} =====")
        hits = 0
        for path in files:
            try:
                with open(path, "r", errors="replace") as fh:
                    text = fh.read()
            except OSError as exc:
                print(f"  [err] {path}: {exc}")
                continue
            for m in rx.finditer(text):
                hits += 1
                if hits > MAX_HITS_PER_PATTERN:
                    break
                start = max(0, m.start() - 70)
                end = min(len(text), m.end() + 70)
                snippet = text[start:end].replace("\n", " ")
                rel = os.path.relpath(path, ROOT)
                print(f"  [{rel} @byte {m.start()}] match={m.group(0)[:160]!r}")
                print(f"      ctx: ...{snippet}...")
            if hits > MAX_HITS_PER_PATTERN:
                break
        if hits == 0:
            print("  (none)")


if __name__ == "__main__":
    main()
