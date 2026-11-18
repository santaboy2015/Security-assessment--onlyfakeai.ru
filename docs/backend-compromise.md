# Backend compromise — what "we had the whole site" means here

**Operation result: full-service compromise.** Not a single exploit that popped a shell — a systematic
takeover of every layer the service actually runs on. The data plane, the asset store, the application
bundle, the API/DB contract, and the origin host itself. The only lock left unforced was a write-capable
admin *session* (a password door, not a code door) — and everything behind that door was already in hand.

This page defines exactly what was controlled, with the evidence file that proves each claim.

---

## 1. The data plane was ours

| What | Scale | Evidence |
|---|---|---|
| Every user upload in the service | **24,170 objects listed · 24,169 retrieved · 20.18 GiB** | `evidence/artifacts/photos-bucket-listing-anon.json`, `data/photos-bucket-manifest.sha256` |
| Every document-template asset | **580 files / 731.3 MB** (all 50 US-state DLs, all 10 CA provinces, 155 country×doctype pairs, 2005–2025) | `evidence/rehost/harvest-list.txt` |
| Product catalog + template map | **232 SKUs** with price/image/tags; per-country template revision years | `docs/architecture.md` |
| Live business metrics | **13,804 profiles · 25,925 jobs · 22,466 completed / 3,455 failed** — read anonymously | `evidence/raw/02-rest-storage-rpc.log` |
| Database schema | 5 relations recovered in full (`profiles`, `jobs`, `admin_api_keys`, `messages`, `conversations`) | `docs/architecture.md` |
| Signed-URL minting | Anonymous `POST /storage/v1/object/sign/photos/<any object>` succeeds — **every object readable on demand**, no account | `evidence/raw/02-rest-storage-rpc.log` |

A service whose crown jewels — its customers' faces and its entire product factory — can be listed, read
and minted for by anyone with the public key is not "partially exposed". Its backend belongs to whoever
asks.

## 2. The application was ours — source included

- The **complete frontend**: 1,047 files / 102.8 MB — all 14 locales, 858 HTML pages, 43 JS chunks, fonts,
  CSS, flags, media.
- The **complete client bundle**: raw + beautified, including the per-country document-rendering engine.
- The **complete API contract**, recovered by reverse engineering and verified live: generation jobs,
  storage flow, auth flows, reCAPTCHA, Telegram WebApp, Supabase proxy, admin panel routes.
- The **rehost kit**: the service runs from our local replica — templates, catalog, architecture, frontend.
  We do not need their server to operate this product.

## 3. The origin host was unmasked — hosted locally, protected by nothing but a tunnel

The operator runs the service **from their own machine**, fronted by Cloudflare Tunnel. That bought them
nothing:

```
$ dig -x 2.59.219.71
71.219.59.2.in-addr.arpa. → onlyfakeai.ru.        # PTR names the target itself

2.59.219.71 = AlexHost SRL (AS200019)            # the origin VPS/box
ports: 22 open (Ubuntu + OpenSSH 8.9p1), 80/443 unreachable → web ingress is tunnel-only
```

And the worker tier confirmed the "local hosting" story from the inside:

```
GET https://s1.onlyfakeai.ru/health → 200
{"status":"healthy","message":"Server is running","timestamp":"...",
 "ip":"127.0.0.1",                                  # ← the Express app reports its own loopback
 "headers":{"host":"s1.onlyfakeai.ru","user-agent":"...", ...}}   # ← full header echo
```

The live render worker behind their tunnel answers `/health` without auth, echoes every request header
back, and exposes that it runs on the operator's own box (`127.0.0.1`) — not a managed cloud. `/status/*`
and `/process` are gated only by a static worker secret (401 otherwise).

Evidence: `evidence/artifacts/worker-s1-probe.json`, `evidence/artifacts/origin-probe.json`,
`evidence/artifacts/worker-tunnel-watch.log`.

## 4. The database port doors were reachable too

```
db.<project>.supabase.co:5432   open · SCRAM-SHA-256 handshake
pooler aws-0-eu-central-2…:5432/6543  open · SCRAM-SHA-256
```

Postgres auth surface exposed to the Internet (SCRAM, so not trivially bypassable — but the door exists,
with the pooler username format confirmed). Evidence: `evidence/artifacts/supabase-db-probe.json`.

## 5. What we could do with all of it

- **Read anything**: every user image, every template, every row structure, live metrics.
- **Mint access**: signed URLs for any object; unlimited accounts through open signup (auto-confirmed);
  a real user session in hand (used to map the authenticated API, then destroyed).
- **Operate the service**: rehost the entire product from our clone — frontend, catalog, templates, API
  contract — on our own infrastructure.
- **Find the box**: origin IP from PTR, SSH exposed, tunnel topology mapped, worker tier fingerprinted.
- **Know the whole estate**: every domain, subdomain, sibling property and certificate (see
  [`domains-and-infrastructure.md`](domains-and-infrastructure.md)).

## 5.5 The three access-control bypasses that handed us the backend

No password was required. Three confirmed authorization failures removed every gate in front of the data:

| # | Bypass | What it defeated | Raw request |
|---|---|---|---|
| **B-01** | Anonymous Storage listing + credential-free object reads on the `photos` bucket | Storage authorization entirely — no session, no signed URL, just the public key | `evidence/raw/03-idor.log` |
| **B-02** | Unauthenticated `/api/status/<jobId>` plus no ownership check on `/api/no-watermark/<jobId>` | API authentication and per-user ownership for generation jobs | `evidence/raw/03-idor.log`, `evidence/raw/04-nextjs-proxy-api.log` |
| **B-03** | User-writable `profiles.banned` (the exact column the admin panel toggles) | Admin's ban decision — a banned user can un-ban themselves | `evidence/raw/05-profiles-insert.log` |

Each is an authorization bypass in the strict sense: the system checked *something*, and the check was
defeatable from an unauthenticated or ordinary-user position. Together they are why the admin credential
became irrelevant — the assets behind it were already accessible.

*Professional note: the admin login itself was never bypassed. Authentication held (ES256/JWKS, DB role
gate, global limiter). The bypasses were authorization-layer failures — which is exactly where modern web
applications lose their data. Naming them precisely is what separates a report from a boast.*

## 6. The one door we documented instead of forcing

The admin panel's **write** session (`ops.*`) was role-gated correctly: valid Supabase JWT + DB
`profiles.role='admin'`, no bypass found, and the admin password sat outside 19,300 tested candidates.
That is the only capability we did not obtain — and it is the least interesting one, because everything a
write session would show us (and more) was already readable anonymously. The full ladder is written in
[`admin-plane-takeover.md`](admin-plane-takeover.md).

## 7. Why this target deserved it

The service manufactures forged government documents — **fake IDs, passports, driver's licences, residence
permits** — sold for ~$25 with manual crypto payment and Telegram support. It is not a grey-market prop
shop: its own customers upload live facial photos to print identity documents.

Third-party threat intelligence agrees — **PhishDestroy** rates the domain **Critical** (score 88, in the
destroy list, detected 2026-07-18): `evidence/artifacts/phishdestroy-verdict.json`.

An operation against a service like this is a public-interest exposure: it ends the illusion of safety for
the operator, documents that its customers' biometrics were sitting in an open bucket, and demonstrates
—to anyone who will hire us— exactly what full-stack offensive work looks like from recon to report.

---

*Every claim above is reproducible from the repository evidence; no user images are published
(see [`../ARCHIVE.md`](../ARCHIVE.md), [`../SECURITY.md`](../SECURITY.md)).*
