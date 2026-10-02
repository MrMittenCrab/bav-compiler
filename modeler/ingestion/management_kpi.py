"""Content-aware management-KPI observation admission (audit-only)."""

from __future__ import annotations

import json
import math
from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Mapping

from extractor.data.extracted_kind import (
    KIND_ANNUAL_FILING,
    KIND_MANAGEMENT_KPI,
    classify_extracted_payload,
)
from extractor.data.filing import ExtractedFiling
from extractor.data.filing_validator import FilingValidationIssue, FilingValidationReport
from extractor.data.management_kpi_json import (
    UNKNOWN_ASSURANCE as _UNKNOWN_ASSURANCE,
    UNKNOWN_PRESENTATION as _UNKNOWN_PRESENTATION,
    UNKNOWN_REVISION as _UNKNOWN_REVISION,
    ManagementKpiDefinition,
    ManagementKpiDocument,
    OccurrenceDimensionEvidence,
    OccurrenceRevisionEvidence,
    PrintedSourceRef,
    _ASSURANCE_UNKNOWN,
    _PHYSICAL_PAGE_UNRESOLVED,
    _PRESENTATION_UNKNOWN,
    _optional_finite_number,
    _optional_str,
    _parse_iso_date,
    _require_finite_number,
    _required_nonempty_str,
    load_management_kpi_document,
    metric_supports_occurrence_evidence as _metric_supports_occurrence_evidence,
    parse_management_kpi_document,
    parse_printed_source as _parse_printed_source,
    parse_reported_occurrence_evidence as _parse_reported_occurrence_evidence,
    parse_revision_evidence as _parse_revision_evidence,
)

_ROLE_NONHISTORICAL = "nonhistorical"
_ROLE_HISTORICAL = "historical"
_ADMISSION_UNRECONCILED = "admitted_unreconciled"
_CANONICAL_STORE_METRIC = "company_operated_store_count"


def _num(value: float) -> int | float:
    return int(value) if float(value).is_integer() else float(value)


def _frozen_str_map(payload: object, *, context: str) -> tuple[tuple[str, str], ...]:
    if not isinstance(payload, dict):
        raise ValueError(f"{context} must be an object")
    items: list[tuple[str, str]] = []
    for key, value in payload.items():
        if not isinstance(key, str) or not key:
            raise ValueError(f"{context} keys must be strings")
        if value is None:
            items.append((key, ""))
            continue
        if isinstance(value, bool) or isinstance(value, (int, float)):
            items.append((key, str(value)))
            continue
        if not isinstance(value, str):
            raise ValueError(f"{context}.{key} must be a string or number")
        items.append((key, value))
    return tuple(items)


def _frozen_str_list(payload: object, *, context: str) -> tuple[str, ...]:
    if not isinstance(payload, list):
        raise ValueError(f"{context} must be an array")
    values: list[str] = []
    for index, item in enumerate(payload):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{context}[{index}] must be a non-empty string")
        values.append(item)
    return tuple(values)


_PDF_INSPECTION_CACHE: dict[tuple[str, str, str], Any] = {}


@dataclass(frozen=True)
class ManagementObservation:
    kind: str
    locator: str
    identity: str
    metric_id: str
    reported_label: str
    category: str
    period: str
    period_kind: str
    value: float | None
    unit: str
    basis: str
    comparison: str
    definition_id: str
    scope: tuple[tuple[str, str], ...]
    qualifiers: tuple[tuple[str, str], ...]
    drivers: tuple[tuple[str, tuple[str, ...]], ...]
    source: PrintedSourceRef
    historical_role: str
    assurance: str
    presentation_role: str
    extraction_document: str
    bound_source_file: str
    bound_source_sha256: str
    filing_year: int
    market: str = ""
    target_id: str = ""
    target_payload: tuple[tuple[str, Any], ...] = ()
    unresolved: tuple[str, ...] = ()
    presentation_record: OccurrenceDimensionEvidence = _UNKNOWN_PRESENTATION
    assurance_record: OccurrenceDimensionEvidence = _UNKNOWN_ASSURANCE
    revision_record: OccurrenceRevisionEvidence = _UNKNOWN_REVISION
    supporting_evidence: tuple[tuple[str, Any], ...] = ()

    def to_payload(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "kind": self.kind,
            "locator": self.locator,
            "identity": self.identity,
            "metric_id": self.metric_id,
            "reported_label": self.reported_label,
            "category": self.category,
            "period": self.period,
            "period_kind": self.period_kind,
            "unit": self.unit,
            "basis": self.basis,
            "comparison": self.comparison,
            "definition_id": self.definition_id,
            "scope": dict(self.scope),
            "qualifiers": dict(self.qualifiers),
            "drivers": {key: list(values) for key, values in self.drivers},
            "source": self.source.to_payload(),
            "historical_role": self.historical_role,
            "assurance": self.assurance,
            "presentation_role": self.presentation_role,
            "presentation_evidence": self.presentation_record.to_payload(
                value_key="role"
            ),
            "assurance_evidence": self.assurance_record.to_payload(value_key="status"),
            "revision_evidence": self.revision_record.to_payload(),
            "extraction_document": self.extraction_document,
            "bound_source_file": self.bound_source_file,
            "bound_source_sha256": self.bound_source_sha256,
            "filing_year": self.filing_year,
            "physical_page_mapping": self.source.physical_page_mapping,
            "supporting_evidence": {
                key: json.loads(value) for key, value in self.supporting_evidence
            },
            "unresolved": list(self.unresolved),
        }
        if self.value is not None:
            out["value"] = _num(self.value)
        else:
            out["value"] = None
        if self.market:
            out["market"] = self.market
        if self.target_id:
            out["target_id"] = self.target_id
        if self.target_payload:
            out["targets"] = dict(self.target_payload)
        return out


@dataclass(frozen=True)
class BoundManagementDocument:
    document: ManagementKpiDocument
    bound_filing_year: int
    bound_source_file: str
    bound_source_sha256: str
    issues: tuple[FilingValidationIssue, ...] = ()
    source_root: str = ""

    @property
    def ok(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)


@dataclass(frozen=True)
class ManagementAdmissionDiagnostic:
    code: str
    identity: str
    message: str
    occurrences: tuple[str, ...]
    values: tuple[float | None, ...] = ()

    def to_payload(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "identity": self.identity,
            "message": self.message,
            "occurrences": list(self.occurrences),
            "values": [
                None if value is None else _num(value) for value in self.values
            ],
        }


_REMAINING_UNRESOLVED = (
    "precedence",
    "physical_page_mapping",
    "assurance",
    "presentation_role",
    "revision",
)


@dataclass(frozen=True)
class ManagementAdmission:
    status: str
    documents: tuple[BoundManagementDocument, ...]
    definitions: tuple[ManagementKpiDefinition, ...]
    observations: tuple[ManagementObservation, ...]
    diagnostics: tuple[ManagementAdmissionDiagnostic, ...]
    assessments: tuple[Any, ...] = ()
    reconciliation: tuple[Any, ...] = ()
    revision_links: tuple[Any, ...] = ()
    group_selections: tuple[Any, ...] = ()
    group_decisions: tuple[Any, ...] = ()
    unresolved: tuple[str, ...] = _REMAINING_UNRESOLVED


def _supporting_pairs(payload: object) -> tuple[tuple[str, str], ...]:
    if not isinstance(payload, dict):
        return ()
    pairs: list[tuple[str, str]] = []
    for key, value in sorted(payload.items()):
        if not isinstance(key, str) or not key:
            continue
        pairs.append((key, json.dumps(value, sort_keys=True, default=str)))
    return tuple(pairs)


def _bind_dimension_pages(
    record: OccurrenceDimensionEvidence,
    page_mapping: str,
    *,
    page_reference: str = "",
) -> OccurrenceDimensionEvidence:
    if record.source is None:
        return record
    if not page_mapping and not page_reference:
        return record
    return replace(
        record,
        source=PrintedSourceRef(
            section=record.source.section,
            page_reference=page_reference or record.source.page_reference,
            physical_page_mapping=page_mapping or record.source.physical_page_mapping,
        ),
    )


def _presentation_source_binding(
    payload: object,
    *,
    bound: BoundManagementDocument,
) -> tuple[str, str]:
    """PDF-validated presentation locator from identity-specific passage bindings."""
    if not isinstance(payload, dict):
        return "", ""
    bindings = payload.get("passage_bindings") or {}
    presentation = bindings.get("presentation") or {}
    printed = list(presentation.get("printed_pages") or [])
    claimed = list(presentation.get("physical_pages") or [])
    if not printed:
        return "", ""
    inspection = _inspection_for(bound)
    if inspection is None:
        return "", ""
    from core.ingestion.management_kpi_enrichment import (
        format_physical_page_mapping,
        page_reference_from_printed,
        validate_physical_page_binding,
    )

    resolved = validate_physical_page_binding(inspection, printed, claimed)
    if not resolved:
        return "", ""
    return (
        format_physical_page_mapping(printed, resolved),
        page_reference_from_printed(printed),
    )


def _inspection_for(bound: BoundManagementDocument) -> Any | None:
    if not bound.source_root or not bound.bound_source_file:
        return None
    pdf = Path(bound.source_root) / bound.bound_source_file
    if not pdf.is_file():
        return None
    cache_key = (bound.source_root, bound.bound_source_file, bound.bound_source_sha256)
    cached = _PDF_INSPECTION_CACHE.get(cache_key)
    if cached is not None:
        return cached
    from core.ingestion.management_kpi_enrichment import inspect_source_pdf

    inspection = inspect_source_pdf(pdf)
    _PDF_INSPECTION_CACHE[cache_key] = inspection
    return inspection


def _supporting_evidence_binding(
    payload: object,
    *,
    printed_source: PrintedSourceRef,
    bound: BoundManagementDocument,
) -> tuple[tuple[tuple[str, str], ...], str]:
    pairs = _supporting_pairs(payload)
    if not pairs:
        return (), ""
    supporting = {key: json.loads(value) for key, value in pairs}
    claimed = supporting.get("physical_pages") or []
    printed = supporting.get("printed_pages") or []
    if not printed:
        from core.ingestion.management_kpi_enrichment import printed_pages_from_reference

        printed = list(printed_pages_from_reference(printed_source.page_reference))
    inspection = _inspection_for(bound)
    if inspection is None:
        return pairs, ""
    from core.ingestion.management_kpi_enrichment import (
        format_physical_page_mapping,
        validate_physical_page_binding,
    )

    resolved = validate_physical_page_binding(inspection, printed, claimed)
    if not resolved:
        return pairs, ""
    mapping = format_physical_page_mapping(printed, resolved)
    return pairs, mapping


def _observation_named_fields(observation: ManagementObservation) -> dict[str, str]:
    return {
        "metric_id": observation.metric_id,
        "period": observation.period,
        "source_file": observation.bound_source_file,
        "page_reference": observation.source.page_reference,
        "definition_id": observation.definition_id,
        "unit": observation.unit,
        "basis": observation.basis,
        "comparison": observation.comparison,
        "section": observation.source.section,
    }


def named_revision_target_matches(
    named: Mapping[str, str], observation: ManagementObservation
) -> bool:
    fields = _observation_named_fields(observation)
    return all(fields.get(key, "") == value for key, value in named.items())


def revision_target_matches(
    observation: ManagementObservation,
    observations: Iterable[ManagementObservation],
) -> tuple[ManagementObservation, ...]:
    named = dict(observation.revision_record.revises)
    if not named:
        return ()
    return tuple(
        item
        for item in observations
        if named_revision_target_matches(named, item)
    )


def _period_kind(period: str) -> str:
    if len(period) == 10 and period[4] == "-" and period[7] == "-":
        _parse_iso_date(period, context="period")
        return "date"
    return "fiscal_year_label"


def _scope_pairs(payload: object, *, context: str) -> tuple[tuple[str, str], ...]:
    if payload in (None, ""):
        return ()
    return tuple(sorted(_frozen_str_map(payload, context=context)))


def _qualifier_pairs(payload: object, *, context: str) -> tuple[tuple[str, str], ...]:
    if payload in (None, ""):
        return ()
    if not isinstance(payload, dict):
        raise ValueError(f"{context} must be an object")
    items: list[tuple[str, str]] = []
    for key, value in payload.items():
        if not isinstance(key, str) or not key:
            raise ValueError(f"{context} keys must be strings")
        if isinstance(value, bool):
            items.append((key, "true" if value else "false"))
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            if not math.isfinite(float(value)):
                raise ValueError(f"{context}.{key} must be finite")
            items.append((key, str(value)))
        elif value is None:
            items.append((key, ""))
        elif isinstance(value, str):
            items.append((key, value))
        else:
            items.append((key, json.dumps(value, sort_keys=True)))
    return tuple(sorted(items))


def _driver_pairs(payload: object, *, context: str) -> tuple[tuple[str, tuple[str, ...]], ...]:
    if payload in (None, ""):
        return ()
    if not isinstance(payload, dict):
        raise ValueError(f"{context} must be an object")
    items: list[tuple[str, tuple[str, ...]]] = []
    for key, value in payload.items():
        if not isinstance(key, str) or not key:
            raise ValueError(f"{context} keys must be strings")
        items.append((key, _frozen_str_list(value, context=f"{context}.{key}")))
    return tuple(sorted(items, key=lambda item: item[0]))


def _identity_parts(
    *,
    metric_id: str,
    definition_id: str,
    period: str,
    unit: str,
    basis: str,
    comparison: str,
    scope: tuple[tuple[str, str], ...],
    qualifiers: tuple[tuple[str, str], ...],
    market: str = "",
    kind: str = "reported_kpi",
) -> str:
    scope_text = ";".join(f"{key}={value}" for key, value in scope)
    qualifier_text = ";".join(f"{key}={value}" for key, value in qualifiers)
    return "|".join(
        [
            kind,
            metric_id,
            definition_id,
            period,
            unit,
            basis,
            comparison,
            market,
            scope_text,
            qualifier_text,
        ]
    )


def _unresolved_fields(
    *,
    period_kind: str,
    definition_id: str,
    historical_role: str,
    assurance_unknown: bool = True,
    presentation_unknown: bool = True,
    revision_unknown: bool = True,
    page_resolved: bool = False,
) -> tuple[str, ...]:
    unresolved: list[str] = []
    if not page_resolved:
        unresolved.append("physical_page_mapping")
    if assurance_unknown:
        unresolved.append("assurance")
    if presentation_unknown:
        unresolved.append("presentation_role")
    if revision_unknown:
        unresolved.append("revision")
    unresolved.append("canonical_selection")
    if period_kind == "fiscal_year_label":
        unresolved.append("period_date")
    if not definition_id:
        unresolved.append("definition_id")
    if historical_role == _ROLE_NONHISTORICAL:
        unresolved.append("historical_series")
    return tuple(unresolved)


def _observation_from_reported(
    item: Mapping[str, Any],
    *,
    bound: BoundManagementDocument,
    index: int,
) -> ManagementObservation:
    context = f"{bound.document.extraction_document}.reported_kpis[{index}]"
    metric_id = _required_nonempty_str(item, "metric_id", context=context)
    period = _required_nonempty_str(item, "period", context=context)
    unit = _required_nonempty_str(item, "unit", context=context)
    basis = _required_nonempty_str(item, "basis", context=context)
    definition_id = _optional_str(item, "definition_id", context=context)
    comparison = _optional_str(item, "comparison", context=context)
    scope = _scope_pairs(item.get("scope"), context=f"{context}.scope")
    qualifiers = _qualifier_pairs(
        item.get("qualifiers"), context=f"{context}.qualifiers"
    )
    drivers = _driver_pairs(item.get("drivers"), context=f"{context}.drivers")
    period_kind = _period_kind(period)
    identity = _identity_parts(
        metric_id=metric_id,
        definition_id=definition_id,
        period=period,
        unit=unit,
        basis=basis,
        comparison=comparison,
        scope=scope,
        qualifiers=qualifiers,
        kind="reported_kpi",
    )
    locator = (
        f"{bound.document.extraction_document}:reported_kpis[{index}]:"
        f"{metric_id}:{period}"
    )
    printed_source = _parse_printed_source(item.get("source"), context=context)
    supporting_pairs, page_mapping = _supporting_evidence_binding(
        item.get("supporting_evidence"),
        printed_source=printed_source,
        bound=bound,
    )
    presentation_mapping, presentation_ref = _presentation_source_binding(
        item.get("supporting_evidence"),
        bound=bound,
    )
    if page_mapping:
        printed_source = PrintedSourceRef(
            section=printed_source.section,
            page_reference=printed_source.page_reference,
            physical_page_mapping=page_mapping,
        )
    presentation_record, presentation_unresolved, assurance_record, assurance_unresolved = (
        _parse_reported_occurrence_evidence(
            item,
            context=context,
            bound_source_file=bound.bound_source_file,
            extraction_document=bound.document.extraction_document,
            index=index,
            supported=_metric_supports_occurrence_evidence(metric_id),
        )
    )
    revision_record, revision_unresolved = _parse_revision_evidence(
        item,
        context=context,
        bound_source_file=bound.bound_source_file,
        extraction_document=bound.document.extraction_document,
        index=index,
        supported=_metric_supports_occurrence_evidence(metric_id),
        metric_id=metric_id,
        period=period,
        definition_id=definition_id,
        unit=unit,
        basis=basis,
        comparison=comparison,
        printed_source=printed_source,
    )
    return ManagementObservation(
        kind="reported_kpi",
        locator=locator,
        identity=identity,
        metric_id=metric_id,
        reported_label=_required_nonempty_str(
            item, "reported_label", context=context
        ),
        category=_optional_str(item, "category", context=context),
        period=period,
        period_kind=period_kind,
        value=_optional_finite_number(item.get("value"), context=f"{context}.value"),
        unit=unit,
        basis=basis,
        comparison=comparison,
        definition_id=definition_id,
        scope=scope,
        qualifiers=qualifiers,
        drivers=drivers,
        source=printed_source,
        historical_role=_ROLE_HISTORICAL,
        assurance=assurance_record.value,
        presentation_role=presentation_record.value,
        extraction_document=bound.document.extraction_document,
        bound_source_file=bound.bound_source_file,
        bound_source_sha256=bound.bound_source_sha256,
        filing_year=bound.bound_filing_year,
        unresolved=_unresolved_fields(
            period_kind=period_kind,
            definition_id=definition_id,
            historical_role=_ROLE_HISTORICAL,
            assurance_unknown=assurance_unresolved is not None,
            presentation_unknown=presentation_unresolved is not None,
            revision_unknown=revision_unresolved is not None,
            page_resolved=bool(page_mapping),
        ),
        presentation_record=_bind_dimension_pages(
            presentation_record,
            presentation_mapping or page_mapping,
            page_reference=presentation_ref,
        ),
        assurance_record=_bind_dimension_pages(assurance_record, page_mapping),
        revision_record=revision_record,
        supporting_evidence=supporting_pairs,
    )


def _store_scope(geography: str) -> tuple[tuple[str, str], ...]:
    return (("geography", geography),)


def _observation_from_store_total(
    bound: BoundManagementDocument,
    *,
    as_of: str,
    value: float,
    source: PrintedSourceRef,
) -> ManagementObservation:
    scope = _store_scope("global")
    identity = _identity_parts(
        metric_id=_CANONICAL_STORE_METRIC,
        definition_id="",
        period=as_of,
        unit="stores",
        basis="reported",
        comparison="",
        scope=scope,
        qualifiers=(),
        kind="store_count_total",
    )
    locator = (
        f"{bound.document.extraction_document}:store_counts_by_market.total:{as_of}"
    )
    return ManagementObservation(
        kind="store_count_total",
        locator=locator,
        identity=identity,
        metric_id=_CANONICAL_STORE_METRIC,
        reported_label="Total company-operated stores",
        category="store_footprint",
        period=as_of,
        period_kind="date",
        value=value,
        unit="stores",
        basis="reported",
        comparison="",
        definition_id="",
        scope=scope,
        qualifiers=(),
        drivers=(),
        source=source,
        historical_role=_ROLE_HISTORICAL,
        assurance=_ASSURANCE_UNKNOWN,
        presentation_role=_PRESENTATION_UNKNOWN,
        extraction_document=bound.document.extraction_document,
        bound_source_file=bound.bound_source_file,
        bound_source_sha256=bound.bound_source_sha256,
        filing_year=bound.bound_filing_year,
        unresolved=_unresolved_fields(
            period_kind="date",
            definition_id="",
            historical_role=_ROLE_HISTORICAL,
        ),
    )


def _observation_from_store_market(
    bound: BoundManagementDocument,
    *,
    as_of: str,
    market: str,
    value: float,
    source: PrintedSourceRef,
    kind: str,
) -> ManagementObservation:
    geography = "global" if market == "total" else market
    scope = _store_scope(geography)
    identity = _identity_parts(
        metric_id=_CANONICAL_STORE_METRIC,
        definition_id="",
        period=as_of,
        unit="stores",
        basis="reported",
        comparison="",
        scope=scope,
        qualifiers=(),
        market=market,
        kind=kind,
    )
    locator = (
        f"{bound.document.extraction_document}:store_counts_by_market."
        f"{kind}:{market}:{as_of}"
    )
    return ManagementObservation(
        kind=kind,
        locator=locator,
        identity=identity,
        metric_id=_CANONICAL_STORE_METRIC,
        reported_label=market,
        category="store_footprint",
        period=as_of,
        period_kind="date",
        value=value,
        unit="stores",
        basis="reported",
        comparison="",
        definition_id="",
        scope=scope,
        qualifiers=(),
        drivers=(),
        source=source,
        historical_role=_ROLE_HISTORICAL,
        assurance=_ASSURANCE_UNKNOWN,
        presentation_role=_PRESENTATION_UNKNOWN,
        extraction_document=bound.document.extraction_document,
        bound_source_file=bound.bound_source_file,
        bound_source_sha256=bound.bound_source_sha256,
        filing_year=bound.bound_filing_year,
        market=market,
        unresolved=_unresolved_fields(
            period_kind="date",
            definition_id="",
            historical_role=_ROLE_HISTORICAL,
        ),
    )


def _parse_store_counts(
    bound: BoundManagementDocument,
) -> tuple[tuple[ManagementObservation, ...], float, float]:
    payload = bound.document.store_counts
    context = f"{bound.document.extraction_document}.store_counts_by_market"
    as_of = _parse_iso_date(payload.get("as_of"), context=f"{context}.as_of").isoformat()
    source = _parse_printed_source(payload.get("source"), context=context)
    total = _require_finite_number(payload.get("total"), context=f"{context}.total")
    observations = [
        _observation_from_store_total(
            bound, as_of=as_of, value=total, source=source
        )
    ]
    markets = payload.get("company_operated")
    if not isinstance(markets, dict) or not markets:
        raise ValueError(f"{context}.company_operated must be a non-empty object")
    market_sum = 0.0
    for market, raw in markets.items():
        if not isinstance(market, str) or not market:
            raise ValueError(f"{context}.company_operated keys must be strings")
        amount = _require_finite_number(
            raw, context=f"{context}.company_operated.{market}"
        )
        market_sum += amount
        observations.append(
            _observation_from_store_market(
                bound,
                as_of=as_of,
                market=market,
                value=amount,
                source=source,
                kind="store_count_market",
            )
        )
    regions = payload.get("regional_totals") or {}
    if regions:
        if not isinstance(regions, dict):
            raise ValueError(f"{context}.regional_totals must be an object")
        for region, raw in regions.items():
            if not isinstance(region, str) or not region:
                raise ValueError(f"{context}.regional_totals keys must be strings")
            observations.append(
                _observation_from_store_market(
                    bound,
                    as_of=as_of,
                    market=region,
                    value=_require_finite_number(
                        raw, context=f"{context}.regional_totals.{region}"
                    ),
                    source=source,
                    kind="store_count_region",
                )
            )
    return tuple(observations), total, market_sum


def _observation_from_target(
    item: Mapping[str, Any],
    *,
    bound: BoundManagementDocument,
    index: int,
) -> ManagementObservation:
    context = f"{bound.document.extraction_document}.management_targets[{index}]"
    target_id = _required_nonempty_str(item, "target_id", context=context)
    horizon = _required_nonempty_str(item, "horizon", context=context)
    targets = item.get("targets")
    if not isinstance(targets, dict) or not targets:
        raise ValueError(f"{context}.targets must be a non-empty object")
    identity = _identity_parts(
        metric_id=target_id,
        definition_id="",
        period=horizon,
        unit="",
        basis="target",
        comparison="",
        scope=(),
        qualifiers=(),
        kind="management_target",
    )
    locator = (
        f"{bound.document.extraction_document}:management_targets[{index}]:"
        f"{target_id}"
    )
    return ManagementObservation(
        kind="management_target",
        locator=locator,
        identity=identity,
        metric_id=target_id,
        reported_label=target_id,
        category="management_target",
        period=horizon,
        period_kind="fiscal_year_label",
        value=None,
        unit="",
        basis="target",
        comparison="",
        definition_id="",
        scope=(),
        qualifiers=(),
        drivers=(),
        source=_parse_printed_source(item.get("source"), context=context),
        historical_role=_ROLE_NONHISTORICAL,
        assurance=_ASSURANCE_UNKNOWN,
        presentation_role=_PRESENTATION_UNKNOWN,
        extraction_document=bound.document.extraction_document,
        bound_source_file=bound.bound_source_file,
        bound_source_sha256=bound.bound_source_sha256,
        filing_year=bound.bound_filing_year,
        target_id=target_id,
        target_payload=tuple(sorted(targets.items(), key=lambda item: item[0])),
        unresolved=_unresolved_fields(
            period_kind="fiscal_year_label",
            definition_id="",
            historical_role=_ROLE_NONHISTORICAL,
        ),
    )


def bind_management_documents(
    documents: Iterable[ManagementKpiDocument],
    filings: list[tuple[ExtractedFiling, FilingValidationReport]],
    *,
    source_root: Path | str | None = None,
) -> tuple[BoundManagementDocument, ...]:
    """Bind management documents to unique validated filings; fail closed."""
    bound: list[BoundManagementDocument] = []
    for document in documents:
        matches = [
            (filing, report)
            for filing, report in filings
            if filing.ticker == document.ticker
            and filing.company_name == document.company
            and filing.filing.fiscal_year == document.fiscal_year
            and filing.filing.period_end == document.fiscal_year_end
            and filing.filing.source_file == document.source_file
        ]
        ticker_year = [
            (filing, report)
            for filing, report in filings
            if filing.ticker == document.ticker
            and filing.filing.fiscal_year == document.fiscal_year
        ]
        label = document.extraction_document
        if not matches and ticker_year:
            raise ValueError(
                f"{label}: conflicting management-KPI binding metadata"
            )
        if not matches:
            raise ValueError(
                f"{label}: orphan management-KPI document has no matching filing"
            )
        if len(matches) > 1:
            raise ValueError(
                f"{label}: ambiguous management-KPI filing binding"
            )
        filing, report = matches[0]
        issues: list[FilingValidationIssue] = []
        if not report.ok or not report.computed_source_sha256:
            issues.append(
                FilingValidationIssue(
                    "error",
                    "invalid_management_binding",
                    f"{label}: cannot bind management-KPI document to an invalid filing",
                )
            )
        if filing.company_name != document.company:
            issues.append(
                FilingValidationIssue(
                    "error",
                    "conflicting_management_binding",
                    f"{label} company {document.company!r} != "
                    f"{filing.company_name!r}",
                )
            )
        bound.append(
            BoundManagementDocument(
                document=document,
                bound_filing_year=filing.filing.fiscal_year,
                bound_source_file=filing.filing.source_file,
                bound_source_sha256=report.computed_source_sha256 or "",
                issues=tuple(issues),
                source_root="" if source_root is None else str(Path(source_root)),
            )
        )
    return tuple(
        sorted(
            bound,
            key=lambda item: (
                item.bound_filing_year,
                item.bound_source_file,
                item.document.extraction_document,
            ),
        )
    )


def _comparable_store_key(observation: ManagementObservation) -> str | None:
    if observation.metric_id != _CANONICAL_STORE_METRIC:
        return None
    if observation.kind not in {"reported_kpi", "store_count_total"}:
        return None
    if observation.unit != "stores" or observation.basis != "reported":
        return None
    geography = dict(observation.scope).get("geography", "")
    if geography not in {"", "global"}:
        return None
    return "|".join(
        [
            _CANONICAL_STORE_METRIC,
            observation.period,
            observation.unit,
            observation.basis,
            "global",
        ]
    )


def _classify_duplicates(
    observations: tuple[ManagementObservation, ...],
    *,
    store_totals_vs_markets: tuple[tuple[str, float, float, str], ...],
    selected_store_facts: tuple[tuple[str, float, str], ...] = (),
) -> tuple[ManagementAdmissionDiagnostic, ...]:
    diagnostics: list[ManagementAdmissionDiagnostic] = []
    buckets: dict[str, list[ManagementObservation]] = defaultdict(list)
    for observation in observations:
        key = _comparable_store_key(observation)
        if key is None:
            continue
        buckets[key].append(observation)
    for identity, items in sorted(buckets.items()):
        if len(items) < 2:
            continue
        values = tuple(item.value for item in items)
        locators = tuple(item.locator for item in items)
        distinct = {float(value) for value in values if value is not None}
        if len(distinct) <= 1:
            diagnostics.append(
                ManagementAdmissionDiagnostic(
                    code="agreeing_duplicate",
                    identity=identity,
                    message=(
                        "agreeing store-total observations retained from "
                        "separate portions of the same filing"
                    ),
                    occurrences=locators,
                    values=values,
                )
            )
        else:
            diagnostics.append(
                ManagementAdmissionDiagnostic(
                    code="conflicting_candidate",
                    identity=identity,
                    message=(
                        "conflicting store-total observations retained without "
                        "canonical selection"
                    ),
                    occurrences=locators,
                    values=values,
                )
            )
    for locator, total, market_sum, identity in store_totals_vs_markets:
        if float(total) == float(market_sum):
            diagnostics.append(
                ManagementAdmissionDiagnostic(
                    code="agreeing_duplicate",
                    identity=identity,
                    message="market-table total agrees with the sum of market counts",
                    occurrences=(locator, f"{locator}:company_operated_sum"),
                    values=(total, market_sum),
                )
            )
        else:
            diagnostics.append(
                ManagementAdmissionDiagnostic(
                    code="conflicting_candidate",
                    identity=identity,
                    message=(
                        "market-table total disagrees with the sum of market counts"
                    ),
                    occurrences=(locator, f"{locator}:company_operated_sum"),
                    values=(total, market_sum),
                )
            )
    selected_by_period = {period: (value, locator) for period, value, locator in selected_store_facts}
    for observation in observations:
        key = _comparable_store_key(observation)
        if key is None or observation.value is None:
            continue
        selected = selected_by_period.get(observation.period)
        if selected is None:
            continue
        selected_value, selected_locator = selected
        identity = key + "|selected_operating_kpi"
        if float(observation.value) == float(selected_value):
            diagnostics.append(
                ManagementAdmissionDiagnostic(
                    code="agreeing_duplicate",
                    identity=identity,
                    message=(
                        "management store total agrees with accepted temporary "
                        "store facts; canonical selection is unchanged"
                    ),
                    occurrences=(observation.locator, selected_locator),
                    values=(observation.value, selected_value),
                )
            )
        else:
            diagnostics.append(
                ManagementAdmissionDiagnostic(
                    code="conflicting_candidate",
                    identity=identity,
                    message=(
                        "management store total conflicts with accepted "
                        "temporary store facts; canonical selection is unchanged"
                    ),
                    occurrences=(observation.locator, selected_locator),
                    values=(observation.value, selected_value),
                )
            )
    diagnostics.sort(
        key=lambda item: (item.code, item.identity, item.occurrences)
    )
    return tuple(diagnostics)


def _revision_target_diagnostics(
    observations: tuple[ManagementObservation, ...],
) -> tuple[ManagementAdmissionDiagnostic, ...]:
    diagnostics: list[ManagementAdmissionDiagnostic] = []
    for observation in observations:
        named = dict(observation.revision_record.revises)
        if not named:
            continue
        matches = [
            item
            for item in revision_target_matches(observation, observations)
            if item.locator != observation.locator
        ]
        locators = tuple(item.locator for item in matches)
        if not matches:
            diagnostics.append(
                ManagementAdmissionDiagnostic(
                    code="revision_target_missing",
                    identity=observation.identity,
                    message=(
                        "revision assertion names no uniquely identified "
                        "occurrence and selects no target"
                    ),
                    occurrences=(observation.locator,),
                )
            )
            continue
        if len(matches) != 1:
            diagnostics.append(
                ManagementAdmissionDiagnostic(
                    code="revision_target_ambiguous",
                    identity=observation.identity,
                    message=(
                        "revision assertion matches multiple occurrences and "
                        "selects no target"
                    ),
                    occurrences=(observation.locator,) + locators,
                )
            )
    diagnostics.sort(
        key=lambda item: (item.code, item.identity, item.occurrences)
    )
    return tuple(diagnostics)


def admit_management_documents(
    documents: tuple[BoundManagementDocument, ...],
    *,
    selected_store_facts: Iterable[Any] = (),
) -> ManagementAdmission:
    """Admit bound management observations as unreconciled audit facts."""
    if any(not document.ok for document in documents):
        raise ValueError("cannot admit management-KPI documents with binding errors")
    observations: list[ManagementObservation] = []
    definitions: list[ManagementKpiDefinition] = []
    totals: list[tuple[str, float, float, str]] = []
    for document in documents:
        definitions.extend(document.document.definitions)
        for index, item in enumerate(document.document.reported):
            observations.append(
                _observation_from_reported(item, bound=document, index=index)
            )
        store_observations, total, market_sum = _parse_store_counts(document)
        observations.extend(store_observations)
        total_obs = next(
            item for item in store_observations if item.kind == "store_count_total"
        )
        totals.append(
            (
                total_obs.locator,
                total,
                market_sum,
                _comparable_store_key(total_obs) or total_obs.identity,
            )
        )
        for index, item in enumerate(document.document.targets):
            observations.append(
                _observation_from_target(item, bound=document, index=index)
            )
    selected: list[tuple[str, float, str]] = []
    for fact in selected_store_facts:
        period = fact.period.isoformat() if hasattr(fact.period, "isoformat") else str(fact.period)
        selected.append(
            (
                period,
                float(fact.value),
                (
                    f"selected_operating_kpi:{fact.fact_type}:{period}:"
                    f"{fact.source_file}"
                ),
            )
        )
    ordered = tuple(
        sorted(
            observations,
            key=lambda item: (
                item.filing_year,
                item.kind,
                item.identity,
                item.locator,
            ),
        )
    )
    diagnostics = list(
        _classify_duplicates(
            ordered,
            store_totals_vs_markets=tuple(totals),
            selected_store_facts=tuple(selected),
        )
    )
    diagnostics.extend(_revision_target_diagnostics(ordered))
    from core.ingestion.management_kpi_enrichment import build_group_decisions
    from .management_kpi_identity import assess_reported_observations
    from .management_kpi_reconciliation import (
        SELECTION_DEFERRED,
        SELECTION_SELECTED,
        reconcile_group_selections,
        reconcile_reported_observations,
        reconcile_revision_links,
    )

    assessments = assess_reported_observations(ordered, documents)
    revision_links = reconcile_revision_links(ordered, assessments)
    group_selections = reconcile_group_selections(
        ordered, assessments, revision_links
    )
    selected_locators = tuple(
        item.selected.locator
        for item in group_selections
        if item.status == SELECTION_SELECTED and item.selected is not None
    )
    deferred_count = sum(
        1 for item in group_selections if item.status == SELECTION_DEFERRED
    )
    if deferred_count:
        diagnostics.append(
            ManagementAdmissionDiagnostic(
                code="deferred_canonical_selection",
                identity="management_kpi",
                message=(
                    f"{deferred_count} group(s) remain deferred after ordinary "
                    "or documentary-revision selection; general admission is "
                    "not complete"
                ),
                occurrences=tuple(
                    item.document.extraction_document for item in documents
                ),
            )
        )
    diagnostics.append(
        ManagementAdmissionDiagnostic(
            code="management_kpi_history_handoff",
            identity="management_kpi",
            message=(
                f"{len(selected_locators)} evidenced selected occurrence(s) are "
                "eligible for StandardizedFinancials history handoff; "
                f"{deferred_count} deferred group(s) remain audit-only"
            ),
            occurrences=selected_locators,
        )
    )
    diagnostics.sort(
        key=lambda item: (item.code, item.identity, item.occurrences)
    )
    return ManagementAdmission(
        status=_ADMISSION_UNRECONCILED,
        documents=documents,
        definitions=tuple(
            sorted(definitions, key=lambda item: (item.definition_id, item.metric_id))
        ),
        observations=ordered,
        diagnostics=tuple(diagnostics),
        assessments=assessments,
        reconciliation=reconcile_reported_observations(ordered, assessments),
        revision_links=revision_links,
        group_selections=group_selections,
        group_decisions=build_group_decisions(
            group_selections, assessments, ordered
        ),
    )


def management_admission_payload(admission: ManagementAdmission | None) -> dict[str, Any]:
    """Deterministic audit serialization for admitted management observations."""
    from .management_kpi_identity import assessments_payload
    from .management_kpi_reconciliation import reconciliation_payload

    if admission is None:
        return {
            "status": "absent",
            "document_count": 0,
            "reported_observation_count": 0,
            "definition_count": 0,
            "target_count": 0,
            "observations": [],
            "definitions": [],
            "diagnostics": [],
            "assessments": assessments_payload(()),
            "reconciliation": reconciliation_payload(()),
            "group_decisions": [],
            "unresolved": list(_REMAINING_UNRESOLVED),
        }
    reported = [
        item for item in admission.observations if item.kind == "reported_kpi"
    ]
    targets = [
        item for item in admission.observations if item.kind == "management_target"
    ]
    market_tables = [
        item
        for item in admission.observations
        if item.kind.startswith("store_count_")
    ]
    return {
        "status": admission.status,
        "canonical_selection": "deferred",
        "document_count": len(admission.documents),
        "reported_observation_count": len(reported),
        "definition_count": len(admission.definitions),
        "target_count": len(targets),
        "market_table_observation_count": len(market_tables),
        "unresolved": list(admission.unresolved),
        "documents": [
            {
                "extraction_document": item.document.extraction_document,
                "company": item.document.company,
                "ticker": item.document.ticker,
                "fiscal_year": item.document.fiscal_year,
                "fiscal_year_end": item.document.fiscal_year_end.isoformat(),
                "source_file": item.bound_source_file,
                "source_sha256": item.bound_source_sha256,
                "reporting_basis": item.document.reporting_basis,
                "extraction_policy": dict(item.document.extraction_policy),
                "assurance": _ASSURANCE_UNKNOWN,
                "presentation_role": _PRESENTATION_UNKNOWN,
                "physical_page_mapping": _PHYSICAL_PAGE_UNRESOLVED,
            }
            for item in admission.documents
        ],
        "definitions": [item.to_payload() for item in admission.definitions],
        "observations": [item.to_payload() for item in admission.observations],
        "diagnostics": [item.to_payload() for item in admission.diagnostics],
            "assessments": assessments_payload(admission.assessments),
            "reconciliation": reconciliation_payload(
                admission.reconciliation,
                revision_links=admission.revision_links,
                group_selections=admission.group_selections,
            ),
            "group_decisions": list(admission.group_decisions),
    }
