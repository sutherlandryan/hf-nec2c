# SPDX-License-Identifier: BSD-2-Clause
"""Explicit numerical tolerance and published-precision helpers."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
import math
from numbers import Real


class NumericClassification(str, Enum):
    """Machine-readable result classes used by qualification checks."""

    PASS = "PASS"
    PASS_WITH_REFERENCE_PRECISION_LIMIT = "PASS_WITH_REFERENCE_PRECISION_LIMIT"
    FAIL = "FAIL"


@dataclass(frozen=True)
class ToleranceComparison:
    """Result of an absolute-plus-relative numerical comparison."""

    actual: float
    expected: float
    absolute_error: float
    allowed_error: float
    classification: NumericClassification

    @property
    def accepted(self) -> bool:
        return self.classification is NumericClassification.PASS


@dataclass(frozen=True)
class PublishedInterval:
    """Rounding interval implied by one displayed reference literal."""

    literal: str
    center: Decimal
    half_lsd: Decimal
    lower: Decimal
    upper: Decimal


@dataclass(frozen=True)
class PublishedComparison:
    """Candidate classification against a displayed reference interval."""

    actual: Decimal
    interval: PublishedInterval
    absolute_error: Decimal
    classification: NumericClassification

    @property
    def accepted(self) -> bool:
        return self.classification is not NumericClassification.FAIL


@dataclass(frozen=True)
class DisplayedIntervalComparison:
    """Comparison of intervals implied by candidate and reference displays."""

    candidate: PublishedInterval
    reference: PublishedInterval
    classification: NumericClassification

    @property
    def accepted(self) -> bool:
        return self.classification is not NumericClassification.FAIL


def absolute_relative_limit(
    reference: Real,
    *,
    absolute_tolerance: Real,
    relative_tolerance: Real,
    near_zero_threshold: Real = 0.0,
) -> float:
    """Return ``abs_tol + rel_tol * abs(reference)`` outside near zero.

    Relative tolerance is deliberately disabled when the reference magnitude
    is at or below ``near_zero_threshold``.
    """

    reference_value = _finite_real(reference, "reference")
    absolute = _nonnegative_real(absolute_tolerance, "absolute_tolerance")
    relative = _nonnegative_real(relative_tolerance, "relative_tolerance")
    near_zero = _nonnegative_real(near_zero_threshold, "near_zero_threshold")
    if abs(reference_value) <= near_zero:
        return absolute
    return absolute + relative * abs(reference_value)


def compare_with_tolerance(
    actual: Real,
    expected: Real,
    *,
    absolute_tolerance: Real,
    relative_tolerance: Real,
    near_zero_threshold: Real = 0.0,
) -> ToleranceComparison:
    """Compare finite values using an explicit absolute-plus-relative rule."""

    actual_value = _finite_real(actual, "actual")
    expected_value = _finite_real(expected, "expected")
    limit = absolute_relative_limit(
        expected_value,
        absolute_tolerance=absolute_tolerance,
        relative_tolerance=relative_tolerance,
        near_zero_threshold=near_zero_threshold,
    )
    error = abs(actual_value - expected_value)
    classification = (
        NumericClassification.PASS if error <= limit else NumericClassification.FAIL
    )
    return ToleranceComparison(
        actual=actual_value,
        expected=expected_value,
        absolute_error=error,
        allowed_error=limit,
        classification=classification,
    )


def within_tolerance(
    actual: Real,
    expected: Real,
    *,
    absolute_tolerance: Real,
    relative_tolerance: Real,
    near_zero_threshold: Real = 0.0,
) -> bool:
    """Return whether values satisfy the explicit comparison rule."""

    return compare_with_tolerance(
        actual,
        expected,
        absolute_tolerance=absolute_tolerance,
        relative_tolerance=relative_tolerance,
        near_zero_threshold=near_zero_threshold,
    ).accepted


def is_near_zero(value: Real, *, absolute_tolerance: Real) -> bool:
    """Compare a finite value with zero using only an absolute tolerance."""

    candidate = _finite_real(value, "value")
    tolerance = _nonnegative_real(absolute_tolerance, "absolute_tolerance")
    return abs(candidate) <= tolerance


def circular_phase_distance(
    actual_degrees: Real,
    expected_degrees: Real,
    *,
    period_degrees: Real = 360.0,
) -> float:
    """Return the shortest unsigned distance between two wrapped phases."""

    actual = _finite_real(actual_degrees, "actual_degrees")
    expected = _finite_real(expected_degrees, "expected_degrees")
    period = _finite_real(period_degrees, "period_degrees")
    if period <= 0.0:
        raise ValueError("period_degrees must be positive")
    wrapped = (actual - expected + period / 2.0) % period - period / 2.0
    return abs(wrapped)


def within_circular_tolerance(
    actual_degrees: Real,
    expected_degrees: Real,
    *,
    absolute_tolerance_degrees: Real,
    period_degrees: Real = 360.0,
) -> bool:
    """Return whether wrapped phases are within an absolute angle tolerance."""

    tolerance = _nonnegative_real(
        absolute_tolerance_degrees,
        "absolute_tolerance_degrees",
    )
    return (
        circular_phase_distance(
            actual_degrees,
            expected_degrees,
            period_degrees=period_degrees,
        )
        <= tolerance
    )


def published_half_lsd(displayed_literal: str) -> Decimal:
    """Return half one unit in the last displayed digit of a finite literal."""

    value = _displayed_decimal(displayed_literal)
    unit = Decimal(1).scaleb(value.as_tuple().exponent)
    return unit.copy_abs() / Decimal(2)


def displayed_precision_interval(displayed_literal: str) -> PublishedInterval:
    """Return the inclusive half-LSD rounding interval for a displayed value."""

    center = _displayed_decimal(displayed_literal)
    half_lsd = published_half_lsd(displayed_literal)
    return PublishedInterval(
        literal=displayed_literal,
        center=center,
        half_lsd=half_lsd,
        lower=center - half_lsd,
        upper=center + half_lsd,
    )


def compare_published_value(
    actual: Decimal | Real | str,
    displayed_literal: str,
) -> PublishedComparison:
    """Classify a candidate against a displayed reference's half-LSD interval."""

    candidate = _candidate_decimal(actual)
    interval = displayed_precision_interval(displayed_literal)
    error = abs(candidate - interval.center)
    if candidate < interval.lower or candidate > interval.upper:
        classification = NumericClassification.FAIL
    elif candidate == interval.center:
        classification = NumericClassification.PASS
    else:
        classification = NumericClassification.PASS_WITH_REFERENCE_PRECISION_LIMIT
    return PublishedComparison(
        actual=candidate,
        interval=interval,
        absolute_error=error,
        classification=classification,
    )


def compare_displayed_intervals(
    candidate_literal: str,
    reference_literal: str,
) -> DisplayedIntervalComparison:
    """Compare printed values without inventing unavailable digits.

    Equal centers pass directly. Otherwise, intersecting half-LSD rounding
    intervals pass with an explicit reference-precision limitation.
    """

    candidate = displayed_precision_interval(candidate_literal)
    reference = displayed_precision_interval(reference_literal)
    if candidate.center == reference.center:
        classification = NumericClassification.PASS
    elif candidate.upper < reference.lower or reference.upper < candidate.lower:
        classification = NumericClassification.FAIL
    else:
        classification = NumericClassification.PASS_WITH_REFERENCE_PRECISION_LIMIT
    return DisplayedIntervalComparison(
        candidate=candidate,
        reference=reference,
        classification=classification,
    )


def _finite_real(value: Real, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{label} must be a real number")
    converted = float(value)
    if not math.isfinite(converted):
        raise ValueError(f"{label} must be finite")
    return converted


def _nonnegative_real(value: Real, label: str) -> float:
    converted = _finite_real(value, label)
    if converted < 0.0:
        raise ValueError(f"{label} must be non-negative")
    return converted


def _displayed_decimal(literal: str) -> Decimal:
    if not isinstance(literal, str):
        raise TypeError("displayed_literal must be str")
    if not literal or literal != literal.strip():
        raise ValueError("displayed_literal must be a stripped numeric literal")
    try:
        value = Decimal(literal)
    except InvalidOperation as error:
        raise ValueError("displayed_literal is not numeric") from error
    if not value.is_finite():
        raise ValueError("displayed_literal must be finite")
    return value


def _candidate_decimal(value: Decimal | Real | str) -> Decimal:
    if isinstance(value, bool):
        raise TypeError("actual must be Decimal, real, or numeric str")
    try:
        candidate = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ValueError("actual is not numeric") from error
    if not candidate.is_finite():
        raise ValueError("actual must be finite")
    return candidate
