# hf-nec2c

`hf-nec2c` is an independent preservation and maintained-derivative repository. It is not the
official NEC2C project, does not claim succession to that project, and does not claim endorsement
by Neoklis Kyriazis.

The repository preserves the original-author NEC2C 1.3.1 distribution, records the untouched-source
Windows compiler baselines, and carries the independently authored
`HF_NEC2C_MAINTAINED_SOURCE_V1` portability candidate under `src/nec2c/`. The immutable archive and
upstream extraction remain byte-preserved; maintained changes are isolated and reconstructible
from a deterministic combined patch.

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

## Windows x64 untouched-source build baselines

### A2: MSVC

The A2 build entry point is:

```powershell
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass `
    -File .\build-support\windows-x64\build.ps1 -BuildId <fresh-id>
```

It authenticates and freshly extracts the archive before compiling, keeps all generated
material ignored, and reverifies source and preservation state afterward. The installed
environment had no GCC/MinGW-w64 or Clang route. The only native AMD64 candidate, MSVC 19.29,
failed consistently because the untouched source requires `unistd.h`. See
[docs/WINDOWS_X64_UNMODIFIED_BUILD.md](docs/WINDOWS_X64_UNMODIFIED_BUILD.md) and
[manifests/windows-x64-unmodified-build-v1.json](manifests/windows-x64-unmodified-build-v1.json).
The canonical disposition is: **UNMODIFIED MSVC WINDOWS X64 BUILD ATTEMPT REPRODUCIBLY BLOCKED
BY POSIX HEADER DEPENDENCY**.

### A2b: MSYS2 UCRT64 / MinGW-w64

The A2b build entry point is:

```powershell
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass `
    -File .\build-support\windows-x64-mingw-ucrt64\build.ps1 `
    -BuildId <fresh-id>
```

The authenticated, fully updated MSYS2 environment at `C:\msys64` used UCRT64 GCC 16.1.0-5
targeting `x86_64-w64-mingw32`. The shipped `configure` completed out of tree, then GNU `make`
failed while compiling the first translation unit because original `nec2c.h` line 15 requires
`sys/times.h`, which the installed MinGW-w64 UCRT64 headers do not provide. Source authentication
and preservation checks passed before and after the attempt. No source byte was changed, no
compatibility code was added, no executable was produced, and numerical behavior remains
unqualified.

See
[docs/WINDOWS_X64_MINGW_UCRT64_UNMODIFIED_BUILD.md](docs/WINDOWS_X64_MINGW_UCRT64_UNMODIFIED_BUILD.md)
and
[manifests/windows-x64-mingw-ucrt64-unmodified-build-v1.json](manifests/windows-x64-mingw-ucrt64-unmodified-build-v1.json).
The canonical disposition is: **UNMODIFIED MSYS2 UCRT64 WINDOWS X64 BUILD ATTEMPT BLOCKED BY
SYS/TIMES.H DEPENDENCY**.

### Native process-timing reconnaissance

A project-authored BSD-2-Clause reconnaissance candidate now records the smallest tested
process-CPU-time boundary for the original NEC2C 1.3.1 source. The candidate remains a patch
artifact under [`probes/`](probes/portable-process-timing-v1.patch); it is not a maintained source
tree, qualified solver, or distribution approval.

The corrected patch preserved the existing source-file EOF bytes and every non-timing line in the
MSYS minimal-dipole report. Under native UCRT64, it advanced compilation beyond `sys/times.h` to
the first new proven blocker: the unavailable `struct sigaction` interface at original `main.c`
line 84. Linking was not reached and no native executable was produced. See the
[native UCRT64 timing probe](docs/NATIVE_UCRT64_TIMING_PROBE.md) for the bounded evidence and
non-qualification limits.

### Native signal-registration reconnaissance

A second project-authored BSD-2-Clause reconnaissance patch records the smallest tested
signal-registration platform boundary. It remains a patch artifact under
[`probes/`](probes/portable-signal-registration-v1.patch), not a maintained source tree,
qualified solver, or distribution approval.

The patch preserved the complete 6,825-byte MSYS minimal-dipole report and advanced native
UCRT64 compilation beyond `struct sigaction`, producing `main.o`. The next proven blocker is
the original `CR` macro at `nec2c.h:76` colliding with the native `winnt.h` `CR` bit-field
while compiling `misc.c`. Linking was not reached and no native executable was produced. See
the [native UCRT64 signal probe](docs/NATIVE_UCRT64_SIGNAL_PROBE.md) for the bounded evidence and
non-qualification limits.

### Native parser-control-character reconnaissance

A third project-authored BSD-2-Clause reconnaissance patch localizes NEC2C's generic `CR` and
`LF` parser constants. It remains a patch artifact under
[`probes/`](probes/portable-parser-control-chars-v1.patch), not a maintained source tree,
qualified solver, release artifact, or integration approval.

After the validated timing and signal patches, this patch preserved the complete accepted
6,825-byte MSYS report. Native UCRT64 then compiled all 12 translation units, linked a PE32+
AMD64 executable with no `msys-2.0.dll` import, and passed `-v`, `-h`, and one
minimal-dipole run. Normalizing only native CRLF to LF made the complete native report
byte-identical to the MSYS report. See the
[native UCRT64 parser-control-character probe](docs/NATIVE_UCRT64_CONTROL_CHAR_PROBE.md) for the
bounded evidence and non-qualification limits.

## Maintained source candidate

The validated probe sequence has been promoted into the provenance-complete
`HF_NEC2C_MAINTAINED_SOURCE_V1` tree at `src/nec2c/`. The final tree contains 36 files and 788,897
bytes. A fresh authenticated extraction reconstructed it byte-for-byte using only the combined
[`nec2c-1.3.1-hf-portability-v1.patch`](patches/maintained/nec2c-1.3.1-hf-portability-v1.patch),
whose SHA-256 is
`cfb8da8689ec85817d12c2f95c51c599117c1b5e140f589a0a05bd82c9899e5b`.

Exactly one maintained-source MSYS build retained the accepted 6,825-byte report identity.
Exactly one native UCRT64 build compiled all 12 translation units, linked PE32+ AMD64 without an
`msys-2.0.dll` import, and produced a report that matched MSYS byte-for-byte after only CRLF-to-LF
normalization. These are build and bounded regression results, not numerical qualification.

See the [maintained-source record](docs/MAINTAINED_SOURCE_V1.md) and
[manifest](manifests/maintained-source-v1.json) for construction, provenance, hashes, build
evidence, and current limitations.

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

This repository contains maintained source but no tracked solver executable, release, Git LFS
object, GitHub Actions workflow, submodule, package dependency, or Software Heritage submission.
The maintained candidate is independent, numerically unqualified, unreleased, and unapplied. It
is not approved for distribution or HF Propagation Control integration. The next separately
authorized milestone is the `v0.0.5f-B` nec2dx numerical baseline and comparison corpus.

See [PROVENANCE.md](PROVENANCE.md), [CONTRIBUTING.md](CONTRIBUTING.md), and
[MAINTENANCE.md](MAINTENANCE.md) for the evidence and controls.

## Engineering policy and portability map

- [Engineering execution policy](docs/ENGINEERING_EXECUTION_POLICY.md)
- [NEC2C 1.3.1 portability map](docs/NEC2C_PORTABILITY_MAP.md)
- [MSYS POSIX unmodified build probe](docs/MSYS_POSIX_UNMODIFIED_BUILD_PROBE.md) records that
  untouched NEC2C 1.3.1 builds and runs as an unqualified, MSYS-runtime regression-baseline candidate.
