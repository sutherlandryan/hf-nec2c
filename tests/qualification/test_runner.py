# SPDX-License-Identifier: BSD-2-Clause
"""Focused tests for the qualification comparison runner."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.qualification.run_qualification import (
    QualificationInputError,
    qualification_summary,
    run_qualification,
)


_REPORT_TEMPLATE = """\
                         --------- FREQUENCY --------
                          FREQUENCY : 3.0000E+02 MHz
                          STRUCTURE IMPEDANCE LOADING

                 --------- ANTENNA INPUT PARAMETERS ---------
 TAG SEG VOLTAGE REAL IMAG CURRENT REAL IMAG IMPEDANCE REAL IMAG ADMITTANCE REAL IMAG POWER
   0   5 1.0000E+00 0.0000E+00 6.6377E-03-4.2683E-03 {resistance} 6.8538E+01 6.6377E-03-4.2683E-03 3.3188E-03

                    -------- CURRENTS AND LOCATION --------
 SEG TAG X Y Z LENGTH CURRENT REAL IMAG MAGN PHASE
   1   0 0.0000 0.0000-0.2188 0.06250 1.0000E-03-2.0000E-04 1.0198E-03-11.310
   8   0 0.0000 0.0000 0.2188 0.06250 1.0000E-03-2.0000E-04 1.0198E-03-11.310

                       ---------- POWER BUDGET ---------
                       INPUT POWER   = 3.3188E-03 Watts
                       RADIATED POWER= 2.5715E-03 Watts
                       STRUCTURE LOSS= 7.4730E-04 Watts
                       NETWORK LOSS  = 0.0000E+00 Watts
                       EFFICIENCY    = 77.48 Percent

                     ---------- RADIATION PATTERNS -----------
 THETA PHI MAJOR MINOR TOTAL AXIAL TILT SENSE E(THETA) MAG PHASE E(PHI) MAG PHASE
  90.00 {pattern_phi} 2.10-999.99 2.10 0.0000-0.00 LINEAR 7.5039E-01 116.56 0.0000E+00 {e_phi_phase}
"""


class QualificationRunnerTests(unittest.TestCase):
    """Exercise primary blocking and secondary diagnostic boundaries."""

    def _workspace(
        self,
        root: Path,
        *,
        reference_literal: str,
        msys_resistance: str = "1.0658E+02",
        ucrt_resistance: str = "1.0658E+02",
        nec2dx_resistance: str = "1.1243E+02",
        msys_e_phi_phase: str = "0.00",
        ucrt_e_phi_phase: str = "0.00",
        nec2dx_e_phi_phase: str = "0.00",
        pattern_phi: str = "0.00",
        maximum_expected_phi: float | None = None,
    ) -> tuple[Path, Path, Path, Path]:
        result_roots = []
        for name in ("msys", "ucrt64", "nec2dx"):
            path = root / name
            path.mkdir()
            result_roots.append(path)

        cases = []
        for index in range(6):
            case_id = f"case-{index}"
            deck_path = root / f"{case_id}.nec"
            deck_path.write_text(f"CM {case_id}\nEN\n", encoding="ascii")
            deck_hash = hashlib.sha256(deck_path.read_bytes()).hexdigest()
            checks = []
            invariants = []
            if index == 0:
                checks.append(
                    {
                        "id": "published-loaded-resistance",
                        "snapshot": 0,
                        "observable": "feed",
                        "identity": [0, 5],
                        "field": "resistance_ohms",
                        "reference_literal": reference_literal,
                    }
                )
                invariants.extend(
                    [
                        {
                            "id": "power-closes",
                            "type": "power_conservation",
                            "snapshot": 0,
                        },
                        {
                            "id": "currents-mirror",
                            "type": "current_mirror",
                            "snapshot": 0,
                            "pairs": [[[0, 1], [0, 8]]],
                        },
                        {
                            "id": "scaled-current-position",
                            "type": "current_position",
                            "snapshot": 0,
                            "identity": [0, 1],
                            "expected": {
                                "x_wavelengths": 0.0,
                                "y_wavelengths": 0.0,
                                "z_wavelengths": -0.2188,
                                "length_wavelengths": 0.0625,
                            },
                            "absolute_tolerance": 5e-5,
                            "relative_tolerance": 0.0,
                        },
                    ]
                )
                if maximum_expected_phi is not None:
                    invariants.append(
                        {
                            "id": "wrapped-maximum-direction",
                            "type": "maximum_direction",
                            "snapshot": 0,
                            "theta_degrees": 90.0,
                            "phi_degrees": maximum_expected_phi,
                        }
                    )
            cases.append(
                {
                    "case_id": case_id,
                    "deck_path": deck_path.name,
                    "deck_sha256": deck_hash,
                    "authoritative_checks": checks,
                    "invariants": invariants,
                }
            )
            reports = (
                _REPORT_TEMPLATE.format(
                    resistance=msys_resistance,
                    e_phi_phase=msys_e_phi_phase,
                    pattern_phi=pattern_phi,
                ),
                _REPORT_TEMPLATE.format(
                    resistance=ucrt_resistance,
                    e_phi_phase=ucrt_e_phi_phase,
                    pattern_phi=pattern_phi,
                ),
                _REPORT_TEMPLATE.format(
                    resistance=nec2dx_resistance,
                    e_phi_phase=nec2dx_e_phi_phase,
                    pattern_phi=pattern_phi,
                ),
            )
            for result_root, report in zip(result_roots, reports):
                (result_root / f"{case_id}.out").write_text(
                    report,
                    encoding="ascii",
                )

        manifest = root / "manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "repository_root": ".",
                    "tolerances": {
                        "undefined_phase_magnitude_v_per_m": 5.0e-12,
                        "secondary_diagnostic_by_observable_class": {
                            "feed_impedance": {"absolute": 0.006, "relative": 5e-5}
                        },
                    },
                    "cases": cases,
                }
            ),
            encoding="utf-8",
        )
        return (manifest, *result_roots)

    def test_published_ld5_mismatch_blocks_matching_primary_builds(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            paths = self._workspace(
                Path(temporary),
                reference_literal="112.430",
            )
            result = run_qualification(*paths)
            summary = qualification_summary(result)

        self.assertEqual(result["overall_status"], "NUMERICAL_QUALIFICATION_BLOCKED")
        first = result["cases"][0]
        self.assertEqual(first["case_status"], "BLOCKED_BY_NUMERICAL_DISCREPANCY")
        self.assertEqual(first["authoritative"][0]["classification"], "FAIL")
        self.assertTrue(
            all(
                item["classification"] in {"PASS", "NOT_APPLICABLE"}
                for item in first["cross_platform"]
            )
        )
        self.assertEqual(len(summary["authoritative_failures"]), 1)
        self.assertEqual(
            summary["authoritative_failures"][0]["id"],
            "published-loaded-resistance",
        )
        self.assertEqual(len(summary["cases"][0]["reports"]), 3)
        self.assertNotIn("cross_platform", summary["cases"][0])
        self.assertTrue(
            any(
                item["classification"] == "SECONDARY_DISAGREEMENT"
                for item in first["secondary_diagnostic"]
            )
        )

    def test_secondary_disagreement_cannot_block_or_rescue(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            paths = self._workspace(
                Path(temporary),
                reference_literal="1.0658E+02",
            )
            first = run_qualification(*paths)
            second = run_qualification(*paths)
            first_summary = qualification_summary(first)
            second_summary = qualification_summary(second)

        self.assertEqual(first, second)
        self.assertEqual(first_summary, second_summary)
        self.assertEqual(first["overall_status"], "NUMERICAL_QUALIFICATION_PASSED")
        self.assertEqual(
            first["cases"][0]["case_status"],
            "QUALIFIED_FOR_INTENDED_SUBSET",
        )
        self.assertEqual(
            first["cases"][1]["case_status"],
            "QUALIFIED_WITH_DOCUMENTED_GAP",
        )
        self.assertEqual(
            first["cases"][0]["authoritative"][0]["classification"], "PASS"
        )
        self.assertTrue(
            any(
                item["classification"] == "SECONDARY_DISAGREEMENT"
                for item in first["cases"][0]["secondary_diagnostic"]
            )
        )
        self.assertTrue(first_summary["secondary_disagreements"])
        self.assertTrue(
            all(
                set(group)
                >= {
                    "case_id",
                    "snapshot_index",
                    "observable_class",
                    "count",
                }
                for group in first_summary["secondary_disagreements"]
            )
        )
        position_results = [
            item
            for item in first["cases"][0]["invariants"]
            if item["type"] == "current_position"
        ]
        self.assertEqual(len(position_results), 8)
        self.assertTrue(
            all(item["classification"] == "PASS" for item in position_results)
        )

    def test_phase_at_numerical_field_null_is_not_applicable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            paths = self._workspace(
                Path(temporary),
                reference_literal="1.0658E+02",
                ucrt_e_phi_phase="137.00",
            )
            result = run_qualification(*paths)

        phase = next(
            item
            for item in result["cases"][0]["cross_platform"]
            if item["id"].endswith("e_phi_phase_degrees")
        )
        self.assertEqual(phase["classification"], "NOT_APPLICABLE")
        self.assertEqual(phase["reason"], "phase undefined at numerical field null")
        self.assertEqual(result["overall_status"], "NUMERICAL_QUALIFICATION_PASSED")

    def test_cross_platform_mismatch_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            paths = self._workspace(
                Path(temporary),
                reference_literal="1.0658E+02",
                ucrt_resistance="1.0758E+02",
            )
            result = run_qualification(*paths)

        self.assertEqual(result["overall_status"], "NUMERICAL_QUALIFICATION_BLOCKED")
        self.assertTrue(
            any(
                item["classification"] == "FAIL"
                for item in result["cases"][0]["cross_platform"]
            )
        )

    def test_maximum_direction_wraps_phi_circularly(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            paths = self._workspace(
                Path(temporary),
                reference_literal="1.0658E+02",
                pattern_phi="360.00",
                maximum_expected_phi=0.0,
            )
            result = run_qualification(*paths)

        maximum_records = [
            item
            for item in result["cases"][0]["invariants"]
            if item["type"] == "maximum_direction"
        ]
        self.assertEqual(len(maximum_records), 2)
        self.assertTrue(all(item["absolute_error"] == 0.0 for item in maximum_records))
        self.assertTrue(
            all(item["classification"] == "PASS" for item in maximum_records)
        )
        self.assertEqual(result["overall_status"], "NUMERICAL_QUALIFICATION_PASSED")

    def test_deck_hash_mismatch_is_rejected_before_comparison(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths = self._workspace(root, reference_literal="1.0658E+02")
            (root / "case-3.nec").write_text("CM tampered\nEN\n", encoding="ascii")
            with self.assertRaisesRegex(QualificationInputError, "SHA-256 mismatch"):
                run_qualification(*paths)

    def test_metadata_hash_mismatch_is_rejected_before_comparison(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths = self._workspace(root, reference_literal="1.0658E+02")
            manifest_path = paths[0]
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            metadata_path = root / "case-0.json"
            metadata_path.write_text('{"purpose":"original"}\n', encoding="utf-8")
            manifest["cases"][0]["metadata_path"] = metadata_path.name
            manifest["cases"][0]["metadata_sha256"] = hashlib.sha256(
                metadata_path.read_bytes()
            ).hexdigest()
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            metadata_path.write_text('{"purpose":"mutated"}\n', encoding="utf-8")

            with self.assertRaisesRegex(
                QualificationInputError,
                "metadata SHA-256 mismatch",
            ):
                run_qualification(*paths)


if __name__ == "__main__":
    unittest.main()
