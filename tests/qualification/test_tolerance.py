# SPDX-License-Identifier: BSD-2-Clause
"""Focused tests for numerical and displayed-precision tolerances."""

from __future__ import annotations

from decimal import Decimal
import math
import unittest

from tools.qualification.tolerance import (
    NumericClassification,
    absolute_relative_limit,
    circular_phase_distance,
    compare_published_value,
    compare_displayed_intervals,
    compare_with_tolerance,
    displayed_precision_interval,
    is_near_zero,
    published_half_lsd,
    within_circular_tolerance,
    within_tolerance,
)


class ToleranceTests(unittest.TestCase):
    """Freeze absolute, relative, near-zero, phase, and precision behavior."""

    def test_absolute_plus_relative_limit_and_boundary(self) -> None:
        self.assertEqual(
            absolute_relative_limit(
                100.0,
                absolute_tolerance=0.01,
                relative_tolerance=0.001,
            ),
            0.11,
        )
        result = compare_with_tolerance(
            100.11,
            100.0,
            absolute_tolerance=0.01,
            relative_tolerance=0.001,
        )
        self.assertTrue(result.accepted)
        self.assertEqual(result.classification, NumericClassification.PASS)
        self.assertFalse(
            within_tolerance(
                100.12,
                100.0,
                absolute_tolerance=0.01,
                relative_tolerance=0.001,
            )
        )

    def test_near_zero_disables_relative_component(self) -> None:
        self.assertEqual(
            absolute_relative_limit(
                1.0e-12,
                absolute_tolerance=1.0e-9,
                relative_tolerance=1.0,
                near_zero_threshold=1.0e-10,
            ),
            1.0e-9,
        )
        self.assertTrue(is_near_zero(-1.0e-9, absolute_tolerance=1.0e-9))
        self.assertFalse(is_near_zero(1.1e-9, absolute_tolerance=1.0e-9))

    def test_circular_phase_wrap_and_tolerance(self) -> None:
        self.assertEqual(circular_phase_distance(359.0, 1.0), 2.0)
        self.assertEqual(circular_phase_distance(-179.0, 179.0), 2.0)
        self.assertTrue(
            within_circular_tolerance(
                359.0,
                1.0,
                absolute_tolerance_degrees=2.0,
            )
        )
        self.assertFalse(
            within_circular_tolerance(
                359.0,
                1.0,
                absolute_tolerance_degrees=1.9,
            )
        )

    def test_published_half_lsd_respects_exponent_and_trailing_zero(self) -> None:
        self.assertEqual(published_half_lsd("4.6029E-03"), Decimal("5E-8"))
        interval = displayed_precision_interval("1.230E+02")
        self.assertEqual(interval.center, Decimal("123.0"))
        self.assertEqual(interval.half_lsd, Decimal("0.05"))
        self.assertEqual(interval.lower, Decimal("122.95"))
        self.assertEqual(interval.upper, Decimal("123.05"))

    def test_published_value_classification_is_inclusive_at_half_lsd(self) -> None:
        exact = compare_published_value("82.6979", "82.6979")
        bounded = compare_published_value("82.69795", "82.6979")
        failed = compare_published_value("82.697951", "82.6979")
        self.assertEqual(exact.classification, NumericClassification.PASS)
        self.assertEqual(
            bounded.classification,
            NumericClassification.PASS_WITH_REFERENCE_PRECISION_LIMIT,
        )
        self.assertTrue(bounded.accepted)
        self.assertEqual(failed.classification, NumericClassification.FAIL)
        self.assertFalse(failed.accepted)

    def test_invalid_tolerances_and_nonfinite_values_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-negative"):
            within_tolerance(
                1.0,
                1.0,
                absolute_tolerance=-1.0,
                relative_tolerance=0.0,
            )
        with self.assertRaisesRegex(ValueError, "finite"):
            is_near_zero(math.inf, absolute_tolerance=1.0)
        with self.assertRaisesRegex(ValueError, "finite"):
            compare_published_value("NaN", "1.0")
        with self.assertRaisesRegex(ValueError, "stripped"):
            displayed_precision_interval(" 1.0")

    def test_candidate_and_reference_display_intervals_may_overlap(self) -> None:
        limited = compare_displayed_intervals("8.2698E+01", "82.6979")
        failed = compare_displayed_intervals("8.2699E+01", "82.6979")
        self.assertEqual(
            limited.classification,
            NumericClassification.PASS_WITH_REFERENCE_PRECISION_LIMIT,
        )
        self.assertTrue(limited.accepted)
        self.assertEqual(failed.classification, NumericClassification.FAIL)


if __name__ == "__main__":
    unittest.main()
