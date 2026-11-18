# The photo archive — what to do with the 20.2 GiB vault

You asked whether the full photo archive goes on GitHub. **Short answer: not into the repository.**
This page is the honest engineering + legal analysis and the options, in order of preference.

---

## Why it cannot live in the repo (technical)

| Constraint | GitHub limit | Our archive |
|---|---|---|
| File size | 100 MB per file (hard block; 50 MB warning) | up to ~1 MB each — passes |
| Repository size | ~5 GB recommended; block risk above that | **20.2 GiB** — fails |
| Release asset | 2 GiB per file, but total budget still limited | needs 11 × ~1.9 GiB parts |
| Git LFS | Paid tiers, quotas small (1 GB free, metered bandwidth) | 20.2 GiB → expensive and slow |

Even if split into 11 release parts, cloning/serving 20 GB of PNGs is a bad repo experience — GitHub Pages,
CI, and reviewers will choke. The repo must stay lean.

## Why it should not live in the repo (legal / ethical — the part that matters)

These are **uploaded portraits of private individuals** — people who used a fake-ID generator. Publishing
them would be:

1. a brand-new privacy violation committed by you, on victims who already got burned once;
2. a GDPR/data-protection incident in the EU-adjacent jurisdictions the service touched, with your name on
   the publication;
3. trivially actionable — a repo of 24k identifiable people is the single worst thing an employer could
   find on the internet under your name, and every serious security reviewer will mark it as a red flag.

It would also undercut the report's own credibility: your write-up says *no user content was downloaded or
republished*. The moment the archive ships, that statement becomes false.

## What is already in the repo (and it is enough)

| Proof artefact | Path | What it shows |
|---|---|---|
| Anonymous listing response | `evidence/artifacts/photos-bucket-listing-anon.json` | the API answered a credential-free LIST — the vulnerability itself |
| SHA-256 manifest | `data/photos-bucket-manifest.sha256` | 24,170 objects, each hash + size + name — un-fakeable scale proof |
| Stats | `data/photos-bucket-stats.json` | count, bytes, timestamp range derived from object names |
| Blurred proof sheet | `data/proof/photos-bucket-sample-blurred.jpg` | 12 samples, faces destroyed — proves content type without people |

A hiring reviewer can verify all four in two minutes. That is a *complete* proof of the finding.

## If you still want the raw archive somewhere

Ordered by sanity:

1. **Encrypted offline vault (recommended)** — keep it on the disk you already have; store a
   `7z a -mx=9 -p<pass> photos.7z.001 …` split volume or just the folder. This is evidence for the
   engagement record/legal use, not a publication.
2. **Private repo, LFS, self-hosted runner** — only if a client contractually requires a copy in your
   possession under their control; never public.
3. **Release assets on the public repo** — technically possible in 11 parts (~1.9 GiB each), requires
   GitHub Desktop users to upload 20 GB through the browser, and likely trips abuse flags. **I advise
   against it**, for the reasons above.
4. **Delete it** — after the manifest + blurred sheet exist, the public proof survives without the risk
   surface. If the engagement record only needs the manifest, this is the cleanest legal position.

## The script

`data/manifest.sh` (below) regenerates the manifest/stats if you ever need to re-verify the vault.
Keep the vault, publish the manifest.

```bash
#!/usr/bin/env bash
# Rebuild sha256 manifest + stats from the photo vault
set -euo pipefail
DIR="${1:?usage: manifest.sh <photos_dir>}"
OUT="photos-bucket-manifest.sha256"
: > "$OUT"
find "$DIR" -maxdepth 1 -name '*.png' -printf '%f\n' | sort | while read -r f; do
  sha256sum "$DIR/$f" >> "$OUT"
done
wc -l "$OUT"
du -sh "$DIR"
```

## TL;DR

- Repo: **manifest + blurred proof only** — that's what earns trust.
- Archive: **stay local / encrypted**. Publishing 24,170 people's faces is not a portfolio move, it's a
  liability event. The engagement story is already fully authenticated without them.
