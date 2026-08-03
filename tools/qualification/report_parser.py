# SPDX-License-Identifier: BSD-2-Clause
"""Parse stable physical results from NEC2C and NEC2DX text reports.

The parser deliberately keys off report headings and physical row identities.
It does not depend on page numbers, absolute line numbers, or fixed columns.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Iterable


_NUMBER_RE = re.compile(r"[+-]?(?:(?:\d+(?:\.\d*)?)|(?:\.\d+))(?:[DdEe][+-]?\d+)?")
_INTEGER_RE = re.compile(r"[+-]?\d+")
_FREQUENCY_RE = re.compile(
    rf"\bFREQUENCY\s*(?::|=)\s*({_NUMBER_RE.pattern})\s*(?:MHZ)?\b",
    re.IGNORECASE,
)
_SENSE_RE = re.compile(r"\b(LINEAR|RIGHT|LEFT)\b", re.IGNORECASE)


@dataclass(frozen=True)
class Diagnostic:
    """A warning or failure marker preserved with its report location."""

    severity: str
    line_number: int
    text: str


@dataclass(frozen=True)
class FeedImpedance:
    """One driven-segment row, identified by wire tag and segment number."""

    tag: int
    segment: int
    voltage_real: float
    voltage_imaginary: float
    current_real: float
    current_imaginary: float
    resistance_ohms: float
    reactance_ohms: float
    admittance_real_mhos: float
    admittance_imaginary_mhos: float
    power_watts: float
    raw_numeric_literals: tuple[str, ...]

    @property
    def identity(self) -> tuple[int, int]:
        return (self.tag, self.segment)


@dataclass(frozen=True)
class CurrentSample:
    """A segment current and location, identified by wire tag and segment."""

    segment: int
    tag: int
    x_wavelengths: float
    y_wavelengths: float
    z_wavelengths: float
    length_wavelengths: float
    real_amperes: float
    imaginary_amperes: float
    magnitude_amperes: float
    phase_degrees: float
    raw_numeric_literals: tuple[str, ...]

    @property
    def identity(self) -> tuple[int, int]:
        return (self.tag, self.segment)


@dataclass(frozen=True)
class PowerBudget:
    """Power accounting printed for one NEC solution snapshot."""

    input_power_watts: float | None
    radiated_power_watts: float | None
    structure_loss_watts: float | None
    network_loss_watts: float | None
    efficiency_percent: float | None
    raw_numeric_literals: tuple[tuple[str, str], ...]

    def literal(self, field: str) -> str:
        """Return the exact displayed literal for a named power field."""

        matches = [
            literal for name, literal in self.raw_numeric_literals if name == field
        ]
        return _require_unique(matches, field, "power literal")


@dataclass(frozen=True)
class FarFieldSample:
    """One far-field row, identified by theta and phi angles."""

    theta_degrees: float
    phi_degrees: float
    major_gain_db: float
    minor_gain_db: float
    total_gain_db: float
    axial_ratio: float
    tilt_degrees: float
    sense: str
    e_theta_magnitude_volts_per_meter: float
    e_theta_phase_degrees: float
    e_phi_magnitude_volts_per_meter: float
    e_phi_phase_degrees: float
    raw_numeric_literals: tuple[str, ...]

    @property
    def identity(self) -> tuple[float, float]:
        return (self.theta_degrees, self.phi_degrees)


@dataclass(frozen=True)
class Snapshot:
    """Results belonging to one ANTENNA INPUT PARAMETERS occurrence."""

    index: int
    frequency_mhz: float | None
    loading: str | None
    ground: str | None
    feeds: tuple[FeedImpedance, ...]
    currents: tuple[CurrentSample, ...]
    power_budget: PowerBudget | None
    far_fields: tuple[FarFieldSample, ...]
    average_power_gain: float | None
    average_power_gain_literal: str | None
    diagnostics: tuple[Diagnostic, ...]

    def feed(self, tag: int, segment: int) -> FeedImpedance:
        """Return a feed row by physical identity."""

        return _unique_identity(self.feeds, (tag, segment), "feed")

    def current(self, tag: int, segment: int) -> CurrentSample:
        """Return a current row by physical identity."""

        return _unique_identity(self.currents, (tag, segment), "current")

    def far_field(
        self,
        theta_degrees: float,
        phi_degrees: float,
        *,
        angular_tolerance: float = 1.0e-9,
    ) -> FarFieldSample:
        """Return a pattern row by angular identity."""

        matches = [
            sample
            for sample in self.far_fields
            if math.isclose(
                sample.theta_degrees,
                theta_degrees,
                rel_tol=0.0,
                abs_tol=angular_tolerance,
            )
            and math.isclose(
                sample.phi_degrees,
                phi_degrees,
                rel_tol=0.0,
                abs_tol=angular_tolerance,
            )
        ]
        return _require_unique(matches, (theta_degrees, phi_degrees), "far field")


@dataclass(frozen=True)
class QualificationReport:
    """Structured qualification-relevant content from a solver report."""

    solver: str
    snapshots: tuple[Snapshot, ...]
    diagnostics: tuple[Diagnostic, ...]
    line_count: int

    @property
    def has_failures(self) -> bool:
        return any(item.severity in {"error", "failure"} for item in self.diagnostics)


def numeric_tokens(text: str) -> tuple[str, ...]:
    """Return numeric literals, including adjacent signed exponent fields."""

    return tuple(match.group(0) for match in _NUMBER_RE.finditer(text))


def parse_report(text: str, *, solver: str = "unknown") -> QualificationReport:
    """Parse a NEC2C- or NEC2DX-shaped human-readable report.

    A snapshot begins at every ``ANTENNA INPUT PARAMETERS`` heading. This
    preserves repeated solutions at the same frequency, such as before and
    after an impedance-loading card.
    """

    if not isinstance(text, str):
        raise TypeError("report text must be str")
    normalized_solver = solver.strip().lower()
    if not normalized_solver:
        raise ValueError("solver must not be empty")

    lines = text.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    diagnostics = _parse_diagnostics(lines)
    input_headings = [
        index
        for index, line in enumerate(lines)
        if _contains_heading(line, "ANTENNA INPUT PARAMETERS")
    ]

    snapshots: list[Snapshot] = []
    previous_heading = 0
    for snapshot_index, heading_index in enumerate(input_headings):
        end_index = (
            input_headings[snapshot_index + 1]
            if snapshot_index + 1 < len(input_headings)
            else len(lines)
        )
        context = lines[previous_heading:heading_index]
        block = lines[heading_index:end_index]
        block_diagnostics = tuple(
            item
            for item in diagnostics
            if heading_index + 1 <= item.line_number <= end_index
        )
        average_power_gain, average_power_gain_literal = _parse_average_power_gain(
            block
        )
        snapshots.append(
            Snapshot(
                index=snapshot_index,
                frequency_mhz=_last_frequency(lines, heading_index),
                loading=_loading_context(context),
                ground=_ground_context(context),
                feeds=_parse_feed_rows(block),
                currents=_parse_current_rows(block),
                power_budget=_parse_power_budget(block),
                far_fields=_parse_far_field_rows(block),
                average_power_gain=average_power_gain,
                average_power_gain_literal=average_power_gain_literal,
                diagnostics=block_diagnostics,
            )
        )
        previous_heading = heading_index + 1

    return QualificationReport(
        solver=normalized_solver,
        snapshots=tuple(snapshots),
        diagnostics=diagnostics,
        line_count=len(lines),
    )


def _to_float(token: str) -> float:
    return float(token.replace("D", "E").replace("d", "e"))


def _canonical(line: str) -> str:
    return " ".join(line.upper().split())


def _contains_heading(line: str, heading: str) -> bool:
    return heading in _canonical(line)


def _last_frequency(lines: list[str], stop: int) -> float | None:
    value: float | None = None
    for line in lines[:stop]:
        match = _FREQUENCY_RE.search(line)
        if match:
            value = _to_float(match.group(1))
    return value


def _loading_context(lines: Iterable[str]) -> str | None:
    context: str | None = None
    for line in lines:
        canonical = _canonical(line)
        if "THIS STRUCTURE IS NOT LOADED" in canonical:
            context = "not_loaded"
        elif "STRUCTURE IMPEDANCE LOADING" in canonical:
            context = "loaded"
    return context


def _ground_context(lines: Iterable[str]) -> str | None:
    context: str | None = None
    for line in lines:
        canonical = _canonical(line)
        if "PERFECT GROUND" in canonical:
            context = "perfect_ground"
        elif "FINITE GROUND" in canonical or "REFLECTION COEFFICIENT" in canonical:
            context = "finite_reflection_ground"
        elif "FREE SPACE" in canonical:
            context = "free_space"
    return context


def _section(
    block: list[str],
    start_heading: str,
    stop_headings: tuple[str, ...],
) -> list[str]:
    start: int | None = None
    for index, line in enumerate(block):
        if _contains_heading(line, start_heading):
            start = index + 1
            break
    if start is None:
        return []
    stop = len(block)
    for index in range(start, len(block)):
        if any(_contains_heading(block[index], heading) for heading in stop_headings):
            stop = index
            break
    return block[start:stop]


def _parse_feed_rows(block: list[str]) -> tuple[FeedImpedance, ...]:
    rows = _section(
        block,
        "ANTENNA INPUT PARAMETERS",
        (
            "CURRENTS AND LOCATION",
            "POWER BUDGET",
            "RADIATION PATTERNS",
            "NEAR ELECTRIC FIELDS",
            "NEAR MAGNETIC FIELDS",
        ),
    )
    parsed: list[FeedImpedance] = []
    for line in rows:
        tokens = numeric_tokens(line)
        if len(tokens) < 11 or not all(
            _INTEGER_RE.fullmatch(token) for token in tokens[:2]
        ):
            continue
        values = tuple(_to_float(token) for token in tokens[2:11])
        parsed.append(
            FeedImpedance(
                tag=int(tokens[0]),
                segment=int(tokens[1]),
                voltage_real=values[0],
                voltage_imaginary=values[1],
                current_real=values[2],
                current_imaginary=values[3],
                resistance_ohms=values[4],
                reactance_ohms=values[5],
                admittance_real_mhos=values[6],
                admittance_imaginary_mhos=values[7],
                power_watts=values[8],
                raw_numeric_literals=tokens[:11],
            )
        )
    return tuple(parsed)


def _parse_current_rows(block: list[str]) -> tuple[CurrentSample, ...]:
    rows = _section(
        block,
        "CURRENTS AND LOCATION",
        (
            "POWER BUDGET",
            "CHARGE DENSITIES",
            "RADIATION PATTERNS",
            "NEAR ELECTRIC FIELDS",
            "NEAR MAGNETIC FIELDS",
        ),
    )
    parsed: list[CurrentSample] = []
    for line in rows:
        tokens = numeric_tokens(line)
        if len(tokens) < 10 or not all(
            _INTEGER_RE.fullmatch(token) for token in tokens[:2]
        ):
            continue
        values = tuple(_to_float(token) for token in tokens[2:10])
        parsed.append(
            CurrentSample(
                segment=int(tokens[0]),
                tag=int(tokens[1]),
                x_wavelengths=values[0],
                y_wavelengths=values[1],
                z_wavelengths=values[2],
                length_wavelengths=values[3],
                real_amperes=values[4],
                imaginary_amperes=values[5],
                magnitude_amperes=values[6],
                phase_degrees=values[7],
                raw_numeric_literals=tokens[:10],
            )
        )
    return tuple(parsed)


def _parse_power_budget(block: list[str]) -> PowerBudget | None:
    labels = {
        "INPUT POWER": "input_power_watts",
        "RADIATED POWER": "radiated_power_watts",
        "STRUCTURE LOSS": "structure_loss_watts",
        "NETWORK LOSS": "network_loss_watts",
        "EFFICIENCY": "efficiency_percent",
    }
    values: dict[str, float | None] = dict.fromkeys(labels.values())
    found = False
    literals: list[tuple[str, str]] = []
    for line in block:
        canonical = _canonical(line)
        for label, field in labels.items():
            if label not in canonical:
                continue
            label_pattern = r"\b" + r"\s+".join(label.split()) + r"\b"
            match = re.search(label_pattern, line, flags=re.IGNORECASE)
            if match is None:
                continue
            suffix = line[match.end() :]
            tokens = numeric_tokens(suffix)
            if tokens:
                values[field] = _to_float(tokens[0])
                literals.append((field, tokens[0]))
                found = True
            break
    if not found:
        return None
    return PowerBudget(**values, raw_numeric_literals=tuple(literals))


def _parse_far_field_rows(block: list[str]) -> tuple[FarFieldSample, ...]:
    rows = _section(
        block,
        "RADIATION PATTERNS",
        (
            "NORMALIZED GAIN",
            "DATA CARD NO",
            "NEAR ELECTRIC FIELDS",
            "NEAR MAGNETIC FIELDS",
            "RECEIVING PATTERN PARAMETERS",
            "CURRENTS AND LOCATION",
            "POWER BUDGET",
        ),
    )
    parsed: list[FarFieldSample] = []
    for line in rows:
        sense_match = _SENSE_RE.search(line)
        tokens = numeric_tokens(line)
        if len(tokens) < 11:
            continue
        values = tuple(_to_float(token) for token in tokens[:11])
        parsed.append(
            FarFieldSample(
                theta_degrees=values[0],
                phi_degrees=values[1],
                major_gain_db=values[2],
                minor_gain_db=values[3],
                total_gain_db=values[4],
                axial_ratio=values[5],
                tilt_degrees=values[6],
                sense=(sense_match.group(1).upper() if sense_match else "UNDEFINED"),
                e_theta_magnitude_volts_per_meter=values[7],
                e_theta_phase_degrees=values[8],
                e_phi_magnitude_volts_per_meter=values[9],
                e_phi_phase_degrees=values[10],
                raw_numeric_literals=tokens[:11],
            )
        )
    return tuple(parsed)


def _parse_average_power_gain(block: list[str]) -> tuple[float | None, str | None]:
    for line in block:
        canonical = _canonical(line)
        if "AVERAGE POWER GAIN" not in canonical:
            continue
        marker = re.search(r"AVERAGE\s+POWER\s+GAIN", line, flags=re.IGNORECASE)
        if marker is None:
            continue
        tokens = numeric_tokens(line[marker.end() :])
        if tokens:
            return (_to_float(tokens[0]), tokens[0])
    return (None, None)


def _parse_diagnostics(lines: list[str]) -> tuple[Diagnostic, ...]:
    parsed: list[Diagnostic] = []
    for line_number, line in enumerate(lines, start=1):
        canonical = _canonical(line)
        severity: str | None = None
        if re.search(r"\b(ERROR|FATAL|ABORT(?:ED)?|TERMINATED)\b", canonical):
            severity = "error"
        elif re.search(r"\b(FAIL|FAILED|FAILURE)\b", canonical):
            if not re.search(r"\bNO\s+FAIL(?:URES?)?\b", canonical):
                severity = "failure"
        elif re.search(r"\b(WARNING|CAUTION)\b", canonical):
            severity = "warning"
        if severity is not None:
            parsed.append(
                Diagnostic(
                    severity=severity,
                    line_number=line_number,
                    text=line.strip(),
                )
            )
    return tuple(parsed)


def _unique_identity(items, identity, label):
    matches = [item for item in items if item.identity == identity]
    return _require_unique(matches, identity, label)


def _require_unique(matches, identity, label):
    if not matches:
        raise KeyError(f"{label} identity not found: {identity!r}")
    if len(matches) != 1:
        raise ValueError(f"{label} identity is not unique: {identity!r}")
    return matches[0]
