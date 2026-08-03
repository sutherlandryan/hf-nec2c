# NEC2 numerical qualification seed corpus

## Disposition

Milestone: **v0.0.5f-B — NEC2 numerical qualification seed corpus**.

Outcome: **C. NUMERICAL QUALIFICATION BLOCKED**.

Seven cases met their declared, bounded case criteria. The authoritative NEC-2 Part III Example 2
finite-conductivity stage did not: the fresh MSYS and native UCRT64 builds of
`HF_NEC2C_MAINTAINED_SOURCE_V1` agree with each other, but both disagree with the official
published result and with the internal NEC2DX secondary diagnostic. The first implicated boundary
is the `LD` type 5 circular-wire internal-impedance calculation in `zint()`.

This result does **not** qualify the maintained solver, make it release-ready, approve a binary,
or authorize HF Propagation Control integration. Maintained source was not modified. Corpus
expansion stopped at the frozen eight-case ceiling, and the failing project-authored deck plus the
small normalized evidence summary were preserved for a separately authorized investigation.

The deterministic definitions are in
[`numerical-qualification-v0.0.5f-b.json`](../manifests/numerical-qualification-v0.0.5f-b.json).
The normalized result is in
[`numerical-qualification-v0.0.5f-b-results.json`](../manifests/numerical-qualification-v0.0.5f-b-results.json),
whose SHA-256 is
`dfa0fff497cd8fb1b51894e3975cf75031a65a7c18ef89e58403efa318f297b2`. Raw reports,
executables, compiler products, manual
files, and internal NEC2DX material are not committed.

## Exact question and bounded claim

The milestone asked whether the maintained candidate reproduces authoritative NEC-2 results,
satisfies declared analytic and physical invariants, agrees across fresh MSYS and native UCRT64
builds, and remains consistent with internal NEC2DX for the wire-antenna functionality intended by
HF Propagation Control.

The claim is deliberately case- and observable-specific:

- `QUALIFIED_FOR_INTENDED_SUBSET` means that every declared authoritative check, invariant, and
  cross-platform check for that one case met its frozen criteria. It is not a claim about an
  untested card, geometry, ground method, matrix regime, or the solver as a whole.
- `QUALIFIED_WITH_DOCUMENTED_GAP` means that the declared invariants and implementation
  comparisons passed, but no authenticated authoritative numeric publication was available for
  that project-authored case. Agreement with NEC2DX cannot fill that gap.
- `BLOCKED_BY_NUMERICAL_DISCREPANCY` means at least one authoritative, analytic,
  cross-platform, or conservation check failed. One such case blocks the milestone.

The overall result is therefore blocked even though seven individual cases have bounded passing
classifications.

## Scope

The seed exercises only the intended field-application subset represented by the corpus:

- thin straight and connected wires;
- voltage-source excitation for the intended subset; Example 2's applied-field excitation is
  only the incidental stimulus of an authoritative benchmark, not qualified intended
  functionality;
- free space, perfect ground, and reflection-coefficient ground;
- lumped loading and circular-wire conductivity loading;
- geometry scaling and symmetric connected structures;
- feed impedance, complex segment currents, power accounting, structure efficiency, and far-field
  gain, polarization, symmetry, maxima, and nulls; and
- one controlled 11/21/41-segment convergence series.

It excludes surface patches, aircraft or scattering models, numerical Green-function files,
out-of-core operation, unexercised historical cards, structured solver output, binary production,
distribution, and application integration. Sommerfeld/Norton ground is also excluded because no
redistributable authoritative reference with compatible `SOM2D.NEC` data was authenticated. No
case or expected value was invented to hide that gap.

## Evidence hierarchy

Every case was judged in this order:

1. **Authoritative NEC-2 Part III published values.** These are the deciding numeric references
   where available.
2. **Analytic and physical invariants.** These include symmetry, conservation of power, expected
   pattern topology, image-theory behavior, and controlled segmentation convergence.
3. **Fresh maintained NEC2C cross-platform agreement.** Named physical values from MSYS and
   native UCRT64 reports were compared; report bytes were not.
4. **Internal NEC2DX secondary diagnostics.** This implementation has shared lineage with NEC2C.
   It can expose translation or runtime differences, but agreement cannot independently prove
   correctness and disagreement cannot by itself fail a case.

A case with no evidence from levels 1 or 2 cannot pass solely because levels 3 and 4 agree.

## Authoritative reference provenance

The deciding publication is:

- G. J. Burke and A. J. Poggio, *Numerical Electromagnetics Code (NEC) — Method of Moments,
  Part III: User's Guide* (1981);
- NTIS/DTIC identifier `ADA956129`;
- official NTIS/NTRL catalog record:
  <https://ntrl.ntis.gov/NTRL/dashboard/searchResults/titleDetail/ADA956129.xhtml>.

The official NTIS download used for authentication was 17,527,148 bytes, contained 730 PDF pages,
and had SHA-256
`0bb280883b2b17fafb1bbd6a1504dcbf645e49cd8a7c8bd02424b5cea8a3d9e6`. It was used only in
ignored research storage. Example cards were checked at printed page 97 / PDF page 643; accepted
output literals were checked directly on the applicable printed pages 99–109 / PDF pages
645–655. Each committed expected-value record names its example, printed and PDF page locator,
observable, units, literal, and displayed precision.

The NEC2.org and FUNET `nec2prt3.pdf` research copies were also checked. They were byte-identical
to one another: 423,411 bytes, SHA-256
`bd2d988654054a0b08b14b233cf8a159cc75043b9aaebd008a52e093a7b28caf`. They are a 1996 WDBN
OCR transcription, not an independent scan of the 1981 manual. They were useful for search, but
no transcription literal became acceptance evidence until checked against the official NTIS
scan. This corrects the informal description of the FUNET copy as a “scan.”

No manual PDF, page rendering, screenshot, long manual passage, or third-party example deck is
tracked. The committed decks are project-authored reconstructions from executable parameter
facts, accompanied by citations rather than copied report text.

## Frozen corpus

The corpus contains exactly eight cases. Each deck is content-addressed in its metadata and the
suite manifest.

| Case | Deck SHA-256 | Distinct qualification purpose |
|---|---|---|
| `minimal-free-space-dipole` | `395603f62e0e0682215d9985443e4e13ff73f583646427b8dc9785ca76571520` | Existing parser/harness baseline; centered-feed impedance, mirrored currents, power, and broadside topology |
| `nec2-part3-example1-lumped-load` | `8a5133e22794fd726c76e554ad8f578f98d1e53bf2c54246b4335c57a6a23c30` | Published unloaded and lumped-RLC states; feed, power, efficiency, and current symmetry |
| `nec2-part3-example2-conductivity-sweep` | `39121efd2346da4b136e07901fb9e76b3b54494c47abf91277a3545fd95d95bc` | Published 200/250/300 MHz applied-field sweep plus 300 MHz `LD` type 5 conductivity rerun |
| `nec2-part3-example3-perfect-ground` | `a81b99a75df45d5ddb27f0d8ae4ec6ef7102037fb0442e7d2041489c3f5c1606` | Published perfect-ground monopole feed, power, average gain, image-theory pattern, null, and rotational symmetry |
| `nec2-part3-example3-reflection-ground` | `c0e58690e47a1bf7d17cb79475533a302f058a37d049789b555297cbe327ab2d` | Published finite reflection ground with dielectric/conductivity, feed, pattern change, horizon null, and maximum |
| `connected-scaled-inverted-v` | `2219ab61aa88a5c4443b46cbb155b86adfa24c70eb531554573be20c34d58582` | Three-wire connected junction, `GS 0.01` transformed segment centers/lengths, mirrored-arm current identity, and two-plane pattern grid |
| `minimal-dipole-21-segment` | `8b9ec2efd309bbd29f3c9234788b40552ffc5ada3e7b7f3d95f2ccf88230c9af` | Middle point in a controlled segmentation refinement with full currents and two-plane pattern |
| `minimal-dipole-41-segment` | `51a8c79cfa4f76e5eeff713db692dc0971892731b539b524584f3d62f45b2ad5` | Fine point in the same convergence series |

The existing 11-segment smoke deck is reused without duplication. The other seven decks and all
eight metadata records live under [`tests/qualification/cases/`](../tests/qualification/cases/).

## Fresh build identities

Both maintained executables were built out of tree from the unchanged 36-file, 788,897-byte
`HF_NEC2C_MAINTAINED_SOURCE_V1` tree through its shipped `configure` and GNU `make -j1 V=1`
route. Build and result directories were ignored and were removed after evidence capture.

Both routes used GNU Bash 5.3.15(1) (`x86_64-pc-cygwin`, SHA-256
`41b09f0a9c1c68fd65253a7e8087b3775f0af245b729ade74ca4425d14392c2d`) through
`/usr/bin/bash --noprofile --norc` and GNU Make 4.4.1 (SHA-256
`91b7e155590d59db22e5eb0a3ffeec6350149f70f9ed2c242d133e584eb72fee`). Their
process-local `TEMP`, `TMP`, and `TMPDIR` values were each `/tmp`.

| Build | Compiler identity | Executable identity | Architecture and runtime |
|---|---|---|---|
| MSYS POSIX | GCC 15.3.0, `x86_64-pc-cygwin`; compiler SHA-256 `4bd76635b6053a7926f4579a30f9c800a673632fd10b4d6adf8083d3eda1b80c` | 332,949 bytes; SHA-256 `c5c28af40d86ac787d03e9aade3d49350517eef514a910ed0fa65d263aed252f` | PE32+ x86-64; `msys-2.0.dll`, `msys-gcc_s-seh-1.dll`, `KERNEL32.dll` |
| Native UCRT64 | GCC 16.1.0, `x86_64-w64-mingw32`; compiler SHA-256 `f96a3bdb1d3a3967b309d75c7413399391e857b5be4cb17162572ed66f6772a0` | 436,657 bytes; SHA-256 `028206530fc9d5f06e73697cbfef5e7f5a3f4f511b1b51326e7fa38959c99e41` | PE32+ x86-64; `KERNEL32.dll` and Universal CRT API-set imports; no `msys-2.0.dll` |

The effective build commands were:

```text
CC=/usr/bin/gcc /usr/bin/bash $REPO/src/nec2c/configure
/usr/bin/make -j1 V=1

CC=/ucrt64/bin/gcc /usr/bin/bash $REPO/src/nec2c/configure
/usr/bin/make -j1 V=1
```

Executable-hash equality across separate toolchains was not required. The evidence uses each
fresh executable's own identity and its named physical results.

### Internal NEC2DX diagnostic build

The internal archive remained untracked and non-redistributable: 262,656 bytes, SHA-256
`ad20c15a8cb594b19928595c853eca2b576c875c45c39a45eeaf26ee1be79774`. Its authenticated
`nec2dx.f` SHA-256 was
`ca2ffebef9fb928d17e1eedcaa6f87b7bd61125a5f1abe19227d3f8251d9b293`. Applying only the
documented two `EXTERNAL SECOND` declarations produced the expected edited-source SHA-256
`bf894ae10325ff8534a45960e901f1a88d98485ce5f97569cea137f125d0e15c`.

The diagnostic executable was built once with GNU Fortran 16.1.0 for
`x86_64-w64-mingw32` (compiler SHA-256
`f1f086d81f4c6701281df5543ca232cd741857f7c4611c43904d0e88e58718ce`) using:

```text
gfortran -O0 -std=legacy -ffixed-line-length-none -o nec2dx.exe nec2dx.f
```

With process-local `PARALLEL=1` and `OMP_NUM_THREADS=1`, the PE32+ x86-64 executable was 587,405
bytes with SHA-256
`a29c65e22838d7788ee2ae367f4add2e8591465b2b1c8ad6d62d71e2ebe7a343`. It imported
`libgcc_s_seh-1.dll`, `libgfortran-5.dll`, `KERNEL32.dll`, and Universal CRT API-set DLLs, not
`msys-2.0.dll`. Neither source, edit, executable, report, nor runtime DLL was committed.

## Parser and comparison method

The project-authored tooling under [`tools/qualification/`](../tools/qualification/) finds report
sections by headings, then identifies feeds, currents, power fields, and far-field rows by their
physical tag/segment or theta/phi identity. It preserves exact displayed numeric literals for
published-precision comparisons and parses diagnostics without depending on fixed report line
numbers. It does not change NEC2C output or compare raw bytes between NEC2C and NEC2DX.

The deterministic runner authenticates every deck, metadata record, and expected report name;
requires all three fresh reports; parses complex feed values, currents, power, efficiency,
complete requested patterns, polarization fields, average gain, and diagnostics; applies every
typed manifest check; and emits a small sorted JSON result. Undefined polarization phases are
classified `NOT_APPLICABLE` only when the associated magnitude is below its declared threshold.

## Frozen tolerance policy

There is no blanket percentage tolerance. For absolute-plus-relative checks, the limit is
`absolute + relative * |reference|`; near zero uses the stated absolute bound. Azimuth and current
phases use shortest circular distance; polar theta comparisons remain linear.

### Published values and the display-interval amendment

The initial source rule bounded each official value by one half-unit in its last displayed digit,
including its exponent. The parser then established that maintained NEC2C prints fewer digits than
the manual for several values. Treating the lower-precision candidate's center as exact would
invent digits the report does not contain.

The final rule therefore compares the inclusive half-LSD interval implied by the candidate
literal with the inclusive half-LSD interval implied by the official-scan literal:

- equal centers: `PASS`;
- distinct centers whose intervals intersect: `PASS_WITH_REFERENCE_PRECISION_LIMIT`; and
- disjoint intervals: `FAIL`.

Published zero is bounded only by its displayed absolute precision. Published `-999.99` is a null
sentinel, not a physical negative-infinite gain. This post-initial amendment is explicitly
source-precision-driven: it does not widen either printed interval, every affected acceptance is
marked precision-limited rather than direct `PASS`, and all eight Example 2 conductivity
discrepancies remain disjoint and fail.

### Cross-platform and invariant tolerances

| Observable or invariant | Absolute tolerance | Relative tolerance / additional rule |
|---|---:|---|
| Any named MSYS–UCRT64 numeric value | `1e-12` | `1e-12` |
| Power conservation | `5e-8 W` | `5e-4`; compare input with radiated + structure + network loss |
| Expected zero structure/network loss | `5e-8 W` | no relative term |
| Mirrored current magnitude | `5e-8 A` | `5e-5` |
| Mirrored current phase | `0.02°` | wrapped circularly |
| Pattern symmetry | `0.02 dB` | compare same-theta cuts |
| Expected maximum direction | `0.005°` | grid direction, not interpolated maximum |
| Undefined field phase | `5e-12 V/m` | phase is `NOT_APPLICABLE` below this magnitude |
| Perfect-ground average power gain | `0.05` | compare with image-theory value 2.0 |
| Segmentation convergence | trend check | second 21→41 delta must be smaller than first 11→21 delta for feed impedance and broadside gain |

### NEC2DX secondary tolerances

These bounds classify diagnostics only. They cannot make a case pass.

| Observable class | Absolute tolerance | Relative tolerance |
|---|---:|---:|
| Feed impedance | `0.006 ohm` | `5e-5` |
| Feed/segment current and current magnitude | `5e-8 A` | `5e-5` |
| Current or far-field phase and polarization tilt | `0.02°` | `0` |
| Feed admittance | `5e-8 mho` | `5e-5` |
| Feed voltage | `5e-6 V` | `5e-5` |
| Input, radiated, structure-loss, network-loss, and feed power | `5e-8 W` | `5e-5` |
| Efficiency | `0.01 percentage point` | `5e-5` |
| Far-field gain | `0.02 dB` | `0` |
| Far-field magnitude | `5e-5 V/m` | `5e-5` |
| Current position and segment length | `5e-5 wavelength` | `5e-5` |
| Frequency | `5e-6 MHz` | `5e-5` |
| Average power gain | `5e-5` | `5e-5` |
| Any remaining numeric class | `1e-6` | `5e-5` |

## Results

All 24 report-integrity records passed: each of the eight cases had complete, diagnostic-free
MSYS, UCRT64, and NEC2DX reports. The runner classified 6,392 normalized check records:

| Classification | Count |
|---|---:|
| `PASS` | 5,981 |
| `PASS_WITH_REFERENCE_PRECISION_LIMIT` | 26 |
| `FAIL` | 8 |
| `SECONDARY_DISAGREEMENT` | 43 |
| `NOT_APPLICABLE` | 334 |

The two explicit `REFERENCE_UNAVAILABLE` gaps are recorded separately because they describe absent
authority, not a comparison against a generated value.

### Per-case classification

`P` means `PASS`, `PPR` means `PASS_WITH_REFERENCE_PRECISION_LIMIT`, `F` means `FAIL`, `SD`
means `SECONDARY_DISAGREEMENT`, `NA` means `NOT_APPLICABLE`, and `RU` means
`REFERENCE_UNAVAILABLE`. Counts include all named values and declared invariant records, not raw
report lines.

| Case | Case disposition | Official values | Invariants | MSYS vs UCRT64 | NEC2DX secondary |
|---|---|---:|---:|---:|---:|
| Minimal 11-segment dipole | `QUALIFIED_WITH_DOCUMENTED_GAP` | RU | 30 P | 111 P / 1 NA | 111 P / 1 NA |
| Part III Example 1, unloaded + lumped load | `QUALIFIED_FOR_INTENDED_SUBSET` | 11 P / 7 PPR | 36 P | 142 P | 142 P |
| Part III Example 2, frequency + conductivity | `BLOCKED_BY_NUMERICAL_DISCREPANCY` | 2 P / 8 PPR / 8 F | 88 P | 316 P | 273 P / 43 SD |
| Part III Example 3, perfect ground | `QUALIFIED_FOR_INTENDED_SUBSET` | 14 P / 6 PPR | 34 P | 246 P / 22 NA | 246 P / 22 NA |
| Part III Example 3, reflection ground | `QUALIFIED_FOR_INTENDED_SUBSET` | 15 P / 5 PPR | 34 P | 246 P / 22 NA | 246 P / 22 NA |
| Connected, scaled inverted-V | `QUALIFIED_WITH_DOCUMENTED_GAP` | RU | 100 P | 515 P / 42 NA | 515 P / 42 NA |
| Minimal 21-segment dipole | `QUALIFIED_WITH_DOCUMENTED_GAP` | RU | 90 P | 485 P / 40 NA | 485 P / 40 NA |
| Minimal 41-segment dipole | `QUALIFIED_WITH_DOCUMENTED_GAP` | RU | 130 P | 645 P / 40 NA | 645 P / 40 NA |

All four suite-level convergence records passed: both maintained builds had decreasing successive
11→21→41 feed-impedance deltas and decreasing successive broadside-gain deltas.

### Maximum discrepancies by observable class

For official published checks, the maximum candidate-center discrepancies were:

| Observable class | Maximum absolute discrepancy | Classification consequence |
|---|---:|---|
| Average power gain | `4e-5` | precision-limited pass |
| Efficiency | `4.03 percentage points` | fail in Example 2 conductivity stage |
| Far-field total gain | `0.01 dB` | precision-limited pass |
| Feed current component | `4.015e-4 A` | fail in Example 2 conductivity stage |
| Feed impedance component | `5.85 ohm` | fail in Example 2 conductivity stage |
| Input power | `3.35e-6 W` | fail in Example 2 conductivity stage |
| Radiated power | `1.314e-4 W` | fail in Example 2 conductivity stage |
| Structure loss | `1.3472e-4 W` | fail in Example 2 conductivity stage |
| Network loss | `0 W` | pass |

Across the maintained MSYS and native UCRT64 reports, every normalized observable class had zero
maximum discrepancy except far-field magnitude, whose maximum was `9.23e-18 V/m`. That value is
well inside the `1e-12 + 1e-12 * |reference|` cross-platform limit. All 2,706 applicable
cross-platform records passed; 167 phase/polarization records were not applicable at undefined
field components.

The largest invariant residuals were `7.0e-8 W` for power conservation and `0.0279` for the
perfect-ground average-power-gain relation to 2.0. Both met their declared limits. Current
magnitude and phase symmetry, pattern symmetry, expected null sentinels, maximum directions,
zero-loss checks, the six typed inverted-V coordinate/segment-length checks after `GS 0.01`, and
both convergence trends had zero recorded tolerance violation; all 546 invariant records passed.

For the NEC2DX secondary diagnostic, the nonzero maximum differences by class were:

| Observable class | Maximum absolute difference |
|---|---:|
| Average power gain | `4.0e-5` |
| Current magnitude | `2.071e-4 A` |
| Current phase | `2.484°` |
| Feed admittance | `4.017e-4 mho` |
| Feed current component | `4.017e-4 A` |
| Feed impedance component | `5.85 ohm` |
| Feed power | `3.35e-6 W` |
| Input power | `3.4e-6 W` |
| Radiated power | `1.314e-4 W` |
| Segment-current component | `3.944e-4 A` |
| Structure loss | `1.3472e-4 W` |
| Far-field magnitude | `3.0e-5 V/m` |

Maximum NEC2DX differences for current position, segment length, frequency, feed voltage, network
loss, far-field gain, far-field phase, polarization tilt, and axial ratio were zero. Efficiency
itself differed by `4.03 percentage points` in the Example 2
conductivity stage. All 43 `SECONDARY_DISAGREEMENT` records belong to that one stage. The other
supported comparisons met their type-specific secondary bounds.

## Blocking Example 2 discrepancy

The three perfect-conductor frequency stages at 200, 250, and 300 MHz met the official displayed
values. The discrepancy begins only after the project-authored reconstruction applies
`LD 5 0 0 0 3.720E+07` and reruns at 300 MHz.

Both maintained builds emitted the same values:

| Observable | Maintained NEC2C | Official NTIS scan | Absolute difference |
|---|---:|---:|---:|
| Feed resistance | `106.58 ohm` | `112.430 ohm` | `5.85 ohm` |
| Feed reactance | `68.538 ohm` | `65.4276 ohm` | `3.1104 ohm` |
| Feed-current real component | `6.6377e-3 A` | `6.64431e-3 A` | `6.61e-6 A` |
| Feed-current imaginary component | `-4.2683e-3 A` | `-3.86680e-3 A` | `4.015e-4 A` |
| Input power | `3.3188e-3 W` | `3.32215e-3 W` | `3.35e-6 W` |
| Radiated power | `2.5716e-3 W` | `2.4402e-3 W` | `1.314e-4 W` |
| Structure loss | `7.4727e-4 W` | `8.8199e-4 W` | `1.3472e-4 W` |
| Network loss | `0 W` | `0 W` | `0 W` |
| Efficiency | `77.48%` | `73.45%` | `4.03 percentage points` |

The maintained values satisfy their own power-conservation check and agree across toolchains.
Those facts do not override the authoritative failures. Internal NEC2DX instead produced
`112.430 + j65.4277 ohm`, a feed current of approximately
`6.64430e-3 - j3.86660e-3 A`, radiated power `2.4402e-3 W`, structure loss
`8.8199e-4 W`, and efficiency `73.45%`, corroborating the published side as secondary evidence.

### First implicated subsystem boundary

The first implicated boundary is the `LD` type 5 circular-wire internal-impedance path,
[`zint()` in `src/nec2c/calculations.c`](../src/nec2c/calculations.c). For this deck the routine's
dimensionless branch variable is approximately `x = 2.97`, so the `x <= 8` approximation should
supply the result. The maintained C translation computes that branch, then falls through and
overwrites it with the `x <= 110` result, then falls through once more and overwrites it with the
`x > 110` asymptotic value. The internal NEC2DX control flow selects one branch and transfers to a
single common final assignment.

An adjacent source anomaly was recorded but is not claimed as the cause of this `x <= 8` case:
the maintained C `cc5` imaginary coefficient is `-9.765e4`, while the corresponding NEC2DX
literal is `-9.765D-4`. That coefficient belongs to another approximation path and requires its
own authenticated investigation.

This milestone did not repair, patch around, or otherwise alter either observation. The source
tree, combined maintained patch, and maintained manifest remain the previously reviewed v1
identity.

## Unresolved gaps and exclusions

- **Sommerfeld/Norton ground — `REFERENCE_UNAVAILABLE`.** No authenticated redistributable
  reference with compatible `SOM2D.NEC` data was available. NEC2DX was not used to fabricate one.
- **Project-authored baseline, junction, and refinement cases — `REFERENCE_UNAVAILABLE`.** Their
  case classifications rely on invariants, cross-platform agreement, and secondary diagnostics,
  not a claimed published numeric oracle.
- The seed does not cover every thin-wire topology, frequency, load, ground parameter, matrix
  condition, or historical NEC card. Passing a seed case cannot be generalized to those spaces.
- Surface patches, scattering, aircraft models, numerical Green functions, out-of-core operation,
  binary hardening, structured output, packaging, and application behavior were not evaluated.
- NEC2DX has shared implementation lineage and unresolved redistribution limits. Its results stay
  diagnostic and internal.
- Structure efficiency in the finite reflection-ground case is not a claim of zero ground loss;
  it accounts for the report's defined structure/network loss terms.

## Production and provenance boundary

The tracked work consists only of project-authored decks, metadata, manifest data, parser and
comparison tooling, focused tests, this documentation, and a small normalized result summary.
The official manual and all internal NEC2DX artifacts remained ignored research inputs. No
third-party source, edit, executable, object, DLL, raw complete report, scan, screenshot, or
temporary extraction was committed.

Nothing in this record approves distribution, a solver binary, a GitHub release, HF Propagation
Control integration, or applying solver-derived antenna patterns. The maintained candidate remains
unreleased and unapplied.

## Exact next milestone

Do not begin it without separate authorization. The exact next milestone is a **bounded solver
investigation of the NEC2C `LD` type 5 `zint()` translation discrepancy**:

1. start from the preserved Example 2 conductivity deck and normalized failing evidence;
2. authenticate and trace the original NEC-2/NEC2DX branch equations, constants, and control flow
   against the maintained C translation;
3. isolate the `x <= 8`, `8 < x <= 110`, and `x > 110` regimes with narrowly designed diagnostic
   cases;
4. determine the complete defect boundary and propose, but do not silently integrate, a minimal
   source correction and regression plan; and
5. require a separately reviewed source-change and requalification milestone before any patch,
   release, or application integration.

The current eight-case corpus must remain frozen until that investigation is explicitly
authorized and resolved.
