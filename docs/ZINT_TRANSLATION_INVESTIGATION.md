# NEC2C `zint()` translation investigation

## Decision

**Disposition: C. ZINT DISCREPANCY NOT FULLY EXPLAINED.**

The original NEC-2 control flow selects exactly one impedance approximation. The maintained C
translation lost the two transfers to the common final assignment, so every `x <= 110` result is
eventually overwritten by the large-`x` approximation. Restoring only those transfers reproduces
the authenticated Fortran `ZINT` values to floating-point precision and explains the principal
Part III Example 2 `LD 5` discrepancy at `x ~= 2.97`.

That result is not a numerical requalification. Under the already-frozen published-decimal policy,
the control-flow candidate passes 17 of the 18 Example 2 checks. Its feed-current imaginary literal,
`-3.8666E-03 A`, remains disjoint from the official `-3.86680E-03 A` half-LSD interval. The same
candidate value is produced by authenticated internal NEC2DX. Because the complete authoritative
observable set is not restored, disposition A would overstate the result. Variant B produces the
same 316 parsed Example 2 observables as Variant A, so disposition B is also unsupported.

The maintained source, frozen cases, manifests, results, and maintained-source identity were not
changed. The existing **C. NUMERICAL QUALIFICATION BLOCKED** disposition remains in force.

## Question and bounds

The exact question was:

> What exact NEC2-to-C translation defects exist in the maintained `zint()` circular-wire
> internal-impedance routine, which defects cause the frozen Part III Example 2 `LD 5` failure, and
> what is the smallest scientifically justified source correction and regression plan?

The investigation was limited to `LD` type 5 and `zint()`. It used ignored diagnostic copies,
harnesses, builds, and reports. It did not alter [`src/nec2c/`](../src/nec2c/), the qualification
corpus, expected values, manifests, frozen results, archive, upstream material, patches, or tags. It
did not run the full eight-case corpus, qualify a solver, authorize a release, or integrate anything
with HF Propagation Control.

The starting repository state was clean `main` at
`ea120620a4debd0ce1e0b354a61421dbd91d365d`; freshly fetched `origin/main` was identical. That commit
contains qualification commit `6250d238d411a97fdef5f9af1cd4a3426876c1ad`, and PR #13 was already
merged. The investigation ran on branch `agent/zint-translation-investigation`.

## Authorities and identities

| Evidence | Authenticated identity | Use and limit |
|---|---|---|
| Official NTIS scan for *Numerical Electromagnetics Code (NEC) - Method of Moments, Part III: User's Guide*, record `ADA956129` | [NTIS record](https://ntrl.ntis.gov/NTRL/dashboard/searchResults/titleDetail/ADA956129.xhtml); PDF 17,527,148 bytes and 730 pages; SHA-256 `0bb280883b2b17fafb1bbd6a1504dcbf645e49cd8a7c8bd02424b5cea8a3d9e6`; embedded Part II `ZINT` listing on PDF page 458, printed Part II page 354 | Primary authority for the original literals, expressions, labels, and transfers. The image-only page was rendered and visually checked. |
| Internal NEC2DX source | [FUNET `nec2dx.tar`](https://www.nic.funet.fi/pub/ham/antenna/NEC/nec2dx.tar), 262,656 bytes, SHA-256 `ad20c15a8cb594b19928595c853eca2b576c875c45c39a45eeaf26ee1be79774`; extracted `nec2dx.f`, 257,436 bytes, SHA-256 `ca2ffebef9fb928d17e1eedcaa6f87b7bd61125a5f1abe19227d3f8251d9b293` | Independent source trace and secondary runtime diagnostic only; it is not a qualification oracle. No third-party bytes are tracked. |
| Maintained C routine | [`src/nec2c/calculations.c`](../src/nec2c/calculations.c), blob `aaf12987dd4e6b0204a5accaf828982dd57873f9`, file SHA-256 `868bfecee7bbd2b1f555852b3a11f7940e732aa088a3c31a1faeb36a3d188d00` | Investigation subject. The blob is unchanged between the maintained-source tag and the starting commit. |
| Maintained-source tag | annotated tag `maintained/nec2c-1.3.1-hf-portability-v1`: tag object `1ca11974e247407b41f47d0a9d2a6288d172dd86`, target `05f9a4f7ad9a089e45459db9099e47e0bf4533c2` | Preserved identity; unchanged by this investigation. |
| Frozen Example 2 deck | [`nec2-part3-example2-conductivity-sweep.nec`](../tests/qualification/cases/nec2-part3-example2-conductivity-sweep.nec), SHA-256 `39121efd2346da4b136e07901fb9e76b3b54494c47abf91277a3545fd95d95bc` | The unchanged four-snapshot deck used for all end-to-end Example 2 runs. |
| Frozen policy and results | [`numerical-qualification-v0.0.5f-b.json`](../manifests/numerical-qualification-v0.0.5f-b.json) and the [qualification record](NUMERICAL_QUALIFICATION_V0_0_5F_B.md) | Existing published half-LSD and cross-platform policies; neither was adjusted after observing candidate results. |

The official listing and NEC2DX `ZINT` agree on all audited statements and data. This investigation
therefore treats their shared branch semantics and literals as independently authenticated.

## Complete control-flow trace

The `LD 5` call mapping is exact: NEC2DX calls
`ZINT(ZLR(ISTEP)*WLAM,BI(I))`, while maintained C calls
`zint(zlr[istepx]*data.wlam,data.bi[i],&zt)`. Fortran `REAL*8` / `COMPLEX*16` map to
C `double` / `complex double`; C returns the complex result through a pointer.

The original listing computes `x = sqrt(TPCMU * SIGL) * ROLAM` and then follows this labeled flow:

| Original statement | Original effect | Maintained C translation | Effective maintained behavior |
|---|---|---|---|
| `IF (X.GT.110.) GO TO 2` | `x > 110` goes directly to the large-`x` approximation. | Outer `if (x <= 110)` skips its body for `x > 110`. | Large approximation executes once; correct. |
| `IF (X.GT.8.) GO TO 1` | Within `x <= 110`, `x > 8` goes directly to the medium approximation. | Inner `if (x <= 8)` runs the small approximation when applicable. | Branch condition is equivalent, but there is no transfer after the small assignment. |
| Small approximation, then `GO TO 3` | `x <= 8` skips the medium and large calculations and reaches the common final scale. | Small approximation assigns `*zint`, then execution continues. | Small, medium, and large calculations all run; the large value is returned. |
| Label `1` medium approximation, then `GO TO 3` | `8 < x <= 110` skips the large calculation and reaches the common final scale. | Medium approximation assigns `*zint`, then execution continues past the outer `if`. | Medium and large calculations run; the large value is returned. |
| Label `2` large approximation | Only `x > 110` forms `BR1 = 0.70710678 - j0.70710678`. | The large calculation is unconditional after the outer `if`. | It overwrites every earlier result. |
| Label `3` common assignment and `RETURN` | Exactly one selected `BR1` is scaled once and returned. | Each block repeats the scale, but the first two lack `return`. | The missing equivalents of both `GO TO 3` transfers are the causal translation defect. |

The intended regimes are therefore exactly:

- `x <= 8`: small polynomial, including the boundary `x = 8`;
- `8 < x <= 110`: medium asymptotic expansion, including `x = 110`;
- `x > 110`: large asymptote.

The current maintained routine returns the large asymptote for all three regimes. For `x <= 8`, it
also needlessly evaluates the medium expressions before the overwrite.

| `x` region | Original selection | Maintained execution | Maintained return |
|---:|---|---|---|
| `x < 8` | small only | small, medium, large | large |
| `x = 8` | small only | small, medium, large | large |
| `8 < x < 110` | medium only | medium, large | large |
| `x = 110` | medium only | medium, large | large |
| `x > 110` | large only | large | large |

## Complete constants and expressions

### Shared scalars and complex constants

| Symbol | Official NEC / NEC2DX | Maintained C | Finding |
|---|---:|---:|---|
| `PI` | `3.1415926D+0` | `3.141592654` | C carries more digits; not a mistranslation. |
| `POT` | `1.5707963D+0` | `1.570796327` | C carries more digits; not a mistranslation. |
| `TP` | `6.2831853D+0` | `6.283185308` | C carries more digits; not a mistranslation. |
| `TPCMU` | `2.368705D+3` | `2.368705e+3` | Exact. |
| `CMOTP` | `60.00` | `60.00` | Exact. |
| `FJ` | `0 + j1` | `CPLX_01 = 0 + j1` | Exact. |
| `CN` | `0.70710678 + j0.70710678` | alias of `cc14`, `0.7071068 + j0.7071068` | Translation defect: two decimal digits were lost by collapsing distinct constants; medium regime only. |
| `cc1` | `6.0e-7 + j1.9e-6` | same | Exact. |
| `cc2` | `-3.4e-6 + j5.1e-6` | same | Exact. |
| `cc3` | `-2.52e-5 + j0` | same | Exact. |
| `cc4` | `-9.06e-5 - j9.01e-5` | same | Exact. |
| `cc5` | `0 - j9.765e-4` | `0 - j9.765e4` | Translation defect: exponent sign lost, a factor of `10^8`; medium regime only. |
| `cc6` | `0.0110486 - j0.0110485` | same | Exact. |
| `cc7` | `0 - j0.3926991` | same | Exact. |
| `cc8` | `1.6e-6 - j3.2e-6` | same | Exact. |
| `cc9` | `1.17e-5 - j2.4e-6` | same | Exact. |
| `cc10` | `3.46e-5 + j3.38e-5` | same | Exact. |
| `cc11` | `5.0e-7 + j2.452e-4` | same | Exact. |
| `cc12` | `-1.3813e-3 + j1.3811e-3` | same | Exact. |
| `cc13` | `-6.25001e-2 - j1.0e-7` | same | Exact. |
| `cc14` | `0.7071068 + j0.7071068` | same | Exact; it is not the original `CN`. |
| large `BR1` | `0.70710678 - j0.70710678` | same | Exact. |

Reducing the longer C `PI`, `POT`, or `TP` values to the shorter original literals is not justified:
the C values are benign precision refinements, not translation defects.

### Small-regime polynomials

With `y = (x / 8)^2` and `s = y^2`, the following are the Horner coefficients from highest
power to constant. Every coefficient, sign, decimal, exponent, multiplier, and ordering is identical
between the official listing, NEC2DX, and maintained C.

| Quantity | Coefficients / outer factors |
|---|---|
| first `BER` | `-9.01e-6, +1.22552e-3, -0.08349609, +2.6419140, -32.363456, +113.77778, -64, +1` |
| first `BEI` | `+1.1346e-4, -0.01103667, +0.52185615, -10.567658, +72.817777, -113.77778, +16`; multiply by `y` |
| second `BER` | `-3.94e-6, +4.5957e-4, -0.02609253, +0.66047849, -6.0681481, +14.222222, -4`; multiply by `y * x` |
| second `BEI` | `+4.609e-5, -3.79386e-3, +0.14677204, -2.3116751, +11.377778, -10.666667, +0.5`; multiply by `x` |

The small-regime ratio is exactly
`BR1 = complex(first BER, first BEI) / complex(second BER, second BEI)`.

### Medium expressions and common scale

| Expression | Official meaning | Audit |
|---|---|---|
| `TH(d)` | `cc1*d^6 + cc2*d^5 + cc3*d^4 + cc4*d^3 + cc5*d^2 + cc6*d + cc7` in Horner form | Structure exact; maintained `cc5` literal is wrong. |
| `PH(d)` | `cc8*d^6 + cc9*d^5 + cc10*d^4 + cc11*d^3 + cc12*d^2 + cc13*d + cc14` in Horner form | Exact. |
| `F(d)` | `sqrt(POT/d) * exp(-CN*d + TH(-8/x))` | Structure exact; maintained `CN` and `cc5` differ. |
| `G(d)` | `exp(CN*d + TH(8/x)) / sqrt(TP*d)` | Structure exact; maintained `CN` and `cc5` differ. |
| medium ratio | with `B2 = j*F(x)/PI`, `(G(x)+B2) / (G(x)*PH(8/x)-B2*PH(-8/x))` | Exact expression and signs. |
| common result | `j * sqrt(CMOTP/SIGL) * BR1 / ROLAM` | Exact scale and assignment in all three C blocks. |

`cc5*d^2` contributes the same exponential factor to `F(x)` and `G(x)` because `d^2` is even.
That factor cancels algebraically from the medium ratio. The wrong exponent can still worsen complex
argument reduction and rounding, but it cannot cause the small-regime Example 2 failure. Restoring
`cc5` alone at `x = 8.001`, while retaining maintained `CN`, changed the binary64 result by only
`-7.1054e-15 + j0`. Restoring `CN` alone changed it by
`-2.1214e-10 - j5.1296e-10`; adding the `cc5` correction after that changed it by about `2.01e-14`
in complex magnitude. Restoring both reduces the per-component difference from authenticated
Fortran near `x = 8.001` from at most `5.17e-10` to at most `9.02e-12`. Neither constant is
evaluated by the intended small branch at `x ~= 2.97`.

Beyond the three documented higher-precision shared scalars and the two authenticated constant
mismatches, no other coefficient, sign, exponent, decimal, complex constant, expression, final
scale, or assignment difference was found.

## Diagnostic variants and builds

All variant source and outputs were ignored and removed after evidence capture. The variants copied
the exact 36-file maintained tree; only `calculations.c` differed as shown below.

| Variant | `calculations.c` SHA-256 | Exact internal diff | Fresh builds |
|---|---|---|---|
| 0 | `868bfecee7bbd2b1f555852b3a11f7940e732aa088a3c31a1faeb36a3d188d00` | None; byte-identical to maintained source. | MSYS GCC 15.3.0; executable SHA-256 `cf6c1d7ffa2be6d51dcea0c825286a75423ebcd87825668a29fbe2837f6a9581`. |
| A | `58a46917994910e007075042174b60a04fbe3e6abe8ab75141787083b0811cd1` | Add `return;` immediately after the small and medium result assignments; no constant changes. | MSYS executable `bcffc5cb7c0164ce8859e21bc717f2995306178c6f8cbf2434d5f352c995de00`; UCRT64 GCC 16.1.0 executable `cd6c692cdcb7185bb059e862d3be315040240ffa21b9a8af426ecbbb46d0b0c5`. |
| B | `b1bb02d1a1c762e881becb1e324c033b1d266c9c9a5a318009d244a12b053e6e` | Variant A plus `cc5: -j9.765e4 -> -j9.765e-4` and a separate `CN = 0.70710678 + j0.70710678`. | MSYS executable `77671e9e10a2696c8188637d1b466a23a3c0f3670921a91c5a0aa436f264f853`. |

The native Variant A executable imports Windows UCRT/KERNEL32 libraries and does not import
`msys-2.0.dll`. Internal NEC2DX was built with GNU Fortran 16.1.0 after exactly the separately
documented `EXTERNAL SECOND` declarations needed for modern compilation; its executable SHA-256 was
`5d8db47e90746d3339498d86e3e8322e28d3916cc0f1a1ac376f68ed5088aa04`. That declaration-only build
is a diagnostic and is not an untouched-source or numerical qualification result.

## Direct `zint()` regime probe

The harnesses compiled the exact C routine body from each ignored variant and the exact
authenticated Fortran function body. They used `SIGL = 1` and
`ROLAM = x / sqrt(2368.705)` so both implementations received equivalent `x`. Values below are the
unrounded binary64 results formatted to 12 significant digits. The branch column is the original
branch that should supply the result.

| x (actual when rounded) | branch | Fortran Re + j Im | Variant 0 Re + j Im | Variant A Re + j Im | Variant B Re + j Im |
|---:|---|---:|---:|---:|---:|
| 0.1 | small | `75398.2620606 + j94.2477539447` | `2665.72972676 + j2665.72972676` | `75398.2620606 + j94.2477539447` | `75398.2620606 + j94.2477539447` |
| 1 | small | `757.892931321 + j94.003444328` | `266.572972676 + j266.572972676` | `757.892931321 + j94.003444328` | `757.892931321 + j94.003444328` |
| 2.97 | small | `111.842723581 + j80.0828646353` | `89.7552096553 + j89.7552096553` | `111.842723581 + j80.0828646353` | `111.842723581 + j80.0828646353` |
| 7.999 (`7.9990000000000006`) | small | `36.4605533606 + j33.0918302492` | `33.325787308 + j33.325787308` | `36.4605533606 + j33.0918302492` | `36.4605533606 + j33.0918302492` |
| 8 | small | `36.4555826039 + j33.0877595146` | `33.3216215845 + j33.3216215845` | `36.4555826039 + j33.0877595146` | `36.4555826039 + j33.0877595146` |
| 8.001 | medium | `36.4506088573 + j33.0836797236` | `33.3174569024 + j33.3174569024` | `36.4506088575 + j33.0836797241` | `36.4506088573 + j33.0836797236` |
| 20 | medium | `13.8123370906 + j13.3152283354` | `13.3286486338 + j13.3286486338` | `13.8123370906 + j13.3152283354` | `13.8123370906 + j13.3152283354` |
| 50 | medium | `5.40765696704 + j5.33063664541` | `5.33145945353 + j5.33145945353` | `5.40765696704 + j5.33063664541` | `5.40765696704 + j5.33063664541` |
| 109.999 (`109.99899999999998`) | medium | `2.43906618645 + j2.42333657333` | `2.42341269172 + j2.42341269172` | `2.43906618645 + j2.42333657333` | `2.43906618645 + j2.42333657333` |
| 110 | medium | `2.43904387013 + j2.42331454439` | `2.42339066069 + j2.42339066069` | `2.43904387013 + j2.42331454439` | `2.43904387013 + j2.42331454439` |
| 110.001 | large | `2.42336863007 + j2.42336863007` | `2.42336863007 + j2.42336863007` | `2.42336863007 + j2.42336863007` | `2.42336863007 + j2.42336863007` |
| 200 | large | `1.33286486338 + j1.33286486338` | `1.33286486338 + j1.33286486338` | `1.33286486338 + j1.33286486338` | `1.33286486338 + j1.33286486338` |

Absolute and relative differences below are per complex component against the authenticated Fortran
result. No post-observation pass tolerance is applied.

| x | Variant 0: abs Re (rel); abs Im (rel) | Variant A: abs Re (rel); abs Im (rel) | Variant B: abs Re (rel); abs Im (rel) |
|---:|---:|---:|---:|
| 0.1 | `7.273e+04 (9.646e-01); 2.571e+03 (2.728e+01)` | `0 (0); 0 (0)` | `0 (0); 0 (0)` |
| 1 | `4.913e+02 (6.483e-01); 1.726e+02 (1.836e+00)` | `0 (0); 0 (0)` | `0 (0); 0 (0)` |
| 2.97 | `2.209e+01 (1.975e-01); 9.672e+00 (1.208e-01)` | `0 (0); 0 (0)` | `0 (0); 0 (0)` |
| 7.999 | `3.135e+00 (8.598e-02); 2.340e-01 (7.070e-03)` | `0 (0); 0 (0)` | `0 (0); 0 (0)` |
| 8 | `3.134e+00 (8.597e-02); 2.339e-01 (7.068e-03)` | `0 (0); 0 (0)` | `0 (0); 0 (0)` |
| 8.001 | `3.133e+00 (8.596e-02); 2.338e-01 (7.066e-03)` | `2.211e-10 (6.067e-12); 5.167e-10 (1.562e-11)` | `9.017e-12 (2.474e-13); 3.737e-12 (1.130e-13)` |
| 20 | `4.837e-01 (3.502e-02); 1.342e-02 (1.008e-03)` | `0 (0); 1.776e-15 (1.334e-16)` | `3.553e-15 (2.572e-16); 0 (0)` |
| 50 | `7.620e-02 (1.409e-02); 8.228e-04 (1.544e-04)` | `0 (0); 8.882e-16 (1.666e-16)` | `0 (0); 0 (0)` |
| 109.999 | `1.565e-02 (6.418e-03); 7.612e-05 (3.141e-05)` | `0 (0); 0 (0)` | `0 (0); 4.441e-16 (1.833e-16)` |
| 110 | `1.565e-02 (6.418e-03); 7.612e-05 (3.141e-05)` | `4.441e-16 (1.821e-16); 0 (0)` | `8.882e-16 (3.642e-16); 0 (0)` |
| 110.001 | `0 (0); 0 (0)` | `0 (0); 0 (0)` | `0 (0); 0 (0)` |
| 200 | `0 (0); 0 (0)` | `0 (0); 0 (0)` | `0 (0); 0 (0)` |

The original boundary selection is confirmed: `x = 8` uses small and `x = 110` uses medium. At
the same `x = 8`, the medium limit minus the selected small value is
`-4.341963816e-6 - j1.005409670e-5`, a relative complex step of `2.2245e-7`. At the same `x = 110`,
the large limit minus the selected medium value is `-0.01565320944 + j0.00007611630086`, a relative
complex step of `0.0045528`. These are properties of the original piecewise approximation, not
candidate-induced seams.

## Frozen Example 2 confirmation

Fresh reports contain four snapshots: 200 MHz perfect conductor, 250 MHz perfect conductor,
300 MHz perfect conductor, and the 300 MHz `LD 5` conductivity rerun. The first three snapshots are
exactly unchanged between Variant 0 and Variant A at the parsed physical-result level.

The named final-snapshot results are:

| Observable | Official publication | Variant 0, MSYS | Variant A, MSYS | Variant B, MSYS | Internal NEC2DX |
|---|---:|---:|---:|---:|---:|
| feed resistance, ohm | `112.430` | `106.58` | `112.43` | `112.43` | `112.43` |
| feed reactance, ohm | `65.4276` | `68.538` | `65.428` | `65.428` | `65.4277` |
| feed-current real, A | `6.64431e-3` | `6.6377e-3` | `6.6443e-3` | `6.6443e-3` | `6.6443e-3` |
| feed-current imaginary, A | `-3.86680e-3` | `-4.2683e-3` | `-3.8666e-3` | `-3.8666e-3` | `-3.8666e-3` |
| input power, W | `3.32215e-3` | `3.3188e-3` | `3.3222e-3` | `3.3222e-3` | `3.3222e-3` |
| radiated power, W | `2.4402e-3` | `2.5716e-3` | `2.4402e-3` | `2.4402e-3` | `2.4402e-3` |
| structure loss, W | `8.8199e-4` | `7.4727e-4` | `8.8199e-4` | `8.8199e-4` | `8.8199e-4` |
| network loss, W | `0` | `0` | `0` | `0` | `0` |
| efficiency, percent | `73.45` | `77.48` | `73.45` | `73.45` | `73.45` |

All eight segment-current rows were parsed. Symmetry makes segments 5 through 8 duplicates of
segments 4 through 1, so the unique half is shown:

| Segment | Variant 0 Re + j Im, A | Variant A / B Re + j Im, A | NEC2DX Re + j Im, A |
|---:|---:|---:|---:|
| 1 | `0.0013836 - j0.0010477` | `0.0013862 - j0.00096305` | `0.0013862 - j0.00096305` |
| 2 | `0.0037794 - j0.0027847` | `0.0037848 - j0.0025546` | `0.0037848 - j0.0025546` |
| 3 | `0.0055595 - j0.0039463` | `0.0055658 - j0.0036091` | `0.0055658 - j0.0036091` |
| 4 | `0.0065149 - j0.0043726` | `0.0065215 - j0.0039782` | `0.0065215 - j0.0039782` |

Variant A and Variant B are identical across all 316 parsed observables in the full four-snapshot
report; their complete MSYS reports are byte-identical. Thus neither authenticated medium-regime
constant correction is needed for this small-regime case. Variant A also passes all 316 comparisons
to internal NEC2DX under the frozen secondary-diagnostic tolerances. For the named final state they
agree at their common displayed precision except NEC2DX prints one more reactance digit and one more
feed-power digit.

Using the frozen half-LSD interval comparison, Variant A resolves 7 of Variant 0's 8 failures and
yields 6 direct passes, 11 passes limited by published precision, and one failure. The sole failure
is feed-current imaginary:
`-3.8666E-03 A` versus `-3.86680E-03 A`, absolute center difference `2.0e-7 A`. No tolerance was
widened to absorb it, and its cause is unresolved within the authorized `zint()` boundary.

All four Example 2 snapshots pass the frozen power-conservation policy in both Variant A builds. For
the loaded snapshot, the displayed power residual is
`input - (radiated + structure + network) = 1.0e-8 W`. It passes the frozen conservation bound
`5e-8 W + 5e-4 * abs(accounted power) = 1.711095e-6 W`.

## Cross-platform confirmation

Variant A was freshly built and the unchanged Example 2 deck was run under both MSYS and native
UCRT64. Both reports expose the same 316 physical observable identities. Every numeric value agrees
exactly at report precision; the maximum observed difference is zero. This passes the pre-existing
cross-platform bound `abs(error) <= 1e-12 + 1e-12 * abs(MSYS reference)` without consuming any
tolerance. After normalizing only native CRLF to LF, the complete reports are byte-identical with
SHA-256 `b46d6d89f738988e9efc91d5895628d8c701e1d99a1cc79a048e6305477263c9`.

This is candidate-specific cross-platform evidence. It does not qualify a maintained solver or
authorize a native binary distribution.

## Bounded regression impact

Variant 0 and Variant A used fresh MSYS builds and the same authenticated deck bytes. Equality below
means exact equality of every parsed field in the named snapshots, including feeds, segment currents,
power, fields, context, literals, and diagnostics.

| Case | Deck SHA-256 | Snapshot result |
|---|---|---|
| Part III Example 1 lumped load | `8a5133e22794fd726c76e554ad8f578f98d1e53bf2c54246b4335c57a6a23c30` | Both snapshots exactly unchanged. |
| Part III Example 2 full sequence | `39121efd2346da4b136e07901fb9e76b3b54494c47abf91277a3545fd95d95bc` | Snapshots 0-2 exactly unchanged; snapshot 3 changes as expected on `LD 5`. |
| Part III Example 3 perfect ground | `a81b99a75df45d5ddb27f0d8ae4ec6ef7102037fb0442e7d2041489c3f5c1606` | Its sole snapshot is exactly unchanged. |
| Part III Example 3 reflection ground | `c0e58690e47a1bf7d17cb79475533a302f058a37f049789b555297cbe327ab2d` | Its sole snapshot is exactly unchanged. |

No committed expected value changed. Per the investigation boundary, this is not the complete
eight-case qualification rerun.

## Defect boundary and proposed correction

Three exact translation defects are established:

1. The equivalents of the small- and medium-branch `GO TO 3` transfers are absent. This is causal
   for the frozen Example 2 discrepancy and for every returned `x <= 110` value.
2. `cc5` is `-j9.765e4` instead of authenticated `-j9.765e-4`. It is medium-only, differs by
   `10^8`, and cancels algebraically from the medium ratio apart from numerical conditioning. It is
   not causal for Example 2.
3. `CN` was incorrectly aliased to `cc14`, changing each component from `0.70710678` to
   `0.7071068`. It is medium-only and numerically small. It is not causal for Example 2.

At the starting source, the smallest causal change is to add `return;` after the result assignments
at logical lines 1499 and 1507 of `calculations.c`. That represents the two original transfers
without reformatting or refactoring the routine. Its expected effects are: restore the polynomial
for `x <= 8`, restore the medium approximation for `8 < x <= 110`, and make no numeric change for
`x > 110`. At Example 2's `x ~= 2.97`, it produces the authenticated small-branch impedance and the
NEC2DX-correlated end-to-end result, but it does not resolve the one official feed-current literal.

The minimum complete source-fidelity patch should additionally change logical line 1453 from
`-j9.765e4` to `-j9.765e-4` and replace the logical line 1463 alias with the distinct authenticated
`CN = 0.70710678 + j0.70710678`. Those corrections are necessary to stop carrying two known
medium-regime mistranslations, not to claim that they repair Example 2. Variant B demonstrates the
exact four-line scope. No surrounding modernization, reformat, algebraic rewrite, or unrelated
solver change is justified.

This document proposes those changes; it does not apply them.

## Exact next source-fix milestone

The next milestone is a separately reviewed maintained-source v2 candidate, not a silent mutation
of v1. It must:

1. add direct `zint()` branch tests for all three regimes;
2. add boundary-adjacent tests around `x = 8` and `x = 110`;
3. rerun the authoritative Example 2 conductivity comparisons and preserve the unresolved
   feed-current result unless new authenticated evidence explains it;
4. demonstrate fresh MSYS and native UCRT64 agreement;
5. rerun the complete frozen eight-case qualification suite;
6. prove no change to unaffected reference cases;
7. update the maintained-source patch and manifest identities;
8. assign a new maintained-source identity rather than mutating v1;
9. receive independent review before merge; and
10. withhold release and HF Propagation Control integration until numerical qualification passes.

The source-fix milestone must keep the official publication primary, NEC2DX secondary, the frozen
policy unchanged, and the qualification disposition honest. Investigation evidence alone is not a
release, integration, or qualification gate.
