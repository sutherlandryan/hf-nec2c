# SPDX-License-Identifier: BSD-2-Clause
"""Hostile-input and end-to-end tests for the reviewed A2 source guard."""

from __future__ import annotations

import importlib.util
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_GUARD_PATH = (
    REPOSITORY_ROOT / "build-support" / "windows-x64" / "source_guard.py"
)
SPEC = importlib.util.spec_from_file_location("a2_source_guard", SOURCE_GUARD_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("could not load source guard")
source_guard = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = source_guard
SPEC.loader.exec_module(source_guard)


class FakeArchive:
    """Minimal TarFile-shaped member inventory for validation tests."""

    def __init__(self, members: list[tarfile.TarInfo]) -> None:
        self._members = members

    def getmembers(self) -> list[tarfile.TarInfo]:
        return self._members


def directory_member(name: str) -> tarfile.TarInfo:
    member = tarfile.TarInfo(name)
    member.type = tarfile.DIRTYPE
    return member


def regular_member(name: str) -> tarfile.TarInfo:
    member = tarfile.TarInfo(name)
    member.type = tarfile.REGTYPE
    member.size = 1
    return member


class SourceGuardTests(unittest.TestCase):
    """Exercise path rejection, member rejection, extraction, and tamper checks."""

    def test_archive_path_policy_accepts_only_fixed_layout(self) -> None:
        self.assertEqual(
            source_guard.validate_archive_path(
                "nec2c-1.3.1",
                label="test",
                expected_component_count=1,
            ).as_posix(),
            "nec2c-1.3.1",
        )
        self.assertEqual(
            source_guard.validate_archive_path(
                "nec2c-1.3.1/nec2c.h",
                label="test",
                expected_component_count=2,
            ).as_posix(),
            "nec2c-1.3.1/nec2c.h",
        )
        unsafe = (
            "",
            "/nec2c-1.3.1/nec2c.h",
            "../nec2c-1.3.1/nec2c.h",
            "nec2c-1.3.1/../nec2c.h",
            "nec2c-1.3.1//nec2c.h",
            r"nec2c-1.3.1\nec2c.h",
            "C:/nec2c-1.3.1/nec2c.h",
            "other/nec2c.h",
            "nec2c-1.3.1/nested/nec2c.h",
        )
        for value in unsafe:
            with self.subTest(value=value):
                with self.assertRaises(source_guard.SourceGuardError):
                    source_guard.validate_archive_path(
                        value,
                        label="test",
                        expected_component_count=2,
                    )

    def test_archive_member_policy_rejects_special_and_colliding_entries(
        self,
    ) -> None:
        top = directory_member("nec2c-1.3.1")

        symlink = tarfile.TarInfo("nec2c-1.3.1/nec2c.h")
        symlink.type = tarfile.SYMTYPE
        symlink.linkname = "other.h"
        with self.assertRaisesRegex(
            source_guard.SourceGuardError,
            "link or special",
        ):
            source_guard.validate_archive_members(
                FakeArchive([top, symlink]),
                {"nec2c-1.3.1/nec2c.h": "0" * 64},
            )

        with self.assertRaisesRegex(
            source_guard.SourceGuardError,
            "duplicate or case-colliding",
        ):
            source_guard.validate_archive_members(
                FakeArchive(
                    [
                        top,
                        regular_member("nec2c-1.3.1/nec2c.h"),
                        regular_member("nec2c-1.3.1/NEC2C.H"),
                    ]
                ),
                {"nec2c-1.3.1/nec2c.h": "0" * 64},
            )

        with self.assertRaisesRegex(
            source_guard.SourceGuardError,
            "path is unsafe",
        ):
            source_guard.validate_archive_members(
                FakeArchive(
                    [
                        top,
                        regular_member("nec2c-1.3.1/../escape.h"),
                    ]
                ),
                {"nec2c-1.3.1/escape.h": "0" * 64},
            )

    def test_preserved_archive_inventory_authenticates(self) -> None:
        manifest = source_guard.parse_file_manifest(REPOSITORY_ROOT)
        self.assertEqual(len(manifest), 34)
        archive_path = source_guard.authenticate_archive(REPOSITORY_ROOT)
        with tarfile.open(archive_path, mode="r:bz2") as archive:
            members = source_guard.validate_archive_members(archive, manifest)
        self.assertEqual(set(members), set(manifest))

    def test_fresh_extraction_verifies_and_tampering_is_detected(self) -> None:
        build_temp = REPOSITORY_ROOT / ".build-temp"
        build_temp.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix="source-guard-test-",
            dir=build_temp,
        ) as temporary:
            destination = Path(temporary) / "source"
            source_guard.extract_authenticated_source(
                REPOSITORY_ROOT,
                destination,
            )
            manifest = source_guard.parse_file_manifest(REPOSITORY_ROOT)
            source_guard.verify_extracted_tree(destination, manifest)

            target = destination / "nec2c-1.3.1" / "nec2c.h"
            target.write_bytes(target.read_bytes() + b"\n")
            with self.assertRaisesRegex(
                source_guard.SourceGuardError,
                "SHA-256 mismatch",
            ):
                source_guard.verify_extracted_tree(destination, manifest)


if __name__ == "__main__":
    unittest.main()
