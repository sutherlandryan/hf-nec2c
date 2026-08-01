# Windows x64 MSYS2 UCRT64 untouched-source build driver

`build.ps1` records the v0.0.5f-A2b build route without editing or supplementing an original
NEC2C 1.3.1 archive member. It requires the separately provisioned and pinned MSYS2 UCRT64
toolchain documented in
[`../../docs/WINDOWS_X64_MINGW_UCRT64_UNMODIFIED_BUILD.md`](../../docs/WINDOWS_X64_MINGW_UCRT64_UNMODIFIED_BUILD.md).

The driver:

1. pins Bash, pacman, the MSYS2 runtime, UCRT64 GCC, and the linker by file hash;
2. pins both preservation-helper implementations before executing them;
3. binds GCC, binutils, pacman, and GNU Make to their expected UCRT64/MSYS paths;
4. requires exact zero-altered-file `pacman -Qkk` results for 13 trust-root and build packages;
5. runs the preservation verifier;
6. uses the reviewed A2 source guard to authenticate and freshly extract all 34 original files;
7. launches Bash with a cleared environment, attempt-local HOME/TEMP, and no startup files;
8. runs the shipped `configure` out of tree and then GNU `make`;
9. captures raw and path-normalized diagnostics below ignored `.build-output/`;
10. inventories every generated build file;
11. reverifies every source byte and the preservation layer; and
12. writes an atomic local attempt record that binds the driver and helper hashes.

The manifest separately records the complete provisioning-time package-integrity audit, including
the qualified legacy-MTREE false-positive disposition. The per-attempt check is deliberately
limited to build-critical packages that report zero altered files; it does not reinterpret or
waive any provisioning finding.

It never runs `autogen.sh`, edits generated upstream inputs, adds a compatibility header or source
file, or copies maintained NEC2C v1.3.3 code. The direct-GCC route remains explicitly not
attempted: it cannot be used to bypass a result from the authoritative shipped Autotools route.

Run with a fresh identifier:

```powershell
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass `
    -File .\build-support\windows-x64-mingw-ucrt64\build.ps1 `
    -BuildId <fresh-id>
```

Identifiers are single-use. Generated source, build products, diagnostics, and executables remain
under ignored `.build-temp/<id>/` and `.build-output/<id>/` paths and must never be staged.

Exit codes are:

| Code | Meaning |
|---:|---|
| `1` | Launch or preflight validation failed before an attempt record could be created |
| `10` | Authenticated untouched source failed during configure, compile, or link |
| `20` | Authentication, tool identity, integrity, timeout, driver, or preservation validation failed |

The current A2b result is a compile-time missing-header failure, so no success exit exists in the
versioned evidence. If an unchanged future environment unexpectedly links, the driver returns
`20`; two fresh builds, PE/import inspection, and bounded smoke validation must then be completed
before recording success.
