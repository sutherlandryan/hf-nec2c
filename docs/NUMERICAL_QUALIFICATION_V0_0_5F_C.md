# NEC2 maintained-source v2 frozen-corpus rerun

## Disposition

Milestone: **v0.0.5f-C — maintained NEC2C source v2 and frozen-corpus rerun**.

Outcome:

**B. V2 SOURCE FIX VALIDATED; QUALIFICATION REMAINS BLOCKED BY THE FROZEN REFERENCE MISMATCH.**

The exact four-line `zint()` source-fidelity correction passed direct compiled testing,
independent source reconstruction, fresh MSYS and native UCRT64 builds, every declared
cross-platform comparison, every invariant, and the complete frozen eight-case corpus rerun. The
only remaining qualification blocker is the already frozen official Example 2 feed-current
imaginary literal.

This outcome does **not** qualify the solver, make it release-ready, approve a binary or
distribution, create a v2 tag, or authorize HF Propagation Control integration. The v1 manifest,
patch, documentation, and tag remain preserved; the v1 tag still targets
`05f9a4f7ad9a089e45459db9099e47e0bf4533c2`.

## Frozen baseline and unchanged policy

The rerun used the exact eight case definitions, deck identities, authoritative expected
literals, tolerances, evidence hierarchy, parser classifications, and comparison rules frozen in
[`numerical-qualification-v0.0.5f-b.json`](../manifests/numerical-qualification-v0.0.5f-b.json).
Neither that manifest nor the existing
[`v0.0.5f-B result summary`](../manifests/numerical-qualification-v0.0.5f-b-results.json) changed.

The normalized v2 wrapper result is
[`numerical-qualification-v0.0.5f-c-results.json`](../manifests/numerical-qualification-v0.0.5f-c-results.json).
No expected value was replaced, no tolerance was widened, and internal NEC2DX remained secondary
diagnostic evidence only.

The complete runner invocation was equivalent to:

```text
py -3.13 -B tools\qualification\run_qualification.py --manifest manifests\numerical-qualification-v0.0.5f-b.json --msys-results <v2-msys-results> --ucrt64-results <v2-ucrt64-results> --nec2dx-results <nec2dx-results> --repository-root . --output <ignored-full-result> --summary-output <ignored-base-summary>
```

The runner returned its expected nonzero status because the sole frozen authoritative failure
remained. That status is evidence of preserving the gate, not a runner or report-integrity error.

## Source and build identities

The tested source was `HF_NEC2C_MAINTAINED_SOURCE_V2`: 36 regular files and 788,941 bytes. Its
complete combined patch is 7,624 bytes with SHA-256
`9b165d93e4e3335f4c2762c70950a7086d1f6c7ee0559a1f3f3f5c08f6219e52`. Independent fresh
reconstruction from the authenticated original archive matched every file, byte, and hash with
no missing, extra, normalized, or reparse-point path. See the
[maintained-source v2 record](MAINTAINED_SOURCE_V2.md).

| Build | Compiler identity | Executable identity | Runtime boundary |
|---|---|---|---|
| MSYS POSIX | GCC 15.3.0, `x86_64-pc-cygwin`; SHA-256 `4bd76635b6053a7926f4579a30f9c800a673632fd10b4d6adf8083d3eda1b80c` | 335,509 bytes; SHA-256 `ef0dac79e1416a066f7e7ccb1416ddc8124a85beae205b89af319e3fe6877adc` | PE32+ x86-64; `msys-2.0.dll`, `msys-gcc_s-seh-1.dll`, and `KERNEL32.dll` |
| Native UCRT64 | GCC 16.1.0, `x86_64-w64-mingw32`; SHA-256 `f96a3bdb1d3a3967b309d75c7413399391e857b5be4cb17162572ed66f6772a0` | 439,729 bytes; SHA-256 `c96228b4aa301408f5b47647fe5951f951dc42da2256787cf1ae2af2645e97fc` | PE32+ x86-64; UCRT and `KERNEL32.dll`; no `msys-2.0.dll` |

The project-authored direct harness invoked the actual compiled `zint()` implementation under
both toolchains. All 12 requested regime and boundary values passed. Small- and large-regime
results matched at exact binary64 precision; each medium-regime component met
`abs(error) <= 1e-11 + 5e-12 * abs(reference)`. The `x = 8`, `x = 110`, and `x = 110.001`
boundaries selected small, medium, and large respectively. Mutation guards rejected removal of
either return, reversion of `cc5`, and re-aliasing of `cn` to `cc14`.

## Complete corpus result

All 24 solver reports passed integrity: each of the eight cases had complete, diagnostic-free
MSYS, UCRT64, and NEC2DX reports. The runner classified 6,392 normalized check records:

| Classification | v0.0.5f-B | v0.0.5f-C |
|---|---:|---:|
| `PASS` | 5,981 | 6,028 |
| `PASS_WITH_REFERENCE_PRECISION_LIMIT` | 26 | 29 |
| `FAIL` | 8 | 1 |
| `SECONDARY_DISAGREEMENT` | 43 | 0 |
| `NOT_APPLICABLE` | 334 | 334 |

Every cross-platform record and every invariant passed. Both convergence trends and every power
conservation check passed. There was no secondary disagreement. All previously resolved
authoritative checks remained resolved.

For each primary implementation, all seven unaffected cases were exactly equal between the
complete parsed v1 and v2 reports. In Example 2, snapshots 0 through 2 were also exactly equal;
snapshot 3, the loaded `LD` type 5 state, was the only changed snapshot. Thus no new discrepancy
appeared outside the intended corrected branch.

## Example 2 loaded-state comparison

The v2 MSYS and native UCRT64 reports passed every frozen cross-platform comparison. The frozen
v1 baseline and v2 loaded-state values are:

| Observable | Preserved v1 result | Maintained v2 result |
|---|---:|---:|
| Feed impedance | `106.58 + j68.538 ohm` | `112.43 + j65.428 ohm` |
| Feed current | `6.6377e-3 - j4.2683e-3 A` | `6.6443e-3 - j3.8666e-3 A` |
| Input power | `3.3188e-3 W` | `3.3222e-3 W` |
| Radiated power | `2.5716e-3 W` | `2.4402e-3 W` |
| Structure loss | `7.4727e-4 W` | `8.8199e-4 W` |
| Efficiency | `77.48%` | `73.45%` |

The v2 power balance passes the unchanged conservation policy. Internal NEC2DX agrees with the
v2 loaded-state values at the recorded report precision and has no remaining secondary
disagreement, but it remains a secondary diagnostic and cannot override the official reference.

## Sole remaining frozen mismatch

The official Example 2 feed-current imaginary component is:

```text
-3.86680E-03 A
```

Both maintained v2 primary builds and internal NEC2DX report approximately:

```text
-3.8666E-03 A
```

The frozen published-precision comparison classifies that one record as `FAIL`. Its cause remains
unresolved. This milestone does not widen a tolerance, replace or relabel the official literal,
declare a publication error, patch unrelated solver code, or begin a new investigation of the
value.

## Production and provenance boundary

The tracked result is a compact project-authored summary. Executables, objects, raw reports,
compiler products, manuals, images, DLLs, NEC2DX source, and build directories remain outside the
tracked source. The maintained solver remains unreleased and unapplied. No distribution, release,
maintained-source v2 tag, or HF Propagation Control integration is approved.

## Exact next milestone

The exact recommended next milestone is independent review and merge of this v2
source-fix/requalification pull request. Do not create or move a maintained-source v2 tag before
merge. Release and HF Propagation Control integration remain deferred pending resolution of the
frozen reference mismatch.
