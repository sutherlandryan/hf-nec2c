# Third-party notices

This repository contains mixed-provenance material. The notices below preserve the governing
engineering policy without replacing the original evidence.

## Original NEC2C 1.3.1 distribution

- Original author: Neoklis Kyriazis
- Preserved release: NEC2C 1.3.1
- Original archive: `archive/nec2c-1.3.1.tar.bz2`
- Exact extracted tree: `upstream/nec2c-1.3.1/`

The original README section 7 declares NEC2C public domain and asks software incorporating it to
remain public domain or use an open license such as GPL or BSD. The project handles the selected
original-author source under that preserved statement.

The same original distribution includes the complete GNU General Public License version 3 text
at `upstream/nec2c-1.3.1/COPYING`. That file remains byte-preserved historical source evidence;
it has not disappeared, been edited, or been treated as irrelevant. Retaining it does not by
itself resolve or rewrite the scope of the README's more specific statement.

Original source files also preserve U.S. government sponsorship notices and warranty, liability,
accuracy, completeness, usefulness, and non-infringement disclaimers. Those notices remain in
their original files and are not restated here as a substitute.

## Project-authored work

Copyrightable project-authored additions and modifications are made available under
BSD-2-Clause as described in [LICENSES/README.md](LICENSES/README.md). That license is not
asserted over the original archive or extracted upstream source merely because they are stored
in this repository.

The maintained `src/nec2c/` tree is mixed-provenance work. Original NEC2C 1.3.1 material remains
handled under the preserved original-author public-domain statement. Project-authored portability
additions and modifications are BSD-2-Clause and are identified exactly by the
[v1 manifest](manifests/maintained-source-v1.json),
[v1 combined patch](patches/maintained/nec2c-1.3.1-hf-portability-v1.patch),
[v2 manifest](manifests/maintained-source-v2.json), and
[v2 combined patch](patches/maintained/nec2c-1.3.1-hf-portability-zint-v2.patch). In v2,
`calculations.c` is an additional original file containing the project-authored four-line
`zint()` source-fidelity modification; `main.c`, `misc.c`, and `nec2c.h` retain their earlier
identified portability modifications. Original material retained in those files is not relabeled
as BSD-2-Clause. The two platform headers are wholly project-authored BSD-2-Clause files. The
maintained source is independent, not official NEC2C, and remains unqualified, unreleased, and
unapplied.

## Excluded maintained-tree code

The maintained NEC2C v1.3.3 tree is a research/comparison reference only and is not the source
base. No later-contributor source was silently imported. Future use of later work requires
separately established provenance and licensing or an independent project-authored
implementation from permissible technical facts.

This notice records the repository's adopted source-selection and distribution policy. It does
not purport to adjudicate every legal question.
