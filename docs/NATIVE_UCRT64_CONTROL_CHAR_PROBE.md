# Native UCRT64 parser-control-character probe

## Task class and exact question

**RECONNAISSANCE.** After applying the already validated process-timing and
signal-registration patches, does replacing NEC2C's global `CR` and `LF` parser macros with
local, namespaced parser constants:

1. preserve the complete accepted MSYS output; and
2. allow native UCRT64 NEC2C to compile, link, and run?

If native UCRT64 reached another source, linker, or runtime blocker, this task was required to
record only the first proven blocker and stop. This work does not create maintained source and
is not numerical qualification, release engineering, reproducible-build work, structured-output
work, or HF Propagation Control integration.

Starting clean synchronized `main` was
`60eadaeefc3dfebe0875a07a1c746e5a6c075b49`. It contained the merged reviewed PR #6 content
formerly headed by `73eade522b9fe4379e04d8940909a64ac05f16bf`.

## Validated patch chain and candidate identity

Every candidate and build tree began with a fresh extraction authenticated by the existing source
guard. The two committed prerequisite patches were applied in this order from their exact
committed LF byte streams:

| Order | Patch | SHA-256 |
|---:|---|---|
| 1 | [`portable-process-timing-v1.patch`](../probes/portable-process-timing-v1.patch) | `f65347275a21bbdc90b009aec4fb9db10a2918ac33a77be30809fb1db57b8aae` |
| 2 | [`portable-signal-registration-v1.patch`](../probes/portable-signal-registration-v1.patch) | `6fc3f4b63eef0a90ae7a78708aa77bca01da802864a1cd1b6fc85091027e27af` |

After those two patches, the complete changed-source inventory was exactly:

```text
M main.c
M misc.c
M nec2c.h
A platform_signal.h
A platform_time.h
```

The tested parser candidate was made by one deterministic Python standard-library raw-byte
editor. It required every intended source sequence exactly once, used
`Path.read_bytes()` and `Path.write_bytes()`, and modified only `misc.c` and `nec2c.h`.
The candidate removed the two global macros, added `NEC2C_CR` and `NEC2C_LF` in a file-scope
enum immediately after the local include block in `misc.c`, and renamed only executable
comparisons in `load_line()`. The constants retain the exact numeric values `0x0d` and `0x0a`;
`load_line()` control flow, CR input behavior, LF input behavior, CRLF input behavior, EOF behavior,
whitespace handling, file modes, normal output, and all electromagnetic calculations are unchanged.

The exact tested candidate identities were:

| Path | Before bytes | Before SHA-256 | Candidate bytes | Candidate SHA-256 |
|---|---:|---|---:|---|
| `misc.c` | 5,485 | `9033e9635c5ec7d22d9cbc6c46588e5b49987cc88b9a02607e3d347837760403` | 5,581 | `63433ce16cf5627e6d986d9cb702ca39ba7041d7795f90454e1606c0a83b9f02` |
| `nec2c.h` | 14,612 | `233f36230455675e8ca7db49bdbaececc067dec3bf13e11e0c7859acf32ff003` | 14,580 | `089e65709686a0130a77435bc397b7f221da51c299d48582a141bd8fd6dc9293` |

Both files retained exactly two terminal LF bytes and byte-identical final 128-byte suffixes.
The staged diff had no third path, EOF-only hunk, unrelated formatting or whitespace change,
absolute path, input-buffer change, or timing/signal change.

The final project-authored patch is
[`portable-parser-control-chars-v1.patch`](../probes/portable-parser-control-chars-v1.patch):

- bytes: 1,570
- SHA-256: `d010c3d04a78537b03f717674947fd610747e9c347845d4a109cb2595e459283`
- exact paths: `misc.c`, `nec2c.h`

A further fresh authenticated extraction accepted the timing patch, signal patch, and then this
patch with `git apply --check --whitespace=error-all`. Applying it reproduced both candidate
hashes exactly.

## Complete CR/LF token inventory

A case-sensitive word-boundary search covered all 14 preserved `.c` and `.h` files. It found
10 complete identifier occurrences on seven source lines. No uppercase `CR` or `LF` token
occurred in a comment, another source file, or another semantic role.

| Token | Path | Line | Classification | Exact preserved source line |
|---|---|---:|---|---|
| `CR` | `nec2c.h` | 77 | definition | `#define<TAB>CR<TAB>0x0d` |
| `LF` | `nec2c.h` | 78 | definition | `#define<TAB>LF<TAB>0x0a` |
| `CR` | `misc.c` | 132 | code use in `load_line()` | `<TAB>  (chr == CR ) ||` |
| `LF` | `misc.c` | 133 | code use in `load_line()` | `<TAB>  (chr == LF ) )` |
| `CR` | `misc.c` | 136 | code use in `load_line()` | `<TAB>while( (chr != CR) && (chr != LF) )` |
| `LF` | `misc.c` | 136 | code use in `load_line()` | `<TAB>while( (chr != CR) && (chr != LF) )` |
| `CR` | `misc.c` | 141 | code use in `load_line()` | `<TAB>while( (chr == CR) || (chr == LF) )` |
| `LF` | `misc.c` | 141 | code use in `load_line()` | `<TAB>while( (chr == CR) || (chr == LF) )` |
| `CR` | `misc.c` | 150 | code use in `load_line()` | `<TAB>if( (chr == CR) || (chr == LF) )` |
| `LF` | `misc.c` | 150 | code use in `load_line()` | `<TAB>if( (chr == CR) || (chr == LF) )` |

Lowercase prose such as `lf/cr` and the unrelated lowercase local variable `cr` in
`fields.c` are not occurrences of the case-sensitive C identifiers.

## Patched MSYS result

An independent fresh authenticated tree reproduced all five expected patched source hashes. Its
disposable nested Git repository reported exactly the required `M/M/M/A/A` inventory and
`git diff --check` passed before the nested `.git` directory was removed.

The one authorized build used `MSYSTEM=MSYS`, `/usr/bin/gcc`, the shipped `configure`, and
`/usr/bin/make -j1`:

- `configure`: exit `0`
- `make -j1`: exit `0`
- objects linked: 12
- `nec2c -v`: exit `0`
- `nec2c -h`: exit `0`
- processed minimal-dipole run: exit `0`
- report logical lines: 119
- report bytes: 6,825
- report SHA-256: `396b90cfb8e49fcf1938e01d291638163f74e3b065e29b8456ece3b3ca482567`

The first smoke orchestration used an overlong temporary output pathname. NEC2C rejected that
pathname before processing the deck with exit `254` and
`Output file name too long - aborting`. This permitted path mistake was corrected by using
`-oprobe.out`; no rebuild occurred, the successful version and help checks were not repeated,
and exactly one minimal-dipole execution processed the deck.

The corrected report was byte-for-byte identical to the complete accepted MSYS report. No timing
or non-timing line differed. This is a bounded regression result, not numerical qualification.

## Patched native UCRT64 result

Only after the MSYS gate passed, a second independent fresh authenticated tree reproduced the same
five patched source hashes and exact `M/M/M/A/A` inventory. The one authorized native build
used `MSYSTEM=UCRT64`, `/ucrt64/bin/gcc`, the shipped `configure`, and
`/usr/bin/make -j1`, with `TEMP`, `TMP`, and `TMPDIR` bound to installed MSYS `/tmp`.

- `configure`: exit `0`
- `make -j1`: exit `0`
- translation units compiled: 12
- objects linked: 12
- linking reached: yes
- executable produced: yes
- `nec2c -v`: exit `0`
- `nec2c -h`: exit `0`
- minimal-dipole run: exit `0`

The ignored, untracked native executable was:

- bytes: 436,657
- SHA-256: `4da7ab8b9b1d5f0c064363e9a18e04a2a3abea390cbb657d189e4ad06e9a0a46`
- format: PE32+ AMD64 (`pei-x86-64`, `i386:x86-64`)
- imported DLLs:
  - `KERNEL32.dll`
  - `api-ms-win-crt-convert-l1-1-0.dll`
  - `api-ms-win-crt-environment-l1-1-0.dll`
  - `api-ms-win-crt-heap-l1-1-0.dll`
  - `api-ms-win-crt-locale-l1-1-0.dll`
  - `api-ms-win-crt-math-l1-1-0.dll`
  - `api-ms-win-crt-private-l1-1-0.dll`
  - `api-ms-win-crt-runtime-l1-1-0.dll`
  - `api-ms-win-crt-stdio-l1-1-0.dll`
  - `api-ms-win-crt-string-l1-1-0.dll`

It does not import `msys-2.0.dll`.

The native report had:

- raw bytes: 6,943
- raw SHA-256: `1a9baf6a9a2954f77ccd543d1739ff97caf6b748a255b00bf149fbb2c3fd671c`
- CRLF sequences: 118
- bare CR bytes: 0
- logical lines: 119

Normalizing only CRLF to LF produced 6,825 bytes and SHA-256
`396b90cfb8e49fcf1938e01d291638163f74e3b065e29b8456ece3b3ca482567`, exactly matching the
complete patched MSYS report. The timing output sites are source-established in `main.c` for
`FILL`/`FACTOR` and `TOTAL RUN TIME`; those lines did not differ in this run. There was no
first non-timing difference: every logical line, line order, and report structure matched.

No subsequent compiler, linker, or runtime blocker was reached.

## Preservation and scope result

Before and after each build, the archive remained 186,124 bytes with SHA-256
`8c706008bcb11c34bf33a3f8f78711c79f7bb49de8a22d74df6b10e1203c013e`.
The preservation verifier passed, all 34 preserved regular files and 786,583 extracted bytes
remained authenticated, and no preserved byte or immutable archival/preservation tag changed.
All 36 files in each patched source set retained their expected hashes after its build.

No package command or package operation occurred. No MSYS2 configuration or global Windows
`PATH` changed. No maintained source tree, build driver, JSON manifest, package inventory,
structured output, committed log, object, executable, package archive, release artifact,
reproducibility infrastructure, or full test suite was created. HF Propagation Control remained
clean and read-only.

## Result and exact next decision

**YES.** Replacing the global parser macros with local namespaced constants preserved the complete
accepted MSYS report and allowed native UCRT64 NEC2C to compile, link, and run all three bounded
smoke cases. The native report differs in raw bytes only because native text output uses CRLF;
after CRLF-to-LF normalization it is byte-identical to the MSYS report. No subsequent blocker was
reached.

This result proves only the narrow portability and smoke question. It does not establish
numerical qualification, reproducible builds, release readiness, distribution approval,
structured-output readiness, or HF Propagation Control integration.

The exact next decision is whether to authorize a separate, explicitly scoped native UCRT64
numerical-qualification job against an approved reference suite. Until such work is separately
authorized and completed, keep this as a reconnaissance patch artifact and do not integrate,
distribute, or describe the executable as qualified.
