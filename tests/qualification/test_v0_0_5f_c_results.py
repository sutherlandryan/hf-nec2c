# SPDX-License-Identifier: BSD-2-Clause
"""Freeze the compact v0.0.5f-C qualification result and its inputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / "manifests" / "numerical-qualification-v0.0.5f-c-results.json"
V2_MANIFEST = ROOT / "manifests" / "maintained-source-v2.json"
V2_PATCH = ROOT / "patches" / "maintained" / "nec2c-1.3.1-hf-portability-zint-v2.patch"
RESULT_IDENTITY = (
    11615,
    "47f72ce8c6eb17a94a98611010801f6052be429b7505d0275f33d015abd5a90b",
)
RESULT_CANONICAL_SHA256 = (
    "9a14d6ace0d5b8b9224bdb14327fd7b193bc2b3fee9778611ab4f3375cba5323"
)
V2_MANIFEST_IDENTITY = (
    7809,
    "6d3899ede74d77832732b196e5e64636578c03e667d5e6feb43270ab8e39f37a",
)
V2_PATCH_IDENTITY = (
    7624,
    "9b165d93e4e3335f4c2762c70950a7086d1f6c7ee0559a1f3f3f5c08f6219e52",
)
FROZEN_INPUTS = {
    "manifest": (
        ROOT / "manifests" / "numerical-qualification-v0.0.5f-b.json",
        45630,
        "7df54bd3b5c44b2f9b588b42534d201ddd3a2fffbbb8a8d8fb663fd51262c817",
    ),
    "prior_result": (
        ROOT / "manifests" / "numerical-qualification-v0.0.5f-b-results.json",
        39413,
        "dfa0fff497cd8fb1b51894e3975cf75031a65a7c18ef89e58403efa318f297b2",
    ),
}
DISPOSITION = (
    "B. V2 SOURCE FIX VALIDATED; QUALIFICATION REMAINS BLOCKED BY THE "
    "FROZEN REFERENCE MISMATCH"
)


def _identity(path: Path) -> tuple[int, str]:
    data = path.read_bytes()
    return len(data), hashlib.sha256(data).hexdigest()


class QualificationV005FCResultTests(unittest.TestCase):
    """Require deterministic evidence and the unchanged frozen policy boundary."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = RESULT.read_bytes()
        cls.result = json.loads(cls.raw.decode("utf-8"))

    def test_result_is_deterministic_and_binds_v2(self) -> None:
        self.assertNotIn(b"\r", self.raw)
        self.assertTrue(self.raw.endswith(b"\n"))
        self.assertEqual(_identity(RESULT), RESULT_IDENTITY)
        canonical = json.dumps(
            self.result,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        self.assertEqual(
            hashlib.sha256(canonical).hexdigest(),
            RESULT_CANONICAL_SHA256,
        )
        self.assertEqual(_identity(V2_MANIFEST), V2_MANIFEST_IDENTITY)
        self.assertEqual(_identity(V2_PATCH), V2_PATCH_IDENTITY)
        source = self.result["maintained_source_v2"]
        self.assertEqual(source["identity"], "HF_NEC2C_MAINTAINED_SOURCE_V2")
        self.assertEqual(
            (source["manifest"]["bytes"], source["manifest"]["sha256"]),
            V2_MANIFEST_IDENTITY,
        )
        self.assertEqual(
            (source["combined_patch"]["bytes"], source["combined_patch"]["sha256"]),
            V2_PATCH_IDENTITY,
        )

    def test_frozen_b_inputs_and_policy_are_unchanged(self) -> None:
        frozen = self.result["frozen_corpus"]
        self.assertFalse(
            frozen["case_definitions_expected_values_tolerances_and_policy_changed"]
        )
        self.assertEqual(frozen["case_count"], 8)
        for key, (path, size, digest) in FROZEN_INPUTS.items():
            self.assertEqual(_identity(path), (size, digest))
            self.assertEqual(
                (frozen[key]["bytes"], frozen[key]["sha256"]),
                (size, digest),
            )

    def test_direct_build_and_secondary_boundaries_are_frozen(self) -> None:
        direct = self.result["direct_zint_validation"]
        self.assertEqual(direct["status"], "PASS")
        self.assertEqual(len(direct["sample_x"]), 12)
        self.assertEqual(
            direct["boundary_selection"],
            {"8.0": "small", "110.0": "medium", "110.001": "large"},
        )
        self.assertTrue(direct["cross_toolchain_numeric_values_equal"])

        builds = self.result["maintained_builds"]
        self.assertEqual(builds["msys_gcc"]["status"], "PASS")
        self.assertEqual(builds["ucrt64_gcc"]["status"], "PASS")
        self.assertIn("msys-2.0.dll", builds["msys_gcc"]["imported_dlls"])
        self.assertFalse(builds["ucrt64_gcc"]["imports_msys_2_0_dll"])
        self.assertNotIn("msys-2.0.dll", builds["ucrt64_gcc"]["imported_dlls"])

        secondary = self.result["secondary_reference_build"]
        self.assertEqual(secondary["role"], "SECONDARY_DIAGNOSTIC_ONLY")
        self.assertTrue(secondary["internal_only"])
        self.assertTrue(secondary["reports_complete_and_diagnostic_free"])
        self.assertEqual(secondary["secondary_disagreement_count"], 0)

    def test_v1_to_v2_regression_has_only_the_reviewed_change(self) -> None:
        baseline = self.result["v1_baseline_reproduction"]
        self.assertEqual(baseline["status"], "PASS")
        self.assertTrue(baseline["classification_counts_match_frozen_result"])
        self.assertEqual(baseline["raw_report_identity_match_count"], 19)
        self.assertEqual(baseline["raw_report_identity_difference_count"], 5)
        self.assertTrue(
            baseline["raw_report_identity_is_not_a_semantic_pass_criterion"]
        )
        self.assertTrue(
            baseline["summary_equal_after_rebinding_only_case_report_evidence"]
        )

        regression = self.result["parsed_regression"]
        self.assertEqual(regression["status"], "PASS")
        self.assertEqual(len(regression["unaffected_case_ids"]), 7)
        for solver in ("msys_nec2c", "ucrt64_nec2c"):
            evidence = regression["solvers"][solver]
            self.assertEqual(evidence["unaffected_complete_parsed_reports_equal"], 7)
            self.assertEqual(evidence["example2_changed_snapshot_indices"], [3])
        self.assertEqual(
            [snapshot["equal"] for snapshot in regression["example2_snapshot_sha256"]],
            [True, True, True, False],
        )

    def test_disposition_b_has_exactly_one_authoritative_failure(self) -> None:
        milestone = self.result["milestone"]
        self.assertEqual(milestone["disposition"], DISPOSITION)
        self.assertEqual(
            milestone["status"],
            "QUALIFICATION_REMAINS_BLOCKED_BY_FROZEN_REFERENCE_MISMATCH",
        )

        qualification = self.result["qualification"]
        self.assertEqual(
            qualification["overall_status"],
            "NUMERICAL_QUALIFICATION_BLOCKED",
        )
        self.assertEqual(
            qualification["classification_counts"],
            {
                "FAIL": 1,
                "NOT_APPLICABLE": 334,
                "PASS": 6028,
                "PASS_WITH_REFERENCE_PRECISION_LIMIT": 29,
            },
        )
        self.assertEqual(
            qualification["section_classification_counts"]["report_integrity"],
            {"PASS": 24},
        )
        self.assertEqual(qualification["secondary_disagreements"], [])
        self.assertEqual(len(qualification["authoritative_failures"]), 1)
        failure = qualification["authoritative_failures"][0]
        self.assertEqual(failure["id"], "ex2.300-loaded.feed.current-imaginary")
        self.assertEqual(failure["reference_literal"], "-3.86680E-03")
        self.assertEqual(failure["candidate_literal"], "-3.8666E-03")
        self.assertTrue(all(qualification["gates"].values()))

        boundaries = self.result["authorization_boundaries"]
        self.assertFalse(boundaries["release_authorized"])
        self.assertFalse(boundaries["product_integration_approved"])
        self.assertFalse(boundaries["maintained_source_v2_tag_created"])
        self.assertEqual(boundaries["distribution_status"], "UNRELEASED")


if __name__ == "__main__":
    unittest.main()
