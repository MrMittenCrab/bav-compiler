"""Durable case storage, conservative selection, locks and atomic saves."""

from __future__ import annotations

import fcntl
import json
import os
import re
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping

from bav.debater.contracts import PendingItem
from bav.director.repository import repository_root
from bav.extractor.research.paths import sha256_text

CASE_SCHEMA_VERSION = 1
_SLUG = re.compile(r"[^a-z0-9]+")


class CaseLocked(RuntimeError):
    """Another writer holds the case lock."""


class CaseSelectionError(ValueError):
    """Case reference is missing, ambiguous, or conflicting."""


@dataclass(frozen=True)
class CaseRecord:
    payload: dict[str, Any]
    path: Path

    @property
    def slug(self) -> str:
        return str(self.payload["slug"])

    @property
    def title(self) -> str:
        return str(self.payload["title"])

    @property
    def proposition(self) -> str:
        return str(self.payload["proposition"]["accepted"])

    @property
    def pending(self) -> dict[str, Any] | None:
        item = self.payload.get("pending")
        return item if isinstance(item, dict) else None

    @property
    def authority(self) -> str:
        return sha256_text(canonical_json(self.payload))


def cases_root(*, repository: Path | None = None) -> Path:
    return (repository or repository_root()) / "build" / "input" / "cases"


def default_allowance() -> dict[str, Any]:
    return {
        "active_routes": 1,
        "candidate_routes": 3,
        "research_batches": 4,
        "backend_calls": 12,
        "tool_dispatches": 20,
        "elapsed_seconds": 1200,
        "intake_operations": 0,
        "local_planning_operations": 0,
    }


def allowance_fingerprint(allowance: Mapping[str, Any]) -> str:
    tracked = {
        key: allowance.get(key)
        for key in (
            "active_routes",
            "candidate_routes",
            "research_batches",
            "backend_calls",
            "tool_dispatches",
            "elapsed_seconds",
        )
    }
    return sha256_text(canonical_json(tracked))


def canonical_json(payload: Mapping[str, Any] | list[Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def safe_slug(title: str) -> str:
    text = _SLUG.sub("-", title.casefold()).strip("-")[:80]
    return text or "case"


def new_case_payload(
    *,
    title: str,
    slug: str,
    classification: Mapping[str, Any],
    pending: PendingItem | None,
    corpus: Mapping[str, Any],
    backend: Mapping[str, Any],
    allowance: Mapping[str, Any],
    last_display: Mapping[str, Any],
    approved_scope: Mapping[str, Any] | None = None,
    approved_plan: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": CASE_SCHEMA_VERSION,
        "slug": slug,
        "title": title,
        "proposition": dict(classification),
        "status": None,
        "pending": pending.to_payload() if pending is not None else None,
        "consumed_approvals": [],
        "approved_scope": approved_scope,
        "approved_plan": approved_plan,
        "backend": dict(backend),
        "allowance": dict(allowance),
        "corpus": dict(corpus),
        "revision": 1,
        "last_display": dict(last_display),
    }


def increment_intake(allowance: Mapping[str, Any], *, planning: bool) -> dict[str, Any]:
    updated = dict(allowance)
    updated["intake_operations"] = int(updated.get("intake_operations") or 0) + 1
    if planning:
        updated["local_planning_operations"] = int(updated.get("local_planning_operations") or 0) + 1
    return updated


def list_cases(root: Path) -> tuple[CaseRecord, ...]:
    if not root.is_dir():
        return ()
    records: list[CaseRecord] = []
    for child in sorted(path for path in root.iterdir() if path.is_dir()):
        path = child / "case.json"
        if not path.is_file():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict) and payload.get("title") and payload.get("slug"):
            records.append(CaseRecord(payload, path))
    return tuple(records)


def find_by_proposition(root: Path, proposition: str) -> CaseRecord | None:
    from bav.debater.intake import conservative_proposition_match

    matches = [
        record
        for record in list_cases(root)
        if conservative_proposition_match(record.proposition, proposition)
    ]
    if len(matches) > 1:
        raise CaseSelectionError("multiple cases share the same accepted proposition")
    return matches[0] if matches else None


def select_case(root: Path, reference: str) -> CaseRecord:
    records = list_cases(root)
    if not records:
        raise CaseSelectionError("no_match")
    exact = [record for record in records if record.title == reference]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        raise CaseSelectionError("ambiguous")
    needle = reference.casefold()
    fragments = [record for record in records if needle in record.title.casefold()]
    if len(fragments) == 1:
        return fragments[0]
    if len(fragments) > 1:
        raise CaseSelectionError("ambiguous")
    raise CaseSelectionError("no_match")


def allocate_title(root: Path, title: str, proposition: str) -> str:
    from bav.debater.intake import conservative_proposition_match

    for record in list_cases(root):
        if record.title != title:
            continue
        if conservative_proposition_match(record.proposition, proposition):
            return title
        marker = "negated" if re.search(r"\bnot\b", proposition, re.I) else "alt wording"
        return f"{title} ({marker})"
    return title


def allocate_slug(root: Path, title: str, proposition: str) -> str:
    from bav.debater.intake import conservative_proposition_match

    base = safe_slug(title)
    existing = root / base / "case.json"
    if not existing.is_file():
        return base
    try:
        payload = json.loads(existing.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return f"{base}-{sha256_text(proposition)[:8]}"
    if conservative_proposition_match(str(payload.get("proposition", {}).get("accepted") or ""), proposition):
        return base
    return f"{base}-{sha256_text(proposition)[:8]}"


@contextmanager
def locked_case(directory: Path, *, nonblocking: bool = True) -> Iterator[None]:
    directory.mkdir(parents=True, exist_ok=True)
    fd = os.open(directory / ".case.lock", os.O_CREAT | os.O_RDWR, 0o644)
    flags = fcntl.LOCK_EX | (fcntl.LOCK_NB if nonblocking else 0)
    try:
        fcntl.flock(fd, flags)
    except BlockingIOError as exc:
        os.close(fd)
        raise CaseLocked("case is locked by another writer") from exc
    try:
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def write_case_atomically(directory: Path, payload: Mapping[str, Any]) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "sources").mkdir(exist_ok=True)
    (directory / "extracted").mkdir(exist_ok=True)
    revisions = directory / "revisions"
    revisions.mkdir(exist_ok=True)
    target = directory / "case.json"
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    fd, tmp_name = tempfile.mkstemp(prefix="case.json.", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, target)
    except Exception:
        if os.path.exists(tmp_name):
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
        raise
    revision = int(payload.get("revision") or 1)
    (revisions / f"r{revision}.json").write_text(encoded, encoding="utf-8")
    return target


def load_case(directory: Path) -> CaseRecord:
    path = directory / "case.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("case.json must be an object")
    if payload.get("schema_version") != CASE_SCHEMA_VERSION:
        raise ValueError("unsupported case schema")
    return CaseRecord(payload, path)


def pending_from_payload(payload: Mapping[str, Any] | None) -> PendingItem | None:
    if not payload:
        return None
    return PendingItem(
        item_id=str(payload["item_id"]),
        kind=payload["kind"],
        revision=str(payload["revision"]),
        actions=tuple(payload.get("actions") or ()),
        input_fingerprint=str(payload["input_fingerprint"]),
        provider_boundary=dict(payload.get("provider_boundary") or {}),
        allowance_fingerprint=str(payload["allowance_fingerprint"]),
        displayed=dict(payload.get("displayed") or {}),
        consumed=bool(payload.get("consumed")),
    )
