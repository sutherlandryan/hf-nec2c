# Windows x64 smoke input

`minimal-dipole.nec` is a small, independently authored NEC input used only to prove ordinary
input parsing, calculation, and report creation after a compiler baseline exists. It was not
copied or adapted from maintained NEC2C v1.3.3, which is not the source base. The preserved
NEC2C 1.3.1 archive contains no example decks.

The deck defines one eleven-segment, center-fed, ten-meter straight wire in free space at
14.2 MHz and requests one far-field sample. It is intentionally too small to be a numerical
qualification corpus. Successful execution would prove only that the unmodified executable can
complete this controlled command path.

The build driver also generates a three-byte `ZZ` plus LF malformed deck inside its ignored temporary
workspace. Smoke commands always use short leaf names and an explicit output:

```text
nec2c.exe
nec2c.exe -imissing.nec -omissing.out
nec2c.exe -imalformed.nec -omalformed.out
nec2c.exe -iinput.nec -ovalid-1.out
nec2c.exe -iinput.nec -ovalid-2.out
```

No smoke output is a claim of agreement with NEC2, `nec2dx`, NEC-4, or NEC-5. Numerical
qualification and tolerance selection belong to v0.0.5f-B.
