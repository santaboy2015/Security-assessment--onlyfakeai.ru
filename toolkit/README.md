# Toolkit

The actual harnesses, in the order they were used. These are **engagement scripts**, not polished products —
they were written to answer a question against a live target, and every one of them ran for real.
Paths and identifiers are sanitised (`<WORKSPACE>`, `<target>`, `<publishable-key>`); set them in `env.sh`
or at the top of each script before reuse.

| Folder | Phase | What it does |
|---|---|---|
| `recon/` | Estate discovery | DNS/CT enumeration, exposure/surface mapping, bundle extraction, OSINT, content discovery |
| `auth/` | Trust boundaries | JWT forgery matrix, `user_metadata` injection, RLS/role tests, RPC fuzzing, redirect/SSRF probes |
| `api/` | Application fuzzing | 40+ numbered probes against the Next.js API, Supabase proxy, PostgREST, Storage, Realtime |
| `ops-panel/` | Admin plane | Route discovery, auth-gap matrix, credential oracle, rate-limit measurement |
| `credential-harness/` | Credential operations | Wordlist builders, queue generators, pacing/limiter analysis, Tor circuit sprayers |
| `storage-and-photos/` | Storage abuse | Bucket listing/fingerprinting, object-presence enumeration, bulk metadata collection |
| `report-harnesses/` | Reproduction | The numbered scripts cited by the reports — run these to reproduce specific findings |

## Running anything

```bash
export TARGET="https://<target>"
export CDN="https://cdn.<target>"          # Supabase gateway
export PUBKEY="<publishable-key>"          # public by design
python3 api/app_probe1.py
```

## Ground rules these scripts encode

- Read-only by default: no destructive method is ever sent with a valid token against a real identifier.
- Pacing: request loops include sleeps; the fuzzers were deliberately throttled to a few requests/second.
- Every probe writes its own log next to itself — the report's evidence trail was built this way.

## What is NOT here

- No credential lists (excluded for size and safety).
- No captured sessions/tokens/cookies.
- No raw user content.

If a script references a wordlist path, provide your own.
