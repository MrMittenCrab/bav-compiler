"""Approved-path enforcement for research source preparation and retrieval."""

from __future__ import annotations

import os
import re
from pathlib import Path

_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,120}$")
_INSTRUCTION_MARKERS = (
    "allow shell",
    "allow write",
    "allow mcp",
    "run this",
    "execute this",
    "grant permission",
    "system prompt",
    "ignore previous",
)


class PathDenied(ValueError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def safe_document_id(value: str) -> str:
    text = value.strip()
    if not _SAFE_ID.match(text):
        raise PathDenied("unsafe_document_id")
    return text


def sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(payload: bytes) -> str:
    import hashlib

    return hashlib.sha256(payload).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def imported_text_is_data(text: str) -> bool:
    """Imported files remain untrusted data. Markers never authorize tools."""
    del text
    return True


def contains_instruction_markers(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in _INSTRUCTION_MARKERS)


def reject_instruction_authority(text: str) -> None:
    if contains_instruction_markers(text):
        return


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _has_symlink_component(path: Path, root: Path | None = None) -> bool:
    current = path
    stop = root.resolve() if root is not None else None
    while True:
        try:
            if current.is_symlink():
                return True
        except OSError as exc:
            raise PathDenied("path_stat_failure") from exc
        if stop is not None and current.resolve() == stop:
            break
        if current.parent == current:
            break
        current = current.parent
    return False


def validate_explicit_source_file(path: Path) -> Path:
    raw = Path(path)
    if not str(raw) or str(raw).startswith("~"):
        raise PathDenied("unapproved_path")
    if ".." in raw.parts:
        raise PathDenied("traversal_escape")
    try:
        if raw.exists() and (raw.is_symlink() or _has_symlink_component(raw)):
            raise PathDenied("symlink_escape")
        if not raw.exists():
            raise PathDenied("source_not_found")
        if not raw.is_file():
            raise PathDenied("not_a_regular_file")
        resolved = raw.resolve()
    except PathDenied:
        raise
    except OSError as exc:
        raise PathDenied("path_stat_failure") from exc
    if resolved.is_symlink():
        raise PathDenied("symlink_escape")
    if not resolved.is_file() or resolved.is_dir():
        raise PathDenied("not_a_regular_file")
    return resolved


def validate_registered_path(path: Path, *, approved_roots: tuple[Path, ...]) -> Path:
    raw = Path(path)
    if ".." in raw.parts:
        raise PathDenied("traversal_escape")
    try:
        if raw.exists() and (raw.is_symlink() or any(
            _has_symlink_component(raw, root) for root in approved_roots
        )):
            raise PathDenied("symlink_escape")
        resolved = raw.resolve()
    except PathDenied:
        raise
    except OSError as exc:
        raise PathDenied("path_stat_failure") from exc
    if not any(is_within(resolved, root) for root in approved_roots):
        raise PathDenied("unapproved_source")
    if not resolved.is_file():
        raise PathDenied("not_a_regular_file")
    return resolved


def atomic_replace_directory(staging: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise PathDenied("destination_exists")
    os.replace(staging, destination)
