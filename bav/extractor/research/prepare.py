"""Prepare supplied Markdown or PDFs into versioned research-source bundles."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from bav.extractor.research.adapter import (
    ConverterCapabilityGap,
    ConversionAttempt,
    convert_pdf,
    inspect_installed_converter,
)
from bav.extractor.research.contracts import (
    ConverterProfile,
    PreparationRequest,
    PreparedBundle,
)
from bav.extractor.research.index import index_document_markdown, passage_to_dict
from bav.extractor.research.paths import (
    PathDenied,
    sha256_bytes,
    sha256_file,
    sha256_text,
    validate_explicit_source_file,
)
from bav.extractor.research.store import (
    DOCUMENT_NAME,
    case_source_root,
    company_research_root,
    find_reusable_bundle,
    register_bundle,
    reuse_key,
)


def prepare_source(
    request: PreparationRequest,
    *,
    input_root: Path,
    converter: ConverterProfile | ConversionAttempt | None = None,
) -> PreparedBundle:
    source = validate_explicit_source_file(request.source_path)
    original_bytes = source.read_bytes()
    original_sha256 = sha256_bytes(original_bytes)
    original_filename = request.original_filename or source.name
    suffix = source.suffix.lower()
    issuer_status = "assigned" if request.issuer and request.company_slug else (
        "uncertain" if request.issuer or request.company_slug else "unknown"
    )
    case_local = request.company_slug is None or issuer_status != "assigned"
    if case_local and not request.case_slug:
        if issuer_status != "assigned":
            raise PathDenied("ambiguous_import_requires_case")
        case_local = False
    destination_root = (
        case_source_root(input_root, request.case_slug)
        if case_local
        else company_research_root(input_root, request.company_slug or "")
    )
    if suffix in {".md", ".markdown", ".txt"}:
        document_text = original_bytes.decode("utf-8")
        prepared_sha256 = sha256_text(document_text)
        existing = find_reusable_bundle(
            destination_root,
            original_sha256=original_sha256,
            converter_profile_id=None,
            prepared_sha256=prepared_sha256,
        )
        if existing:
            return existing
        document_id = request.document_id or f"supplied-{prepared_sha256[:12]}"
        limitations = _markdown_limitations(document_text, request)
        passages, index_limits = index_document_markdown(
            _write_temp_markdown(source, document_text),
            document_id=document_id,
            source_fingerprint=original_sha256,
            representation_fingerprint=prepared_sha256,
            existing_limitations=limitations,
        )
        manifest = _manifest(
            request,
            document_id=document_id,
            original_filename=original_filename,
            original_sha256=original_sha256,
            prepared_sha256=prepared_sha256,
            representation="supplied_markdown",
            converter=None,
            case_local=case_local,
            issuer_status=issuer_status,
            limitations=index_limits,
        )
        bundle_dir = register_bundle(
            destination_root,
            document_id=document_id,
            original_bytes=original_bytes,
            original_filename=original_filename,
            original_suffix=".md",
            document_text=document_text,
            manifest=manifest,
            passages_payload={
                "document_id": document_id,
                "limitations": list(index_limits),
                "passages": [passage_to_dict(item) for item in passages],
            },
        )
        return PreparedBundle(
            document_id=document_id,
            company_slug=None if case_local else request.company_slug,
            case_slug=request.case_slug if case_local else None,
            bundle_dir=bundle_dir,
            original_filename=original_filename,
            original_sha256=original_sha256,
            prepared_sha256=prepared_sha256,
            converter_profile_id=None,
            representation="supplied_markdown",
            status="prepared",
            reused=False,
            case_local=case_local,
            limitations=index_limits,
            publication_date=request.publication_date,
            publication_date_status="known" if request.publication_date else "unknown",
            issuer_status=issuer_status,  # type: ignore[arg-type]
            lineage={
                "reuse_key": reuse_key(original_sha256, None, prepared_sha256),
                "pdf_and_markdown_are_independent_corroboration": False,
            },
        )
    if suffix != ".pdf":
        raise PathDenied("unsupported_source_type")
    inspected = converter if converter is not None else inspect_installed_converter()
    if isinstance(inspected, ConversionAttempt):
        existing = find_reusable_bundle(
            destination_root,
            original_sha256=original_sha256,
            converter_profile_id=None,
        )
        if existing:
            return existing
        return PreparedBundle(
            document_id=request.document_id or f"unprepared-{original_sha256[:12]}",
            company_slug=None if case_local else request.company_slug,
            case_slug=request.case_slug if case_local else None,
            bundle_dir=destination_root,
            original_filename=original_filename,
            original_sha256=original_sha256,
            prepared_sha256="",
            converter_profile_id=None,
            representation="converted_markdown",
            status="capability_gap",
            reused=False,
            case_local=case_local,
            limitations=(inspected.capability_gap or "converter_unavailable",),
            publication_date=request.publication_date,
            publication_date_status="known" if request.publication_date else "unknown",
            issuer_status=issuer_status,  # type: ignore[arg-type]
            lineage={"conversion": inspected.__dict__},
        )
    existing = find_reusable_bundle(
        destination_root,
        original_sha256=original_sha256,
        converter_profile_id=inspected.profile_id,
    )
    if existing:
        return existing
    if not request.allow_conversion:
        return PreparedBundle(
            document_id=request.document_id or f"unprepared-{original_sha256[:12]}",
            company_slug=None if case_local else request.company_slug,
            case_slug=request.case_slug if case_local else None,
            bundle_dir=destination_root,
            original_filename=original_filename,
            original_sha256=original_sha256,
            prepared_sha256="",
            converter_profile_id=inspected.profile_id,
            representation="converted_markdown",
            status="capability_gap",
            reused=False,
            case_local=case_local,
            limitations=("conversion_not_authorized_for_this_request",),
            publication_date=request.publication_date,
            publication_date_status="unknown",
            issuer_status=issuer_status,  # type: ignore[arg-type]
            lineage={},
        )
    staging = destination_root / ".conversion-staging"
    staging.mkdir(parents=True, exist_ok=True)
    work = staging / original_sha256
    work.mkdir(parents=True, exist_ok=True)
    input_copy = work / original_filename
    if not input_copy.exists():
        input_copy.write_bytes(original_bytes)
    try:
        markdown_path, attempt = convert_pdf(input_copy, work / "converter_output", profile=inspected)
        document_text = markdown_path.read_text(encoding="utf-8")
    except ConverterCapabilityGap as exc:
        return PreparedBundle(
            document_id=request.document_id or f"unprepared-{original_sha256[:12]}",
            company_slug=None if case_local else request.company_slug,
            case_slug=request.case_slug if case_local else None,
            bundle_dir=destination_root,
            original_filename=original_filename,
            original_sha256=original_sha256,
            prepared_sha256="",
            converter_profile_id=inspected.profile_id,
            representation="converted_markdown",
            status="failed",
            reused=False,
            case_local=case_local,
            limitations=(exc.reason,),
            publication_date=None,
            publication_date_status="unknown",
            issuer_status=issuer_status,  # type: ignore[arg-type]
            lineage={"conversion": (exc.attempt.__dict__ if exc.attempt else {})},
        )
    prepared_sha256 = sha256_text(document_text)
    reused = find_reusable_bundle(
        destination_root,
        original_sha256=original_sha256,
        converter_profile_id=inspected.profile_id,
        prepared_sha256=prepared_sha256,
    )
    if reused:
        return reused
    document_id = request.document_id or f"converted-{prepared_sha256[:12]}"
    limitations = (
        "converted_markdown_is_not_independently_supplied_evidence",
        "publication_date_unknown" if not request.publication_date else "publication_date_supplied_by_caller",
    )
    temp_md = work / DOCUMENT_NAME
    temp_md.write_text(document_text, encoding="utf-8")
    passages, index_limits = index_document_markdown(
        temp_md,
        document_id=document_id,
        source_fingerprint=original_sha256,
        representation_fingerprint=prepared_sha256,
        existing_limitations=limitations,
    )
    manifest = _manifest(
        request,
        document_id=document_id,
        original_filename=original_filename,
        original_sha256=original_sha256,
        prepared_sha256=prepared_sha256,
        representation="converted_markdown",
        converter=inspected,
        case_local=case_local,
        issuer_status=issuer_status,
        limitations=index_limits,
        conversion=attempt,
    )
    bundle_dir = register_bundle(
        destination_root,
        document_id=document_id,
        original_bytes=original_bytes,
        original_filename=original_filename,
        original_suffix=".pdf",
        document_text=document_text,
        manifest=manifest,
        passages_payload={
            "document_id": document_id,
            "limitations": list(index_limits),
            "passages": [passage_to_dict(item) for item in passages],
        },
    )
    return PreparedBundle(
        document_id=document_id,
        company_slug=None if case_local else request.company_slug,
        case_slug=request.case_slug if case_local else None,
        bundle_dir=bundle_dir,
        original_filename=original_filename,
        original_sha256=original_sha256,
        prepared_sha256=prepared_sha256,
        converter_profile_id=inspected.profile_id,
        representation="converted_markdown",
        status="prepared",
        reused=False,
        case_local=case_local,
        limitations=index_limits,
        publication_date=request.publication_date,
        publication_date_status="known" if request.publication_date else "unknown",
        issuer_status=issuer_status,  # type: ignore[arg-type]
        lineage={
            "reuse_key": reuse_key(original_sha256, inspected.profile_id, prepared_sha256),
            "pdf_and_markdown_are_independent_corroboration": False,
            "conversion": {
                "command": list(attempt.command),
                "elapsed_seconds": attempt.elapsed_seconds,
                "exit_code": attempt.exit_code,
            },
        },
    )


def _markdown_limitations(text: str, request: PreparationRequest) -> tuple[str, ...]:
    limits = ["supplied_markdown_accepted_without_conversion"]
    if not request.issuer:
        limits.append("issuer_uncertain")
    if not request.publication_date:
        limits.append("publication_date_unknown")
    if not request.document_type:
        limits.append("document_type_uncertain")
    if contains_partial_excerpt_markers(text):
        limits.append("possible_partial_excerpt")
    return tuple(limits)


def contains_partial_excerpt_markers(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in ("[excerpt]", "...", "snip", "continued on"))


def _write_temp_markdown(source: Path, text: str) -> Path:
    if source.suffix.lower() in {".md", ".markdown", ".txt"}:
        return source
    sibling = source.with_suffix(".prepared.md")
    sibling.write_text(text, encoding="utf-8")
    return sibling


def _manifest(
    request: PreparationRequest,
    *,
    document_id: str,
    original_filename: str,
    original_sha256: str,
    prepared_sha256: str,
    representation: str,
    converter: ConverterProfile | None,
    case_local: bool,
    issuer_status: str,
    limitations: tuple[str, ...],
    conversion: Any | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "document_id": document_id,
        "company_slug": None if case_local else request.company_slug,
        "case_slug": request.case_slug if case_local else None,
        "case_local": case_local,
        "issuer": request.issuer,
        "issuer_status": issuer_status,
        "document_type": request.document_type,
        "period_end": request.period_end,
        "publication_date": request.publication_date,
        "publication_date_status": "known" if request.publication_date else "unknown",
        "original_filename": original_filename,
        "original_sha256": original_sha256,
        "prepared_sha256": prepared_sha256,
        "representation": representation,
        "limitations": list(limitations),
        "identity_link": {
            "pdf_and_markdown_are_two_representations_of_one_source": representation == "converted_markdown",
            "independent_corroboration": False,
        },
    }
    if converter is not None:
        payload["converter"] = {
            "executable": converter.executable,
            "package": converter.package,
            "package_version": converter.package_version,
            "profile": converter.profile,
            "profile_id": converter.profile_id,
            "timeout_seconds": converter.timeout_seconds,
            "ocr": False,
            "llm_enrichment": False,
        }
        if conversion is not None:
            payload["converter"]["elapsed_seconds_real"] = conversion.elapsed_seconds
            payload["converter"]["exit_code"] = conversion.exit_code
    return payload
