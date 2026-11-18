# LinkedIn / X announcement drafts

Three lengths. Pick one, tweak the voice, post with a screenshot of the architecture diagram or the blurred
proof sheet (never user data). Link the repo.

---

## Short (LinkedIn, ~120 words)

I just published a full security-engagement record from a two-day audit of a live SaaS estate.

Stack: Cloudflare → Next.js → Supabase → a public Express admin plane.
Result: 10 findings, a 24,170-image public-bucket exposure, and a 19,300-attempt credential operation that
found nothing — which is exactly why the report is worth reading. The negative results are the interesting
part: JWT forgery, role injection, RLS/trigger escalation, admin-plane bypass matrices, all documented with
raw evidence.

Full methodology, harnesses, and write-ups here: **<repo-link>**

I'm looking for a role where this kind of work is the job — web/API/cloud pentesting, red team, or
application security. DMs open.

---

## Medium (covers the technical hook)

**What does it look like to audit an estate you have to map from zero?**

Over two days I took a fake-document marketplace apart: certificate transparency found an unlinked admin
plane, client bundles gave up the API contract, and the storage layer turned out to serve 24,170 user
uploads to anyone with the site's public key and a browser.

The part I'm proudest of isn't a vulnerability — it's the honesty of the record:

- 10 findings, severity-rated with reproduction steps — including **3 confirmed access-control bypasses**
- a 199-request authorization matrix proving the admin gate actually held
- a 19,300-attempt credential operation that turned out to be unnecessary: the data behind the admin door
  was already open to anonymous access
- a negative-results register listing every wall so nobody re-spends the time

Reports, raw evidence, and every harness: **<repo-link>**

I build and break web/API/cloud stacks — and I document like the report will be read by someone
technical, skeptical, and short on time. That's the job I want next.

---

## Technical / X thread starter

1/ I spent two days auditing a live Next.js + Supabase estate. Found a public bucket serving 24,170 user
images, an unlinked admin dashboard, and a login limiter that's global for the whole planet. Full write-up ↑

2/ The estate was mapped from zero: CT logs → 4 hostnames, 141-name DNS brute → a dead CF tunnel, client
bundle beautification → complete API contract. No docs needed.

3/ The storage bug was simple and devastating: publishable key is public by design, but the `photos` bucket
accepted anonymous LIST. And object names were `<unix-ms>_preview.png` — which the app reused as job IDs.

4/ The admin plane was exposed but *correct*: ES256/JWKS, server-side role check, per-route gating. I threw a
199-request matrix at it — no bypass. Exposure + no MFA was the finding, not an auth magic trick.

5/ The fun part: 19,300 credential attempts via Tor circuit rotation — then proof that the password was
unnecessary, because three access-control bypasses (anonymous storage read, unauthenticated job endpoints,
self-unban) already handed over the backend. Authorization was the weak layer, not authentication.

6/ Repo has every raw request/response log, the harnesses, the negative results. Reports are the article of
record. **<repo-link>** — open to pentest / appsec / red-team roles.
