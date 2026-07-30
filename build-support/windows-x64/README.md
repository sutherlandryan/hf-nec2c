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
5. selects the pinned Visual Studio 2019, MSVC v142, and Windows SDK identities without
   recording their local paths;
6. invokes the twelve-source production list from the original `Makefile.am` with deterministic
   environment and compiler flags;
7. records the driver, source guard, tool binaries, arguments, runtime, exit, and post-compile
   artifact inventory and writes unnormalized and normalized local diagnostics below ignored
   `.build-output/<id>/`;
8. reverifies every extracted source byte; and
9. reruns preservation verification even after a compiler failure.

The source guard and driver are correctness controls for a non-adversarial local workspace, not
an operating-system security sandbox. They reject persistent path, link, inventory, and byte
contradictions, but cannot prevent a concurrent local process with the same user permissions
from replacing or mutating paths before, during, or between checks. Process timeouts use bounded
best-effort Windows process-tree termination and make any timeout, stream-drain uncertainty, or
termination failure a driver validation failure rather than canonical A2 evidence. Trusted local
tools are assumed not to spawn detached descendants; a process that escapes the targeted tree
remains outside the claimed boundary. Captured output is held in memory, so this driver is scoped
to the fixed authenticated A2 inputs and trusted installed tools, not arbitrary noisy commands.

If extraction or verification fails after creating the fresh destination, the partial
`.build-temp/<id>/source/` tree is deliberately retained for diagnosis and the identifier remains
burned. The guard does not race an untrusted workspace by recursively cleaning a path that may
have been replaced. Inspect and remove only that exact task-created directory under the manual
cleanup rule below.

The original GNU Autotools route is preferred in principle but unavailable in the recorded A2
environment: no GCC, MinGW-w64, Clang, GNU make, or complete MSYS2 toolchain is installed.
MSVC is therefore the only existing native Windows AMD64 compiler candidate. The direct external
driver is explicitly allowed by the A2 unmodified-source definition; it is not represented as an
Autotools build.

Run two attempts from Windows PowerShell:

```powershell
$stamp = Get-Date -Format yyyyMMddHHmmss
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass `
    -File .\build-support\windows-x64\build.ps1 -BuildId "manual-a-$stamp"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass `
    -File .\build-support\windows-x64\build.ps1 -BuildId "manual-b-$stamp"
```

Each build identifier is single-use. The driver refuses to reuse an extraction or output path.
Only remove a task-created `.build-temp/<id>/` and `.build-output/<id>/` directory after first
confirming its exact repository-local path.

Invalid, reserved-device, or colliding identifiers are pre-attempt refusals. They return `20`,
rerun preservation verification when the repository is available, and do not overwrite or add
an attempt record below an existing output path.

Exit codes are:

| Code | Meaning |
|---:|---|
| `0` | The executable, PE inspection, and smoke path completed |
| `10` | Untouched source failed to compile or link |
| `20` | Authentication, tool discovery, timeout/termination, capture, driver, or post-build preservation failed |

The current versioned result is in
[`../../manifests/windows-x64-unmodified-build-v1.json`](../../manifests/windows-x64-unmodified-build-v1.json).
Local logs and executables are evidence only, remain ignored, and must never be staged or
published.
