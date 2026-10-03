"""Mixed-directory management-KPI admission and source-binding controls."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
from datetime import date
from pathlib import Path

import pytest

from bav.modeler.data.standardized_io import standardized_from_payload, standardized_to_payload
from bav.director.ingestion.filing_cli import load_and_validate_extracted_dir
from bav.extractor.data.filing_json import load_extracted_filing, load_extracted_json_object
from bav.modeler.ingestion.filing_reconciler import reconcile_filings
from bav.modeler.ingestion.filing_standardizer import (
    reconciliation_conflicts_payload,
    reconciliation_management_admission_payload,
    reconciliation_provenance_payload,
    standardize_reconciled,
)
from bav.extractor.data.extracted_kind import (
    KIND_ANNUAL_FILING,
    KIND_MANAGEMENT_KPI,
    classify_extracted_payload,
)
from bav.extractor.data.management_kpi_json import load_management_kpi_document
from bav.modeler.operating_kpi import compute_operating_kpi_series
from bav.modeler.period_axis import canonical_fiscal_periods
from bav.modeler.tests.test_operating_kpi_analysis import _independent_from_counts
from bav.modeler.tests.test_operating_kpi_facts import (
    ADMIT_2022,
    INDEPENDENT_STORE_TOTALS,
    P2022,
    P2023,
    P2024,
    P2025,
    P2026,
    _prepare_augmented,
    _validated_augmented,
)

ROOT = Path(__file__).resolve().parents[3]
BENCH = ROOT / "build" / "input" / "lululemon"
EXTRACTED = BENCH / "extracted"
SOURCE = BENCH / "source"
ANNUAL_NAMES = (
    "LULU_FY2022.json",
    "LULU_FY2023.json",
    "LULU_FY2024.json",
    "LULU_FY2025.json",
)
MANAGEMENT_NAMES = (
    "LULU_FY2022_management_kpis.json",
    "LULU_FY2023_management_kpis.json",
    "LULU_FY2024_management_kpis.json",
    "LULU_FY2025_management_kpis.json",
)
REPORTED_COUNTS = {2022: 29, 2023: 36, 2024: 37, 2025: 33}
STORE_TOTALS = {2022: 655, 2023: 711, 2024: 767, 2025: 811}


def _copy_json(names: tuple[str, ...], dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    for name in names:
        shutil.copy2(EXTRACTED / name, dest / name)
    return dest


def _bytes_by_name(directory: Path) -> dict[str, bytes]:
    return {
        path.name: path.read_bytes()
        for path in sorted(directory.glob("*.json"))
    }


def _canonicalize(payload: dict) -> dict:
    comparable = dict(payload)
    comparable.pop("historical_segment", None)
    comparable.pop("historical_operating_kpis", None)
    return comparable


def _statement_provenance(payload: dict) -> dict:
    comparable = dict(payload)
    comparable["note_facts"] = []
    comparable.pop("selected_geographic_segment_facts", None)
    comparable.pop("selected_operating_kpi_facts", None)
    return comparable


def test_directory_loader_no_longer_misparses_management_documents():
    for name in MANAGEMENT_NAMES:
        path = EXTRACTED / name
        payload = load_extracted_json_object(path)
        assert classify_extracted_payload(payload, path=path) == KIND_MANAGEMENT_KPI
        with pytest.raises(ValueError, match="company object is required"):
            load_extracted_filing(path)
        document = load_management_kpi_document(path)
        assert document.ticker == "LULU"
        assert document.fiscal_year == int(name.replace("LULU_FY", "").split("_")[0])

    mixed = load_and_validate_extracted_dir(EXTRACTED, source_root=SOURCE)
    assert len(mixed) == 4
    assert len(mixed.management_documents) == 4
    years = {filing.filing.fiscal_year for filing, _ in mixed}
    assert years == {2022, 2023, 2024, 2025}
    reported = []
    for bound in mixed.management_documents:
        reported.append(len(bound.document.reported))
        assert bound.ok
        assert bound.bound_source_sha256
        assert bound.bound_source_file.endswith("_Annual_Report.pdf")
    assert reported == [29, 36, 37, 33]


def test_dispatch_is_content_based_not_filename(tmp_path: Path):
    dest = tmp_path / "renamed"
    dest.mkdir()
    mapping = {
        "a-mgmt.json": MANAGEMENT_NAMES[0],
        "z-annual.json": ANNUAL_NAMES[0],
        "mid-mgmt.json": MANAGEMENT_NAMES[1],
        "mid-annual.json": ANNUAL_NAMES[1],
    }
    for dest_name, source_name in mapping.items():
        shutil.copy2(EXTRACTED / source_name, dest / dest_name)
    validated = load_and_validate_extracted_dir(dest, source_root=SOURCE)
    assert {filing.filing.fiscal_year for filing, _ in validated} == {2022, 2023}
    assert {item.document.fiscal_year for item in validated.management_documents} == {
        2022,
        2023,
    }
    for bound in validated.management_documents:
        assert bound.document.extraction_document.endswith(".json")
        assert bound.bound_source_file.startswith("LULU_FY")


@pytest.mark.parametrize(
    "mutate,match",
    [
        (lambda p: p.__setitem__("schema_version", "2.0"), "schema_version"),
        (lambda p: p.pop("reported_kpis"), "malformed management-KPI schema"),
        (lambda p: p.__setitem__("company", {"name": "x"}), "ambiguous"),
        (lambda p: p.__setitem__("filing", {"fiscal_year": 2022}), "ambiguous"),
    ],
)
def test_unknown_ambiguous_and_malformed_schemas_fail_closed(
    tmp_path: Path, mutate, match
):
    payload = json.loads((EXTRACTED / MANAGEMENT_NAMES[0]).read_text(encoding="utf-8"))
    original = copy.deepcopy(payload)
    mutate(payload)
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match=match):
        classify_extracted_payload(load_extracted_json_object(path), path=path)
        load_management_kpi_document(path)
    assert json.loads((EXTRACTED / MANAGEMENT_NAMES[0]).read_text(encoding="utf-8")) == original


def test_unknown_schema_fails_closed(tmp_path: Path):
    path = tmp_path / "unknown.json"
    path.write_text(json.dumps({"schema_version": "1.0", "x": 1}), encoding="utf-8")
    with pytest.raises(ValueError, match="unknown extracted schema"):
        classify_extracted_payload(load_extracted_json_object(path), path=path)


def test_malformed_values_and_dangling_definitions_fail_closed(tmp_path: Path):
    payload = json.loads((EXTRACTED / MANAGEMENT_NAMES[0]).read_text(encoding="utf-8"))
    original = copy.deepcopy(payload)
    payload["reported_kpis"][0]["value"] = "655"
    path = tmp_path / "bad-value.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="must be numeric"):
        load_management_kpi_document(path)

    payload = copy.deepcopy(original)
    payload["reported_kpis"][0]["definition_id"] = "missing_definition"
    path = tmp_path / "dangling.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="dangling definition_id"):
        load_management_kpi_document(path)
    assert json.loads((EXTRACTED / MANAGEMENT_NAMES[0]).read_text(encoding="utf-8")) == original


SUPPORTED_EVIDENCE_METRIC_IDS = (
    "comparable_sales_growth",
    "comparable_sales_growth_constant_dollar",
    "americas_comparable_sales_growth",
    "sales_per_square_foot",
)
PRESENTATION_ROLES = ("current", "comparative", "restated", "prior")
ASSURANCE_STATUSES = ("audited", "unaudited")
PRESENTATION_EVIDENCE = "MD&A presents this KPI in the stated role."
ASSURANCE_EVIDENCE = "The filing states this KPI's assurance in the cited section."
REVISION_EVIDENCE = "The later filing restates this previously reported KPI."


def _metric_items(payload: dict, metric_id: str) -> list[dict]:
    return [
        item
        for item in payload["reported_kpis"]
        if item.get("metric_id") == metric_id
    ]


def _printed_source(item: dict, source_file: str | None = None) -> dict:
    source = {
        "section": item["source"]["section"],
        "page_reference": item["source"]["page_reference"],
    }
    if source_file is not None:
        source["source_file"] = source_file
    return source


def _attach_presentation(
    item: dict,
    role: str | None,
    *,
    evidence: object = PRESENTATION_EVIDENCE,
    source_file: str | None = None,
    include_source: bool = True,
) -> dict:
    payload: dict[str, object] = {}
    if role is not None:
        payload["role"] = role
    if evidence is not Ellipsis:
        payload["evidence"] = evidence
    if include_source:
        payload["source"] = _printed_source(item, source_file)
    item["presentation"] = payload
    return item


def _attach_assurance(
    item: dict,
    status: str | None,
    *,
    evidence: object = ASSURANCE_EVIDENCE,
    source_file: str | None = None,
    include_source: bool = True,
) -> dict:
    payload: dict[str, object] = {}
    if status is not None:
        payload["status"] = status
    if evidence is not Ellipsis:
        payload["evidence"] = evidence
    if include_source:
        payload["source"] = _printed_source(item, source_file)
    item["assurance"] = payload
    return item


def _revision_target(item: dict, source_file: str, **overrides: str) -> dict[str, str]:
    target = {
        "metric_id": item["metric_id"],
        "period": item["period"],
        "source_file": source_file,
        "page_reference": item["source"]["page_reference"],
    }
    target.update(overrides)
    return target


def _attach_revision(
    item: dict,
    revises: dict | None,
    *,
    evidence: object = REVISION_EVIDENCE,
    source_file: str | None = None,
    include_source: bool = True,
) -> dict:
    payload: dict[str, object] = {}
    if revises is not None:
        payload["revises"] = revises
    if evidence is not Ellipsis:
        payload["evidence"] = evidence
    if include_source:
        payload["source"] = _printed_source(item, source_file)
    item["revision"] = payload
    return item


def _admit_mutated(tmp_path: Path, mutate, *, years: slice = slice(1, 2)) -> dict:
    dest = _copy_json(ANNUAL_NAMES[years] + MANAGEMENT_NAMES[years], tmp_path / "admit")
    original = json.loads(
        (EXTRACTED / MANAGEMENT_NAMES[years][0]).read_text(encoding="utf-8")
    )
    payload = mutate(copy.deepcopy(original))
    (dest / MANAGEMENT_NAMES[years][0]).write_text(json.dumps(payload), encoding="utf-8")
    admitted = reconciliation_management_admission_payload(
        reconcile_filings(load_and_validate_extracted_dir(dest, source_root=SOURCE))
    )
    assert json.loads(
        (EXTRACTED / MANAGEMENT_NAMES[years][0]).read_text(encoding="utf-8")
    ) == original
    return admitted


def _observation(payload: dict, metric_id: str) -> dict:
    matches = [
        item
        for item in payload["observations"]
        if item["kind"] == "reported_kpi" and item["metric_id"] == metric_id
    ]
    assert matches
    return matches[0]


def _set_named_revision_evidence(item: dict, blank: object) -> None:
    revision = item["revision"]
    if blank is Ellipsis:
        revision.pop("evidence", None)
    else:
        revision["evidence"] = blank


def _assessments_status(payload: dict, locator: str) -> str:
    return next(
        item["status"]
        for item in payload["assessments"]["items"]
        if item["locator"] == locator
    )

