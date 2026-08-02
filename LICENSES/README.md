# License scope

This is intentionally a mixed-provenance repository. There is no plain root `LICENSE` file that
could imply one blanket license over every stored artifact.

## BSD-2-Clause scope

[BSD-2-Clause.txt](BSD-2-Clause.txt) applies only to copyrightable project-authored additions
and modifications that identify that license or are documented as project-authored work. This
includes the preservation documentation and verification tooling added outside the immutable
upstream tree. It also covers the exact project-authored portability additions and modifications
identified by `../manifests/maintained-source-v1.json` and the combined maintained patch.
`../src/nec2c/platform_time.h` and `../src/nec2c/platform_signal.h` are wholly project-authored
BSD-2-Clause files. Original material retained in modified source files is not relabeled as BSD.

An SPDX header is used on project-authored scripts and source files where appropriate:

```text
SPDX-License-Identifier: BSD-2-Clause
```

## Upstream scope

BSD-2-Clause does not relabel or claim ownership of:

- `archive/nec2c-1.3.1.tar.bz2`;
- `upstream/nec2c-1.3.1/`;
- original notices, disclaimers, or historical license evidence; or
- later third-party contributions not actually imported with separately established terms.

The selected original-author source is handled under the public-domain statement preserved in
`upstream/nec2c-1.3.1/README` section 7. The bundled GPLv3 `COPYING` remains preserved at
`upstream/nec2c-1.3.1/COPYING`. See [../THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) for
the complete repository notice.
