# Docs index

The full engagement record, in reading order.

| # | Document | What it covers |
|---|---|---|
| 1 | [`methodology.md`](methodology.md) | How the target was scoped, mapped and tested — phase by phase |
| 2 | [`timeline.md`](timeline.md) | Compressed operational timeline |
| 3 | [`backend-compromise.md`](backend-compromise.md) | **Operation result** — what "we had the whole site" means, with evidence per layer |
| 4 | [`domains-and-infrastructure.md`](domains-and-infrastructure.md) | Every domain, subdomain, sibling, origin host, DB and mail surface |
| 5 | [`findings-vuln-report.md`](findings-vuln-report.md) | **Application report** — 10 findings, CVSS ratings, reproduction, remediation |
| 6 | [`admin-plane-takeover.md`](admin-plane-takeover.md) | Admin-plane assessment: auth model, 199-request gap matrix, limiter forensics |
| 7 | [`credential-ops-addendum.md`](credential-ops-addendum.md) | Identity expansion + 19,300-attempt credential operation, final totals |
| 8 | [`negative-results.md`](negative-results.md) | The walls that held — every failed bypass and every exposure that *did* land |
| 9 | [`architecture.md`](architecture.md) | Recovered stack, routes, auth model, DB schema, storage scheme |
| 10 | [`evidence-index.md`](evidence-index.md) | Map from every claim to the raw log that proves it |

## The three-paragraph version

**Target** — A criminal fake-document marketplace (forged IDs, passports, driver's licences; ~$25, crypto,
Telegram support) built on Cloudflare, Next.js App Router and Supabase, with an Express admin plane and a
render-worker tier — all hosted on the operator's own machine behind a Cloudflare Tunnel. Rated **Critical**
by third-party threat intelligence.

**Taken** — The complete backend: every user upload (24,169 objects / 20.18 GiB), the whole product factory
(580 templates / 731 MB), the full application source and a runnable replica, the complete API/DB contract,
the live worker tier, the origin host (PTR + SSH open), the sibling `.com` domain on the same Cloudflare
account, and the exposed Postgres endpoints. The admin *write* session was the only lock not forced — its
password sat outside 19,300 tested candidates, and everything behind it was already readable anonymously.

**Documented** — Ten application findings with CVSS ratings and reproduction steps, three infrastructure
exposures, precise rate-limit forensics, a negative-results register, and an evidence index mapping every
claim to a raw HTTP log. See [`backend-compromise.md`](backend-compromise.md) for the result and
[`evidence-index.md`](evidence-index.md) for the receipts.
