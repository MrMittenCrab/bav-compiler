"""Source-faithful management-KPI document types, parse, and load."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Mapping

from .extracted_kind import KIND_MANAGEMENT_KPI, classify_extracted_payload, document_label
from .filing import SCHEMA_VERSION

_MISSING = object()
_PHYSICAL_PAGE_UNRESOLVED = "unresolved"
_ASSURANCE_UNKNOWN = "unknown"
_PRESENTATION_UNKNOWN = "unknown"
_PRESENTATION_ROLES = frozenset(
    {"current", "comparative", "restated", "prior", "unknown"}
)
_ASSURANCE_STATUSES = frozenset({"audited", "unaudited", "unknown"})
_PRESENTATION_OBJECT_KEYS = frozenset({"role", "evidence", "source"})
_ASSURANCE_OBJECT_KEYS = frozenset({"status", "evidence", "source"})
_REVISION_OBJECT_KEYS = frozenset({"revises", "evidence", "source"})
_REVISION_TARGET_REQUIRED = (
    "metric_id",
    "period",
    "source_file",
    "page_reference",
)
_REVISION_TARGET_OPTIONAL = (
    "definition_id",
    "unit",
    "basis",
    "comparison",
    "section",
)
_REVISION_TARGET_KEYS = frozenset(
    _REVISION_TARGET_REQUIRED + _REVISION_TARGET_OPTIONAL
)
_EVIDENCE_SOURCE_KEYS = frozenset(
    {"section", "page_reference", "source_file", "physical_page_mapping"}
)


def _required_nonempty_str(payload: Mapping[str, Any], key: str, *, context: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}.{key} is required")
    return value


def _optional_str(payload: Mapping[str, Any], key: str, *, context: str) -> str:
    if key not in payload or payload[key] is None:
        return ""
    value = payload[key]
    if not isinstance(value, str):
        raise ValueError(f"{context}.{key} must be a string")
    return value


def _require_finite_number(value: object, *, context: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{context} must be numeric")
    amount = float(value)
    if not math.isfinite(amount):
        raise ValueError(f"{context} must be finite")
    return amount


def _optional_finite_number(value: object, *, context: str) -> float | None:
    if value is None:
        return None
    return _require_finite_number(value, context=context)


def _parse_iso_date(value: object, *, context: str) -> date:
    if not isinstance(value, str) or len(value) != 10:
        raise ValueError(f"{context} invalid date: {value!r}")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{context} invalid date: {value!r}") from exc
    if parsed.isoformat() != value:
        raise ValueError(f"{context} invalid date: {value!r}")
    return parsed


@dataclass(frozen=True)
class PrintedSourceRef:
    section: str
    page_reference: str
    physical_page_mapping: str = _PHYSICAL_PAGE_UNRESOLVED

    def to_payload(self) -> dict[str, str]:
        return {
            "section": self.section,
            "page_reference": self.page_reference,
            "physical_page_mapping": self.physical_page_mapping,
        }


@dataclass(frozen=True)
class OccurrenceDimensionEvidence:
    value: str
    evidence: str = ""
    source: PrintedSourceRef | None = None
    locator: str = ""

    def to_payload(self, *, value_key: str) -> dict[str, Any]:
        return {
            value_key: self.value,
            "evidence": self.evidence,
            "locator": self.locator,
            "source": None if self.source is None else self.source.to_payload(),
        }


@dataclass(frozen=True)
class OccurrenceRevisionEvidence:
    evidence: str = ""
    source: PrintedSourceRef | None = None
    locator: str = ""
    revises: tuple[tuple[str, str], ...] = ()

    def to_payload(self) -> dict[str, Any]:
        return {
            "evidence": self.evidence,
            "locator": self.locator,
            "source": None if self.source is None else self.source.to_payload(),
            "revises": dict(self.revises) if self.revises else None,
        }


UNKNOWN_PRESENTATION = OccurrenceDimensionEvidence(value=_PRESENTATION_UNKNOWN)
UNKNOWN_ASSURANCE = OccurrenceDimensionEvidence(value=_ASSURANCE_UNKNOWN)
UNKNOWN_REVISION = OccurrenceRevisionEvidence()


@dataclass(frozen=True)
class ManagementKpiDefinition:
    definition_id: str
    metric_id: str
    reported_label: str
    definition: str
    source: PrintedSourceRef

    def to_payload(self) -> dict[str, Any]:
        return {
            "definition_id": self.definition_id,
            "metric_id": self.metric_id,
            "reported_label": self.reported_label,
            "definition": self.definition,
            "source": self.source.to_payload(),
        }


@dataclass(frozen=True)
class ManagementKpiDocument:
    schema_version: str
    company: str
    ticker: str
    fiscal_year: int
    fiscal_year_end: date
    source_file: str
    reporting_basis: str
    extraction_policy: tuple[tuple[str, str], ...]
    definitions: tuple[ManagementKpiDefinition, ...]
    reported: tuple[dict[str, Any], ...]
    store_counts: dict[str, Any]
    targets: tuple[dict[str, Any], ...]
    extraction_document: str


def load_management_kpi_document(path: Path) -> ManagementKpiDocument:
    """Parse one management-KPI extraction document."""
    raw_path = Path(path)
    payload = json.loads(raw_path.read_text(encoding="utf-8"))
    return parse_management_kpi_document(payload, path=raw_path)


def parse_management_kpi_document(
    payload: object,
    *,
    path: Path | str | None = None,
) -> ManagementKpiDocument:
    label = document_label(path)
    if not isinstance(payload, dict):
        raise ValueError(f"{label}: extracted JSON must be an object")
    kind = classify_extracted_payload(payload, path=path)
    if kind != KIND_MANAGEMENT_KPI:
        raise ValueError(f"{label}: not a management-KPI document")
    schema_version = str(payload.get("schema_version") or "")
    if schema_version != SCHEMA_VERSION:
        raise ValueError(
            f"{label}: unsupported schema_version: {schema_version!r}"
        )
    company = _required_nonempty_str(payload, "company", context=label)
    ticker = _required_nonempty_str(payload, "ticker", context=label)
    report = payload.get("report")
    if not isinstance(report, dict):
        raise ValueError(f"{label}.report must be an object")
    fiscal_year = report.get("fiscal_year")
    if (
        not isinstance(fiscal_year, int)
        or isinstance(fiscal_year, bool)
        or fiscal_year <= 0
    ):
        raise ValueError(f"{label}.report.fiscal_year must be a positive integer")
    fiscal_year_end = _parse_iso_date(
        report.get("fiscal_year_end"), context=f"{label}.report.fiscal_year_end"
    )
    source_file = _required_nonempty_str(
        report, "source_file", context=f"{label}.report"
    )
    reporting_basis = _optional_str(
        report, "reporting_basis", context=f"{label}.report"
    )
    policy_raw = payload.get("extraction_policy") or {}
    if not isinstance(policy_raw, dict):
        raise ValueError(f"{label}.extraction_policy must be an object")
    policy = tuple(
        (str(key), str(value))
        for key, value in policy_raw.items()
        if isinstance(value, str)
    )
    definitions = tuple(
        parse_definition(item, context=f"{label}.kpi_definitions[{index}]")
        for index, item in enumerate(payload["kpi_definitions"])
    )
    seen_definitions: set[str] = set()
    for definition in definitions:
        if definition.definition_id in seen_definitions:
            raise ValueError(
                f"{label}: duplicate definition_id {definition.definition_id!r}"
            )
        seen_definitions.add(definition.definition_id)
    reported = payload["reported_kpis"]
    if not isinstance(reported, list):
        raise ValueError(f"{label}.reported_kpis must be an array")
    for index, item in enumerate(reported):
        if not isinstance(item, dict):
            raise ValueError(f"{label}.reported_kpis[{index}] must be an object")
        definition_id = item.get("definition_id")
        if definition_id not in (None, ""):
            if not isinstance(definition_id, str):
                raise ValueError(
                    f"{label}.reported_kpis[{index}].definition_id must be a string"
                )
            if definition_id not in seen_definitions:
                raise ValueError(
                    f"{label}.reported_kpis[{index}]: dangling definition_id "
                    f"{definition_id!r}"
                )
        _optional_finite_number(
            item.get("value"),
            context=f"{label}.reported_kpis[{index}].value",
        )
        parse_reported_occurrence_evidence(
            item,
            context=f"{label}.reported_kpis[{index}]",
            bound_source_file=source_file,
            extraction_document=label,
            index=index,
            supported=metric_supports_occurrence_evidence(item.get("metric_id")),
        )
    store_counts = payload["store_counts_by_market"]
    if not isinstance(store_counts, dict):
        raise ValueError(f"{label}.store_counts_by_market must be an object")
    targets = payload["management_targets"]
    if not isinstance(targets, list):
        raise ValueError(f"{label}.management_targets must be an array")
    for index, item in enumerate(targets):
        if not isinstance(item, dict):
            raise ValueError(
                f"{label}.management_targets[{index}] must be an object"
            )
    return ManagementKpiDocument(
        schema_version=schema_version,
        company=company,
        ticker=ticker,
        fiscal_year=fiscal_year,
        fiscal_year_end=fiscal_year_end,
        source_file=source_file,
        reporting_basis=reporting_basis,
        extraction_policy=policy,
        definitions=definitions,
        reported=tuple(reported),
        store_counts=store_counts,
        targets=tuple(targets),
        extraction_document=document_label(path),
    )


def parse_printed_source(payload: object, *, context: str) -> PrintedSourceRef:
    if not isinstance(payload, dict):
        raise ValueError(f"{context}.source must be an object")
    section = _optional_str(payload, "section", context=f"{context}.source")
    page_reference = _optional_str(
        payload, "page_reference", context=f"{context}.source"
    )
    if not page_reference.strip():
        raise ValueError(f"{context}.source.page_reference is required")
    return PrintedSourceRef(
        section=section,
        page_reference=page_reference,
        physical_page_mapping=_PHYSICAL_PAGE_UNRESOLVED,
    )


def metric_supports_occurrence_evidence(metric_id: object) -> bool:
    from core.ingestion.management_kpi_identity import SUPPORTED_METRIC_MAPPINGS

    return isinstance(metric_id, str) and metric_id in SUPPORTED_METRIC_MAPPINGS


def _retain_evidence_text(value: object, *, context: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{context} must be a string")
    return value


def parse_evidence_source(
    payload: object,
    *,
    context: str,
    bound_source_file: str,
) -> PrintedSourceRef:
    if not isinstance(payload, dict):
        raise ValueError(f"{context} must be an object")
    extra = sorted(key for key in payload if key not in _EVIDENCE_SOURCE_KEYS)
    if extra:
        raise ValueError(f"{context} has unexpected fields: {extra}")
    mapping = payload.get("physical_page_mapping")
    if mapping not in (None, "", _PHYSICAL_PAGE_UNRESOLVED):
        raise ValueError(
            f"{context}.physical_page_mapping cannot certify a PDF page"
        )
    source_file = payload.get("source_file")
    if source_file is not None:
        if not isinstance(source_file, str):
            raise ValueError(f"{context}.source_file must be a string")
        if source_file.strip() != bound_source_file:
            raise ValueError(
                f"{context} is not bound to the observation source document"
            )
    parsed = parse_printed_source(payload, context=context.rsplit(".", 1)[0])
    return PrintedSourceRef(
        section=parsed.section,
        page_reference=parsed.page_reference,
        physical_page_mapping=_PHYSICAL_PAGE_UNRESOLVED,
    )


def parse_dimension_evidence(
    item: Mapping[str, Any],
    *,
    object_key: str,
    value_key: str,
    allowed: frozenset[str],
    unknown: str,
    context: str,
    bound_source_file: str,
    locator: str,
    supported: bool,
    unresolved_reason: str,
    top_level_key: str | None = None,
) -> tuple[OccurrenceDimensionEvidence, str | None]:
    raw = item.get(object_key, _MISSING)
    if raw is _MISSING or raw is None:
        top = _top_level_dimension_value(
            item, key=top_level_key, allowed=allowed, unknown=unknown, context=context
        )
        if top is not None and top != unknown:
            raise ValueError(
                f"{context}.{top_level_key} asserts {top!r} without documentary evidence"
            )
        return (
            OccurrenceDimensionEvidence(value=unknown, locator=locator),
            unresolved_reason,
        )
    if not isinstance(raw, dict):
        raise ValueError(f"{context}.{object_key} must be an object")
    extra = sorted(key for key in raw if key not in (
        _PRESENTATION_OBJECT_KEYS if object_key == "presentation" else _ASSURANCE_OBJECT_KEYS
    ))
    if extra:
        raise ValueError(f"{context}.{object_key} has unexpected fields: {extra}")
    value_raw = raw.get(value_key, _MISSING)
    if value_raw is _MISSING or value_raw is None:
        value = unknown
    elif not isinstance(value_raw, str):
        raise ValueError(f"{context}.{object_key}.{value_key} must be a string")
    else:
        value = value_raw.strip()
        if not value:
            value = unknown
        elif value not in allowed:
            raise ValueError(
                f"{context}.{object_key}.{value_key} is invalid: {value_raw!r}"
            )
    top = _top_level_dimension_value(
        item, key=top_level_key, allowed=allowed, unknown=unknown, context=context
    )
    if top is not None and top != value:
        raise ValueError(
            f"{context} has contradictory {unresolved_reason} assertions"
        )
    evidence = _retain_evidence_text(
        raw.get("evidence") if "evidence" in raw else None,
        context=f"{context}.{object_key}.evidence",
    )
    source_raw = raw.get("source", _MISSING)
    source: PrintedSourceRef | None = None
    if source_raw is not _MISSING and source_raw is not None:
        source = parse_evidence_source(
            source_raw,
            context=f"{context}.{object_key}.source",
            bound_source_file=bound_source_file,
        )
    record = OccurrenceDimensionEvidence(
        value=value,
        evidence=evidence,
        source=source,
        locator=locator,
    )
    if value == unknown:
        return record, unresolved_reason
    if not supported:
        raise ValueError(
            f"{context}.{object_key} cannot assign {value!r} on an unsupported observation"
        )
    if not evidence.strip():
        raise ValueError(
            f"{context}.{object_key} requires nonblank documentary evidence"
        )
    if source is None:
        raise ValueError(
            f"{context}.{object_key} requires a source bound to the observation document"
        )
    return record, None


def _top_level_dimension_value(
    item: Mapping[str, Any],
    *,
    key: str | None,
    allowed: frozenset[str],
    unknown: str,
    context: str,
) -> str | None:
    if not key or key not in item:
        return None
    raw = item[key]
    if raw is None:
        return unknown
    if not isinstance(raw, str):
        raise ValueError(f"{context}.{key} must be a string")
    value = raw.strip() or unknown
    if value not in allowed:
        raise ValueError(f"{context}.{key} is invalid: {raw!r}")
    return value


def parse_reported_occurrence_evidence(
    item: Mapping[str, Any],
    *,
    context: str,
    bound_source_file: str,
    extraction_document: str,
    index: int,
    supported: bool,
) -> tuple[OccurrenceDimensionEvidence, str | None, OccurrenceDimensionEvidence, str | None]:
    presentation, presentation_unresolved = parse_dimension_evidence(
        item,
        object_key="presentation",
        value_key="role",
        allowed=_PRESENTATION_ROLES,
        unknown=_PRESENTATION_UNKNOWN,
        context=context,
        bound_source_file=bound_source_file,
        locator=f"{extraction_document}:reported_kpis[{index}].presentation",
        supported=supported,
        unresolved_reason="presentation_role",
        top_level_key="presentation_role",
    )
    assurance, assurance_unresolved = parse_dimension_evidence(
        item,
        object_key="assurance",
        value_key="status",
        allowed=_ASSURANCE_STATUSES,
        unknown=_ASSURANCE_UNKNOWN,
        context=context,
        bound_source_file=bound_source_file,
        locator=f"{extraction_document}:reported_kpis[{index}].assurance",
        supported=supported,
        unresolved_reason="assurance",
    )
    return presentation, presentation_unresolved, assurance, assurance_unresolved


def parse_revision_target(
    payload: object, *, context: str
) -> tuple[tuple[str, str], ...]:
    if not isinstance(payload, dict):
        raise ValueError(f"{context}.revises must be an object")
    extra = sorted(key for key in payload if key not in _REVISION_TARGET_KEYS)
    if extra:
        raise ValueError(f"{context}.revises has unexpected fields: {extra}")
    parsed: dict[str, str] = {}
    for key in _REVISION_TARGET_REQUIRED:
        raw = payload.get(key, _MISSING)
        if raw is _MISSING or raw is None:
            raise ValueError(f"{context}.revises.{key} is required")
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError(f"{context}.revises.{key} is required")
        parsed[key] = raw.strip()
    for key in _REVISION_TARGET_OPTIONAL:
        if key not in payload or payload[key] is None:
            continue
        raw = payload[key]
        if not isinstance(raw, str):
            raise ValueError(f"{context}.revises.{key} must be a string")
        stripped = raw.strip()
        if stripped:
            parsed[key] = stripped
    return tuple(sorted(parsed.items()))


def parse_revision_evidence(
    item: Mapping[str, Any],
    *,
    context: str,
    bound_source_file: str,
    extraction_document: str,
    index: int,
    supported: bool,
    metric_id: str,
    period: str,
    definition_id: str,
    unit: str,
    basis: str,
    comparison: str,
    printed_source: PrintedSourceRef,
) -> tuple[OccurrenceRevisionEvidence, str | None]:
    locator = f"{extraction_document}:reported_kpis[{index}].revision"
    raw = item.get("revision", _MISSING)
    top = item.get("revises", _MISSING)
    if raw is _MISSING or raw is None:
        if top is not _MISSING and top is not None:
            raise ValueError(
                f"{context}.revises asserts a target without documentary evidence"
            )
        return OccurrenceRevisionEvidence(locator=locator), None
    if not isinstance(raw, dict):
        raise ValueError(f"{context}.revision must be an object")
    extra = sorted(key for key in raw if key not in _REVISION_OBJECT_KEYS)
    if extra:
        raise ValueError(f"{context}.revision has unexpected fields: {extra}")
    revises_raw = raw.get("revises", _MISSING)
    revises: tuple[tuple[str, str], ...] = ()
    if revises_raw is not _MISSING and revises_raw is not None:
        revises = parse_revision_target(revises_raw, context=f"{context}.revision")
    if top is not _MISSING and top is not None:
        top_target = parse_revision_target(top, context=context)
        if top_target != revises:
            raise ValueError(f"{context} has contradictory revises assertions")
    evidence = _retain_evidence_text(
        raw.get("evidence") if "evidence" in raw else None,
        context=f"{context}.revision.evidence",
    )
    source_raw = raw.get("source", _MISSING)
    source: PrintedSourceRef | None = None
    if source_raw is not _MISSING and source_raw is not None:
        source = parse_evidence_source(
            source_raw,
            context=f"{context}.revision.source",
            bound_source_file=bound_source_file,
        )
    record = OccurrenceRevisionEvidence(
        evidence=evidence,
        source=source,
        locator=locator,
        revises=revises,
    )
    if not revises:
        return record, "revision"
    if not supported:
        raise ValueError(
            f"{context}.revision cannot assign a target on an unsupported observation"
        )
    if source is None:
        raise ValueError(
            f"{context}.revision requires a source bound to the observation document"
        )
    named = dict(revises)
    self_fields = {
        "metric_id": metric_id,
        "period": period,
        "source_file": bound_source_file,
        "page_reference": printed_source.page_reference,
        "definition_id": definition_id,
        "unit": unit,
        "basis": basis,
        "comparison": comparison,
        "section": printed_source.section,
    }
    if all(self_fields.get(key, "") == value for key, value in named.items()):
        raise ValueError(f"{context}.revision is self-referential")
    if not evidence.strip():
        return record, "revision"
    return record, None


def parse_definition(payload: object, *, context: str) -> ManagementKpiDefinition:
    if not isinstance(payload, dict):
        raise ValueError(f"{context} must be an object")
    return ManagementKpiDefinition(
        definition_id=_required_nonempty_str(
            payload, "definition_id", context=context
        ),
        metric_id=_required_nonempty_str(payload, "metric_id", context=context),
        reported_label=_required_nonempty_str(
            payload, "reported_label", context=context
        ),
        definition=_required_nonempty_str(payload, "definition", context=context),
        source=parse_printed_source(payload.get("source"), context=context),
    )
