# NEC2DX reproducibility probe

## Result

Task class: **reconnaissance**.

Exact question: From two separately authenticated and freshly extracted internal NEC2DX source
copies, does the documented declaration-only compatibility recipe produce repeatable native
UCRT64 builds and repeatable output for the same minimal dipole deck?

**Answer: yes at the source-recipe, compilation, executable-structure, raw-report, and parsed
physical-output levels.** The two executables were not byte-identical, but a bounded comparison
found only their two-second PE timestamps and corresponding PE checksums differed. The disposition
is:

> **A. NEC2DX INTERNAL RECIPE AND PHYSICAL OUTPUT REPRODUCIBLE**

This was an intra-NEC2DX build-plumbing check only. It was not numerical qualification, a
comparison against NEC2C, corpus generation, tolerance setting, primary-oracle selection, public
source intake, release work, or product integration. NEC2DX remains an internal-only,
non-redistributable, numerically unqualified secondary cross-check.

## Starting gate and boundaries

The probe began from clean `main` at `d50f505098dbff8ba50beee652d117a439baa050`, identical to a
freshly fetched `origin/main`. That commit merged PR number 11 and contains the reviewed
compatibility commit `77186178b8f0eade4be90472ab642a3f8b7f2e69`. Work occurred on
`agent/nec2dx-reproducibility-probe`.

The offline preservation verifier passed before the experiment. The maintained-source tag
`maintained/nec2c-1.3.1-hf-portability-v1` still resolved to
`05f9a4f7ad9a089e45459db9099e47e0bf4533c2`. The separate HF Propagation Control checkout was clean
on `main` at `ac231157b218415598f9d8a389492bef11d0a5a6` and remained read-only.

The archive, extracted and edited source, executables, reports, logs, and supporting records stayed
in ignored `.build-temp/nec2dx-reproducibility-probe/` storage. The two work roots shared no source,
object, executable, or output file. No third-party artifact or compatibility patch was tracked.

## Artifact authentication and two-work-root method

The probe acquired the same FUNET `nec2dx.tar` artifact once, authenticated it before extraction,
and made two separately verified fresh extractions into `run-a/` and `run-b/`.

| Evidence | Identity |
|---|---|
| Archive bytes | `262,656` |
| Archive SHA-256 | `ad20c15a8cb594b19928595c853eca2b576c875c45c39a45eeaf26ee1be79774` |
| Regular files | `4` |
| Total regular-file bytes | `258,373` |
| Unsafe paths, links, special objects, duplicates, case collisions | `0` for each category |
| Authenticated `nec2dx.f` bytes | `257,436` |
| Authenticated `nec2dx.f` SHA-256 | `ca2ffebef9fb928d17e1eedcaa6f87b7bd61125a5f1abe19227d3f8251d9b293` |

Every extracted file in each root matched its corresponding archive member by size and SHA-256.
The project-authored smoke deck was separately copied into each work root and matched the required
identity: `196` bytes and SHA-256
`395603f62e0e0682215d9985443e4e13ff73f583646427b8dc9785ca76571520`.

## Compatibility-recipe verification

The documented declaration-only recipe was applied independently in each fresh copy: one external
declaration for the existing custom `SECOND` procedure in the unnamed main program and one in
`FACIO`. Each declaration was one 22-byte LF-terminated line, for a total addition of 44 bytes per
source copy. No line ending was normalized.

Both edited sources were `257,480` bytes with SHA-256
`bf894ae10325ff8534a45960e901f1a88d98485ce5f97569cea137f125d0e15c`. Removing only the two
declarations from either edited copy restored the authenticated source byte-for-byte. This proves
that the custom `REAL*8 SECOND` routine, its eight calls, timing types, numerical code, and every
other source byte were unchanged. The other three extracted files also remained byte-identical to
their authenticated archive members in both roots.

## Toolchain and environment

No package transaction or global environment change occurred. The installed packages remained:

- `mingw-w64-ucrt-x86_64-gcc-libgfortran 16.1.0-5`
- `mingw-w64-ucrt-x86_64-gcc-fortran 16.1.0-5`

Both builds used one process-local environment that prepended `C:\msys64\ucrt64\bin` to `PATH`,
set `PARALLEL=1` and `OMP_NUM_THREADS=1`, retained culture `en-US`, and retained Windows timezone
`US Mountain Standard Time` (`UTC-07:00`, Arizona).

| Component | Bytes | SHA-256 / identity |
|---|---:|---|
| GNU Fortran 16.1.0, `x86_64-w64-mingw32` | `3,309,309` | `f1f086d81f4c6701281df5543ca232cd741857f7c4611c43904d0e88e58718ce` |
| GNU ld 2.47.20260726 | `1,933,847` | `fb152d34cf00bf66fc57a66522806a4e64914654d8c1ab8cdd0a1d78283ec215` |
| `libgcc_s_seh-1.dll` | `153,412` | `ff139cfe956709283f7b70a06af8bc8bb9d1c3bef60ec1bc8d363c91351cfeb2` |
| `libgfortran-5.dll` | `3,795,660` | `2cbb28fd66914d68ad52520fc27b4549cd5ae031d678cc543c6d26b406537ac0` |
| `libquadmath-0.dll` | `417,775` | `9508edce590f1d78f9364e832f50ed933bfd2b442f5fe1a6e7c42aaee13adc71` |
| `libwinpthread-1.dll` | `64,703` | `4bd23b274a3a96ff8114d0069e69177fd0c88911a987f530fabc12a2cc5b5ecc` |

The complete effective compile command in each isolated source directory was:

```text
gfortran -O0 -std=legacy -ffixed-line-length-none -o nec2dx.exe nec2dx.f
```

## Build and executable findings

Each command was run exactly once. Both exited `0`, wrote no standard output, emitted identical
legacy-warning streams, and produced no standalone object file.

| Evidence | `run-a` | `run-b` |
|---|---:|---:|
| Executable bytes | `587,405` | `587,405` |
| Executable SHA-256 | `84451e7d844b3eeb54524360e86d624d9f28f97d023b37017c3823160963d5e6` | `919cd31e77ad1bff77a9bca325cccfb9f75b8a16de6338a28bdeed7b98d96da3` |
| PE format | `pei-x86-64` | `pei-x86-64` |
| Architecture | `i386:x86-64` | `i386:x86-64` |

Both executables imported the same DLL set:

- `libgcc_s_seh-1.dll`
- `libgfortran-5.dll`
- `KERNEL32.dll`
- `api-ms-win-crt-environment-l1-1-0.dll`
- `api-ms-win-crt-heap-l1-1-0.dll`
- `api-ms-win-crt-locale-l1-1-0.dll`
- `api-ms-win-crt-math-l1-1-0.dll`
- `api-ms-win-crt-private-l1-1-0.dll`
- `api-ms-win-crt-runtime-l1-1-0.dll`
- `api-ms-win-crt-stdio-l1-1-0.dll`
- `api-ms-win-crt-string-l1-1-0.dll`

Neither executable imported `msys-2.0.dll`.

The bounded binary comparison found exactly two differing bytes in two one-byte ranges:

| PE field | Offset | `run-a` | `run-b` | Finding |
|---|---:|---:|---:|---|
| COFF timestamp | `0x88` | `1785669400` | `1785669402` | Two-second build-time difference |
| Optional-header checksum | `0xd8` | `0x0009a478` | `0x0009a47a` | Corresponding PE checksum difference |

Every other executable byte was identical. The difference is limited to identified non-code PE
metadata; there was no path, debug record, section-content, import, architecture, image-size, or
other structural variation. No third build, disassembly, linker-flag change, or reproducibility
flag was used.

## Smoke-report and physical-output findings

Each executable was run once, through the required interactive filename input, against its own
copy of the exact same deck. The separate output names were `run-a-report.out` and
`run-b-report.out`. Both completed within the 30-second bound, produced the final report
end and run-time line, wrote the same 55-byte prompt stream to standard output, and wrote empty
standard error. The Windows process wrapper did not expose either completed process's numeric exit
code. Because source processing and report generation had already occurred, the no-retry ceiling
prohibited a replay; the two numeric smoke exit codes are therefore **not captured**, not inferred.

| Report evidence | `run-a` | `run-b` |
|---|---:|---:|
| Bytes | `7,155` | `7,155` |
| SHA-256 | `3edc35f32509f952b037eada2e173846cf3effe5cb0321c9c6ca9bc9a38cc352` | `3edc35f32509f952b037eada2e173846cf3effe5cb0321c9c6ca9bc9a38cc352` |
| CRLF sequences | `161` | `161` |
| Lone LF / lone CR | `0` / `0` | `0` / `0` |

The complete raw reports were byte-identical. Both contained structure specification, antenna
input, segment-current, power-budget, radiation-pattern, ending-card, and run-time sections.
`SOM2D.NEC` was absent from the archive and both work roots, was not named in either report, and was
not required by this free-space deck.

The bounded parser extracted only the physical values already present in each report. The parsed
structures were identical, including:

- feed impedance: `6.72756E+01 - j3.59579E+01` ohms;
- all `11` segment-current rows;
- input and radiated power: `5.7807E-03` watts each;
- structure and network loss: `0.0000E+00` watts each;
- efficiency: `100.00` percent; and
- the one requested radiation-pattern row, including angles, gains, polarization, and field
  magnitudes and phases.

## Reproducibility classification

| Classification | Finding |
|---|---|
| 1. Source-recipe reproducibility | **Yes**; edited source identities matched and declaration removal restored the authenticated source |
| 2. Compilation success reproducibility | **Yes**; both single builds exited `0` |
| 3. Executable byte reproducibility | **No**; two identified PE metadata bytes differed |
| 4. Executable structural reproducibility | **Yes**; all non-metadata bytes, size, architecture, and imports matched |
| 5. Raw report byte reproducibility | **Yes**; complete report bytes and hashes matched |
| 6. Parsed physical-output reproducibility | **Yes**; every extracted physical value matched |

The uncaptured smoke exit-code properties limit that process-status evidence but do not alter the
observed source, compiler-exit, executable, completed-report, raw-byte, or parsed-value identities.
This disposition does not establish numerical accuracy or authorize any use beyond the existing
internal secondary-cross-check boundary.

## Exact next milestone

Do not begin it in this task. The exact next milestone remains the separately authorized
`v0.0.5f-B` NEC2DX numerical baseline and comparison corpus described by the maintained-source
roadmap. That milestone must define and validate semantic deck equivalence, parsed observables,
independent deciding evidence, and tolerances without treating NEC2DX as the primary oracle or
relabeling this reproducibility result as numerical qualification.
