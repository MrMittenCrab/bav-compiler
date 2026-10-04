"""Atomic research-source registration and reuse keyed by content identity."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping

from bav.extractor.research.contracts import (
    InventoryRecord,
    PreparedBundle,
    Representation,
)
from bav.extractor.research.paths import (
    PathDenied,
    atomic_replace_directory,
    safe_document_id,
    sha256_file,
    sha256_text,
)

MANIFEST_NAME = "manifest.json"
DOCUMENT_NAME = "document.md"
ORIGINAL_MD_NAME = "original.md"
ORIGINAL_PDF_NAME = "original.pdf"
PASSAGES_NAME = "passages.json"
ASSETS_NAME = "assets"


def company_research_root(input_root: Path, company_slug: str) -> Path:
    return input_root / company_slug / "research_sources"


def case_source_root(input_root: Path, case_slug: str) -> Path:
    return input_root / "cases" / safe_document_id(case_slug) / "sources"


def reuse_key(original_sha256: str, converter_profile_id: str | None, prepared_sha256: str) -> str:
    return f"{original_sha256}:{converter_profile_id or 'supplied-markdown'}:{prepared_sha256}"


def find_reusable_bundle(
    root: Path,
    *,
    original_sha256: str,
    converter_profile_id: str | None,
    prepared_sha256: str | None = None,
) -> PreparedBundle | None:
    if not root.is_dir():
        return None
    wanted = original_sha256
    profile = converter_profile_id
    for child in sorted(
        path for path in root.iterdir() if path.is_dir() and not path.name.startswith(".")
    ):
        manifest_path = child / MANIFEST_NAME
        if not manifest_path.is_file():
            continue
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        if payload.get("original_sha256") != wanted:
            continue
        recorded_profile = _profile_id_from_manifest(payload)
        if profile is not None and recorded_profile != profile:
            continue
        document = child / DOCUMENT_NAME
        if not document.is_file():
            continue
        observed_prepared = sha256_file(document)
        if prepared_sha256 is not None and observed_prepared != prepared_sha256:
            continue
        if payload.get("prepared_sha256") and payload.get("prepared_sha256") != observed_prepared:
            continue
        return bundle_from_manifest(child, payload, reused=True)
    return None


def register_bundle(
    destination_root: Path,
    *,
    document_id: str,
    original_bytes: bytes,
    original_filename: str,
    original_suffix: str,
    document_text: str,
    manifest: Mapping[str, Any],
    passages_payload: Mapping[str, Any] | None = None,
    assets: Mapping[str, bytes] | None = None,
) -> Path:
    safe_id = safe_document_id(document_id)
    destination = destination_root / safe_id
    if destination.exists():
        existing = destination / MANIFEST_NAME
        if existing.is_file():
            payload = json.loads(existing.read_text(encoding="utf-8"))
            if (
                payload.get("original_sha256") == manifest.get("original_sha256")
                and payload.get("prepared_sha256") == manifest.get("prepared_sha256")
                and _profile_id_from_manifest(payload) == _profile_id_from_manifest(manifest)
            ):
                return destination
        versioned = f"{safe_id}-{manifest.get('prepared_sha256', 'changed')[:12]}"
        safe_id = safe_document_id(versioned)
        destination = destination_root / safe_id
        if destination.exists():
            return destination
    destination_root.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=f".{safe_id}.", dir=str(destination_root))
    )
    try:
        original_name = ORIGINAL_PDF_NAME if original_suffix.lower() == ".pdf" else ORIGINAL_MD_NAME
        (staging / original_name).write_bytes(original_bytes)
        (staging / DOCUMENT_NAME).write_text(document_text, encoding="utf-8")
        (staging / MANIFEST_NAME).write_text(
            json.dumps(dict(manifest), indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        if passages_payload is not None:
            (staging / PASSAGES_NAME).write_text(
                json.dumps(dict(passages_payload), indent=2, ensure_ascii=True) + "\n",
                encoding="utf-8",
            )
        if assets:
            asset_dir = staging / ASSETS_NAME
            asset_dir.mkdir()
            for name, payload in assets.items():
                safe_name = Path(name).name
                if not safe_name or safe_name in {".", ".."} or "/" in name or "\\" in name:
                    continue
                (asset_dir / safe_name).write_bytes(payload)
        for handle_path in staging.rglob("*"):
            if handle_path.is_file():
                with handle_path.open("rb") as handle:
                    os.fsync(handle.fileno())
        atomic_replace_directory(staging, destination)
    except Exception:
        _remove_tree(staging)
        raise
    return destination


def load_inventory_record(bundle_dir: Path) -> InventoryRecord:
    payload = json.loads((bundle_dir / MANIFEST_NAME).read_text(encoding="utf-8"))
    bundle = bundle_from_manifest(bundle_dir, payload, reused=True)
    return InventoryRecord(
        document_id=bundle.document_id,
        company_slug=bundle.company_slug,
        case_local=bundle.case_local,
        original_filename=bundle.original_filename,
        original_sha256=bundle.original_sha256,
        prepared_sha256=bundle.prepared_sha256,
        converter_profile_id=bundle.converter_profile_id,
        representation=bundle.representation,
        publication_date_status=bundle.publication_date_status,
        issuer_status=bundle.issuer_status,
        limitations=bundle.limitations,
        bundle_dir=bundle.bundle_dir,
    )


def bundle_from_manifest(
    bundle_dir: Path,
    payload: Mapping[str, Any],
    *,
    reused: bool,
) -> PreparedBundle:
    representation: Representation
    if payload.get("representation") in {"supplied_markdown", "converted_markdown"}:
        representation = payload["representation"]  # type: ignore[assignment]
    elif payload.get("converter"):
        representation = "converted_markdown"
    else:
        representation = "supplied_markdown"
    publication_status = payload.get("publication_date_status") or (
        "known" if payload.get("publication_date") else "unknown"
    )
    issuer = payload.get("issuer")
    issuer_status = payload.get("issuer_status") or (
        "assigned" if isinstance(issuer, dict) and issuer.get("name") else "unknown"
    )
    limitations = payload.get("limitations") or ()
    return PreparedBundle(
        document_id=str(payload.get("document_id") or bundle_dir.name),
        company_slug=payload.get("company_slug"),
        case_slug=payload.get("case_slug"),
        bundle_dir=bundle_dir,
        original_filename=str(payload.get("original_filename") or ""),
        original_sha256=str(payload.get("original_sha256") or ""),
        prepared_sha256=str(payload.get("prepared_sha256") or sha256_file(bundle_dir / DOCUMENT_NAME)),
        converter_profile_id=_profile_id_from_manifest(payload),
        representation=representation,
        status="reused" if reused else "prepared",
        reused=reused,
        case_local=bool(payload.get("case_local")),
        limitations=tuple(limitations),
        publication_date=payload.get("publication_date"),
        publication_date_status=publication_status,
        issuer_status=issuer_status,
        lineage={
            "identity_link": payload.get("identity_link") or {},
            "retained_locations": payload.get("retained_locations") or {},
            "reuse_key": reuse_key(
                str(payload.get("original_sha256") or ""),
                _profile_id_from_manifest(payload),
                str(payload.get("prepared_sha256") or ""),
            ),
        },
    )


def verify_bundle_hashes(bundle_dir: Path) -> tuple[bool, tuple[str, ...]]:
    document = bundle_dir / DOCUMENT_NAME
    manifest = json.loads((bundle_dir / MANIFEST_NAME).read_text(encoding="utf-8"))
    problems: list[str] = []
    if not document.is_file():
        return False, ("prepared_document_missing",)
    observed = sha256_file(document)
    expected = manifest.get("prepared_sha256")
    if expected and expected != observed:
        problems.append("prepared_hash_mismatch")
    original = bundle_dir / ORIGINAL_PDF_NAME
    if not original.is_file():
        original = bundle_dir / ORIGINAL_MD_NAME
    if original.is_file() and manifest.get("original_sha256"):
        if sha256_file(original) != manifest.get("original_sha256"):
            problems.append("original_hash_mismatch")
    return not problems, tuple(problems)


def _profile_id_from_manifest(payload: Mapping[str, Any]) -> str | None:
    converter = payload.get("converter")
    if isinstance(converter, dict):
        if converter.get("profile_id"):
            return str(converter["profile_id"])
        package = converter.get("package") or "marker-pdf"
        version = converter.get("package_version") or converter.get("version") or ""
        profile = converter.get("profile") or ""
        if package or version or profile:
            return f"{package}:{version}:{profile}:ocr={converter.get('ocr', False)}:llm={converter.get('llm_enrichment', False)}"
    return payload.get("converter_profile_id")


def _remove_tree(path: Path) -> None:
    if not path.exists():
        return
    for child in sorted(path.rglob("*"), reverse=True):
        if child.is_file() or child.is_symlink():
            child.unlink()
        elif child.is_dir():
            child.rmdir()
    if path.is_dir():
        path.rmdir()
