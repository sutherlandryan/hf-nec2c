# SPDX-License-Identifier: BSD-2-Clause
"""Run the maintained-NEC2C numerical qualification comparison.

The runner consumes only authenticated deck bytes, explicitly declared checks,
and fresh text reports.  NEC2DX results are reported as secondary diagnostics;
they can neither rescue nor independently block maintained-NEC2C qualification.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from typing import Any, Iterable, Mapping, Sequence

try:
    from .report_parser import QualificationReport, Snapshot, parse_report
    from .tolerance import (
        NumericClassification,
        circular_phase_distance,
        compare_displayed_intervals,
        compare_with_tolerance,
    )
except ImportError:  # pragma: no cover - exercised by direct command use
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tools.qualification.report_parser import (  # type: ignore[no-redef]
        QualificationReport,
        Snapshot,
        parse_report,
    )
    from tools.qualification.tolerance import (  # type: ignore[no-redef]
        NumericClassification,
        circular_phase_distance,
        compare_displayed_intervals,
        compare_with_tolerance,
    )


PRIMARY_SOLVERS = ("msys_nec2c", "ucrt64_nec2c")
SECONDARY_SOLVER = "nec2dx"


class QualificationInputError(ValueError):
    """Raised when the manifest or result inputs are incomplete or ambiguous."""


@dataclass(frozen=True)
class CaseDefinition:
    """Validated, normalized manifest definition for one qualification case."""

    case_id: str
    deck_path: str
    deck_sha256: str
    report_filename: str
    authoritative_checks: tuple[Mapping[str, Any], ...]
    invariants: tuple[Mapping[str, Any], ...]


@dataclass(frozen=True)
class Observable:
    """One report value with a stable physical identity."""

    identifier: str
    observable_class: str
    value: float
    literal: str | None = None
    phase_reference_magnitude: float | None = None


_FEED_FIELDS = {
    "voltage_real": ("voltage_real", 2, "feed_voltage"),
    "voltage_imaginary": ("voltage_imaginary", 3, "feed_voltage"),
    "current_real": ("current_real", 4, "feed_current"),
    "current_imaginary": ("current_imaginary", 5, "feed_current"),
    "resistance_ohms": ("resistance_ohms", 6, "feed_impedance"),
    "reactance_ohms": ("reactance_ohms", 7, "feed_impedance"),
    "admittance_real_mhos": ("admittance_real_mhos", 8, "feed_admittance"),
    "admittance_imaginary_mhos": (
        "admittance_imaginary_mhos",
        9,
        "feed_admittance",
    ),
    "power_watts": ("power_watts", 10, "feed_power"),
}

_CURRENT_FIELDS = {
    "x_wavelengths": ("x_wavelengths", 2, "current_position"),
    "y_wavelengths": ("y_wavelengths", 3, "current_position"),
    "z_wavelengths": ("z_wavelengths", 4, "current_position"),
    "length_wavelengths": ("length_wavelengths", 5, "segment_length"),
    "real_amperes": ("real_amperes", 6, "segment_current"),
    "imaginary_amperes": ("imaginary_amperes", 7, "segment_current"),
    "magnitude_amperes": ("magnitude_amperes", 8, "current_magnitude"),
    "phase_degrees": ("phase_degrees", 9, "current_phase"),
}

_POWER_FIELDS = {
    "input_power_watts": "input_power_watts",
    "radiated_power_watts": "radiated_power_watts",
    "structure_loss_watts": "structure_loss_watts",
    "network_loss_watts": "network_loss_watts",
    "efficiency_percent": "efficiency_percent",
}

_FAR_FIELDS = {
    "major_gain_db": ("major_gain_db", 2, "far_field_gain"),
    "minor_gain_db": ("minor_gain_db", 3, "far_field_gain"),
    "total_gain_db": ("total_gain_db", 4, "far_field_gain"),
    "axial_ratio": ("axial_ratio", 5, "far_field_axial_ratio"),
    "tilt_degrees": ("tilt_degrees", 6, "far_field_tilt"),
    "e_theta_magnitude_volts_per_meter": (
        "e_theta_magnitude_volts_per_meter",
        7,
        "far_field_magnitude",
    ),
    "e_theta_phase_degrees": (
        "e_theta_phase_degrees",
        8,
        "far_field_phase",
    ),
    "e_phi_magnitude_volts_per_meter": (
        "e_phi_magnitude_volts_per_meter",
        9,
        "far_field_magnitude",
    ),
    "e_phi_phase_degrees": (
        "e_phi_phase_degrees",
        10,
        "far_field_phase",
    ),
}

_FIELD_ALIASES = {
    "real": "resistance_ohms",
    "imaginary": "reactance_ohms",
    "resistance": "resistance_ohms",
    "reactance": "reactance_ohms",
    "input": "input_power_watts",
    "radiated": "radiated_power_watts",
    "structure_loss": "structure_loss_watts",
    "network_loss": "network_loss_watts",
    "efficiency": "efficiency_percent",
    "total_gain": "total_gain_db",
    "magnitude": "magnitude_amperes",
    "phase": "phase_degrees",
}


def run_qualification(
    manifest_path: str | Path,
    msys_results: str | Path,
    ucrt64_results: str | Path,
    nec2dx_results: str | Path,
    *,
    repository_root: str | Path | None = None,
) -> dict[str, Any]:
    """Validate inputs, compare reports, and return deterministic result data."""

    manifest_file = Path(manifest_path).resolve()
    manifest = _read_json(manifest_file, "manifest")
    repo_root = _repository_root(manifest, manifest_file, repository_root)
    cases = _load_cases(manifest, repo_root)
    _validate_decks(cases, repo_root)

    result_roots = {
        "msys_nec2c": Path(msys_results).resolve(),
        "ucrt64_nec2c": Path(ucrt64_results).resolve(),
        "nec2dx": Path(nec2dx_results).resolve(),
    }
    reports, report_evidence = _load_reports(cases, result_roots)
    tolerances = _normalized_tolerances(manifest)

    maxima: dict[str, dict[str, dict[str, Any]]] = {
        "cross_platform": {},
        "authoritative": {},
        "invariants": {},
        "secondary_diagnostic": {},
    }
    case_results: list[dict[str, Any]] = []
    any_primary_failure = False

    for case in cases:
        case_reports = {
            solver: reports[solver][case.case_id]
            for solver in (*PRIMARY_SOLVERS, SECONDARY_SOLVER)
        }
        integrity = _report_integrity(case.case_id, case_reports)
        cross = _compare_reports(
            case.case_id,
            case_reports["msys_nec2c"],
            case_reports["ucrt64_nec2c"],
            tolerances["cross_platform"],
            tolerances["undefined_phase_magnitude_v_per_m"],
            maxima["cross_platform"],
        )
        authoritative = _evaluate_authoritative_checks(
            case,
            case_reports,
            maxima["authoritative"],
        )
        invariants = _evaluate_invariants(
            case,
            case_reports,
            reports,
            tolerances,
            maxima["invariants"],
        )
        secondary = _compare_secondary(
            case.case_id,
            case_reports["msys_nec2c"],
            case_reports["nec2dx"],
            tolerances["secondary_diagnostic"],
            tolerances["secondary_diagnostic_by_observable_class"],
            tolerances["undefined_phase_magnitude_v_per_m"],
            maxima["secondary_diagnostic"],
        )

        primary_failed = (
            any(item["classification"] == "FAIL" for item in integrity)
            or any(item["classification"] == "FAIL" for item in cross)
            or any(item["classification"] == "FAIL" for item in authoritative)
            or any(item["classification"] == "FAIL" for item in invariants)
        )
        any_primary_failure |= primary_failed
        if primary_failed:
            case_status = "BLOCKED_BY_NUMERICAL_DISCREPANCY"
        elif not authoritative:
            case_status = "QUALIFIED_WITH_DOCUMENTED_GAP"
        else:
            case_status = "QUALIFIED_FOR_INTENDED_SUBSET"

        case_results.append(
            {
                "case_id": case.case_id,
                "case_status": case_status,
                "deck": {
                    "path": case.deck_path,
                    "sha256": case.deck_sha256,
                },
                "reports": {
                    solver: report_evidence[solver][case.case_id]
                    for solver in (*PRIMARY_SOLVERS, SECONDARY_SOLVER)
                },
                "report_integrity": integrity,
                "cross_platform": cross,
                "authoritative": authoritative,
                "invariants": invariants,
                "secondary_diagnostic": secondary,
            }
        )

    suite_invariants = _evaluate_suite_invariants(
        manifest,
        reports,
        tolerances,
        maxima["invariants"],
    )
    if any(item["classification"] == "FAIL" for item in suite_invariants):
        any_primary_failure = True

    overall_status = (
        "NUMERICAL_QUALIFICATION_BLOCKED"
        if any_primary_failure
        else "NUMERICAL_QUALIFICATION_PASSED"
    )
    result = {
        "schema_version": 1,
        "manifest": {
            "path": _display_path(manifest_file, repo_root),
            "sha256": _sha256_file(manifest_file),
        },
        "case_count": len(cases),
        "overall_status": overall_status,
        "secondary_evidence_policy": (
            "NEC2DX is secondary diagnostic evidence only and cannot establish "
            "or rescue maintained-NEC2C qualification."
        ),
        "evidence_policies": {
            "authoritative": (
                "Candidate and reference displayed half-LSD intervals must intersect; "
                "non-identical intersecting centers retain a precision-limit label."
            ),
            "cross_platform": (
                "All applicable maintained-build numeric observables use the frozen "
                "absolute-plus-relative tolerance."
            ),
            "invariants": (
                "Only typed manifest invariants with their frozen class-specific "
                "tolerances may establish analytic or physical evidence."
            ),
            "secondary_diagnostic": (
                "NEC2DX is shared-lineage secondary evidence only; disagreement does "
                "not independently fail and agreement does not establish qualification."
            ),
            "undefined_phase": (
                "A field-component phase is NOT_APPLICABLE only when both associated "
                "magnitudes are at or below the frozen numerical-null threshold."
            ),
        },
        "tolerances": tolerances,
        "maximum_discrepancies_by_observable_class": {
            source: dict(sorted(entries.items()))
            for source, entries in sorted(maxima.items())
        },
        "classification_counts": _classification_counts(
            case_results,
            suite_invariants,
        ),
        "suite_invariants": suite_invariants,
        "cases": case_results,
    }
    return result


def qualification_summary(full_result: Mapping[str, Any]) -> dict[str, Any]:
    """Project a full run into small, deterministic committed evidence.

    The projection retains deck/report binding evidence, all failures, aggregate
    discrepancy information, and the frozen policies.  It deliberately omits
    the thousands of individual passing observable rows.
    """

    if not isinstance(full_result, Mapping):
        raise TypeError("full_result must be a mapping")
    raw_cases = full_result.get("cases")
    if not isinstance(raw_cases, list):
        raise QualificationInputError("full result cases must be a list")

    authoritative_failures: list[dict[str, Any]] = []
    secondary_groups: dict[tuple[str, int | None, str], dict[str, Any]] = {}
    compact_cases: list[dict[str, Any]] = []
    section_names = (
        "report_integrity",
        "cross_platform",
        "authoritative",
        "invariants",
        "secondary_diagnostic",
    )

    for case in raw_cases:
        if not isinstance(case, Mapping):
            raise QualificationInputError("full result case must be an object")
        case_id = _require_string(case.get("case_id"), "result case_id")
        section_counts: dict[str, dict[str, int]] = {}
        for section_name in section_names:
            items = case.get(section_name)
            if not isinstance(items, list):
                raise QualificationInputError(
                    f"result case {case_id} section {section_name} must be a list"
                )
            counts = Counter(str(item["classification"]) for item in items)
            section_counts[section_name] = dict(sorted(counts.items()))

        for item in case["authoritative"]:
            if item["classification"] != "FAIL":
                continue
            failure = {
                "case_id": case_id,
                "id": item["id"],
                "observable_class": item["observable_class"],
                "reference_literal": item["reference_literal"],
                "candidates": _json_copy(item["candidates"]),
                "classification": "FAIL",
            }
            if "source_locator" in item:
                failure["source_locator"] = item["source_locator"]
            authoritative_failures.append(failure)

        for item in case["secondary_diagnostic"]:
            if item["classification"] != "SECONDARY_DISAGREEMENT":
                continue
            snapshot_match = re.match(r"^snapshot\[(\d+)\]", str(item["id"]))
            snapshot_index = (
                int(snapshot_match.group(1)) if snapshot_match is not None else None
            )
            observable_class = str(item["observable_class"])
            key = (case_id, snapshot_index, observable_class)
            group = secondary_groups.setdefault(
                key,
                {
                    "case_id": case_id,
                    "snapshot_index": snapshot_index,
                    "observable_class": observable_class,
                    "count": 0,
                    "maximum_absolute_error": -1.0,
                    "maximum_error_observable_id": None,
                    "classification": "SECONDARY_DISAGREEMENT",
                },
            )
            group["count"] += 1
            error = float(item["absolute_error"])
            if error > group["maximum_absolute_error"]:
                group["maximum_absolute_error"] = error
                group["maximum_error_observable_id"] = item["id"]

        compact_cases.append(
            {
                "case_id": case_id,
                "case_status": case["case_status"],
                "deck": _json_copy(case["deck"]),
                "reports": _json_copy(case["reports"]),
                "section_classification_counts": section_counts,
            }
        )

    secondary_disagreements = [
        secondary_groups[key]
        for key in sorted(
            secondary_groups,
            key=lambda item: (
                item[0],
                -1 if item[1] is None else item[1],
                item[2],
            ),
        )
    ]
    expected_count = _integer(full_result.get("case_count"), "result case_count")
    if expected_count != len(compact_cases):
        raise QualificationInputError("full result case_count does not match cases")

    return {
        "schema": "hf-nec2c.numerical-qualification-summary",
        "schema_version": 1,
        "qualification_result_schema_version": full_result.get("schema_version"),
        "manifest": _json_copy(full_result["manifest"]),
        "overall_status": full_result["overall_status"],
        "case_count": expected_count,
        "evidence_policies": _json_copy(full_result["evidence_policies"]),
        "tolerances": _json_copy(full_result["tolerances"]),
        "classification_counts": _json_copy(full_result["classification_counts"]),
        "maximum_discrepancies_by_observable_class": _json_copy(
            full_result["maximum_discrepancies_by_observable_class"]
        ),
        "suite_invariants": _json_copy(full_result["suite_invariants"]),
        "authoritative_failures": authoritative_failures,
        "secondary_disagreements": secondary_disagreements,
        "cases": compact_cases,
    }


def _repository_root(
    manifest: Mapping[str, Any],
    manifest_file: Path,
    explicit: str | Path | None,
) -> Path:
    if explicit is not None:
        return Path(explicit).resolve()
    declared = manifest.get("repository_root")
    if declared is not None:
        path = Path(_require_string(declared, "repository_root"))
        return (
            (manifest_file.parent / path).resolve() if not path.is_absolute() else path
        )
    return Path(__file__).resolve().parents[2]


def _load_cases(
    manifest: Mapping[str, Any],
    repo_root: Path,
) -> tuple[CaseDefinition, ...]:
    raw_cases = manifest.get("cases")
    if not isinstance(raw_cases, list):
        raise QualificationInputError("manifest cases must be a list")
    if not 6 <= len(raw_cases) <= 8:
        raise QualificationInputError("qualification corpus must contain 6 to 8 cases")

    definitions: list[CaseDefinition] = []
    seen: set[str] = set()
    for index, raw_case in enumerate(raw_cases):
        if not isinstance(raw_case, Mapping):
            raise QualificationInputError(f"case {index} must be an object")
        metadata = _case_metadata(raw_case, repo_root)
        merged = dict(metadata)
        merged.update(raw_case)
        identity = merged.get("identity", {})
        case_id_value = merged.get("case_id")
        if case_id_value is None and isinstance(identity, Mapping):
            case_id_value = identity.get("case_id")
        case_id = _require_string(case_id_value, f"cases[{index}].case_id")
        if case_id in seen:
            raise QualificationInputError(f"duplicate case_id: {case_id}")
        seen.add(case_id)

        deck = merged.get("deck", {})
        deck_path_value = merged.get("deck_path")
        deck_hash_value = merged.get("deck_sha256")
        if isinstance(deck, Mapping):
            deck_path_value = deck_path_value or deck.get("path")
            deck_hash_value = deck_hash_value or deck.get("sha256")
        deck_path = _require_string(
            deck_path_value,
            f"case {case_id} deck_path",
        )
        deck_sha256 = _require_hash(deck_hash_value, f"case {case_id} deck_sha256")
        report_filename = _require_string(
            merged.get(
                "report_filename",
                merged.get("report_basename", f"{case_id}.out"),
            ),
            f"case {case_id} report_filename",
        )
        if Path(report_filename).name != report_filename:
            raise QualificationInputError(
                f"case {case_id} report_filename must be a basename"
            )

        checks = merged.get("authoritative_checks", ())
        invariants = merged.get("invariants", ())
        definitions.append(
            CaseDefinition(
                case_id=case_id,
                deck_path=deck_path,
                deck_sha256=deck_sha256,
                report_filename=report_filename,
                authoritative_checks=_object_tuple(
                    checks,
                    f"case {case_id} authoritative_checks",
                    strings_are_rejected=True,
                ),
                invariants=_object_tuple(
                    invariants,
                    f"case {case_id} invariants",
                    strings_are_rejected=True,
                ),
            )
        )
    return tuple(definitions)


def _case_metadata(raw_case: Mapping[str, Any], repo_root: Path) -> Mapping[str, Any]:
    value = raw_case.get("metadata_path", raw_case.get("case_metadata_path"))
    if value is None:
        return {}
    path = _resolve_repo_path(repo_root, _require_string(value, "metadata_path"))
    expected_sha256 = _require_hash(
        raw_case.get("metadata_sha256"),
        f"case metadata {path} SHA-256",
    )
    if not path.is_file():
        raise QualificationInputError(f"case metadata does not exist: {path}")
    actual_sha256 = _sha256_file(path)
    if actual_sha256 != expected_sha256:
        raise QualificationInputError(
            f"case metadata SHA-256 mismatch: expected {expected_sha256}, "
            f"got {actual_sha256}: {path}"
        )
    return _read_json(path, f"case metadata {path}")


def _validate_decks(cases: Sequence[CaseDefinition], repo_root: Path) -> None:
    for case in cases:
        path = _resolve_repo_path(repo_root, case.deck_path)
        if not path.is_file():
            raise QualificationInputError(
                f"case {case.case_id} deck does not exist: {path}"
            )
        actual = _sha256_file(path)
        if actual != case.deck_sha256:
            raise QualificationInputError(
                f"case {case.case_id} deck SHA-256 mismatch: "
                f"expected {case.deck_sha256}, got {actual}"
            )


def _load_reports(
    cases: Sequence[CaseDefinition],
    roots: Mapping[str, Path],
) -> tuple[
    dict[str, dict[str, QualificationReport]],
    dict[str, dict[str, dict[str, Any]]],
]:
    reports: dict[str, dict[str, QualificationReport]] = {
        solver: {} for solver in roots
    }
    evidence: dict[str, dict[str, dict[str, Any]]] = {solver: {} for solver in roots}
    for solver, root in roots.items():
        if not root.is_dir():
            raise QualificationInputError(f"result directory does not exist: {root}")
        for case in cases:
            path = root / case.report_filename
            if not path.is_file():
                raise QualificationInputError(
                    f"missing {solver} report for {case.case_id}: {path}"
                )
            data = path.read_bytes()
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError as error:
                raise QualificationInputError(
                    f"report is not UTF-8 text: {path}"
                ) from error
            reports[solver][case.case_id] = parse_report(text, solver=solver)
            evidence[solver][case.case_id] = {
                "filename": case.report_filename,
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
            }
    return reports, evidence


def _normalized_tolerances(manifest: Mapping[str, Any]) -> dict[str, Any]:
    declared = manifest.get("tolerances", manifest.get("tolerance_policy", {}))
    if not isinstance(declared, Mapping):
        raise QualificationInputError("tolerances must be an object")
    invariant_declared = declared.get("invariants", {})
    if not isinstance(invariant_declared, Mapping):
        raise QualificationInputError("tolerances.invariants must be an object")

    def invariant_value(name: str) -> Any:
        return invariant_declared.get(name, declared.get(name))

    raw_secondary_classes = declared.get(
        "secondary_diagnostic_by_observable_class",
        {},
    )
    if not isinstance(raw_secondary_classes, Mapping):
        raise QualificationInputError(
            "tolerances.secondary_diagnostic_by_observable_class must be an object"
        )
    secondary_classes = {
        _require_string(name, "secondary observable class"): _tolerance(
            value,
            absolute=1.0e-6,
            relative=0.0,
        )
        for name, value in raw_secondary_classes.items()
    }

    return {
        "cross_platform": _tolerance(
            declared.get("cross_platform"),
            absolute=1.0e-12,
            relative=1.0e-12,
        ),
        "secondary_diagnostic": _tolerance(
            declared.get("secondary_diagnostic", declared.get("nec2dx")),
            absolute=1.0e-6,
            relative=5.0e-5,
        ),
        "secondary_diagnostic_by_observable_class": dict(
            sorted(secondary_classes.items())
        ),
        "undefined_phase_magnitude_v_per_m": _nonnegative_number(
            declared.get("undefined_phase_magnitude_v_per_m", 0.0),
            "undefined phase magnitude threshold",
        ),
        "power_conservation": _tolerance(
            invariant_value("power_conservation"),
            absolute=5.0e-8,
            relative=5.0e-4,
        ),
        "near_zero_loss": _tolerance(
            invariant_value("near_zero_loss"),
            absolute=5.0e-8,
            relative=0.0,
        ),
        "current_magnitude_symmetry": _tolerance(
            invariant_value("current_magnitude_symmetry"),
            absolute=5.0e-8,
            relative=5.0e-5,
        ),
        "current_phase_symmetry_degrees": _absolute_tolerance(
            invariant_value("current_phase_symmetry_degrees"),
            0.02,
        ),
        "pattern_symmetry_db": _absolute_tolerance(
            invariant_value("pattern_symmetry_db"),
            0.02,
        ),
        "direction_degrees": _absolute_tolerance(
            invariant_value("direction_degrees"),
            0.005,
        ),
        "average_gain": _tolerance(
            invariant_value("average_gain"),
            absolute=0.05,
            relative=0.0,
        ),
        "current_position": _tolerance(
            invariant_value("current_position"),
            absolute=5.0e-5,
            relative=0.0,
        ),
    }


def _report_integrity(
    case_id: str,
    reports: Mapping[str, QualificationReport],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for solver in (*PRIMARY_SOLVERS, SECONDARY_SOLVER):
        report = reports[solver]
        blocking = solver in PRIMARY_SOLVERS
        failed = not report.snapshots or report.has_failures
        if blocking:
            classification = "FAIL" if failed else "PASS"
        else:
            classification = "REFERENCE_UNAVAILABLE" if failed else "PASS"
        results.append(
            {
                "id": f"{case_id}.report_integrity.{solver}",
                "solver": solver,
                "snapshot_count": len(report.snapshots),
                "failure_diagnostics": [
                    {
                        "line_number": item.line_number,
                        "severity": item.severity,
                        "text": item.text,
                    }
                    for item in report.diagnostics
                    if item.severity in {"error", "failure"}
                ],
                "classification": classification,
            }
        )
    return results


def _compare_reports(
    case_id: str,
    first: QualificationReport,
    second: QualificationReport,
    tolerance: Mapping[str, float],
    undefined_phase_magnitude: float,
    maxima: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    left = _report_observables(first)
    right = _report_observables(second)
    results: list[dict[str, Any]] = []
    for identifier in sorted(set(left) | set(right)):
        a = left.get(identifier)
        b = right.get(identifier)
        if a is None or b is None:
            present = a or b
            results.append(
                {
                    "id": identifier,
                    "observable_class": (
                        present.observable_class if present else "report_structure"
                    ),
                    "msys_value": a.value if a else None,
                    "ucrt64_value": b.value if b else None,
                    "classification": "FAIL",
                    "reason": "observable set differs between maintained builds",
                }
            )
            continue
        if _phase_is_undefined(a, b, undefined_phase_magnitude):
            results.append(
                {
                    "id": identifier,
                    "observable_class": a.observable_class,
                    "msys_value": a.value,
                    "ucrt64_value": b.value,
                    "classification": "NOT_APPLICABLE",
                    "reason": "phase undefined at numerical field null",
                }
            )
            continue
        if "phase" in a.observable_class:
            absolute_error = circular_phase_distance(a.value, b.value)
            allowed_error = tolerance["absolute"] + tolerance["relative"] * abs(b.value)
            classification = "PASS" if absolute_error <= allowed_error else "FAIL"
        else:
            comparison = compare_with_tolerance(
                a.value,
                b.value,
                absolute_tolerance=tolerance["absolute"],
                relative_tolerance=tolerance["relative"],
            )
            absolute_error = comparison.absolute_error
            allowed_error = comparison.allowed_error
            classification = comparison.classification.value
        item = {
            "id": identifier,
            "observable_class": a.observable_class,
            "msys_value": a.value,
            "ucrt64_value": b.value,
            "absolute_error": absolute_error,
            "allowed_error": allowed_error,
            "classification": classification,
        }
        results.append(item)
        _record_maximum(
            maxima,
            a.observable_class,
            absolute_error,
            case_id,
            identifier,
        )
    return results


def _evaluate_authoritative_checks(
    case: CaseDefinition,
    reports: Mapping[str, QualificationReport],
    maxima: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for index, check in enumerate(case.authoritative_checks):
        check_id = _require_string(
            check.get("id", f"published-{index}"),
            f"case {case.case_id} authoritative check id",
        )
        reference_literal = _require_string(
            check.get("reference_literal", check.get("expected_literal")),
            f"authoritative check {check_id} reference_literal",
        )
        candidates: dict[str, Any] = {}
        classifications: list[str] = []
        observable_class = _check_observable_class(check)
        for solver in PRIMARY_SOLVERS:
            observable = _select_observable(reports[solver], check)
            if observable.literal is None:
                raise QualificationInputError(
                    f"authoritative check {check_id} selects a value without a "
                    "preserved displayed literal"
                )
            comparison = compare_displayed_intervals(
                observable.literal,
                reference_literal,
            )
            classification = comparison.classification.value
            classifications.append(classification)
            absolute_error = float(
                abs(comparison.candidate.center - comparison.reference.center)
            )
            candidates[solver] = {
                "value": observable.value,
                "literal": observable.literal,
                "absolute_center_error": absolute_error,
                "classification": classification,
            }
            _record_maximum(
                maxima,
                observable_class,
                absolute_error,
                case.case_id,
                check_id,
            )
        combined = _worst_primary_classification(classifications)
        item: dict[str, Any] = {
            "id": check_id,
            "observable_class": observable_class,
            "reference_literal": reference_literal,
            "candidates": candidates,
            "classification": combined,
        }
        if "source_locator" in check:
            item["source_locator"] = check["source_locator"]
        results.append(item)
    return results


def _evaluate_invariants(
    case: CaseDefinition,
    case_reports: Mapping[str, QualificationReport],
    all_reports: Mapping[str, Mapping[str, QualificationReport]],
    tolerances: Mapping[str, Any],
    maxima: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for index, invariant in enumerate(case.invariants):
        invariant_type = _require_string(
            invariant.get("type"),
            f"case {case.case_id} invariant {index} type",
        ).lower()
        invariant_id = _require_string(
            invariant.get("id", f"{invariant_type}-{index}"),
            f"case {case.case_id} invariant id",
        )
        if invariant_type == "power_conservation":
            generated = _invariant_power_conservation(
                case.case_id,
                invariant_id,
                invariant,
                case_reports,
                tolerances,
            )
        elif invariant_type in {"near_zero_loss", "zero_loss"}:
            generated = _invariant_near_zero_loss(
                case.case_id,
                invariant_id,
                invariant,
                case_reports,
                tolerances,
            )
        elif invariant_type in {"current_mirror", "current_symmetry"}:
            generated = _invariant_current_mirror(
                case.case_id,
                invariant_id,
                invariant,
                case_reports,
                tolerances,
            )
        elif invariant_type in {"pattern_phi_symmetry", "pattern_symmetry"}:
            generated = _invariant_pattern_symmetry(
                case.case_id,
                invariant_id,
                invariant,
                case_reports,
                tolerances,
            )
        elif invariant_type == "null_sentinel":
            generated = _invariant_null_sentinel(
                case.case_id,
                invariant_id,
                invariant,
                case_reports,
            )
        elif invariant_type in {"maximum_direction", "pattern_maximum"}:
            generated = _invariant_maximum_direction(
                case.case_id,
                invariant_id,
                invariant,
                case_reports,
                tolerances,
            )
        elif invariant_type in {"average_gain_near_two", "average_gain"}:
            generated = _invariant_average_gain(
                case.case_id,
                invariant_id,
                invariant,
                case_reports,
                tolerances,
            )
        elif invariant_type == "convergence_series":
            generated = _invariant_convergence(
                invariant_id,
                invariant,
                all_reports,
            )
        elif invariant_type == "snapshot_count":
            generated = _invariant_snapshot_count(
                case.case_id,
                invariant_id,
                invariant,
                case_reports,
            )
        elif invariant_type == "current_position":
            generated = _invariant_current_position(
                case.case_id,
                invariant_id,
                invariant,
                case_reports,
                tolerances,
            )
        else:
            raise QualificationInputError(
                f"case {case.case_id} declares unsupported invariant type: "
                f"{invariant_type}"
            )
        results.extend(generated)
        for item in generated:
            if "absolute_error" in item:
                _record_maximum(
                    maxima,
                    item["observable_class"],
                    float(item["absolute_error"]),
                    case.case_id,
                    item["id"],
                )
    return results


def _evaluate_suite_invariants(
    manifest: Mapping[str, Any],
    reports: Mapping[str, Mapping[str, QualificationReport]],
    tolerances: Mapping[str, Any],
    maxima: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    raw = manifest.get("suite_invariants", ())
    invariants = _object_tuple(raw, "suite_invariants", strings_are_rejected=True)
    generated: list[dict[str, Any]] = []
    for index, invariant in enumerate(invariants):
        invariant_type = _require_string(
            invariant.get("type"),
            f"suite invariant {index} type",
        ).lower()
        invariant_id = _require_string(
            invariant.get("id", f"{invariant_type}-{index}"),
            "suite invariant id",
        )
        if invariant_type != "convergence_series":
            raise QualificationInputError(
                f"unsupported suite invariant type: {invariant_type}"
            )
        items = _invariant_convergence(invariant_id, invariant, reports)
        generated.extend(items)
        for item in items:
            if "absolute_error" in item:
                _record_maximum(
                    maxima,
                    item["observable_class"],
                    float(item["absolute_error"]),
                    "suite",
                    item["id"],
                )
    return generated


def _compare_secondary(
    case_id: str,
    maintained: QualificationReport,
    secondary: QualificationReport,
    fallback_tolerance: Mapping[str, float],
    tolerance_by_class: Mapping[str, Mapping[str, float]],
    undefined_phase_magnitude: float,
    maxima: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    left = _report_observables(maintained)
    right = _report_observables(secondary)
    results: list[dict[str, Any]] = []
    for identifier in sorted(set(left) | set(right)):
        a = left.get(identifier)
        b = right.get(identifier)
        if a is None or b is None:
            present = a or b
            results.append(
                {
                    "id": identifier,
                    "observable_class": (
                        present.observable_class if present else "report_structure"
                    ),
                    "maintained_value": a.value if a else None,
                    "nec2dx_value": b.value if b else None,
                    "classification": "REFERENCE_UNAVAILABLE",
                    "reason": "observable set differs; no diagnostic comparison made",
                }
            )
            continue
        if _phase_is_undefined(a, b, undefined_phase_magnitude):
            results.append(
                {
                    "id": identifier,
                    "observable_class": a.observable_class,
                    "maintained_value": a.value,
                    "nec2dx_value": b.value,
                    "classification": "NOT_APPLICABLE",
                    "reason": "phase undefined at numerical field null",
                }
            )
            continue
        tolerance = tolerance_by_class.get(a.observable_class, fallback_tolerance)
        if "phase" in a.observable_class:
            absolute_error = circular_phase_distance(a.value, b.value)
            allowed_error = tolerance["absolute"] + tolerance["relative"] * abs(b.value)
            accepted = absolute_error <= allowed_error
        else:
            comparison = compare_with_tolerance(
                a.value,
                b.value,
                absolute_tolerance=tolerance["absolute"],
                relative_tolerance=tolerance["relative"],
            )
            absolute_error = comparison.absolute_error
            allowed_error = comparison.allowed_error
            accepted = comparison.classification is NumericClassification.PASS
        classification = "PASS" if accepted else "SECONDARY_DISAGREEMENT"
        results.append(
            {
                "id": identifier,
                "observable_class": a.observable_class,
                "maintained_value": a.value,
                "nec2dx_value": b.value,
                "absolute_error": absolute_error,
                "allowed_error": allowed_error,
                "tolerance_source": (
                    "observable_class"
                    if a.observable_class in tolerance_by_class
                    else "fallback"
                ),
                "classification": classification,
            }
        )
        _record_maximum(
            maxima,
            a.observable_class,
            absolute_error,
            case_id,
            identifier,
        )
    return results


def _report_observables(report: QualificationReport) -> dict[str, Observable]:
    observations: dict[str, Observable] = {}
    for snapshot in report.snapshots:
        prefix = f"snapshot[{snapshot.index}]"
        if snapshot.frequency_mhz is not None:
            _add_observable(
                observations,
                Observable(
                    f"{prefix}.frequency_mhz",
                    "frequency",
                    snapshot.frequency_mhz,
                ),
            )
        for feed in snapshot.feeds:
            row = f"{prefix}.feed[tag={feed.tag},segment={feed.segment}]"
            for field, (
                attribute,
                literal_index,
                observable_class,
            ) in _FEED_FIELDS.items():
                _add_observable(
                    observations,
                    Observable(
                        f"{row}.{field}",
                        observable_class,
                        float(getattr(feed, attribute)),
                        feed.raw_numeric_literals[literal_index],
                    ),
                )
        for current in snapshot.currents:
            row = f"{prefix}.current[tag={current.tag},segment={current.segment}]"
            for field, (
                attribute,
                literal_index,
                observable_class,
            ) in _CURRENT_FIELDS.items():
                _add_observable(
                    observations,
                    Observable(
                        f"{row}.{field}",
                        observable_class,
                        float(getattr(current, attribute)),
                        current.raw_numeric_literals[literal_index],
                    ),
                )
        if snapshot.power_budget is not None:
            for field in _POWER_FIELDS:
                value = getattr(snapshot.power_budget, field)
                if value is None:
                    continue
                try:
                    literal = snapshot.power_budget.literal(field)
                except KeyError:
                    literal = None
                _add_observable(
                    observations,
                    Observable(
                        f"{prefix}.power.{field}",
                        _power_observable_class(field),
                        float(value),
                        literal,
                    ),
                )
        for sample in snapshot.far_fields:
            row = (
                f"{prefix}.far_field[theta={_identity_number(sample.theta_degrees)},"
                f"phi={_identity_number(sample.phi_degrees)}]"
            )
            for field, (
                attribute,
                literal_index,
                observable_class,
            ) in _FAR_FIELDS.items():
                phase_reference_magnitude: float | None = None
                if field == "e_theta_phase_degrees":
                    phase_reference_magnitude = sample.e_theta_magnitude_volts_per_meter
                elif field == "e_phi_phase_degrees":
                    phase_reference_magnitude = sample.e_phi_magnitude_volts_per_meter
                _add_observable(
                    observations,
                    Observable(
                        f"{row}.{field}",
                        observable_class,
                        float(getattr(sample, attribute)),
                        sample.raw_numeric_literals[literal_index],
                        phase_reference_magnitude,
                    ),
                )
        if snapshot.average_power_gain is not None:
            _add_observable(
                observations,
                Observable(
                    f"{prefix}.average_power_gain",
                    "average_power_gain",
                    snapshot.average_power_gain,
                    snapshot.average_power_gain_literal,
                ),
            )
    return observations


def _select_observable(
    report: QualificationReport,
    raw_check: Mapping[str, Any],
) -> Observable:
    selector = raw_check.get("selector", {})
    if selector is not None and not isinstance(selector, Mapping):
        raise QualificationInputError("authoritative selector must be an object")
    check = dict(selector or {})
    check.update(raw_check)
    snapshot_index = _integer(
        check.get("snapshot", check.get("snapshot_index", 0)),
        "authoritative snapshot",
    )
    snapshot = _snapshot(report, snapshot_index)
    kind = _require_string(
        check.get("observable", check.get("kind")),
        "authoritative observable",
    ).lower()
    field = _canonical_field(
        _require_string(check.get("field", "value"), "authoritative field")
    )
    if kind in {"feed", "feed_impedance", "feed_current"}:
        tag, segment = _identity(check, integer=True)
        feed = snapshot.feed(int(tag), int(segment))
        if field not in _FEED_FIELDS:
            raise QualificationInputError(f"unsupported feed field: {field}")
        attribute, literal_index, observable_class = _FEED_FIELDS[field]
        return Observable(
            f"snapshot[{snapshot_index}].feed[{tag},{segment}].{field}",
            observable_class,
            float(getattr(feed, attribute)),
            feed.raw_numeric_literals[literal_index],
        )
    if kind in {"current", "segment_current"}:
        tag, segment = _identity(check, integer=True)
        current = snapshot.current(int(tag), int(segment))
        if field not in _CURRENT_FIELDS:
            raise QualificationInputError(f"unsupported current field: {field}")
        attribute, literal_index, observable_class = _CURRENT_FIELDS[field]
        return Observable(
            f"snapshot[{snapshot_index}].current[{tag},{segment}].{field}",
            observable_class,
            float(getattr(current, attribute)),
            current.raw_numeric_literals[literal_index],
        )
    if kind in {"power", "power_budget"}:
        if snapshot.power_budget is None:
            raise QualificationInputError(
                f"snapshot {snapshot_index} has no power budget"
            )
        if field not in _POWER_FIELDS:
            raise QualificationInputError(f"unsupported power field: {field}")
        value = getattr(snapshot.power_budget, field)
        if value is None:
            raise QualificationInputError(
                f"snapshot {snapshot_index} power field is absent: {field}"
            )
        return Observable(
            f"snapshot[{snapshot_index}].power.{field}",
            _power_observable_class(field),
            float(value),
            snapshot.power_budget.literal(field),
        )
    if kind in {"far_field", "pattern"}:
        theta, phi = _identity(check, integer=False)
        sample = snapshot.far_field(theta, phi)
        if field not in _FAR_FIELDS:
            raise QualificationInputError(f"unsupported far-field field: {field}")
        attribute, literal_index, observable_class = _FAR_FIELDS[field]
        return Observable(
            f"snapshot[{snapshot_index}].far_field[{theta},{phi}].{field}",
            observable_class,
            float(getattr(sample, attribute)),
            sample.raw_numeric_literals[literal_index],
        )
    if kind in {"average_power_gain", "average_gain"}:
        if snapshot.average_power_gain is None:
            raise QualificationInputError(
                f"snapshot {snapshot_index} has no average power gain"
            )
        return Observable(
            f"snapshot[{snapshot_index}].average_power_gain",
            "average_power_gain",
            snapshot.average_power_gain,
            snapshot.average_power_gain_literal,
        )
    raise QualificationInputError(f"unsupported authoritative observable: {kind}")


def _invariant_power_conservation(
    case_id: str,
    invariant_id: str,
    spec: Mapping[str, Any],
    reports: Mapping[str, QualificationReport],
    tolerances: Mapping[str, Any],
) -> list[dict[str, Any]]:
    tolerance = _invariant_tolerance(
        spec,
        tolerances["power_conservation"],
        absolute_key="absolute_tolerance_watts",
    )
    results: list[dict[str, Any]] = []
    for solver in PRIMARY_SOLVERS:
        report = reports[solver]
        for index in _snapshot_indices(spec, report):
            budget = _require_power_budget(_snapshot(report, index), invariant_id)
            fields = (
                budget.input_power_watts,
                budget.radiated_power_watts,
                budget.structure_loss_watts,
                budget.network_loss_watts,
            )
            if any(value is None for value in fields):
                raise QualificationInputError(
                    f"invariant {invariant_id} requires all power-budget fields"
                )
            actual = float(fields[0])
            expected = float(fields[1]) + float(fields[2]) + float(fields[3])
            comparison = compare_with_tolerance(
                actual,
                expected,
                absolute_tolerance=tolerance["absolute"],
                relative_tolerance=tolerance["relative"],
            )
            results.append(
                {
                    "id": f"{invariant_id}.{solver}.snapshot[{index}]",
                    "type": "power_conservation",
                    "solver": solver,
                    "observable_class": "power_conservation",
                    "input_power_watts": actual,
                    "accounted_power_watts": expected,
                    "absolute_error": comparison.absolute_error,
                    "allowed_error": comparison.allowed_error,
                    "classification": comparison.classification.value,
                }
            )
    return results


def _invariant_near_zero_loss(
    case_id: str,
    invariant_id: str,
    spec: Mapping[str, Any],
    reports: Mapping[str, QualificationReport],
    tolerances: Mapping[str, Any],
) -> list[dict[str, Any]]:
    del case_id
    tolerance = _invariant_tolerance(
        spec,
        tolerances["near_zero_loss"],
        absolute_key="absolute_tolerance_watts",
    )
    raw_fields = spec.get("fields", spec.get("field", ["structure_loss_watts"]))
    if isinstance(raw_fields, str):
        raw_fields = [raw_fields]
    if not isinstance(raw_fields, list) or not raw_fields:
        raise QualificationInputError(f"invariant {invariant_id} fields must be a list")
    fields = [
        _canonical_field(_require_string(value, "loss field")) for value in raw_fields
    ]
    results: list[dict[str, Any]] = []
    for solver in PRIMARY_SOLVERS:
        report = reports[solver]
        for index in _snapshot_indices(spec, report):
            budget = _require_power_budget(_snapshot(report, index), invariant_id)
            for field in fields:
                if field not in {"structure_loss_watts", "network_loss_watts"}:
                    raise QualificationInputError(
                        f"invariant {invariant_id} has unsupported loss field: {field}"
                    )
                value = getattr(budget, field)
                if value is None:
                    raise QualificationInputError(
                        f"invariant {invariant_id} field is absent: {field}"
                    )
                comparison = compare_with_tolerance(
                    value,
                    0.0,
                    absolute_tolerance=tolerance["absolute"],
                    relative_tolerance=tolerance["relative"],
                )
                results.append(
                    {
                        "id": f"{invariant_id}.{solver}.snapshot[{index}].{field}",
                        "type": "near_zero_loss",
                        "solver": solver,
                        "observable_class": _power_observable_class(field),
                        "actual": float(value),
                        "expected": 0.0,
                        "absolute_error": comparison.absolute_error,
                        "allowed_error": comparison.allowed_error,
                        "classification": comparison.classification.value,
                    }
                )
    return results


def _invariant_current_mirror(
    case_id: str,
    invariant_id: str,
    spec: Mapping[str, Any],
    reports: Mapping[str, QualificationReport],
    tolerances: Mapping[str, Any],
) -> list[dict[str, Any]]:
    del case_id
    magnitude_tolerance = _invariant_tolerance(
        spec,
        tolerances["current_magnitude_symmetry"],
        absolute_key="magnitude_absolute_tolerance",
        relative_key="magnitude_relative_tolerance",
    )
    phase_tolerance = float(
        spec.get(
            "phase_absolute_tolerance_degrees",
            tolerances["current_phase_symmetry_degrees"],
        )
    )
    if phase_tolerance < 0.0 or not math.isfinite(phase_tolerance):
        raise QualificationInputError("phase tolerance must be finite and non-negative")
    pairs = _current_pairs(spec)
    snapshot_index = _integer(spec.get("snapshot", 0), "current mirror snapshot")
    results: list[dict[str, Any]] = []
    for solver in PRIMARY_SOLVERS:
        snapshot = _snapshot(reports[solver], snapshot_index)
        for pair_index, (left_identity, right_identity) in enumerate(pairs):
            left = snapshot.current(*left_identity)
            right = snapshot.current(*right_identity)
            comparison = compare_with_tolerance(
                left.magnitude_amperes,
                right.magnitude_amperes,
                absolute_tolerance=magnitude_tolerance["absolute"],
                relative_tolerance=magnitude_tolerance["relative"],
            )
            base = f"{invariant_id}.{solver}.pair[{pair_index}]"
            results.append(
                {
                    "id": f"{base}.magnitude",
                    "type": "current_mirror",
                    "solver": solver,
                    "observable_class": "current_magnitude_symmetry",
                    "left_identity": list(left_identity),
                    "right_identity": list(right_identity),
                    "left_value": left.magnitude_amperes,
                    "right_value": right.magnitude_amperes,
                    "absolute_error": comparison.absolute_error,
                    "allowed_error": comparison.allowed_error,
                    "classification": comparison.classification.value,
                }
            )
            phase_error = circular_phase_distance(
                left.phase_degrees,
                right.phase_degrees,
            )
            results.append(
                {
                    "id": f"{base}.phase",
                    "type": "current_mirror",
                    "solver": solver,
                    "observable_class": "current_phase_symmetry",
                    "left_identity": list(left_identity),
                    "right_identity": list(right_identity),
                    "left_value_degrees": left.phase_degrees,
                    "right_value_degrees": right.phase_degrees,
                    "absolute_error": phase_error,
                    "allowed_error": phase_tolerance,
                    "classification": "PASS"
                    if phase_error <= phase_tolerance
                    else "FAIL",
                }
            )
    return results


def _invariant_pattern_symmetry(
    case_id: str,
    invariant_id: str,
    spec: Mapping[str, Any],
    reports: Mapping[str, QualificationReport],
    tolerances: Mapping[str, Any],
) -> list[dict[str, Any]]:
    del case_id
    snapshot_index = _integer(spec.get("snapshot", 0), "pattern symmetry snapshot")
    phis = spec.get("phis", [spec.get("phi_a", 0.0), spec.get("phi_b", 90.0)])
    if not isinstance(phis, list) or len(phis) != 2:
        raise QualificationInputError(f"invariant {invariant_id} needs two phis")
    phi_a, phi_b = (_finite_number(value, "pattern phi") for value in phis)
    raw_fields = spec.get("fields", [spec.get("field", "total_gain_db")])
    if not isinstance(raw_fields, list) or not raw_fields:
        raise QualificationInputError(f"invariant {invariant_id} fields must be a list")
    fields = [
        _canonical_field(_require_string(value, "pattern field"))
        for value in raw_fields
    ]
    tolerance = float(
        spec.get("absolute_tolerance_db", tolerances["pattern_symmetry_db"])
    )
    results: list[dict[str, Any]] = []
    for solver in PRIMARY_SOLVERS:
        snapshot = _snapshot(reports[solver], snapshot_index)
        raw_thetas = spec.get("thetas")
        if raw_thetas is None:
            theta_a = {
                sample.theta_degrees
                for sample in snapshot.far_fields
                if math.isclose(sample.phi_degrees, phi_a, abs_tol=1.0e-9)
            }
            theta_b = {
                sample.theta_degrees
                for sample in snapshot.far_fields
                if math.isclose(sample.phi_degrees, phi_b, abs_tol=1.0e-9)
            }
            thetas = sorted(theta_a & theta_b)
        else:
            if not isinstance(raw_thetas, list):
                raise QualificationInputError(
                    f"invariant {invariant_id} thetas must be a list"
                )
            thetas = [_finite_number(value, "pattern theta") for value in raw_thetas]
        if not thetas:
            raise QualificationInputError(
                f"invariant {invariant_id} found no matching theta samples"
            )
        for theta in thetas:
            left = snapshot.far_field(theta, phi_a)
            right = snapshot.far_field(theta, phi_b)
            for field in fields:
                if field not in _FAR_FIELDS:
                    raise QualificationInputError(
                        f"invariant {invariant_id} has unsupported field: {field}"
                    )
                attribute = _FAR_FIELDS[field][0]
                a = float(getattr(left, attribute))
                b = float(getattr(right, attribute))
                error = (
                    circular_phase_distance(a, b)
                    if field.endswith("phase_degrees")
                    else abs(a - b)
                )
                results.append(
                    {
                        "id": (
                            f"{invariant_id}.{solver}.theta[{_identity_number(theta)}]."
                            f"{field}"
                        ),
                        "type": "pattern_phi_symmetry",
                        "solver": solver,
                        "observable_class": "pattern_symmetry",
                        "theta_degrees": theta,
                        "phi_a_degrees": phi_a,
                        "phi_b_degrees": phi_b,
                        "left_value": a,
                        "right_value": b,
                        "absolute_error": error,
                        "allowed_error": tolerance,
                        "classification": "PASS" if error <= tolerance else "FAIL",
                    }
                )
    return results


def _invariant_null_sentinel(
    case_id: str,
    invariant_id: str,
    spec: Mapping[str, Any],
    reports: Mapping[str, QualificationReport],
) -> list[dict[str, Any]]:
    del case_id
    snapshot_index = _integer(spec.get("snapshot", 0), "null snapshot")
    theta, phi = _identity(spec, integer=False)
    field = _canonical_field(
        _require_string(spec.get("field", "total_gain_db"), "null field")
    )
    if field not in _FAR_FIELDS:
        raise QualificationInputError(f"unsupported null-sentinel field: {field}")
    expected = _require_string(
        spec.get("expected_literal", "-999.99"),
        "null expected_literal",
    )
    results: list[dict[str, Any]] = []
    for solver in PRIMARY_SOLVERS:
        sample = _snapshot(reports[solver], snapshot_index).far_field(theta, phi)
        attribute, literal_index, _ = _FAR_FIELDS[field]
        literal = sample.raw_numeric_literals[literal_index]
        comparison = compare_displayed_intervals(literal, expected)
        error = float(abs(comparison.candidate.center - comparison.reference.center))
        results.append(
            {
                "id": f"{invariant_id}.{solver}",
                "type": "null_sentinel",
                "solver": solver,
                "observable_class": "far_field_null_sentinel",
                "actual": float(getattr(sample, attribute)),
                "literal": literal,
                "expected_literal": expected,
                "absolute_error": error,
                "classification": comparison.classification.value,
            }
        )
    return results


def _invariant_maximum_direction(
    case_id: str,
    invariant_id: str,
    spec: Mapping[str, Any],
    reports: Mapping[str, QualificationReport],
    tolerances: Mapping[str, Any],
) -> list[dict[str, Any]]:
    del case_id
    snapshot_index = _integer(spec.get("snapshot", 0), "maximum snapshot")
    expected_theta = _finite_number(
        spec.get("theta_degrees", spec.get("expected_theta_degrees")),
        "expected maximum theta",
    )
    expected_phi_value = spec.get("phi_degrees", spec.get("expected_phi_degrees"))
    expected_phi = (
        None
        if expected_phi_value is None
        else _finite_number(expected_phi_value, "expected maximum phi")
    )
    tolerance = float(
        spec.get("angular_tolerance_degrees", tolerances["direction_degrees"])
    )
    results: list[dict[str, Any]] = []
    for solver in PRIMARY_SOLVERS:
        snapshot = _snapshot(reports[solver], snapshot_index)
        if not snapshot.far_fields:
            raise QualificationInputError(f"invariant {invariant_id} needs far fields")
        maximum = max(sample.total_gain_db for sample in snapshot.far_fields)
        maxima = [
            sample
            for sample in snapshot.far_fields
            if math.isclose(sample.total_gain_db, maximum, rel_tol=0.0, abs_tol=1.0e-12)
        ]
        errors = [
            max(
                abs(sample.theta_degrees - expected_theta),
                0.0
                if expected_phi is None
                else circular_phase_distance(sample.phi_degrees, expected_phi),
            )
            for sample in maxima
        ]
        error = min(errors)
        results.append(
            {
                "id": f"{invariant_id}.{solver}.direction",
                "type": "maximum_direction",
                "solver": solver,
                "observable_class": "pattern_maximum_direction",
                "maximum_total_gain_db": maximum,
                "expected_theta_degrees": expected_theta,
                "expected_phi_degrees": expected_phi,
                "absolute_error": error,
                "allowed_error": tolerance,
                "classification": "PASS" if error <= tolerance else "FAIL",
            }
        )
    return results


def _invariant_average_gain(
    case_id: str,
    invariant_id: str,
    spec: Mapping[str, Any],
    reports: Mapping[str, QualificationReport],
    tolerances: Mapping[str, Any],
) -> list[dict[str, Any]]:
    del case_id
    snapshot_index = _integer(spec.get("snapshot", 0), "average gain snapshot")
    target = _finite_number(
        spec.get("expected", spec.get("target", 2.0)), "gain target"
    )
    tolerance = _invariant_tolerance(spec, tolerances["average_gain"])
    results: list[dict[str, Any]] = []
    for solver in PRIMARY_SOLVERS:
        value = _snapshot(reports[solver], snapshot_index).average_power_gain
        if value is None:
            raise QualificationInputError(
                f"invariant {invariant_id} needs average gain"
            )
        comparison = compare_with_tolerance(
            value,
            target,
            absolute_tolerance=tolerance["absolute"],
            relative_tolerance=tolerance["relative"],
        )
        results.append(
            {
                "id": f"{invariant_id}.{solver}",
                "type": "average_gain_near_two",
                "solver": solver,
                "observable_class": "average_power_gain",
                "actual": value,
                "expected": target,
                "absolute_error": comparison.absolute_error,
                "allowed_error": comparison.allowed_error,
                "classification": comparison.classification.value,
            }
        )
    return results


def _invariant_convergence(
    invariant_id: str,
    spec: Mapping[str, Any],
    reports: Mapping[str, Mapping[str, QualificationReport]],
) -> list[dict[str, Any]]:
    raw_series = spec.get("series")
    if not isinstance(raw_series, list) or len(raw_series) < 3:
        raise QualificationInputError(
            f"invariant {invariant_id} series must contain at least three selectors"
        )
    results: list[dict[str, Any]] = []
    for solver in PRIMARY_SOLVERS:
        impedances: list[complex] = []
        gains: list[float] = []
        labels: list[str] = []
        for index, raw_item in enumerate(raw_series):
            if not isinstance(raw_item, Mapping):
                raise QualificationInputError(
                    f"invariant {invariant_id} series item {index} must be an object"
                )
            case_id = _require_string(raw_item.get("case_id"), "series case_id")
            try:
                report = reports[solver][case_id]
            except KeyError as error:
                raise QualificationInputError(
                    f"invariant {invariant_id} references unknown case {case_id}"
                ) from error
            snapshot = _snapshot(
                report,
                _integer(raw_item.get("snapshot", 0), "series snapshot"),
            )
            tag, segment = _identity(raw_item, integer=True, prefix="feed_")
            feed = snapshot.feed(int(tag), int(segment))
            impedances.append(complex(feed.resistance_ohms, feed.reactance_ohms))
            labels.append(case_id)
            pattern_identity = raw_item.get("pattern_identity")
            if pattern_identity is not None:
                if not isinstance(pattern_identity, list) or len(pattern_identity) != 2:
                    raise QualificationInputError(
                        "pattern_identity must be [theta, phi]"
                    )
                theta = _finite_number(pattern_identity[0], "series theta")
                phi = _finite_number(pattern_identity[1], "series phi")
                gains.append(snapshot.far_field(theta, phi).total_gain_db)

        impedance_deltas = [
            abs(current - previous)
            for previous, current in zip(impedances, impedances[1:])
        ]
        for index, (previous, current) in enumerate(
            zip(impedance_deltas, impedance_deltas[1:]),
            start=1,
        ):
            error = max(0.0, current - previous)
            results.append(
                {
                    "id": f"{invariant_id}.{solver}.impedance_delta[{index}]",
                    "type": "convergence_series",
                    "solver": solver,
                    "observable_class": "feed_impedance_convergence",
                    "coarser_delta_ohms": previous,
                    "finer_delta_ohms": current,
                    "absolute_error": error,
                    "classification": "PASS" if current < previous else "FAIL",
                }
            )
        if gains:
            if len(gains) != len(raw_series):
                raise QualificationInputError(
                    f"invariant {invariant_id} must select pattern gain for every item"
                )
            gain_deltas = [
                abs(current - previous) for previous, current in zip(gains, gains[1:])
            ]
            for index, (previous, current) in enumerate(
                zip(gain_deltas, gain_deltas[1:]),
                start=1,
            ):
                error = max(0.0, current - previous)
                results.append(
                    {
                        "id": f"{invariant_id}.{solver}.gain_delta[{index}]",
                        "type": "convergence_series",
                        "solver": solver,
                        "observable_class": "broadside_gain_convergence",
                        "coarser_delta_db": previous,
                        "finer_delta_db": current,
                        "absolute_error": error,
                        "classification": "PASS" if current < previous else "FAIL",
                    }
                )
    return results


def _invariant_snapshot_count(
    case_id: str,
    invariant_id: str,
    spec: Mapping[str, Any],
    reports: Mapping[str, QualificationReport],
) -> list[dict[str, Any]]:
    del case_id
    expected = _integer(spec.get("expected"), "expected snapshot count")
    results: list[dict[str, Any]] = []
    for solver in PRIMARY_SOLVERS:
        actual = len(reports[solver].snapshots)
        error = abs(actual - expected)
        results.append(
            {
                "id": f"{invariant_id}.{solver}",
                "type": "snapshot_count",
                "solver": solver,
                "observable_class": "snapshot_count",
                "actual": actual,
                "expected": expected,
                "absolute_error": error,
                "classification": "PASS" if actual == expected else "FAIL",
            }
        )
    return results


def _invariant_current_position(
    case_id: str,
    invariant_id: str,
    spec: Mapping[str, Any],
    reports: Mapping[str, QualificationReport],
    tolerances: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Check parsed, wavelength-normalized current-row coordinates and length."""

    del case_id
    snapshot_index = _integer(spec.get("snapshot", 0), "current position snapshot")
    tag, segment = _identity(spec, integer=True)
    expected = spec.get("expected")
    if not isinstance(expected, Mapping) or not expected:
        raise QualificationInputError(
            f"invariant {invariant_id} expected must be a non-empty object"
        )
    allowed_fields = {
        "x_wavelengths",
        "y_wavelengths",
        "z_wavelengths",
        "length_wavelengths",
    }
    unknown = sorted(set(expected) - allowed_fields)
    if unknown:
        raise QualificationInputError(
            f"invariant {invariant_id} has unsupported position fields: {unknown}"
        )
    tolerance = _invariant_tolerance(
        spec,
        tolerances["current_position"],
    )
    results: list[dict[str, Any]] = []
    for solver in PRIMARY_SOLVERS:
        current = _snapshot(reports[solver], snapshot_index).current(tag, segment)
        for field in sorted(expected):
            actual = float(getattr(current, field))
            target = _finite_number(expected[field], f"{invariant_id} {field}")
            comparison = compare_with_tolerance(
                actual,
                target,
                absolute_tolerance=tolerance["absolute"],
                relative_tolerance=tolerance["relative"],
            )
            results.append(
                {
                    "id": f"{invariant_id}.{solver}.{field}",
                    "type": "current_position",
                    "solver": solver,
                    "observable_class": (
                        "segment_length"
                        if field == "length_wavelengths"
                        else "current_position"
                    ),
                    "identity": [tag, segment],
                    "field": field,
                    "actual": actual,
                    "expected": target,
                    "absolute_error": comparison.absolute_error,
                    "allowed_error": comparison.allowed_error,
                    "classification": comparison.classification.value,
                }
            )
    return results


def _current_pairs(
    spec: Mapping[str, Any],
) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    raw_pairs = spec.get("pairs")
    if raw_pairs is not None:
        if not isinstance(raw_pairs, list) or not raw_pairs:
            raise QualificationInputError(
                "current mirror pairs must be a non-empty list"
            )
        parsed: list[tuple[tuple[int, int], tuple[int, int]]] = []
        for raw_pair in raw_pairs:
            if isinstance(raw_pair, Mapping):
                raw_left, raw_right = raw_pair.get("left"), raw_pair.get("right")
            elif isinstance(raw_pair, list) and len(raw_pair) == 2:
                raw_left, raw_right = raw_pair
            else:
                raise QualificationInputError("current mirror pair is malformed")
            parsed.append((_current_identity(raw_left), _current_identity(raw_right)))
        return parsed

    if "tag" in spec:
        tag = _integer(spec["tag"], "mirror tag")
        segment_range = spec.get("segment_range")
        if segment_range is None:
            segment_range = [spec.get("first_segment"), spec.get("last_segment")]
        first, last = _integer_pair(segment_range, "segment_range")
        return [
            ((tag, left), (tag, right))
            for left, right in zip(range(first, last), range(last, first, -1))
            if left < right
        ]

    left = spec.get("left")
    right = spec.get("right")
    if not isinstance(left, Mapping) or not isinstance(right, Mapping):
        raise QualificationInputError(
            "current mirror needs explicit pairs, a tag/range, or left/right ranges"
        )
    left_tag = _integer(left.get("tag"), "left tag")
    right_tag = _integer(right.get("tag"), "right tag")
    left_first, left_last = _integer_pair(left.get("segments"), "left segments")
    right_first, right_last = _integer_pair(right.get("segments"), "right segments")
    left_segments = list(_inclusive_range(left_first, left_last))
    right_segments = list(_inclusive_range(right_first, right_last))
    if spec.get("reverse_right", False):
        right_segments.reverse()
    if len(left_segments) != len(right_segments):
        raise QualificationInputError("current mirror ranges have different lengths")
    return [
        ((left_tag, a), (right_tag, b)) for a, b in zip(left_segments, right_segments)
    ]


def _check_observable_class(check: Mapping[str, Any]) -> str:
    declared = check.get("observable_class")
    if declared is not None:
        return _require_string(declared, "observable_class")
    kind = str(check.get("observable", check.get("kind", "unknown"))).lower()
    field = _canonical_field(str(check.get("field", "value")))
    if kind.startswith("feed") and field in _FEED_FIELDS:
        return _FEED_FIELDS[field][2]
    if kind in {"current", "segment_current"} and field in _CURRENT_FIELDS:
        return _CURRENT_FIELDS[field][2]
    if kind in {"power", "power_budget"}:
        return _power_observable_class(field)
    if kind in {"far_field", "pattern"} and field in _FAR_FIELDS:
        return _FAR_FIELDS[field][2]
    if kind in {"average_gain", "average_power_gain"}:
        return "average_power_gain"
    return "other"


def _identity(
    source: Mapping[str, Any],
    *,
    integer: bool,
    prefix: str = "",
) -> tuple[Any, Any]:
    value = source.get(f"{prefix}identity", source.get("identity"))
    if value is None:
        first_name, second_name = (
            (f"{prefix}tag", f"{prefix}segment")
            if integer
            else ("theta_degrees", "phi_degrees")
        )
        value = [source.get(first_name), source.get(second_name)]
    if not isinstance(value, list) or len(value) != 2:
        raise QualificationInputError("observable identity must contain two values")
    if integer:
        return (
            _integer(value[0], "identity tag"),
            _integer(value[1], "identity segment"),
        )
    return (
        _finite_number(value[0], "identity theta"),
        _finite_number(value[1], "identity phi"),
    )


def _current_identity(value: Any) -> tuple[int, int]:
    if isinstance(value, Mapping):
        return (
            _integer(value.get("tag"), "current tag"),
            _integer(value.get("segment"), "current segment"),
        )
    if not isinstance(value, list) or len(value) != 2:
        raise QualificationInputError("current identity must be [tag, segment]")
    return (_integer(value[0], "current tag"), _integer(value[1], "current segment"))


def _snapshot_indices(
    spec: Mapping[str, Any],
    report: QualificationReport,
) -> list[int]:
    raw = spec.get("snapshots")
    if raw is None and "snapshot" in spec:
        raw = [spec["snapshot"]]
    if raw is None:
        return list(range(len(report.snapshots)))
    if not isinstance(raw, list):
        raise QualificationInputError("snapshots must be a list")
    return [_integer(value, "snapshot index") for value in raw]


def _snapshot(report: QualificationReport, index: int) -> Snapshot:
    if index < 0 or index >= len(report.snapshots):
        raise QualificationInputError(
            f"snapshot index {index} out of range for {report.solver} report"
        )
    return report.snapshots[index]


def _require_power_budget(snapshot: Snapshot, invariant_id: str):
    if snapshot.power_budget is None:
        raise QualificationInputError(
            f"invariant {invariant_id} requires a power budget"
        )
    return snapshot.power_budget


def _invariant_tolerance(
    spec: Mapping[str, Any],
    default: Mapping[str, float],
    *,
    absolute_key: str = "absolute_tolerance",
    relative_key: str = "relative_tolerance",
) -> dict[str, float]:
    absolute = _finite_number(spec.get(absolute_key, default["absolute"]), absolute_key)
    relative = _finite_number(spec.get(relative_key, default["relative"]), relative_key)
    if absolute < 0.0 or relative < 0.0:
        raise QualificationInputError("tolerances must be non-negative")
    return {"absolute": absolute, "relative": relative}


def _tolerance(value: Any, *, absolute: float, relative: float) -> dict[str, float]:
    if value is None:
        return {"absolute": absolute, "relative": relative}
    if not isinstance(value, Mapping):
        raise QualificationInputError("tolerance declaration must be an object")
    result = {
        "absolute": _finite_number(
            value.get("absolute", value.get("absolute_tolerance", absolute)),
            "absolute tolerance",
        ),
        "relative": _finite_number(
            value.get("relative", value.get("relative_tolerance", relative)),
            "relative tolerance",
        ),
    }
    if result["absolute"] < 0.0 or result["relative"] < 0.0:
        raise QualificationInputError("tolerances must be non-negative")
    return result


def _absolute_tolerance(value: Any, default: float) -> float:
    if value is None:
        return default
    if isinstance(value, Mapping):
        value = value.get("absolute", value.get("absolute_tolerance", default))
    result = _finite_number(value, "absolute tolerance")
    if result < 0.0:
        raise QualificationInputError("tolerances must be non-negative")
    return result


def _classification_counts(
    case_results: Sequence[Mapping[str, Any]],
    suite_invariants: Sequence[Mapping[str, Any]],
) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for case in case_results:
        for section in (
            "report_integrity",
            "cross_platform",
            "authoritative",
            "invariants",
            "secondary_diagnostic",
        ):
            for item in case[section]:
                counts[str(item["classification"])] += 1
    for item in suite_invariants:
        counts[str(item["classification"])] += 1
    return dict(sorted(counts.items()))


def _record_maximum(
    maxima: dict[str, dict[str, Any]],
    observable_class: str,
    absolute_error: float,
    case_id: str,
    identifier: str,
) -> None:
    if not math.isfinite(absolute_error):
        raise QualificationInputError("discrepancy is not finite")
    previous = maxima.get(observable_class)
    if previous is None or absolute_error > previous["absolute_error"]:
        maxima[observable_class] = {
            "absolute_error": absolute_error,
            "case_id": case_id,
            "observable_id": identifier,
        }


def _phase_is_undefined(
    first: Observable,
    second: Observable,
    magnitude_threshold: float,
) -> bool:
    """Return whether both phase values belong to numerical field nulls."""

    return (
        "phase" in first.observable_class
        and first.phase_reference_magnitude is not None
        and second.phase_reference_magnitude is not None
        and first.phase_reference_magnitude <= magnitude_threshold
        and second.phase_reference_magnitude <= magnitude_threshold
    )


def _worst_primary_classification(classifications: Iterable[str]) -> str:
    ranking = {
        "PASS": 0,
        "PASS_WITH_REFERENCE_PRECISION_LIMIT": 1,
        "FAIL": 2,
    }
    return max(classifications, key=ranking.__getitem__)


def _add_observable(
    observations: dict[str, Observable],
    observable: Observable,
) -> None:
    if observable.identifier in observations:
        raise QualificationInputError(
            f"report contains duplicate observable identity: {observable.identifier}"
        )
    if not math.isfinite(observable.value):
        raise QualificationInputError(
            f"report observable is not finite: {observable.identifier}"
        )
    observations[observable.identifier] = observable


def _power_observable_class(field: str) -> str:
    return {
        "input_power_watts": "input_power",
        "radiated_power_watts": "radiated_power",
        "structure_loss_watts": "structure_loss",
        "network_loss_watts": "network_loss",
        "efficiency_percent": "efficiency",
    }.get(field, "power")


def _canonical_field(field: str) -> str:
    return _FIELD_ALIASES.get(field, field)


def _resolve_repo_path(repo_root: Path, value: str) -> Path:
    path = Path(value)
    resolved = path.resolve() if path.is_absolute() else (repo_root / path).resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as error:
        raise QualificationInputError(
            f"repository path escapes repository root: {value}"
        ) from error
    return resolved


def _display_path(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return str(path)


def _json_copy(value: Any) -> Any:
    """Return a detached copy while rejecting non-JSON numeric values."""

    return json.loads(json.dumps(value, allow_nan=False))


def _read_json(path: Path, label: str) -> Mapping[str, Any]:
    if not path.is_file():
        raise QualificationInputError(f"{label} does not exist: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise QualificationInputError(
            f"{label} is not valid UTF-8 JSON: {path}"
        ) from error
    if not isinstance(value, Mapping):
        raise QualificationInputError(f"{label} root must be an object")
    return value


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise QualificationInputError(f"{label} must be a non-empty stripped string")
    return value


def _require_hash(value: Any, label: str) -> str:
    text = _require_string(value, label)
    if len(text) != 64 or any(
        character not in "0123456789abcdef" for character in text
    ):
        raise QualificationInputError(f"{label} must be lowercase SHA-256 hex")
    return text


def _object_tuple(
    value: Any,
    label: str,
    *,
    strings_are_rejected: bool,
) -> tuple[Mapping[str, Any], ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise QualificationInputError(f"{label} must be a list")
    objects: list[Mapping[str, Any]] = []
    for index, item in enumerate(value):
        if isinstance(item, str) and strings_are_rejected:
            raise QualificationInputError(
                f"{label}[{index}] is prose; checks must be typed objects"
            )
        if not isinstance(item, Mapping):
            raise QualificationInputError(f"{label}[{index}] must be an object")
        objects.append(item)
    return tuple(objects)


def _finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise QualificationInputError(f"{label} must be numeric")
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise QualificationInputError(f"{label} must be numeric") from error
    if not math.isfinite(result):
        raise QualificationInputError(f"{label} must be finite")
    return result


def _nonnegative_number(value: Any, label: str) -> float:
    result = _finite_number(value, label)
    if result < 0.0:
        raise QualificationInputError(f"{label} must be non-negative")
    return result


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise QualificationInputError(f"{label} must be an integer")
    try:
        result = int(value)
    except (TypeError, ValueError) as error:
        raise QualificationInputError(f"{label} must be an integer") from error
    if isinstance(value, float) and value != result:
        raise QualificationInputError(f"{label} must be an integer")
    if isinstance(value, str) and str(result) != value:
        raise QualificationInputError(f"{label} must be a canonical integer")
    return result


def _integer_pair(value: Any, label: str) -> tuple[int, int]:
    if not isinstance(value, list) or len(value) != 2:
        raise QualificationInputError(f"{label} must be [first, last]")
    return (_integer(value[0], label), _integer(value[1], label))


def _inclusive_range(first: int, last: int) -> range:
    step = 1 if last >= first else -1
    return range(first, last + step, step)


def _identity_number(value: float) -> str:
    return format(value, ".15g")


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare maintained NEC2C MSYS/UCRT64 reports with declared numerical "
            "references and invariants; use NEC2DX only as a secondary diagnostic."
        )
    )
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--msys-results", required=True, type=Path)
    parser.add_argument("--ucrt64-results", required=True, type=Path)
    parser.add_argument("--nec2dx-results", required=True, type=Path)
    parser.add_argument("--repository-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--summary-output",
        type=Path,
        help="write the compact committed-evidence projection to this path",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Command-line entry point."""

    arguments = _argument_parser().parse_args(argv)
    try:
        result = run_qualification(
            arguments.manifest,
            arguments.msys_results,
            arguments.ucrt64_results,
            arguments.nec2dx_results,
            repository_root=arguments.repository_root,
        )
    except (QualificationInputError, KeyError, ValueError) as error:
        print(f"qualification input error: {error}", file=sys.stderr)
        return 2
    serialized = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if arguments.output is None and arguments.summary_output is None:
        sys.stdout.write(serialized)
    elif arguments.output is not None:
        arguments.output.write_text(serialized, encoding="utf-8", newline="\n")
    if arguments.summary_output is not None:
        summary = qualification_summary(result)
        summary_serialized = (
            json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )
        arguments.summary_output.write_text(
            summary_serialized,
            encoding="utf-8",
            newline="\n",
        )
    return 1 if result["overall_status"] == "NUMERICAL_QUALIFICATION_BLOCKED" else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
