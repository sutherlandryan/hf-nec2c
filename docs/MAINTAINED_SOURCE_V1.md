# Maintained NEC2C source v1

## Status

`HF_NEC2C_MAINTAINED_SOURCE_V1` is the first provenance-complete maintained source candidate in
this independent repository. It is based on the preserved original-author NEC2C 1.3.1 release,
adds the three validated Windows-portability behaviors, and retains upstream `PACKAGE_STRING`
unchanged.

This candidate is unqualified, unreleased, and unapplied. It is not approved for binary
distribution or HF Propagation Control integration. The build and smoke results below are bounded
portability and same-input regression evidence, not numerical qualification.

## Construction

The maintained tree was constructed without using NEC2C v1.3.3 or any later-contributor source:

1. Authenticate `archive/nec2c-1.3.1.tar.bz2` at SHA-256
   `8c706008bcb11c34bf33a3f8f78711c79f7bb49de8a22d74df6b10e1203c013e` and freshly extract its
   34 regular files with the repository source guard.
2. Initialize a disposable Git repository at the extracted source root with `core.autocrlf=false`
   and `core.eol=lf`, then commit the authenticated original baseline.
3. Check and apply, with `git apply --whitespace=error-all`, these exact committed patches in
   order:
   1. `probes/portable-process-timing-v1.patch` —
      `f65347275a21bbdc90b009aec4fb9db10a2918ac33a77be30809fb1db57b8aae`
   2. `probes/portable-signal-registration-v1.patch` —
      `6fc3f4b63eef0a90ae7a78708aa77bca01da802864a1cd1b6fc85091027e27af`
   3. `probes/portable-parser-control-chars-v1.patch` —
      `d010c3d04a78537b03f717674947fd610747e9c347845d4a109cb2595e459283`
4. Require the resulting source delta to be exactly `M main.c`, `M misc.c`, `M nec2c.h`,
   `A platform_signal.h`, and `A platform_time.h`; require the other 31 original files to remain
   byte-identical; run `git diff --check`; and remove the disposable Git metadata.
5. In the maintained tree only, change the introductory comments in the two platform headers to
   identify them as project-authored maintained portability code and retain their
   `SPDX-License-Identifier: BSD-2-Clause` lines. This promotion is source-comment-only.

The resulting `src/nec2c/` tree contains 36 regular files and 788,897 bytes. Exact per-file hashes
are in [`maintained-source-v1.json`](../manifests/maintained-source-v1.json).

## Reconstruction identity

[`nec2c-1.3.1-hf-portability-v1.patch`](../patches/maintained/nec2c-1.3.1-hf-portability-v1.patch)
is the deterministic combined patch from the authenticated original baseline to the final
maintained tree. Its SHA-256 is
`cfb8da8689ec85817d12c2f95c51c599117c1b5e140f589a0a05bd82c9899e5b`.

A separate fresh authenticated extraction accepted only this combined patch and reproduced all 36
maintained files byte-for-byte, with no missing, extra, or changed path.

## Provenance and license scope

Original NEC2C material remains handled under the original-author public-domain statement
preserved in `src/nec2c/README` and `upstream/nec2c-1.3.1/README`. Original notices and
disclaimers remain in the maintained files. The project-authored portability additions and
modifications are BSD-2-Clause; the combined patch and manifest identify their exact scope.
`platform_signal.h` and `platform_time.h` are wholly project-authored BSD-2-Clause files.

This repository and maintained source are independent and are not official NEC2C or endorsed by
Neoklis Kyriazis. No blanket BSD claim is made over the original material.

## Maintained-source build and smoke results

Exactly two fresh out-of-tree builds used the shipped `configure` route and `/usr/bin/make -j1`.
No `autoreconf` or package operation was run, and neither build modified `src/nec2c/`.

### MSYS POSIX

- Environment: `MSYSTEM=MSYS`
- Compiler: `/usr/bin/gcc`
- Translation units compiled: 12
- Link: succeeded
- `nec2c -v`: exit 0
- `nec2c -h`: exit 0
- One minimal-dipole run: exit 0
- Report: 6,825 bytes
- Report SHA-256: `396b90cfb8e49fcf1938e01d291638163f74e3b065e29b8456ece3b3ca482567`

The report exactly retains the accepted untouched MSYS report identity.

### Native UCRT64

- Environment: `MSYSTEM=UCRT64`
- Compiler: `/ucrt64/bin/gcc`
- Translation units compiled: 12
- Link: succeeded
- Executable format: PE32+ AMD64 (`pei-x86-64`; `i386:x86-64`)
- Executable bytes: 436,657
- Executable SHA-256: `6e1f836c0d6244715026a64889623ab9a33021b830a71f8eb048cd115b931dc5`
- Imported DLLs: `KERNEL32.dll`, `api-ms-win-crt-convert-l1-1-0.dll`,
  `api-ms-win-crt-environment-l1-1-0.dll`, `api-ms-win-crt-heap-l1-1-0.dll`,
  `api-ms-win-crt-locale-l1-1-0.dll`, `api-ms-win-crt-math-l1-1-0.dll`,
  `api-ms-win-crt-private-l1-1-0.dll`, `api-ms-win-crt-runtime-l1-1-0.dll`,
  `api-ms-win-crt-stdio-l1-1-0.dll`, and `api-ms-win-crt-string-l1-1-0.dll`
- `msys-2.0.dll` imported: no
- `nec2c -v`: exit 0
- `nec2c -h`: exit 0
- One minimal-dipole run: exit 0
- Raw report: 6,943 bytes
- Raw report SHA-256: `1a9baf6a9a2954f77ccd543d1739ff97caf6b748a255b00bf149fbb2c3fd671c`
- CRLF sequences: 118; bare CR bytes: 0
- CRLF-to-LF normalized report: 6,825 bytes
- Normalized SHA-256: `396b90cfb8e49fcf1938e01d291638163f74e3b065e29b8456ece3b3ca482567`

Normalizing only CRLF to LF made the complete native report byte-for-byte identical to the MSYS
report.

## Current limitations and next milestone

This result does not establish numerical accuracy, tolerances, reproducible executable bytes,
structured output, release readiness, binary publication, solver installation qualification, or
product integration. It changes no numerical core and does not add `nec2dx` work.

The exact recommended next milestone is the separately authorized `v0.0.5f-B` nec2dx numerical
baseline and comparison corpus. That milestone must validate the pinned maintained candidate
without relabeling this bounded build-and-smoke result as numerical qualification.
