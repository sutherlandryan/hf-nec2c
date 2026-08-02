# Native UCRT64 signal-registration probe

## Task class and exact question

**RECONNAISSANCE.** After the validated portable process-timing patch is applied, does one
minimal signal-registration portability boundary:

1. preserve normal NEC2C output under the working MSYS POSIX baseline; and
2. allow the native UCRT64 build to compile, link, and run?

If UCRT64 reached another source, linker, or runtime blocker, the task was required to identify
the first proven blocker and stop. This work does not create maintained source, perform numerical
qualification, or perform release engineering.

Starting `main` and the clean existing branch
`agent/nec2c-native-signal-probe` were both exactly
`181022373c725dc4acbc3f9b6c6770110de43641`, the merge of PR #5.

## Patch identities and candidate scope

The committed process-timing patch was authenticated from its committed LF byte stream before
every use:

- path: `probes/portable-process-timing-v1.patch`
- SHA-256: `f65347275a21bbdc90b009aec4fb9db10a2918ac33a77be30809fb1db57b8aae`
- exact paths: `misc.c`, `nec2c.h`, and `platform_time.h`

The tested signal candidate was produced by one deterministic Python standard-library raw-byte
editor. It required every source sequence exactly once, retained LF bytes, preserved the two
terminal LF bytes and final unchanged 128-byte suffix of `main.c`, and changed exactly:

```text
M main.c
A platform_signal.h
```

The tested candidate identities were:

| Path | Bytes | SHA-256 |
|---|---:|---|
| `main.c` | 48,268 | `8648f01c636c802f24f231a2827fac988da07f677a4fdfcc6a8b2fa21c6881d5` |
| `platform_signal.h` | 1,231 | `85b6abcb4301e2db32110c9599e31e8a7a86ae279f80f45cd76df6876c1cefd8` |

Independent fresh authenticated MSYS and UCRT64 trees reproduced those identities exactly after
the unchanged timing patch was applied. The other timing-patched file identities also matched
exactly in both trees:

| Path | Bytes | SHA-256 |
|---|---:|---|
| `misc.c` | 5,485 | `9033e9635c5ec7d22d9cbc6c46588e5b49987cc88b9a02607e3d347837760403` |
| `nec2c.h` | 14,612 | `233f36230455675e8ca7db49bdbaececc067dec3bf13e11e0c7859acf32ff003` |
| `platform_time.h` | 599 | `2b2af7ef1309d60f018d383a9f1d5f9a721b68478ab0a8ea37581e70ad9522db` |

The final signal patch was generated only after valid build results existed, directly from the
exact staged tested candidate with `git diff --cached --binary --full-index` captured and
written as raw bytes:

- path: [`../probes/portable-signal-registration-v1.patch`](../probes/portable-signal-registration-v1.patch)
- bytes: 2,624
- SHA-256: `6fc3f4b63eef0a90ae7a78708aa77bca01da802864a1cd1b6fc85091027e27af`
- exact paths: `main.c` and `platform_signal.h`

One more fresh authenticated extraction accepted the timing patch and then
`git apply --check --whitespace=error-all` accepted the signal patch. Applying it reproduced the
two tested candidate hashes exactly.

## Signal boundary

The candidate preserves the existing `sig_handler(int signal)`, handled signal set, handler
messages, cleanup behavior, and exit behavior. It registers exactly `SIGINT`, `SIGSEGV`,
`SIGFPE`, `SIGTERM`, and `SIGABRT`.

MSYS and Cygwin retain the original `struct sigaction`, `sigemptyset()`, `sa_flags = 0`, and
`sigaction()` behavior, including the old-action pointer for `SIGINT` and null old-action
arguments for the other four signals. Native MinGW/UCRT64 uses ISO C `signal()` for the same
handler and five signal constants. Any native `SIG_ERR` result returns failure to `main`,
which emits one concise project-authored diagnostic and returns `EXIT_FAILURE`.

The BSD-2-Clause header identifies itself as a reconnaissance candidate that is not maintained
source and is not qualified for distribution. It contains no numerical logic. The patch adds no
Windows console-control API, timing, CLI, filesystem, exit-policy normalization, numerical,
output-format, or Autotools change.

## Patched MSYS result

The independent patched MSYS tree used `MSYSTEM=MSYS`, `/usr/bin/gcc`, the shipped
`configure`, and `/usr/bin/make -j1`.

- `configure`: exit `0`
- `make -j1`: exit `0`
- objects linked: 12
- `nec2c -v`: exit `0`
- `nec2c -h`: exit `0`
- one minimal-dipole run: exit `0`
- report lines: 119
- report bytes: 6,825
- report SHA-256: `396b90cfb8e49fcf1938e01d291638163f74e3b065e29b8456ece3b3ca482567`

The complete report, including both source-established timing lines, matched the accepted MSYS
POSIX baseline byte-for-byte. Successful normal NEC2C output did not change. This bounded
regression comparison is not numerical qualification.

## Patched UCRT64 result

The independent native tree used `MSYSTEM=UCRT64`, `/ucrt64/bin/gcc`, the shipped
`configure`, and `/usr/bin/make -j1`.

An initial orchestration invocation stripped the temporary-directory variables. Native `g++`
therefore attempted to create a temporary file in unwritable `C:\WINDOWS`, and `configure`
exited 77 before a valid compiler test or NEC2C compilation. That invocation is not treated as
source/compiler evidence. Its sole generated `config.log` was removed, all 36 patched-source
hashes and preservation were reverified, and the environment was corrected only by binding
`TEMP`, `TMP`, and `TMPDIR` to installed MSYS `/tmp`.

The valid native result was:

- `configure`: exit `0`
- `make -j1`: exit `2`
- first failing translation unit: `misc.c`
- first proven source blocker: original `nec2c.h:76`, `#define CR 0x0d`
- conflicting native declaration: `C:\msys64\ucrt64\include\winnt.h:8885`,
  `DWORD CR : 2;`
- first diagnostic: `error: expected identifier or '(' before numeric constant`
- object files produced: 9
- linking reached: no
- executable produced: no

The nine objects were `calculations.o`, `fields.o`, `geometry.o`, `ground.o`, `input.o`,
`main.o`, `matrix.o`, `network.o`, and `shared.o`. Production of `main.o` proves that
the narrow signal boundary advanced compilation beyond the prior unavailable
`struct sigaction` blocker. Compilation then stopped when the original `CR` macro expanded
against the native Windows header bit-field while compiling the timing-patched `misc.c`.
No fix was attempted, linking was not reached, and no native smoke or PE/import inspection was
possible.

## Preservation and scope result

Before and after each valid build, the preservation verifier authenticated the 186,124-byte
archive at SHA-256
`8c706008bcb11c34bf33a3f8f78711c79f7bb49de8a22d74df6b10e1203c013e`, verified all 34
original preserved files and 786,583 extracted bytes, rejected missing or extra preserved files,
and confirmed that no preserved byte changed. All 36 files in each patched source set retained
their independently established hashes after its build.

The authorization performed one tested candidate, one valid patched MSYS build/smoke, and one
valid patched UCRT64 compiler attempt. No package command, package inventory, full test suite,
maintained source tree, build driver, JSON manifest, committed log, executable, object file,
release artifact, numerical qualification, or release engineering was added to the repository.
`C:\hf-prop-control` remained clean and read-only at
`ac231157b218415598f9d8a389492bef11d0a5a6`.

## Result and exact next decision

**NO.** The minimal signal-registration boundary preserved the complete normal MSYS output and
advanced native UCRT64 compilation beyond `struct sigaction`, but UCRT64 did not compile, link,
or run. The first new proven blocker is the original `CR` macro at `nec2c.h:76` colliding with
the `CR` bit-field in native `winnt.h:8885` while compiling `misc.c`.

The exact next decision is whether to authorize a separate **RECONNAISSANCE** job for one narrow
native Windows header/macro-collision boundary. It should preserve the original `CR` semantics
and the accepted MSYS output, test only one native build, and stop at the first subsequent
compiler, linker, or runtime blocker. It must not expand into maintained source, numerical
qualification, distribution, or release engineering.
