# SPDX-License-Identifier: BSD-2-Clause
"""Freeze and reconstruct the maintained NEC2C source v2 identity."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "nec2c"
UPSTREAM = ROOT / "upstream" / "nec2c-1.3.1"
MANIFEST = ROOT / "manifests" / "maintained-source-v2.json"
ARCHIVE = ROOT / "archive" / "nec2c-1.3.1.tar.bz2"
ORIGINAL_FILES = ROOT / "manifests" / "nec2c-1.3.1-files.sha256"
PATCH = ROOT / "patches" / "maintained" / "nec2c-1.3.1-hf-portability-zint-v2.patch"
V1_TAG = "maintained/nec2c-1.3.1-hf-portability-v1"
V1_TAG_OBJECT = "1ca11974e247407b41f47d0a9d2a6288d172dd86"
V1_TAG_TARGET = "05f9a4f7ad9a089e45459db9099e47e0bf4533c2"
V1_FILES = {
    "manifests/maintained-source-v1.json": (
        5121,
        "627bc5a6fe9b5214d6ce6d49fca29d0c8a5f7fd1e4bd727587a29b390084ea07",
    ),
    "patches/maintained/nec2c-1.3.1-hf-portability-v1.patch": (
        6152,
        "cfb8da8689ec85817d12c2f95c51c599117c1b5e140f589a0a05bd82c9899e5b",
    ),
    "docs/MAINTAINED_SOURCE_V1.md": (
        5822,
        "bd0feb95ac87eb697e6974e0cba1c5ffee674ba478819b1626f9e3f39e0e651a",
    ),
}
V2_MANIFEST_BYTES = 7809
V2_MANIFEST_RAW_SHA256 = (
    "6d3899ede74d77832732b196e5e64636578c03e667d5e6feb43270ab8e39f37a"
)
V2_MANIFEST_CANONICAL_SHA256 = (
    "e1352c200efa0cd8c3475e1645ae9ad9b95843fc99fe2476e13f27b3a7c9c7c4"
)
V2_PATCH_IDENTITY = (
    7624,
    "9b165d93e4e3335f4c2762c70950a7086d1f6c7ee0559a1f3f3f5c08f6219e52",
)
ORIGINAL_ARCHIVE_IDENTITY = (
    186124,
    "8c706008bcb11c34bf33a3f8f78711c79f7bb49de8a22d74df6b10e1203c013e",
)


def _identity(path: Path) -> tuple[int, str]:
    data = path.read_bytes()
    return len(data), hashlib.sha256(data).hexdigest()


def _inventory(root: Path) -> dict[str, tuple[int, str]]:
    entries = sorted(root.iterdir(), key=lambda path: path.name)
    if any(path.is_symlink() or not path.is_file() for path in entries):
        raise AssertionError(f"non-regular source entry below {root}")
    return {path.name: _identity(path) for path in entries}


def _run(arguments: list[str], cwd: Path = ROOT) -> str:
    result = subprocess.run(
        arguments, cwd=cwd, check=False, capture_output=True, text=True
    )
    if result.returncode:
        raise AssertionError(
            f"command failed: {arguments!r}\n{result.stdout}\n{result.stderr}"
        )
    return result.stdout.strip()


def _extract_authenticated_original(destination: Path) -> None:
    if _identity(ARCHIVE) != ORIGINAL_ARCHIVE_IDENTITY:
        raise AssertionError("original archive identity differs")
    expected: dict[str, str] = {}
    for line in ORIGINAL_FILES.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        prefix = "upstream/nec2c-1.3.1/"
        if not relative.startswith(prefix):
            raise AssertionError("original manifest path is outside the source root")
        expected[relative.removeprefix(prefix)] = digest
    if len(expected) != 34:
        raise AssertionError("original manifest does not contain 34 files")

    destination.mkdir()
    with tarfile.open(ARCHIVE, mode="r:bz2") as archive:
        members = archive.getmembers()
        regular = {member.name: member for member in members if member.isfile()}
        expected_members = {f"nec2c-1.3.1/{name}" for name in expected}
        if len(members) != 35 or set(regular) != expected_members:
            raise AssertionError("original archive inventory differs")
        if any(not (member.isdir() or member.isfile()) for member in members):
            raise AssertionError("original archive contains a link or special member")
        for name, digest in expected.items():
            extracted = archive.extractfile(regular[f"nec2c-1.3.1/{name}"])
            if extracted is None:
                raise AssertionError(f"cannot read original archive member: {name}")
            data = extracted.read()
            if hashlib.sha256(data).hexdigest() != digest:
                raise AssertionError(f"original archive member differs: {name}")
            (destination / name).write_bytes(data)


class MaintainedSourceV2Tests(unittest.TestCase):
    """Require immutable v1 lineage and byte-exact v2 reconstruction."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = MANIFEST.read_bytes()
        cls.manifest = json.loads(cls.raw.decode("utf-8"))

    def test_v1_identity_is_frozen(self) -> None:
        for relative, expected in V1_FILES.items():
            self.assertEqual(_identity(ROOT / relative), expected)
        self.assertEqual(_run(["git", "rev-parse", V1_TAG]), V1_TAG_OBJECT)
        self.assertEqual(_run(["git", "rev-parse", f"{V1_TAG}^{{}}"]), V1_TAG_TARGET)
        lineage = self.manifest["v1_lineage"]
        self.assertEqual(lineage["tag"]["object"], V1_TAG_OBJECT)
        self.assertEqual(lineage["tag"]["target"], V1_TAG_TARGET)

    def test_v2_manifest_and_inventory_are_deterministic(self) -> None:
        self.assertNotIn(b"\r", self.raw)
        self.assertTrue(self.raw.endswith(b"\n"))
        self.assertEqual(
            _identity(MANIFEST), (V2_MANIFEST_BYTES, V2_MANIFEST_RAW_SHA256)
        )
        canonical = json.dumps(
            self.manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        self.assertEqual(
            hashlib.sha256(canonical).hexdigest(), V2_MANIFEST_CANONICAL_SHA256
        )
        self.assertEqual(_identity(PATCH), V2_PATCH_IDENTITY)

        actual = _inventory(SOURCE)
        declared = self.manifest["final_source"]
        self.assertEqual(len(actual), declared["regular_file_count"])
        self.assertEqual(
            sum(size for size, _ in actual.values()), declared["total_bytes"]
        )
        self.assertEqual(
            {name: digest for name, (_, digest) in actual.items()},
            declared["files_sha256"],
        )
        original = _inventory(UPSTREAM)
        changed = {name for name in original if actual[name] != original[name]}
        added = set(actual) - set(original)
        self.assertEqual(changed, {"calculations.c", "main.c", "misc.c", "nec2c.h"})
        self.assertEqual(added, {"platform_signal.h", "platform_time.h"})
        self.assertEqual(len(set(original) - changed), 30)

    def test_zint_source_has_only_the_four_authenticated_corrections(self) -> None:
        expected = (UPSTREAM / "calculations.c").read_bytes()
        replacements = (
            (b"I*9.765e4)", b"I*9.765e-4)"),
            (b"#define cn\tcc14\n", b"#define cn\t(0.70710678 + I*0.70710678)\n"),
            (
                b"\t  *zint= CPLX_01* sqrt( cmotp/sigl )* br1/ rolam;\n\n",
                b"\t  *zint= CPLX_01* sqrt( cmotp/sigl )* br1/ rolam;\n\t  return;\n\n",
            ),
            (
                b"\t*zint= CPLX_01* sqrt( cmotp/ sigl)* br1/ rolam;\n\n",
                b"\t*zint= CPLX_01* sqrt( cmotp/ sigl)* br1/ rolam;\n\treturn;\n\n",
            ),
        )
        for before, after in replacements:
            self.assertEqual(expected.count(before), 1)
            expected = expected.replace(before, after, 1)
        self.assertEqual((SOURCE / "calculations.c").read_bytes(), expected)

    def test_fresh_archive_plus_only_v2_patch_reconstructs_source(self) -> None:
        with tempfile.TemporaryDirectory(prefix="hf-nec2c-v2-replay-") as temporary:
            replay = Path(temporary) / "nec2c-1.3.1"
            _extract_authenticated_original(replay)
            _run(["git", "init"], replay)
            _run(["git", "config", "core.autocrlf", "false"], replay)
            _run(["git", "config", "core.eol", "lf"], replay)
            _run(
                ["git", "apply", "--check", "--whitespace=error-all", str(PATCH)],
                replay,
            )
            _run(["git", "apply", "--whitespace=error-all", str(PATCH)], replay)
            shutil.rmtree(replay / ".git")
            self.assertEqual(_inventory(replay), _inventory(SOURCE))


if __name__ == "__main__":
    unittest.main()
