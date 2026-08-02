# NEC2DX internal native build probe

## Result

Task class: **reconnaissance**.

Exact question: Can the exact authenticated internal-use `nec2dx.tar` artifact be compiled
untouched into a native UCRT64 executable and successfully process one simple compatible NEC
deck?

**Answer: no. The untouched native UCRT64 build is blocked at compilation.** GNU Fortran
16.1.0 reaches the source but rejects eight calls to `SECOND`: each actual timing argument is
double precision (kind 8), while the compiler resolves `SECOND` as its intrinsic and requires a
kind-4 `time` argument. The source later defines a custom `SUBROUTINE SECOND` with a `REAL*8`
dummy argument, but its call sites do not declare that external procedure.

The disposition is:

> **B. INTERNAL NEC2DX BUILD BLOCKED**

No object or executable was produced, the linker was not invoked, and the smoke deck was not
run. This is only a source/compiler-interface result. NEC2DX remains an internal secondary
cross-check, public intake remains blocked, and it remains numerically unqualified.

## Governing boundary

The governing disposition remains **INTERNAL ORACLE USE AUTHORIZED; PUBLIC INTAKE BLOCKED**.
NEC2DX is a secondary cross-check, not the primary numerical oracle. The archive, extracted
source, source fragments, executable and generated outputs remain ignored internal material and
are not redistributed by this repository.

This probe did not modify or normalize third-party source, add compatibility source, copy code
from another NEC implementation, build maintained NEC2C, perform a numeric comparison, define a
corpus or tolerance, qualify either implementation, or integrate anything with HF Propagation
Control.

## Starting gate

The probe began from clean `main` at merge commit
`f1cb0f91c00a19522705d41becbdbe28aed71aa9`, identical to the local `origin/main` ref. The
reviewed NEC2DX oracle-decision commit
`cfff0ec3088776bd911b9f473ac5bb79390172f5` is an ancestor. The maintained-source tag
`maintained/nec2c-1.3.1-hf-portability-v1` resolved to
`05f9a4f7ad9a089e45459db9099e47e0bf4533c2`.

The offline preservation verifier passed before acquisition. The separate HF Propagation
Control checkout was clean on `main` at
`ac231157b218415598f9d8a389492bef11d0a5a6` and remained read-only.

## Artifact authentication and safety

The one acquired artifact was the exact
[FUNET `nec2dx.tar`](https://www.nic.funet.fi/pub/ham/antenna/NEC/nec2dx.tar):

| Evidence | Recorded identity |
|---|---|
| Byte count | `262,656` |
| SHA-256 | `ad20c15a8cb594b19928595c853eca2b576c875c45c39a45eeaf26ee1be79774` |
| Regular files | `4` |
| Directories | `0` |
| Links | `0` |
| Special objects | `0` |
| Traversal or absolute paths | `0` |
| Duplicate or case-colliding names | `0` |
| Extracted regular-file bytes | `258,373` |

The four extracted files matched their tar-member bytes exactly. The archive and extracted files
remained under ignored `.build-temp/nec2dx-build/` storage.

## Additions-only package transaction

The installed-state query was performed without synchronizing package databases. Neither target
package was present. The no-install preview proposed exactly these two additions and no upgrade,
downgrade, replacement, removal, reinstall or unrelated package:

| Newly installed package | Version |
|---|---|
| `mingw-w64-ucrt-x86_64-gcc-libgfortran` | `16.1.0-5` |
| `mingw-w64-ucrt-x86_64-gcc-fortran` | `16.1.0-5` |

The exact installation command was:

```text
C:\msys64\usr\bin\pacman.exe --noconfirm --needed -S mingw-w64-ucrt-x86_64-gcc-fortran
```

No `pacman -Sy`, `pacman -Syu`, `pacman -Su`, update, removal or complete package inventory was
run.

## Compiler, runtime and linker identity

| Component | Recorded identity |
|---|---|
| Compiler | `GNU Fortran (Rev5, Built by MSYS2 project) 16.1.0` |
| Target | `x86_64-w64-mingw32` |
| Resolved compiler | `/ucrt64/bin/gfortran.exe` |
| Compiler byte count | `3,309,309` |
| Compiler SHA-256 | `f1f086d81f4c6701281df5543ca232cd741857f7c4611c43904d0e88e58718ce` |
| Newly installed runtime DLL | `/ucrt64/bin/libgfortran-5.dll`; `3,795,660` bytes |
| Runtime DLL SHA-256 | `2cbb28fd66914d68ad52520fc27b4549cd5ae031d678cc543c6d26b406537ac0` |
| Linker | `GNU ld (GNU Binutils) 2.47.20260726`; `/ucrt64/bin/ld.exe` |
| Linker SHA-256 | `fb152d34cf00bf66fc57a66522806a4e64914654d8c1ab8cdd0a1d78283ec215` |

No output-specific runtime dependency list exists because compilation produced no executable.

## Untouched compilation attempts

Both invocations set `PARALLEL=1` and `OMP_NUM_THREADS=1`. The initial command was executed from
the directory containing the exact extracted files:

```text
C:\msys64\ucrt64\bin\gfortran.exe -O0 -std=legacy -ffixed-line-length-none -o nec2dx.exe nec2dx.f
```

It exited `1` before reading source because the calling process had not placed
`C:\msys64\ucrt64\bin` on its process-local `PATH`. Direct inspection confirmed that
`f951.exe` existed but exited `-1073741515` (`STATUS_DLL_NOT_FOUND`). No global environment was
changed.

That compiler-invocation failure authorized the one corrected replay. The replay prepended only
`C:\msys64\ucrt64\bin` to the process-local `PATH` and used the identical command and flags. It
reached the source, emitted legacy `H`-format warnings, and exited `1` at the first genuine
blocker:

```text
nec2dx.f:127:18:

  127 |       CALL SECOND(EXTIM)
      |                  1
Error: 'time' argument of 'second' intrinsic at (1) must be of kind 4
```

The same diagnostic occurred at source lines 239, 659, 662, 673, 677, 3524 and 3526. The main
program's `IMPLICIT REAL*8(A-H,O-Z)` makes those timing variables kind 8; the source's custom
routine at line 8151 also declares `REAL*8 CPUSECD`. No compatibility flag was added after the
permitted replay, and no source was changed. The four extracted-file hashes remained identical
to the authenticated archive members after both invocations.

Compilation therefore failed, linking did not begin, and no executable architecture, size, hash,
imports or embedded-path inspection exists.

## Smoke-deck result

No smoke deck was copied or executed because the build had already reached the required stop
condition. There was no process exit code, stdout/stderr stream, output report, report hash,
report section result or `SOM2D.NEC` runtime requirement to record. No numeric comparison against
maintained NEC2C occurred.

## Exact next decision

Do not begin a smoke corpus or numerical comparison. A separate decision is required to authorize
or decline an internal-only compatibility analysis of GNU Fortran's resolution of the legacy
custom `SECOND` routine. Any later compiler experiment or source-portability change must be a new,
explicitly bounded job and must preserve the public-intake block and secondary-cross-check-only
role.
