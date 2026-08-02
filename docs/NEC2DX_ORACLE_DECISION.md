# NEC2DX numerical-oracle decision

## Task and answer

Task class: **decision + reconnaissance**.

Exact question: Is the historical `nec2dx.tar` double-precision Fortran implementation a
suitable, legally and technically supportable independent numerical oracle for qualifying
`HF_NEC2C_MAINTAINED_SOURCE_V1`?

**Answer: no, not as the primary independent numerical oracle.** The acquired source is a useful
internal, secondary cross-check because it is double precision and can be compiled through a
different language toolchain and runtime. It is not independent enough to decide correctness:
maintained NEC2C is a hand translation of NEC2 Fortran, and `nec2dx` and NEC2C share the same
distinctive non-transposed-matrix `FACTR`/`SOLVE` design. A matching result could therefore repeat
a shared lineage defect. No numerical comparison or qualification occurred in this task.

The source-use disposition is **B. INTERNAL ORACLE USE AUTHORIZED; PUBLIC INTAKE BLOCKED**. The
FUNET archive intentionally offers the source with compilation directions, which supports bounded
internal build and execution. The archive contains no express license or redistribution grant for
the `nec2dx` modifications, and one incorporated timing routine says copyright 1990 and 1992, The
Regents of the University of California, all rights reserved. The archive and extracted source
must therefore remain untracked research material unless the relevant rights holders clarify the
redistribution terms. This is a conservative project disposition, not legal advice.

## Source artifact identity

| Field | Recorded value |
| --- | --- |
| Archive index | [FUNET unofficial NEC archives](https://www.nic.funet.fi/pub/ham/antenna/NEC/swindex.html) |
| Named artifact | `nec2dx.tar` |
| Requested and resolved URL | <https://www.nic.funet.fi/pub/ham/antenna/NEC/nec2dx.tar> |
| Retrieval started | `2026-08-02T08:40:39.3018260Z` |
| Retrieval completed | `2026-08-02T08:40:40.9007718Z` |
| HTTP status | `200 OK` |
| Content type | `application/x-tar` |
| Content length and local bytes | `262656` |
| Last-Modified | `Thu, 22 Mar 2001 21:17:00 GMT` |
| ETag | `"40200-3801f0f598b00"` |
| SHA-256 | `ad20c15a8cb594b19928595c853eca2b576c875c45c39a45eeaf26ee1be79774` |

The GET wrote directly to ignored `.intake-temp/nec2dx-oracle/nec2dx.tar`. A bodyless HEAD request
immediately afterward exposed the HTTP metadata above and showed no redirect. The archive remains
ignored and is not part of this repository's preservation set.

## Archive safety and inventory

The member list was inspected before extraction. It contains no absolute path, traversal, link,
special object, duplicate path, or case-colliding path. Extraction was allowed only after those
checks passed and used ignored `.intake-temp/nec2dx-oracle/extracted/` without normalizing or
editing any member.

| Measure | Value |
| --- | ---: |
| Members | 4 |
| Regular files | 4 |
| Directories | 0 |
| Total regular-file bytes | 258373 |
| Links or special objects | 0 |

There is no enclosing directory. The exact top-level layout is:

| File | Bytes | SHA-256 | Role |
| --- | ---: | --- | --- |
| `nec2dx.f` | 257436 | `ca2ffebef9fb928d17e1eedcaa6f87b7bd61125a5f1abe19227d3f8251d9b293` | NEC-2D Fortran source |
| `nec2dx.txt` | 282 | `d940413b4b25bdf6d43359b401ecf6bc41be2f4b6085952470db0fb5f2d3e07d` | matrix-change note |
| `NEC2DPAR.INC` | 43 | `2f54019d7fb2cb396123672726b76cf136578fa92f2efa70e3f41161cfc1e80c` | 1500-segment/matrix limits |
| `compilation_d.txt` | 612 | `3c9e09c0a78fe951713cd101137c5eda1a1a6324f7fbd15c2eb50ab0212503ab` | Sun Fortran build notes |

The archive contains no example deck, SOMNEC generator, `SOM2D.NEC` grid, license file, or
executable.

## Provenance

The archive index was updated on March 25, 2002. Its `nec2dx` entry, dated March 22, 2001, names
Ray Anderson, WB6TPU, as contributor and claims:

- Fortran 77 double-precision NEC2 source;
- modified `FACTR` and `SOLVE` routines for non-transposed matrices;
- source and simple compilation directions in `nec2dx.tar`;
- a separately offered Solaris executable built for 1500 segments with multithreading support;
- compilation on Solaris 2.5.1 and testing on Solaris 7 and 8.

The artifact corroborates only part of that archive-level description:

- `nec2dx.f` identifies NEC2 as developed at Lawrence Livermore Laboratory, says the file was
  created April 11, 1980, and marks the double-precision conversion as June 4, 1985.
- Its history records a May 4, 1995 matrix re-transpose and `FACTR`/`SOLVE` changes for a
  non-transposed matrix. `nec2dx.txt` repeats that description.
- `NEC2DPAR.INC` fixes both `MAXSEG` and `MAXMAT` at 1500.
- `compilation_d.txt` says Sun Fortran 77 on Solaris 7 compiled with
  `f77 -fast -O4 -parallel nec2dx.f` and documents `PARALLEL=1` or a higher processor count.

The artifact does **not** identify Ray Anderson as the author of the modifications or provide a
complete modification history. The only named author inside the modified source is Scott L. Ray
for the 1990-1992 `stopwtch` routine. Ray Anderson's role is therefore recorded as the FUNET
index's contributor claim, not upgraded to source authorship.

## Rights and redistribution assessment

The five rights questions remain separate:

1. **Underlying NEC2.** The source header says the code was prepared as government-sponsored work
   and preserves the U.S./DOE warranty and liability disclaimer. It does not say that the authors
   were federal employees, that the source is a work of the United States Government, or that it
   is public domain. NEC2 is widely described as public domain, and an
   [LLNL-authored history hosted by OSTI](https://www.osti.gov/servlets/purl/891397) describes
   NEC2 as open source and notes the absence of distribution controls before NEC3. Those facts
   support the historical public-reference status of original NEC2 but do not turn every later
   modification into public domain. In particular, government sponsorship alone is not the test
   in [17 U.S.C. sections 101 and 105](https://www.law.cornell.edu/uscode/text/17/105), and the
   statute's notes expressly distinguish contractor-created works.
2. **`nec2dx` modifications.** Neither the archive nor the source grants permission to copy,
   modify, or redistribute the 1995 matrix changes. The embedded `stopwtch` routine separately
   states copyright 1990 and 1992 by The Regents of the University of California and “all rights
   reserved”; it contains no license grant.
3. **Public preservation.** Blocked. Publicly committing the archive or source would redistribute
   modified and separately copyrighted material without an express grant. Historical public
   hosting and attribution are provenance evidence, not a redistribution license.
4. **Internal numerical use.** Authorized as a bounded project disposition. The named archive
   deliberately makes source and compilation instructions available, strongly evidencing an
   intent that recipients compile and run it. Keeping an exact internal research copy and using
   its output as non-dispositive test evidence is supportable; broader copying, publication, or
   product distribution is not authorized by this decision.
5. **Attribution and notices.** Any permitted use must retain the complete source header and
   disclaimer; credit Lawrence Livermore Laboratory and the NEC2 authorship/contact shown there;
   identify Ray Anderson, WB6TPU, only as the FUNET-contributed archive source; retain the Scott L.
   Ray history and Regents copyright in `stopwtch`; cite the FUNET index and exact archive hash;
   and describe the 1995 `FACTR`/`SOLVE` modification without implying endorsement.

The evidence therefore supports disposition **B**, not public reference intake. If explicit
redistribution permission is later obtained for the complete archive, public intake must be a
separate decision with its own notice and preservation review.

## Technical suitability

### Arithmetic and lineage

The program uses `IMPLICIT REAL*8(A-H,O-Z)`, explicit `REAL*8`, and `COMPLEX*16` throughout its
electromagnetic calculations. That makes it a useful double-precision check against maintained
NEC2C's C `double` and C complex arithmetic.

It is not an independent algorithmic lineage. NEC2C's preserved README says it is a mostly manual
translation of NEC2 Fortran. More decisively, both implementations contain the same unusual
matrix path:

- an explicit full-matrix un-transpose before Gauss-Doolittle elimination;
- the same column scratch-vector traversal and pivot selection rule;
- the same squared-magnitude pivot threshold of `1e-10`;
- the same row-permutation behavior; and
- the same forward- and backward-substitution ordering.

The Fortran source and NEC2C also describe the change in the same terms: handling the main matrix
in non-transposed form for speed. This is evidence of shared implementation lineage, not merely a
shared NEC-2 specification. The different language, compiler, library, and runtime can expose
translation and floating-point-environment errors, but agreement cannot exclude a shared defect.

**Oracle disposition: secondary cross-check.** It is unsuitable as the primary independent
numerical oracle. A primary decision source must add a genuinely independent implementation,
authoritative reference results, analytically tractable cases, or a defensible combination of
those sources.

### Matrix and parallel behavior

The May 1995 `FACTR` change transposes the populated matrix in place before elimination, after
which `FACTR` and `SOLVE` operate on the resulting non-transposed layout. This changes storage
access and the floating-point operation sequence; it must not be assumed numerically invisible.
Pivot choices, singular/near-singular reporting, solution residuals, and solver outputs must be
checked, particularly for poorly conditioned and symmetry-reduced cases.

The source contains no OpenMP directives or explicit thread library. The documented
multithreading came from Sun `f77 -parallel` automatic parallelization, controlled by the
`PARALLEL` environment variable. `PARALLEL=1` is the documented single-processor setting. A
deterministic baseline must use that setting and must not enable compiler auto-parallelization;
repeat-run identity must be established rather than presumed.

### Limits, cards, ground, and files

- `MAXSEG=1500` and `MAXMAT=1500`; the in-core matrix reserve is `MAXMAT**2` complex values.
- Other fixed limits include 30 loads, 30 excitation sources, 30 network entries, five coupling
  pairs, and 200 impedance-normalization values. Maintained NEC2C dynamically allocates major
  calculation buffers and intentionally removed the old out-of-core/NGF path.
- Geometry dispatch includes `GW`, `GX`, `GR`, `GS`, `GE`, `GM`, `SP`, `SM`, `GF`, `GA`, `SC`,
  `GC`, and `GH`. Control dispatch includes `CE`, `FR`, `LD`, `GN`, `EX`, `NT`, `XQ`, `NE`, `GD`,
  `RP`, `CM`, `NX`, `EN`, `TL`, `PT`, `KH`, `NH`, `PQ`, `EK`, `WG`, `CP`, and `PL`.
- Ground paths include free space, perfect ground, reflection-coefficient approximation, radial
  screen handling, and Sommerfeld/Norton ground. `GN` mode 2 requires an external unformatted
  `SOM2D.NEC` whose dielectric/conductivity grid must match; this archive supplies neither that
  file nor SOMNEC. Maintained NEC2C instead integrates SOMNEC and regenerates grids as needed.
- `nec2dx` is interactive: it reads input and output filenames from standard input and writes a
  monolithic text report. NEC2C is non-interactive, accepts CLI filenames, has a more permissive
  parser, and edited report formatting. Raw report bytes are therefore not a compatibility
  criterion.
- Expected numeric report sections include structure geometry and segmentation, loads and ground,
  matrix timing, excitation and network data, segment currents, input impedance, input/radiated/
  loss power and efficiency, coupling, near electric/magnetic fields, and far-field gain and
  polarization. Comparisons must parse named physical values and preserve units and identities.

The archive has no example deck. Its Solaris recipe uses compiler-specific `-fast`, `-O4`, and
`-parallel` flags. Those flags combine aggressive optimization and automatic parallelization and
are not a defensible deterministic reference recipe for GNU Fortran.

### Required evidence before any oracle claim

A later, separately authorized qualification design must, before calling this source an oracle:

- prove repeatability with one thread and a pinned compiler/runtime;
- establish deck-level semantic equivalence despite parser and invocation differences;
- compare complex feed impedance, segment currents, power terms, efficiency, and directional
  near/far-field values by identity and units rather than report bytes;
- cover free space, perfect ground, reflection ground, loads, geometry transforms, symmetry,
  frequency stepping, and the maintained candidate's intended operating subset;
- treat Sommerfeld mode as unavailable until an independently authenticated compatible
  `SOM2D.NEC` generation route is authorized;
- exercise matrix-sensitive and near-singular cases and record pivot/residual behavior; and
- use genuinely independent reference evidence to decide disagreements and detect shared defects.

This task deliberately did not create a corpus, choose cases, set tolerances, or run either
solver.

## Existing toolchain inventory and build route

No suitable Fortran compiler is currently installed, so the optional untouched build was not
attempted.

| Location | Result | Target/runtime consequence |
| --- | --- | --- |
| MSYS `/usr/bin/gfortran` | not installed | No MSYS-runtime Fortran route currently exists. Installed C-only GCC is 15.3.0 targeting `x86_64-pc-cygwin`. |
| UCRT64 `/ucrt64/bin/gfortran.exe` | not installed | No native-Windows Fortran route currently exists. Installed C-only GCC is 16.1.0 targeting `x86_64-w64-mingw32`. |
| Other MSYS2 environment bins | no `gfortran`, `g77`, or `flang` executable | No alternate MSYS2 Fortran runtime. |
| Windows `PATH` | no `gfortran`, `g77`, `flang`, `flang-new`, `ifort`, `ifx`, `nvfortran`, or `nagfor` | No other already-available Windows compiler. |
| WSL | only `docker-desktop`; `gfortran` absent | No existing Linux/WSL compiler route. |

The cached MSYS2 package database was queried without synchronization. The non-mutating
`pacman -Sp --needed` preview for `mingw-w64-ucrt-x86_64-gcc-fortran` returned exactly two
additions, both version `16.1.0-5`:

1. `mingw-w64-ucrt-x86_64-gcc-libgfortran`
2. `mingw-w64-ucrt-x86_64-gcc-fortran`

It reported no upgrade, downgrade, replacement, or removal. The resulting compiler is expected to
be `/ucrt64/bin/gfortran.exe`, target `x86_64-w64-mingw32`, producing a native Windows UCRT-linked
executable and supporting fixed-form legacy Fortran. That expectation must be verified after any
future installation; cached package state can change.

The exact minimal future package command, only in a separately authorized job and only after a
fresh additions-only preview, is:

```powershell
C:\msys64\usr\bin\pacman.exe --needed -S mingw-w64-ucrt-x86_64-gcc-fortran
```

No package transaction was run in this task.

## Exact next bounded job

Authorize one **native UCRT64 untouched NEC2DX build probe**, not a numerical comparison job:

1. re-authenticate `nec2dx.tar` at the SHA-256 above and repeat the safe extraction checks;
2. re-preview the package transaction and stop unless it remains additions-only;
3. install only the two UCRT64 Fortran packages identified above;
4. inventory and hash the compiler, target, runtime DLLs, and package records;
5. make one untouched, single-thread build attempt in ignored storage, using GNU fixed-form legacy
   compatibility without Sun auto-parallel flags, source edits, or numerical optimization; and
6. record the first compile/link blocker or executable identity, imports, and repeatability.

Because the archive contains no example deck, that job must not invent or silently substitute a
bundled example run. It must stop after the build-route question is resolved. Corpus design,
comparison execution, and tolerance setting remain later, separately authorized work.

## Scope confirmation

- No numerical qualification occurred.
- No comparison corpus was begun.
- No Fortran compiler or package was installed, removed, updated, or synchronized.
- No maintained NEC2C source was modified or built.
- No third-party source, archive, object, executable, output, example result, package, or toolchain
  file was committed.
- Public `nec2dx` intake remains blocked by the rights evidence above.
