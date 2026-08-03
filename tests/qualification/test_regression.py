# SPDX-License-Identifier: BSD-2-Clause
"""Focused tests for the frozen v1-to-v2 parsed-report regression layer."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.qualification.regression import (
    EXAMPLE2_CASE_ID,
    FROZEN_CASE_IDS,
    RegressionComparisonError,
    canonical_dataclass_bytes,
    compare_baseline_regression,
    parsed_dataclass_sha256,
)
from tools.qualification.report_parser import parse_report


_SNAPSHOT_TEMPLATE = """\
                         --------- FREQUENCY --------
                          FREQUENCY : {frequency} MHz
                          {loading}
                          {ground}

                 --------- ANTENNA INPUT PARAMETERS ---------
 TAG SEG VOLTAGE REAL IMAG CURRENT REAL IMAG IMPEDANCE REAL IMAG ADMITTANCE REAL IMAG POWER
   0   5 1.0000E+00 0.0000E+00 {current_real} {current_imaginary} {resistance} {reactance} 6.0000E-03-4.0000E-03 {input_power}

                    -------- CURRENTS AND LOCATION --------
 SEG TAG X Y Z LENGTH CURRENT REAL IMAG MAGN PHASE
   1   0 0.0000 0.0000-0.2188 0.06250 1.0000E-03-2.0000E-04 1.0198E-03-11.310

                       ---------- POWER BUDGET ---------
                       INPUT POWER   = {input_power} Watts
                       RADIATED POWER= {radiated_power} Watts
                       STRUCTURE LOSS= {structure_loss} Watts
                       NETWORK LOSS  = 0.0000E+00 Watts
                       EFFICIENCY    = {efficiency} Percent
"""


def _snapshot(
    index: int,
    *,
    loaded: bool = False,
    v2_loaded: bool = False,
) -> str:
    values = {
        "frequency": f"{200 + index * 25}.000",
        "loading": (
            "STRUCTURE IMPEDANCE LOADING" if loaded else "THIS STRUCTURE IS NOT LOADED"
        ),
        "ground": "FREE SPACE",
        "current_real": "6.6377E-03",
        "current_imaginary": "-4.2683E-03",
        "resistance": "1.0658E+02",
        "reactance": "6.8538E+01",
        "input_power": "3.3188E-03",
        "radiated_power": "2.5716E-03",
        "structure_loss": "7.4727E-04",
        "efficiency": "77.48",
    }
    if v2_loaded:
        values.update(
            {
                "current_real": "6.6443E-03",
                "current_imaginary": "-3.8666E-03",
                "resistance": "1.1243E+02",
                "reactance": "6.5428E+01",
                "input_power": "3.3222E-03",
                "radiated_power": "2.4402E-03",
                "structure_loss": "8.8199E-04",
                "efficiency": "73.45",
            }
        )
    return _SNAPSHOT_TEMPLATE.format(**values)


class RegressionComparisonTests(unittest.TestCase):
    """Exercise exact equality, the sole exception, and mutation rejection."""

    def _workspace(self, root: Path) -> tuple[Path, Path, Path, Path, Path]:
        snapshot_counts = {
            "minimal-free-space-dipole": 1,
            "nec2-part3-example1-lumped-load": 2,
            EXAMPLE2_CASE_ID: 4,
            "nec2-part3-example3-perfect-ground": 1,
            "nec2-part3-example3-reflection-ground": 1,
            "connected-scaled-inverted-v": 1,
            "minimal-dipole-21-segment": 1,
            "minimal-dipole-41-segment": 1,
        }
        manifest = root / "numerical-qualification-v0.0.5f-b.json"
        manifest.write_text(
            json.dumps(
                {
                    "cases": [
                        {
                            "case_id": case_id,
                            "invariants": [
                                {
                                    "id": f"{case_id}.snapshot-count",
                                    "type": "snapshot_count",
                                    "expected": snapshot_counts[case_id],
                                }
                            ],
                        }
                        for case_id in FROZEN_CASE_IDS
                    ]
                }
            ),
            encoding="utf-8",
        )

        roots = [
            root / name for name in ("v1-msys", "v1-ucrt64", "v2-msys", "v2-ucrt64")
        ]
        for result_root in roots:
            result_root.mkdir()
            is_v2 = result_root.name.startswith("v2-")
            for case_id in FROZEN_CASE_IDS:
                snapshots = []
                for index in range(snapshot_counts[case_id]):
                    loaded = case_id == EXAMPLE2_CASE_ID and index == 3
                    snapshots.append(
                        _snapshot(
                            index,
                            loaded=loaded,
                            v2_loaded=is_v2 and loaded,
                        )
                    )
                (result_root / f"{case_id}.out").write_text(
                    "".join(snapshots),
                    encoding="utf-8",
                    newline="\n",
                )
        return (manifest, *roots)

    def test_happy_path_is_deterministic_and_summary_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            paths = self._workspace(Path(temporary))
            first = compare_baseline_regression(*paths)
            second = compare_baseline_regression(*paths)

        self.assertEqual(first, second)
        self.assertEqual(first["status"], "PASS")
        self.assertEqual(first["case_count"], 8)
        for solver in ("msys_nec2c", "ucrt64_nec2c"):
            cases = {
                case["case_id"]: case for case in first["solvers"][solver]["cases"]
            }
            self.assertEqual(
                cases[EXAMPLE2_CASE_ID]["changed_snapshot_indices"],
                [3],
            )
            self.assertTrue(
                all(
                    not case["changed_snapshot_indices"]
                    for case_id, case in cases.items()
                    if case_id != EXAMPLE2_CASE_ID
                )
            )
            snapshots = cases[EXAMPLE2_CASE_ID]["snapshots"]
            self.assertEqual(
                [item["equal"] for item in snapshots], [True] * 3 + [False]
            )

        loaded = first["example2_loaded_named_values"]["msys_nec2c"]
        self.assertEqual(
            loaded["prior"]["feed_current_imaginary_amperes"]["literal"],
            "-4.2683E-03",
        )
        self.assertEqual(
            loaded["v2"]["feed_current_imaginary_amperes"]["literal"],
            "-3.8666E-03",
        )

    def test_canonical_digest_covers_complete_snapshot_context(self) -> None:
        report = parse_report(_snapshot(0), solver="msys_nec2c")
        snapshot = report.snapshots[0]
        first = canonical_dataclass_bytes(snapshot)
        second = canonical_dataclass_bytes(snapshot)
        self.assertEqual(first, second)
        self.assertEqual(
            parsed_dataclass_sha256(snapshot), parsed_dataclass_sha256(snapshot)
        )
        self.assertIn(b'"ground":"free_space"', first)
        self.assertIn(b'"raw_numeric_literals"', first)

    def test_unaffected_numeric_literal_mutation_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            paths = self._workspace(Path(temporary))
            report = paths[3] / "minimal-free-space-dipole.out"
            report.write_text(
                report.read_text(encoding="utf-8").replace(
                    "1.0658E+02",
                    "1.0659E+02",
                    1,
                ),
                encoding="utf-8",
                newline="\n",
            )
            with self.assertRaisesRegex(
                RegressionComparisonError,
                "must remain exactly unchanged",
            ):
                compare_baseline_regression(*paths)

    def test_loaded_context_mutation_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            paths = self._workspace(Path(temporary))
            report = paths[3] / f"{EXAMPLE2_CASE_ID}.out"
            text = report.read_text(encoding="utf-8")
            loaded_marker = text.rfind("FREE SPACE")
            self.assertGreaterEqual(loaded_marker, 0)
            text = text[:loaded_marker] + "PERFECT GROUND" + text[loaded_marker + 10 :]
            report.write_text(text, encoding="utf-8", newline="\n")
            with self.assertRaisesRegex(
                RegressionComparisonError,
                "context or structure changed",
            ):
                compare_baseline_regression(*paths)

    def test_report_diagnostic_mutation_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            paths = self._workspace(Path(temporary))
            report = paths[3] / f"{EXAMPLE2_CASE_ID}.out"
            report.write_text(
                report.read_text(encoding="utf-8")
                + "FATAL ERROR: synthetic regression\n",
                encoding="utf-8",
                newline="\n",
            )
            with self.assertRaisesRegex(
                RegressionComparisonError,
                "report-level diagnostics changed",
            ):
                compare_baseline_regression(*paths)

    def test_forbidden_example2_snapshot_mutation_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            paths = self._workspace(Path(temporary))
            report = paths[3] / f"{EXAMPLE2_CASE_ID}.out"
            report.write_text(
                report.read_text(encoding="utf-8").replace(
                    "225.000",
                    "226.000",
                    1,
                ),
                encoding="utf-8",
                newline="\n",
            )
            with self.assertRaisesRegex(
                RegressionComparisonError,
                "forbidden changed snapshot",
            ):
                compare_baseline_regression(*paths)

    def test_loaded_snapshot_change_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            paths = self._workspace(Path(temporary))
            for filename in FROZEN_CASE_IDS:
                source = paths[1] / f"{filename}.out"
                destination = paths[3] / f"{filename}.out"
                destination.write_bytes(source.read_bytes())
            with self.assertRaisesRegex(
                RegressionComparisonError,
                "required loaded snapshot 3 did not change",
            ):
                compare_baseline_regression(*paths)


if __name__ == "__main__":
    unittest.main()
