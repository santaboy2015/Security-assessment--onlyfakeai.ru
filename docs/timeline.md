# Engagement timeline

*A compressed operational timeline. Wall-clock times are UTC from the evidence logs; the whole engagement
ran over ~48 hours of working sessions.*

## Day 0 — Estate discovery & rehost reconnaissance

- Certificate transparency reveals the wildcard certificate and four live hostnames (`cdn`, `ops`, `www`,
  apex). **The admin plane was never linked from the public site** — CT alone found it.
- 141-name DNS brute: only known hosts + one dead Cloudflare Tunnel (`s3.*`, Error 1033).
- Next.js site crawl: 14 locales, 232 shop products, generator/auth/checkout shells.
- Public Supabase buckets identified; template buckets harvested (`id`, `dl`, `passport`, `residence`,
  `product` — 518 files, 155 country×doctype pairs, 2005–2025).
- Client bundles recovered and beautified; full route/API map extracted; rehost architecture documented.

## Day 1 — Application audit

- Auth settings recovered from GoTrue; JWT lane tested (alg family, JWKS, forgery matrix) — all walls held.
- RLS mapped on `profiles` / `jobs`; DB trigger found blocking privileged columns; upsert/INSERT/PK-move
  paths all closed.
- RPC surface enumerated (~780 PGRST202 probes) → 12 functions; anonymous `SECURITY DEFINER`
  aggregates leak live business metrics (13,804 profiles / 25,925 jobs).
- **Storage test: the `photos` bucket lists anonymously and serves every object from the public CDN with
  no credentials.** Scale quantified (99 objects / 88.3 MB on page one); bucket content archived by hash
  and counted (24,170 objects, 20.2 GiB) under read-only discipline.
- SSRF probes on job submission, status endpoints and image optimizer → zero callbacks.
- Rate-limit behaviour measured on every auth surface; ops login limiter identified as a **global**
  5-attempt/900 s window (availability bug).

## Day 2 — Admin plane & credential operations

- `ops.onlyfakeai.ru` mapped: `/health` version leak, `/script.js` (100 KB admin bundle served
  unauthenticated) → complete 16-endpoint API map.
- 199-request auth-gap matrix: route × auth-state × method × path-variant — no bypass.
- Signup oracle (`422 user_already_exists`) identifies 4 registered admin identities.
- 19,300 credential attempts across two channels (ops limiter + direct GoTrue via Tor circuit rotation) —
  **0 hits**; stop condition documented.
- Final reports written: vuln report (10 findings), admin-plane takeover report, round-2 addendum with
  trial totals and remaining finish paths.
- Operation closed; test-artefact inventory handed over *for cleanup.

## Post-engagement — packaging

- Evidence sanitised and indexed; raw request/response logs preserved.
- Photos bucket proven by manifest + stats + blurred proof sheet (no personal data published).
- This repository assembled: reports, harnesses, evidence, methodology, negative results.

---

*Full evidence: [`../evidence/`](../evidence/) · Phase detail: [`methodology.md`](methodology.md)*
