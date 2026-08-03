# SPDX-License-Identifier: BSD-2-Clause
"""Compare fresh maintained-source v1 and v2 qualification reports.

The frozen v0.0.5f-B result intentionally retains no complete raw reports or
full passing-observable projection.  This module therefore compares freshly
generated v1 and v2 reports at the complete parsed-dataclass level.  It permits
only the already-reviewed change to snapshot 3 of the Part III Example 2 case.
"""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .report_parser import QualificationReport, Snapshot, parse_report


FROZEN_CASE_IDS = (
    "minimal-free-space-dipole",
    "nec2-part3-example1-lumped-load",
    "nec2-part3-example2-conductivity-sweep",
    "nec2-part3-example3-perfect-ground",
    "nec2-part3-example3-reflection-ground",
    "connected-scaled-inverted-v",
    "minimal-dipole-21-segment",
    "minimal-dipole-41-segment",
)
EXAMPLE2_CASE_ID = "nec2-part3-example2-conductivity-sweep"
EXAMPLE2_LOADED_SNAPSHOT = 3
PRIMARY_SOLVERS = ("msys_nec2c", "ucrt64_nec2c")


class RegressionComparisonError(ValueError):
    """Raised when inputs or parsed v1-to-v2 behavior violate the frozen policy."""


def canonical_dataclass_bytes(value: Any) -> bytes:
    """Return deterministic UTF-8 JSON for a parsed report dataclass."""

    try:
        payload = asdict(value)
    except TypeError as error:
        raise TypeError("value must be a parsed report dataclass instance") from error
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def parsed_dataclass_sha256(value: Any) -> str:
    """Return the SHA-256 of a canonical parsed report dataclass."""

    return hashlib.sha256(canonical_dataclass_bytes(value)).hexdigest()


def compare_baseline_regression(
    manifest_path: str | Path,
    v1_msys_results: str | Path,
    v1_ucrt64_results: str | Path,
    v2_msys_results: str | Path,
    v2_ucrt64_results: str | Path,
) -> dict[str, Any]:
    """Compare fresh v1 and v2 reports and return deterministic compact evidence.

    All seven unaffected cases must remain exactly equal as parsed reports.
    Example 2 must contain four snapshots: snapshots 0 through 2 must remain
    exactly equal, while loaded snapshot 3 must change without changing its
    context, physical row identities, diagnostics, or report structure.
    """

    manifest_file = Path(manifest_path).resolve()
    manifest_bytes = _read_bytes(manifest_file, "qualification manifest")
    manifest = _read_manifest(manifest_bytes, manifest_file)
    cases = _load_frozen_cases(manifest)

    roots = {
        "msys_nec2c": {
            "v1": Path(v1_msys_results).resolve(),
            "v2": Path(v2_msys_results).resolve(),
        },
        "ucrt64_nec2c": {
            "v1": Path(v1_ucrt64_results).resolve(),
            "v2": Path(v2_ucrt64_results).resolve(),
        },
    }
    for solver_roots in roots.values():
        for label, root in solver_roots.items():
            if not root.is_dir():
                raise RegressionComparisonError(
                    f"{label} result directory does not exist: {root}"
                )

    solver_results: dict[str, Any] = {}
    loaded_values: dict[str, Any] = {}
    for solver in PRIMARY_SOLVERS:
        case_results: list[dict[str, Any]] = []
        for case in cases:
            case_id = case["case_id"]
            report_filename = case["report_filename"]
            expected_snapshots = case["expected_snapshots"]
            v1_report, v1_evidence = _load_report(
                roots[solver]["v1"] / report_filename,
                solver,
            )
            v2_report, v2_evidence = _load_report(
                roots[solver]["v2"] / report_filename,
                solver,
            )
            _require_snapshot_count(
                v1_report,
                expected_snapshots,
                f"{solver} v1 {case_id}",
            )
            _require_snapshot_count(
                v2_report,
                expected_snapshots,
                f"{solver} v2 {case_id}",
            )

            changed = _changed_snapshot_indices(v1_report, v2_report)
            _require_report_level_equality(solver, case_id, v1_report, v2_report)
            if case_id == EXAMPLE2_CASE_ID:
                _require_example2_change(solver, v1_report, v2_report, changed)
                loaded_values[solver] = {
                    "prior": _loaded_named_values(
                        v1_report.snapshots[EXAMPLE2_LOADED_SNAPSHOT]
                    ),
                    "v2": _loaded_named_values(
                        v2_report.snapshots[EXAMPLE2_LOADED_SNAPSHOT]
                    ),
                }
            elif changed or v1_report != v2_report:
                raise RegressionComparisonError(
                    f"{solver} {case_id} must remain exactly unchanged"
                )

            case_results.append(
                {
                    "case_id": case_id,
                    "report_filename": report_filename,
                    "snapshot_count": expected_snapshots,
                    "changed_snapshot_indices": changed,
                    "v1_report": {
                        **v1_evidence,
                        "parsed_sha256": parsed_dataclass_sha256(v1_report),
                    },
                    "v2_report": {
                        **v2_evidence,
                        "parsed_sha256": parsed_dataclass_sha256(v2_report),
                    },
                    "snapshots": [
                        {
                            "snapshot_index": index,
                            "equal": v1_snapshot == v2_snapshot,
                            "v1_sha256": parsed_dataclass_sha256(v1_snapshot),
                            "v2_sha256": parsed_dataclass_sha256(v2_snapshot),
                        }
                        for index, (v1_snapshot, v2_snapshot) in enumerate(
                            zip(v1_report.snapshots, v2_report.snapshots, strict=True)
                        )
                    ],
                }
            )
        solver_results[solver] = {
            "case_count": len(case_results),
            "cases": case_results,
        }

    return {
        "schema": "hf-nec2c.qualification-baseline-regression",
        "schema_version": 1,
        "status": "PASS",
        "manifest": {
            "filename": manifest_file.name,
            "bytes": len(manifest_bytes),
            "sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        },
        "policy": {
            "unaffected_cases": "complete parsed reports must remain exactly equal",
            "example2_unchanged_snapshots": [0, 1, 2],
            "example2_required_changed_snapshot": EXAMPLE2_LOADED_SNAPSHOT,
            "example2_loaded_context_and_structure_must_remain_equal": True,
        },
        "case_count": len(cases),
        "solvers": solver_results,
        "example2_loaded_named_values": loaded_values,
    }


def _read_bytes(path: Path, label: str) -> bytes:
    if not path.is_file():
        raise RegressionComparisonError(f"{label} does not exist: {path}")
    return path.read_bytes()


def _read_manifest(data: bytes, path: Path) -> Mapping[str, Any]:
    try:
        decoded = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise RegressionComparisonError(f"manifest is not UTF-8: {path}") from error
    try:
        manifest = json.loads(decoded)
    except json.JSONDecodeError as error:
        raise RegressionComparisonError(
            f"manifest is not valid JSON: {path}"
        ) from error
    if not isinstance(manifest, Mapping):
        raise RegressionComparisonError("qualification manifest must be an object")
    return manifest


def _load_frozen_cases(manifest: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    raw_cases = manifest.get("cases")
    if not isinstance(raw_cases, list):
        raise RegressionComparisonError("qualification manifest cases must be a list")
    case_ids = [
        str(case.get("case_id")) if isinstance(case, Mapping) else ""
        for case in raw_cases
    ]
    if tuple(case_ids) != FROZEN_CASE_IDS:
        raise RegressionComparisonError(
            "qualification manifest does not contain the exact frozen case inventory"
        )

    cases: list[dict[str, Any]] = []
    for raw_case, case_id in zip(raw_cases, case_ids, strict=True):
        assert isinstance(raw_case, Mapping)
        report_filename = raw_case.get("report_filename", f"{case_id}.out")
        if not isinstance(report_filename, str) or not report_filename:
            raise RegressionComparisonError(
                f"case {case_id} report filename must be a nonempty string"
            )
        if Path(report_filename).name != report_filename:
            raise RegressionComparisonError(
                f"case {case_id} report filename must be a basename"
            )
        expected_snapshots = _expected_snapshot_count(raw_case, case_id)
        cases.append(
            {
                "case_id": case_id,
                "report_filename": report_filename,
                "expected_snapshots": expected_snapshots,
            }
        )
    return tuple(cases)


def _expected_snapshot_count(case: Mapping[str, Any], case_id: str) -> int:
    invariants = case.get("invariants")
    if not isinstance(invariants, list):
        raise RegressionComparisonError(f"case {case_id} invariants must be a list")
    matches = [item for item in invariants if item.get("type") == "snapshot_count"]
    if len(matches) != 1:
        raise RegressionComparisonError(
            f"case {case_id} must declare exactly one snapshot_count invariant"
        )
    expected = matches[0].get("expected")
    if isinstance(expected, bool) or not isinstance(expected, int) or expected < 1:
        raise RegressionComparisonError(
            f"case {case_id} snapshot_count expected value must be a positive integer"
        )
    return expected


def _load_report(
    path: Path,
    solver: str,
) -> tuple[QualificationReport, dict[str, Any]]:
    data = _read_bytes(path, f"{solver} report")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise RegressionComparisonError(f"report is not UTF-8: {path}") from error
    report = parse_report(text, solver=solver)
    return report, {
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _require_snapshot_count(
    report: QualificationReport,
    expected: int,
    label: str,
) -> None:
    actual = len(report.snapshots)
    if actual != expected:
        raise RegressionComparisonError(
            f"{label} snapshot count mismatch: expected {expected}, got {actual}"
        )


def _changed_snapshot_indices(
    v1_report: QualificationReport,
    v2_report: QualificationReport,
) -> list[int]:
    return [
        index
        for index, (v1_snapshot, v2_snapshot) in enumerate(
            zip(v1_report.snapshots, v2_report.snapshots, strict=True)
        )
        if v1_snapshot != v2_snapshot
    ]


def _require_report_level_equality(
    solver: str,
    case_id: str,
    v1_report: QualificationReport,
    v2_report: QualificationReport,
) -> None:
    label = f"{solver} {case_id}"
    if v1_report.solver != v2_report.solver:
        raise RegressionComparisonError(f"{label} solver identity changed")
    if v1_report.diagnostics != v2_report.diagnostics:
        raise RegressionComparisonError(f"{label} report-level diagnostics changed")
    if v1_report.line_count != v2_report.line_count:
        raise RegressionComparisonError(f"{label} parsed line count changed")


def _require_example2_change(
    solver: str,
    v1_report: QualificationReport,
    v2_report: QualificationReport,
    changed: Sequence[int],
) -> None:
    if len(v1_report.snapshots) != EXAMPLE2_LOADED_SNAPSHOT + 1:
        raise RegressionComparisonError(
            f"{solver} {EXAMPLE2_CASE_ID} must contain exactly four snapshots"
        )
    if list(changed) != [EXAMPLE2_LOADED_SNAPSHOT]:
        if EXAMPLE2_LOADED_SNAPSHOT not in changed:
            raise RegressionComparisonError(
                f"{solver} {EXAMPLE2_CASE_ID} required loaded snapshot 3 did not change"
            )
        forbidden = [index for index in changed if index != EXAMPLE2_LOADED_SNAPSHOT]
        raise RegressionComparisonError(
            f"{solver} {EXAMPLE2_CASE_ID} has forbidden changed snapshot(s): "
            f"{forbidden}"
        )

    v1_loaded = v1_report.snapshots[EXAMPLE2_LOADED_SNAPSHOT]
    v2_loaded = v2_report.snapshots[EXAMPLE2_LOADED_SNAPSHOT]
    if _snapshot_structure(v1_loaded) != _snapshot_structure(v2_loaded):
        raise RegressionComparisonError(
            f"{solver} {EXAMPLE2_CASE_ID} loaded snapshot context or structure changed"
        )


def _snapshot_structure(snapshot: Snapshot) -> dict[str, Any]:
    return {
        "index": snapshot.index,
        "frequency_mhz": snapshot.frequency_mhz,
        "loading": snapshot.loading,
        "ground": snapshot.ground,
        "feed_identities": [list(feed.identity) for feed in snapshot.feeds],
        "current_identities": [list(current.identity) for current in snapshot.currents],
        "has_power_budget": snapshot.power_budget is not None,
        "far_field_identities": [
            list(sample.identity) for sample in snapshot.far_fields
        ],
        "has_average_power_gain": snapshot.average_power_gain is not None,
        "diagnostics": [asdict(item) for item in snapshot.diagnostics],
    }


def _loaded_named_values(snapshot: Snapshot) -> dict[str, Any]:
    try:
        feed = snapshot.feed(0, 5)
    except KeyError as error:
        raise RegressionComparisonError(
            "Example 2 loaded snapshot is missing feed identity tag 0, segment 5"
        ) from error
    power = snapshot.power_budget
    if power is None:
        raise RegressionComparisonError("Example 2 loaded snapshot has no power budget")

    def value_record(value: float | None, literal: str | None) -> dict[str, Any]:
        return {"literal": literal, "value": value}

    def power_record(field: str) -> dict[str, Any]:
        value = getattr(power, field)
        try:
            literal = power.literal(field)
        except KeyError:
            literal = None
        return value_record(value, literal)

    return {
        "snapshot_index": snapshot.index,
        "frequency_mhz": snapshot.frequency_mhz,
        "loading": snapshot.loading,
        "ground": snapshot.ground,
        "feed_current_real_amperes": value_record(
            feed.current_real,
            feed.raw_numeric_literals[4],
        ),
        "feed_current_imaginary_amperes": value_record(
            feed.current_imaginary,
            feed.raw_numeric_literals[5],
        ),
        "feed_resistance_ohms": value_record(
            feed.resistance_ohms,
            feed.raw_numeric_literals[6],
        ),
        "feed_reactance_ohms": value_record(
            feed.reactance_ohms,
            feed.raw_numeric_literals[7],
        ),
        "input_power_watts": power_record("input_power_watts"),
        "radiated_power_watts": power_record("radiated_power_watts"),
        "structure_loss_watts": power_record("structure_loss_watts"),
        "network_loss_watts": power_record("network_loss_watts"),
        "efficiency_percent": power_record("efficiency_percent"),
    }


__all__ = [
    "EXAMPLE2_CASE_ID",
    "EXAMPLE2_LOADED_SNAPSHOT",
    "FROZEN_CASE_IDS",
    "RegressionComparisonError",
    "canonical_dataclass_bytes",
    "compare_baseline_regression",
    "parsed_dataclass_sha256",
]
