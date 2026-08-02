# NEC2DX `SECOND` compatibility probe

## Result

Task class: **reconnaissance**.

Exact question: Does declaring NEC2DX's existing custom `SECOND` subroutine as external in every
calling program unit allow the exact authenticated NEC2DX source to compile, link, and process one
simple deck under native UCRT64 GNU Fortran?

**Answer: yes.** The disposition is:

> **INTERNAL NEC2DX COMPATIBILITY BUILD AND SMOKE SUCCEEDED**

The declaration-only compatibility experiment allowed GNU Fortran 16.1.0 to compile and link the
authenticated source, and the resulting native x86-64 executable completed the bounded free-space
dipole smoke with exit code `0`.

This result does not authorize redistribution or numerical use. NEC2DX remains internal-use only,
public intake remains blocked, and it remains a secondary cross-check rather than the primary
numerical oracle. No numeric comparison, corpus, tolerance, numerical qualification, or integration
work occurred. No maintained NEC2C source changed.

## Starting gate and artifact identity

The probe began from clean `main` at merge commit
`09fa1fabe1a1cbc14b89625cc31ea8f61ec028d0`, identical to `origin/main`. That commit merged PR
number 10 and contains the reviewed untouched-build-probe commit
`868cebe2a822cd14de319a6a32046a8ea12027e5`. Work occurred on
`agent/nec2dx-second-compatibility-probe`.

The acquired artifact was the same [FUNET `nec2dx.tar`](https://www.nic.funet.fi/pub/ham/antenna/NEC/nec2dx.tar)
used by the earlier oracle decision and untouched build probe:

| Evidence | Identity |
|---|---|
| Archive bytes | `262,656` |
| Archive SHA-256 | `ad20c15a8cb594b19928595c853eca2b576c875c45c39a45eeaf26ee1be79774` |
| Authenticated `nec2dx.f` bytes | `257,436` |
| Authenticated `nec2dx.f` SHA-256 | `ca2ffebef9fb928d17e1eedcaa6f87b7bd61125a5f1abe19227d3f8251d9b293` |

The archive, extracted source, edited source, executable, reports, and supporting records stayed in
ignored internal research storage throughout the experiment.

## Calling-program-unit analysis

The eight calls occur in two program units:

| Program unit | Calls | Specification section and declaration analysis |
|---|---:|---|
| Unnamed main program | 6 | Its specification section contains the include, parameter, implicit-typing, type, common-block, dimension, equivalence, and data statements before the first executable statement. The external-procedure declaration belongs immediately after the implicit-typing statement. |
| `FACIO` subroutine | 2 | Its specification section contains the implicit-typing, complex-type, common-block, and dimension statements before the first executable assignment. The external-procedure declaration belongs immediately after the implicit-typing statement. |

Neither calling unit originally declared `SECOND` intrinsic or external. Both use
`IMPLICIT REAL*8(A-H,O-Z)`. Although that rule gives otherwise implicit names beginning with `S` a
double-precision type, it does not conflict with designating a subroutine name as an external
procedure. The declaration prevents GNU Fortran from resolving these calls to its kind-4
`SECOND` intrinsic.

## Internal compatibility edit

The exact edit classification is **ignored, internal-only, declaration-only source compatibility**.
One external-procedure declaration for `SECOND` was added to each of the two calling program
units. Nothing was added to any other unit. The custom timing routine, timing-variable types,
numerical statements, headers, notices, fixed-form layout, and LF line endings were unchanged.

The edited file was 44 bytes larger: exactly two 22-byte LF-terminated declaration lines. Removing
those two lines reproduced the authenticated source SHA-256 exactly. All eight call lines and the
complete custom `REAL*8` timing routine remained byte-identical to the authenticated source. The
edited source and any patch representation remain untracked and are not redistributed.

## Native compilation and executable identity

The process-local environment set `PARALLEL=1` and `OMP_NUM_THREADS=1`. The exact command was:

```text
gfortran -O0 -std=legacy -ffixed-line-length-none -o nec2dx.exe nec2dx.f
```

GNU Fortran `(Rev5, Built by MSYS2 project) 16.1.0`, targeting `x86_64-w64-mingw32`, completed the
single authorized compilation and implicit link with exit code `0`. It emitted warnings for the
legacy Hollerith format feature, no compile or link error, and left no standalone object file.

| Executable evidence | Identity |
|---|---|
| PE format and architecture | `pei-x86-64`; `i386:x86-64` |
| Bytes | `587,405` |
| SHA-256 | `044b47f5ac693bf92fb70b723db07f226cea30ff7950b61039f4827d38f15933` |

The imported DLLs were:

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

`msys-2.0.dll` was absent. The executable requires the UCRT64 GCC and GNU Fortran runtime DLLs and
is not a self-contained redistributable artifact.

## Bounded smoke result

The one smoke case was the project-authored [`tests/smoke/minimal-dipole.nec`](../tests/smoke/minimal-dipole.nec)
free-space straight-wire dipole deck, copied unchanged into ignored storage:

| Smoke evidence | Identity |
|---|---|
| Input bytes | `196` |
| Input SHA-256 | `395603f62e0e0682215d9985443e4e13ff73f583646427b8dc9785ca76571520` |
| Process exit code | `0` |
| Report bytes | `7,155` |
| Report SHA-256 | `3edc35f32509f952b037eada2e173846cf3effe5cb0321c9c6ca9bc9a38cc352` |

NEC2DX received the input and output filenames through standard input. Standard output contained
only the two interactive filename prompts; standard error was empty. The initial bounded Windows
process wrapper completed and produced the report but did not expose its exit-code property, so a
direct exit-code capture replay used the same deck. It returned `0`, and the two reports were
byte-identical. This replay established process completion only; it was not a numerical comparison
or qualification exercise.

The report contained structure specification and geometry, unloaded-structure status, excitation,
feed current and impedance, segment currents, the power budget, a radiation-pattern section, the
ending data card, and final run time. The free-space case neither supplied nor required
`SOM2D.NEC`.

## Source-use boundary

- NEC2DX remains an internal-only, secondary cross-check and is publicly non-redistributable under
  the current rights disposition.
- The archive, source, edited source, source fragments, compatibility patch, executable, objects,
  reports, runtime DLLs, and package archives are not tracked or published.
- The two declarations were an ignored compatibility experiment, not a maintained NEC2C change or
  a redistributable third-party patch.
- No value was compared with NEC2C. No corpus, parser, tolerance, numerical qualification, release,
  or HF Propagation Control integration resulted.

## Exact next decision

Do not begin numerical comparison work. The exact next bounded job is to authorize or decline one
internal-only reproducibility probe: start from another freshly authenticated ignored source copy,
apply the same declaration-only recipe, rebuild with the pinned UCRT64 compiler and environment,
and test executable and same-deck report identity. That job must remain non-redistributable, must
not compare values with NEC2C, and must stop after recording reproducibility or the first blocker.
