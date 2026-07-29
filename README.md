# hf-nec2c

`hf-nec2c` is an independent preservation and maintained-derivative repository. It is not the
official NEC2C project, does not claim succession to that project, and does not claim endorsement
by Neoklis Kyriazis.

The current repository establishes only the preservation intake of the original-author NEC2C
1.3.1 distribution. It has not compiled, executed, patched, formatted, normalized, modernized,
or otherwise modified the preserved source.

## Preservation identity

- Original author: Neoklis Kyriazis
- Selected release: NEC2C 1.3.1
- Original archive: `nec2c-1.3.1.tar.bz2`
- Archive size: 186,124 bytes
- SHA-256:
  `8c706008bcb11c34bf33a3f8f78711c79f7bb49de8a22d74df6b10e1203c013e`
- Archive tag: `archive/nec2c-1.3.1-original`
- Intake tag: `preservation/nec2c-1.3.1-intake-v1`

The original archive is preserved byte-for-byte in `archive/`. Its exact extracted source tree
is in `upstream/nec2c-1.3.1/`. Deterministic hashes, archive metadata, and retrieval evidence are
in `manifests/`.

The maintained NEC2C v1.3.3 tree is not the source base. No later-contributor source has been
silently imported.

## Provenance and licensing

Repository policy handles the original NEC2C 1.3.1 source under the preserved original-author
public-domain statement in README section 7. The complete original README, its author/date
footer, original notices and disclaimers, and the bundled GPLv3 `COPYING` remain preserved as
historical source evidence.

BSD-2-Clause applies only to copyrightable project-authored additions and modifications. It does
not relabel the original archive, the extracted upstream source, or later third-party work as
project-owned BSD code. This mixed-provenance repository intentionally has no plain root
`LICENSE`; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and
[LICENSES/README.md](LICENSES/README.md).

## Verify offline

From Windows PowerShell:

```powershell
.\verify-preservation.ps1
```

Or invoke the standard-library Python verifier directly:

```powershell
py -3 -I .\tools\verify_preservation.py --repository-root .
```

The verifier performs no network access and writes no files. It recomputes the fixed archive
SHA-256, checks the archive byte count, verifies every extracted file from raw bytes, and detects
missing, extra, linked, reparse-point, or other unsupported objects in the preserved tree.

## Relationship to HF Propagation Control

HF Propagation Control remains a separate application. Its planned integration uses a documented
process/file boundary:

```text
HF Propagation Control
    -> generated NEC input deck
    -> separate hf-nec2c executable
    -> structured solver result
    -> solver-neutral pattern data
```

No NEC2C source is copied into HF Propagation Control. This process boundary supports independent
provenance and release management; it is not claimed to be a complete operating-system sandbox.

## Current boundary

This intake contains no solver build, binary, release, Git LFS object, GitHub Actions workflow,
submodule, package dependency, or Software Heritage submission. The next job, after human review,
is v0.0.5f-A2: create a reproducible unmodified Windows x64 build outside the immutable upstream
tree. A2 has not started.

See [PROVENANCE.md](PROVENANCE.md), [CONTRIBUTING.md](CONTRIBUTING.md), and
[MAINTENANCE.md](MAINTENANCE.md) for the evidence and controls.
