# Contributing

The immutable preservation layer is evidence, not a normal development tree.

## Non-negotiable boundaries

- Never edit, normalize, regenerate, recompress, or replace
  `archive/nec2c-1.3.1.tar.bz2`.
- Never edit or add project changes inside `upstream/nec2c-1.3.1/`.
- Never move or recreate `archive/nec2c-1.3.1-original` or
  `preservation/nec2c-1.3.1-intake-v1`.
- Never silently copy maintained v1.3.3 or other later-contributor source.
- Never imply that this repository is official NEC2C or endorsed by Neoklis Kyriazis.
- Never apply BSD-2-Clause as a blanket label over upstream or other third-party material.

Future source, build, and tooling changes use ordinary feature branches and pull requests. Keep
project-authored maintained source outside `upstream/`, preserve file-level provenance, and add
`SPDX-License-Identifier: BSD-2-Clause` to eligible scripts and source files where appropriate.

## Before proposing a change

Run the offline preservation check:

```powershell
.\verify-preservation.ps1
```

Review the complete diff and confirm that no archive, upstream, manifest, binary, generated build
product, credential, machine-specific path, or unrelated dependency entered the change.

Every pull request that draws on external technical evidence must identify that evidence and
state whether the implementation is copied, adapted, or independently authored. Later
maintained-tree code requires separately established provenance and licensing before import.

v0.0.5f-A2 records the unmodified Windows x64 compiler baseline outside the archival tree. Its
two clean MSVC attempts fail consistently at the original `unistd.h` dependency and produce no
executable. Any Windows portability layer, alternate compiler policy, or source change is a
separate reviewed job; do not turn an A2 contribution into an unreviewed port.
