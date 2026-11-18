# onlyfakeai.ru — Recon & Rehost Architecture

Compiled from live probing + client bundle reverse engineering on 2026‑11‑10.
Source of truth for the clone: `rehost/src/` (raw + beautified chunks), `catalog-products.json`, `template-map.json`.

---

## 1. Stack

| Layer | Technology | Notes |
|---|---|---|
| Edge | Cloudflare | HTTP/2, h3, bot-management cookies, `cf-ray` |
| Frontend | Next.js App Router (`x-powered-by: Next.js`, build id `S2HurGa5cGUpA5514zy3f`) | i18n middleware rewrites `/en/*` → `/*`; `x-middleware-rewrite: /en` |
| Auth/DB | Supabase, project ref `mcdcezagfjuagbuwsjv`, GoTrue `v2.197.0` | Proxied at `https://cdn.onlyfakeai.ru` (custom domain), and again through `/api/supabase/*` |
| Storage | Supabase Storage (S3-compatible) at `cdn.onlyfakeai.ru/storage/v1/...` | Public buckets; filenames predictable |
| Workers | "photoshop job" fleet | Behind `api` (multiple internal servers), currently down: every `/api/status/*` returns `All servers returned an error or timed out` |
| Telegram | WebApp initData auth + OIDC (client id `<telegram-client-id>`) | bot `@<remote-auth-bot>`, channel/support `@<remote-support>` |
| Maps | Yandex Geocoder / Yandex Maps JS | `NEXT_PUBLIC_YANDEX_MAPS_API_KEY` in client bundle |
| i18n | 14 locales: en de es fr ru zh-CN ar hi id it ja ko nl pt | multilingual pages under locale prefix |

## 2. Routes (public, no auth)

- `/` — landing
- `/<locale>` — locale landing
- `/generator` — document generator SPA (login required for job submit, UI renders public)
- `/shop`, `/shop?page=1..10`, `/shop/<category>?page=N` — 232 template products. Categories: `passport` (58), `id-usa` (50), `dl-usa` (49), `id` (36), `residence` (30), `dl` (9). Server-rendered RSC payload contains full product JSON (id, name, category, price=25, originalPrice=40, image URL, views, description, tags, country, year).
- `/login` — email+password form, Telegram login, "Login via Telegram"
- `/history` — generation history
- `/cart`, `/rate` — checkout/plans
- `/blog`, `/documentation`, `/faq`, `/terms`, `/live360` — content
- `/[locale]/[slug]` — SSG blog/docs slugs (`__SSG_MANIFEST`: `[locale]`, `[locale]/[slug]`, `[locale]/product/[id]`)
- `/[locale]/product/[id]` — product detail page (redirects to login for anonymous users)

## 3. Authentication

### Email/password (Supabase GoTrue)
- `disable_signup: false`, `mailer_autoconfirm: true` → **open registration with instant confirmation** (no email round-trip).
- Client: `supabase-js` `createClient("https://cdn.onlyfakeai.ru", "<publishable-key>", {auth:{persistSession:true, autoRefreshToken:true, detectSessionInUrl:true}})`.
- Session stored under localStorage key `supabase.auth.token`; API calls send `Authorization: Bearer <access_token>`.
- JWT: ES256, issuer `https://mcdcezagfjuagbuwsjv.supabase.co/auth/v1`, role `authenticated`, expiry ~7 days.

### Telegram WebApp
- POST `/api/auth/telegram-webapp` with `{initData, user}`; server validates HMAC (all forged initData → 401 `Invalid Telegram Web App data`, so this path is secure).
- On success returns `{redirect_url}` (session established server-side).

### Telegram OIDC (login page button)
- GET `/api/auth/telegram-oidc/start?locale=en` → 307 to
  `https://oauth.telegram.org/auth?client_id=<telegram-client-id>&redirect_uri=https://onlyfakeai.ru/api/auth/telegram-oidc/callback&response_type=code&scope=openid+profile+phone&state=<32B>&code_challenge=<S256>&code_challenge_method=S256`
- Sets cookie `tg_oidc_flow` (`{codeVerifier, csrfState, locale}`, Path=/api/auth/telegram-oidc, Max-Age 300, HttpOnly, Secure, SameSite=lax).

## 4. Database (inferred)

`public.profiles` (readable per-user under RLS; one row per auth user):

```
user_id uuid PK (FK auth.users)
activePlan text default '-'
generations_left int default 0
last_payment_date timestamptz
payment_status text
auto_delete_enabled bool default false
auto_delete_days int default 30
email text
created_at timestamptz
last_sign_in_at timestamptz
role text default 'user'            -- privileged
secret_key text                     -- writable by user (!)
remarks text
banned bool default false
banned_at timestamptz
banned_by text
ban_reason text
```

- UPDATE trigger blocks privileged columns: `role`, `generations_left`, `activePlan`, `payment_status`
  (`P0001 Not authorized to change privileged profile fields`).
- Writable by the user: `auto_delete_days`, `secret_key`, `banned`, `email`, `remarks`, and `role='user'` (no-op).
- `public.jobs` exists (empty when probed). RPC functions exist, at least `public.get_jobs_time_series` (signature unknown; disclosed by PostgREST "did you mean" hint).

## 5. Storage buckets

Base: `https://cdn.onlyfakeai.ru/storage/v1/object/public/<bucket>/<path>`

| Bucket | Purpose | Access |
|---|---|---|
| `product` | marketing previews of all 232 templates — `product/<category>/<COUNTRY>_<DocType>_<YEAR>-EXAMPLE.jpg` | public object read |
| `id` | generator templates: `id_card`, `ssn`, `passport_card` → `<COUNTRY>_ID_<year>-EXAMPLE.jpg`, `..._SSN_...` | public object read |
| `dl` | driving-license templates → `<COUNTRY>_DL_<year>-EXAMPLE.jpg` | public object read |
| `passport` | passport templates → `<COUNTRY>_Passport_<year>-EXAMPLE.jpg` | public object read |
| `residence` | residence permits → `<COUNTRY>_Residence-related document_<year>-EXAMPLE.jpg` / `..._Residence_...` | public object read |
| `portraits-public` | stock portrait faces used by "random portrait" feature → `portraits-public/<gender>/<ageGroup>/<filename>` | public object read |
| `photos` | per-job generated previews → `<ms-timestamp>_preview.png` | used via getPublicUrl |
| `backgrounds` | uploaded background images → `<prefix>_<rand>.<ext>` | used via getPublicUrl |

Storage API `list` operations return empty with publishable/anon keys; `getPublicUrl` paths work directly. There is no bucket listing for anonymous users.

Filename builder (from bundle): `COUNTRY.toUpperCase() + "_" + DOC + "_" + revisionYear + "-EXAMPLE.jpg"` — full country × doctype × year map in `rehost/src/template-map.json`; country metadata (doc numbers/address formats per document type) embedded in `rehost/src/app/8794-9e09a720aa8a0cf1.js`.

## 6. API contract (Next.js route handlers)

| Route | Method | Auth | Behavior |
|---|---|---|---|
| `/api/auth/telegram-webapp` | POST | none | HMAC-validated initData → session/redirect |
| `/api/auth/telegram-oidc/start` | GET | none | 307 to Telegram OAuth (PKCE) |
| `/api/auth/telegram-oidc/callback` | GET | cookie | code→token exchange |
| `/api/telegram-admin-url` | GET | none | `{"url":"https://t.me/<remote-support>"}` |
| `/api/telegram-auth-bot-url` | GET | none | `{"url":"https://t.me/<remote-auth-bot>"}` |
| `/api/telegram-channel-url` | GET | none | `{"url":"https://t.me/+BtbpIl2-QnQzZTg8"}` |
| `/api/maintenance-status` | GET | none | `{"maintenanceMode":false}` |
| `/api/portraits/list?gender=&ageGroup=` | GET | none | `{filenames:[...]}` for the portraits-public bucket (ageGroup value vocabulary unknown; all guesses rejected) |
| `/api/remove-background` | POST multipart `file` | none | proxies internal background-removal service, returns PNG blob; failure leaks `details:"Background removal service responded with status: 500"` |
| `/api/generate-code128` / `code39` / `datamatrix` / `itf` / `pdf417` / `qr` | POST | none | barcode/QR PNG generators (free) |
| `/api/generate-signature` | POST `{text,...}` | none | returns `{bias,color,image:data:image/png;base64,...}` synthetic signature |
| `/api/verify-recaptcha` | POST `{token}` | none | 400 `{"success":false,"error":"reCAPTCHA token is required"}` on empty |
| `/api/submit-photoshop-job` | POST | Bearer (Supabase access token) | queue generation; body = full document data (see below); rate-limited (429 + Retry-After); 403/error `Access denied. No generations left.` |
| `/api/status/<jobId>` | GET | **none** | polls workers; 500 `{"error":"Failed to check job status on all servers","details":"All servers returned an error or timed out"}` while fleet is down |
| `/api/no-watermark/<jobId>` | GET | Bearer | 401 without header; 500 `{"error":"Failed to fetch job"}` for unknown ids; returns `{no_watermark_url}` |
| `/api/broadcast` | GET/POST | (n/a) | OPTIONS advertises GET; GET returns Next 404 currently |

Rewrite proxies exposed by build manifest:

```
/api/status/1/:path*  ->  /status/:path*
/api/process/1        ->  /process
/api/supabase/:path*  ->  Supabase  (forwards the caller's apikey/authorization; no service key injected)
```

### submit-photoshop-job body (client-built)

```
documentType, country, revision, firstName, middleName, lastName, birthday, issueDate,
expiryDate, docNumber, cuit, optionalData1..3, address, signatureWidth, photoUrl,
signature, removeWatermark, generationType, backgroundPhoto, mockup,
backgroundOrientation, mrz, pdf417Data, pdf417Image, code128Data, code128DocData,
code39Data, itfData, qrData, qrData2, qrImage, qrImage2, dataMatrixData,
metadataEnabled, deviceProfile, metadataDate/Hour/Minute/Second,
gpsEnabled, metadataLat, metadataLng, licenseType (id_card)
```
Response: `{jobId}` → poll `/api/status/<jobId>` until `status:"completed"` + `watermarkUrl` → optional `/api/no-watermark/<jobId>` → `{no_watermark_url}`. Job id = Unix-ms timestamp; generated preview files are named `<timestamp>_preview.png` in the `photos` bucket.

## 7. Client-side document engine

The 1.79 MB generator chunk (`rehost/src/app/page-bf5f8970043f7336.js`, beautified in `rehost/src/beautified/`) contains the whole per-country engine: MRZ generation, check digits, PDF417 payloads, per-country field schemas/defaults, canvas compositing of template + photo + barcodes + signature, metadata (EXIF/device/GPS) injection, mockup rendering. Rehosting the generator means reusing this chunk against a new backend contract, or re-implementing the render step server-side with the PSD/JPEG templates.

## 8. Operational state observed 2026-11-10

- Landing/shop/generator shell fully online.
- Worker fleet for generation/background-removal **down** (`All servers returned an error or timed out`, background removal 500 upstream).
- `/api/status/<id>` does not require auth → job-status enumeration is possible by design (timestamps enumerable), but no live jobs were retrievable during recon.
- Supabase auth open for registration; RLS restricts `profiles` to own row; privileged columns guarded by trigger.

## 9. Rehost checklist

1. **Static site**: serve `rehost/site` (all locales + `_next` chunks + local assets). CORS/README available in `rehost/site/MIRROR-NOTES.md`.
2. **Template library**: `rehost/assets` (public buckets id/dl/residence/passport/product, plus catalog previews). Excluded: `photos`, `backgrounds`, `portraits-public` (user-uploaded / face imagery).
3. **Catalog**: import `rehost/src/catalog-products.json` into new DB/shop; 232 SKUs, images already in `product` bucket harvest.
4. **Backend**: re-implement the 6 collections above (auth, storage public read, job queue, barcode/signature generators, template metadata map). Endpoint contracts are in section 6; document data schema is section 6 body + the engine chunk.
5. **Supabase**: either self-host (GoTrue + PostgREST + Storage) or new project; recreate `profiles` schema + RLS + privileged-column trigger; storage buckets `id/dl/passport/residence/product` public-read.
6. **Config to replace**: Supabase URL + publishable key (client chunk 8794/10ca), Telegram bot token (server side only, not in client), OIDC client id `<telegram-client-id>`, Yandex Maps/Geocoder key, reCAPTCHA keys, `cdn.onlyfakeai.ru` base URL, job-worker endpoints.
7. **Not extractable from the web surface**: server-side source (Next.js route handlers), `.env`, bot token, service-role key. Those need owner credentials/hosting access, not a clone.

## 10. Admin plane — `ops.onlyfakeai.ru` (discovered via Certificate Transparency)

Separate Express app, same estate, behind Cloudflare. Full details + evidence: `report/ops/OPS-TAKEOVER.md`.

- Surfaces: `/` dashboard shell, `/login`, `/health` (`version 1.0.0` + uptime), `/script.js` (100 KB; full admin API map).
- Auth model: `Authorization: Bearer <Supabase access_token>` → server validates JWT → reads `profiles.role`; non-admin → `403 {"error":"Admin privileges required","details":"Your role is 'user'..."}`; unauthenticated → `401 {"error":"Access token required"}`.
- Admin API: `/api/auth/login` `{email,password}` (GoTrue password grant + role check), `/api/auth/verify`, `/api/profiles[?filters]`, `/api/profiles/<userId>` PATCH (plan/credits/ban/remarks/secret_key), `/api/jobs`, `/api/jobs/stats`, `/api/jobs/<id>`, `/api/analytics`, `/api/analytics/admin-activity`, `/api/analytics/summary`, `/api/admin-users`, `/api/admin-users/<userId>/revoke`, `/api/admin-api-keys`, `/api/admin-api-keys/<keyId>/revoke`.
- Login limiter: **global 5 attempts / 900 s** (draft-7 `ratelimit-*` headers, window boundaries at :08:12/:23:12/:38:12/:53:12 Z); any client can lock the admin out (DoS), and it makes password guessing impractical.
- Unauthenticated SECURITY DEFINER RPCs on the Supabase project expose live counts: `get_total_counts` (13,804 profiles / 25,925 jobs), `get_recent_activity`, `get_job_status_counts`, `is_admin`, `get_jobs_time_series`, `get_profiles_time_series`; plus hint-visible write funcs (`deduct_credits`, `deduct_generation`, `credit_tokens_after_payment`, `grant_plan_credits`, `remove_watermark_and_deduct_token`, `cleanup_expired_payment_assignments`).
- Identity association (public reporting): the site's operator was charged/pled guilty in SDNY in 2026 (aliases include "John Wick", matching the site's `johnwicktemplate.jpg`); contact identity = `onlyfake@tuta.io` (registered Supabase user).
