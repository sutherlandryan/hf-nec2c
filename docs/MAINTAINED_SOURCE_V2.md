# Maintained NEC2C source v2

## Status

`HF_NEC2C_MAINTAINED_SOURCE_V2` is the provenance-complete successor to the preserved
`HF_NEC2C_MAINTAINED_SOURCE_V1` candidate. It starts from main commit
`16a22ff6c854a09ef9e580161cc94d8face3f9a3` and adds exactly one authenticated four-line
source-fidelity correction in `calculations.c`. The earlier v1 manifest, combined patch,
documentation, and tag remain preserved. The annotated tag
`maintained/nec2c-1.3.1-hf-portability-v1` still targets
`05f9a4f7ad9a089e45459db9099e47e0bf4533c2`.

The milestone disposition is:

**B. V2 SOURCE FIX VALIDATED; QUALIFICATION REMAINS BLOCKED BY THE FROZEN REFERENCE MISMATCH.**

The source correction, direct tests, reconstruction, fresh builds, cross-platform comparisons,
and complete frozen-corpus rerun passed their declared gates. The sole qualification blocker is
the unresolved official Example 2 feed-current literal described in the
[v0.0.5f-C qualification record](NUMERICAL_QUALIFICATION_V0_0_5F_C.md).

This candidate remains unreleased and unapplied. It is not approved for executable distribution,
a release, a maintained-source v2 tag, or HF Propagation Control integration.

## Exact source correction

The correction changes only `src/nec2c/calculations.c` and only these four logical lines in
`zint()`:

1. Correct `cc5` from `0. - I*9.765e4` to `0. - I*9.765e-4`.
2. Replace `#define cn cc14` with
   `#define cn (0.70710678 + I*0.70710678)`.
3. Add `return;` immediately after the small-regime result assignment.
4. Add `return;` immediately after the medium-regime result assignment.

No other maintained-source byte changed relative to v1. No polynomial, branch condition,
large-regime literal, parser behavior, output formatting, build machinery, or unrelated solver
code was altered. The two returns restore the authenticated branch transfers; the two constant
corrections stop carrying the independently established medium-regime mistranslations.

This scope implements the bounded findings authenticated in
[`ZINT_TRANSLATION_INVESTIGATION.md`](ZINT_TRANSLATION_INVESTIGATION.md) at commit
`2f36e4211632aef6a283416803f0404d1ddb2a5e`. It does not broaden that investigation or pursue
the remaining official feed-current mismatch.

## Construction and reconstruction identity

The deterministic combined patch is
[`nec2c-1.3.1-hf-portability-zint-v2.patch`](../patches/maintained/nec2c-1.3.1-hf-portability-zint-v2.patch).
It is the complete delta from the authenticated original NEC2C 1.3.1 archive to v2, not an
incremental patch that requires v1 first.

- Original archive bytes: 186,124
- Original archive SHA-256: `8c706008bcb11c34bf33a3f8f78711c79f7bb49de8a22d74df6b10e1203c013e`
- Patch bytes: 7,624
- Patch SHA-256: `9b165d93e4e3335f4c2762c70950a7086d1f6c7ee0559a1f3f3f5c08f6219e52`
- Final regular files: 36
- Final total bytes: 788,941
- Per-file identities: [`maintained-source-v2.json`](../manifests/maintained-source-v2.json)

An independent fresh reconstruction reauthenticated and extracted
`archive/nec2c-1.3.1.tar.bz2`, applied only the v2 combined patch, and compared the result with
`src/nec2c/`. All 36 regular files, all 788,941 bytes, and every per-file SHA-256 matched. There
was no missing or extra path, byte normalization, link, or reparse point.

The reconstructed tree modifies four original files: `calculations.c`, `main.c`, `misc.c`, and
`nec2c.h`. It adds the wholly project-authored `platform_signal.h` and `platform_time.h`; the
other 30 original files remain byte-identical to the authenticated extraction. No maintained
NEC2C v1.3.3 or later-contributor source was imported.

## Direct compiled `zint()` validation

The focused harness invokes the actual `zint()` compiled from `src/nec2c/calculations.c`; it does
not copy or reimplement the function. Fresh runs passed under MSYS GCC 15.3.0 and native UCRT64
GCC 16.1.0 for all 12 frozen values:

- small regime: `0.1`, `1.0`, approximately `2.97`, `7.999`, and `8.0`;
- medium regime: `8.001`, `20`, `50`, `109.999`, and `110.0`; and
- large regime: `110.001` and `200`.

The boundaries selected the intended branches: `x = 8` selected small, `x = 110` selected
medium, and `x = 110.001` selected large. Every small- and large-regime component matched the
authenticated reference at exact binary64 precision. Every medium-regime component met the
frozen bound `abs(error) <= 1e-11 + 5e-12 * abs(reference)`.

Mutation guards separately proved that the tests fail if either branch `return` is removed, if
`cc5` reverts to `9.765e4`, or if `cn` is again aliased to `cc14`.

## Fresh maintained builds

Both builds were fresh, out of tree, and used the shipped conservative `configure` and GNU
`make -j1 V=1` route:

```text
CC=/usr/bin/gcc /usr/bin/bash $REPO/src/nec2c/configure
/usr/bin/make -j1 V=1

CC=/ucrt64/bin/gcc /usr/bin/bash $REPO/src/nec2c/configure
/usr/bin/make -j1 V=1
```

| Build | Compiler identity | Executable identity | Architecture and runtime |
|---|---|---|---|
| MSYS POSIX | GCC 15.3.0, `x86_64-pc-cygwin`; compiler SHA-256 `4bd76635b6053a7926f4579a30f9c800a673632fd10b4d6adf8083d3eda1b80c` | 335,509 bytes; SHA-256 `ef0dac79e1416a066f7e7ccb1416ddc8124a85beae205b89af319e3fe6877adc` | PE32+ x86-64; `msys-2.0.dll`, `msys-gcc_s-seh-1.dll`, and `KERNEL32.dll` |
| Native UCRT64 | GCC 16.1.0, `x86_64-w64-mingw32`; compiler SHA-256 `f96a3bdb1d3a3967b309d75c7413399391e857b5be4cb17162572ed66f6772a0` | 439,729 bytes; SHA-256 `c96228b4aa301408f5b47647fe5951f951dc42da2256787cf1ae2af2645e97fc` | PE32+ x86-64; `KERNEL32.dll` and Universal CRT API-set imports; no `msys-2.0.dll` |

Neither executable was published or tracked. These identities authenticate the binaries used for
the direct tests and the frozen-corpus rerun; they do not authorize distribution.

## Provenance and license scope

Original NEC2C material remains handled under the original-author public-domain statement
preserved in `src/nec2c/README` and `upstream/nec2c-1.3.1/README`. Original notices and
disclaimers remain in the maintained files. BSD-2-Clause applies only to the exactly identified
project-authored additions and modifications. In v2, `calculations.c` is additionally modified by
this project, but its retained original material is not relabeled as BSD-2-Clause.

This repository and maintained source are independent and are not official NEC2C or endorsed by
Neoklis Kyriazis. No blanket BSD claim is made over an original file, the original source tree,
or the preserved distribution.

## Current limitation and next milestone

The complete v0.0.5f-C rerun leaves one frozen authoritative-reference mismatch: the official
Example 2 feed-current imaginary component is `-3.86680E-03 A`, while both v2 primary builds and
internal NEC2DX report approximately `-3.8666E-03 A`. The cause remains unresolved. This record
does not call the official literal a publication error, waive it, replace it, or begin a new
investigation.

The exact recommended next milestone is independent review and merge of this v2
source-fix/requalification pull request. Do not create or move a maintained-source v2 tag before
merge. Release and HF Propagation Control integration remain deferred pending resolution of the
frozen reference mismatch.
