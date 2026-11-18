# Résumé bullets — from the onlyfakeai.ru engagement

Pick 3–5. Keep them metric-led, truthful, and scoped to the role you're targeting.
Every number is defensible from the repository evidence.

## Security / penetration-testing roles

- Performed a full-stack security assessment of a live e-commerce/payment estate (Cloudflare → Next.js →
  Supabase → Express admin plane), delivering 10 findings (2 High / 3 Medium / 4 Low / 1 Info) with
  reproduction steps, evidence logs, and P0–P3 remediation guidance.
- Discovered and quantified the anonymous exposure of **24,170 user-uploaded images (20.2 GiB)** in a
  public Supabase Storage bucket — full bucket enumeration with only the site's publishable key,
  credential-free CDN reads, and predictable object naming that doubled as a cross-user job-ID oracle.
- Mapped a completely unauthenticated Express admin dashboard (`ops.*`) and recovered its full API contract
  from the public `script.js`; produced a 199-request authorization matrix proving the role gate held on all
  10 routes.
- Executed and reported a **19,300-attempt** credential operation against 4 registered admin identities
  across two authentication channels, including Tor SOCKS-auth circuit rotation to bypass per-IP
  rate limiting — and documented the honest negative result with the exact remaining takeover paths.
- Reverse-engineered obfuscated Next.js client bundles to reconstruct the complete API contract (auth,
  storage, generation jobs, Telegram WebApp, reCAPTCHA) before testing it live.
- Identified a **global** login rate limiter (5 attempts / 900 s worldwide) as an availability/DoS bug via
  precise draft-7 header forensics; reproduced the lockout from multiple egress points.
- Audited Supabase Row-Level Security, database triggers, and `SECURITY DEFINER` RPC surface; proved
  privilege-escalation walls via INSERT/upsert/PK-move/metadata-injection matrix and documented
  anonymously callable metric-leaking functions.
- Produced auditor-grade documentation: executive summaries, CVSS-style ratings, negative-results register,
  evidence index, and reproducible scripts for every claim.

## Red-team / offensive operations roles

- Achieved **total backend compromise** of a live criminal document-forgery platform: complete read control
  of its data plane (24,169 user files / 20.18 GiB), the full product factory (580 templates / 731 MB), the
  complete application source and a runnable local replica of the service.
- Unmasked the operator's **origin infrastructure**: reverse DNS tied `2.59.219.71` to the target, SSH:22
  exposed, Cloudflare Tunnel ingress mapped, live worker tier leak discovered — proving the "hosted
  locally" deployment model provided zero protection.
- Mapped the full estate — 2 operator domains (including a brand-twin `.com` on the **same Cloudflare
  account**), 9 subdomains, 3 live web apps, exposed Postgres endpoints — and confirmed the service's
  **Critical** threat-intel rating (PhishDestroy, score 88).
- Delivered a full red-team-style operational record against a hardened live target: reconnaissance,
  surface mapping, exploit research, credential operations, reporting — with read-only discipline and
  zero destructive writes across ~1.3k requests.
- Built custom Python/Bash tooling for every phase: bundle extraction, RPC name-space harvesting (~780
  probes), auth-gap matrices, limiter analysis, and a Tor-isolated credential harness sustaining 4–5
  attempts/s with zero rate-limit rejections.
- Evaluated 2025–2026-era CVE exposure (Next.js middleware bypass, RSC/React2Shell chain) and documented
  why the edge architecture (Cloudflare semantic WAF, Cloudflare Tunnel origin) made them unreachable.

## Application security engineer / API security roles

- Tested the full Supabase stack (GoTrue v2.197.0, PostgREST, Storage, Realtime): JWT alg/JWKS enforcement,
  RLS policy boundaries, `SECURITY DEFINER` grant hygiene, storage bucket policies, and auth-flow edge cases.
- Recovered and tested a role-based admin authorization model (Supabase JWT + `profiles.role` DB check) and
  proved no bypass existed via method/header/path/CORS/prototype-pollution matrices.
- Identified storage-layer privacy failures as a class: anon listing, public object URLs, predictable names,
  and the downstream IDOR risk from reusing those names as application identifiers.

## SOC / monitoring / cloud-security roles (adapted)

- Operated an OSINT-and-telemetry workstream during the engagement: signup/login page watchers, tunnel
  availability monitoring, and estate-event tracking — translating infrastructure noise into actionable
  attacker-model changes.
- Authored detection-relevant observations: what the global limiter looks like in logs, what anonymous
  bucket enumeration traffic looks like, and which admin-plane endpoints produce useful audit signals.

## One-liner for the top of a résumé

> Security researcher & pentester — full-stack web/API/cloud assessments, red-team operations, and
> reverse engineering. I find the door, prove it's open, and write the report that gets it fixed.
> Portfolio: **<your-github>/onlyfakeai-security-audit**
