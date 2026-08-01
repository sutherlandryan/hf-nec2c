# MSYS POSIX unmodified build probe

## Task class and question

**RECONNAISSANCE.** Can authenticated, untouched original-author NEC2C 1.3.1 build and execute
under the existing MSYS2 MSYS POSIX runtime after installing only the missing MSYS-target GCC
development toolchain?

Starting `main` was `1d6996c00a67aad00608f991fb5bee593fddcd1d`. Its tree matched the former
PR #3 head `271d6870a32d8444f0c2afa103a84b1911e04135` after the squash merge.

## Approved package transaction

With no MSYS2 process running, the existing package database proposed additions only for
`pacman --noconfirm --needed -S gcc`. One transaction installed:

| Package | Version |
|---|---|
| `binutils` | `2.47-1` |
| `isl` | `0.27-1` |
| `mpc` | `1.4.1-1` |
| `msys2-runtime-devel` | `3.6.10-1` |
| `msys2-w32api-headers` | `14.0.0.r0.g9b3dd0125-1` |
| `msys2-w32api-runtime` | `14.0.0.r0.g9b3dd0125-1` |
| `windows-default-manifest` | `6.4-2` |
| `gcc` | `15.3.0-1` |

No installed package was upgraded, downgraded, replaced, removed, or reinstalled. The separate
UCRT64 compiler package remained `mingw-w64-ucrt-x86_64-gcc 16.1.0-5`.

## Compiler and runtime identity

- Compiler: `/usr/bin/gcc`, `gcc (GCC) 15.3.0`
- Target: `x86_64-pc-cygwin`
- Make: `/usr/bin/make`
- Linker: `/usr/bin/ld`, GNU ld `2.47.20260726`
- Runtime package: `msys2-runtime 3.6.10-1`
- Runtime identity: `MSYS_NT-10.0-26200 3.6.10-9a6cbe55.x86_64 2026-07-16 20:47 UTC`
- `/usr/include/sys/times.h`: present
- `struct sigaction`, `sigaction()`, and `sigemptyset()`: declared by the MSYS headers

## Configure and make

The existing source guard freshly extracted and authenticated all 34 original files under the
ignored `.build-temp/` tree. The shipped `configure` ran out of tree with `MSYSTEM=MSYS`, reported
build and host type `x86_64-pc-msys`, and exited `0`. `/usr/bin/make -j1` compiled 12 objects,
linked `nec2c.exe`, and exited `0`.

An initial PowerShell-to-`bash -c` argument-splitting error occurred before `configure` or any
generated file. Source and preservation checks passed and the build directory was empty before
the one allowed corrected replay. A subsequent unavailable host launcher API also started no
process; the corrected replay used the already-proven simple `bash -c` invocation.

## Successful executable result

- Size: 332,949 bytes
- SHA-256: `4a286fb75ad238762b8d6315cbc32cbf62581577b42e59464b9d2e5d5469f92c`
- Architecture: PE32+ x86-64 console executable
- Imported runtime DLLs: `msys-2.0.dll`, `msys-gcc_s-seh-1.dll`, and `KERNEL32.dll`

The executable is an MSYS-runtime program, not the native UCRT64 production candidate. It was
kept only in ignored temporary storage and is not approved for distribution or integration.

## Smoke result

`nec2c -v`, `nec2c -h`, and both runs of the existing project-authored minimal dipole deck exited
`0` under timeouts. Version output was 12 bytes with SHA-256
`15d67da393a970a9297675275306e17d7cb348d511496af1fa0b7792297d9c2f`. Help output was 156
stderr bytes with SHA-256 `1f2c6f7efd1b0d5f1dd7ec3fdba814c56faa8341a429f4f4e0dfd5a5b6076378`.

Each smoke report was 6,825 bytes with SHA-256
`396b90cfb8e49fcf1938e01d291638163f74e3b065e29b8456ece3b3ca482567`. All 119 report lines were
identical; there was no timing-line or other difference. Both smoke stdout and stderr streams were
empty.

## Source preservation

The archive remained 186,124 bytes with SHA-256
`8c706008bcb11c34bf33a3f8f78711c79f7bb49de8a22d74df6b10e1203c013e`. The source guard verified
exactly 34 original files before and after the build, and `verify-preservation.ps1` passed before
and after it. No original source byte changed. No generated output or executable is tracked.

## Result and exact next decision

**UNMODIFIED NEC2C 1.3.1 BUILDS AND RUNS UNDER THE MSYS POSIX RUNTIME.**

This is a same-implementation regression-baseline candidate. It depends on the MSYS runtime; it
is not a native Windows production executable, is not numerically qualified, and is not approved
for distribution or HF Propagation Control integration.

The next decision is whether to authorize a separate task that uses this MSYS result as the
same-implementation comparison baseline for the smallest project-authored native Windows timing
portability boundary. That work is not part of this reconnaissance.
