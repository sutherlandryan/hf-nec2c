# SPDX-License-Identifier: BSD-2-Clause
"""Freeze the v0.0.5f-B corpus and compact qualification disposition."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPOSITORY_ROOT / "manifests" / "numerical-qualification-v0.0.5f-b.json"
SUMMARY_PATH = (
    REPOSITORY_ROOT / "manifests" / "numerical-qualification-v0.0.5f-b-results.json"
)

EXPECTED_CASE_IDS = [
    "minimal-free-space-dipole",
    "nec2-part3-example1-lumped-load",
    "nec2-part3-example2-conductivity-sweep",
    "nec2-part3-example3-perfect-ground",
    "nec2-part3-example3-reflection-ground",
    "connected-scaled-inverted-v",
    "minimal-dipole-21-segment",
    "minimal-dipole-41-segment",
]
EXPECTED_MANIFEST_CANONICAL_SHA256 = (
    "b25a27595a08feec7b28dfa6d6b46e1e70666c8f574c9d2839021c21fdad8cd3"
)
EXPECTED_MANIFEST_RAW_SHA256 = (
    "7df54bd3b5c44b2f9b588b42534d201ddd3a2fffbbb8a8d8fb663fd51262c817"
)
EXPECTED_SUMMARY_SHA256 = (
    "dfa0fff497cd8fb1b51894e3975cf75031a65a7c18ef89e58403efa318f297b2"
)


def sha256_bytes(data: bytes) -> str:
    """Return lowercase SHA-256 for exact evidence bytes."""

    return hashlib.sha256(data).hexdigest()


class QualificationManifestTests(unittest.TestCase):
    """Validate inventory, provenance, hashes, and the blocked summary."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest_bytes = MANIFEST_PATH.read_bytes()
        cls.manifest = json.loads(cls.manifest_bytes.decode("utf-8"))
        cls.summary_bytes = SUMMARY_PATH.read_bytes()
        cls.summary = json.loads(cls.summary_bytes.decode("utf-8"))

    def test_manifest_semantics_and_text_are_frozen(self) -> None:
        self.assertNotIn(b"\r", self.manifest_bytes)
        self.assertTrue(self.manifest_bytes.endswith(b"\n"))
        canonical = json.dumps(
            self.manifest,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        self.assertEqual(
            sha256_bytes(canonical),
            EXPECTED_MANIFEST_CANONICAL_SHA256,
        )
        self.assertEqual(
            sha256_bytes(self.manifest_bytes),
            EXPECTED_MANIFEST_RAW_SHA256,
        )

    def test_case_inventory_and_deck_hashes_are_exact(self) -> None:
        cases = self.manifest["cases"]
        self.assertEqual([case["case_id"] for case in cases], EXPECTED_CASE_IDS)
        self.assertEqual(len(cases), 8)

        for case in cases:
            deck_path = REPOSITORY_ROOT / case["deck_path"]
            metadata_path = REPOSITORY_ROOT / case["metadata_path"]
            self.assertTrue(deck_path.is_file(), case["deck_path"])
            self.assertTrue(metadata_path.is_file(), case["metadata_path"])
            self.assertEqual(
                sha256_bytes(deck_path.read_bytes()),
                case["deck_sha256"],
                case["case_id"],
            )
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            self.assertEqual(
                sha256_bytes(metadata_path.read_bytes()),
                case["metadata_sha256"],
                case["case_id"],
            )
            self.assertEqual(metadata["identity"]["case_id"], case["case_id"])
            self.assertEqual(metadata["deck"]["path"], case["deck_path"])
            self.assertEqual(metadata["deck"]["sha256"], case["deck_sha256"])
            if case["authoritative_checks"]:
                precision_policy = metadata["reference_precision"]["policy"]
                self.assertIn("equal centers are PASS", precision_policy)
                self.assertIn(
                    "distinct intersecting intervals are "
                    "PASS_WITH_REFERENCE_PRECISION_LIMIT",
                    precision_policy,
                )
                self.assertIn("disjoint intervals are FAIL", precision_policy)

    def test_every_published_literal_is_bound_to_the_official_scan(self) -> None:
        checks = [
            check
            for case in self.manifest["cases"]
            for check in case["authoritative_checks"]
        ]
        self.assertEqual(len(checks), 76)
        for check in checks:
            self.assertEqual(check["source_kind"], "official_ntis_scan")
            self.assertIn("Section IV Example", check["source_locator"])
            self.assertIn("printed page", check["source_locator"])
            self.assertIn("PDF page", check["source_locator"])
            self.assertIsInstance(check["reference_literal"], str)
            self.assertTrue(check["reference_literal"])
            self.assertIsInstance(check["units"], str)
            self.assertTrue(check["units"])

    def test_scaled_connected_case_fixes_geometry_and_current_identity(self) -> None:
        case = next(
            item
            for item in self.manifest["cases"]
            if item["case_id"] == "connected-scaled-inverted-v"
        )
        deck = (REPOSITORY_ROOT / case["deck_path"]).read_text(encoding="ascii")
        self.assertIn("GW 1 5 0 0 200 0 0 250 0.1\n", deck)
        self.assertIn("GW 2 10 0 0 250 -500 0 0 0.1\n", deck)
        self.assertIn("GW 3 10 0 0 250 500 0 0 0.1\n", deck)
        self.assertIn("GS 0 0 0.01\n", deck)

        invariants = case["invariants"]
        positions = [item for item in invariants if item["type"] == "current_position"]
        self.assertEqual(len(positions), 6)
        symmetry = next(
            item
            for item in invariants
            if item["id"] == "inverted-v.arm-current-symmetry"
        )
        self.assertEqual(symmetry["left"], {"tag": 2, "segments": [6, 15]})
        self.assertEqual(symmetry["right"], {"tag": 3, "segments": [16, 25]})

    def test_compact_summary_freezes_expected_blocked_disposition(self) -> None:
        self.assertNotIn(b"\r", self.summary_bytes)
        self.assertEqual(sha256_bytes(self.summary_bytes), EXPECTED_SUMMARY_SHA256)
        self.assertEqual(
            self.summary["manifest"]["sha256"],
            EXPECTED_MANIFEST_RAW_SHA256,
        )
        self.assertEqual(
            self.summary["overall_status"],
            "NUMERICAL_QUALIFICATION_BLOCKED",
        )
        self.assertEqual(self.summary["case_count"], 8)
        self.assertEqual(
            self.summary["classification_counts"],
            {
                "FAIL": 8,
                "NOT_APPLICABLE": 334,
                "PASS": 5981,
                "PASS_WITH_REFERENCE_PRECISION_LIMIT": 26,
                "SECONDARY_DISAGREEMENT": 43,
            },
        )

        statuses = {
            case["case_id"]: case["case_status"] for case in self.summary["cases"]
        }
        self.assertEqual(
            statuses["nec2-part3-example2-conductivity-sweep"],
            "BLOCKED_BY_NUMERICAL_DISCREPANCY",
        )
        self.assertEqual(
            statuses["nec2-part3-example1-lumped-load"],
            "QUALIFIED_FOR_INTENDED_SUBSET",
        )
        self.assertEqual(
            statuses["nec2-part3-example3-perfect-ground"],
            "QUALIFIED_FOR_INTENDED_SUBSET",
        )
        self.assertEqual(
            statuses["nec2-part3-example3-reflection-ground"],
            "QUALIFIED_FOR_INTENDED_SUBSET",
        )
        for case_id in (
            "minimal-free-space-dipole",
            "connected-scaled-inverted-v",
            "minimal-dipole-21-segment",
            "minimal-dipole-41-segment",
        ):
            self.assertEqual(
                statuses[case_id],
                "QUALIFIED_WITH_DOCUMENTED_GAP",
            )

        failed_ids = {item["id"] for item in self.summary["authoritative_failures"]}
        self.assertEqual(
            failed_ids,
            {
                "ex2.300-loaded.feed.current-real",
                "ex2.300-loaded.feed.current-imaginary",
                "ex2.300-loaded.feed.resistance",
                "ex2.300-loaded.feed.reactance",
                "ex2.300-loaded.power.input",
                "ex2.300-loaded.power.radiated",
                "ex2.300-loaded.power.structure-loss",
                "ex2.300-loaded.efficiency",
            },
        )
        self.assertEqual(
            sum(item["count"] for item in self.summary["secondary_disagreements"]),
            43,
        )
        self.assertTrue(
            all(
                item["case_id"] == "nec2-part3-example2-conductivity-sweep"
                and item["snapshot_index"] == 3
                for item in self.summary["secondary_disagreements"]
            )
        )


if __name__ == "__main__":
    unittest.main()
