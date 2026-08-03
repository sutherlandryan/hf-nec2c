# Preservation maintenance

## Immutable references

The following annotated tags are permanent:

- `archive/nec2c-1.3.1-original` — first archival commit containing only the preservation
  envelope
- `preservation/nec2c-1.3.1-intake-v1` — archival commit plus project preservation
  documentation and verification tooling
- `maintained/nec2c-1.3.1-hf-portability-v1` — preserved maintained-source v1 identity,
  targeting `05f9a4f7ad9a089e45459db9099e47e0bf4533c2`

Never force-update, delete, move, or recreate any of these tags after publication. Confirm tag objects
and peeled commit targets before and after every repository transfer:

```powershell
git cat-file -t archive/nec2c-1.3.1-original
git rev-parse 'archive/nec2c-1.3.1-original^{}'
git cat-file -t preservation/nec2c-1.3.1-intake-v1
git rev-parse 'preservation/nec2c-1.3.1-intake-v1^{}'
git cat-file -t maintained/nec2c-1.3.1-hf-portability-v1
git rev-parse 'maintained/nec2c-1.3.1-hf-portability-v1^{}'
```

Run `.\verify-preservation.ps1` after clones, storage moves, Git upgrades, and before any public
release derived from the preserved source. A passing Git status alone is not preservation
verification.

## Future development

After the initial `main` and tags are published, all source, build, and tooling changes use
feature branches and pull requests. The immutable `archive/` and `upstream/` trees remain
unchanged. Build systems and maintained source belong in separate project-authored paths.

## Unmodified Windows baseline

The v0.0.5f-A2 external driver authenticates a fresh extraction, compiles only from that
disposable source tree, and performs source and repository preservation checks after every
attempt. Its versioned result is a repeatable MSVC failure at the original `unistd.h` dependency;
no executable exists.

Local `.build-temp/` and `.build-output/` evidence is ignored and must never be staged,
published, or copied into `upstream/`. Before removing an A2 temporary directory, resolve the
exact target and confirm that it is a task-created child of one of those two repository-local
roots. Never use a broad cleanup command.

The v0.0.5f-A2b driver applies the same source and preservation controls to the authenticated
MSYS2 UCRT64 / MinGW-w64 route at `C:\msys64`. The versioned result is a compile failure at the
original `sys/times.h` dependency after the shipped `configure` succeeds. No executable exists.
The package, installer, compiler, build-route, and normalized-diagnostic identities are pinned in
`manifests/windows-x64-mingw-ucrt64-unmodified-build-v1.json`.

A2b local evidence uses the same ignored `.build-temp/` and `.build-output/` roots. Attempt
identifiers are single-use. Do not delete evidence during a run; if later removal is explicitly
authorized, validate the exact task-created child path first.

## Maintained source identities

`HF_NEC2C_MAINTAINED_SOURCE_V1` remains preserved by its unchanged manifest, combined patch,
documentation, and immutable tag. Do not rewrite those v1 artifacts to describe later source.

`src/nec2c/` is now the independent `HF_NEC2C_MAINTAINED_SOURCE_V2` candidate. Relative to v1,
it contains exactly one four-line source-fidelity correction in `calculations.c`: the corrected
`cc5` exponent, the distinct `cn` constant, and the restored small- and medium-regime returns.
The complete combined v2 patch reconstructs all 36 files and 788,941 bytes directly from the
authenticated original archive; its identity and every source hash are recorded in
[`manifests/maintained-source-v2.json`](manifests/maintained-source-v2.json). It never replaces or
mutates `upstream/`.

Any later maintained-source change must update the combined patch and manifest, re-prove fresh
reconstruction, and retain the mixed-provenance license boundary. `calculations.c`, `main.c`,
`misc.c`, and `nec2c.h` remain original files containing exactly identified project-authored
modifications; their retained original material is not relabeled as BSD-2-Clause.

Builds stay out of tree under ignored task directories. Executables, objects, dependency files,
generated Makefiles, configuration logs, and reports are never tracked. The v2 candidate is
unqualified, unreleased, and unapplied. The
[NEC2DX oracle decision](docs/NEC2DX_ORACLE_DECISION.md) continues to allow only internal
secondary-cross-check use. Do not create or move a maintained-source v2 tag before review and
merge.

## Numerical qualification v0.0.5f-C

The frozen eight-case v1 baseline remains recorded unchanged in the
[v0.0.5f-B qualification record](docs/NUMERICAL_QUALIFICATION_V0_0_5F_B.md) and its existing
result summary. The complete v2 rerun has disposition **B. V2 SOURCE FIX VALIDATED;
QUALIFICATION REMAINS BLOCKED BY THE FROZEN REFERENCE MISMATCH.** All 24 reports passed integrity;
all cross-platform comparisons, invariants, convergence checks, and power-conservation checks
passed; all unaffected results remained exact; and no NEC2DX secondary disagreement remains.

The sole failure is the frozen official Example 2 feed-current imaginary literal
`-3.86680E-03 A`, versus approximately `-3.8666E-03 A` from both v2 primary builds and internal
NEC2DX. Do not widen its tolerance, replace or relabel the expected literal, declare it a
publication error, or begin an unrelated source investigation to route around it. See the
[v0.0.5f-C qualification record](docs/NUMERICAL_QUALIFICATION_V0_0_5F_C.md), unchanged
[suite manifest](manifests/numerical-qualification-v0.0.5f-b.json), and
[v2 result summary](manifests/numerical-qualification-v0.0.5f-c-results.json).

Keep rerun builds, executables, raw reports, official-manual files, and all NEC2DX material in
ignored task storage. The exact next milestone is independent review and merge of the v2
source-fix/requalification pull request. Release and HF Propagation Control integration remain
deferred pending resolution of the frozen reference mismatch.

## Post-review replication procedures

The following actions are intentionally deferred until a human has reviewed the public intake.
They were not performed during v0.0.5f-A1.

### Local bare mirror

Choose an approved storage location outside the working repository, then:

```text
git clone --mirror https://github.com/sutherlandryan/hf-nec2c.git <mirror-directory>
git -C <mirror-directory> fsck --full
git -C <mirror-directory> show-ref --heads --tags
```

For periodic maintenance:

```text
git -C <mirror-directory> bundle create <pre-fetch-bundle> --all
git -C <mirror-directory> fetch --no-tags origin +refs/heads/*:refs/heads/*
git -C <mirror-directory> fsck --full
```

Before and after that fetch, compare the exact archival and intake tag object IDs and peeled
targets. The command updates branch refs only; it deliberately neither prunes nor force-updates
tags. Fetch a new, human-reviewed tag with an explicit non-forced tag refspec. If an existing
immutable tag differs from the public remote, stop and investigate rather than updating it.

Record the mirror path only in the operator's local inventory, not in repository files.

### Periodic Git bundle

Create a dated bundle from the reviewed mirror or a clean clone:

```text
git -C <reviewed-clone> bundle create <bundle-file> --all
git -C <reviewed-clone> bundle verify <bundle-file>
```

Record the bundle byte count and SHA-256 in a separate preservation inventory. Restore-test the
bundle into a temporary location and run the repository verifier against its checked-out
`main` and archival tag.

### Off-site archive copy

Copy the reviewed Git bundle and the exact
`archive/nec2c-1.3.1.tar.bz2` to approved off-site storage. Recompute SHA-256 after transfer and
require the fixed archive digest
`8c706008bcb11c34bf33a3f8f78711c79f7bb49de8a22d74df6b10e1203c013e`.
Document storage identity and verification time outside this public repository; do not record
credentials or private storage paths here.

### Software Heritage

After public-repository human review, submit the public repository through the Software Heritage
save-code-now workflow. Record the returned archival identifier in a later reviewed
project-authored commit. Do not treat submission as a substitute for the byte manifests,
immutable tags, mirror, or bundle.
