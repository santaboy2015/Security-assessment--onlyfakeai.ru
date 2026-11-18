# Proof data

This folder proves the scale of the storage exposure **without republishing any personal data**.

| File | Content |
|---|---|
| `photos-bucket-manifest.sha256` | One line per object: `sha256  size  filename`. 24,170 lines. If you have a candidate copy of the bucket, verify it with `sha256sum -c`. |
| `photos-bucket-stats.json` | Machine-readable summary: object count, total bytes, naming scheme, first/last object timestamps, provenance note. |
| `proof/photos-bucket-sample-blurred.jpg` | 12 sampled objects, Gaussian-blurred to destroy facial detail. Proves the objects are portrait PNGs and that the bucket is real. |

## Verification

```bash
# count check
wc -l photos-bucket-manifest.sha256
# -> 24170

# verify a local copy of the bucket against the manifest
cd /path/to/photos_copy
sha256sum -c /path/to/photos-bucket-manifest.sha256
```

## Read this before asking "where are the photos?"

They are **deliberately not published**. See [`../ARCHIVE.md`](../ARCHIVE.md) and
[`../SECURITY.md`](../SECURITY.md): the exposure itself is the finding; republishing the victims' faces
would be a second violation. The manifest is the un-fakeable proof.
