# SPDX-License-Identifier: BSD-2-Clause
"""Contract tests for the A2b untouched-source MSYS2 UCRT64 evidence."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = (
    REPOSITORY_ROOT / "manifests" / "windows-x64-mingw-ucrt64-unmodified-build-v1.json"
)
DRIVER_PATH = (
    REPOSITORY_ROOT / "build-support" / "windows-x64-mingw-ucrt64" / "build.ps1"
)
BUILD_README_PATH = DRIVER_PATH.with_name("README.md")
REPORT_PATH = REPOSITORY_ROOT / "docs" / "WINDOWS_X64_MINGW_UCRT64_UNMODIFIED_BUILD.md"
SOURCE_GUARD_PATH = (
    REPOSITORY_ROOT / "build-support" / "windows-x64" / "source_guard.py"
)
PRESERVATION_WRAPPER_PATH = REPOSITORY_ROOT / "verify-preservation.ps1"
PRESERVATION_VERIFIER_PATH = REPOSITORY_ROOT / "tools" / "verify_preservation.py"
EXPECTED_ARCHIVE_SHA256 = (
    "8c706008bcb11c34bf33a3f8f78711c79f7bb49de8a22d74df6b10e1203c013e"
)
EXPECTED_GCC_SHA256 = "f96a3bdb1d3a3967b309d75c7413399391e857b5be4cb17162572ed66f6772a0"
EXPECTED_BASH_SHA256 = (
    "41b09f0a9c1c68fd65253a7e8087b3775f0af245b729ade74ca4425d14392c2d"
)
EXPECTED_PACMAN_SHA256 = (
    "209b2d527f359608cdb092515d3d99f46ac9d2209d130adced81a8cdd79057d8"
)
EXPECTED_MSYS_RUNTIME_SHA256 = (
    "0cb645ead21947b7e865448413f3e281236638ed38695b43c2a6d9c06598e046"
)
EXPECTED_DRIVER_SHA256 = (
    "021d370f0472158af43045e87ac2a980564137abb9b1ff497b8bccc7222d3e04"
)
EXPECTED_SOURCE_GUARD_SHA256 = (
    "331718ae2b79390b71b8eb935953b7652d5a702a3e56cf1deb6aa51152b88b13"
)
EXPECTED_PRESERVATION_WRAPPER_SHA256 = (
    "a8c19981db3fdbcaee380755c29f56975ea1ead3d78976fb90c81c22e438e0f7"
)
EXPECTED_PRESERVATION_VERIFIER_SHA256 = (
    "4fbfebcf7a09307dc7314a75fe2789860f243ae60e8b64604125821f729fc658"
)
EXPECTED_ATTEMPT_RECORD_SHA256 = (
    "7de74afe975cf1da3218dcb9300a371db7291b420e5106af460ca0a5a233b2f2"
)
EXPECTED_STARTING_MAIN = "e74b603cab40ed7d8613d6318acc84abd4ba4217"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
MARKDOWN_LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)\r\n]+)\)")
FORBIDDEN_BUILD_SUFFIXES = {
    ".7z",
    ".a",
    ".bin",
    ".bz2",
    ".dll",
    ".exe",
    ".exp",
    ".gz",
    ".ilk",
    ".lib",
    ".msi",
    ".msix",
    ".o",
    ".obj",
    ".pdb",
    ".tar",
    ".zip",
    ".zst",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_string_values(value: object, path: str = "$"):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from iter_string_values(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from iter_string_values(child, f"{path}[{index}]")
    elif isinstance(value, str):
        yield path, value


def local_markdown_targets(path: Path) -> list[str]:
    targets: list[str] = []
    text = path.read_text(encoding="utf-8")
    for match in MARKDOWN_LINK_PATTERN.finditer(text):
        target = match.group(1).strip()
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1]
        else:
            # The A2b documentation does not use link titles. Keeping this
            # parser deliberately narrow prevents a title from becoming a path.
            target = target.split(maxsplit=1)[0]
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc or target.startswith("#"):
            continue
        targets.append(unquote(parsed.path))
    return targets


class MingwUcrt64EvidenceTests(unittest.TestCase):
    """Validate the versioned A2b boundary and its recorded failed attempt."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest_bytes = MANIFEST_PATH.read_bytes()
        cls.manifest = json.loads(cls.manifest_bytes.decode("utf-8"))
        cls.driver_text = DRIVER_PATH.read_text(encoding="utf-8")
        cls.report_text = REPORT_PATH.read_text(encoding="utf-8")

    def test_manifest_is_canonical_sorted_json(self) -> None:
        self.assertFalse(self.manifest_bytes.startswith(b"\xef\xbb\xbf"))
        self.assertNotIn(b"\r", self.manifest_bytes)
        expected = (
            json.dumps(
                self.manifest,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
        self.assertEqual(self.manifest_bytes, expected)
        self.assertEqual(
            self.manifest["serialization"],
            {
                "encoding": "UTF-8",
                "final_newline": True,
                "indentation_spaces": 2,
                "key_order": "recursive ASCII lexical",
                "line_endings": "LF",
            },
        )

    def test_manifest_records_authenticated_official_inputs(self) -> None:
        acquisition = self.manifest["acquisition"]
        self.assertEqual(acquisition["release"], "2026-06-11")
        self.assertEqual(acquisition["installer_file"], "msys2-x86_64-20260611.exe")
        self.assertEqual(
            acquisition["installer_sha256"],
            acquisition["sidecar_sha256_value"],
        )
        self.assertEqual(
            acquisition["installer_sha256"],
            acquisition["github_api_asset_sha256"],
        )
        self.assertEqual(
            acquisition["installer_sha256"],
            "3150d7d9aa5dedd900a7f52300d4d918271e3a8fc47de94848818fd5a430e6b0",
        )
        self.assertTrue(acquisition["checksum_match"])
        self.assertEqual(acquisition["authenticode"]["status"], "Valid")
        self.assertNotIn(
            "?",
            acquisition["final_redirect_url_without_expiring_query"],
        )

        installation = self.manifest["installation"]
        self.assertEqual(installation["installation_path"], r"C:\msys64")
        self.assertEqual(installation["exit_code"], 0)
        self.assertEqual(installation["elevation"], "not_required")
        self.assertFalse(installation["global_windows_path_changed"])
        self.assertFalse(installation["installation_root_reparse_point"])
        pre_install = installation["pre_install_inventory"]
        self.assertFalse(pre_install["c_msys64_existed"])
        self.assertFalse(pre_install["stop_condition"])
        self.assertIn("coverage limitation", pre_install["all_users_appx_query"])
        for key in (
            "matching_commands",
            "matching_common_installation_roots",
            "matching_path_entries",
            "matching_processes",
            "matching_uninstall_entries",
        ):
            self.assertEqual(pre_install[key], [], key)

        toolchain = self.manifest["toolchain"]
        self.assertEqual(
            toolchain["explicit_requests"],
            [
                "mingw-w64-ucrt-x86_64-gcc",
                "make",
                "autoconf",
                "automake",
                "libtool",
                "pkgconf",
            ],
        )
        self.assertEqual(
            toolchain["gcc"]["package"],
            "mingw-w64-ucrt-x86_64-gcc 16.1.0-5",
        )
        self.assertEqual(toolchain["gcc"]["target"], "x86_64-w64-mingw32")
        self.assertEqual(
            toolchain["gcc"]["resolved_compiler_path"],
            "/ucrt64/bin/gcc",
        )
        self.assertEqual(toolchain["gcc"]["executable_sha256"], EXPECTED_GCC_SHA256)
        self.assertEqual(
            toolchain["bash"],
            {
                "executable_sha256": EXPECTED_BASH_SHA256,
                "package": "bash 5.3.015-1",
                "resolved_path": "/usr/bin/bash",
            },
        )
        self.assertEqual(
            toolchain["pacman"],
            {
                "executable_sha256": EXPECTED_PACMAN_SHA256,
                "package": "pacman 6.1.0-25",
                "remote_package_signature_policy": "Required",
                "resolved_path": "/usr/bin/pacman",
            },
        )
        self.assertEqual(
            toolchain["msys_runtime"],
            {
                "executable_sha256": EXPECTED_MSYS_RUNTIME_SHA256,
                "package": "msys2-runtime 3.6.10-1",
                "resolved_path": "/usr/bin/msys-2.0.dll",
            },
        )
        self.assertEqual(
            toolchain["binutils"]["linker_sha256"],
            "fb152d34cf00bf66fc57a66522806a4e64914654d8c1ab8cdd0a1d78283ec215",
        )
        self.assertEqual(
            toolchain["binutils"]["resolved_linker_path"],
            "/ucrt64/bin/ld",
        )
        self.assertEqual(toolchain["make"]["resolved_path"], "/usr/bin/make")
        integrity = toolchain["integrity"]
        self.assertTrue(integrity["qualified_exception"])
        self.assertTrue(integrity["package_archives_match_repository_sha256"])
        self.assertEqual(
            integrity["pacman_remote_package_signature_policy"],
            "Required",
        )
        self.assertEqual(
            integrity["pacman_transaction_authentication"],
            "enforced for the 38-package transaction",
        )
        full_qkk = integrity["full_added_package_qkk"]
        self.assertEqual(full_qkk["package_count"], 38)
        self.assertEqual(full_qkk["pacman_exit_code"], 1)
        self.assertEqual(full_qkk["altered_file_reports"], 606)
        legacy_audit = integrity["affected_legacy_audit"]
        self.assertTrue(legacy_audit["overall_pass"])
        self.assertEqual(
            legacy_audit["expected_package_count"],
            6,
        )
        self.assertEqual(
            legacy_audit["observed_qkk_sha256_warning_count"],
            606,
        )
        self.assertEqual(len(legacy_audit["packages"]), 6)
        for package in legacy_audit["packages"]:
            self.assertTrue(package["detached_signature"]["valid"])
            self.assertTrue(package["repository_archive"]["match"])
            self.assertTrue(package["mtree"]["local_database_matches_archive"])
            self.assertTrue(package["stored_md5_vs_installed"]["all_match"])
            self.assertTrue(package["aggregate_payload"]["match"])
            self.assertEqual(package["payload"]["symlinks"], 0)
            self.assertEqual(package["payload"]["archive_install_scripts"], 0)
            self.assertEqual(package["payload"]["local_install_scripts"], 0)

    def test_package_inventories_are_complete_and_internally_consistent(
        self,
    ) -> None:
        msys2 = self.manifest["msys2"]
        toolchain = self.manifest["toolchain"]
        base_record = msys2["post_update_pre_toolchain_inventory"]
        final_record = msys2["post_toolchain_inventory"]
        added_record = toolchain["added_packages_inventory"]
        base = base_record["packages"]
        final = final_record["packages"]
        added = toolchain["added_packages"]

        self.assertEqual(base_record["count"], 90)
        self.assertEqual(final_record["count"], 128)
        self.assertEqual(added_record["count"], 38)
        self.assertEqual(len(base), 90)
        self.assertEqual(len(final), 128)
        self.assertEqual(len(added), 38)
        self.assertEqual(base, sorted(set(base)))
        self.assertEqual(final, sorted(set(final)))

        added_identities = [
            f"{package['name']} {package['version']}" for package in added
        ]
        self.assertEqual(
            len({package["name"] for package in added}),
            len(added),
        )
        self.assertEqual(set(final) - set(base), set(added_identities))
        self.assertFalse(set(base) - set(final))

        # These hashes preserve the collected files: the base and added-package
        # inventories use LF, while the post-toolchain inventory uses CRLF.
        base_bytes = ("\n".join(base) + "\n").encode("utf-8")
        final_bytes = ("\r\n".join(final) + "\r\n").encode("utf-8")
        added_bytes = ("\n".join(added_identities) + "\n").encode("utf-8")
        self.assertEqual(base_record["line_endings"], "LF")
        self.assertEqual(final_record["line_endings"], "CRLF")
        self.assertEqual(added_record["line_endings"], "LF")
        self.assertEqual(len(base_bytes), base_record["bytes"])
        self.assertEqual(
            hashlib.sha256(base_bytes).hexdigest(),
            base_record["sha256"],
        )
        self.assertEqual(len(final_bytes), final_record["bytes"])
        self.assertEqual(
            hashlib.sha256(final_bytes).hexdigest(),
            final_record["sha256"],
        )
        self.assertEqual(
            hashlib.sha256(added_bytes).hexdigest(),
            added_record["sha256"],
        )
        for package in added:
            self.assertRegex(package["archive_sha256"], SHA256_PATTERN)
            self.assertTrue(package["archive_file"].endswith(".pkg.tar.zst"))

    def test_failed_build_result_preserves_the_milestone_boundary(self) -> None:
        self.assertEqual(
            self.manifest["schema"],
            "org.sutherlandryan.hf-nec2c.windows-x64-mingw-ucrt64-unmodified-build.v1",
        )
        self.assertEqual(
            self.manifest["outcome"],
            "UNMODIFIED MSYS2 UCRT64 WINDOWS X64 BUILD ATTEMPT "
            "BLOCKED BY SYS/TIMES.H DEPENDENCY",
        )

        attempt = self.manifest["build"]["attempt"]
        self.assertEqual(
            attempt["build_id"],
            "canonical-ucrt64-v4-20260730",
        )
        self.assertEqual(attempt["driver_exit_code"], 10)
        self.assertEqual(attempt["outcome"], "unmodified_source_build_failed")
        self.assertEqual(attempt["failing_stage"], "compile")
        self.assertEqual(attempt["record_sha256"], EXPECTED_ATTEMPT_RECORD_SHA256)
        self.assertEqual(attempt["duration_milliseconds"], 37_278)

        autotools = self.manifest["build"]["autotools"]
        self.assertEqual(autotools["configure"]["exit_code"], 0)
        self.assertEqual(autotools["configure"]["duration_milliseconds"], 35_048)
        self.assertFalse(autotools["configure"]["timed_out"])
        self.assertEqual(autotools["make"]["exit_code"], 2)
        self.assertEqual(autotools["make"]["duration_milliseconds"], 546)
        self.assertFalse(autotools["make"]["timed_out"])
        for stage in ("configure", "make"):
            for channel in ("normalized_stdout", "normalized_stderr"):
                self.assertRegex(
                    autotools[stage][channel]["sha256"],
                    SHA256_PATTERN,
                )
                self.assertGreaterEqual(autotools[stage][channel]["bytes"], 0)

        failure = self.manifest["build"]["failure"]
        self.assertEqual(failure["category"], "compile_time_header_failure")
        self.assertTrue(failure["expected_blocker_matched"])
        self.assertEqual(
            failure["first_reached_blocker"],
            "original nec2c.h line 15 requires sys/times.h",
        )
        for validation in ("pe_inspection", "reproducibility", "smoke_tests"):
            self.assertEqual(
                self.manifest["build"][validation]["status"],
                "not_reached",
            )
        self.assertEqual(
            self.manifest["build"]["direct_gcc"]["status"],
            "not_attempted",
        )
        self.assertEqual(
            self.manifest["build"]["starting_main_sha"],
            EXPECTED_STARTING_MAIN,
        )
        self.assertEqual(
            self.manifest["build"]["branch"],
            "agent/v005f-a2b-mingw-ucrt64-build",
        )
        inventory = self.manifest["build"]["generated_build_inventory"]
        self.assertEqual(inventory["file_count"], 17)
        self.assertEqual(inventory["total_bytes"], 98_789)
        self.assertFalse(inventory["executable_present"])
        self.assertFalse(inventory["object_file_present"])
        self.assertFalse(inventory["final_link_reached"])
        self.assertEqual(
            [record["path"] for record in inventory["files"]],
            sorted(record["path"] for record in inventory["files"]),
        )
        self.assertFalse(
            any(
                record["path"].lower().endswith((".exe", ".o", ".obj"))
                for record in inventory["files"]
            )
        )

        source = self.manifest["source"]
        self.assertEqual(source["archive_sha256"], EXPECTED_ARCHIVE_SHA256)
        self.assertEqual(source["archive_bytes"], 186_124)
        self.assertEqual(source["file_count"], 34)
        for key in (
            "preservation_before",
            "preservation_after",
            "source_authentication_before",
            "source_authentication_after",
        ):
            self.assertTrue(source[key], key)
        self.assertFalse(source["upstream_bytes_changed"])
        self.assertFalse(source["maintained_v1_3_3_imported"])
        self.assertTrue(source["source_guard_bound_in_attempt_record"])
        self.assertEqual(
            source["source_guard_sha256"],
            EXPECTED_SOURCE_GUARD_SHA256,
        )
        self.assertEqual(
            source["preservation_wrapper_sha256"],
            EXPECTED_PRESERVATION_WRAPPER_SHA256,
        )
        self.assertEqual(
            source["preservation_verifier_sha256"],
            EXPECTED_PRESERVATION_VERIFIER_SHA256,
        )
        self.assertTrue(self.manifest["build"]["driver"]["bound_in_attempt_record"])
        self.assertEqual(
            self.manifest["build"]["authentication_helpers"],
            {
                "preservation_verifier_sha256": EXPECTED_PRESERVATION_VERIFIER_SHA256,
                "preservation_wrapper_sha256": EXPECTED_PRESERVATION_WRAPPER_SHA256,
                "source_guard_sha256": EXPECTED_SOURCE_GUARD_SHA256,
            },
        )
        self.assertEqual(
            sha256_file(PRESERVATION_WRAPPER_PATH),
            EXPECTED_PRESERVATION_WRAPPER_SHA256,
        )
        self.assertEqual(
            sha256_file(PRESERVATION_VERIFIER_PATH),
            EXPECTED_PRESERVATION_VERIFIER_SHA256,
        )

        environment = self.manifest["build"]["environment"]
        self.assertEqual(
            environment["controls"]["PATH"],
            "/ucrt64/bin:/usr/bin",
        )
        self.assertEqual(
            environment["controls"]["CC"],
            "/ucrt64/bin/gcc",
        )
        self.assertEqual(
            environment["boundary"],
            {
                "arbitrary_parent_variables_inherited": False,
                "environment_policy": "explicit allowlist",
                "shell_invocation": "bash --noprofile --norc -c",
                "startup_files_executed": False,
                "windows_runtime_variables_copied": ["SystemRoot", "WINDIR"],
            },
        )
        self.assertEqual(
            environment["controls"]["HOME"],
            "<ATTEMPT_ROOT>/control/home",
        )
        self.assertEqual(
            environment["controls"]["TEMP"],
            "<ATTEMPT_ROOT>/control/tmp",
        )
        attempt_integrity = self.manifest["toolchain"]["attempt_start_integrity"]
        self.assertEqual(attempt_integrity["package_count"], 13)
        self.assertEqual(
            attempt_integrity["status"],
            "pacman-Qkk-zero-altered-files-at-attempt-start",
        )

        self.assertEqual(
            self.manifest["statements"],
            {
                "executable_or_build_product_tracked": False,
                "hf_propagation_control_modified": False,
                "numerical_qualification_claimed": False,
                "structured_output_started": False,
                "untouched_source": True,
            },
        )

    def test_manifest_contains_no_private_or_expiring_paths(self) -> None:
        for field, value in iter_string_values(self.manifest):
            lowered = value.lower()
            self.assertNotIn(r"c:\users", lowered, field)
            self.assertNotIn("c:\\\\users", lowered, field)
            self.assertNotIn("/users/", lowered, field)
            self.assertNotIn("/home/", lowered, field)
            self.assertNotIn("/c/hf-nec2c", lowered, field)
            self.assertNotIn(r"c:\hf-nec2c", lowered, field)
            self.assertNotIn("x-amz-", lowered, field)
            self.assertNotIn("signature=", lowered, field)
            self.assertNotIn("credential=", lowered, field)
            paths = re.findall(
                r"(?i)(?<![a-z])([a-z]:[\\/](?![\\/])\S+)",
                value,
            )
            for absolute_path in paths:
                normalized = absolute_path.replace("/", "\\").lower()
                self.assertTrue(
                    normalized == r"c:\msys64" or normalized.startswith("c:\\msys64\\"),
                    f"{field} contains an unapproved absolute path: {absolute_path}",
                )

    def test_driver_pins_identity_and_cannot_edit_original_source(self) -> None:
        driver = self.driver_text
        self.assertTrue(driver.startswith("# SPDX-License-Identifier: BSD-2-Clause\n"))
        self.assertEqual(
            sha256_file(DRIVER_PATH),
            EXPECTED_DRIVER_SHA256,
        )
        self.assertEqual(
            self.manifest["build"]["driver"]["sha256"],
            EXPECTED_DRIVER_SHA256,
        )
        self.assertEqual(
            sha256_file(SOURCE_GUARD_PATH),
            EXPECTED_SOURCE_GUARD_SHA256,
        )
        self.assertIn(EXPECTED_ARCHIVE_SHA256, driver)
        self.assertIn(EXPECTED_GCC_SHA256, driver)
        self.assertIn(EXPECTED_BASH_SHA256, driver)
        self.assertIn(EXPECTED_PACMAN_SHA256, driver)
        self.assertIn(EXPECTED_MSYS_RUNTIME_SHA256, driver)
        self.assertIn(
            "fb152d34cf00bf66fc57a66522806a4e64914654d8c1ab8cdd0a1d78283ec215",
            driver,
        )
        self.assertIn(EXPECTED_PRESERVATION_WRAPPER_SHA256, driver)
        self.assertIn(EXPECTED_PRESERVATION_VERIFIER_SHA256, driver)
        self.assertIn(EXPECTED_SOURCE_GUARD_SHA256, driver)
        self.assertIn("Invoke-PreservationVerifier -RepositoryRoot", driver)
        self.assertIn("Invoke-SourceGuard -Operation extract", driver)
        self.assertGreaterEqual(
            driver.count("Invoke-SourceGuard -Operation verify"),
            2,
        )
        self.assertIn("'$sourceMsys/configure'", driver)
        self.assertIn("cd '$buildMsys'; /usr/bin/make -j1 V=1", driver)
        self.assertIn("export CC=/ucrt64/bin/gcc", driver)
        self.assertIn("export PATH=/ucrt64/bin:/usr/bin", driver)
        self.assertIn(
            "/usr/bin/pacman -Qkk bash pacman msys2-runtime ",
            driver,
        )
        self.assertEqual(driver.count("'--noprofile'"), 3)
        self.assertEqual(driver.count("'--norc'"), 3)
        self.assertEqual(driver.count("-ClearEnvironment $true"), 3)
        self.assertNotIn("'-lc'", driver)
        self.assertIn("$startInfo.EnvironmentVariables.Clear()", driver)
        for selector in (
            "COMPILER_PATH",
            "CPATH",
            "CPLUS_INCLUDE_PATH",
            "C_INCLUDE_PATH",
            "GCC_EXEC_PREFIX",
            "LIBRARY_PATH",
        ):
            self.assertIn(selector, driver)
        self.assertIn("autotools_make_failure", driver)
        self.assertIn("sha256 = $driverSha256", driver)
        self.assertIn("source_guard_sha256 = $sourceGuardSha256", driver)
        self.assertIn(
            "preservation_wrapper_sha256 = $preservationWrapperSha256",
            driver,
        )
        self.assertIn(
            "preservation_verifier_sha256 = $preservationVerifierSha256",
            driver,
        )
        self.assertIn("$sourceContainer = Join-Path $attemptRoot 'source'", driver)
        self.assertIn(
            "$buildRoot = Join-Path $attemptRoot 'build\\autotools'",
            driver,
        )
        self.assertIn("status = 'not_attempted'", driver)
        for forbidden in (
            "autogen.sh",
            "nec2c-1.3.3",
            "Copy-Item",
            "Set-Content",
            "Add-Content",
            "Out-File",
        ):
            self.assertNotIn(forbidden, driver)

    def test_report_matches_the_canonical_attempt(self) -> None:
        attempt = self.manifest["build"]["attempt"]
        autotools = self.manifest["build"]["autotools"]
        driver = self.manifest["build"]["driver"]
        helpers = self.manifest["build"]["authentication_helpers"]
        normalized_report = " ".join(self.report_text.split())

        for expected in (
            attempt["build_id"],
            f"{attempt['duration_milliseconds']:,} ms",
            f"{autotools['configure']['duration_milliseconds']:,} ms",
            f"{autotools['make']['duration_milliseconds']:,} ms",
            attempt["record_sha256"],
            driver["sha256"],
            helpers["source_guard_sha256"],
            helpers["preservation_wrapper_sha256"],
            helpers["preservation_verifier_sha256"],
            "bash --noprofile --norc -c",
            "No arbitrary parent environment variable was inherited.",
            "zero altered files for 13",
        ):
            self.assertIn(expected, normalized_report)

        for stale in (
            "canonical-ucrt64-v2-20260730",
            "ten build-critical",
            "those ten packages",
            "launch a login shell",
            "After the installed MSYS2 `/etc/profile` ran",
        ):
            self.assertNotIn(stale, normalized_report)

    def test_project_documentation_links_resolve(self) -> None:
        self.assertTrue(BUILD_README_PATH.is_file())
        self.assertTrue(REPORT_PATH.is_file())
        documents = sorted(
            {
                *REPOSITORY_ROOT.glob("*.md"),
                *(REPOSITORY_ROOT / "docs").glob("*.md"),
                *(REPOSITORY_ROOT / "build-support").glob("**/*.md"),
                *(REPOSITORY_ROOT / "LICENSES").glob("*.md"),
            }
        )
        self.assertIn(BUILD_README_PATH, documents)
        self.assertIn(REPORT_PATH, documents)
        for document in documents:
            targets = local_markdown_targets(document)
            for target in targets:
                resolved = (document.parent / target).resolve()
                self.assertTrue(
                    resolved.is_file(),
                    f"{document.relative_to(REPOSITORY_ROOT)} links to "
                    f"missing file {target}",
                )

        report_targets = set(local_markdown_targets(REPORT_PATH))
        self.assertTrue(
            {
                "../manifests/windows-x64-mingw-ucrt64-unmodified-build-v1.json",
                "../build-support/windows-x64-mingw-ucrt64/build.ps1",
                "../build-support/windows-x64-mingw-ucrt64/README.md",
                "WINDOWS_X64_UNMODIFIED_BUILD.md",
                "../verify-preservation.ps1",
                "../tools/verify_preservation.py",
                "../build-support/windows-x64/source_guard.py",
                "../tests/smoke/minimal-dipole.nec",
            }.issubset(report_targets)
        )

    def test_preserved_sources_pass_and_no_build_products_are_candidates(
        self,
    ) -> None:
        verifier = REPOSITORY_ROOT / "tools" / "verify_preservation.py"
        completed = subprocess.run(
            [
                sys.executable,
                "-I",
                str(verifier),
                "--repository-root",
                str(REPOSITORY_ROOT),
            ],
            cwd=REPOSITORY_ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn(
            "PASS: NEC2C 1.3.1 preservation verified",
            completed.stdout,
        )
        self.assertIn("Extracted regular files: 34", completed.stdout)

        listed = subprocess.run(
            [
                "git",
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "-z",
            ],
            cwd=REPOSITORY_ROOT,
            check=False,
            capture_output=True,
        )
        self.assertEqual(
            listed.returncode,
            0,
            listed.stderr.decode("utf-8", errors="replace"),
        )
        candidates = {
            entry.decode("utf-8", errors="strict").replace("\\", "/")
            for entry in listed.stdout.split(b"\0")
            if entry
        }
        self.assertNotIn("", candidates)
        for path_text in candidates:
            self.assertFalse(
                path_text.startswith(
                    (".build-output/", ".build-temp/", ".intake-temp/")
                ),
                f"ignored generated path is a version-control candidate: {path_text}",
            )
            if path_text == "archive/nec2c-1.3.1.tar.bz2":
                continue
            self.assertNotIn(
                Path(path_text).suffix.lower(),
                FORBIDDEN_BUILD_SUFFIXES,
                f"build product is a version-control candidate: {path_text}",
            )


if __name__ == "__main__":
    unittest.main()
