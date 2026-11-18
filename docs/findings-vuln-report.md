# Backend Vulnerability Audit — onlyfakeai.ru

**Engagement:** owner-authorized security audit (task `task-3`) — *no destructive testing, no DoS, only our own test accounts; real user content was not downloaded.*
**Date:** 2026-11-10
**Auditor:** vuln-rat (team member), per Team Lead instruction
**Assets in scope:** `onlyfakeai.ru` (Next.js + Cloudflare), `cdn.onlyfakeai.ru` (Supabase gateway/project `mcdcezagfjuagbuwsjv`, GoTrue v2.197.0), and the discovered backend host `ops.onlyfakeai.ru`.
**Evidence directory:** [`evidence/`](evidence/) — raw request/response logs, saved JS/HTML, and every helper script used (see [evidence/README.md](evidence/README.md)).

---

## 1. Executive summary

The main site's client/API plane is **reasonably hardened**: JWT signature validation (ES256) is enforced everywhere we tested, forged/unsigned JWTs are rejected, Telegram WebApp `initData` signatures are validated, the OIDC flow uses PKCE + state with a fixed redirect URI, the reCAPTCHA verification endpoint fails closed, Next.js source maps are not served, and the profile table's privilege-escalation surface (privileged columns, INSERT/upsert/delete/PK-move) is blocked by a database trigger plus RLS. No server secret (service_role key, Telegram bot token, JWT secret) was found in the rehosted client bundles.

However, two **high-severity exposures** were confirmed and one **large attack surface was newly discovered**:

1. **`ops.onlyfakeai.ru` — a publicly reachable Express "Admin Dashboard"** (login + full control panel: profiles, jobs, admins, API keys, credit/plan assignment, analytics). The panel's API is properly gated by a Supabase JWT + database role check (`admin` required) and its login is rate-limited (429 + Retry-After observed), but the interface is exposed on the public Internet with no IP allow-listing, exposes the complete admin API map via `/script.js`, and `/health` leaks the app version/uptime. It is the single most valuable target on this estate: one admin credential (or one write of `profiles.role='admin'`) yields full backend control.
2. **Public Supabase bucket `photos` leaks user-generated document preview images.** With only the *publishable* key (which is embedded in the public JS bundle), an anonymous caller can list the bucket (`POST /storage/v1/object/list/photos`) and read objects over the public CDN URL with **no credentials at all**. One page of 100 objects contained 99 real user PNGs totalling **88.3 MB**; filenames are `<unix-ms>_preview.png` and are trivially predictable/enumerable. This is a privacy/PII exposure (generated document previews, likely containing portraits and document data).
3. **A user-controlled `banned` column** on `profiles` (PATCH allowed by RLS) most likely allows **self-unban/ban evasion**, and user-writable `email`/`remarks`/`secret_key` pollute the admin panel's view of accounts. The admin panel does escape rendered values (static check), so this is a logic/integrity issue, not XSS.

Secondary findings: unauthenticated job-status endpoint `/api/status/<jobId>` that fans out to internal workers (all workers were down during the test → only generic 500s, so live cross-user access could not be demonstrated), an unauthenticated signature-generation endpoint, wide-open CORS headers, and account-abuse controls that are weak on the main site while present on the admin panel.

**Confirmed takeover?** No. Full backend takeover was **not achieved** from an unauthenticated position: the admin panel requires `profiles.role='admin'`, the privileged-column trigger blocks writing that role from the web, and no service key/secret was recovered. The concrete remaining path is credential/role acquisition (see §7 "Takeover path" and §8 "Not confirmed / needs credentials").

### Findings at a glance

| ID | Severity | Finding | Primary endpoint | Evidence |
|----|----------|---------|------------------|----------|
| V-01 | **High** | Anonymous listing + unauthenticated read of user-generated images in Supabase bucket `photos` | `POST /storage/v1/object/list/photos`, `GET /storage/v1/object/public/photos/<name>` | `raw/03-idor.log`, `raw/15-final-checks.log`, `raw/photos-bucket-listing-anon.json` |
| V-02 | **High** | Publicly exposed admin control panel `ops.onlyfakeai.ru` (login, dashboard, admin API map, health/version) | `https://ops.onlyfakeai.ru/{,login,health,script.js}` | `raw/10-ops-subdomain.log`, `raw/11-ops-admin.log`, `raw/13-ops-auth-attacks.log` |
| V-03 | Medium | Unauthenticated job-status endpoint fanning out to internal workers; ownership on `/api/no-watermark/<jobId>` not verifiable (workers down) → IDOR risk | `/api/status/<jobId>`, `/api/no-watermark/<jobId>` | `raw/03-idor.log`, `raw/04-nextjs-proxy-api.log` |
| V-04 | Medium | Open registration without e-mail verification or server-enforced CAPTCHA; weak password policy; e-mail enumeration | `POST /auth/v1/signup` | `raw/08-ratelimit.log`, `raw/05-profiles-insert.log` |
| V-05 | Medium | User-writable `profiles.banned` (and `email`, `remarks`, `secret_key`) → probable ban evasion / integrity abuse | `PATCH /rest/v1/profiles` | `raw/09-misc.log`, `raw/05-profiles-insert.log` |
| V-06 | Low | CORS misconfiguration: `Access-Control-Allow-Origin: *` on the site + `Access-Control-Allow-Credentials: true`; wildcard on admin API; Supabase REST reflects any Origin | all site/ops responses | `raw/00-baseline.log`, `raw/13-ops-auth-attacks.log` |
| V-07 | Low | Information disclosure: admin app version/uptime, full admin API map in `/script.js`, Next.js build manifest/rewrites, `x-powered-by` | `ops /health`, `ops /script.js`, `/_next/static/<build>/_buildManifest.js` | `raw/10-ops-subdomain.log`, `raw/11-ops-admin.log`, `raw/04-nextjs-proxy-api.log` |
| V-08 | Low | Unauthenticated compute endpoint `/api/generate-signature` (free abuse; other generators require auth) | `POST /api/generate-signature` | `raw/04-nextjs-proxy-api.log` |
| V-09 | Low | Inconsistent abuse controls: no rate limiting observed on main-site verify/signup/telegram endpoints (admin login *is* limited) | site `/api/*`, `/auth/v1/*` | `raw/08-ratelimit.log` |
| V-10 | Info | Backend job workers unavailable during audit (all `/api/status/*` fail) — availability observation, blocks IDOR validation | `/api/status/*` | `raw/03-idor.log` |

Ratings are qualitative with indicative CVSS v3.1 base estimates; no scoring tool was used.

---

## 2. Scope, method and rules of engagement

* Authorized by the site owner (task brief). No data was destroyed or modified outside our own throwaway accounts; no DoS; request budgets kept small (≤20 per endpoint for rate-limit tests).
* Test accounts used (all @dropmail.me fake addresses, no privileges):
  * `<probe>@dropmail.me` — pre-existing test account (JWT used as "our bearer"; `user_id 23c8fb62-49c5-42d9-b031-906b97cd1cb4`).
  * `<probe>@dropmail.me` — second account created for INSERT/upsert escalation tests.
  * 8 × `vulnrat-rl-<ts>-<n>@dropmail.me` (signup rate-limit test) and 2 × `vulnrat-pw-<ts>-*@dropmail.me` (password-policy test). All disposable; recommend the owner delete them.
* Reusable pieces: publishable key `<publishable-key>` (public, embedded in JS), our test JWT, and an attacker-side callback collector (webhook.site token) to check for server-side fetches.
* Every request/response pair that matters is saved under `evidence/raw/`; scripts under `evidence/scripts/`.

---

## 3. Findings — detail and reproduction

### V-01 (High) — Anonymous listing and unauthenticated download of user images in public bucket `photos`

**What.** The Supabase Storage bucket `photos` accepts an anonymous list request authenticated only with the *publishable* key, and its objects are served from the public CDN route with no credentials at all.

**Reproduce** (no account, no login):

```bash
# 1) List the bucket anonymously (publishable key only, no Authorization header)
curl -sS -H "apikey: <publishable-key>" \
  -H "Content-Type: application/json" \
  -d '{"prefix":"","limit":100,"offset":0,"sortBy":{"column":"name","order":"asc"}}' \
  https://cdn.onlyfakeai.ru/storage/v1/object/list/photos
# -> HTTP 200, 53,384 bytes, 100 entries: 99 × "<unix-ms>_preview.png", image/png, 88,255,130 bytes total

# 2) Read one listed object's metadata without any credentials (HEAD only; GET would return the image)
curl -sSI https://cdn.onlyfakeai.ru/storage/v1/object/public/photos/1778112266686_preview.png
# -> HTTP 200, content-type: image/png, content-length: 557165
```

**Trimmed raw response (listing, one entry):**

```json
[{"name":".emptyFolderPlaceholder", ...},
 {"name":"1778112266686_preview.png","updated_at":"2026-05-07T00:04:28.948Z",
  "metadata":{"size":557165,"mimetype":"image/png"},"archived_at":null},
 ...]
```

**Impact.** Anyone who reads the site's JS bundle obtains the publishable key; from there the whole history of user-uploaded preview images is enumerable and downloadable. Filenames are predictable `<Date.now()>_preview.png` (also the job identifier used by `/api/no-watermark/<jobId>`). This is a PII/privacy breach (CWE-200/CWE-284; est. CVSS 7.5). During the audit only *metadata* was read (HEAD/list); no user image was downloaded.

**Remediation.** Make `photos` private; remove the anon `SELECT` policy on `storage.objects` for it; serve previews via short-lived signed URLs or authenticated API routes; purge/rotate the bucket contents; do not use guessable filenames for private objects.

---

### V-02 (High) — Admin control panel publicly exposed at `ops.onlyfakeai.ru`

**What.** `ops.onlyfakeai.ru` (discovered via Certificate Transparency: `crt.sh` shows `*.onlyfakeai.ru`, `ops`, `cdn`, `www`) is an Express application exposing an "Admin Dashboard" login page and the dashboard itself:

```
GET https://ops.onlyfakeai.ru/        -> 200, HTML "Admin Dashboard" (51 KB)
GET https://ops.onlyfakeai.ru/login   -> 200, HTML "Admin Login" (10 KB)
GET https://ops.onlyfakeai.ru/health  -> 200 {"status":"healthy","timestamp":"...","uptime":287871.8,"version":"1.0.0"}
GET https://ops.onlyfakeai.ru/script.js -> 200, 100 KB dashboard JS (full API map)
```

The dashboard exposes (shown in HTML/JS): Total Profiles, Total Jobs, job status/analytics, **Add Admin**, profile edit (assign plan, add credits, ban/unban, delete, edit `secret_key`/`remarks`), job edit/delete, **API key management**, admin activity/credit assignment log, flagged users, no-watermark jobs.

**Auth behaviour (tested).** Every admin API requires a valid Supabase JWT and then a database role of `admin`; a normal user's valid token is rejected:

```http
GET /api/auth/verify HTTP/2
Authorization: Bearer <valid regular-user Supabase JWT>

HTTP/2 403
{"error":"Admin privileges required","details":"Your role is 'user', but 'admin' is required.","help":"Contact administrator to upgrade your role."}
```

Unauthenticated → `401 {"error":"Access token required"}`. Forged tokens (`alg:none`, HS256 signed with the publishable key / `"supabase"` / common secrets) → `403 {"error":"Invalid or expired token","details":"invalid JWT: ... signing method none is invalid"}`, i.e. proper verification. The login endpoint validates input strictly and rate-limits aggressively:

```http
POST /api/auth/login {"email":"...","password":"..."}   -> HTTP 429
{"error":"Too many login attempts. Please try again later.","retryAfter":"15 minutes"}
retry-after: 766
```

**Admin API map recovered from the public `script.js`:** `/api/auth/login`, `/api/auth/verify`, `/api/profiles` (+ `/{id}`), `/api/jobs` (+ `/{id}`, `/stats`), `/api/analytics`, `/api/analytics/admin-activity`, `/api/admin-users` (+ `/{id}`), `/api/admin-api-keys` (+ `/{id}`). Token is kept in `localStorage.adminToken`; permissions (`isSuperAdmin`) are re-derived server-side via `/api/auth/verify`.

**Impact.** The estate's administrative plane is Internet-facing behind only a password + rate limit. There is no apparent IP allow-list, Cloudflare Access policy, or MFA. A single admin credential (phishing, credential reuse, leaked password, client-side token theft) gives full control: add/remove admins, mint API keys, assign plans/credits, edit/delete profiles and jobs, read all user data and analytics. `/health` and `/script.js` hand an attacker the version and complete endpoint map. (est. CVSS 8.1 — requires credential acquisition, but exposure itself is a serious control gap; CWE-306/CWE-668).

**Remediation (urgent).**
1. Put `ops.onlyfakeai.ru` behind Cloudflare Access / VPN / IP allow-list, or remove its public DNS record (it is reachable via the wildcard cert anyway — restrict at Cloudflare/ingress).
2. Enforce MFA for admin accounts (the panel is Supabase-auth based; add TOTP/WebAuthn at the auth layer or move admin auth to SSO).
3. Rotate admin passwords and all API keys shown in the panel; review the admin list.
4. Remove/restrict `/health` details and do not serve `script.js` unauthenticated (or at least don't ship the admin bundle publicly).
5. Alert on admin login failures/429s and on new admin/API-key creation.

---

### V-03 (Medium) — Unauthenticated job-status endpoint + unverified ownership on job-image endpoints

**What.** `/api/status/<jobId>` requires **no authentication at all** and always answers with a generic fan-out failure while the worker fleet is down:

```http
GET https://onlyfakeai.ru/api/status/1778112266686      # real job id harvested from the public bucket listing
HTTP/2 500
{"error":"Failed to check job status on all servers","details":"All servers returned an error or timed out"}
```

`/api/no-watermark/<jobId>` requires *some* valid session token (any user, role not checked) and returns a generic `500 {"error":"Failed to fetch job"}` for both real and bogus ids while the backend is unavailable:

```http
GET /api/no-watermark/1778112266686  (Authorization: Bearer <our regular user JWT>) -> 500 {"error":"Failed to fetch job"}
GET /api/no-watermark/1              (same)                                         -> 500 {"error":"Failed to fetch job"}
GET /api/no-watermark/x              (no header)                                    -> 401 {"error":"No authorization header found"}
```

Next.js `_buildManifest.js` (public) confirms the internal proxying to workers:

```js
__rewrites:{afterFiles:[
  {source:"/api/status/1/:path*", destination:"/status/:path*"},
  {source:"/api/process/1",      destination:"/process"},
  {source:"/api/supabase/:path*",destination:<minified>}
]}
```

Path-injection attempts on the job id (`http://…`, `//host/…`, `..%2F..`, cloud-metadata URL) produced only generic 500s / Cloudflare 400/308; no fetch reached our collector.

**Impact.** Once workers are healthy, both endpoints appear to act on arbitrary job ids: `/api/status` with no authentication (CWE-306) and `/api/no-watermark` with only "any authenticated user" (ownership check not demonstrated). Because job ids are `<unix-ms>` timestamps and are enumerable through V-01, cross-user access to generated document images/status is plausible (CWE-639). Not confirmed live because every worker call failed during the test window (V-10).

**Remediation.** Require authentication on `/api/status/<jobId>` and enforce `jobs.user_id = auth.uid()` on both routes (or use the service role only inside the route and compare ownership explicitly); return a uniform 404 for unknown ids; rate-limit and log these routes.

---

### V-04 (Medium) — Open registration without e-mail verification / CAPTCHA, weak passwords, e-mail enumeration

**Evidence.** GoTrue settings are public (standard Supabase behaviour) and permissive:

```json
{"external":{"email":true,...},"disable_signup":false,"mailer_autoconfirm":true,
 "saml_enabled":false,"saml_private_key_next_configured":true,"passkeys_enabled":false}
```

* 8 rapid `POST /auth/v1/signup` calls with new fake addresses → **all HTTP 200 with a usable access_token** (no e-mail confirmation, no CAPTCHA, no rate limit).
* Password policy is length 6 only: `123456` and `abcdef` are accepted; only `123` is rejected (`weak_password`).
* E-mail enumeration: re-using an address returns `422 {"code":422,"error_code":"user_already_exists","msg":"User already registered"}` (the password-recovery endpoint, by contrast, is non-enumerating: 200 `{}` for both known and unknown).
* A CAPTCHA endpoint exists (`/api/verify-recaptcha`, fails closed: empty → `{"success":false,"error":"reCAPTCHA token is required"}`, junk → `{"success":false,...}`), but it is only called from the login UI; account creation itself accepts requests without it.

**Impact.** Mass disposable account creation, e-mail/account enumeration, weak admin/user credentials, and amplification of any free endpoint (see V-08); complicates abuse handling. (est. CVSS 5.3; CWE-307/CWE-287/CWE-204).

**Remediation.** Enable Supabase CAPTCHA protection for signup/login (GoTrue `security.captcha`), enable e-mail confirmation, raise the password policy, rate-limit and alert on signup bursts, and avoid the `user_already_exists` 422 difference on signup (generic response).

---

### V-05 (Medium) — User-writable `banned` / profile fields → probable ban evasion and data-integrity abuse

**What.** RLS lets a user update some of their own profile columns; a database trigger blocks the privileged ones (`role`, `generations_left`, `activePlan`, `payment_status`), but `banned`, `email`, `remarks`, `secret_key`, `auto_delete_days` remain writable:

```http
PATCH /rest/v1/profiles?user_id=eq.<us>
{"banned":true}          -> 200 [{"...","banned":true,...}]   # accepted
{"banned":false}         -> 204                              # accepted (restore)
{"generations_left":5}   -> 400 {"code":"P0001","message":"Not authorized to change privileged profile fields"}
{"user_id":"<other>"}    -> 403 {"code":"42501","message":"new row violates row-level security policy for table \"profiles\""}
```

The admin panel's Ban/Unban button is documented (in its JS/API map) to toggle **this same column** (`toggleBanProfile(user_id, banned)`), so a user banned through the panel can simply `PATCH {"banned":false}` with their own JWT to un-ban themselves (unless a separate GoTrue-level ban is applied — not visible from outside). The same route lets users spoof the `email` shown to admins, plant arbitrary `remarks`, and set a `secret_key` the admin UI displays.

**Impact.** Ban evasion / abuse-control bypass, admin-visible data forgery (est. CVSS 5.4; CWE-269/CWE-693). `secret_key` is writable but its purpose was not identified — it is displayed in the admin panel and should be reviewed by the owner (possible auth material for a non-web API).

**Remediation.** Move `banned` (and ban metadata), `email`, `remarks`, `secret_key` into the trigger's protected column list (or revoke column-level UPDATE from `authenticated`); enforce bans in GoTrue as well as in the DB; derive `email` from `auth.users` rather than a user-writable copy.

---

### V-06 (Low) — CORS misconfiguration

Every Next.js response (HTML and API) carries:

```http
access-control-allow-origin: *
access-control-allow-credentials: true
access-control-allow-methods: GET, POST, PUT, DELETE, OPTIONS
access-control-allow-headers: X-Requested-With, Content-Type, Authorization, X-Client-Info, apikey
```

`*` combined with `credentials: true` is an invalid/unsafe combination (browsers refuse credentialed requests, so real impact is limited). The ops admin API also returns `Access-Control-Allow-Origin: *` (OPTIONS preflight echoes requested headers including `authorization`). Supabase REST reflects any supplied `Origin` (`access-control-allow-origin: https://evil.example`).

**Impact.** Low today because auth uses bearer tokens in `localStorage`, not cookies; but it is a red flag and eases any future cookie-based or XSS-assisted token abuse. **Remediation:** allow-list exact origins, never emit `*` with credentials, restrict admin API origins to the ops origin.

---

### V-07 (Low) — Information disclosure

* `GET https://ops.onlyfakeai.ru/health` → `{"status":"healthy","timestamp":"...","uptime":287871.8,"version":"1.0.0"}`.
* `GET https://ops.onlyfakeai.ru/script.js` → 100 KB unauthenticated JS with the complete admin API map, auth flow and UI internals.
* `/_next/static/S2HurGa5cGUpA5514zy3f/_buildManifest.js` is public and exposes internal rewrites (`/api/supabase/:path*`, `/api/status/1/:path*` → `/status/:path*`, `/api/process/1` → `/process`); `x-powered-by: Next.js` is present on many routes.
* `crt.sh` reveals `*.onlyfakeai.ru`, `cdn`, `ops`, `www` (and `ops` is internet-reachable, see V-02).
* Server error messages are sometimes informative (`"Failed to check job status on all servers"`, `"Background removal service responded with status: 500"`) but do not leak stacks or secrets.
* **No** `.env`, `.git`, `package.json`, source maps, `swagger.json`, backups or source files were exposed on the Next.js app or the ops app (all 404/blocked).

**Remediation:** remove detailed `/health`, serve admin assets only after auth, disable `x-powered-by`, asset-hash the admin bundle and keep it behind the authenticated path, standardize generic error messages.

---

### V-08 (Low) — Unauthenticated compute endpoint `/api/generate-signature`

`POST /api/generate-signature {"text":"..."}` works with **no account** and returns a 61 KB JSON with a base64 PNG + stroke data (HTTP 200). The other generators (`generate-qr`, `-code128`, `-code39`, `-datamatrix`, `-itf`, `-pdf417`) correctly return `401 {"error":"Authentication required"}`. This is a free resource/abuse primitive useful to document-forgery workflows. **Remediation:** require auth and rate-limit; align with the other generator routes.

---

### V-09 (Low) — Abuse controls are weak on the main site (inconsistent with admin panel)

Measured, gentle bursts (2026-11-10, ~15:40Z):

| Test | Result |
|---|---|
| 20 × `POST /api/verify-recaptcha` (junk) | all HTTP 400, no 429/Retry-After |
| 20 × `POST /api/auth/telegram-webapp` (junk) | all HTTP 401 `Invalid Telegram Web App data` (HMAC validation works), no rate limit |
| 8 × `POST /auth/v1/signup` | all HTTP 200 with tokens (V-04) |
| 10 × wrong-password GoTrue logins | all HTTP 400 `invalid_credentials`, no 429/lockout |
| Ops admin login (control) | 429 + `Retry-After: 766` after ~10 attempts — properly limited |

**Remediation:** add per-IP/per-account rate limits on the Next.js `/api/*` routes and GoTrue auth endpoints (Supabase rate limits / Cloudflare WAF rate-limit rules); keep the ops limiter.

---

### V-10 (Info) — Backend job workers unavailable

Every `/api/status/<id>` call (real and bogus ids, valid/invalid jobId shapes) failed with `{"error":"Failed to check job status on all servers","details":"All servers returned an error or timed out"}` and `/api/no-watermark` failed with `{"error":"Failed to fetch job"}`. This blocked live IDOR validation (V-03) and SSRF validation (see §8). It is an availability observation, not a vulnerability by itself.

---

## 4. Positive controls that held (negative results)

These deserve recording so the owner does not spend effort re-checking them:

| Control | Test | Result |
|---|---|---|
| Supabase JWT signature enforcement | `alg:none` (with/without trailing dot), HS256 signed with publishable key / `supabase` / `""` / `jwt_secret` / user id, tampered `exp` | **All rejected** — `401 PGRST301 "JWSError JWSNoSignatures"/"JWSInvalidSignature"` (REST) and `401 {"error":"Invalid authentication token"}` (Next API). No expiry/role forgery bypass. |
| Next.js API auth | same forged tokens against `/api/no-watermark/<id>`, `/api/submit-photoshop-job` | rejected (`401 Invalid authentication token`) |
| Ops admin JWT verification | `alg:none`, HS256 with 8 common secrets, forged `role/isSuperAdmin` claims | rejected with explicit `signing method none is invalid` / invalid-signature errors |
| Telegram WebApp auth | 20 forged `initData` payloads | all `401 {"error":"Invalid Telegram Web App data"}` (HMAC validated server-side) |
| OIDC / open redirect | `locale=../../evil`, `locale=https://evil`, `//evil`; callback with `state`/`error` tampering | `307` always to a **fixed** `redirect_uri=https://onlyfakeai.ru/api/auth/telegram-oidc/callback`, PKCE S256 + random state + HttpOnly SameSite=lax flow cookie; callback → `/en/login?error=telegram_oidc_invalid_state` (no open redirect) |
| reCAPTCHA | empty / garbage / unknown-action tokens | fail-closed 400, no bypass |
| Privilege escalation via `profiles` | INSERT self as admin (409 duplicate key), INSERT foreign `user_id` (42501), upsert `merge-duplicates` (trigger P0001), PK move `user_id` (42501), cross-user PATCH (0 rows), DELETE own row (0 rows) | **all blocked**; privileged-field trigger catches UPDATE and upsert |
| RPC surface | 30 candidate names + `get_jobs_time_series` signature probing | only two functions exist: `is_admin()` (returns `false`) and `get_jobs_time_series` (not callable with guessed signatures); no `exec_sql`/admin/user-dump RPCs |
| Storage write abuse | anon upload to `photos`/`backgrounds`/`portraits-public`; authed upload to `portraits-public` | RLS denied (`new row violates row-level security policy`); app-expected uploads to `photos`/`backgrounds` require auth (intended) |
| Next.js image-optimizer SSRF | `/_next/image?url=https://webhook.site/...`, WSL IP, `169.254.169.254`, `file://` | `400 "url" parameter is not allowed/invalid` — no external fetch |
| Secrets in client bundles | regex sweep of 54 artifacts: Telegram bot token, service_role/JWT, Google/AWS keys, Discord/webhook.site URLs, private keys, env assignments | **none found**; only public values: Supabase URL + publishable key, reCAPTCHA *site* key `6LdH730sAAAAAF3VFvBQ-4cIxqcQe1k7kTpyJqK-`; `NEXT_PUBLIC_YANDEX_MAPS_API_KEY` is referenced in code but its value is not embedded |
| Source/code disclosure | source maps, `.env*`, `.git/*`, `package.json`, backups, traversal on both apps | 404 / blocked |
| CVE-2025-29927 middleware-bypass | `x-middleware-subrequest: middleware:middleware:middleware:middleware:middleware` against `/api/no-watermark/x`, `/admin`, `/api/supabase/...` | no behaviour change (no middleware-based auth to bypass; route-level auth held). Exact Next.js patch version could not be determined (not disclosed). |
| Admin-panel XSS (static) | audit of `script.js` DOM sinks: 28 `innerHTML` sites, `escapeHtml()` helper used at 38 sites; inspected profile table, job table, edit modals (profile + job) | user-controlled DB fields (`email`, `remarks`, `secret_key`, `ban_reason`, `document_type`, `country`, job ids) are passed through `escapeHtml()`; plan badge escapes custom plans; no unescaped attacker-controlled sink found. Not execution-tested (no admin browser access). |
| Supabase proxy (`/api/supabase/*`) | path traversal tricks (`..%2F`, `//host`, `https:/`, encoded) | `404 {"error":"requested path is invalid"}`; with the anon key it forwards to Supabase with RLS respected; `auth/v1/admin/users` → `403 not_admin` (no service key injection observed) |

---

## 5. Attack-surface inventory (what exists)

**Main site (Next.js app router, Cloudflare):**
`/api/auth/telegram-webapp` (POST, HMAC-validated), `/api/maintenance-status`, `/api/telegram-admin-url`, `/api/telegram-auth-bot-url`, `/api/telegram-channel-url`, `/api/auth/telegram-oidc/{start,callback}` (PKCE), `/api/portraits/list` (validates `gender`+`ageGroup`; serves `male|female/<era>/<file>.png` from public `portraits-public` bucket), `/api/generate-{qr,code128,code39,datamatrix,itf,pdf417}` (auth), `/api/generate-signature` (**no auth**), `/api/remove-background` (no auth; multipart only; internal background-removal service), `/api/submit-photoshop-job` (bearer; 403 gated on credits), `/api/no-watermark/<jobId>` (bearer), `/api/status/<jobId>` (**no auth**), `/api/verify-recaptcha`, `/api/supabase/*` proxy, plus rewrites `/api/status/1/:path*`→`/status/:path*` and `/api/process/1`→`/process` (targets return 404/405 right now). Build id: `S2HurGa5cGUpA5514zy3f`.

**Supabase gateway (`cdn.onlyfakeai.ru`):** GoTrue signup open + autoconfirm, email provider only; REST tables visible: `profiles`, `jobs` (RLS-scoped; own rows only, empty for us), storage buckets `photos`, `backgrounds`, `portraits-public`, `id`, `dl`, `passport`, `residence`, `product`, `templates`, `site-assets` (some empty/prefix-based). JWTs are ES256 (`kid <redacted-kid>`), `sb-gateway-version: 1`, `sb-project-ref: mcdcezagfjuagbuwsjv`.

**Admin plane (`ops.onlyfakeai.ru`, Express):** login + dashboard + admin API (V-02); `/health`; public `script.js`; role-checked APIs; rate-limited login; all management functions live here (credits/plans, admins, API keys, jobs/profiles edit/delete, analytics). Admin accounts are Supabase users whose `profiles.role` is `admin` (confirmed by the error text "Your role is 'user', but 'admin' is required"). No admin UI on the main domain; `admin.onlyfakeai.ru` does not resolve; `api.onlyfakeai.ru` does not resolve.

---

## 6. Data-exposure summary

* `profiles` RLS: a user only reads its own row; anon reads return `[]`; no cross-user reads possible via REST.
* `jobs` RLS: a user sees only own jobs (empty for our test account); cross-user rows not readable via REST.
* **V-01 is the exception**: user preview images are anonymously listable/readable in the `photos` bucket. Metadata evidence: 99 real PNG files, 88.3 MB, timestamps spanning a single 14-hour window in one 100-item page (the bucket almost certainly contains much more).
* No user PII was downloaded during this audit; only listing metadata and HEAD status/size were captured.

---

## 7. Takeover path — how full backend control is reached (and what is missing)

The web-facing estate has **one control plane**: the admin panel at `ops.onlyfakeai.ru`. Everything below is reachable *once an actor has an admin session*; none of it was obtained during this audit.

### 7.1 Concrete steps if an admin session is obtained (attacker or authorized operator)

1. `POST https://ops.onlyfakeai.ru/api/auth/login {"email":"<admin>","password":"<pw>"}` → store `access_token`.
2. `GET /api/auth/verify` → confirm `isSuperAdmin`.
3. **Add a persistent admin**: `POST /api/admin-users` (add-admin modal in panel), or directly `PATCH https://cdn.onlyfakeai.ru/rest/v1/profiles` as the admin (admin JWT / service role) to set `role="admin"`.
4. **Data export**: `GET /api/profiles?page=N&limit=20` (all profile rows: e-mail, plan, credits, payment status, secret_key, remarks, ban state) and `GET /api/jobs?page=N` (all job rows) — paged, scriptable; `GET /api/admin-api-keys` lists API keys; `GET /api/analytics*` aggregates. With the Supabase **service_role** key (not found in client artifacts; lives in server env) a full REST dump of every table/bucket via `cdn.onlyfakeai.ru` is trivial.
5. **Monetisation / abuse control**: `PATCH /api/profiles/<id>` to set plans and `generations_left` (the panel's "Credit & Plan Assignment" flow), `POST /api/admin-api-keys` to mint keys, ban/unban/delete users, edit/delete jobs.
6. **Persistence**: add a covert admin account; keep an API key; if Supabase service role key or Telegram bot token are ever reachable from the ops host (server-side env), reset user passwords (`/auth/v1/admin/users`) / control the Telegram channel and admin bot — this is the path to *irreversible* takeover and requires host-level access to ops (SSRF/RCE/credential reuse), which was not found in this pass.
7. **Infrastructure**: site+supabase+ops all sit behind Cloudflare on a wildcard Let's Encrypt cert; no hosting/origin IP was exposed in this audit. Origin takeover was not achieved.

### 7.2 Why it was not reachable unauthenticated

* Admin APIs require a **valid Supabase JWT + `profiles.role='admin'` DB check** (V-02 evidence) → no token forgery (verified), no role write (trigger + RLS verified), no admin INSERT/upsert/PK-move/delete path (verified).
* The **service_role key / JWT signing secret / Telegram bot token** do not appear in the rehosted client bundles (V-07/secrets sweep: none found); they live server-side only.
* Ops login is **rate-limited** (15-minute lockout observed) and input-validated; we deliberately did not brute force it.
* The admin panel's rendering escapes user-controlled fields, so the "stored XSS → steal admin localStorage token" chain was **not evidenced** in static review.

### 7.3 Recommended owner actions (validation + hardening)

1. **Immediately restrict `ops.onlyfakeai.ru`** (Cloudflare Access/VPN/IP allow-list) and rotate admin credentials + panel API keys; enable MFA.
2. **Fix V-01**: private bucket + RLS + signed URLs; purge/rotate exposed previews; assess breach-notification obligations (the bucket has likely exposed the last months of customers' images to anyone).
3. Harden `profiles` (V-05) and signup (V-04) as described.
4. To let the audit **finish the unconfirmed items** (§8), the owner can supply: (a) a temporary admin-role test account on ops.onlyfakeai.ru (or add our test UUID `23c8fb62-49c5-42d9-b031-906b97cd1cb4` to `admin` for the test window), (b) a paid test account (e.g. Try plan, 1 credit) so `/api/submit-photoshop-job` clears its credit gate and the `photoUrl` SSRF test becomes meaningful, and (c) a note when the job-worker fleet is online, to re-test V-03 IDOR with a real job created by the paid account.

---

## 8. Not confirmed / needs credentials or conditions

| # | Item | Why not confirmed | What is needed |
|---|---|---|---|
| 1 | IDOR on `/api/no-watermark/<jobId>` (read another user's no-watermark image) | backend workers down; both real (other-user) and bogus ids return the same `500 {"error":"Failed to fetch job"}`; no ownership oracle | workers online + a real job id (we already have other-user ids from V-01) |
| 2 | IDOR / enumeration on `/api/status/<jobId>` (unauthenticated) | always `500` while workers down | workers online |
| 3 | SSRF via `photoUrl` / `backgroundPhoto` in `POST /api/submit-photoshop-job` | request is rejected with `403 {"error":"Access denied. No generations left."}` **before** any URL fetch; our webhook collector received no request from any tested URL (`https://webhook.site/...`, WSL IP `:8899`, `169.254.169.254`, `file:///etc/passwd`) | a paid account with ≥1 generation (owner-provided Try plan) |
| 4 | SSRF via `/api/status/<jobId>` path/URL injection | only generic 500s; no callback; no timing signal | worker up + ability to distinguish fetch errors; or server-side logs |
| 5 | Admin API authorization depth / destructive functions (add admin, API keys, delete profiles/jobs, data export) | 403 for regular user; we did not obtain admin credentials | temporary admin role for our test account |
| 6 | Ban-evasion exploit confirmation (V-05) | `profiles.banned` write confirmed, but we could not observe an admin-issued ban + its enforcement path | owner-confirmed ban mechanism (profiles column vs GoTrue ban) or an admin account to issue the ban |
| 7 | Stored XSS in admin panel | static review found consistent `escapeHtml()`; no admin browser to execute a payload | source of the exact rendering or an admin session + browser (owner-approved test) |
| 8 | `service_role` key / JWT secret / Telegram bot token / host access | not present in rehosted client artifacts; server env only | source/hosting access review, or SSRF/RCE (not found) |
| 9 | Exact Next.js version / CVE applicability | version banner and source maps unavailable; `x-powered-by` only; `x-nextjs-stale-time` suggests Next 15.x | `package.json`/lockfile or deployed build info from the owner; CVE-2025-29927 probe was negative but version-specific CVEs can't be ruled out |
| 10 | Generation-credit/payment bypass through `/api/submit-photoshop-job` | blocked by "No generations left" for our unprivileged accounts; DB writes to `generations_left` blocked | paid account + admin API access for comparison |
| 11 | Password-reset / e-mail flows abuse | recovery endpoint behaves non-enumerating; actual mail delivery not tested (fake inboxes only) | owner mail logs |

---

## 9. Remediation priorities

| Priority | Action |
|---|---|
| P0 | Restrict/close `ops.onlyfakeai.ru` to trusted networks + MFA; rotate admin credentials and panel-issued API keys; review admin accounts/audit log. |
| P0 | Make `photos` bucket private, remove anon list/read, switch to signed URLs; assess data-breach obligations and purge/rotate exposed files. |
| P1 | Enforce ownership checks and auth on `/api/status/*` and `/api/no-watermark/*`; rate-limit and audit them. |
| P1 | Harden `profiles` column grants/trigger (`banned`, `email`, `remarks`, `secret_key`); enforce bans in GoTrue too. |
| P1 | CAPTCHA on signup/login + e-mail confirmation + password policy; generic signup response; rate-limit auth endpoints (Cloudflare/WAF or Supabase auth limits). |
| P2 | CORS allow-lists; remove `/health` details; protect vendored admin JS; disable `x-powered-by`; generic error messages; keep dependencies patched (Next.js/GoTrue) and subscribe to advisories. |
| P2 | Add authentication + rate limiting to `/api/generate-signature`; keep reCAPTCHA fail-closed (already good). |
| P3 | After fixes, re-run the unconfirmed tests in §8 (we can provide the exact scripts from `evidence/scripts/`). |

---

## 10. Evidence index (`rehost/report/evidence/`)

| File | Contents |
|---|---|
| `raw/00-baseline.log` | Response headers/fingerprint, API route auth behaviour, well-known files |
| `raw/01-auth-jwt.log` | JWT forgery matrix (alg=none/HS256/expired/tampered) vs REST + Next API |
| `raw/02-bundle-context.log` | Extracted client-bundle request contracts (`submit-photoshop-job`, `no-watermark`, jobs id, storage upload, recaptcha) |
| `raw/02-rest-storage-rpc.log` | REST table exposure, storage buckets/list/upload/delete/signed URLs, RPC enumeration, reCAPTCHA, OIDC, CORS |
| `raw/03-idor.log` | Public `photos` listing + anon HEAD reads, job-ID probes (no watermark/status), anon uploads, jobs RLS |
| `raw/04-nextjs-proxy-api.log` | Build manifest/rewrites, `/api/supabase` proxy, OpenAPI block, auth settings, generators, remove-background, OIDC callback, source maps, RPC signature probes |
| `raw/05-profiles-insert.log` | Second account creation, INSERT/upsert/`user_id` escalation attempts, cross-user PATCH, e-mail enumeration |
| `raw/06-profile-delete-reinsert.log` | Self-DELETE + re-INSERT privileged row attempt (blocked by RLS/unique key) |
| `raw/07-ssrf.log` | Webhook collector self-test, WSL listener, photoUrl/status/supabase/image-optimizer/remove-background SSRF attempts, zero callbacks |
| `raw/08-ratelimit.log` | 20× reCAPTCHA, 20× telegram-webapp, 8× signup, 10× bad logins, password policy, recovery enumeration |
| `raw/09-misc.log` | CVE-2025-29927 probes, profile column reachability, RPC param probes, Next version search, crt.sh subdomains, public-object HEAD reads |
| `raw/09-secrets-sweep.log` | Full regex secret sweep over 54 rehosted artifacts |
| `raw/10-ops-subdomain.log` | `ops.onlyfakeai.ru` discovery, TLS cert, page/health/robots, DNS, locale redirects |
| `raw/11-ops-admin.log` | Saved admin HTML/JS analysis, endpoint probes, OPTIONS methods |
| `raw/12-ops-analyze.log` / `raw/14b-xss-analyze.log` / `raw/14c-xss-sinks.log` / `raw/14d-modal-code.txt` | Admin dashboard JS analysis: admin API map, auth flow, `escapeHtml` coverage, XSS-sink review |
| `raw/13-ops-auth-attacks.log` | Admin API authz matrix (none/own/forged), login validation + rate-limit, static/traversal leak probes, forged-JWT matrix, CORS |
| `raw/14-ops-xss-workers.log` | Worker/process endpoint method matrix, more unauth endpoints, CSP headers |
| `raw/15-final-checks.log` | Scale of public `photos` exposure (100 objects / 88.3 MB), anon HEAD reads, role check, auth settings |
| `raw/ops-index.html`, `raw/ops-login.html`, `raw/ops-script.js`, `raw/ops-health.json`, `raw/ops-robots.txt` | Saved copies of the exposed admin app artifacts |
| `raw/site-home.html`, `raw/site-home.headers`, `raw/crt-subdomains.json`, `raw/photos-bucket-listing-anon.json` | Site capture, CT subdomains, bucket listing evidence (metadata only) |
| `scripts/*.sh`, `scripts/*.py` | Every reproducible test used (env, probes, JWT forging, IDOR, SSRF, rate-limit, ops analysis) |

### Test artefacts left on the target (owner may remove)

* Test accounts (no privileges): `<probe>@dropmail.me`, `<probe>@dropmail.me`, 8 × `vulnrat-rl-<ts>-*@dropmail.me`, 2 × `vulnrat-pw-<ts>-*@dropmail.me` (fake e-mail domains; signup is auto-confirmed so they are usable accounts).
* One 30-byte file `backgrounds/vulnrat-audit-1794321400.txt` created in a writable storage bucket; deletion was denied by storage RLS for our test user (contents: the literal string `vulnrat-audit-test-<ts>`). It is publicly readable via the `backgrounds` public URL but contains no user data.
* No other data was created, modified or deleted; real user content was never downloaded.

---

*Report generated from live evidence on 2026-11-10. Reproduce any section with the scripts in `evidence/scripts/` (set `EVID` in `env.sh` if the workspace layout changes).*
