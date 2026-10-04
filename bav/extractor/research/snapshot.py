"""Approved-snapshot inventory over registered research-source bundles."""

from __future__ import annotations

import json
from pathlib import Path

from bav.extractor.research.contracts import InventoryRecord, SnapshotInventory
from bav.extractor.research.paths import PathDenied, sha256_file, sha256_text, validate_registered_path
from bav.extractor.research.store import (
    DOCUMENT_NAME,
    ORIGINAL_MD_NAME,
    ORIGINAL_PDF_NAME,
    load_inventory_record,
    verify_bundle_hashes,
)

SNAPSHOT_IDENTITY_VERSION = "verified-source-v2"

DEFAULT_SNAPSHOT_ID = "2026-10-04-debater-asia-benchmark"


def snapshot_manifest_path(input_root: Path, snapshot_id: str) -> Path:
    return input_root / "research_snapshots" / snapshot_id / "manifest.json"


def load_snapshot_inventory(
    snapshot_id: str,
    *,
    input_root: Path,
    repository: Path,
) -> SnapshotInventory:
    repo = repository
    manifest_path = snapshot_manifest_path(input_root, snapshot_id)
    approved_roots = (
        input_root / "lululemon" / "research_sources",
        input_root / "fast_retailing" / "research_sources",
        input_root / "cases",
        input_root / "research_snapshots",
    )
    validate_registered_path(manifest_path, approved_roots=(input_root / "research_snapshots",))
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    selected = payload.get("selected_corpus") or ()
    records: list[InventoryRecord] = []
    gaps: list[str] = []
    fingerprints: list[str] = [
        SNAPSHOT_IDENTITY_VERSION,
        sha256_text(manifest_path.read_text(encoding="utf-8")),
    ]
    for relative in selected:
        path = (repo / relative).resolve() if not Path(relative).is_absolute() else Path(relative)
        try:
            validate_registered_path(path, approved_roots=approved_roots)
        except PathDenied as exc:
            gaps.append(f"unapproved_manifest:{relative}:{exc.reason}")
            continue
        bundle_dir = path.parent
        try:
            record = load_inventory_record(bundle_dir)
        except (OSError, json.JSONDecodeError, KeyError) as exc:
            gaps.append(f"unreadable_bundle:{relative}:{exc}")
            continue
        observed_prepared, observed_original, ok, problems = inspect_bundle_state(bundle_dir)
        if not ok:
            gaps.extend(f"{record.document_id}:{item}" for item in problems)
        records.append(record)
        fingerprints.extend(
            (
                record.document_id,
                record.original_sha256,
                record.prepared_sha256,
                observed_original,
                observed_prepared,
                record.converter_profile_id or "",
                "|".join(problems),
                "|".join(record.limitations),
            )
        )
        gaps.extend(record.limitations)
    coverage = tuple(dict.fromkeys(gaps))
    fingerprints.append("|".join(coverage))
    snapshot_fingerprint = sha256_text("|".join(fingerprints))
    return SnapshotInventory(
        snapshot_id=snapshot_id,
        snapshot_fingerprint=snapshot_fingerprint,
        records=tuple(records),
        coverage_gaps=coverage,
    )


def inspect_bundle_state(bundle_dir: Path) -> tuple[str, str, bool, tuple[str, ...]]:
    """Observed representation hashes and current integrity, not declared hashes alone."""
    document = bundle_dir / DOCUMENT_NAME
    observed_prepared = sha256_file(document) if document.is_file() else "prepared-missing"
    original = bundle_dir / ORIGINAL_PDF_NAME
    if not original.is_file():
        original = bundle_dir / ORIGINAL_MD_NAME
    observed_original = sha256_file(original) if original.is_file() else "original-missing"
    ok, problems = verify_bundle_hashes(bundle_dir)
    return observed_prepared, observed_original, ok, problems
