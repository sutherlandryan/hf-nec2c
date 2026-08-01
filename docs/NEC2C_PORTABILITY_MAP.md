# NEC2C 1.3.1 portability map

## Scope and evidence boundary

This is a **RECONNAISSANCE** result. It maps the original-author NEC2C 1.3.1 Windows-portability
surface without changing or compiling NEC2C, installing packages, producing a solver executable,
or performing numerical qualification. The preserved source remains immutable under
`upstream/nec2c-1.3.1/`.

The map preserves two established build results:

- **MSVC PROVEN BLOCKER:** two authenticated untouched-source attempts stopped at the
  unconditional `unistd.h` include at `nec2c.h:9`. No object or executable was produced.
- **UCRT64 PROVEN BLOCKER:** the shipped `configure` completed, then the first production
  translation unit stopped at the unconditional `sys/times.h` include at `nec2c.h:15`. No object
  or executable was produced.

Nothing below promotes a statically likely issue or a feature-probe result into a blocker reached
by a complete NEC2C build.

## Status vocabulary

| Status | Meaning |
|---|---|
| **PROVEN BLOCKER** | An authenticated untouched-source NEC2C build stopped at this interface. |
| **CONFIRMED AVAILABLE** | The ISO C/UCRT64 contract, installed headers plus a bounded syntax/link probe, or the established configure route confirms support. |
| **LIKELY PORTABILITY WORK** | Static inspection or a feature probe identifies work likely needed, but an NEC2C build has not reached it. |
| **UNTESTED** | Source inspection identifies a relevant assumption whose actual runtime consequence has not been exercised. |
| **NOT RELEVANT TO NUMERICAL CORE** | The interface affects orchestration, diagnostics, timing, files, or process behavior rather than electromagnetic calculations. |

## Complete static portability table

| Status | Interface and exact source location | Purpose and UCRT64 disposition | Numerical risk, smallest boundary, and future validation |
|---|---|---|---|
| **PROVEN BLOCKER** on MSVC; **CONFIRMED AVAILABLE** on UCRT64 | `<unistd.h>` at `nec2c.h:9` | Declares POSIX interfaces used later by CLI parsing and process timing. UCRT64 provides it at `ucrt64/include/unistd.h`; the prior UCRT64 build passed this include. MSVC did not. | Header availability does not affect electromagnetic calculations. Keep platform selection in project-authored support headers, not numerical files. Rebuild the maintained source with each supported compiler and run the CLI matrix. |
| **PROVEN BLOCKER** on UCRT64; **NOT RELEVANT TO NUMERICAL CORE** | `<sys/times.h>` at `nec2c.h:15`; `struct tms`, `times()`, `sysconf()`, and `_SC_CLK_TCK` at `misc.c:77-85` | Supplies user-plus-system process time in milliseconds. UCRT64 has no `sys/times.h`; the authenticated build stopped there. The later symbols were therefore not reached by that build. | `secnds()` is observational: calls at `main.c:176,934,1192,1194,1197` and `somnec.c:48,169` do not feed solver calculations, although timing values enter report text at `main.c:936,1199-1203`. Create one process-timing interface outside numerical files. Validate monotonic/non-negative behavior, units, failure handling, and identical solver fields after excluding declared timing text. |
| **LIKELY PORTABILITY WORK**; UCRT64 interface **confirmed absent** | `struct sigaction`, `sigemptyset()`, and `sigaction()` at `main.c:82-97`; handler at `main.c:1981-2008` | Registers handlers for `SIGINT`, `SIGSEGV`, `SIGFPE`, `SIGTERM`, and `SIGABRT`. UCRT64 `signal.h` declares those signal constants and ISO `signal()`, but not the POSIX `sigaction` family. A syntax probe failed on the missing type and declarations. NEC2C has not compiled far enough to prove this is the next build blocker. | Registration and diagnostics are outside the numerical core in uninterrupted runs. Put registration behind one support interface only if the post-timing build reaches it. Validate normal execution, each controllable signal, cleanup, exit status, and absence of solver-output change. Reassess the existing non-async-signal-safe `fprintf`, `fclose`, and `exit` calls rather than preserving them accidentally. |
| **CONFIRMED AVAILABLE** on UCRT64; **NOT RELEVANT TO NUMERICAL CORE** | `getopt()`, `optarg`, and `optind` at `main.c:79,107-137` via `<unistd.h>` | Parses `-i`, `-o`, `-h`, and `-v`. UCRT64 `unistd.h` includes `getopt.h`; syntax and link probes passed. Native MSVC availability after its earlier header failure remains untested. | No UCRT64 replacement is justified. If a later compiler needs one, isolate CLI parsing from solver state. Validate attached and separate option arguments, option order, unknown/missing options, help/version, filenames, and exact exit policy before comparing solver output. |
| **CONFIRMED AVAILABLE** on UCRT64; numerically sensitive ISO C dependency | C99 complex types/macros at `nec2c.h:4,25-29,95,165,232,256,273,332,380,415,431,442,446-447`; APIs `cabs`, `carg`, `cexp`, `cimag`, `clog`, `conj`, `creal`, and `csqrt` are used in `calculations.c:54-55,199-210,1467-1468,1520`, `fields.c:167,507,1068-1069`, `ground.c:95-99`, `main.c:1116,1416-1420`, `matrix.c:787,1096-1104`, `network.c:179,486`, `radiation.c:74,719-727`, and `somnec.c:56-60,701,921-938` | Implements electromagnetic complex arithmetic throughout the solver. The UCRT64 C11 complex/VLA/`snprintf` syntax and link probes passed with `-lm`. This is ISO C, not a compiler extension. Post-`unistd.h` MSVC support remains untested. | **High numerical risk.** Do not wrap, replace, or emulate complex operations as part of the Windows platform layer. Any compiler/runtime change requires same-implementation regression against a working unmodified POSIX baseline, with declared tolerances before any qualification claim. |
| **CONFIRMED AVAILABLE** on UCRT64; numerically sensitive ISO C dependency | Real math APIs: `abs` at `calculations.c:521-522`; `asin` at `geometry.c:777`; `atan` at `geometry.c:1134`, `ground.c:297`, `radiation.c:393`; `atan2` at `geometry.c:778`, `radiation.c:755`; `floor` at `radiation.c:648`; `log10` at `calculations.c:477,488`; `pow` at `geometry.c:640,2403` and `main.c:1831`; representative `cos`, `fabs`, `log`, `sin`, `sqrt`, and `tan` sites at `calculations.c:81-83,205,351`, `fields.c:93,149`, and `radiation.c:46-48,85`. `configure.ac:28,41` checks `libm`, `floor`, `pow`, and `sqrt`. | Implements geometry and electromagnetic calculations. The shipped UCRT64 configure route found the required math support and reached source compilation. | **High numerical risk.** Keep these calls in the numerical core. Compare a maintained build against unmodified same-implementation output before considering cross-compiler or reference-code qualification. |
| **CONFIRMED AVAILABLE** on UCRT64; **NOT RELEVANT TO NUMERICAL CORE** | ISO `signal()` and `SIG*` constants in `<signal.h>` included at `nec2c.h:6` | A syntax and link probe passed. It is a possible implementation mechanism, not proof that it matches the required `sigaction` semantics. | Use only behind a signal-registration interface after explicitly defining required behavior. Validate handler persistence/reset semantics and interruption behavior on Windows. |
| **CONFIRMED AVAILABLE** on UCRT64; **NOT RELEVANT TO NUMERICAL CORE** | Standard file I/O at `main.c:140-170,293,899-912`; shared streams at `shared.h:17-18` and `shared.c:18-19`; cleanup at `misc.c:93-103`; character input at `misc.c:114-174` | Uses only narrow-character `fopen("r")`, `fopen("w")`, `rewind`, `fgetc`, `fprintf`, and `fclose`. No low-level POSIX file descriptor API is used. | Keep file opening and naming at the application boundary. Validate missing/read-only files, directories, spaces, both Windows separators, non-ASCII names, overwrite behavior, and cleanup. Solver calculations should be identical for identical parsed decks. |
| **LIKELY PORTABILITY WORK** only if product requirements demand normalization; **NOT RELEVANT TO NUMERICAL CORE** | Fixed filename/path buffers and derivation at `main.c:40,112-120,140-170,899-912`; first-dot truncation at `main.c:153-160` | Input/output names are capped at 75 bytes in 81-byte arrays. Default output naming truncates at the first `.` anywhere in the supplied path, mutates `infile`, and appends `.out`; plot naming later appends `.plt`. There is no `PATH_MAX`, path canonicalization, directory creation, or wide-character API. | Do not change until required behavior is specified. If needed, create one filename/filesystem boundary. Validate dotted directories, multiple extensions, 75/76-byte names, long paths, Unicode, relative/absolute paths, separators, collision/overwrite behavior, and identical parsed input. |
| **UNTESTED** runtime byte behavior; **NOT RELEVANT TO NUMERICAL CORE** except through parsing | Text mode at `main.c:140,164,906`; explicit CR/LF parsing at `nec2c.h:76-81` and `misc.c:114-174`; numeric parsing with `atoi`/`atof` at `geometry.c:1796,1862` and `input.c:292,360` | Windows text mode may translate CRLF on input/output; `load_line()` explicitly accepts CR and LF. The program never calls `setlocale`, so ISO C startup locale governs numeric parsing/formatting. Raw report bytes can differ by line ending even when solver values do not. | Validate LF, CRLF, CR, final-line-without-EOL, and malformed cards. Define line-ending normalization only in comparison tooling or file policy, never inside electromagnetic calculations. Compare parsed values and normalized reports separately from raw bytes. |
| **UNTESTED** pre-existing cross-platform safety issue; not a Windows-only blocker | `LINE_LEN` is 132 at `nec2c.h:80-81`; `load_line()` writes through that bound at `misc.c:147-172`; `main()` passes `line_buf[81]` at `main.c:41,245,269`, while `geometry.c:1728` and `input.c:224` use 134-byte buffers | Static inspection shows a buffer-size contract mismatch for long comment/command lines passed from `main()`. This task did not execute NEC2C or characterize the runtime consequence. | Treat as a separate correctness/hardening issue, not incidental portability scope. Any fix can change accepted-input behavior and therefore has numerical risk for long decks. Add boundary tests before changing it and compare parsed cards and solver output. |
| **CONFIRMED AVAILABLE** on UCRT64; compiler portability concern for MSVC is **UNTESTED** | C99 variable-length array `record[101+ichar*4]` at `main.c:1925`; `snprintf()` at `main.c:1955,1965` | Formats report records. UCRT64 syntax and link probes passed. This is standard C99, not a GNU extension. The prior MSVC build did not pass `unistd.h`, so later VLA behavior is not a proven MSVC blocker. | Formatting only. If a future compiler requires replacement, keep it local to reporting and validate bounds plus exact normalized report content. |
| **LIKELY PORTABILITY WORK** at the process contract; **NOT RELEVANT TO NUMERICAL CORE** | `exit(-1)` and `exit(0)` at `main.c:103,125,129,133,146,170,912`; signal-number exits at `main.c:1988-2005`; negative `why` values flow through `misc.c:30-73,93-103`; many solver error paths call `stop(-1)` | C only gives portable meaning to `0`, `EXIT_SUCCESS`, and `EXIT_FAILURE`; negative status mapping is host/shell dependent. Cleanup closes global streams, and fatal-signal paths do not consistently use it. | Define exit categories in one process boundary only after observing the working baseline. Validate help/version, CLI errors, missing/malformed input, solver errors, user interruption, and shell-visible status on each platform. Do not conflate exit normalization with solver qualification. |
| **CONFIRMED AVAILABLE** for the recorded UCRT64 route; detection gaps are **LIKELY PORTABILITY WORK** before durable builds | `configure.ac:4-9,21-25,28,33,35-41,43-44`; `Makefile.am:7-28,30-49`; conditional `config.h` inclusion at `main.c:26-28`; generated `PACKAGE_STRING` use at `main.c:128` | Autotools requires a POSIX shell and unnecessarily discovers C++; it checks `unistd.h` but the source includes it unconditionally, and it does not check `complex.h`, `sys/times.h`, timing symbols, `getopt`, `sigaction`, `snprintf`, or VLA support. It defaults to `-Wall -O2` without declaring a C standard. The shipped configure nevertheless completed under MSYS2/UCRT64 and generated the package macro used by `-v`; the external MSVC baseline supplied that macro explicitly. Install/dist hooks assume shell tools but do not affect the production source compile. | Keep reconnaissance changes out of the generated build until a route works. During productionization, make the maintained build declare its C standard and fail early on required platform-layer capabilities. Validate out-of-tree configure/build on each supported host and do not regenerate immutable upstream files. |
| **NOT RELEVANT TO NUMERICAL CORE** and no current implementation use | `<fcntl.h>`, `<errno.h>`, `<time.h>`, and `<sys/types.h>` at `nec2c.h:11-14`; `fcntl.h` is checked at `configure.ac:33` | No `fcntl` flag, `errno`, wall-clock API, or explicit `sys/types.h` type is referenced by original C code. UCRT64 provides these headers, but they do not solve the process-timing dependency. | A maintained derivative may minimize headers in its own support boundary, but removing unused includes is not a standalone portability objective. Rebuild with warnings and compare output if changed. |
| **NOT RELEVANT TO NUMERICAL CORE** because absent | Complete source search found no `fork`, `exec*`, `system`, `popen`, `wait*`, `sleep`, `usleep`, `nanosleep`, `unlink`, `access`, `fileno`, `isatty`, low-level `open/read/write/close`, directory, permission, or process-spawn call | No process creation, delay, terminal, unlink, or low-level file portability layer is currently required by NEC2C 1.3.1. | Do not add abstractions for interfaces the source does not use. Recheck only if maintained code introduces them. |

No GNU `asm`, `typeof`, statement expression, `__attribute__`, `__declspec`, compiler pragma, or
platform preprocessor branch occurs in the original C/header set. The language portability
baseline is C99 or later because the numerical core uses complex arithmetic and reporting uses a
VLA and `snprintf`.

## Temporary UCRT64 feature probes

Eleven temporary probe files were created under exact ignored `.build-temp/portability-*` children
and all were deleted with their outputs. No probe source, object, or executable remains.

| Probe result | Result |
|---|---|
| Initial four-file syntax batch without the required UCRT64 runtime `PATH` | **FAIL (invalid setup)**: compiler exit 1 before useful diagnostics; no interface conclusion. |
| `getopt`, `optarg`, `optind` syntax | **PASS** |
| POSIX `struct sigaction`, `sigemptyset`, `sigaction` syntax | **FAIL**: type and declarations absent |
| ISO `signal()` plus required `SIG*` constants syntax | **PASS** |
| C11 complex arithmetic, VLA, and `snprintf` syntax | **PASS** |
| Minimal links for `getopt`, ISO `signal()`, and C11 complex/VLA/`snprintf` (with `-lm`) | **PASS / PASS / PASS** |

These probes did not compile NEC2C and do not establish runtime or numerical qualification.

## POSIX same-implementation baseline inventory

Classification: **MINIMAL PROVISIONING NEEDED**.

| Route | Current state | Classification |
|---|---|---|
| MSYS2 MSYS runtime | `C:\msys64\usr\bin\bash.exe` and GNU Make 4.4.1 are present. MSYS-target `/usr/bin/gcc` and `/usr/include/sys/times.h` are absent. | Not ready; the cheapest route is to provision the MSYS-target GCC and its required runtime development headers in a separate authorized job. |
| MSYS2 UCRT64 | GCC 16.1.0 targeting `x86_64-w64-mingw32` is present. `unistd.h` and `getopt` are present; `sys/times.h` and the `sigaction` family are absent. | Windows portability target, not an unmodified POSIX baseline. |
| WSL | WSL 2 is installed, but the only registered distribution is the stopped `docker-desktop` service distribution. No ordinary Linux development environment is available. | Not a usable existing baseline route. |

No package was installed, updated, downgraded, removed, or queried as an inventory during this
reconnaissance.

## Smallest coherent future platform layer

Any maintained derivative must remain project-authored and outside `upstream/`. The smallest
coherent boundary is a narrow support layer consumed by the unchanged numerical modules:

1. a process-time function with explicitly defined units and failure behavior;
2. a signal-registration function, only if the first post-timing build confirms it is needed;
3. a CLI option parser boundary, only for a supported compiler that lacks the already-confirmed
   UCRT64 `getopt` route; and
4. process-exit and filename/file-opening policy, only where behavioral tests establish a
   requirement.

Platform selection belongs inside that support layer. Do not scatter `_WIN32` or compiler
conditionals through electromagnetic calculation files.

## Ordered minimal patch plan

Do not implement these steps until an unmodified POSIX same-implementation baseline exists.

1. **Portable process timing.** Independently author the timing interface and POSIX/Windows
   implementations outside the preserved tree. Build both maintained targets; test units,
   monotonicity, failure behavior, and timing report fields; compare all non-timing solver fields
   with the unmodified POSIX baseline.
2. **Portable signal registration, only if confirmed necessary.** After timing compiles, stop at
   the next actual blocker. If it is the `sigaction` family, define required semantics and use a
   single registration boundary. Test ordinary completion, controllable signals, cleanup, and
   exit status; repeat the same-implementation solver comparison.
3. **Portable CLI parsing, only if confirmed necessary.** UCRT64 already links `getopt`, so make no
   change for that route. If another supported target lacks it, implement only the four existing
   options and validate the complete CLI matrix plus identical solver inputs/outputs.
4. **Exit-code and filesystem normalization, only if confirmed necessary.** Specify status and
   path contracts first. Test failure categories, separators, dotted directories, length limits,
   Unicode policy, text line endings, collisions, and overwrite behavior. Repeat preservation and
   same-implementation regression after each coherent change.

Promotion into reproducible build infrastructure, dependency attestation, hardened process
containment, release manifests, broad regression, or numerical qualification is a later
**PRODUCTIONIZATION** task.

## Explicit unknowns

- The first compile or link result after replacing the UCRT64 timing dependency is unknown.
- `sigaction` is confirmed absent from UCRT64 but is not a proven NEC2C build blocker.
- Whether untouched NEC2C builds and runs correctly in an MSYS POSIX runtime is unknown.
- Post-`unistd.h` MSVC portability, including complex arithmetic and VLA support, is untested.
- Required Windows signal semantics, Unicode/long-path policy, and cross-platform raw report-byte
  policy are not yet product contracts.
- Runtime consequences of the 81-byte/132-byte line-buffer mismatch are untested.
- No executable behavior, same-implementation regression, cross-compiler agreement, NEC
  reference agreement, or numerical qualification has been established.

## Exact recommended next job

**Task class: RECONNAISSANCE - Establish the unmodified NEC2C 1.3.1 MSYS POSIX regression
baseline.**

In a separately authorized task, provision only the MSYS-target GCC and required MSYS runtime
development headers in the existing `C:\msys64`; do not update unrelated packages. Authenticate a
fresh disposable extraction, run the shipped Autotools route inside the MSYS runtime without
source changes, and stop at the first blocker. If it links, run only the bounded CLI/smoke matrix
needed to retain same-implementation regression outputs, explicitly separating timing text and
line-ending normalization from solver values. Do not patch NEC2C, create release infrastructure,
or claim numerical qualification in that job.
