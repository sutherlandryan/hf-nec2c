# Windows x64 unmodified build driver

`build.ps1` reproduces the v0.0.5f-A2 compiler-baseline attempt without changing an original
NEC2C 1.3.1 archive member. It runs offline and non-elevated.

The driver:

1. runs the repository preservation verifier;
2. authenticates the 186,124-byte archive at SHA-256
   `8c706008bcb11c34bf33a3f8f78711c79f7bb49de8a22d74df6b10e1203c013e`;
3. rejects unsafe archive members and extracts exactly 34 original regular files into a new
   ignored `.build-temp/<id>/source/` tree;
4. rehashes the complete extracted tree before compilation;
5. locates the installed Visual Studio x64 C toolset without recording its local path;
6. invokes the twelve-source production list from the original `Makefile.am` with deterministic
   environment and compiler flags;
7. writes raw and normalized local evidence below ignored `.build-output/<id>/`;
8. reverifies every extracted source byte; and
9. reruns preservation verification even after a compiler failure.

The original GNU Autotools route is preferred in principle but unavailable in the recorded A2
environment: no GCC, MinGW-w64, Clang, GNU make, or complete MSYS2 toolchain is installed.
MSVC is therefore the only existing native Windows AMD64 compiler candidate. The direct external
driver is explicitly allowed by the A2 unmodified-source definition; it is not represented as an
Autotools build.

Run two attempts from Windows PowerShell:

```powershell
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass `
    -File .\build-support\windows-x64\build.ps1 -BuildId build-a
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass `
    -File .\build-support\windows-x64\build.ps1 -BuildId build-b
```

Each build identifier is single-use. The driver refuses to reuse an extraction or output path.
Only remove a task-created `.build-temp/<id>/` and `.build-output/<id>/` directory after first
confirming its exact repository-local path.

Exit codes are:

| Code | Meaning |
|---:|---|
| `0` | The executable, PE inspection, and smoke path completed |
| `10` | Untouched source failed to compile or link |
| `20` | Authentication, tool discovery, driver, or post-build preservation failed |

The current versioned result is in
[`../../manifests/windows-x64-unmodified-build-v1.json`](../../manifests/windows-x64-unmodified-build-v1.json).
Local logs and executables are evidence only, remain ignored, and must never be staged or
published.
