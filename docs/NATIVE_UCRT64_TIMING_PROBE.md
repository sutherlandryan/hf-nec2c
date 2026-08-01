# Native UCRT64 process-timing probe

## Task class and exact question

**RECONNAISSANCE.** Does one temporary, project-authored portable process-timing boundary:

1. preserve all non-timing NEC2C output under the working MSYS POSIX baseline; and
2. allow the native UCRT64 build to advance beyond the proven `sys/times.h` blocker?

Starting `main` was `feef03a61310cacf723e7cade8dc71ed15f92de0`, the accepted regular
two-parent merge of reviewed PR #4. The existing branch
`agent/nec2c-native-timing-probe` started at the same commit with no additional commit.

## Rejected provisional work

An earlier provisional timing patch was rejected because it deleted an unrelated terminal blank
line from both `nec2c.h` and `misc.c`. Its draft repository files and temporary patch/build trees
were removed before this correction. No provisional patched-build result is treated as evidence
in this report.

The untouched MSYS baseline from the same authenticated run remained valid and was copied only
after rechecking its exact identity:

- report bytes: 6,825
- report SHA-256: `396b90cfb8e49fcf1938e01d291638163f74e3b065e29b8456ece3b3ca482567`

No replacement untouched baseline build was needed.

## Corrected patch generation and EOF preservation

The corrected candidate began with a fresh extraction created and verified by the existing
source guard. The extracted NEC2C source directory was the exact top level of a disposable nested
Git repository with `core.autocrlf=false` and `core.eol=lf`. Its authenticated 34-file baseline
was committed before editing.

Before editing, the original existing-file identities were:

| Path | Original bytes | Original SHA-256 |
|---|---:|---|
| `nec2c.h` | 14,635 | `7fd91d6d5bceccd9d63e5f7fa54636d497023849b0d2fbfe5ceaeee4edd3b286` |
| `misc.c` | 4,796 | `a866a253acfe0daffa76170138bf24bf2019499c5ce7711e03a989eaa9a86e52` |

Both original files ended with LF, contained exactly two terminal LF bytes, and therefore
retained one additional terminal blank line. Their final 128 raw bytes were recorded before
editing.

The corrected staged diff contained exactly:

```text
M misc.c
M nec2c.h
A platform_time.h
```

Its complete hunk inventory was limited to the shared include removal, the `misc.c` include and
`secnds()` implementation, and the new header. No EOF hunk, whitespace-only hunk, unrelated blank
line change, or unexpected no-newline marker occurred.

The deterministic corrected patch is
[`../probes/portable-process-timing-v1.patch`](../probes/portable-process-timing-v1.patch), with
SHA-256:

```text
f65347275a21bbdc90b009aec4fb9db10a2918ac33a77be30809fb1db57b8aae
```

The exact corrected patched-file identities are:

| Path | Patched bytes | Patched SHA-256 |
|---|---:|---|
| `nec2c.h` | 14,612 | `233f36230455675e8ca7db49bdbaececc067dec3bf13e11e0c7859acf32ff003` |
| `misc.c` | 5,485 | `9033e9635c5ec7d22d9cbc6c46588e5b49987cc88b9a02607e3d347837760403` |
| `platform_time.h` | 599 | `2b2af7ef1309d60f018d383a9f1d5f9a721b68478ab0a8ea37581e70ad9522db` |

For both existing files, the corrected candidate, independently applied MSYS tree, and
independently applied UCRT64 tree retained exactly two terminal LF bytes and a byte-identical
final 128-byte suffix. The disposable nested `.git` directory was removed before each build, and
the three patched-file hashes still matched afterward.

## Timing-boundary scope

The patch is project-authored, BSD-2-Clause, and a reconnaissance candidate. It is not maintained
source, is not qualified, and is not approved for distribution.

It makes only these process-timing changes:

- removes the unconditional `sys/times.h` include from shared `nec2c.h`;
- adds `platform_time.h` as the single timing-platform selection boundary; and
- keeps the `secnds(double *x)` API while selecting its implementation in `misc.c`.

For MSYS and Cygwin, the original POSIX block remains byte-identical: `struct tms`, `times()`,
`sysconf(_SC_CLK_TCK)`, user plus system process CPU time, and milliseconds. For native Windows,
`GetProcessTimes()` supplies kernel plus user process CPU time in 100-nanosecond units, converted
to milliseconds. Failure returns the bounded value `0.0`. No wall-clock API is used.

The patch adds no signal, CLI, filesystem, exit-code, input, output-format, numerical, geometry,
matrix, field, radiation, or ground change. It contains no absolute path and no maintained NEC2C
1.3.3 code.

## Corrected patched MSYS result

The corrected patch was independently checked and applied to a separate fresh authenticated
extraction, then built with `MSYSTEM=MSYS`, `/usr/bin/gcc`, the shipped `configure`, and
`/usr/bin/make -j1`.

- `configure`: exit `0`
- `make -j1`: exit `0`
- executable: 332,949 ignored temporary bytes
- `nec2c -v`: exit `0`
- `nec2c -h`: exit `0`
- one minimal-dipole smoke run: exit `0`
- report lines: 119
- report bytes: 6,825
- report SHA-256: `396b90cfb8e49fcf1938e01d291638163f74e3b065e29b8456ece3b3ca482567`

The two timing-value locations were derived from the original reporting source. Report line 73
was `FILL: 0 msec  FACTOR: 0 msec` in both reports. Report line 119 was
`TOTAL RUN TIME: 0 msec` in both reports. There were zero timing-line differences.

All 117 non-timing lines were byte-identical, with no first non-timing difference. Line ordering,
line count, report structure, full byte count, and full SHA-256 were identical to the accepted
untouched MSYS baseline. This bounded comparison is not numerical qualification.

## Corrected patched UCRT64 result

Only after the corrected MSYS comparison passed, the same corrected patch was independently
checked and applied to another fresh authenticated extraction. It was built with
`MSYSTEM=UCRT64`, `/ucrt64/bin/gcc`, the shipped `configure`, and `/usr/bin/make -j1`.

- `configure`: exit `0`
- `make -j1`: exit `2`
- first new proven blocker: original `main.c:84`
- missing interface: complete `struct sigaction` type
- first diagnostic: storage size of `sa_new` is unknown
- object files produced before the blocker: 8
- linking reached: no
- executable produced: no

The eight objects were `calculations.o`, `fields.o`, `geometry.o`, `ground.o`, `input.o`,
`matrix.o`, `network.o`, and `shared.o`.

This proves that the corrected timing patch advances native UCRT64 compilation beyond the former
`sys/times.h` blocker to the absent POSIX `sigaction` interface. The task stopped at this first
new source/compiler blocker. No signal portability code was added.

## Preservation and scope result

Before and after each corrected build, the archive remained 186,124 bytes with SHA-256
`8c706008bcb11c34bf33a3f8f78711c79f7bb49de8a22d74df6b10e1203c013e`. The preservation
verifier passed, all 34 preserved files remained present with no extra preserved-tree file, and
no preserved source byte changed. Both corrected patched build trees retained their verified
35-file state and exact EOF suffixes across compilation.

The authorization performed one corrected candidate generation, one patched-MSYS
configure/build/smoke run, and one patched-UCRT64 configure/build run. No replacement baseline
build or pre-build correction was used. No package command, package inventory, full test suite,
Ruff run, maintained source tree, build driver, JSON manifest, binary publication, release
engineering, signal patch, or numerical qualification was performed. HF Propagation Control
remained clean and read-only.

## Result and exact next decision

**YES.** One project-authored process-timing boundary preserved every non-timing line in the
bounded MSYS report and advanced UCRT64 beyond `sys/times.h`. The first new proven native blocker
is the unavailable complete `struct sigaction` type at original `main.c:84`.

The exact next decision is whether to authorize a separate **RECONNAISSANCE** task for one narrow
signal-registration portability boundary. That work must define and test signal semantics and
stop at its first subsequent blocker. It must not expand into CLI, filesystem, exit-code,
numerical, distribution, reproducibility, or qualification work.
