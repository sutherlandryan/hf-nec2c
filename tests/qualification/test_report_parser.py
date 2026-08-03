# SPDX-License-Identifier: BSD-2-Clause
"""Focused tests for stable NEC report parsing."""

from __future__ import annotations

from pathlib import Path
import unittest

from tools.qualification.report_parser import numeric_tokens, parse_report


FIXTURES = Path(__file__).with_name("fixtures")


class ReportParserTests(unittest.TestCase):
    """Exercise both solver shapes and repeated physical snapshots."""

    def test_nec2c_repeated_frequency_snapshots_and_identities(self) -> None:
        report = parse_report(
            (FIXTURES / "nec2c-report.txt").read_text(encoding="utf-8"),
            solver="NEC2C",
        )

        self.assertEqual(report.solver, "nec2c")
        self.assertEqual(len(report.snapshots), 2)
        first, loaded = report.snapshots
        self.assertEqual(first.frequency_mhz, 14.2)
        self.assertEqual(loaded.frequency_mhz, 14.2)
        self.assertEqual(first.loading, "not_loaded")
        self.assertEqual(loaded.loading, "loaded")

        feed = first.feed(1, 6)
        self.assertEqual(feed.identity, (1, 6))
        self.assertEqual(feed.raw_numeric_literals[6], "6.7276E+01")
        self.assertAlmostEqual(feed.resistance_ohms, 67.276)
        self.assertAlmostEqual(feed.reactance_ohms, -35.958)
        current = first.current(1, 1)
        self.assertAlmostEqual(current.real_amperes, 1.25e-3)
        self.assertAlmostEqual(current.imaginary_amperes, -2.5e-4)
        self.assertAlmostEqual(current.phase_degrees, -11.31)

        self.assertIsNotNone(first.power_budget)
        assert first.power_budget is not None
        self.assertEqual(first.power_budget.input_power_watts, 5.7807e-3)
        self.assertEqual(first.power_budget.efficiency_percent, 100.0)
        pattern = first.far_field(90.0, 0.0)
        self.assertEqual(pattern.identity, (90.0, 0.0))
        self.assertEqual(pattern.total_gain_db, 2.1)
        self.assertEqual(pattern.minor_gain_db, -999.99)

        self.assertEqual(
            [item.severity for item in report.diagnostics],
            ["warning", "failure"],
        )
        self.assertEqual(first.diagnostics[0].severity, "warning")
        self.assertEqual(loaded.diagnostics[0].severity, "failure")
        self.assertTrue(report.has_failures)

    def test_nec2dx_d_exponents_ground_and_error(self) -> None:
        report = parse_report(
            (FIXTURES / "nec2dx-report.txt").read_text(encoding="utf-8"),
            solver="nec2dx",
        )

        self.assertEqual(len(report.snapshots), 1)
        snapshot = report.snapshots[0]
        self.assertEqual(snapshot.frequency_mhz, 299.8)
        self.assertEqual(snapshot.ground, "perfect_ground")
        self.assertAlmostEqual(snapshot.feed(0, 5).reactance_ohms, 9.9058)
        self.assertAlmostEqual(snapshot.current(0, 5).phase_degrees, -5.317)
        self.assertEqual(snapshot.far_field(90.0, 0.0).total_gain_db, 8.52)
        self.assertEqual(report.diagnostics[0].severity, "error")
        self.assertTrue(report.has_failures)

    def test_numeric_tokenizer_separates_concatenated_signed_fields(self) -> None:
        self.assertEqual(
            numeric_tokens("1.2345E-03-6.7890E-04 2.5D+01-.125"),
            ("1.2345E-03", "-6.7890E-04", "2.5D+01", "-.125"),
        )

    def test_missing_identity_is_explicit(self) -> None:
        report = parse_report(
            (FIXTURES / "nec2c-report.txt").read_text(encoding="utf-8")
        )
        with self.assertRaisesRegex(KeyError, "feed identity not found"):
            report.snapshots[0].feed(99, 99)

    def test_diagnostic_only_report_remains_inspectable(self) -> None:
        report = parse_report("FATAL ERROR: synthetic stop\n", solver="nec2c")
        self.assertEqual(report.snapshots, ())
        self.assertEqual(report.diagnostics[0].severity, "error")
        self.assertTrue(report.has_failures)

    def test_charge_density_rows_are_not_segment_currents(self) -> None:
        text = """
FREQUENCY = 1.0 MHZ
ANTENNA INPUT PARAMETERS
 0 1 1 0 1 0 1 0 1 0 0.5
CURRENTS AND LOCATION
 1 0 0 0 0 1 1 0 1 0
CHARGE DENSITIES
 1 0 0 0 0 1 9 0 9 0
POWER BUDGET
 INPUT POWER = 0.5
"""
        report = parse_report(text)
        self.assertEqual(len(report.snapshots[0].currents), 1)

    def test_null_pattern_rows_and_average_gain_are_preserved(self) -> None:
        text = """
FREQUENCY = 30 MHZ
ANTENNA INPUT PARAMETERS
 0 5 1 0 1 0 1 0 1 0 0.5
RADIATION PATTERNS
 0 0 -999.99 -999.99 -999.99 0 0 0 0 0 0
 90 0 8.52 -999.99 8.52 0 0 LINEAR 1.0 0 0 0
AVERAGE POWER GAIN = 2.02794E+00
"""
        snapshot = parse_report(text).snapshots[0]
        self.assertEqual(len(snapshot.far_fields), 2)
        self.assertEqual(snapshot.far_field(0, 0).sense, "UNDEFINED")
        self.assertEqual(snapshot.average_power_gain, 2.02794)
        self.assertEqual(snapshot.average_power_gain_literal, "2.02794E+00")


if __name__ == "__main__":
    unittest.main()
