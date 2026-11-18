# Evidence index — onlyfakeai.ru backend audit (task-3, vuln-rat)

All artefacts were produced on 2026-11-10 from the owner-authorized audit described in
[../VULN-REPORT.md](../VULN-REPORT.md). The directory is read-only evidence: do not edit the raw logs.

## Layout

- `raw/` — raw request/response logs (full tool output) and saved target artifacts.
- `scripts/` — every script used to produce the logs (bash + python3, run from WSL Kali).
  `scripts/env.sh` defines the target constants; `scripts/run.sh <script>.sh` runs one script and
  tees its output to `raw/<script>.log`.

## How to reproduce a log

```bash
# from WSL Kali
cd '<WORKSPACE>/rehost/report/evidence'
bash scripts/run.sh 00-baseline.sh
# or a python probe:
python3 scripts/03-idor.py | tee raw/03-idor.log
```

`scripts/env.sh` reads the test-account JWT from `/tmp/token.txt` (our own @dropmail.me test
account), the public Supabase URL and the public publishable key. No privileged material is stored here.

## Raw log map

| Log | Purpose |
|---|---|
| `00-baseline.log` | headers/fingerprint, API route behaviour with/without bearer |
| `01-auth-jwt.log` | forged/unsigned/expired JWT matrix |
| `02-bundle-context.log` | client-bundle API contracts (submit-photoshop-job, no-watermark, jobs ids, storage, recaptcha) |
| `02-rest-storage-rpc.log` | REST tables, storage buckets/list/upload/delete/sign, RPC enum, reCAPTCHA, OIDC, CORS |
| `03-idor.log` | public `photos` bucket listing + anon HEAD, job-ID probes, jobs RLS |
| `04-nextjs-proxy-api.log` | buildManifest/rewrites, `/api/supabase` proxy, generators, OIDC callback, source maps, RPC probes |
| `05-profiles-insert.log` | second account, INSERT/upsert/user_id escalation attempts, e-mail enumeration |
| `06-profile-delete-reinsert.log` | DELETE+re-INSERT privileged row attempt (blocked) |
| `07-ssrf.log` | webhook collector self-test, WSL listener, photoUrl/status/supabase/next-image SSRF attempts |
| `08-ratelimit.log` | 20× reCAPTCHA, 20× telegram-webapp, 8× signup, 10× bad login, password policy, recovery |
| `09-misc.log` | CVE-2025-29927 probes, profile columns, RPC params, crt.sh subdomains, public object HEAD |
| `09-secrets-sweep.log` | regex secret sweep over 54 rehosted client artifacts |
| `10-ops-subdomain.log` | `ops.onlyfakeai.ru` discovery (crt.sh), TLS, page/health/robots |
| `11-ops-admin.log` | admin app HTML/JS saved, endpoint probes, methods |
| `12-ops-analyze.log` | dashboard JS: API map, auth flow, localStorage token |
| `13-ops-auth-attacks.log` | admin API authz matrix, login validation/rate-limit, static/traversal leaks, forged JWT, CORS |
| `14-ops-xss-workers.log` | worker endpoint method matrix, extra unauth endpoints, headers |
| `14b-xss-analyze.log`, `14c-xss-sinks.log`, `14d-modal-code.txt` | stored-XSS sink review of the admin dashboard JS |
| `15-final-checks.log` | scale of public `photos` exposure, anon HEAD reads, role check, GoTrue settings |
| `ops-index.html`, `ops-login.html`, `ops-script.js`, `ops-health.json`, `ops-robots.txt` | saved copies of the exposed admin app |
| `site-home.html`, `site-home.headers` | main site capture |
| `crt-subdomains.json` | Certificate Transparency names for `*.onlyfakeai.ru` |
| `photos-bucket-listing-anon.json` | anon bucket listing (metadata only — no image bytes) |

## Safety notes

- No real user image/photo was downloaded; only bucket listing metadata and `HEAD` status/size/content-type.
- No destructive action was taken; only our throwaway @dropmail.me test accounts and one 30-byte
  test file in a writable storage bucket (`backgrounds/vulnrat-audit-1794321400.txt`, deletion denied
  by storage RLS) were created.
- Ops admin login was not brute-forced; the 15-minute lockout was reached during validation tests and
  testing stopped there.
