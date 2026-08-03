# Preservation maintenance

## Immutable references

The following annotated tags are permanent:

- `archive/nec2c-1.3.1-original` — first archival commit containing only the preservation
  envelope
- `preservation/nec2c-1.3.1-intake-v1` — archival commit plus project preservation
  documentation and verification tooling

Never force-update, delete, move, or recreate either tag after publication. Confirm tag objects
and peeled commit targets before and after every repository transfer:

```powershell
git cat-file -t archive/nec2c-1.3.1-original
git rev-parse 'archive/nec2c-1.3.1-original^{}'
git cat-file -t preservation/nec2c-1.3.1-intake-v1
git rev-parse 'preservation/nec2c-1.3.1-intake-v1^{}'
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

## Maintained source v1

`src/nec2c/` is the independent `HF_NEC2C_MAINTAINED_SOURCE_V1` candidate. It is reconstructed
from the authenticated original archive by the combined maintained patch recorded in
`manifests/maintained-source-v1.json`; it never replaces or mutates `upstream/`. Any maintained
source change must update the combined patch and manifest, re-prove fresh reconstruction, and
retain the mixed-provenance license boundary.

Builds stay out of tree under ignored task directories. Executables, objects, dependency files,
generated Makefiles, configuration logs, and smoke reports are never tracked. The v1 candidate is
unqualified, unreleased, and unapplied. The
[NEC2DX oracle decision](docs/NEC2DX_ORACLE_DECISION.md) allows only internal secondary-cross-check
use. The later internal build and reproducibility prerequisites did not alter its
non-redistribution boundary or authorize integration.

## Numerical qualification v0.0.5f-B

The frozen eight-case seed corpus has disposition **NUMERICAL QUALIFICATION BLOCKED**. The
authoritative NEC-2 Part III Example 2 `LD` type 5 conductivity stage disagrees with both fresh
maintained builds; the first implicated boundary is `zint()` in the circular-wire
internal-impedance path. Maintained source was deliberately left unchanged. See the
[qualification record](docs/NUMERICAL_QUALIFICATION_V0_0_5F_B.md),
[suite manifest](manifests/numerical-qualification-v0.0.5f-b.json), and
[normalized result summary](manifests/numerical-qualification-v0.0.5f-b-results.json).

Keep rerun builds, executables, raw reports, official-manual files, and all NEC2DX material in
ignored task storage. Do not widen tolerances or expand the corpus to route around the failure.
Any `LD` type 5 / `zint()` investigation, source correction, requalification, binary release, or
HF Propagation Control integration requires its own authorization and reviewed milestone.

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
