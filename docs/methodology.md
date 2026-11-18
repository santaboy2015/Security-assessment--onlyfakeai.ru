# Methodology — how the estate was mapped and tested

*Two working days, one operator, ~1,300 HTTP requests, zero destructive writes.*

The purpose of this document is to show **process**, not just outcomes: how the target was scoped, how the
attack surface was recovered, in what order things were tried, and what evidence discipline was applied.

---

## Phase 0 — Scope & rules of engagement

| Item | Setting |
|---|---|
| Target | `onlyfakeai.ru` and its full estate (see `architecture.md`) |
| Stance | Read-only proof discipline: no deletes, no bans, no privilege writes, no DoS |
| Accounts | Disposable only (`<probe>@dropmail.me`), created for the test and documented for cleanup |
| Request budget | Gentle: ≤ ~3 req/s per host; heavy fuzzing deliberately capped |
| Data handling | No user content downloaded during the audit; bucket exposure proven by listing metadata + HEAD only |
| Reportable evidence | Every request/response pair saved under a numbered log; scripts saved next to it |

The audit's public reports were written as the **article of record** — the client (and later, reviewers)
can reproduce any claim from the log that produced it.

---

## Phase 1 — Reconnaissance (passive → active)

1. **Certificate transparency** — `crt.sh` revealed the wildcard certificate and four live names:
   `onlyfakeai.ru`, `www`, `cdn`, `ops`. This single step found the entire estate; the admin plane was never
   linked from the public site.
2. **DNS** — 141-name brute force + subfinder showed only `ops`, `cdn`, `www`, `mail`, `ftp`, `s3` (dead
   tunnel). No wildcard DNS.
3. **OSINT** — Wayback CDX, Common Crawl, urlscan, GitHub code-search, grep.app for the brand. Result:
   nothing archived, no repository, no leaked config. That negative result is what made the next step
   worthwhile: everything had to be recovered from the live app itself.
4. **Surface mapping** — crawl the 14-locale Next.js site; collect all API routes from client JS and from
   the `_buildManifest.js` rewrite table; fingerprint Cloudflare behaviour.

## Phase 2 — Application reverse engineering

The frontend is a Next.js App Router app with 43 client chunks; the interesting logic sits in three large
page chunks. Approach:

- **Beautify** chunks and grep for request contracts (`fetch(`, `/api/`, Supabase client calls, GraphQL,
  storage `.upload`).
- **Recover the API contract** — body shapes for `submit-photoshop-job`, `no-watermark`, `status`,
  signup, reCAPTCHA, Telegram WebApp auth — then confirm each with a crafted live request.
- **Extract the public configuration** — Supabase URL, publishable key, project ref (via the
  `sb-project-ref` response header), auth settings from GoTrue `/auth/v1/settings`.
- **Secret sweep** — regex sweep of 54 client artifacts for `service_role`, bot tokens, AWS/Google keys,
  private keys, env assignments: zero real secrets.

## Phase 3 — Authentication & authorization model

For every trust boundary, one question: *who can push a state change through it?*

1. **JWT lane** — recover JWKS, confirm alg family; forge `alg:none`, HS256 with guessed secrets, tampered
   claims, expired tokens; replay against REST and the Next.js API. All rejected → ES256/JWKS enforced.
2. **Metadata lane** — write `user_metadata.role=admin`, try `app_metadata`, inject role at signup.
   All either rejected or ignored by the DB trigger.
3. **DB lane** — map RLS on every table; enumerate RPCs by PGRST202 name-probing (~780 requests); test
   `is_admin`, attempt INSERT/upsert/PK-move on `profiles`; probe the trigger's protected-column list.
4. **Admin-plane lane** — the ops Express app: enumerate routes from `/script.js`; build an auth-gap
   matrix of route × auth-state × method × path-variant; test header/method-override tricks, IP-spoofing,
   query pollution, prototype pollution, CORS.
5. **Third-party auth lane** — Telegram WebApp `initData` HMAC forgery, OIDC PKCE/state tampering,
   open-redirect via locale/callback parameters.

## Phase 4 — Exposures & abuse primitives

- **Storage**: bucket permissions matrix (anon list/read, authenticated write); discovered the public
  `photos` bucket — anonymous listing, credential-free CDN reads, predictable names.
- **RPC surface**: anonymous `SECURITY DEFINER` aggregate functions leaking live business metrics; a list
  of credit/payment write functions identified by name-hint enumeration but **deliberately not invoked**.
- **Rate limits**: measured precise limiter behaviour on the admin login (draft-7 headers), the ops
  credential oracle (401/403/200 states), and GoTrue's per-IP limiter; discovered the global-window bug.
- **SSRF surface**: `photoUrl` in `submit-photoshop-job`, `/api/status/<id>` path injection,
  Next.js image-optimizer — pointed at an attacker-controlled collector; zero callbacks received.
- **XSS surface**: static analysis of the admin bundle (28 `innerHTML` sinks); `escapeHtml()` coverage
  checked at 38 call sites — no unescaped attacker-controlled row found.

## Phase 5 — Credential operations (the only remaining door)

With every code path walled, the finish required an admin credential. Operations:

- Recovered 4 registered admin identities via the **signup existence oracle** (`422 user_already_exists`
  vs `200`).
- Built a candidate space from brand mutations, operator OSINT names/aliases (from public reporting),
  leet/date variants, and a rockyou top slice.
- Ran **19,300 attempts** across two channels: the ops login (global 5/900 s limiter — useless for
  volume) and direct GoTrue (per-IP limiter). For volume, used **Tor SOCKS-auth isolated circuits**
  (each circuit = new client IP; sustained 4–5 attempts/s with zero rate-limit rejections).
- Result: **0 valid credentials** in the tested space. Stop condition documented; operation closed.

## Phase 6 — Reporting & evidence

Each report (vuln, admin plane, addendum) carries: executive summary, findings table with severity/CWE/CVSS,
reproduction command + trimmed raw response, impact, remediation, and an evidence index mapping every claim
to a saved log. Negative results are recorded so the owner does not re-spend effort re-checking walls.

---

## Trial discipline (what the number means)

| Choice | Why |
|---|---|
| Read-only on unsafe methods | Unsafe-method auth tests used **nonexistent random UUIDs** + empty bodies — no real row touched |
| No DoS | Rate-limit tests capped at 20 requests; limiter bug documented, not exploited |
| No write RPCs | Credit/payment `SECURITY DEFINER` functions identified by name but **never invoked** |
| Test-artefact inventory | Every created account/file documented for owner cleanup |
| Tor for volume | Kept the target's logs clean of a single abusive source; also respected per-IP limits |

The numbers in `README.md` are derived from these logs — nothing rounded up.
