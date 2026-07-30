# SPDX-License-Identifier: BSD-2-Clause
"""Authenticate, extract, and reverify preserved NEC2C 1.3.1 source bytes."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import stat
import sys
import tarfile
from pathlib import Path, PurePosixPath

ARCHIVE_RELATIVE = Path("archive/nec2c-1.3.1.tar.bz2")
FILE_MANIFEST_RELATIVE = Path("manifests/nec2c-1.3.1-files.sha256")
EXPECTED_ARCHIVE_SHA256 = (
    "8c706008bcb11c34bf33a3f8f78711c79f7bb49de8a22d74df6b10e1203c013e"
)
EXPECTED_ARCHIVE_BYTES = 186_124
EXPECTED_FILE_COUNT = 34
ARCHIVE_TOP_LEVEL = "nec2c-1.3.1"
MANIFEST_PREFIX = "upstream/"
REPARSE_POINT_ATTRIBUTE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


class SourceGuardError(Exception):
    """The archive, manifest, requested path, or extracted tree is unsafe."""


def validate_archive_path(
    value: str, *, label: str, expected_component_count: int
) -> PurePosixPath:
    raw_components = value.split("/")
    pure_path = PurePosixPath(value)
    if (
        not value
        or pure_path.is_absolute()
        or any(component in {"", ".", ".."} for component in raw_components)
        or tuple(pure_path.parts) != tuple(raw_components)
        or "\\" in value
        or ":" in value
        or raw_components[0] != ARCHIVE_TOP_LEVEL
        or len(raw_components) != expected_component_count
    ):
        raise SourceGuardError(f"{label} path is unsafe")
    return pure_path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            before = os.fstat(stream.fileno())
            if (
                not stat.S_ISREG(before.st_mode)
                or is_reparse(before)
                or before.st_nlink != 1
            ):
                raise SourceGuardError(
                    "hashed path is linked, reparsed, or not a regular file"
                )
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
            after = os.fstat(stream.fileno())
        path_after = path.stat(follow_symlinks=False)
    except OSError as error:
        raise SourceGuardError("hashed file cannot be read stably") from error
    identity_before = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_nlink,
    )
    identity_after = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_nlink,
    )
    if identity_before != identity_after:
        raise SourceGuardError("hashed file identity changed while reading")
    if (
        not stat.S_ISREG(path_after.st_mode)
        or is_reparse(path_after)
        or path_after.st_nlink != 1
        or (path_after.st_dev, path_after.st_ino) != (after.st_dev, after.st_ino)
    ):
        raise SourceGuardError("hashed path identity changed after reading")
    return digest.hexdigest()


def is_reparse(result: os.stat_result) -> bool:
    return bool(getattr(result, "st_file_attributes", 0) & REPARSE_POINT_ATTRIBUTE)


def require_plain_directory(path: Path, label: str) -> Path:
    try:
        result = path.lstat()
    except OSError as error:
        raise SourceGuardError(f"{label} is unavailable") from error
    if stat.S_ISLNK(result.st_mode) or is_reparse(result):
        raise SourceGuardError(f"{label} is a link or reparse point")
    if not stat.S_ISDIR(result.st_mode):
        raise SourceGuardError(f"{label} is not a directory")
    try:
        return path.resolve(strict=True)
    except OSError as error:
        raise SourceGuardError(f"{label} cannot be resolved") from error


def require_regular_file(path: Path, label: str) -> os.stat_result:
    try:
        result = path.lstat()
    except OSError as error:
        raise SourceGuardError(f"{label} is unavailable") from error
    if stat.S_ISLNK(result.st_mode) or is_reparse(result):
        raise SourceGuardError(f"{label} is a link or reparse point")
    if not stat.S_ISREG(result.st_mode):
        raise SourceGuardError(f"{label} is not a regular file")
    if result.st_nlink != 1:
        raise SourceGuardError(f"{label} has more than one hard-link name")
    return result


def require_below(path: Path, parent: Path, label: str) -> Path:
    try:
        resolved_parent = parent.resolve(strict=True)
        resolved_path = path.resolve(strict=False)
        resolved_path.relative_to(resolved_parent)
    except (OSError, ValueError) as error:
        raise SourceGuardError(f"{label} must remain below .build-temp") from error
    if resolved_path == resolved_parent:
        raise SourceGuardError(f"{label} cannot be .build-temp itself")
    return resolved_path


def parse_file_manifest(repository_root: Path) -> dict[str, str]:
    path = repository_root / FILE_MANIFEST_RELATIVE
    require_regular_file(path, "source-file manifest")
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise SourceGuardError("source-file manifest cannot be read") from error
    if raw.startswith(b"\xef\xbb\xbf"):
        raise SourceGuardError("source-file manifest contains a UTF-8 BOM")
    normalized = raw.replace(b"\r\n", b"\n")
    if b"\r" in normalized or not normalized.endswith(b"\n"):
        raise SourceGuardError("source-file manifest line endings are invalid")
    try:
        lines = normalized[:-1].decode("utf-8").split("\n")
    except UnicodeDecodeError as error:
        raise SourceGuardError("source-file manifest is not UTF-8") from error

    records: dict[str, str] = {}
    casefolded: set[str] = set()
    for line in lines:
        digest, separator, repository_relative = line.partition("  ")
        if (
            separator != "  "
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
            or not repository_relative.startswith(MANIFEST_PREFIX)
        ):
            raise SourceGuardError("source-file manifest record is malformed")
        archive_relative = repository_relative.removeprefix(MANIFEST_PREFIX)
        validate_archive_path(
            archive_relative,
            label="source-file manifest",
            expected_component_count=2,
        )
        if archive_relative in records or archive_relative.casefold() in casefolded:
            raise SourceGuardError("source-file manifest path is duplicated")
        records[archive_relative] = digest
        casefolded.add(archive_relative.casefold())

    if len(records) != EXPECTED_FILE_COUNT:
        raise SourceGuardError(
            f"source-file manifest has {len(records)} records; expected {EXPECTED_FILE_COUNT}"
        )
    if list(records) != sorted(records):
        raise SourceGuardError("source-file manifest is not in ordinal path order")
    return records


def authenticate_archive(repository_root: Path) -> Path:
    archive_path = repository_root / ARCHIVE_RELATIVE
    result = require_regular_file(archive_path, "preserved archive")
    if result.st_size != EXPECTED_ARCHIVE_BYTES:
        raise SourceGuardError(
            f"preserved archive has {result.st_size} bytes; expected {EXPECTED_ARCHIVE_BYTES}"
        )
    observed = sha256_file(archive_path)
    if observed != EXPECTED_ARCHIVE_SHA256:
        raise SourceGuardError(
            f"preserved archive SHA-256 is {observed}; expected {EXPECTED_ARCHIVE_SHA256}"
        )
    return archive_path


def validate_archive_members(
    archive: tarfile.TarFile, manifest: dict[str, str]
) -> dict[str, tarfile.TarInfo]:
    members = archive.getmembers()
    regular_members: dict[str, tarfile.TarInfo] = {}
    directory_names: list[str] = []
    casefolded: set[str] = set()

    for member in members:
        name = member.name.removesuffix("/") if member.isdir() else member.name
        validate_archive_path(
            name,
            label="archive member",
            expected_component_count=1 if member.isdir() else 2,
        )
        folded = name.casefold()
        if folded in casefolded:
            raise SourceGuardError(
                "archive contains a duplicate or case-colliding member"
            )
        casefolded.add(folded)

        if member.isdir():
            directory_names.append(name)
        elif member.isreg():
            regular_members[name] = member
        else:
            raise SourceGuardError("archive contains a link or special member")

    if directory_names != [ARCHIVE_TOP_LEVEL]:
        raise SourceGuardError(
            "archive directory inventory is not the preserved layout"
        )
    if set(regular_members) != set(manifest):
        missing = sorted(set(manifest) - set(regular_members))
        extra = sorted(set(regular_members) - set(manifest))
        raise SourceGuardError(
            f"archive member inventory mismatch; missing={missing}; extra={extra}"
        )
    return regular_members


def inventory_tree(source_root: Path) -> tuple[dict[str, Path], list[str]]:
    files: dict[str, Path] = {}
    directories: list[str] = []

    def visit(directory: Path) -> None:
        try:
            with os.scandir(directory) as iterator:
                entries = sorted(iterator, key=lambda entry: entry.name)
        except OSError as error:
            raise SourceGuardError("extracted tree cannot be enumerated") from error
        for entry in entries:
            path = Path(entry.path)
            try:
                # Some Windows CPython builds report st_nlink=0 from cached
                # DirEntry.stat(); a direct path stat returns the stable value.
                result = path.stat(follow_symlinks=False)
            except OSError as error:
                raise SourceGuardError("extracted entry cannot be inspected") from error
            relative = path.relative_to(source_root).as_posix()
            if entry.is_symlink() or is_reparse(result):
                raise SourceGuardError(
                    "extracted tree contains a link or reparse point"
                )
            if stat.S_ISDIR(result.st_mode):
                directories.append(relative)
                visit(path)
            elif stat.S_ISREG(result.st_mode):
                if result.st_nlink != 1:
                    raise SourceGuardError(
                        "extracted tree contains a multiply linked file"
                    )
                files[relative] = path
            else:
                raise SourceGuardError("extracted tree contains a special object")

    visit(source_root)
    return files, directories


def verify_extracted_tree(source_root: Path, manifest: dict[str, str]) -> None:
    resolved_source = require_plain_directory(source_root, "extracted source root")
    files, directories = inventory_tree(resolved_source)
    if directories != [ARCHIVE_TOP_LEVEL]:
        raise SourceGuardError(
            f"extracted directory inventory differs: {directories!r}"
        )
    if set(files) != set(manifest):
        missing = sorted(set(manifest) - set(files))
        extra = sorted(set(files) - set(manifest))
        raise SourceGuardError(
            f"extracted file inventory mismatch; missing={missing}; extra={extra}"
        )
    for relative, expected_digest in manifest.items():
        observed = sha256_file(files[relative])
        if observed != expected_digest:
            raise SourceGuardError(
                f"extracted file SHA-256 mismatch: {relative}: {observed}"
            )


def extract_authenticated_source(repository_root: Path, destination: Path) -> None:
    manifest = parse_file_manifest(repository_root)
    archive_path = authenticate_archive(repository_root)
    build_temp = require_plain_directory(repository_root / ".build-temp", ".build-temp")
    resolved_destination = require_below(destination, build_temp, "destination")
    if resolved_destination.exists():
        raise SourceGuardError("destination already exists; a fresh path is required")
    try:
        resolved_destination.mkdir()
    except OSError as error:
        raise SourceGuardError("destination cannot be created") from error

    try:
        with tarfile.open(archive_path, mode="r:bz2") as archive:
            members = validate_archive_members(archive, manifest)
            top_level = resolved_destination / ARCHIVE_TOP_LEVEL
            top_level.mkdir()
            for relative in sorted(members):
                member = members[relative]
                target = resolved_destination.joinpath(*PurePosixPath(relative).parts)
                if target.parent != top_level:
                    raise SourceGuardError(
                        "archive contains an unexpected nested directory"
                    )
                extracted = archive.extractfile(member)
                if extracted is None:
                    raise SourceGuardError("archive regular member cannot be read")
                with extracted, target.open("xb") as output:
                    shutil.copyfileobj(extracted, output, length=1024 * 1024)
                if target.stat().st_size != member.size:
                    raise SourceGuardError(
                        "archive member size changed during extraction"
                    )
                os.utime(target, (member.mtime, member.mtime))
    except (OSError, tarfile.TarError) as error:
        raise SourceGuardError("authenticated archive extraction failed") from error

    verify_extracted_tree(resolved_destination, manifest)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Guard fresh NEC2C 1.3.1 build-source extractions."
    )
    parser.add_argument("operation", choices=("extract", "verify"))
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    try:
        repository_root = require_plain_directory(
            arguments.repository_root, "repository root"
        )
        build_temp = require_plain_directory(
            repository_root / ".build-temp", ".build-temp"
        )
        source_root = require_below(arguments.source_root, build_temp, "source root")
        if arguments.operation == "extract":
            extract_authenticated_source(repository_root, source_root)
        else:
            manifest = parse_file_manifest(repository_root)
            verify_extracted_tree(source_root, manifest)
    except SourceGuardError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1

    print(
        f"PASS: {arguments.operation} authenticated {EXPECTED_FILE_COUNT} original regular files"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
