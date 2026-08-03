# SPDX-License-Identifier: BSD-2-Clause
"""Direct compiled tests for the maintained NEC2C ``zint`` implementation."""

from __future__ import annotations

import math
import os
import subprocess
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CALCULATIONS_PATH = REPOSITORY_ROOT / "src" / "nec2c" / "calculations.c"
HARNESS_PATH = REPOSITORY_ROOT / "tests" / "zint_direct_harness.c"
BUILD_TEMP = REPOSITORY_ROOT / ".build-temp"
MSYS2_ROOT = Path(r"C:\msys64")
BASH_PATH = MSYS2_ROOT / "usr" / "bin" / "bash.exe"

ZINT_START = "/* zint computes the internal impedance of a circular wire */"
ZINT_END = "/*-----------------------------------------------------------------------*/"
CC5_CORRECT = "#define cc5\t\t( 0.         - I*9.765e-4)"
CC5_REVERTED = "#define cc5\t\t( 0.         - I*9.765e4)"
CN_CORRECT = "#define cn\t(0.70710678 + I*0.70710678)"
CN_REVERTED = "#define cn\tcc14"
SMALL_ASSIGNMENT = "\t  *zint= CPLX_01* sqrt( cmotp/sigl )* br1/ rolam;"
MEDIUM_ASSIGNMENT = "\t*zint= CPLX_01* sqrt( cmotp/ sigl)* br1/ rolam;"
LARGE_ASSIGNMENT = "  *zint= CPLX_01* sqrt( cmotp/ sigl)* br1/ rolam;"
SMALL_TRANSFER = SMALL_ASSIGNMENT + "\n\t  return;\n\n  } /* if( x <= 8.) */"
MEDIUM_TRANSFER = MEDIUM_ASSIGNMENT + "\n\treturn;\n\n  } /* if( x <= 110.) */"
LARGE_ENDING = "  br1= cmplx(.70710678,-.70710678);\n" + LARGE_ASSIGNMENT + "\n}"

ABSOLUTE_MEDIUM_TOLERANCE = 1.0e-11
RELATIVE_MEDIUM_TOLERANCE = 5.0e-12


class ZintSourceShapeError(ValueError):
    """The maintained ``zint`` routine no longer has the reviewed shape."""


def _one_occurrence(text: str, expected: str, label: str) -> None:
    count = text.count(expected)
    if count != 1:
        raise ZintSourceShapeError(
            f"{label} must occur exactly once in zint; observed {count}"
        )


def zint_routine(source_text: str) -> str:
    """Extract the uniquely delimited production ``zint`` routine."""

    if source_text.count(ZINT_START) != 1:
        raise ZintSourceShapeError("zint start marker must occur exactly once")
    start = source_text.index(ZINT_START)
    end = source_text.find(ZINT_END, start + len(ZINT_START))
    if end < 0:
        raise ZintSourceShapeError("zint end marker is missing")
    routine = source_text[start:end].rstrip()
    if "void zint( double sigl, double rolam, complex double *zint )" not in routine:
        raise ZintSourceShapeError("reviewed zint function signature is missing")
    return routine


def validate_zint_source_shape(source_text: str) -> str:
    """Require the exact four reviewed source-fidelity corrections."""

    routine = zint_routine(source_text)
    _one_occurrence(routine, CC5_CORRECT, "corrected cc5 definition")
    _one_occurrence(routine, CN_CORRECT, "distinct CN definition")
    _one_occurrence(routine, SMALL_TRANSFER, "small-regime return")
    _one_occurrence(routine, MEDIUM_TRANSFER, "medium-regime return")
    _one_occurrence(routine, LARGE_ENDING, "unchanged large-regime ending")
    _one_occurrence(routine, "\tif( x <= 8.)\n", "small-regime condition")
    _one_occurrence(routine, "  if( x <= 110.)\n", "medium-regime condition")
    if routine.count("#define cc5") != 1:
        raise ZintSourceShapeError("zint must contain exactly one cc5 definition")
    if routine.count("#define cn") != 1:
        raise ZintSourceShapeError("zint must contain exactly one CN definition")
    if routine.count("return;") != 2:
        raise ZintSourceShapeError("zint must contain exactly two early returns")
    if CC5_REVERTED in routine:
        raise ZintSourceShapeError("cc5 exponent correction was reverted")
    if CN_REVERTED in routine:
        raise ZintSourceShapeError("CN was aliased to cc14")
    return routine


@dataclass(frozen=True)
class ExpectedCase:
    target_x: float
    branch: str
    real: float
    imaginary: float

    @property
    def exact_binary64(self) -> bool:
        return self.branch != "medium"


@dataclass(frozen=True)
class ProbeResult:
    target_x: float
    actual_x: float
    branch: str
    real: float
    imaginary: float


# Full-precision values from the authenticated Fortran ZINT direct probe recorded by
# the source-translation investigation. Small and large results agree exactly with
# the corrected C translation; medium results use the pre-run componentwise bound.
EXPECTED_CASES = (
    ExpectedCase(0.1, "small", 75398.262060618858, 94.247753944725901),
    ExpectedCase(1.0, "small", 757.89293132112391, 94.003444327952295),
    ExpectedCase(2.97, "small", 111.84272358107596, 80.082864635342332),
    ExpectedCase(7.999, "small", 36.460553360593764, 33.091830249155009),
    ExpectedCase(8.0, "small", 36.455582603857422, 33.087759514550541),
    ExpectedCase(8.001, "medium", 36.450608857252575, 33.083679723591509),
    ExpectedCase(20.0, "medium", 13.812337090593328, 13.315228335370772),
    ExpectedCase(50.0, "medium", 5.4076569670375676, 5.3306366454099807),
    ExpectedCase(109.999, "medium", 2.4390661864484047, 2.4233365733338430),
    ExpectedCase(110.0, "medium", 2.4390438701331063, 2.4233145443933766),
    ExpectedCase(110.001, "large", 2.4233686300703217, 2.4233686300703217),
    ExpectedCase(200.0, "large", 1.3328648633818272, 1.3328648633818272),
)


@dataclass(frozen=True)
class Toolchain:
    name: str
    msystem: str
    path: str
    compiler: str
    objcopy: str

    @property
    def required_paths(self) -> tuple[Path, ...]:
        compiler = self.compiler.removeprefix("/").replace("/", os.sep) + ".exe"
        objcopy = self.objcopy.removeprefix("/").replace("/", os.sep) + ".exe"
        cxx = compiler.replace("gcc.exe", "g++.exe")
        return (
            BASH_PATH,
            MSYS2_ROOT / compiler,
            MSYS2_ROOT / cxx,
            MSYS2_ROOT / objcopy,
            MSYS2_ROOT / "usr" / "bin" / "make.exe",
        )


TOOLCHAINS = (
    Toolchain("msys", "MSYS", "/usr/bin", "/usr/bin/gcc", "/usr/bin/objcopy"),
    Toolchain(
        "ucrt64",
        "UCRT64",
        "/ucrt64/bin:/usr/bin",
        "/ucrt64/bin/gcc",
        "/ucrt64/bin/objcopy",
    ),
)

OBJECTS = (
    "calculations.o",
    "geometry.o",
    "input.o",
    "matrix.o",
    "network.o",
    "shared.o",
    "fields.o",
    "ground.o",
    "main.zint.o",
    "misc.o",
    "radiation.o",
    "somnec.o",
)


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise AssertionError(f"could not create unique {label} mutant")
    return text.replace(old, new, 1)


def _parse_probe_output(output: str) -> tuple[ProbeResult, ...]:
    begin = "__ZINT_RESULTS_BEGIN__"
    end = "__ZINT_RESULTS_END__"
    if output.count(begin) != 1 or output.count(end) != 1:
        raise AssertionError(
            "compiled harness result markers are missing or duplicated"
        )
    payload = output.split(begin, 1)[1].split(end, 1)[0].strip()
    lines = payload.splitlines()
    if not lines or lines[0] != "target_x\tactual_x\tbranch\treal\timag":
        raise AssertionError("compiled harness header is invalid")

    results = []
    for line in lines[1:]:
        fields = line.split("\t")
        if len(fields) != 5:
            raise AssertionError(f"invalid compiled harness row: {line!r}")
        results.append(
            ProbeResult(
                target_x=float.fromhex(fields[0]),
                actual_x=float.fromhex(fields[1]),
                branch=fields[2],
                real=float.fromhex(fields[3]),
                imaginary=float.fromhex(fields[4]),
            )
        )
    return tuple(results)


class ZintSourceFidelityTests(unittest.TestCase):
    """Protect the exact four-line maintained-source correction."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.source_text = CALCULATIONS_PATH.read_text(encoding="utf-8")

    def test_reviewed_source_shape_is_present(self) -> None:
        routine = validate_zint_source_shape(self.source_text)
        self.assertEqual(routine.count("*zint="), 3)

    def test_source_guard_rejects_each_reviewed_mutation(self) -> None:
        mutants = {
            "small return removed": _replace_once(
                self.source_text,
                SMALL_TRANSFER,
                SMALL_ASSIGNMENT + "\n\n  } /* if( x <= 8.) */",
                "small return",
            ),
            "medium return removed": _replace_once(
                self.source_text,
                MEDIUM_TRANSFER,
                MEDIUM_ASSIGNMENT + "\n\n  } /* if( x <= 110.) */",
                "medium return",
            ),
            "cc5 exponent reverted": _replace_once(
                self.source_text,
                CC5_CORRECT,
                CC5_REVERTED,
                "cc5",
            ),
            "CN aliased to cc14": _replace_once(
                self.source_text,
                CN_CORRECT,
                CN_REVERTED,
                "CN",
            ),
        }
        for label, mutant in mutants.items():
            with self.subTest(mutation=label):
                with self.assertRaises(ZintSourceShapeError):
                    validate_zint_source_shape(mutant)


class ZintCompiledIntegrationTests(unittest.TestCase):
    """Compile and call the actual production object set on both toolchains."""

    results: dict[str, tuple[ProbeResult, ...]]

    @classmethod
    def setUpClass(cls) -> None:
        if os.name != "nt":
            raise unittest.SkipTest("direct MSYS/UCRT64 integration requires Windows")

        missing = sorted(
            {
                path
                for toolchain in TOOLCHAINS
                for path in toolchain.required_paths
                if not path.is_file()
            }
        )
        if missing:
            missing_text = ", ".join(str(path) for path in missing)
            raise unittest.SkipTest(
                f"installed C:\\msys64 tools are absent: {missing_text}"
            )

        BUILD_TEMP.mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(
            prefix="zint-direct-test-",
            dir=BUILD_TEMP,
        )
        cls.addClassCleanup(temporary.cleanup)
        temporary_root = Path(temporary.name)
        cls.results = {
            toolchain.name: cls._build_and_run(toolchain, temporary_root)
            for toolchain in TOOLCHAINS
        }

    @classmethod
    def _build_and_run(
        cls,
        toolchain: Toolchain,
        temporary_root: Path,
    ) -> tuple[ProbeResult, ...]:
        build_directory = temporary_root / toolchain.name
        relative_build = build_directory.relative_to(REPOSITORY_ROOT).as_posix()
        objects = " ".join(OBJECTS)
        script = f"""set -euo pipefail
export PATH={toolchain.path}
export TEMP=/tmp
export TMP=/tmp
export TMPDIR=/tmp
export LANG=C
export LC_ALL=C
export CONFIG_SITE=/dev/null
unset CFLAGS CPPFLAGS LDFLAGS LIBS MAKEFLAGS MFLAGS
repo=$PWD
build=\"$repo/{relative_build}\"
mkdir -p \"$build\"
cd \"$build\"
CC={toolchain.compiler} /usr/bin/bash \"$repo/src/nec2c/configure\"
/usr/bin/make -j1 V=1
{toolchain.objcopy} --redefine-sym main=nec2c_application_main \\
  main.o main.zint.o
{toolchain.compiler} -DHAVE_CONFIG_H -I. -I\"$repo/src/nec2c\" \\
  -Wall -O2 -o zint-direct.exe \"$repo/tests/zint_direct_harness.c\" \\
  {objects} -lm
/usr/bin/printf '%s\\n' __ZINT_RESULTS_BEGIN__
./zint-direct.exe
/usr/bin/printf '%s\\n' __ZINT_RESULTS_END__
"""
        environment = os.environ.copy()
        environment["MSYSTEM"] = toolchain.msystem
        environment["CHERE_INVOKING"] = "yes"
        completed = subprocess.run(
            [str(BASH_PATH), "--noprofile", "--norc", "-c", script],
            cwd=REPOSITORY_ROOT,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )
        if completed.returncode != 0:
            raise AssertionError(
                f"{toolchain.name} direct zint build/run failed with "
                f"exit {completed.returncode}\nSTDOUT:\n{completed.stdout}\n"
                f"STDERR:\n{completed.stderr}"
            )
        return _parse_probe_output(completed.stdout)

    def test_all_requested_values_and_regimes(self) -> None:
        for toolchain, results in self.results.items():
            self.assertEqual(len(results), len(EXPECTED_CASES), toolchain)
            for expected, actual in zip(EXPECTED_CASES, results, strict=True):
                with self.subTest(toolchain=toolchain, x=expected.target_x):
                    self.assertEqual(actual.target_x.hex(), expected.target_x.hex())
                    self.assertEqual(actual.branch, expected.branch)
                    self.assertTrue(math.isfinite(actual.real))
                    self.assertTrue(math.isfinite(actual.imaginary))
                    if expected.exact_binary64:
                        self.assertEqual(actual.real.hex(), expected.real.hex())
                        self.assertEqual(
                            actual.imaginary.hex(),
                            expected.imaginary.hex(),
                        )
                    else:
                        for component, observed, reference in (
                            ("real", actual.real, expected.real),
                            ("imaginary", actual.imaginary, expected.imaginary),
                        ):
                            error = abs(observed - reference)
                            allowed = (
                                ABSOLUTE_MEDIUM_TOLERANCE
                                + RELATIVE_MEDIUM_TOLERANCE * abs(reference)
                            )
                            self.assertLessEqual(
                                error,
                                allowed,
                                f"{toolchain} x={expected.target_x} {component}",
                            )

    def test_boundary_selection(self) -> None:
        expected_boundaries = {
            8.0: "small",
            8.001: "medium",
            110.0: "medium",
            110.001: "large",
        }
        for toolchain, results in self.results.items():
            by_target = {result.target_x: result for result in results}
            for target, branch in expected_boundaries.items():
                with self.subTest(toolchain=toolchain, x=target):
                    self.assertEqual(by_target[target].branch, branch)
            self.assertEqual(by_target[8.0].actual_x, 8.0)
            self.assertEqual(by_target[110.0].actual_x, 110.0)


if __name__ == "__main__":
    unittest.main()
