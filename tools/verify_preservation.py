# SPDX-License-Identifier: BSD-2-Clause
"""Offline verification for the preserved original NEC2C 1.3.1 distribution."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys


EXPECTED_ARCHIVE_SHA256 = (
    "8c706008bcb11c34bf33a3f8f78711c79f7bb49de8a22d74df6b10e1203c013e"
)
EXPECTED_ARCHIVE_SIZE = 186_124
EXPECTED_FILE_COUNT = 34
ARCHIVE_RELATIVE_PATH = "archive/nec2c-1.3.1.tar.bz2"
ARCHIVE_MANIFEST_RELATIVE_PATH = "manifests/nec2c-1.3.1-archive.sha256"
FILE_MANIFEST_RELATIVE_PATH = "manifests/nec2c-1.3.1-files.sha256"
UPSTREAM_RELATIVE_PATH = "upstream/nec2c-1.3.1"
REPARSE_POINT_ATTRIBUTE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class VerificationMismatch(Exception):
    """The preserved bytes or inventory differ from the committed manifest."""


class VerificationEnvironmentError(Exception):
    """The verifier cannot safely interpret the requested checkout."""


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_reparse(stat_result: os.stat_result) -> bool:
    return bool(getattr(stat_result, "st_file_attributes", 0) & REPARSE_POINT_ATTRIBUTE)


def require_root(path: Path) -> Path:
    try:
        initial_stat = path.lstat()
    except OSError as error:
        raise VerificationEnvironmentError(
            f"repository root is unavailable: {path}"
        ) from error
    if stat.S_ISLNK(initial_stat.st_mode) or is_reparse(initial_stat):
        raise VerificationEnvironmentError(
            f"repository root must not be a link or reparse point: {path}"
        )
    if not stat.S_ISDIR(initial_stat.st_mode):
        raise VerificationEnvironmentError(
            f"repository root is not a directory: {path}"
        )
    try:
        return path.resolve(strict=True)
    except OSError as error:
        raise VerificationEnvironmentError(
            f"repository root cannot be resolved safely: {path}"
        ) from error


def repository_path(root: Path, relative: str) -> Path:
    parts = relative.split("/")
    if (
        not parts
        or any(part in {"", ".", ".."} for part in parts)
        or "\\" in relative
        or PurePosixPath(relative).is_absolute()
    ):
        raise VerificationEnvironmentError(
            f"unsafe built-in repository-relative path: {relative!r}"
        )
    candidate = root.joinpath(*parts)
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise VerificationEnvironmentError(
            f"path leaves repository root: {relative!r}"
        ) from error
    return candidate


def require_regular_file(path: Path, label: str) -> os.stat_result:
    try:
        result = path.lstat()
    except FileNotFoundError as error:
        raise VerificationMismatch(f"missing {label}: {path}") from error
    except OSError as error:
        raise VerificationEnvironmentError(f"cannot inspect {label}: {path}") from error
    if stat.S_ISLNK(result.st_mode) or is_reparse(result):
        raise VerificationMismatch(f"{label} is a link or reparse point: {path}")
    if not stat.S_ISREG(result.st_mode):
        raise VerificationMismatch(f"{label} is not a regular file: {path}")
    return result


def read_manifest(path: Path, label: str) -> list[str]:
    require_regular_file(path, label)
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise VerificationEnvironmentError(f"cannot read {label}: {path}") from error
    if raw.startswith(b"\xef\xbb\xbf"):
        raise VerificationEnvironmentError(f"{label} must not contain a UTF-8 BOM")
    normalized = raw.replace(b"\r\n", b"\n")
    if b"\r" in normalized:
        raise VerificationEnvironmentError(f"{label} contains a bare carriage return")
    try:
        text = normalized.decode("utf-8")
    except UnicodeDecodeError as error:
        raise VerificationEnvironmentError(f"{label} is not valid UTF-8") from error
    if any(separator in text for separator in ("\u0085", "\u2028", "\u2029")):
        raise VerificationEnvironmentError(
            f"{label} contains a noncanonical Unicode line separator"
        )
    if not text.endswith("\n"):
        raise VerificationEnvironmentError(
            f"{label} must end with an LF or CRLF line ending"
        )
    return text[:-1].split("\n")


def parse_archive_manifest(path: Path) -> tuple[str, int, str]:
    lines = read_manifest(path, "archive manifest")
    if len(lines) != 3 or lines[0] != "# hf-nec2c archive SHA-256 manifest v1":
        raise VerificationEnvironmentError("archive manifest does not match schema v1")
    byte_count_match = re.fullmatch(r"# byte-count: (0|[1-9][0-9]*)", lines[1])
    if byte_count_match is None:
        raise VerificationEnvironmentError(
            "archive manifest byte-count line is malformed"
        )
    digest, separator, relative = lines[2].partition("  ")
    if (
        separator != "  "
        or not SHA256_PATTERN.fullmatch(digest)
        or not relative
        or "\\" in relative
        or ":" in relative
        or PurePosixPath(relative).is_absolute()
        or any(part in {"", ".", ".."} for part in relative.split("/"))
        or any(ord(character) < 32 or ord(character) == 127 for character in relative)
    ):
        raise VerificationEnvironmentError("archive manifest digest line is malformed")
    return digest, int(byte_count_match.group(1)), relative


def validate_manifest_path(relative: str) -> None:
    if (
        "\\" in relative
        or ":" in relative
        or any(ord(character) < 32 or ord(character) == 127 for character in relative)
    ):
        raise VerificationEnvironmentError(
            f"file manifest contains unsafe path: {relative!r}"
        )
    parts = relative.split("/")
    if (
        any(part in {"", ".", ".."} for part in parts)
        or PurePosixPath(relative).is_absolute()
        or not relative.startswith(f"{UPSTREAM_RELATIVE_PATH}/")
    ):
        raise VerificationEnvironmentError(
            f"file manifest contains invalid path: {relative!r}"
        )


def parse_file_manifest(path: Path) -> dict[str, str]:
    lines = read_manifest(path, "extracted-file manifest")
    if not lines:
        raise VerificationEnvironmentError("extracted-file manifest is empty")
    records: dict[str, str] = {}
    casefolded_paths: set[str] = set()
    for line_number, line in enumerate(lines, start=1):
        digest, separator, relative = line.partition("  ")
        if separator != "  " or not SHA256_PATTERN.fullmatch(digest):
            raise VerificationEnvironmentError(
                f"malformed extracted-file manifest line {line_number}"
            )
        validate_manifest_path(relative)
        if relative in records:
            raise VerificationEnvironmentError(
                f"duplicate extracted-file manifest path: {relative}"
            )
        folded = relative.casefold()
        if folded in casefolded_paths:
            raise VerificationEnvironmentError(
                f"case-colliding extracted-file manifest path: {relative}"
            )
        casefolded_paths.add(folded)
        records[relative] = digest
    if len(records) != EXPECTED_FILE_COUNT:
        raise VerificationEnvironmentError(
            f"extracted-file manifest has {len(records)} records; "
            f"expected {EXPECTED_FILE_COUNT}"
        )
    if list(records) != sorted(records):
        raise VerificationEnvironmentError(
            "extracted-file manifest paths are not in ordinal order"
        )
    return records


def require_directory(path: Path, label: str) -> None:
    try:
        result = path.lstat()
    except FileNotFoundError as error:
        raise VerificationMismatch(f"missing {label}: {path}") from error
    except OSError as error:
        raise VerificationEnvironmentError(f"cannot inspect {label}: {path}") from error
    if stat.S_ISLNK(result.st_mode) or is_reparse(result):
        raise VerificationMismatch(f"{label} is a link or reparse point: {path}")
    if not stat.S_ISDIR(result.st_mode):
        raise VerificationMismatch(f"{label} is not a directory: {path}")


def inventory_upstream(
    root: Path, upstream_root: Path
) -> tuple[dict[str, Path], list[str]]:
    require_directory(upstream_root, "upstream tree")
    files: dict[str, Path] = {}
    unexpected_directories: list[str] = []

    def visit(directory: Path) -> None:
        try:
            with os.scandir(directory) as iterator:
                entries = sorted(iterator, key=lambda entry: entry.name)
        except OSError as error:
            raise VerificationEnvironmentError(
                f"cannot enumerate upstream directory: {directory}"
            ) from error
        for entry in entries:
            entry_path = Path(entry.path)
            try:
                result = entry.stat(follow_symlinks=False)
            except OSError as error:
                raise VerificationEnvironmentError(
                    f"cannot inspect upstream entry: {entry_path}"
                ) from error
            relative = entry_path.relative_to(root).as_posix()
            if entry.is_symlink() or is_reparse(result):
                raise VerificationMismatch(
                    f"unsupported link or reparse point in upstream tree: {relative}"
                )
            if stat.S_ISDIR(result.st_mode):
                unexpected_directories.append(relative)
                visit(entry_path)
            elif stat.S_ISREG(result.st_mode):
                files[relative] = entry_path
            else:
                raise VerificationMismatch(
                    f"unsupported filesystem object in upstream tree: {relative}"
                )

    visit(upstream_root)
    return files, unexpected_directories


def verify(repository_root: Path) -> list[str]:
    archive_manifest_path = repository_path(
        repository_root, ARCHIVE_MANIFEST_RELATIVE_PATH
    )
    file_manifest_path = repository_path(repository_root, FILE_MANIFEST_RELATIVE_PATH)
    archive_manifest_hash, archive_manifest_size, archive_relative = (
        parse_archive_manifest(archive_manifest_path)
    )
    file_manifest = parse_file_manifest(file_manifest_path)

    archive_path = repository_path(repository_root, ARCHIVE_RELATIVE_PATH)
    archive_stat = require_regular_file(archive_path, "preserved archive")
    upstream_root = repository_path(repository_root, UPSTREAM_RELATIVE_PATH)
    actual_files, unexpected_directories = inventory_upstream(
        repository_root, upstream_root
    )

    mismatches: list[str] = []
    if archive_manifest_hash != EXPECTED_ARCHIVE_SHA256:
        mismatches.append(
            "archive manifest SHA-256 differs from the fixed expected value"
        )
    if archive_manifest_size != EXPECTED_ARCHIVE_SIZE:
        mismatches.append(
            "archive manifest byte count differs from the fixed expected value"
        )
    if archive_relative != ARCHIVE_RELATIVE_PATH:
        mismatches.append(
            f"archive manifest path: expected {ARCHIVE_RELATIVE_PATH}, "
            f"observed {archive_relative}"
        )
    if archive_stat.st_size != EXPECTED_ARCHIVE_SIZE:
        mismatches.append(
            f"archive byte count: expected {EXPECTED_ARCHIVE_SIZE}, "
            f"observed {archive_stat.st_size}"
        )
    observed_archive_hash = hash_file(archive_path)
    if observed_archive_hash != EXPECTED_ARCHIVE_SHA256:
        mismatches.append(
            f"archive SHA-256: expected {EXPECTED_ARCHIVE_SHA256}, "
            f"observed {observed_archive_hash}"
        )

    expected_paths = set(file_manifest)
    actual_paths = set(actual_files)
    for relative in sorted(expected_paths - actual_paths):
        mismatches.append(f"missing upstream file: {relative}")
    for relative in sorted(actual_paths - expected_paths):
        mismatches.append(f"extra upstream file: {relative}")
    for relative in sorted(unexpected_directories):
        mismatches.append(f"extra upstream directory: {relative}")

    total_bytes = 0
    for relative in sorted(expected_paths & actual_paths):
        path = actual_files[relative]
        try:
            total_bytes += path.stat(follow_symlinks=False).st_size
            observed = hash_file(path)
        except OSError as error:
            raise VerificationEnvironmentError(
                f"cannot read upstream file: {relative}"
            ) from error
        expected = file_manifest[relative]
        if observed != expected:
            mismatches.append(
                f"upstream SHA-256 mismatch: {relative}: "
                f"expected {expected}, observed {observed}"
            )

    if mismatches:
        raise VerificationMismatch("\n".join(mismatches))

    return [
        "PASS: NEC2C 1.3.1 preservation verified",
        f"Archive SHA-256: {observed_archive_hash}",
        f"Archive bytes: {archive_stat.st_size}",
        f"Extracted regular files: {len(actual_files)}",
        f"Extracted regular-file bytes: {total_bytes}",
    ]


def parse_arguments() -> argparse.Namespace:
    default_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description=(
            "Verify the preserved NEC2C 1.3.1 archive and extracted raw file bytes."
        )
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=default_root,
        help="checkout to verify (defaults to the checkout containing this script)",
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    try:
        root = require_root(arguments.repository_root)
        lines = verify(root)
    except VerificationMismatch as error:
        print("FAIL: NEC2C 1.3.1 preservation mismatch", file=sys.stderr)
        print(error, file=sys.stderr)
        return 1
    except VerificationEnvironmentError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"ERROR: unexpected filesystem failure: {error}", file=sys.stderr)
        return 2

    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
