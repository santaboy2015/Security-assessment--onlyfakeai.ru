# Docs index

The engagement record, in reading order.

| # | Document | What it covers |
|---|---|---|
| 1 | [`methodology.md`](methodology.md) | How the target was scoped, mapped and tested — phase by phase |
| 2 | [`timeline.md`](timeline.md) | Compressed operational timeline (2 days, ~1.3k requests) |
| 3 | [`findings-vuln-report.md`](findings-vuln-report.md) | **Flagship report** — 10 findings, CVSS ratings, reproduction, remediation |
| 4 | [`admin-plane-takeover.md`](admin-plane-takeover.md) | Admin-plane assessment: auth model, 199-request gap matrix, limiter forensics |
| 5 | [`credential-ops-addendum.md`](credential-ops-addendum.md) | Identity expansion + 19,300-attempt credential operation, final totals |
| 6 | [`negative-results.md`](negative-results.md) | The walls that held — every failed bypass, documented |
| 7 | [`architecture.md`](architecture.md) | Recovered stack, routes, auth model, DB schema, storage scheme |
| 8 | [`evidence-index.md`](evidence-index.md) | Map from every claim to the raw log that proves it |

## The three-paragraph version

**What** — A live fake-document marketplace built on Cloudflare, Next.js App Router and Supabase, with an
Express admin plane on a separate subdomain. Two-day full-stack assessment, read-only rules of engagement.

**Found** — Ten findings. Two High: an anonymous Supabase Storage bucket serving 24,169 user portraits
(20.2 GiB), and an Internet-exposed admin dashboard with no MFA or IP allow-list. Plus unauthenticated
`SECURITY DEFINER` RPCs leaking live business counts, a user-writable `banned` column, IDOR-risk job
endpoints, and a global login limiter that lets anyone lock admins out.

**Not found** — No auth bypass, no role-write path, no secret in client artifacts, and no credential in
19,300 attempts. The takeover stopped at a credential door; the report documents the remaining ladder
instead of inventing success. Negative results are in [`negative-results.md`](negative-results.md).
