# Windows x64 unmodified build baseline

## Result

v0.0.5f-A2 reached a reproducible compiler failure without changing NEC2C 1.3.1 source:

> `nec2c.h(9): fatal error C1083: Cannot open include file: 'unistd.h': No such file or directory`

Two independent, authenticated extractions produced the same normalized diagnostics and
compiler exit code `2`. No object file or executable was produced. PE inspection and smoke
execution were consequently not applicable.

Canonical disposition:

> **UNMODIFIED MSVC WINDOWS X64 BUILD ATTEMPT REPRODUCIBLY BLOCKED BY POSIX HEADER
> DEPENDENCY**

This is a compiler and portability baseline only. It is not numerical qualification, solver
qualification, a maintained Windows port, structured output, or integration with HF Propagation
Control.

## Source identity and initial gate

The attempt began from clean `main` commit
`58df591335b8b19babf960e9825a423a2cf836f7`, identical to live `origin/main`.

| Evidence | Identity |
|---|---|
| Original release | NEC2C 1.3.1 by Neoklis Kyriazis |
| Archive | `archive/nec2c-1.3.1.tar.bz2`, 186,124 bytes |
| Archive SHA-256 | `8c706008bcb11c34bf33a3f8f78711c79f7bb49de8a22d74df6b10e1203c013e` |
| Archive tag | `archive/nec2c-1.3.1-original` → `b1ff42e308c8a1c80dc7a77636a5908e870af6f6` |
| Preservation tag | `preservation/nec2c-1.3.1-intake-v1` → `58df591335b8b19babf960e9825a423a2cf836f7` |
| Original files | 34 regular files, 786,583 bytes |
| Feature branch | `agent/v005f-a2-windows-x64-build` |

The checked-in preservation verifier passed before work, before each attempt, after each attempt,
and after the final documentation changes. The host's LocalMachine PowerShell execution policy
is `Restricted`, so the literal invocation without an execution-policy argument is blocked
before the verifier starts. The process-only invocation used throughout was:

```powershell
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass `
    -File .\verify-preservation.ps1
```

It changes no persistent execution policy. Direct standard-library Python verification also
passes. This host-policy caveat is not a preservation mismatch.

The separate HF Propagation Control checkout remained read-only and clean at
`ac231157b218415598f9d8a389492bef11d0a5a6`.

## Installed toolchain inventory

No compiler, SDK, package, or build tool was installed for A2.

| Route | Installed evidence | Disposition |
|---|---|---|
| GCC / MinGW-w64 | No GCC, GNU linker, MinGW-w64 target, or GNU make found | Unavailable |
| Clang / LLVM | No Clang compiler, `clang-cl`, LLD, or LLVM PE inspector found | Unavailable |
| MSYS2 / Cygwin | No standalone installation or compiler toolchain found | Unavailable |
| WSL cross-compiler | Only the `docker-desktop` distribution; no build toolchain | Unavailable |
| CUDA `nvcc` | 12.9.86 | Rejected: not a general C/Autotools route |
| Microsoft C/C++ | Visual Studio Build Tools 2019 16.11.48, MSVC v142 | Selected only existing native AMD64 compiler |

Selected identities:

- compiler: `cl.exe` 19.29.30159.0, 402,544 bytes, SHA-256
  `8e4352b523f4ff37b429aea1d340094be1e17bbdf4f687247fc0be92d6eb9440`,
  compiler-reported target `x64`;
- project-normalized target descriptor: `x86_64-pc-windows-msvc`;
- linker: `link.exe` 14.29.30159.0, 2,243,680 bytes, SHA-256
  `7d80b89e242e2ab4d002c3b3508361a45691a01bd1f4be4d19eb765c8d319762`;
- toolset: MSVC v142 14.29.30133;
- Windows SDK: 10.0.19041.0;
- intended runtime policy: `/MD`, Universal CRT plus VC Runtime;
- available build tools: NMake 14.29.30159.0, MSBuild 16.11.6.22506,
  Microsoft-bundled CMake 3.20.21032501-MSVC_2, and Ninja 1.10.2;
- available PE inspection: DUMPBIN 14.29.30159.0, 23,648 bytes, SHA-256
  `c0f34347853d568e30780146231dd417771bd7515868d6097bca02e7854caa1b`,
  `link.exe /DUMP`, and Git `file.exe` 5.48;
- driver runtimes: Windows PowerShell 5.1.26100.8894 and CPython 3.14.0b3 invoked through
  `py.exe -3 -I`.

NMake cannot consume the GNU Automake output. The original Autotools route therefore could not
run end-to-end with the installed tools.

The driver selects the exact Build Tools product ID, installation version
`16.11.36128.20`, product version `16.11.48`, MSVC tools version `14.29.30133`, Windows
SDK `10.0.19041.0`, and compiler file version `19.29.30159.0`. It does not select a
floating latest installation.

## Unmodified build boundary

Every attempt:

1. authenticated the fixed archive hash and size;
2. inspected all 35 archive members before extraction;
3. required one directory and exactly 34 regular files;
4. rejected absolute, traversing, duplicate, case-colliding, linked, reparse, or special
   members;
5. extracted into a new `.build-temp/<id>/source/` path;
6. compared every regular file with `manifests/nec2c-1.3.1-files.sha256`;
7. placed compiler output only below the sibling ignored build path;
8. rehashed the exact source inventory after compilation; and
9. reran the repository preservation verifier.

No archive member, C file, header, original build script, or source line was edited, normalized,
or supplemented. No compatibility function was compiled or linked. No maintained v1.3.3 code
was copied or imported.

The shipped package supports an Autotools VPATH build, but no compatible GNU toolchain was
installed. The selected fallback was the explicitly permitted project-authored external build
driver. It invoked the twelve production C sources in the order recorded by the original
`Makefile.am`; it did not create a maintained source tree and did not run `autogen.sh`.

## Controlled build policy

Both attempts used:

```text
LANG=C
LANGUAGE=C
LC_ALL=C
TZ=UTC
SOURCE_DATE_EPOCH=1701496474
VSLANG=1033
LIB=
```

`1701496474` is the maximum authenticated archive-member modification time:
2023-12-02 05:54:34 UTC on the top-level `nec2c-1.3.1` directory. The latest regular-file
timestamp is `1701496463` on the shipped `configure`; the archive-wide maximum was selected as
the package epoch.

The compile flags were:

```text
/nologo /TC /std:c11 /O2 /W4 /MD /Brepro
/DPACKAGE_STRING="nec2c 1.3.1" /c /Fo..\..\build\
```

The planned linker flags, not reached, were:

```text
/NOLOGO /MACHINE:X64 /SUBSYSTEM:CONSOLE /INCREMENTAL:NO /BREPRO
```

No debug option, PDB output, post-link rewrite, timestamp patch, or binary-normalization step was
used.

## Independent attempt evidence

| Fact | Build A | Build B |
|---|---:|---:|
| Build identifier | `final-a-20260729` | `final-b-20260729` |
| Fresh source path | Yes | Yes |
| Pre/post source authentication | Pass / Pass | Pass / Pass |
| Pre/post preservation verification | Pass / Pass | Pass / Pass |
| Compiler exit | `2` | `2` |
| Driver exit | `10` | `10` |
| Expected blocker classified | Yes | Yes |
| Non-temporary build artifacts after compile | `0` | `0` |
| Raw diagnostic SHA-256 | `752ff4830542e791a6d29a28a0c7efe326a208f23b9c972536d9f5d1e2a3625c` | `5da644ba61153a8ad98817dcab7c69d0b5bf62c9dd165ede316f023b9ccf94d9` |
| Normalized diagnostic SHA-256 | `3ac5a36f556c88b7f538d1e4ef899b34b44bf00c82e774dd4530ac169223ab91` | `3ac5a36f556c88b7f538d1e4ef899b34b44bf00c82e774dd4530ac169223ab91` |
| Executable SHA-256 | Not applicable | Not applicable |
| Executable bytes | Not applicable | Not applicable |
| Attempt duration | 4,193 ms | 3,838 ms |

The raw diagnostic hashes differ because each ignored log truthfully contains its distinct
temporary extraction path. Longest-path-first normalization replaces known absolute roots
case-insensitively with stable tokens. It does not replace bare usernames or arbitrary matching
substrings. The complete normalized diagnostics are identical and are preserved in the build
manifest. This proves repeatability of the observed failure, not reproducibility of an
executable.

The first missing interface is the unconditional `unistd.h` include at original
`nec2c.h:9`. Each of the twelve translation units stopped at that include. No later portability
blocker was empirically reached or established by A2; later work remains unknown until an
authorized toolchain or portability milestone reaches it.

The next decision is whether to provision and pin a compatible GNU/MinGW-w64 Windows x64
toolchain for another untouched-source attempt or to authorize a separately reviewed,
independently authored Windows portability milestone. The MSVC result alone does not prove that
source modification is unavoidable under every native Windows compiler. Any later portability
work must address the interfaces its selected toolchain actually lacks without copying
maintained v1.3.3 code. A2 does not make that decision or contain that implementation.

## PE inspection and smoke status

No `nec2c.exe` exists, so these success-only checks were not run:

- PE32+ and AMD64 header confirmation;
- section, timestamp, import, and export inspection;
- username, repository path, unrelated environment, and PDB-path scans;
- no-argument, missing-input, malformed-input, and minimal-dipole executions; and
- smoke-output repeatability comparison.

The independent BSD-2-Clause smoke deck remains versioned at
[`../tests/smoke/minimal-dipole.nec`](../tests/smoke/minimal-dipole.nec) for the first authorized
compiler that passes the unmodified source boundary. It is not numerical evidence.

## Reproduce the failure

Use a fresh build identifier for each attempt:

```powershell
$stamp = Get-Date -Format yyyyMMddHHmmss
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass `
    -File .\build-support\windows-x64\build.ps1 -BuildId "manual-a-$stamp"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass `
    -File .\build-support\windows-x64\build.ps1 -BuildId "manual-b-$stamp"
```

The ignored outputs are:

```text
.build-temp/<id>/source/   authenticated original extraction
.build-temp/<id>/build/    generated compiler/build/smoke workspace
.build-output/<id>/        raw and normalized local evidence
```

The driver refuses to reuse any of these paths. Nothing copies a result into `upstream/`.
The source guard uses single-link files, stable-handle reads, and post-read path/file identity
checks. Archive and manifest phases are nevertheless reopened or resolved by path, so the guard
does not claim protection against malicious concurrent mutation or replacement before, during,
or between authentication, manifest reading, extraction, or verification phases, or after the
final identity check. Failed partial extractions are retained for diagnosis and their identifiers
remain burned; cleanup is a manual exact-path operation. The process wrapper treats timeout or
stream-drain uncertainty as driver validation failure, but trusted local tools are still assumed
not to spawn detached descendants. Captured output is held in memory, which is acceptable only
for this fixed authenticated input and trusted installed-tool boundary. Builds assume a
non-adversarial local workspace.

## A2 disposition

The unmodified Windows x64 executable baseline is blocked at compilation. A2 is complete as a
truthful failure record and ready for review of that limited result. It is not ready to supply a
solver binary, numerical baseline, pattern, package, or application integration.
