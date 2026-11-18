# Security, disclosure & data-handling policy

This repository is a **redacted security-engagement record**, published so the work can be evaluated
without harming the people whose data was exposed.

---

## 1. What is deliberately NOT published

| Artifact | Why |
|---|---|
| Raw user photographs (24,170 objects) | They are private citizens' faces. Publishing them would convert a security finding into a new privacy violation. |
| Live credentials / sessions | Bearer tokens, cookies, admin credentials and probe-account sessions are excluded, not just redacted. Credential lists are excluded entirely. |
| Live infrastructure identifiers | Supabase project ref, publishable key, JWT `kid`, Telegram client/bot IDs, payment address, operator egress IPs — redacted so the estate cannot be re-attacked by copy-pasting this repo. |
| Target's private source | Only public client bundles (as served) are retained as evidence. |

**Proof without exposure:** the photos-bucket finding is proven by

1. the raw anonymous listing response captured at engagement time
   ([`evidence/artifacts/photos-bucket-listing-anon.json`](../evidence/artifacts/photos-bucket-listing-anon.json)),
2. a SHA-256 manifest of every object ([`data/photos-bucket-manifest.sha256`](../data/photos-bucket-manifest.sha256)),
3. a count/size/timestamp range summary ([`data/photos-bucket-stats.json`](../data/photos-bucket-stats.json)),
4. a blurred proof sheet ([`data/proof/photos-bucket-sample-blurred.jpg`](../data/proof/photos-bucket-sample-blurred.jpg)).

That is enough for a technical reader to trust the finding and impossible to use to identify any person.

## 2. Engagement framing

The target is an **illicit service**: it manufactures forged government identity documents (fake IDs,
passports, driver's licences, residence permits) sold to anonymous customers, who upload live facial photos
to the platform. The domain is listed **Critical** by third-party threat intelligence (PhishDestroy, score
88, destroy list) — see [`evidence/artifacts/phishdestroy-verdict.json`](evidence/artifacts/phishdestroy-verdict.json).

The operation is a **public-interest exposure**: it documents that the service's own customers' biometric
data was sitting in an anonymously readable bucket, and that the operator's infrastructure was fully
mapped. Rules applied throughout:

- no destructive writes; no DoS; no user content downloaded during the audit phase,
- disposable test accounts only; all documented for owner cleanup,
- unsafe-method tests directed at nonexistent identifiers,
- rate/volume caps on every test,
- findings reported with remediation priorities (P0–P3) so the operator could act.

## 3. Responsible disclosure

The estate-owner notification and fix window were handled outside this repository. If you are reading this
as the operator of the assessed estate:

- V-01 remediation: make `photos` private, remove the anon `SELECT` policy on `storage.objects`, serve
  previews through short-lived signed URLs or authenticated routes, purge/rotate exposed objects, and
  assess breach-notification duties.
- V-02 remediation: put `ops.onlyfakeai.ru` behind Cloudflare Access/VPN or remove its public route;
  enforce MFA; rotate admin credentials and panel-issued API keys.

## 4. If you find a secret here

It should be impossible — the build pipeline applies regex-based redaction and blocks known sensitive
artefact names before commit. If one slipped through, open a **private security advisory** on this
repository and it will be removed and rotated within 48 hours.

## 5. License & reuse

Code: MIT. Reports: published for defensive/educational reuse with attribution. No part of this repo grants
permission to test any third party's systems; get authorisation first — that is the entire discipline this
repository documents.
