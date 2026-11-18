# Evidence index

Every claim in [`../README.md`](../README.md) and the reports maps to a file here. The reports cite these
exact names, so this index doubles as the reproduction map.

## Raw HTTP exchanges (`evidence/raw/`)

Sanitised but otherwise verbatim request/response transcripts captured at engagement time.

| File | What it proves |
|---|---|
| `00-baseline.log` | Baseline fingerprint: headers, API route auth states, well-known files, CORS |
| `01-auth-jwt.log` | JWT forgery matrix (alg:none / HS256 / tampered) vs REST + Next API |
| `02-bundle-context.log` | Request contracts extracted from client bundles (job submit, watermark, storage, recaptcha) |
| `02-rest-storage-rpc.log` | REST table exposure, storage buckets, signed URLs, RPC enum, reCAPTCHA, OIDC, CORS |
| `03-idor.log` | Anonymous `photos` listing, HEAD reads, job-ID probes, anon uploads, jobs RLS |
| `04-nextjs-proxy-api.log` | `_buildManifest.js` rewrites, Supabase proxy, OpenAPI block, generators, image-optimizer SSRF, OIDC callback, RPC probing |
| `05-profiles-insert.log` | Account creation, INSERT/upsert/`user_id` escalation attempts, cross-user PATCH, enumeration |
| `06-profile-delete-reinsert.log` | Self-DELETE + re-INSERT escalation attempt (blocked) |
| `07-ssrf.log` | Collector self-test; photoUrl/status/supabase/image-optimizer/remove-background SSRF — zero callbacks |
| `08-ratelimit.log` | 20× reCAPTCHA, 20× telegram-webapp, 8× signup, 10× bad login; password policy; recovery enumeration |
| `09-misc.log` | CVE-2025-29927 probes, profile column reachability, RPC params, Next version search, crt.sh, HEAD reads |
| `09-secrets-sweep.log` | Full regex secret sweep over 54 rehosted artifacts — none found |
| `10-ops-subdomain.log` | `ops.onlyfakeai.ru` discovery, TLS cert, pages, `/health`, robots, DNS |
| `11-ops-admin.log` | Admin panel HTML/JS analysis, endpoint probes, OPTIONS matrix |
| `12-ops-analyze.log` | Admin API map + auth flow extraction |
| `13-ops-auth-attacks.log` | Admin API authz matrix (none/own/forged), login validation + rate-limit, leak probes, forged JWT matrix, CORS |
| `14-ops-xss-workers.log` | Worker/process endpoint method matrix, more unauthenticated endpoints, CSP |
| `14b-xss-analyze.log` / `14c-xss-sinks.log` / `14d-modal-code.txt` | Admin bundle XSS-sink review: 28 `innerHTML` sites, `escapeHtml` coverage, modal code |
| `15-final-checks.log` | Scale of `photos` exposure, anon HEAD reads, role check, auth settings |

## Captured artefacts (`evidence/artifacts/`)

| File | What it is |
|---|---|
| `ops-admin-panel.html` | The admin dashboard HTML, as served **unauthenticated** |
| `ops-login.html` | Admin login page |
| `ops-admin-bundle.js` | The 100 KB `/script.js` bundle: the complete admin API map — public without auth |
| `ops-health.json` | `/health` response — version + uptime leak |
| `photos-bucket-listing-anon.json` | The anonymous bucket listing itself: object names, sizes, timestamps — the smoking gun for V-01 |
| `crt-subdomains.json` | Certificate-transparency result that found the estate |
| `site-home.headers` | Edge/response-header fingerprint |
| `worker-s1-probe.json` | Worker tier matrix — `/health` loopback + header echo, `/status` + `/process` 401 |
| `worker-tunnel-watch.log` | Tunnel watcher: `s2`/`s3` dead (1033), `s1` live Express health |
| `origin-probe.json` | PTR → origin `2.59.219.71`, open ports (SSH 22), origin HTTP/TLS behaviour |
| `intel-checkhost-status.json` | Third-party TCP check results for the origin host |
| `supabase-db-probe.json` | Postgres pooler / direct DB port reachability, SCRAM handshakes |
| `brand-variants.json` | Domain variant DNS map — `onlyfakeai.com` shares the operator's nameservers |
| `brand-sites.json` | Brand/typo-site liveness fingerprints |
| `siblings.jsonl` | Sibling-domain DNS records (`onlyfakeai.*`, `onlyfake.*`, `fakeai.ru`, …) |
| `subdomain-brute-summary.json` | 5,063-name brute result: the 9 live `onlyfakeai.ru` subdomains |
| `certspotter-com.json` / `crtsh-com.json` | `.com` twin certificates (wildcard, same operator) |
| `live360-probe.json` | `live360.onlyfakeai.ru` app fingerprint |
| `email-posture.jsonl` | DMARC / MTA-STS / mail-posture lookups (NXDOMAIN evidence) |
| `phishdestroy-verdict.json` | Third-party threat-intel verdict: **Critical, score 88, destroy list** |

## Rehost workstream (`evidence/rehost/`)

| File | What it is |
|---|---|
| `harvest-notes.md` | Methodology for the template-bucket harvest (public product material only) |
| `harvest-list.txt` | SHA-256 manifest of harvested template files |

## Photos bucket proof (`data/`)

| File | What it is |
|---|---|
| `photos-bucket-manifest.sha256` | SHA-256 + size + filename for **every** object (24,170 lines) |
| `photos-bucket-stats.json` | Count, total bytes, timestamp range, naming scheme, provenance |
| `proof/photos-bucket-sample-blurred.jpg` | 12 samples with faces destroyed — proof of content type and scale, zero PII |

## Reproducible harnesses

- [`toolkit/`](../toolkit/) — curated harnesses by phase (recon, auth, API, ops panel, credential ops,
  storage/photos).
- [`toolkit/report-harnesses/`](../toolkit/report-harnesses/) — the numbered scripts referenced by the
  report (`00-baseline.sh` … `15-final-checks.sh`, `jwt_forge.py`, `secrets_sweep.py`, `xss_analyze.py`, …).
