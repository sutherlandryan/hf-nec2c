# Windows x64 MSYS2 UCRT64 untouched-source build attempt

## Result

v0.0.5f-A2b provisioned an authenticated MSYS2 UCRT64 / MinGW-w64 GNU toolchain and
used it to build a fresh, authenticated extraction of the original-author NEC2C 1.3.1
distribution. The shipped `configure` completed successfully and GNU `make` reached the
first production C translation unit without any source change. Compilation then stopped at
the original `nec2c.h:15` dependency:

```text
In file included from <ATTEMPT_ROOT>/source/nec2c-1.3.1/calculations.c:26:
<ATTEMPT_ROOT>/source/nec2c-1.3.1/nec2c.h:15:10: fatal error: sys/times.h: No such file or directory
   15 | #include <sys/times.h>
      |          ^~~~~~~~~~~~~
compilation terminated.
make[1]: *** [Makefile:450: calculations.o] Error 1
make: *** [Makefile:325: all] Error 2
```

No solver executable was linked. The canonical disposition is:

> **UNMODIFIED MSYS2 UCRT64 WINDOWS X64 BUILD ATTEMPT BLOCKED BY SYS/TIMES.H
> DEPENDENCY**

This is a source-preserving compiler and portability result. It is not a Windows port,
executable qualification, numerical qualification, structured solver output, or integration
with HF Propagation Control.

The complete machine-readable record is
[`windows-x64-mingw-ucrt64-unmodified-build-v1.json`](../manifests/windows-x64-mingw-ucrt64-unmodified-build-v1.json).
The build entry point and its operating notes are
[`build.ps1`](../build-support/windows-x64-mingw-ucrt64/build.ps1) and
[`README.md`](../build-support/windows-x64-mingw-ucrt64/README.md).

## Merged A2 baseline gate

A2b began only after reviewed pull request #1 had been merged. Local `main` and live
`origin/main` both resolved to:

```text
e74b603cab40ed7d8613d6318acc84abd4ba4217
```

That merge commit has the reviewed A2 head
`5333b70f50469c2f9658f865afdaee8284ff0e2b` as a parent. The merged record therefore
contains the hardened A2 MSVC baseline documented in
[`WINDOWS_X64_UNMODIFIED_BUILD.md`](WINDOWS_X64_UNMODIFIED_BUILD.md): two untouched-source
MSVC attempts stopped at the earlier original `unistd.h` include.

The A2b feature branch is `agent/v005f-a2b-mingw-ucrt64-build`. Before provisioning and
again around the canonical attempt:

- the offline preservation verifier passed;
- the fixed archive remained 186,124 bytes with SHA-256
  `8c706008bcb11c34bf33a3f8f78711c79f7bb49de8a22d74df6b10e1203c013e`;
- all 34 original regular files, totaling 786,583 extracted bytes, authenticated;
- the immutable archival and preservation tag objects remained unchanged;
- no byte under `archive/` or `upstream/nec2c-1.3.1/` changed; and
- the separate HF Propagation Control repository remained read-only and unmodified.

The reviewed A2
[`source_guard.py`](../build-support/windows-x64/source_guard.py) was reused byte-for-byte.
A2b did not weaken or replace its archive-member and extracted-file checks.

## Existing-installation gate

The pre-installation inventory found no existing MSYS2 installation at `C:\msys64`, no
other usable MSYS2, MinGW-w64, or GCC root, and no process using such a root. That cleared
the stop condition against overwriting or silently reusing an unqualified installation.

The inventory covered ordinary filesystem, command, process, and uninstall-registration
locations available without elevation. An all-users application-package query was denied to
the non-elevated process; that coverage limit is recorded rather than treated as a positive
finding. No unrelated installation or global configuration was modified.

## Authenticated MSYS2 acquisition and installation

The selected installer was the official dated stable release available at provisioning time,
not the moving nightly or `latest` alias:

| Evidence | Recorded identity |
|---|---|
| Release | `2026-06-11`, published `2026-06-11T07:23:06Z` |
| Installer | `msys2-x86_64-20260611.exe` |
| Official release URL | [MSYS2 installer 2026-06-11](https://github.com/msys2/msys2-installer/releases/tag/2026-06-11) |
| Size | 94,016,640 bytes |
| SHA-256 | `3150d7d9aa5dedd900a7f52300d4d918271e3a8fc47de94848818fd5a430e6b0` |
| Authenticode status | `Valid` |
| Signer | `CN=Christoph Reiter, O=Christoph Reiter, L=Graz, C=AT` |
| Signer issuer | `CN=Microsoft ID Verified CS AOC CA 04, O=Microsoft Corporation, C=US` |
| Signer thumbprint | `47F81859AE612659DD2248E76A58347A073B2933` |
| Timestamp thumbprint | `FD2F31399C42510141364ACDF168A28F5C79CBC3` |

The computed installer SHA-256 matched both the official `.sha256` sidecar and the GitHub API
asset digest. The release's `.sig` asset was also retrieved as acquisition evidence; this
milestone does not claim a separate GPG verification of that installer signature.

The installer ran non-elevated and completed with exit code `0`:

```text
msys2-x86_64-20260611.exe in --confirm-command --accept-messages --root C:/msys64
```

It installed at exactly `C:\msys64`. The root was an ordinary directory, not a reparse
point, and the global Windows `PATH` was not changed.

Initialization and updating were performed through controlled UCRT64 provisioning shells. The
first update upgraded the core runtime and closed that shell as required; a new shell completed
the remaining full-system updates; a final `pacman --noconfirm -Suy` reported nothing to do for
both the core and full system. These provisioning commands are separate from the isolated
no-startup-file shell boundary used for the canonical build. The resulting base identities were:

- `pacman 6.1.0-25`;
- `msys2-runtime 3.6.10-1`; and
- `msys2-keyring 1~20260214-1`.

The manifest records the complete 90-package post-update base inventory, its canonical text
hash, the package-database hashes, and hashes of `pacman.conf` and the MSYS and MinGW mirror
lists. Installer files, package archives, full local acquisition redirects, and command logs
remain ignored local evidence; no third-party binary was added to this repository.

## Pinned UCRT64 toolchain

The only explicitly requested build packages were:

```text
mingw-w64-ucrt-x86_64-gcc
make
autoconf
automake
libtool
pkgconf
```

Pacman resolved 38 added packages. The post-toolchain inventory contains 128 packages, and
the manifest records every package identity plus the filename and SHA-256 of each added
package archive.

| Component | Pinned identity |
|---|---|
| GCC | `gcc.exe (Rev5, Built by MSYS2 project) 16.1.0` |
| GCC package | `mingw-w64-ucrt-x86_64-gcc 16.1.0-5` |
| GCC target | `x86_64-w64-mingw32` |
| Resolved GCC path | `/ucrt64/bin/gcc` |
| GCC executable SHA-256 | `f96a3bdb1d3a3967b309d75c7413399391e857b5be4cb17162572ed66f6772a0` |
| Bash | `bash 5.3.015-1`; `/usr/bin/bash` |
| Bash executable SHA-256 | `41b09f0a9c1c68fd65253a7e8087b3775f0af245b729ade74ca4425d14392c2d` |
| Pacman | `pacman 6.1.0-25`; `/usr/bin/pacman` |
| Pacman executable SHA-256 | `209b2d527f359608cdb092515d3d99f46ac9d2209d130adced81a8cdd79057d8` |
| MSYS2 runtime | `msys2-runtime 3.6.10-1`; `/usr/bin/msys-2.0.dll` |
| MSYS2 runtime SHA-256 | `0cb645ead21947b7e865448413f3e281236638ed38695b43c2a6d9c06598e046` |
| Binutils | `mingw-w64-ucrt-x86_64-binutils 2.47-1`; GNU ld `2.47.20260726` |
| Resolved linker path | `/ucrt64/bin/ld` |
| Linker SHA-256 | `fb152d34cf00bf66fc57a66522806a4e64914654d8c1ab8cdd0a1d78283ec215` |
| GNU Make | `4.4.1-3` |
| Resolved GNU Make path | `/usr/bin/make` |
| Autoconf | `2.73` via `autoconf-wrapper 20260320-1` |
| Automake | `1.18.1` via `automake-wrapper 20260320-1` |
| Libtool | `2.5.4-5` |
| pkgconf | `2.5.1-1` |
| MinGW-w64 headers | `14.0.0.r220.gd999af622-1` |
| MinGW-w64 CRT | `14.0.0.r220.gd999af622-1` |
| GCC runtime libraries | `16.1.0-5` |

The environment provides `C:\msys64\ucrt64\include\unistd.h`, owned by the pinned
MinGW-w64 headers package. Its SHA-256 is
`33515907c2e69329c9e60e7b2ea7e9dadd76aa9f7adb0aaec2c967769f02652d`.
That explains why A2b passed the `unistd.h` point that blocked the merged A2 MSVC baseline.
It does not imply that every POSIX interface used by NEC2C is available in UCRT64.

## Package-integrity disposition

Immediately before the final canonical attempt, `pacman -Qkk` reported zero altered files for 13
packages: Bash, pacman, the MSYS2 runtime, GCC, GNU Make, the Autoconf and Automake wrappers,
Libtool, pkgconf, Binutils, MinGW-w64 headers, the MinGW-w64 CRT, and GCC runtime libraries. The
driver requires each exact summary line as well as exact anchored package-version lines; a longer
version string cannot satisfy a shorter pin.

The complete provisioning-time check of all 38 added packages reported 606 apparent changes,
confined to one file in `mingw-w64-ucrt-x86_64-windows-default-manifest` and five legacy
Automake packages:

| Legacy package | Apparent changes |
|---|---:|
| `automake1.11` | 128 |
| `automake1.12` | 122 |
| `automake1.13` | 118 |
| `automake1.14` | 119 |
| `automake1.15` | 118 |
| `mingw-w64-ucrt-x86_64-windows-default-manifest` | 1 |

These findings were not ignored. They were investigated against the authenticated cached
package archives and installed package metadata:

- all 606 installed payload files were byte-identical to their package archives;
- the stored legacy MD5 values matched the installed files;
- archive SHA-256 values matched the repository evidence;
- detached signatures for all six affected package archives verified;
- local package metadata matched the archive metadata; and
- the affected packages contained no unaccounted links or installation scripts.

The result is a qualified false-positive disposition: pacman 6.1's file-check path evaluates
SHA-256 while these legacy package MTREE records contain only MD5 digests. The behavior is
traceable to the official
[`pacman` file-check implementation](https://github.com/msys2/msys2-pacman/blob/e3dc296ba35d5039775c6e53decc7296b3bce396/src/pacman/check.c)
and the
[`ALPM-MTREE` format specification](https://alpm.archlinux.page/specifications/ALPM-MTREE.5.html).
This exception classifies a known diagnostic mismatch; it is not a general waiver of package
integrity. The manifest includes the complete six-package audit results, hashes of its
project-authored audit script and JSON evidence, the full 38-package `Qkk` output hashes and exit,
and the unchanged pacman remote-package signature policy (`Required`). The installed bytes used by
the build matched their authenticated package payloads.

## Untouched-source build boundary

The A2b driver enforces the following sequence for every identifier:

1. require the pinned Bash, pacman, MSYS2 runtime, UCRT64 GCC, and linker hashes;
2. require the fixed hashes of the source guard, preservation wrapper, and preservation verifier;
3. exact-match the 13 trust-root and build-package versions, target, and resolved tool paths;
4. require zero altered files for those 13 packages immediately before the attempt;
5. run the offline [preservation verifier](../verify-preservation.ps1);
6. authenticate the fixed archive and inspect every member before extraction;
7. extract all 34 original files into a new ignored attempt directory;
8. compare every extracted byte with the preservation manifest;
9. create a separate ignored out-of-tree build directory;
10. launch Bash as `--noprofile --norc -c` with a cleared, explicit allowlist environment;
11. run the shipped `configure`, then `/usr/bin/make -j1 V=1`;
12. capture raw and path-normalized stdout and stderr;
13. inventory generated build files;
14. reauthenticate the disposable source tree;
15. rerun repository preservation verification; and
16. write an atomic local attempt record that binds the driver and all authentication helpers.

The standard-library implementation behind the repository verifier is
[`verify_preservation.py`](../tools/verify_preservation.py). The driver refuses reused attempt
identifiers, reparse-point roots, package drift, GCC hash drift, target drift, authentication
failure, timeouts, and unexpected success without the required success-only validation.

No original C file, header, `configure`, `Makefile.am`, or other archive member was edited,
normalized, regenerated, or supplemented. The driver did not run `autogen.sh`. It did not
add a compatibility header or function. It did not copy or adapt source from the maintained
NEC2C v1.3.3 tree.

The shipped Autotools route is authoritative for this attempt. A direct-GCC command was not
attempted and cannot be used to bypass a configure, compile, or link result from that route.

## Build environment controls

The canonical process fixed or neutralized these build selectors:

```text
BASH_ENV=
CDPATH=
CHERE_INVOKING=yes
CONFIG_SITE=/dev/null
ENV=
LANG=C
LANGUAGE=C
LC_ALL=C
MAKEFLAGS=
MFLAGS=
MSYSTEM=UCRT64
MSYS2_PATH_TYPE=strict
SOURCE_DATE_EPOCH=1701496474
TZ=UTC
```

Each tool invocation started with a cleared environment and launched Bash as
`bash --noprofile --norc -c`; no shell startup file ran. The explicit allowlist supplied static
build controls, an attempt-local `HOME`, `USERPROFILE`, `TEMP`, `TMP`, and `TMPDIR`, plus only
`SystemRoot` and `WINDIR` copied from the parent process for Windows runtime operation. No
arbitrary parent environment variable was inherited. Inside Bash, the driver fixed
`PATH=/ucrt64/bin:/usr/bin`, bound `CC`, `AR`, `LD`, `NM`, `RANLIB`, and `STRIP` to absolute
UCRT64 paths, and explicitly unset compiler search-path, flag, package-config, dependency-output,
and Make selector variables before applying the recorded flags.

The C flags passed through the shipped build were:

```text
-O2
-fno-ident
-ffile-prefix-map=<SOURCE_ROOT>=/usr/src/nec2c-1.3.1
-fdebug-prefix-map=<SOURCE_ROOT>=/usr/src/nec2c-1.3.1
```

The declared linker flags were:

```text
-Wl,--no-insert-timestamp
-Wl,--build-id=none
```

Configure exercised those flags in its feature probes. The NEC2C final link was not reached.

`configure` detected both build and host as `x86_64-pc-mingw64`, found `unistd.h`,
created `Makefile` and `config.h` outside the authenticated source tree, and exited `0`.
The first Make compile command used `/ucrt64/bin/gcc` on original `calculations.c`, which
includes original `nec2c.h`; GCC stopped at line 15 before producing `calculations.o`.

## Canonical attempt evidence

| Fact | Recorded value |
|---|---|
| Starting `main` | `e74b603cab40ed7d8613d6318acc84abd4ba4217` |
| Build identifier | `canonical-ucrt64-v4-20260730` |
| Driver exit | `10` — authenticated untouched-source build failure |
| Attempt duration | 37,278 ms |
| `configure` exit / duration | `0` / 35,048 ms |
| `make` exit / duration | `2` / 546 ms |
| Failing stage | Compile |
| Expected blocker classified | Yes |
| Source authentication | Pass before / pass after |
| Preservation verification | Pass before / pass after |
| Generated build inventory | 17 files, 98,789 bytes; no object or executable |
| Driver SHA-256 bound in record | `021d370f0472158af43045e87ac2a980564137abb9b1ff497b8bccc7222d3e04` |
| Source-guard SHA-256 bound in record | `331718ae2b79390b71b8eb935953b7652d5a702a3e56cf1deb6aa51152b88b13` |
| Preservation wrapper SHA-256 bound in record | `a8c19981db3fdbcaee380755c29f56975ea1ead3d78976fb90c81c22e438e0f7` |
| Preservation verifier SHA-256 bound in record | `4fbfebcf7a09307dc7314a75fe2789860f243ae60e8b64604125821f729fc658` |
| Atomic attempt-record SHA-256 | `7de74afe975cf1da3218dcb9300a371db7291b420e5106af460ca0a5a233b2f2` |

Normalized evidence:

| Stream | Bytes | SHA-256 |
|---|---:|---|
| `configure` stdout | 2,282 | `2c651e1c5545facc71a4fd7a6fb4e6680ae6c38b6adaaa6251ef186cb17c9248` |
| `configure` stderr | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `make` stdout | 593 | `3dd261400f1c4912d772f19e9240eeef1d3f921e18ffddb87d40e63ce97a806d` |
| `make` stderr | 352 | `526284c767fb1b96646ace2e47a4819c84b9ded1ad78c5cb9cf1bc91458a3d89` |

Normalization replaces the known disposable attempt root with `<ATTEMPT_ROOT>`; it does not
rewrite the substantive compiler message. The manifest commits the exact normalized diagnostic,
the complete relative generated-file inventory, and command templates. Raw diagnostics and local
attempt records remain in ignored directories. Their versioned hashes bind this report to the
local evidence without publishing machine-specific paths.

Only one canonical A2b attempt is recorded. The result establishes the first dependency reached
by that authenticated route; it does not claim two-attempt failure reproducibility and does
not establish what later compilation or link failures may exist.

## Meaning of the `sys/times.h` failure

The original NEC2C 1.3.1 header unconditionally includes both `unistd.h` at line 9 and
`sys/times.h` at line 15. UCRT64 supplies the former, so the GNU route advanced beyond the
merged A2 MSVC blocker. It does not supply the latter in the include search used by this
build. Original `misc.c` later declares `struct tms` and calls `times()`, so this is not merely
an unused include that A2b can delete while claiming untouched source.

The empirical conclusion is deliberately narrow: this authenticated UCRT64 environment cannot
compile the untouched distribution because the original timing interface is unavailable.
A2b does not prove that `sys/times.h` is the only portability issue, prescribe a replacement
clock, or show that source modification is unavoidable under every possible Windows toolchain.

## Checks not reached

Because no `nec2c.exe` was produced, A2b did not perform or claim:

- a second fresh successful build or executable hash comparison;
- PE32+ and AMD64 header confirmation;
- linker timestamp, build ID, section, import, export, runtime-library, or subsystem inspection;
- embedded username, source path, repository path, unrelated environment, or debug-path scans;
- no-argument, missing-input, malformed-input, or minimal-dipole smoke execution;
- deterministic smoke-output comparison;
- numerical comparison against a NEC reference; or
- solver, antenna-pattern, packaging, or application qualification.

The independently authored
[`minimal-dipole.nec`](../tests/smoke/minimal-dipole.nec) remains only a bounded smoke input for
a later authorized build that links. It is not numerical qualification evidence.

No executable, object file, package archive, installer, release asset, or other third-party
binary is tracked or published by A2b. Structured output and HF Propagation Control integration
were not started.

## Run the recorded build route

The driver expects the pinned environment at `C:\msys64`; it does not rely on the global
Windows `PATH`. From a clean repository root, first verify preservation:

```powershell
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass `
    -File .\verify-preservation.ps1
```

Then use a new identifier:

```powershell
$stamp = Get-Date -Format yyyyMMddHHmmss
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass `
    -File .\build-support\windows-x64-mingw-ucrt64\build.ps1 `
    -BuildId "manual-$stamp"
```

In the recorded environment, the expected driver exit is `10`, with the authenticated
`sys/times.h` compile failure. Exit `20` means a tool identity, authentication, integrity,
timeout, driver, preservation, or unexpected-success validation failure and must not be
reclassified as the recorded compiler result. Exit `1` means launch or preflight validation
failed before an attempt record could be created.

Generated material remains ignored:

```text
.build-temp/<id>/source/    authenticated fresh extraction
.build-temp/<id>/build/     generated out-of-tree build workspace
.build-output/<id>/         raw, normalized, inventory, and attempt evidence
```

The driver deliberately refuses to reuse any of those identifier paths. Do not stage their
contents or copy results into `upstream/`. Run the preservation verifier again after the
attempt.

## Reconstructing the tool environment

The exact installer URL, sidecar URL, signatures, package identities, package archive hashes,
package database hashes, update evidence, and mirror configuration are in the versioned
manifest. A strict reconstruction must:

1. retrieve the exact official dated installer;
2. require the recorded byte count and SHA-256;
3. require valid Authenticode identity;
4. install only at `C:\msys64`, without changing global `PATH`;
5. initialize and fully update MSYS2 in restart-aware stages;
6. request only the six documented build packages;
7. require the recorded resolved package identities and archive hashes; and
8. rerun package, compiler, target, source, and preservation gates before building.

MSYS2 repositories are rolling, and this repository intentionally does not redistribute their
installer or package archives. A future ordinary `pacman -S` may resolve versions different
from this record. If the exact authenticated packages are no longer available from official
sources or an operator-controlled authenticated cache, reconstruction must stop rather than
silently substitute newer packages. The versioned evidence makes the recorded environment
auditable and causes the build driver to reject drift; it is not a promise that third-party
rolling repositories will retain every package indefinitely.

## Qualification boundary and next milestone

A2b is complete as a truthful untouched-source build-failure record. It narrows the Windows
portability question from the A2 MSVC `unistd.h` failure to the timing interface actually
reached by an authenticated UCRT64 GNU build.

The next implementation step requires a separately authorized, independently authored Windows
portability milestone. That work should:

- keep `archive/` and `upstream/nec2c-1.3.1/` immutable;
- create maintained project-authored source outside the preservation tree;
- document the semantics required from `sys/times.h`, `struct tms`, and `times()` before
  selecting a Windows timing implementation;
- preserve original provenance and add BSD-2-Clause identification only to eligible
  project-authored work;
- avoid copying or adapting the maintained NEC2C v1.3.3 implementation unless its provenance
  and licensing are separately reviewed and authorized; and
- address only portability dependencies actually established by reviewed evidence.

If that milestone links, it must then perform two fresh builds, executable hash comparison,
PE/import/runtime and embedded-path inspection, and the bounded smoke matrix before claiming a
qualified Windows executable. Numerical qualification, structured output, packaging, and
HF Propagation Control integration remain later, separately reviewed milestones.
