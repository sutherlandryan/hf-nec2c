# NEC2C 1.3.1 preservation provenance

This record describes the byte-exact intake of the selected original-author NEC2C 1.3.1
distribution. It follows the source-selection policy in `sutherlandryan/hf-prop-control` at
commit `ac231157b218415598f9d8a389492bef11d0a5a6`.

## Initial repository state

Before intake, `sutherlandryan/hf-nec2c` was publicly accessible and empty. Git advertised no
refs: there was no README, license, `.gitignore`, branch history, generated initialization
commit, or other repository content. The local destination was absent before the clean clone
used for this intake.

## Selected artifact

| Field | Value |
|---|---|
| Original author | Neoklis Kyriazis |
| Selected release | NEC2C 1.3.1 |
| Original URL | `https://www.qsl.net/5b4az/pkg/nec2/nec2c/nec2c-1.3.1.tar.bz2` |
| Final URL | `https://www.qsl.net/5b4az/pkg/nec2/nec2c/nec2c-1.3.1.tar.bz2` |
| Request started UTC | `2026-07-29T06:26:09.0223842Z` |
| Retrieval completed UTC | `2026-07-29T06:26:09.7719163Z` |
| HTTP method/result | `GET`; `200 OK` |
| Response Date | `Wed, 29 Jul 2026 06:26:10 GMT` |
| Response ETag | `"c9817f-2d70c-60b80e01d4d00;6502866455e40"` |
| Other response metadata | `Content-Length: 186124`; `Content-Type: application/x-bzip2`; `Last-Modified: Sat, 02 Dec 2023 06:20:04 GMT`; `Accept-Ranges: bytes`; `Server: cloudflare` |
| Downloaded bytes | `186124` |
| Expected SHA-256 | `8c706008bcb11c34bf33a3f8f78711c79f7bb49de8a22d74df6b10e1203c013e` |
| Observed SHA-256 | `8c706008bcb11c34bf33a3f8f78711c79f7bb49de8a22d74df6b10e1203c013e` |
| Retrieval tool | Windows PowerShell `Invoke-WebRequest` 5.1.26100.8894 |
| Extraction tool | CPython 3.13.5 standard-library `tarfile` |
| Manifest tool | `HF_NEC2C_PRESERVATION_MANIFEST_GENERATOR` version 1 on CPython 3.13.5 |

The original-author endpoint supplied the exact expected bytes; no recovery mirror, package
manager repack, or substitute artifact was used.

## Archive and extracted layout

The authenticated archive contains one top-level directory, `nec2c-1.3.1`, and no alternative
layout adjustment was required.

| Evidence | Value |
|---|---:|
| Archive members | 35 |
| Directory members | 1 |
| Regular-file members | 34 |
| Extracted regular-file bytes | 786,583 |
| Symbolic links, hard links, or special members | 0 |

Repository paths:

- `archive/nec2c-1.3.1.tar.bz2` — the unmodified original archive
- `upstream/nec2c-1.3.1/` — the unflattened extracted tree
- `manifests/nec2c-1.3.1-archive.sha256` — archive hash, name, and byte count
- `manifests/nec2c-1.3.1-files.sha256` — raw-byte hashes in ordinal path order
- `manifests/nec2c-1.3.1-tar-listing.txt` — original member order and metadata
- `manifests/nec2c-1.3.1-intake.json` — versioned acquisition and intake record

The first archival commit is
`b1ff42e308c8a1c80dc7a77636a5908e870af6f6`, tagged
`archive/nec2c-1.3.1-original`.

## Exact upstream evidence

The exact extracted README is `upstream/nec2c-1.3.1/README`, SHA-256
`8a5542b7753814265448633ac6b2fb92bb8c74aece333615a0baad2a590c6984`.

- Section 7 begins at line 209.
- The public-domain declaration is at line 210.
- The request to keep incorporating software in the public domain or use an open license such as
  GPL or BSD is at lines 211–212.
- The author section begins at line 214.
- The identifying signature, `Neoklis Kyriazis`, is at line 216.
- The associated date, `February 12 2013`, is at line 218.

The bundled complete GPLv3 license text is
`upstream/nec2c-1.3.1/COPYING`, SHA-256
`8ceb4b9ee5adedde47b31e975c1d90c73ad27b6b165a1dcd80c7c545eb65b903`.
It remains byte-preserved and material to the historical evidence. Original U.S. government
sponsorship, warranty, liability, completeness, usefulness, and non-infringement notices also
remain in the source files.

This repository follows the merged source-selection policy based on that preserved evidence. It
does not make a new legal conclusion about every possible copyright question.

## Byte and metadata preservation

`.gitattributes` disables text conversion, filters, keyword expansion, and working-tree encoding
for both the archive and upstream tree. The 34 extracted regular files are hashed from raw bytes.
The eight archive members with mode `0755` are recorded as executable in the archival Git tree.

Windows and Git do not portably retain archive UID/GID, user/group names, every POSIX permission
bit, or filesystem timestamps across checkouts. The original archive remains byte-exact, and the
deterministic tar listing records those original values. Git preserves the regular-file
executable distinction.

Before the archival tag was created, the final archive hash and every extracted-file hash were
recomputed; a separate fresh extraction was compared by raw bytes; missing and extra files were
checked; and the protected Git index blobs were compared with the working-tree bytes.

## Negative provenance statements

- No upstream source was modified or normalized.
- No NEC2C source was compiled or executed.
- No maintained NEC2C v1.3.3 or later-contributor source was imported.
- No build product or solver binary was added.
- The preserved upstream tree came only from the authenticated original-author archive.
