# Negative results — the walls that held

*A penetration test is only as good as its negative results. This page exists so the next tester
(or the owner) doesn't re-spend the same hours on paths that were already proven closed.*

Every row was tested live against the production estate. Evidence logs are under
[`../evidence/raw/`](../evidence/raw/).

---

## 1. Authentication & token layer

| Attempt | Result |
|---|---|
| `alg:none` JWT (with/without trailing dot) against REST + Next API | Rejected — `PGRST301 JWSError JWSNoSignatures` / `401 Invalid authentication token` |
| HS256 token signed with publishable key, `"supabase"`, `""`, `jwt_secret`, user id | Rejected — `JWSInvalidSignature` |
| Tampered `exp` (expired / far-future) | Rejected |
| `user_metadata.role = admin` self-write | Accepted by GoTrue, **ignored** by server: `/api/auth/verify` still `403 role 'user'` |
| `app_metadata` self-write | `403 not_admin` (GoTrue refuses) |
| Signup with metadata `{role:admin,isSuperAdmin:true,plan:ultimate}` | Account created, profile still `role='user'` (trigger ignores metadata) |
| Telegram WebApp `initData` forgery (20 payloads) | `401 Invalid Telegram Web App data` — HMAC validated server-side |
| OIDC `state`/`error` tampering, `locale=../../evil`, `//evil` open-redirect attempts | `307` to fixed `redirect_uri`; PKCE S256 + HttpOnly SameSite cookie flow held |
| reCAPTCHA empty/garbage/unknown-action | Fail-closed `400` |
| Auth transports: `?access_token=`, `apikey:` header, cookies, lowercase / double-space `Bearer` | All rejected or hit the role gate; no transport confusion |

## 2. Database layer (Supabase / PostgREST)

| Attempt | Result |
|---|---|
| INSERT self as admin | `409` duplicate / `42501` RLS |
| INSERT foreign `user_id` | `42501 RLS violation` |
| Upsert `merge-duplicates` on `profiles` | `P0001 Not authorized to change privileged profile fields` |
| PK move (write `user_id` of another row) | `42501` |
| Cross-user PATCH / DELETE own row | `0 rows` affected |
| Privileged columns (`role`, `generations_left`, `activePlan`, `payment_*`) | Blocked by DB trigger via every write path |
| RPC name-space sweep (~780 requests) | Only 12 functions; no `set_role` / `grant_admin` / `promote` / `exec_sql` exists |
| Table enumeration (~70 names) | Exactly 4 tables visible: `profiles`, `jobs`, `admin_api_keys`, `messages` — and RLS filters every one to own rows (empty for anon) |
| PostgREST OpenAPI / root | `401 Secret API key required`; `pg_graphql` disabled |
| Storage write abuse (anon/authed upload) | RLS `AccessDenied` |
| Other public buckets (`id`, `dl`, `passport`, `residence`, `product`, `backgrounds`) | Public readability is **by product design** (document templates); no user PII in them |

## 3. Admin plane (`ops.onlyfakeai.ru`, Express)

| Attempt | Result |
|---|---|
| All 10 live `/api/*` routes, unauthenticated | `401 Access token required` (route discovered by 401-JSON vs 404-HTML) |
| Valid **non-admin** user token | `403 Admin privileges required` — role read from `profiles`, not token claims |
| Forged tokens (`alg:none`, HS256, 8 secrets, forged role/isSuperAdmin claims) | Rejected with explicit alg/signature errors |
| Unsafe methods on real routes (POST/PUT/PATCH/DELETE, random-UUID target, empty body) | All `401` before route logic |
| Path variants (`/API/…`, `/api/./admin-users`, `//`, `%2f`, `%20`, `;`, `%00`, traversal `../`) | Either normalised to the same role gate or `404` / Node `400` — no bypass |
| Header tricks (`X-HTTP-Method-Override`, `X-Original-URL`, `X-Rewrite-URL`, `X-Forwarded-*`) | Ignored |
| IP spoof (`X-Forwarded-For: 127.0.0.1`, `CF-Connecting-IP`) | No effect; CF rejects spoofed `CF-Connecting-IP` at the edge |
| Query / body pollution (`?role=admin`, `?__proto__[role]=admin`, JSON proto payloads) | No effect |
| Static leak scan (~90 paths: `.env`, `.git`, source maps, backups, dumps) | Nothing but `/robots.txt` + `/health` |
| Stored XSS in admin panel (28 `innerHTML` sinks audited) | `escapeHtml()` at 38 sites; no unescaped attacker-controlled field found |
| CORS preflight | `Access-Control-Allow-Origin: *` **is** present — but admin token lives in `localStorage`, not a cookie, so no credentialed browser path |

## 4. Next.js / edge layer

| Attempt | Result |
|---|---|
| CVE-2025-29927 middleware-bypass (`x-middleware-subrequest`) | No behaviour change (no middleware-based auth to bypass) |
| React2Shell / RSC RCE chain (CVE-2025-55182) | Cloudflare semantic WAF returned `403` for 16 evasions; also not proven patched server-side, but unreachable from public edge |
| Next.js image-optimizer SSRF (`/_next/image?url=169.254.169.254`, WSL host, `file://`) | `400 url parameter is not allowed` — no fetch |
| `/api/supabase/*` proxy path tricks (`..%2F`, `//host`, encoded) | `404 requested path is invalid` |
| Build-manifest / source-map leak | Rewrites public (documented), no source maps |
| Response-header leakage | `x-powered-by: Next.js` only; no stacks, no secrets |

## 5. SSRF surface

| Endpoint | Result |
|---|---|
| `POST /api/submit-photoshop-job` `photoUrl` → attacker collector | Blocked earlier by credit gate (`403 No generations left`); no fetch reached collector |
| `/api/status/<jobId>` path/URL injection, cloud-metadata URLs | Generic `500`; no callback, no timing signal (workers were down) |
| `/api/remove-background` (unauthenticated multipart) | Proxies only valid images to internal service; ImageTragick-style payload gave plain `500` |

## 6. Credential operations

| Metric | Result |
|---|---|
| Admin identities found | 4 registered (`onlyfake@tuta.io`, `admin@`, `support@`, `onlyfake@` on the target domain) |
| Attempts executed | **19,300** across two channels |
| Channels | Ops login (global limiter, 5/900 s worldwide) + direct GoTrue (per-IP limiter, Tor circuit rotation) |
| Candidate classes | Brand mutations, operator OSINT aliases + years/leet, dates, rockyou top slice, 10k common |
| Valid credentials | **0** |

**Conclusion:** the admin password is outside the tested guessable space. The door is a credential door,
not a code door.

## 7. OSINT / infrastructure shortcuts

| Attempt | Result |
|---|---|
| Wayback / Common Crawl for `ops.*` | 0 captures |
| GitHub / grep.app for the project | Nothing |
| urlscan public scans | None of `ops` |
| 141-name subdomain brute | Only the known hosts + one dead CF tunnel (`s3.*`, Error 1033) |
| Origin IP discovery | None — Cloudflare Tunnel architecture, no inbound web ports, no DNS leak |

---

*Negative results are re-testable: run the matching numbered script in
[`../toolkit/report-harnesses/`](../toolkit/report-harnesses/).*
