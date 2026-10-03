"""Deterministic management-KPI enrichment transformations and group decisions.

Consumes Extractor documentary evidence. Does not parse PDFs or persist sidecars.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from extractor.data.extracted_kind import KIND_MANAGEMENT_KPI, classify_extracted_payload
from extractor.ingestion.management_kpi_enrichment import (
    FISCAL_CALENDAR_BASIS,
    CalendarYearEvidence,
    ComparisonWindowEvidence,
    MetricExclusionEvidence,
    SourceInspection,
    _calendar_for_occurrence_year,
    _definition_pages_and_text,
    _metric_exclusion_evidence,
    _metric_excludes_53rd_week,
    _occurrence_fiscal_year,
    _page_texts,
    _pages_containing_passage,
    _passage_binding,
    _passage_text,
    _printed_for_physical,
    _shift_rule_record,
    _window_applies_to_item,
    collect_calendar_corpus,
    definition_features,
    extract_comparison_window,
    extract_spsf_prior_period_levels,
    field_supporting_passages,
    format_physical_page_mapping,
    page_reference_from_printed,
    printed_pages_from_reference,
    resolve_physical_pages,
)
from modeler.ingestion.management_kpi_identity import (
    FAMILY_SALES_PER_SQUARE_FOOT,
    SUPPORTED_METRIC_MAPPINGS,
)

MappingLike = dict[str, Any]

CAUSE_SOURCE_ABSENCE = "genuine_source_absence"


CAUSE_AMBIGUITY = "documentary_ambiguity"


CAUSE_SELECTION = "selection_limitation"


CAUSE_IMPLEMENTATION = "implementation_defect"


CAUSE_ACCESS = "unavailable_access"


DEFINITION_EQUIVALENT = "equivalent"


DEFINITION_DIFFERENT = "different"


DEFINITION_UNRESOLVED = "unresolved"


def assess_definition_equivalence(left: str, right: str) -> str:
    """Compare disclosed definition features without overwriting either text."""
    if not str(left).strip() or not str(right).strip():
        return DEFINITION_UNRESOLVED
    if str(left).strip() == str(right).strip():
        return DEFINITION_EQUIVALENT
    left_features = definition_features(left)
    right_features = definition_features(right)
    if not left_features or not right_features:
        return DEFINITION_UNRESOLVED
    shared = set(left_features) & set(right_features)
    if not shared:
        return DEFINITION_UNRESOLVED
    if any(left_features[key] != right_features[key] for key in shared):
        return DEFINITION_DIFFERENT
    return DEFINITION_EQUIVALENT


def _focus_item(item: MappingLike) -> bool:
    return isinstance(item.get("metric_id"), str) and item["metric_id"] in SUPPORTED_METRIC_MAPPINGS


def _existing_spsf_periods(items: Iterable[MappingLike]) -> set[str]:
    keys: set[str] = set()
    for item in items:
        if item.get("metric_id") != "sales_per_square_foot":
            continue
        keys.add(str(item.get("period") or ""))
        label = str(item.get("original_period_label") or "")
        if label:
            keys.add(label)
        period = str(item.get("period") or "")
        if period.startswith("FY"):
            keys.add(period)
    return keys


def _append_traced_spsf_occurrences(
    payload: dict[str, Any],
    levels: Sequence[dict[str, Any]],
    *,
    fiscal_year: int,
    year_end_map: Mapping[int, str],
    calendar_corpus: dict[int, CalendarYearEvidence],
    inspection: SourceInspection,
) -> list[dict[str, Any]]:
    """Add prior-period SPSF levels as documentary occurrences; do not invent revisions."""
    from copy import deepcopy

    items = payload.setdefault("reported_kpis", [])
    template = next(
        (
            item
            for item in items
            if isinstance(item, dict) and item.get("metric_id") == "sales_per_square_foot"
        ),
        None,
    )
    if template is None:
        return []
    existing = _existing_spsf_periods(items)
    added: list[dict[str, Any]] = []
    for level in levels:
        year = int(level["period_label"])
        if year == fiscal_year:
            continue
        period = year_end_map.get(year, "")
        fy_label = f"FY{year}"
        if not period:
            continue
        if period in existing or fy_label in existing or str(year) in existing:
            continue
        item = deepcopy(template)
        item["period"] = period
        item["original_period_label"] = fy_label
        item["value"] = level["value"]
        item.pop("comparison", None)
        item.pop("revision", None)
        item.pop("revises", None)
        item.pop("supporting_evidence", None)
        source = dict(item.get("source") or {})
        source["source_file"] = inspection.source_file
        item["source"] = source
        qualifiers = dict(item.get("qualifiers") or {})
        qualifiers.pop("excludes_53rd_week", None)
        item["qualifiers"] = qualifiers
        item["presentation"] = {
            "role": level["presentation_role"],
            "evidence": level["passage"],
            "source": {
                "section": source.get("section", ""),
                "page_reference": source.get("page_reference", ""),
                "source_file": inspection.source_file,
            },
        }
        item["traced_prior_period"] = True
        items.append(item)
        existing.add(period)
        existing.add(fy_label)
        added.append(item)
    return added


def enrich_management_payload(
    payload: dict[str, Any],
    inspection: SourceInspection,
    *,
    extraction_document: str,
    calendar_corpus: dict[int, CalendarYearEvidence] | None = None,
    year_end_map: Mapping[int, str] | None = None,
    exclusion_corpus: Mapping[tuple[str, int], MetricExclusionEvidence] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return an enriched working copy and the page-resolution record."""
    if classify_extracted_payload(payload, path=extraction_document) != KIND_MANAGEMENT_KPI:
        raise ValueError(f"{extraction_document}: not a management-KPI document")
    enriched = json.loads(json.dumps(payload))
    report = enriched["report"]
    fiscal_year = int(report["fiscal_year"])
    fiscal_year_end = str(report["fiscal_year_end"])
    expected_label = f"FY{fiscal_year}"
    original_basis = report.get("reporting_basis", "")
    if inspection.fiscal_calendar_evidenced:
        if "original_reporting_basis" not in report:
            report["original_reporting_basis"] = original_basis
        report["reporting_basis"] = FISCAL_CALENDAR_BASIS
    corpus = calendar_corpus or collect_calendar_corpus({inspection.source_file: inspection})
    ends_by_year = dict(year_end_map or {})
    ends_by_year.setdefault(fiscal_year, fiscal_year_end)
    filing_window = extract_comparison_window(inspection)
    spsf_levels = extract_spsf_prior_period_levels(inspection)
    _append_traced_spsf_occurrences(
        enriched,
        spsf_levels,
        fiscal_year=fiscal_year,
        year_end_map=ends_by_year,
        calendar_corpus=corpus,
        inspection=inspection,
    )
    fields: list[dict[str, Any]] = []
    for item in enriched["reported_kpis"]:
        if not _focus_item(item):
            continue
        source = item.get("source") or {}
        page_reference = str(source.get("page_reference") or "")
        physical_pages = resolve_physical_pages(page_reference, inspection)
        printed = printed_pages_from_reference(page_reference)
        definition_pages, definition_text = _definition_pages_and_text(
            enriched,
            inspection,
            str(item["metric_id"]),
            definition_id=str(item.get("definition_id") or ""),
        )
        original_period = str(item.get("period") or "")
        if original_period == expected_label:
            item["original_period_label"] = original_period
            item["period"] = fiscal_year_end
        occurrence_year = _occurrence_fiscal_year(
            item, filing_year=fiscal_year, year_end_map=ends_by_year
        )
        calendar = _calendar_for_occurrence_year(occurrence_year, inspection, corpus)
        item_window = _window_applies_to_item(
            filing_window,
            item,
            occurrence_year=occurrence_year,
            filing_year=fiscal_year,
        )
        extra_pages = list(definition_pages)
        if calendar is not None and calendar.source_file == inspection.source_file:
            extra_pages.append(calendar.physical_page)
        if item_window is not None:
            extra_pages.extend(item_window.physical_pages)
        extra_texts = _page_texts(inspection, extra_pages)
        if calendar is not None and calendar.cross_filing:
            extra_texts.append(calendar.passage)
        exclusion = _metric_exclusion_evidence(
            str(item["metric_id"]),
            calendar,
            list(extra_texts) + _page_texts(inspection, physical_pages),
            corpus=exclusion_corpus,
            presenting_source=inspection.source_file,
        )
        week_excluded = _metric_excludes_53rd_week(
            str(item["metric_id"]),
            calendar,
            [exclusion.passage] if exclusion is not None else (),
        )
        qualifiers = item.get("qualifiers")
        if not isinstance(qualifiers, dict):
            qualifiers = {}
            item["qualifiers"] = qualifiers
        if "excludes_53rd_week" not in qualifiers and week_excluded is not None:
            qualifiers["excludes_53rd_week"] = week_excluded
        passages = field_supporting_passages(
            inspection=inspection,
            physical_pages=physical_pages,
            extra_texts=extra_texts,
            item=item,
            comparison_window=item_window,
            calendar=calendar,
            fiscal_year_end=str(item.get("period") or fiscal_year_end),
        )
        mapping = format_physical_page_mapping(printed, physical_pages)
        passage_bindings: dict[str, dict[str, Any]] = {}
        for field_name, passage in passages.items():
            if field_name == "calendar" and calendar is not None:
                passage_bindings[field_name] = _passage_binding(
                    source_file=calendar.source_file,
                    physical_pages=(calendar.physical_page,) if calendar.physical_page else (),
                    printed_pages=_printed_for_physical(
                        inspection, (calendar.physical_page,)
                    )
                    if calendar.source_file == inspection.source_file
                    else (),
                    cross_filing=calendar.cross_filing,
                )
                continue
            if field_name == "comparison_window" and item_window is not None:
                passage_bindings[field_name] = _passage_binding(
                    source_file=item_window.source_file,
                    physical_pages=item_window.physical_pages,
                    printed_pages=_printed_for_physical(
                        inspection, item_window.physical_pages
                    ),
                )
                continue
            pages = _pages_containing_passage(
                inspection,
                passage,
                physical_pages=tuple(physical_pages) + tuple(extra_pages),
            )
            if not pages:
                pages = _pages_containing_passage(inspection, passage)
            passage_bindings[field_name] = _passage_binding(
                source_file=inspection.source_file,
                physical_pages=pages,
                printed_pages=_printed_for_physical(inspection, pages),
            )
        exclusion_record = None
        if exclusion is not None:
            passages["metric_exclusion"] = exclusion.passage
            passage_bindings["metric_exclusion"] = _passage_binding(
                source_file=exclusion.source_file,
                physical_pages=exclusion.physical_pages,
                printed_pages=exclusion.printed_pages,
                cross_filing=exclusion.cross_filing,
            )
            exclusion_record = {
                "metric_id": item["metric_id"],
                "metric_key": exclusion.metric_key,
                "period": item.get("period"),
                "fiscal_year": exclusion.fiscal_year,
                "source_file": exclusion.source_file,
                "physical_pages": list(exclusion.physical_pages),
                "printed_pages": list(exclusion.printed_pages),
                "passage": exclusion.passage,
                "cross_filing": exclusion.cross_filing,
            }
        supporting = {
            "printed_pages": list(printed),
            "physical_pages": list(physical_pages),
            "source_file": inspection.source_file,
            "page_mapping": mapping,
            "passages": passages,
            "passage_bindings": passage_bindings,
            "fiscal_year_length_weeks": (
                53 if calendar is not None and calendar.fifty_three_week else
                52 if calendar is not None else None
            ),
            "metric_excludes_53rd_week": week_excluded,
            "metric_exclusion": exclusion_record,
            "comparison_window": (
                None
                if item_window is None
                else {
                    "label": item_window.label,
                    "current_weeks": item_window.current_weeks,
                    "prior_weeks": item_window.prior_weeks,
                    "not_compared_to": item_window.not_compared_to,
                    "subsequent_year_shift_rule": False,
                    "source_file": item_window.source_file,
                    "physical_pages": list(item_window.physical_pages),
                    "passage": item_window.passage,
                }
            ),
            "subsequent_year_shift_rule": _shift_rule_record(filing_window),
            "calendar_provenance": (
                None
                if calendar is None
                else {
                    "source_file": calendar.source_file,
                    "physical_page": calendar.physical_page,
                    "cross_filing": calendar.cross_filing,
                    "passage": calendar.passage,
                    "fifty_three_week": calendar.fifty_three_week,
                }
            ),
            "definition_features": definition_features(
                definition_text or passages.get("definition", "")
            ),
            "prior_period_levels": (
                spsf_levels
                if item["metric_id"] in SUPPORTED_METRIC_MAPPINGS
                and SUPPORTED_METRIC_MAPPINGS[item["metric_id"]].family
                == FAMILY_SALES_PER_SQUARE_FOOT
                else []
            ),
        }
        item["supporting_evidence"] = supporting
        presentation_passage = passages.get("presentation") or ""
        if item.get("traced_prior_period") and not presentation_passage:
            presentation_passage = next(
                (
                    str(level["passage"])
                    for level in spsf_levels
                    if level["value"] == item.get("value")
                    and level["presentation_role"] == "prior"
                ),
                "",
            )
        if presentation_passage and "presentation" not in item:
            presentation_binding = passage_bindings.get("presentation") or {}
            presentation_printed = tuple(presentation_binding.get("printed_pages") or ())
            presentation_ref = page_reference_from_printed(presentation_printed) or page_reference
            item["presentation"] = {
                "role": "prior" if item.get("traced_prior_period") else "current",
                "evidence": presentation_passage,
                "source": {
                    "section": source.get("section", ""),
                    "page_reference": presentation_ref,
                    "source_file": inspection.source_file,
                },
            }
        fields.append(
            {
                "extraction_document": extraction_document,
                "metric_id": item["metric_id"],
                "period": item.get("period"),
                "original_period_label": item.get("original_period_label", original_period),
                "page_reference": page_reference,
                "printed_pages": list(printed),
                "physical_pages": list(physical_pages),
                "page_mapping": mapping,
                "supporting_passages": passages,
                "passage_bindings": passage_bindings,
                "calendar_week_excluded": week_excluded,
                "fiscal_year_length_weeks": supporting["fiscal_year_length_weeks"],
                "comparison_window": supporting["comparison_window"],
                "calendar_provenance": supporting["calendar_provenance"],
                "metric_exclusion": exclusion_record,
                "definition_features": supporting["definition_features"],
                "prior_period_levels": supporting["prior_period_levels"],
            }
        )
    record = {
        "extraction_document": extraction_document,
        "source_file": inspection.source_file,
        "fiscal_year": fiscal_year,
        "fiscal_year_end": fiscal_year_end,
        "fiscal_calendar_evidenced": inspection.fiscal_calendar_evidenced,
        "fifty_three_week_years": list(inspection.fifty_three_week_years),
        "fifty_two_week_years": list(inspection.fifty_two_week_years),
        "printed_to_physical": {
            str(printed): physical
            for printed, physical in sorted(inspection.printed_to_physical.items())
        },
        "fields": fields,
    }
    return enriched, record


_FAILURE_REMAINING = {
    "calendar_mismatch": (
        "calendar",
        CAUSE_AMBIGUITY,
        "aligned fiscal-year length and metric-specific 53rd-week treatment across the comparison pair",
    ),
    "comparison_window_mismatch": (
        "comparison_window",
        CAUSE_AMBIGUITY,
        "the same disclosed comparison window, or an explicit statement that no completed window applies",
    ),
    "calendar_reporting_mismatch": (
        "calendar_reporting_basis",
        CAUSE_AMBIGUITY,
        "the same documentary fiscal-calendar reporting basis",
    ),
    "definition_mismatch": (
        "definition",
        CAUSE_AMBIGUITY,
        "documentary equivalence of store-only, total-comparable, geographic, population and currency bases",
    ),
    "population_mismatch": (
        "definition",
        CAUSE_AMBIGUITY,
        "the same disclosed population basis",
    ),
    "missing_comparison": (
        "historical_comparison",
        CAUSE_SOURCE_ABSENCE,
        "a disclosed historical comparison observation with its actual comparison window",
    ),
    "peer_missing_comparison": (
        "historical_comparison",
        CAUSE_SOURCE_ABSENCE,
        "a peer occurrence that itself discloses a historical comparison window",
    ),
    "no_distinct_peer": (
        "historical_comparison",
        CAUSE_AMBIGUITY,
        "a distinct same-identity peer year with aligned calendar, window and definition evidence",
    ),
    "period_date": (
        "period_date",
        CAUSE_SOURCE_ABSENCE,
        "a complete documentary period-end date sentence or table row",
    ),
    "calendar_week_adjustment": (
        "calendar_week_adjustment",
        CAUSE_SOURCE_ABSENCE,
        "a disclosed 52/53-week treatment for this fiscal year",
    ),
    "presentation_role": (
        "presentation",
        CAUSE_SOURCE_ABSENCE,
        "a documentary presentation-role passage bound to this occurrence",
    ),
    "assurance": (
        "assurance",
        CAUSE_SELECTION,
        "documentary audited KPI assurance; annual-report placement is not sufficient",
    ),
    "revision": (
        "revision",
        CAUSE_SELECTION,
        "a documentary revision link; repetition of a prior-period level is not a revision",
    ),
    "canonical_selection": (
        "canonical_selection",
        CAUSE_SELECTION,
        "ordinary occurrence admission or a complete documentary revision selection",
    ),
}


def _supporting_dict(observation: Any) -> dict[str, Any]:
    supporting: dict[str, Any] = {}
    for key, raw in getattr(observation, "supporting_evidence", ()):
        try:
            supporting[key] = json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            supporting[key] = raw
    return supporting


def _document_pages(supporting: Mapping[str, Any]) -> list[int]:
    pages = [int(page) for page in supporting.get("physical_pages") or []]
    provenance = supporting.get("calendar_provenance") or {}
    if provenance.get("physical_page"):
        pages.append(int(provenance["physical_page"]))
    window = supporting.get("comparison_window") or {}
    pages.extend(int(page) for page in window.get("physical_pages") or [])
    exclusion = supporting.get("metric_exclusion") or {}
    pages.extend(int(page) for page in exclusion.get("physical_pages") or [])
    bindings = supporting.get("passage_bindings") or {}
    for field_name in ("presentation", "management_use"):
        binding = bindings.get(field_name) or {}
        pages.extend(int(page) for page in binding.get("physical_pages") or [])
    return pages


def _failure_record(
    *,
    requirement: str,
    cause: str,
    remaining: str,
    locator: str = "",
    peer: str = "",
    document: str = "",
    pages: Iterable[int] = (),
    passage: str = "",
    detail: str = "",
) -> dict[str, Any]:
    record = {
        "requirement": requirement,
        "cause": cause,
        "remaining_requirement": remaining,
        "detail": detail,
    }
    if locator:
        record["locator"] = locator
    if peer:
        record["comparison_pair"] = [locator, peer] if locator else [peer]
    if document:
        record["document"] = document
    if pages:
        record["pages"] = sorted(set(int(page) for page in pages))
    if passage:
        record["passage"] = passage
    return record


def _pair_failure_mapping(reason: str) -> tuple[str, str, str] | None:
    mapped = _FAILURE_REMAINING.get(reason)
    if mapped is not None:
        return mapped
    from modeler.ingestion.management_kpi_identity import COMPARISON_CONFLICT_REASONS

    if reason in COMPARISON_CONFLICT_REASONS:
        return (
            reason,
            CAUSE_AMBIGUITY,
            "aligned documentary evidence for this comparison pair",
        )
    return None


def build_group_decisions(
    group_selections: Iterable[Any],
    assessments: Iterable[Any],
    observations: Iterable[Any],
) -> tuple[dict[str, Any], ...]:
    """Reproducible per-group documentary decisions for admission review."""
    from modeler.ingestion.management_kpi_identity import (
        FAMILY_SALES_PER_SQUARE_FOOT,
        HISTORICAL_COMPARISON_ELIGIBLE,
        LEVEL_ADMITTED,
        PAIR_KIND_HISTORICAL,
        PAIR_SUPPORTED,
        REASON_MISSING_COMPARISON,
        REASON_PERIOD_MISMATCH,
        REQUIRED_COMPARISON_REASONS,
    )
    from .management_kpi_reconciliation import (
        REASON_ORDINARY_DISAGREEMENT,
        REASON_SINGLETON,
        REVISION_ROUTE_REASONS,
        SELECTION_SELECTED,
    )

    by_locator = {item.locator: item for item in observations}
    by_assessment = {item.locator: item for item in assessments}
    pair_by_key: dict[tuple[str, str], Any] = {}
    for assessment in assessments:
        for pair in getattr(assessment, "pair_assessments", ()) or ():
            pair_by_key[tuple(pair.locators)] = pair
    decisions: list[dict[str, Any]] = []
    for group in group_selections:
        locators = [item.locator for item in group.occurrences]
        locator_set = set(locators)
        consumed: list[str] = []
        satisfied: list[str] = []
        pages: list[int] = []
        failures: list[dict[str, Any]] = []
        seen_failures: set[tuple[str, str, str, str]] = set()
        level_states: list[str] = []
        comparison_states: list[str] = []
        for locator in locators:
            observation = by_locator.get(locator)
            assessment = by_assessment.get(locator)
            if observation is None:
                continue
            consumed.append(locator)
            supporting = _supporting_dict(observation)
            occurrence_pages = _document_pages(supporting)
            pages.extend(occurrence_pages)
            passages = supporting.get("passages") or {}
            bindings = supporting.get("passage_bindings") or {}
            document = observation.extraction_document
            unresolved_obs = set(getattr(observation, "unresolved", ()) or ())
            if assessment is not None:
                evidence = dict(assessment.evidence)
                if evidence.get("period_kind") == "date":
                    satisfied.append("period_date")
                if evidence.get("calendar_week_adjustment"):
                    satisfied.append("calendar_week_adjustment")
                if evidence.get("calendar_reporting_basis"):
                    satisfied.append("calendar_reporting_basis")
                if evidence.get("definition_text"):
                    satisfied.append("definition")
                if getattr(observation.source, "physical_page_mapping", "") not in (
                    "",
                    "unresolved",
                ):
                    satisfied.append("physical_page_mapping")
                if assessment.level_admission == LEVEL_ADMITTED:
                    satisfied.append("level_admission")
                level_states.append(assessment.level_admission)
                comparison_states.append(assessment.historical_comparison)
                occurrence_reasons = [
                    reason
                    for reason in assessment.unresolved_reasons
                    if reason in REQUIRED_COMPARISON_REASONS
                    or reason
                    in {
                        "presentation_role",
                        "assurance",
                        "revision",
                    }
                ]
                for reason in occurrence_reasons:
                    mapped = _FAILURE_REMAINING.get(reason)
                    if mapped is None:
                        continue
                    requirement, cause, remaining = mapped
                    key = ("occurrence", locator, requirement, reason)
                    if key in seen_failures:
                        continue
                    seen_failures.add(key)
                    field_name = {
                        "comparison_window": "comparison_window",
                        "calendar": "calendar",
                        "definition": "definition",
                        "period_date": "dates",
                        "historical_comparison": "value",
                        "presentation": "presentation",
                    }.get(requirement, "")
                    passage = _passage_text(passages.get(field_name)) if field_name else ""
                    binding = bindings.get(field_name) or {}
                    failure_document = str(binding.get("source_file") or document)
                    failure_pages = [
                        int(page) for page in binding.get("physical_pages") or []
                    ] or occurrence_pages
                    failures.append(
                        _failure_record(
                            requirement=requirement,
                            cause=cause,
                            remaining=remaining,
                            locator=locator,
                            document=failure_document,
                            pages=failure_pages,
                            passage=passage,
                            detail=reason,
                        )
                    )
            for reason in ("presentation_role", "assurance", "revision"):
                if reason not in unresolved_obs:
                    continue
                mapped = _FAILURE_REMAINING[reason]
                key = ("occurrence", locator, mapped[0], reason)
                if key in seen_failures:
                    continue
                seen_failures.add(key)
                failures.append(
                    _failure_record(
                        requirement=mapped[0],
                        cause=mapped[1],
                        remaining=mapped[2],
                        locator=locator,
                        document=document,
                        pages=occurrence_pages,
                        passage=str(passages.get(mapped[0], "")),
                        detail=reason,
                    )
                )
        for pair in sorted(pair_by_key.values(), key=lambda item: item.locators):
            if not locator_set.intersection(pair.locators):
                continue
            if pair.outcome == PAIR_SUPPORTED:
                continue
            for reason in pair.reasons:
                if reason == REASON_PERIOD_MISMATCH and pair.kind == PAIR_KIND_HISTORICAL:
                    continue
                mapped = _pair_failure_mapping(reason)
                if mapped is None:
                    continue
                requirement, cause, remaining = mapped
                key = ("pair", pair.locators[0], pair.locators[1], f"{requirement}:{reason}")
                if key in seen_failures:
                    continue
                seen_failures.add(key)
                left = by_locator.get(pair.locators[0])
                right = by_locator.get(pair.locators[1])
                left_support = _supporting_dict(left) if left is not None else {}
                right_support = _supporting_dict(right) if right is not None else {}
                field_name = {
                    "comparison_window": "comparison_window",
                    "calendar": "calendar",
                    "definition": "definition",
                    "period_date": "dates",
                    "historical_comparison": "value",
                    "presentation": "presentation",
                }.get(requirement, "")
                left_bindings = left_support.get("passage_bindings") or {}
                right_bindings = right_support.get("passage_bindings") or {}
                binding = left_bindings.get(field_name) or right_bindings.get(field_name) or {}
                left_passages = left_support.get("passages") or {}
                right_passages = right_support.get("passages") or {}
                passage = _passage_text(
                    left_passages.get(field_name) or right_passages.get(field_name)
                )
                pair_pages = list(_document_pages(left_support)) + list(
                    _document_pages(right_support)
                )
                failure_pages = [
                    int(page) for page in binding.get("physical_pages") or []
                ] or pair_pages
                failures.append(
                    _failure_record(
                        requirement=requirement,
                        cause=cause,
                        remaining=remaining,
                        locator=pair.locators[0],
                        peer=pair.locators[1],
                        document=str(
                            binding.get("source_file")
                            or (left.extraction_document if left is not None else "")
                        ),
                        pages=failure_pages,
                        passage=passage,
                        detail=reason,
                    )
                )
        reasons = list(group.reasons)
        additional = ""
        unresolved_decision = ""
        primary = ""
        revision_route = bool(REVISION_ROUTE_REASONS & set(reasons)) or REASON_SINGLETON in reasons
        if group.status == SELECTION_SELECTED or not revision_route:
            failures = [
                item
                for item in failures
                if item.get("requirement") not in {"assurance", "revision"}
            ]
        if group.status != SELECTION_SELECTED:
            if reasons:
                primary = CAUSE_SELECTION
                if revision_route:
                    unresolved_decision = (
                        "later-audited two-occurrence revision group with a "
                        "documentary revision link"
                    )
                elif REASON_ORDINARY_DISAGREEMENT in reasons:
                    unresolved_decision = (
                        "agreement on value and identity, definition, population, "
                        "units, currency basis and calendar semantics"
                    )
                else:
                    unresolved_decision = _FAILURE_REMAINING["canonical_selection"][2]
                failures.append(
                    _failure_record(
                        requirement="canonical_selection",
                        cause=CAUSE_SELECTION,
                        remaining=unresolved_decision,
                        detail=", ".join(reasons),
                        pages=pages,
                    )
                )
        group_pairs = [
            pair
            for pair in pair_by_key.values()
            if locator_set.intersection(pair.locators)
        ]
        historical_pairs = [
            pair for pair in group_pairs if pair.kind == PAIR_KIND_HISTORICAL
        ]
        supported_historical = [
            pair for pair in historical_pairs if pair.outcome == PAIR_SUPPORTED
        ]
        comparison_missing = any(
            REASON_MISSING_COMPARISON
            in getattr(by_assessment.get(locator), "unresolved_reasons", ())
            for locator in locators
        )
        alignment_conflicts = [
            item
            for item in failures
            if item["requirement"] in {"calendar", "comparison_window", "definition"}
            and item.get("comparison_pair")
        ]
        same_identity_peers = any(
            getattr(by_assessment.get(locator), "peer_locators", ())
            for locator in locators
        )
        if (
            comparison_missing
            and group.family == FAMILY_SALES_PER_SQUARE_FOOT
            and not supported_historical
        ):
            if same_identity_peers and alignment_conflicts:
                additional = ""
                rewritten: list[dict[str, Any]] = []
                for item in failures:
                    if (
                        item["requirement"] == "historical_comparison"
                        and item.get("cause") == CAUSE_SOURCE_ABSENCE
                        and not item.get("comparison_pair")
                    ):
                        rewritten.append(
                            {
                                **item,
                                "cause": CAUSE_AMBIGUITY,
                                "remaining_requirement": (
                                    "aligned same-identity levels that satisfy existing "
                                    "calendar, window and definition comparison rules"
                                ),
                                "detail": "same_identity_levels_not_aligned",
                            }
                        )
                    else:
                        rewritten.append(item)
                failures = rewritten
                if not any(
                    item["requirement"] == "historical_comparison" for item in failures
                ):
                    failures.append(
                        _failure_record(
                            requirement="historical_comparison",
                            cause=CAUSE_AMBIGUITY,
                            remaining=(
                                "aligned same-identity levels that satisfy existing "
                                "calendar, window and definition comparison rules"
                            ),
                            detail="same_identity_levels_not_aligned",
                            pages=pages,
                        )
                    )
            elif not historical_pairs:
                additional = _FAILURE_REMAINING["missing_comparison"][2]
                if not any(
                    item["requirement"] == "historical_comparison"
                    and item.get("cause") == CAUSE_SOURCE_ABSENCE
                    for item in failures
                ):
                    failures.append(
                        _failure_record(
                            requirement="historical_comparison",
                            cause=CAUSE_SOURCE_ABSENCE,
                            remaining=additional,
                            detail=REASON_MISSING_COMPARISON,
                            pages=pages,
                        )
                    )
                if not primary:
                    primary = CAUSE_SOURCE_ABSENCE
        if not primary and group.status != SELECTION_SELECTED:
            primary = CAUSE_AMBIGUITY
            unresolved_decision = "group remains deferred"
        level_eligibility = (
            LEVEL_ADMITTED
            if level_states and all(state == LEVEL_ADMITTED for state in level_states)
            else "deferred"
        )
        comparison_eligibility = (
            HISTORICAL_COMPARISON_ELIGIBLE
            if any(state == HISTORICAL_COMPARISON_ELIGIBLE for state in comparison_states)
            or supported_historical
            else "ineligible"
        )
        if comparison_eligibility == HISTORICAL_COMPARISON_ELIGIBLE:
            satisfied.append("historical_comparison")
        satisfied = sorted(set(satisfied))
        if comparison_eligibility != HISTORICAL_COMPARISON_ELIGIBLE:
            satisfied = [item for item in satisfied if item != "historical_comparison"]
        decisions.append(
            {
                "family": group.family,
                "metric_identity": group.metric_identity,
                "period": group.period,
                "status": group.status,
                "canonical_selection": group.status,
                "level_eligibility": level_eligibility,
                "comparison_eligibility": comparison_eligibility,
                "locators": locators,
                "evidence_consumed": consumed,
                "requirements_satisfied": satisfied,
                "remaining_failures": failures,
                "pair_assessments": [
                    pair.to_payload()
                    for pair in sorted(group_pairs, key=lambda item: item.locators)
                ],
                "cause": primary or (CAUSE_SELECTION if group.status != SELECTION_SELECTED else ""),
                "pages_searched": sorted(set(pages)),
                "additional_evidence_needed": additional,
                "unresolved_decision": unresolved_decision,
                "selection_reasons": reasons,
            }
        )
    decisions.sort(
        key=lambda item: (
            item["family"],
            item["metric_identity"],
            item["period"],
            tuple(item["locators"]),
        )
    )
    return tuple(decisions)
