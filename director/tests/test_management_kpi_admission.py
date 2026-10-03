"""Mixed-directory management-KPI admission and source-binding controls."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
from datetime import date
from pathlib import Path

import pytest

from modeler.data.standardized_io import standardized_from_payload, standardized_to_payload
from director.ingestion.filing_cli import load_and_validate_extracted_dir
from extractor.data.filing_json import load_extracted_filing, load_extracted_json_object
from modeler.ingestion.filing_reconciler import reconcile_filings
from modeler.ingestion.filing_standardizer import (
    reconciliation_conflicts_payload,
    reconciliation_management_admission_payload,
    reconciliation_provenance_payload,
    standardize_reconciled,
)
from extractor.data.extracted_kind import (
    KIND_ANNUAL_FILING,
    KIND_MANAGEMENT_KPI,
    classify_extracted_payload,
)
from extractor.data.management_kpi_json import load_management_kpi_document
from modeler.operating_kpi import compute_operating_kpi_series
from modeler.period_axis import canonical_fiscal_periods
from modeler.tests.test_operating_kpi_analysis import _independent_from_counts
from modeler.tests.test_operating_kpi_facts import (
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

ROOT = Path(__file__).resolve().parents[2]
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


def test_cli_mixed_directory_writes_separate_admission_artifact(tmp_path: Path):
    import subprocess
    import sys

    mixed = _copy_json(ANNUAL_NAMES + MANAGEMENT_NAMES, tmp_path / "mixed")
    annual = _copy_json(ANNUAL_NAMES, tmp_path / "annual")
    mixed_out = tmp_path / "mixed-out"
    annual_out = tmp_path / "annual-out"
    before = _bytes_by_name(EXTRACTED)
    mixed_run = subprocess.run(
        [
            sys.executable,
            "-m",
            "core",
            "reconcile",
            str(mixed),
            "--source-root",
            str(SOURCE),
            "--admit-period",
            "2022-01-30",
            "-o",
            str(mixed_out),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    annual_run = subprocess.run(
        [
            sys.executable,
            "-m",
            "core",
            "reconcile",
            str(annual),
            "--source-root",
            str(SOURCE),
            "--admit-period",
            "2022-01-30",
            "-o",
            str(annual_out),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert mixed_run.returncode == 0, mixed_run.stdout + mixed_run.stderr
    assert annual_run.returncode == 0, annual_run.stdout + annual_run.stderr
    assert (mixed_out / "management_kpi_admission.json").is_file()
    assert not (annual_out / "management_kpi_admission.json").exists()
    mixed_std = json.loads((mixed_out / "standardized.json").read_text(encoding="utf-8"))
    annual_std = json.loads((annual_out / "standardized.json").read_text(encoding="utf-8"))
    assert _canonicalize(mixed_std) == _canonicalize(annual_std)
    admission = json.loads(
        (mixed_out / "management_kpi_admission.json").read_text(encoding="utf-8")
    )
    assert admission["reported_observation_count"] == 135
    assert admission["document_count"] == 4
    assert len(admission["assessments"]["items"]) == 135
    assert admission["assessments"]["canonical_selection"] == "deferred"
    assert admission["reconciliation"]["canonical_selection"] == "deferred"
    assert admission["reconciliation"]["selected_count"] == 0
    assert admission["reconciliation"]["superseded_count"] == 0
    assert admission["reconciliation"]["group_selection_counts"]["selected"] == 0
    assert admission["reconciliation"]["outcome_counts"]["agreeing_duplicate"] == 0
    assert admission["reconciliation"]["outcome_counts"]["conflicting_candidate"] == 0
    assert admission["status"] == "admitted_unreconciled"
    validate = subprocess.run(
        [
            sys.executable,
            "-m",
            "core",
            "validate-source",
            str(mixed),
            "--source-root",
            str(SOURCE),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert validate.returncode == 0, validate.stdout + validate.stderr
    assert "management-kpi documents: 4" in validate.stdout
    assert "validated 4 filing(s)" in validate.stdout
    assert _bytes_by_name(EXTRACTED) == before


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


def test_cli_serializes_occurrence_evidence(tmp_path: Path):
    import subprocess
    import sys

    dest = _copy_json(ANNUAL_NAMES + MANAGEMENT_NAMES, tmp_path / "cli")
    payload = json.loads((dest / MANAGEMENT_NAMES[1]).read_text(encoding="utf-8"))
    for item in payload["reported_kpis"]:
        if item.get("metric_id") == "comparable_sales_growth":
            _attach_presentation(item, "comparative")
            _attach_assurance(item, "audited")
        if item.get("metric_id") == "sales_per_square_foot":
            _attach_presentation(item, "prior")
            _attach_assurance(item, "unaudited")
    (dest / MANAGEMENT_NAMES[1]).write_text(json.dumps(payload), encoding="utf-8")
    out = tmp_path / "out"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "core",
            "reconcile",
            str(dest),
            "--source-root",
            str(SOURCE),
            "--admit-period",
            "2022-01-30",
            "-o",
            str(out),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    admission = json.loads((out / "management_kpi_admission.json").read_text(encoding="utf-8"))
    compsales = next(
        item
        for item in admission["observations"]
        if item["kind"] == "reported_kpi"
        and item["metric_id"] == "comparable_sales_growth"
        and item["filing_year"] == 2023
    )
    spsf = next(
        item
        for item in admission["observations"]
        if item["kind"] == "reported_kpi"
        and item["metric_id"] == "sales_per_square_foot"
        and item["filing_year"] == 2023
    )
    assert compsales["presentation_role"] == "comparative"
    assert compsales["assurance"] == "audited"
    assert spsf["presentation_role"] == "prior"
    assert spsf["assurance"] == "unaudited"
    assert spsf["presentation_role"] != "comparative"
    for item in admission["reconciliation"]["items"]:
        for occ in item["occurrences"]:
            assert "presentation_evidence" in occ
            assert "assurance_evidence" in occ
            assert "revision_evidence" in occ
        if item["kind"] == "pair":
            rel = item["presentation_relationship"]
            assert rel["combination"]
            assert [member["locator"] for member in rel["members"]] == item["locators"]
            for member, occ in zip(rel["members"], item["occurrences"]):
                assert member["role"] == occ["presentation_evidence"]["role"]
                assert member["occurrence_identity"] == occ["occurrence_identity"]
        else:
            assert "presentation_relationship" not in item
    assert all(
        item["assurance"] == "unknown" and item["presentation_role"] == "unknown"
        for item in admission["documents"]
    )
    assert admission["reconciliation"]["revision_links"] == []
    assert admission["reconciliation"]["revision_link_counts"]["recognized"] == 0


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

