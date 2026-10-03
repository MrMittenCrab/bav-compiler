"""Gated opt-in normalization candidate handoff (Step 9M.2.4.1.1.1.68)."""

from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
from datetime import date
from pathlib import Path

import pytest

from extractor.data.filing_json import load_extracted_filing
from extractor.data.filing_validator import source_row_identity
from modeler.data.historical_segments import SEGMENT_BRIDGE_TOLERANCE
from modeler.data.line_identity import line_identity
from modeler.data.standardized_io import standardized_from_payload, standardized_to_payload
from core.ingestion.normalization_candidate_admission import (
    ANALYTICAL_CONCEPT,
    ANALYTICAL_LABEL,
    ANALYTICAL_SELECTOR,
    AUTHORIZED_IS_IDENTITIES,
    AUTHORIZATION_SYNTHETIC,
    CF_AUDIT_IDENTITIES,
    LEDGER_PERIODS,
    SIGN_TRANSFORMATION,
    AdoptionRecord,
    TreatmentRecord,
    construct_provisional_candidate,
    run_normalization_candidate_handoff,
)
from modeler.financial_math import AnchorMetrics, HistoricalSeries
from core.model.normalization import (
    SUPPORTED_NORMALIZATION_SCOPE,
    compute_normalization_series,
    normalization_cases,
    resolve_income_statement_selector,
)
from modeler.period_axis import canonical_fiscal_periods
from modeler.ratio_values import UNDEFINED_RATIO

ROOT = Path(__file__).resolve().parents[2]
COMPARISON_B = "eb65dc63845b940162c48e39ae9af7598d2a3078"
REVIEWED_CHECKPOINT = "38f5774170c577aa10eb5f03c4cbe99ed7cff789"
AUTHENTICATED_B = "95efb965cd896e462814459b843d9a992358c7a9"
REVIEWED_CHECKPOINT_1091 = "1a82323aac1309141f480e550277ffb2f56b35ca"
REVIEWED_BASELINE_1091 = "250d57178d4b32b3b12a13ba9a08677789d59183"
REQUIRED_PROVENANCE_FIELDS = (
    "observation_fingerprints",
    "source_hashes",
    "physical_pages",
    "printed_pages",
    "row_identities",
    "transformation",
    "sign_conversions_applied",
    "face_reported_usd_thousands",
)
LIVE_DIR = ROOT / "build" / "input" / "lululemon" / "evidence" / "prior-live"
EXTRACTED_DIR = ROOT / "build" / "input" / "lululemon" / "extracted"
SOURCE_DIR = ROOT / "build" / "input" / "lululemon" / "source"
RECONCILED_STD = ROOT / "build" / "input" / "lululemon" / "reconciled" / "standardized.json"
ORDINARY_DIR = ROOT / "core" / "tests" / "fixtures" / "ordinary_reconcile" / "lululemon"
ORDINARY_STD = ORDINARY_DIR / "standardized.json"
ASSUMPTIONS = ROOT / "core" / "tests" / "fixtures" / "ordinary_reconcile" / "lululemon_assumptions.json"
EXTRACTED_FILINGS = (
    EXTRACTED_DIR / "LULU_FY2022.json",
    EXTRACTED_DIR / "LULU_FY2023.json",
    EXTRACTED_DIR / "LULU_FY2024.json",
    EXTRACTED_DIR / "LULU_FY2025.json",
)
RETAINED_LIVE_STD = "6c9aad59b04a5995742c68e08f1a704953796fc9fad97a036b08aeeab59051e5"
RETAINED_LIVE_PROV = "5067c1d04aa93c18062fe7eb90558a86394283b7d9fe45899761f71cfb615951"
RETAINED_LIVE_CONFLICTS = "d8a33012f6ea73126ac4e2ece3613e7011c11cb2b581745d8c3563e3c2e978e0"
ORDINARY_STD_SHA256 = "a3568c29e883c8ba57af23da7b4286641a3c5f929af311e2e9593c5f63ea2287"
EXPECTED_FACE = (0, 407913, 74501, 0, 0)
EXPECTED_ANALYTICAL = (0, -407913, -74501, 0, 0)
EXPECTED_NONRECURRING_PRETAX = (0, 407913, 74501, 0, 0)
EXPECTED_RECURRING_PRETAX = (0, 0, 0, 0, 0)
NOTE_TAX_EFFECTS = (28171, 26085)
# Independently specified from extracted source.page and bound PDF printed-page inspection.
EXPECTED_PHYSICAL_PAGES = {
    "2022-01-30": (50, 56),
    "2023-01-29": (50, 51, 56),
    "2024-01-28": (51, 56),
    "2025-02-02": (51,),
    "2026-02-01": (51,),
}
EXPECTED_PRINTED_PAGES = {
    "2022-01-30": (46, 50),
    "2023-01-29": (46, 50),
    "2024-01-28": (50,),
    "2025-02-02": (),
    "2026-02-01": (),
}
RESOLVED_PRINTED_PAGES = {
    ("LULU_FY2022_Annual_Report.pdf", 50): 46,
    ("LULU_FY2022_Annual_Report.pdf", 53): 49,
    ("LULU_FY2023_Annual_Report.pdf", 56): 50,
    ("LULU_FY2023_Annual_Report.pdf", 59): 53,
}
BOUND_SOURCE_SHA256 = {
    "LULU_FY2022_Annual_Report.pdf": "b344d1e7a710259fa06f88773dee0b3827334820ce2b881fe6b95ca2ae275e4e",
    "LULU_FY2023_Annual_Report.pdf": "cd47ea251d608d06a3e58b5d782f2d41d5a231a994d2f7993267a430cb13c0f1",
    "LULU_FY2024_Annual_Report.pdf": "9268fd530db162babdd1ec4363cf388ebce57125d83b7e097aba6f98ba0ca7ec",
    "LULU_FY2025_Annual_Report.pdf": "82e00f900cc912a7d79596409594156b7779c3a193783ea8fecf87bc013c71cc",
}
ORDINARY_SELECTORS = (
    "concept:impairment_and_restructuring",
    "concept:restructuring_expense",
    "label:Impairment of assets and restructuring costs",
    "label:Impairment of goodwill and other assets, restructuring costs",
    "label:Impairment of goodwill and other assets",
)
C1 = "3f6f5dde023847e3347a4c830d822614a28c81a9"
C2 = "20d93331bd3c1b3cccd72a3bf5c805453789e189"
EXTRACT_BLOB = "5e3ef5cfdbfebcf5871dd7e75fad81654d669151"
RELOCATED = {
    "benchmark/fast_retailing/extracted/FY2021.json": "build/input/fast_retailing/extracted/FY2021.json",
    "benchmark/fast_retailing/extracted/FY2022.json": "build/input/fast_retailing/extracted/FY2022.json",
    "benchmark/fast_retailing/extracted/FY2023.json": "build/input/fast_retailing/extracted/FY2023.json",
    "benchmark/fast_retailing/extracted/FY2024.json": "build/input/fast_retailing/extracted/FY2024.json",
    "benchmark/fast_retailing/extracted/FY2025.json": "build/input/fast_retailing/extracted/FY2025.json",
    "benchmark/fast_retailing/reconciled/conflicts.json": "build/input/fast_retailing/reconciled/conflicts.json",
    "benchmark/fast_retailing/reconciled/provenance.json": "build/input/fast_retailing/reconciled/provenance.json",
    "benchmark/fast_retailing/reconciled/standardized.json": "build/input/fast_retailing/reconciled/standardized.json",
    "benchmark/fast_retailing/source_manifest.json": "build/input/fast_retailing/source_manifest.json",
    "benchmark/fast_retailing/source/Fastretailing_CFS2021.pdf": "build/input/fast_retailing/source/Fastretailing_CFS2021.pdf",
    "benchmark/fast_retailing/source/Fastretailing_CFS2022.pdf": "build/input/fast_retailing/source/Fastretailing_CFS2022.pdf",
    "benchmark/fast_retailing/source/Fastretailing_CFS2023.pdf": "build/input/fast_retailing/source/Fastretailing_CFS2023.pdf",
    "benchmark/fast_retailing/source/Fastretailing_CFS2024.pdf": "build/input/fast_retailing/source/Fastretailing_CFS2024.pdf",
    "benchmark/fast_retailing/source/Fastretailing_CFS2025.pdf": "build/input/fast_retailing/source/Fastretailing_CFS2025.pdf",
    "benchmark/lululemon/extracted/LULU_FY2022.json": "build/input/lululemon/extracted/LULU_FY2022.json",
    "benchmark/lululemon/extracted/LULU_FY2023.json": "build/input/lululemon/extracted/LULU_FY2023.json",
    "benchmark/lululemon/extracted/LULU_FY2024.json": "build/input/lululemon/extracted/LULU_FY2024.json",
    "benchmark/lululemon/extracted/LULU_FY2025.json": "build/input/lululemon/extracted/LULU_FY2025.json",
    "benchmark/lululemon/reconciled/conflicts.json": "core/tests/fixtures/ordinary_reconcile/lululemon/conflicts.json",
    "benchmark/lululemon/reconciled/provenance.json": "core/tests/fixtures/ordinary_reconcile/lululemon/provenance.json",
    "benchmark/lululemon/reconciled/standardized.json": "core/tests/fixtures/ordinary_reconcile/lululemon/standardized.json",
    "benchmark/lululemon/source/LULU_FY2022_Annual_Report.pdf": "build/input/lululemon/source/LULU_FY2022_Annual_Report.pdf",
    "benchmark/lululemon/source/LULU_FY2023_Annual_Report.pdf": "build/input/lululemon/source/LULU_FY2023_Annual_Report.pdf",
    "benchmark/lululemon/source/LULU_FY2024_Annual_Report.pdf": "build/input/lululemon/source/LULU_FY2024_Annual_Report.pdf",
    "benchmark/lululemon/source/LULU_FY2025_Annual_Report.pdf": "build/input/lululemon/source/LULU_FY2025_Annual_Report.pdf",
}
STAYED = [
    "example/DEMO_HK_Answer_Key.xlsx",
    "example/DEMO_HK_Assumptions.json",
    "example/DEMO_HK_Standardized.json",
    "example/DEMO_HK_Trainer.xlsx",
    "example/GOOGL_Demo_Integrated_Financials.xlsx",
]
RETIRED = [
    "release/fast_retailing/FastRetailing_Answer_Key.assumptions.json",
    "release/fast_retailing/FastRetailing_Answer_Key.component_map.json",
    "release/fast_retailing/FastRetailing_Answer_Key.xlsx",
    "release/fast_retailing/FastRetailing_Trainer.xlsx",
    "release/fast_retailing/README.md",
    "release/fast_retailing/availability.json",
    "release/fast_retailing/rowmap.json",
    "release/fast_retailing/supporting/conflicts.json",
    "release/fast_retailing/supporting/provenance.json",
    "release/fast_retailing/supporting/standardized.json",
    "release/lululemon/Lululemon_Answer_Key.assumptions.json",
    "release/lululemon/Lululemon_Answer_Key.component_map.json",
    "release/lululemon/Lululemon_Answer_Key.xlsx",
    "release/lululemon/Lululemon_Trainer.xlsx",
    "release/lululemon/README.md",
    "release/lululemon/availability.json",
    "release/lululemon/rowmap.json",
    "release/lululemon/supporting/conflicts.json",
    "release/lululemon/supporting/provenance.json",
    "release/lululemon/supporting/standardized.json",
]
EXTRACTED_EIGHT_RELOCATED = {
    "benchmark/lululemon/extracted/LULU_FY2022.json": "build/input/lululemon/extracted/LULU_FY2022.json",
    "benchmark/lululemon/extracted/LULU_FY2023.json": "build/input/lululemon/extracted/LULU_FY2023.json",
    "benchmark/lululemon/extracted/LULU_FY2024.json": "build/input/lululemon/extracted/LULU_FY2024.json",
    "benchmark/lululemon/extracted/LULU_FY2025.json": "build/input/lululemon/extracted/LULU_FY2025.json",
    "benchmark/lululemon/extracted/LULU_FY2022_management_kpis.json": "build/input/lululemon/extracted/LULU_FY2022_management_kpis.json",
    "benchmark/lululemon/extracted/LULU_FY2023_management_kpis.json": "build/input/lululemon/extracted/LULU_FY2023_management_kpis.json",
    "benchmark/lululemon/extracted/LULU_FY2024_management_kpis.json": "build/input/lululemon/extracted/LULU_FY2024_management_kpis.json",
    "benchmark/lululemon/extracted/LULU_FY2025_management_kpis.json": "build/input/lululemon/extracted/LULU_FY2025_management_kpis.json",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _git_out(args: list[str]) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def _snapshot_obs(observations: list[dict]) -> str:
    return json.dumps(observations, sort_keys=True, default=str)


def _locator_attached(obs: dict, page_lookup: dict) -> dict:
    """Independently attach physical/printed locators from the bound page lookup."""
    row = dict(obs)
    info = page_lookup.get((str(obs.get("source_file") or ""), int(obs.get("pdf_page") or 0)), {})
    row["physical_page"] = obs.get("pdf_page")
    row["printed_page"] = info.get("printed_page")
    row["printed_page_status"] = info.get("printed_status")
    return row


def _independent_fingerprint(obs: dict) -> str:
    payload = json.dumps(dict(obs), sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _page_lookup() -> dict[tuple[str, int], dict[str, object]]:
    return {
        key: {"printed_page": printed, "printed_status": "resolved"}
        for key, printed in RESOLVED_PRINTED_PAGES.items()
    }


def _derive_observations_from_extracted() -> list[dict]:
    """Build observations from extracted statement rows; not from admission output."""
    authorized = set(AUTHORIZED_IS_IDENTITIES) | set(CF_AUDIT_IDENTITIES)
    observations: list[dict] = []
    for path in EXTRACTED_FILINGS:
        filing = load_extracted_filing(path)
        source_file = filing.filing.source_file
        declared = filing.filing.source_sha256
        if declared != BOUND_SOURCE_SHA256[source_file]:
            pytest.fail(
                f"extracted source hash unbound: {path.name} {declared} "
                f"!= {BOUND_SOURCE_SHA256[source_file]}"
            )
        if _sha256(SOURCE_DIR / source_file) != declared:
            pytest.fail(f"source PDF hash mismatch: {source_file}")
        for statement, rows in (
            ("income_statement", filing.income_statement),
            ("cash_flow", filing.cash_flow),
        ):
            for row in rows:
                ident = source_row_identity(statement, row)
                if ident not in authorized:
                    continue
                for period, cell in row.values.items():
                    observations.append(
                        {
                            "currency": filing.filing.currency,
                            "kind": "statement",
                            "label": row.label,
                            "pdf_page": row.source.page,
                            "period": period.isoformat(),
                            "presentation_role": str(cell.presentation_role),
                            "row_identity": ident,
                            "section": row.section,
                            "source_file": source_file,
                            "source_sha256_declared": declared,
                            "statement": statement,
                            "suggested_concept": row.suggested_concept,
                            "unit_scale": filing.filing.unit_scale,
                            "value": cell.value,
                        }
                    )
    return observations


@pytest.fixture(scope="module")
def retained():
    observations = _derive_observations_from_extracted()
    live_bytes = (LIVE_DIR / "standardized.json").read_bytes()
    ordinary_bytes = ORDINARY_STD.read_bytes()
    reconciled_bytes = RECONCILED_STD.read_bytes()
    live_payload = json.loads(live_bytes.decode("utf-8"))
    ordinary_payload = json.loads(ordinary_bytes.decode("utf-8"))
    reconciled_payload = json.loads(reconciled_bytes.decode("utf-8"))
    return {
        "observations": observations,
        "page_lookup": _page_lookup(),
        "live_payload": live_payload,
        "ordinary_payload": ordinary_payload,
        "reconciled_payload": reconciled_payload,
        "live": standardized_from_payload(copy.deepcopy(live_payload), strict=True),
        "obs_snapshot": _snapshot_obs(observations),
        "live_std_bytes": live_bytes,
        "ordinary_std_bytes": ordinary_bytes,
        "reconciled_std_bytes": reconciled_bytes,
    }


def _axis_is_obs(observations: list[dict]) -> list[dict]:
    return [
        obs
        for obs in observations
        if obs.get("row_identity") in AUTHORIZED_IS_IDENTITIES
        and obs.get("period") in LEDGER_PERIODS
    ]


def _synthetic_adoption(construction, company: str = "LULU") -> AdoptionRecord:
    return AdoptionRecord(
        company=company,
        axis=tuple(construction.axis),
        member_identities=tuple(construction.member_identities),
        analytical_concept=ANALYTICAL_CONCEPT,
        analytical_label=ANALYTICAL_LABEL,
        source_evidence_fingerprints=tuple(construction.used_fingerprints),
        mapping_decision="adopt_three_is_identities_as_one_analytical_aggregate",
        decision_authority="synthetic_test_authority",
        rationale=(
            "SYNTHETIC test authorization only; not a Lululemon accounting judgment "
            "and not established by overlapping amounts or suggested_concept"
        ),
        analytical_scope=SUPPORTED_NORMALIZATION_SCOPE,
        decision_status="adopted",
        authorization_kind=AUTHORIZATION_SYNTHETIC,
    )


def _synthetic_treatment(**overrides) -> TreatmentRecord:
    payload = dict(
        scope=SUPPORTED_NORMALIZATION_SCOPE,
        reference_treatment="Non-recurring",
        rationale="SYNTHETIC test treatment; not a real-company judgment",
        consequence_note="SYNTHETIC consequence; pretax add-back only, after-tax unresolved",
        aggregate_or_component="aggregate",
        cogs_boundary="exclude_studio_cogs",
        deductibility="unresolved",
        etr_disposition="unresolved",
    )
    payload.update(overrides)
    return TreatmentRecord(**payload)


def _dummy_anchor(n: int) -> AnchorMetrics:
    zeros = [0.0] * n
    undefined = [UNDEFINED_RATIO] * n
    return AnchorMetrics(
        revenue=0.0,
        nowc=0.0,
        nola=0.0,
        net_debt=0.0,
        nopat=0.0,
        equity=0.0,
        noa=0.0,
        leverage=0.0,
        hist_avg_after_tax_cod=UNDEFINED_RATIO,
        effective_tax_rate=UNDEFINED_RATIO,
        net_interest=UNDEFINED_RATIO,
        net_interest_after_tax=UNDEFINED_RATIO,
        dupont={},
        reformulation=None,
        historical=HistoricalSeries(
            revenue=list(zeros),
            net_income=list(zeros),
            pretax_income=list(zeros),
            tax_expense=list(zeros),
            effective_tax_rate=list(undefined),
            net_interest=list(undefined),
            net_interest_after_tax=list(undefined),
            nopat=list(zeros),
        ),
    )


def _handoff(retained, **kwargs):
    kwargs.setdefault("observations", retained["observations"])
    kwargs.setdefault("financials", copy.deepcopy(retained["live"]))
    kwargs.setdefault("bound_source_hashes", BOUND_SOURCE_SHA256)
    kwargs.setdefault("page_lookup", retained["page_lookup"])
    return run_normalization_candidate_handoff(**kwargs)


def test_segment_bridge_tolerance_unchanged():
    assert SEGMENT_BRIDGE_TOLERANCE == 0.0


def test_authenticated_retained_evidence_and_eleven_observations(retained):
    is_obs = _axis_is_obs(retained["observations"])
    assert len(is_obs) == 11
    assert tuple(AUTHORIZED_IS_IDENTITIES) == (
        "income_statement||impairment of goodwill and other assets|impairment_and_restructuring",
        "income_statement||impairment of goodwill and other assets, restructuring costs|impairment_and_restructuring",
        "income_statement||impairment of assets and restructuring costs|impairment_and_restructuring",
    )
    excluded = [
        obs
        for obs in retained["observations"]
        if obs.get("period") == "2021-01-31"
        and obs.get("row_identity") in AUTHORIZED_IS_IDENTITIES
    ]
    assert len(excluded) == 1
    assert excluded[0]["value"] == 0
    assert excluded[0]["source_file"] == "LULU_FY2022_Annual_Report.pdf"
    assert _sha256(LIVE_DIR / "standardized.json") == RETAINED_LIVE_STD
    assert _sha256(LIVE_DIR / "provenance.json") == RETAINED_LIVE_PROV
    assert _sha256(LIVE_DIR / "conflicts.json") == RETAINED_LIVE_CONFLICTS
    assert _sha256(ORDINARY_STD) == ORDINARY_STD_SHA256
    assert retained["live_std_bytes"] == (LIVE_DIR / "standardized.json").read_bytes()
    assert retained["ordinary_std_bytes"] == ORDINARY_STD.read_bytes()
    assert retained["reconciled_std_bytes"] == RECONCILED_STD.read_bytes()
    assert _snapshot_obs(retained["observations"]) == retained["obs_snapshot"]
    for obs in retained["observations"]:
        assert obs["currency"] == "USD"
        assert obs["unit_scale"] == "thousands"
        assert obs["source_sha256_declared"] == BOUND_SOURCE_SHA256[obs["source_file"]]
        assert obs["row_identity"]
        assert obs["period"]


def test_provisional_construction_from_observations_not_hand_entered(retained):
    construction = construct_provisional_candidate(
        retained["observations"],
        bound_source_hashes=BOUND_SOURCE_SHA256,
        page_lookup=retained["page_lookup"],
    )
    assert construction.constructed is True
    assert construction.face_series == EXPECTED_FACE
    assert construction.analytical_series == EXPECTED_ANALYTICAL
    assert construction.grouping_is_accepted_source_fact is False
    assert construction.production_activation_authorized is False
    assert construction.mapping_status == "provisional_equivalence_unresolved"
    assert construction.line is not None
    assert construction.line.concept == ANALYTICAL_CONCEPT
    assert construction.line.label == ANALYTICAL_LABEL
    assert sum(row.n_is_observations for row in construction.periods) == 11
    assert _snapshot_obs(retained["observations"]) == retained["obs_snapshot"]
    used: set[str] = set()
    for row in construction.periods:
        assert row.face_retained_unchanged is True
        assert row.zero_filled is False
        assert row.missing is False
        assert row.transformation == SIGN_TRANSFORMATION
        assert row.transformation == "analytical_amount = -reported_face_expense"
        assert row.sign_conversions_applied == 1
        assert row.grouping_is_accepted_source_fact is False
        assert row.studio_cogs_included is False
        assert set(row.row_identities) <= set(AUTHORIZED_IS_IDENTITIES)
        assert row.physical_pages == EXPECTED_PHYSICAL_PAGES[row.period]
        assert row.printed_pages == EXPECTED_PRINTED_PAGES[row.period]
        assert row.source_hashes
        assert set(row.source_hashes) <= set(BOUND_SOURCE_SHA256.values())
        members = [
            obs
            for obs in retained["observations"]
            if obs.get("period") == row.period
            and obs.get("row_identity") in AUTHORIZED_IS_IDENTITIES
        ]
        expected_fps = tuple(
            _independent_fingerprint(_locator_attached(obs, retained["page_lookup"]))
            for obs in members
        )
        assert set(row.observation_fingerprints) == set(expected_fps)
        assert not used.intersection(row.observation_fingerprints)
        used.update(row.observation_fingerprints)
    assert len(used) == 11


def test_real_lululemon_path_blocks_production_without_adoption(retained):
    original_n = len(retained["live"].income_statement)
    original_concepts = [item.concept for item in retained["live"].income_statement]
    result = _handoff(retained)
    assert result.constructed is True
    assert result.production_admitted is False
    assert result.real_company_acceptance is False
    assert result.blocked_reason == "absent_adoption"
    assert result.candidate_configuration is None
    assert result.face_series == EXPECTED_FACE
    assert result.analytical_series == EXPECTED_ANALYTICAL
    assert result.grouping_is_accepted_source_fact is False
    assert len(retained["live"].income_statement) == original_n
    assert [item.concept for item in retained["live"].income_statement] == original_concepts
    assert ANALYTICAL_CONCEPT not in original_concepts
    assert json.loads(ASSUMPTIONS.read_text(encoding="utf-8")).get("normalizationCandidates") == []


@pytest.mark.parametrize(
    "name,kwargs,reason",
    [
        (
            "missing_period_evidence",
            {"drop_period": "2022-01-30"},
            "missing_period_evidence",
        ),
        (
            "altered_or_unbound_source_hash",
            {"alter_binding": True},
            "altered_or_unbound_source_hash",
        ),
        (
            "conflicting_overlapping_observations",
            {"conflict_value": 999999},
            "conflicting_overlapping_observations",
        ),
        (
            "unauthorized_identity_membership",
            {"unauthorized": True},
            "unauthorized_identity_membership",
        ),
        (
            "cash_flow_substitution_forbidden",
            {"cf_members": True},
            "cash_flow_substitution_forbidden",
        ),
        (
            "studio_cogs_excluded",
            {"studio": True},
            "studio_cogs_excluded",
        ),
        (
            "aggregate_and_component_double_count",
            {"component": True},
            "aggregate_and_component_double_count",
        ),
        (
            "absent_sign_conversion",
            {"sign_conversion": "absent"},
            "absent_sign_conversion",
        ),
        (
            "repeated_sign_conversion",
            {"sign_conversion": "repeated"},
            "repeated_sign_conversion",
        ),
        (
            "observation_used_more_than_once",
            {"duplicate": True},
            "observation_used_more_than_once",
        ),
    ],
)
def test_retained_construction_rejection_probes_leave_inputs_unchanged(retained, name, kwargs, reason):
    observations = copy.deepcopy(retained["observations"])
    member_identities = AUTHORIZED_IS_IDENTITIES
    sign_conversion = kwargs.get("sign_conversion", "once")
    allow_cf = False
    if kwargs.get("drop_period"):
        observations = [
            obs
            for obs in observations
            if not (
                obs.get("period") == kwargs["drop_period"]
                and obs.get("row_identity") in AUTHORIZED_IS_IDENTITIES
            )
        ]
    if kwargs.get("alter_binding"):
        for obs in observations:
            if (
                obs.get("period") == "2023-01-29"
                and obs.get("row_identity") == AUTHORIZED_IS_IDENTITIES[0]
            ):
                obs["source_sha256_declared"] = "0" * 64
                break
    if kwargs.get("conflict_value") is not None:
        for obs in observations:
            if (
                obs.get("period") == "2023-01-29"
                and obs.get("row_identity") == AUTHORIZED_IS_IDENTITIES[1]
            ):
                obs["value"] = kwargs["conflict_value"]
                break
    if kwargs.get("unauthorized"):
        observations.append(
            {
                "currency": "USD",
                "kind": "statement",
                "label": "Selling, general and administrative expenses",
                "pdf_page": 50,
                "period": "2023-01-29",
                "presentation_role": "current_period",
                "row_identity": "income_statement||selling, general and administrative expenses|sga",
                "section": "",
                "source_file": "LULU_FY2022_Annual_Report.pdf",
                "source_sha256_declared": BOUND_SOURCE_SHA256["LULU_FY2022_Annual_Report.pdf"],
                "statement": "income_statement",
                "suggested_concept": "sga",
                "unit_scale": "thousands",
                "value": 1,
            }
        )
        member_identities = AUTHORIZED_IS_IDENTITIES + (
            "income_statement||selling, general and administrative expenses|sga",
        )
    if kwargs.get("cf_members"):
        member_identities = CF_AUDIT_IDENTITIES
    if kwargs.get("studio"):
        observations.append(
            {
                "currency": "USD",
                "kind": "statement",
                "label": "lululemon Studio obsolescence provision",
                "pdf_page": 59,
                "period": "2023-01-29",
                "presentation_role": "current_period",
                "row_identity": (
                    "cash_flow|cash flows from operating activities|"
                    "lululemon studio obsolescence provision|studio_obsolescence_provision"
                ),
                "section": "Cash flows from operating activities",
                "source_file": "LULU_FY2023_Annual_Report.pdf",
                "source_sha256_declared": BOUND_SOURCE_SHA256["LULU_FY2023_Annual_Report.pdf"],
                "statement": "cash_flow",
                "suggested_concept": "studio_obsolescence_provision",
                "unit_scale": "thousands",
                "value": 62928,
            }
        )
        member_identities = AUTHORIZED_IS_IDENTITIES + (
            "cash_flow|cash flows from operating activities|"
            "lululemon studio obsolescence provision|studio_obsolescence_provision",
        )
    if kwargs.get("component"):
        observations.append(
            {
                "currency": "USD",
                "kind": "statement",
                "label": "Goodwill impairment component of IS aggregate",
                "pdf_page": 65,
                "period": "2023-01-29",
                "presentation_role": "current_period",
                "row_identity": (
                    "income_statement||goodwill impairment component of is aggregate|"
                    "goodwill_impairment_component"
                ),
                "section": "",
                "source_file": "LULU_FY2022_Annual_Report.pdf",
                "source_sha256_declared": BOUND_SOURCE_SHA256["LULU_FY2022_Annual_Report.pdf"],
                "statement": "income_statement",
                "suggested_concept": "goodwill_impairment_component",
                "unit_scale": "thousands",
                "value": 362492,
            }
        )
        member_identities = AUTHORIZED_IS_IDENTITIES + (
            "income_statement||goodwill impairment component of is aggregate|"
            "goodwill_impairment_component",
        )
    if kwargs.get("duplicate"):
        first_is = next(
            obs
            for obs in observations
            if obs.get("period") == "2023-01-29"
            and obs.get("row_identity") in AUTHORIZED_IS_IDENTITIES
        )
        observations.append(copy.deepcopy(first_is))

    financials = copy.deepcopy(retained["live"])
    original_payload = standardized_to_payload(financials)
    original_obs = _snapshot_obs(retained["observations"])
    result = run_normalization_candidate_handoff(
        observations,
        financials,
        bound_source_hashes=BOUND_SOURCE_SHA256,
        page_lookup=retained["page_lookup"],
        member_identities=member_identities,
        sign_conversion=sign_conversion,
    )
    assert result.constructed is False
    assert result.production_admitted is False
    assert result.blocked_reason == reason, (name, result.blocked_reason, result.gate)
    assert result.candidate_configuration is None
    assert result.constructed_financials is None
    assert standardized_to_payload(financials) == original_payload
    assert _snapshot_obs(retained["observations"]) == original_obs


def test_ambiguous_selector_still_rejected_by_existing_resolver(retained):
    construction = construct_provisional_candidate(
        retained["observations"],
        bound_source_hashes=BOUND_SOURCE_SHA256,
        page_lookup=retained["page_lookup"],
    )
    isolated = copy.deepcopy(retained["live"])
    isolated.income_statement = list(isolated.income_statement)
    isolated.income_statement.append(construction.line)
    isolated.income_statement.append(
        type(construction.line)(
            label=ANALYTICAL_LABEL + " duplicate",
            concept=ANALYTICAL_CONCEPT,
            values=dict(construction.line.values),
        )
    )
    with pytest.raises(ValueError, match="matched 2"):
        resolve_income_statement_selector(isolated, ANALYTICAL_SELECTOR)


def test_provisional_adoption_and_technical_equivalence_cannot_authorize(retained):
    construction = construct_provisional_candidate(
        retained["observations"],
        bound_source_hashes=BOUND_SOURCE_SHA256,
        page_lookup=retained["page_lookup"],
    )
    base = _synthetic_adoption(construction)
    cases = {
        "provisional_adoption": base.__class__(
            **{**base.__dict__, "decision_status": "provisional"}
        ),
        "boolean_approved": base.__class__(**{**base.__dict__, "approved": True}),
        "matching_concept": base.__class__(
            **{**base.__dict__, "equivalent_by_concept": True}
        ),
        "agreeing_amounts": base.__class__(
            **{**base.__dict__, "equivalent_by_agreeing_amounts": True}
        ),
        "rationale_matching_concept": base.__class__(
            **{**base.__dict__, "rationale": "matching concept across three labels"}
        ),
    }
    financials = copy.deepcopy(retained["live"])
    original = standardized_to_payload(financials)
    result = _handoff(retained, financials=financials, adoption=cases["provisional_adoption"])
    assert result.blocked_reason == "provisional_adoption"
    assert result.production_admitted is False
    assert standardized_to_payload(financials) == original
    for key in ("boolean_approved", "matching_concept", "agreeing_amounts", "rationale_matching_concept"):
        blocked = _handoff(retained, adoption=cases[key])
        assert blocked.production_admitted is False
        assert blocked.blocked_reason == "contradictory_adoption"
        assert blocked.real_company_acceptance is False


def test_altered_decision_bindings_and_stale_adoption(retained):
    construction = construct_provisional_candidate(
        retained["observations"],
        bound_source_hashes=BOUND_SOURCE_SHA256,
        page_lookup=retained["page_lookup"],
    )
    base = _synthetic_adoption(construction)
    mismatched = [
        base.__class__(**{**base.__dict__, "company": "NOT_LULU"}),
        base.__class__(**{**base.__dict__, "axis": LEDGER_PERIODS[1:]}),
        base.__class__(
            **{**base.__dict__, "member_identities": AUTHORIZED_IS_IDENTITIES[:2]}
        ),
        base.__class__(**{**base.__dict__, "analytical_concept": "impairment_and_restructuring"}),
    ]
    for record in mismatched:
        result = _handoff(retained, adoption=record, treatment=_synthetic_treatment())
        assert result.blocked_reason == "mismatched_adoption"
        assert result.production_admitted is False
        assert result.candidate_configuration is None
    stale = base.__class__(
        **{**base.__dict__, "source_evidence_fingerprints": ("0" * 64,)}
    )
    stale_result = _handoff(retained, adoption=stale, treatment=_synthetic_treatment())
    assert stale_result.blocked_reason == "stale_adoption"
    assert stale_result.production_admitted is False


def test_missing_treatment_rationale_consequence_and_conflicting_scope(retained):
    construction = construct_provisional_candidate(
        retained["observations"],
        bound_source_hashes=BOUND_SOURCE_SHA256,
        page_lookup=retained["page_lookup"],
    )
    adoption = _synthetic_adoption(construction)
    financials = copy.deepcopy(retained["live"])
    original = standardized_to_payload(financials)
    absent = _handoff(retained, financials=financials, adoption=adoption)
    assert absent.blocked_reason == "absent_treatment"
    assert absent.production_admitted is False
    assert standardized_to_payload(financials) == original
    missing_rationale = _handoff(
        retained,
        adoption=adoption,
        treatment=_synthetic_treatment(rationale=""),
    )
    assert missing_rationale.blocked_reason == "missing_treatment_rationale"
    missing_note = _handoff(
        retained,
        adoption=adoption,
        treatment=_synthetic_treatment(consequence_note=""),
    )
    assert missing_note.blocked_reason == "missing_treatment_consequence"
    conflicting = _handoff(
        retained,
        adoption=adoption,
        treatment=_synthetic_treatment(scope="note_item_specific_tax"),
    )
    assert conflicting.blocked_reason == "conflicting_scope"
    unresolved_scope = _handoff(
        retained,
        adoption=adoption,
        treatment=_synthetic_treatment(aggregate_or_component="component"),
    )
    assert unresolved_scope.blocked_reason == "unresolved_scope"
    unresolved_treatment = _handoff(
        retained,
        adoption=adoption,
        treatment=_synthetic_treatment(reference_treatment="Maybe"),
    )
    assert unresolved_treatment.blocked_reason == "unresolved_recurring_treatment"
    assert all(
        row.production_admitted is False
        for row in (
            absent,
            missing_rationale,
            missing_note,
            conflicting,
            unresolved_scope,
            unresolved_treatment,
        )
    )


def test_synthetic_admission_export_reload_and_hypothetical_pretax(retained):
    construction = construct_provisional_candidate(
        retained["observations"],
        bound_source_hashes=BOUND_SOURCE_SHA256,
        page_lookup=retained["page_lookup"],
    )
    financials = copy.deepcopy(retained["live"])
    original_n = len(financials.income_statement)
    result = run_normalization_candidate_handoff(
        retained["observations"],
        financials,
        bound_source_hashes=BOUND_SOURCE_SHA256,
        page_lookup=retained["page_lookup"],
        adoption=_synthetic_adoption(construction),
        treatment=_synthetic_treatment(),
    )
    assert result.constructed is True
    assert result.production_admitted is True
    assert result.real_company_acceptance is False
    assert result.authorization_kind == AUTHORIZATION_SYNTHETIC
    assert result.mapping_status == "synthetic_test_authorization"
    assert result.grouping_is_accepted_source_fact is False
    assert result.after_tax_available is False
    assert result.note_tax_effects_attributed is False
    assert result.tax_disposition == "unresolved"
    assert result.face_series == EXPECTED_FACE
    assert result.analytical_series == EXPECTED_ANALYTICAL
    assert result.candidate_configuration is not None
    assert result.candidate_configuration["selector"] == ANALYTICAL_SELECTOR
    assert result.candidate_configuration["referenceTreatment"] == "Non-recurring"
    assert len(financials.income_statement) == original_n
    isolated = result.constructed_financials
    assert isolated is not None
    assert len(isolated.income_statement) == original_n + 1
    exported = standardized_to_payload(isolated)
    reloaded = standardized_from_payload(exported, strict=True)
    item = resolve_income_statement_selector(reloaded, ANALYTICAL_SELECTOR)
    ident = line_identity(item)
    assert item.label == ANALYTICAL_LABEL
    assert item.concept == ANALYTICAL_CONCEPT
    dates = [date.fromisoformat(p) for p in LEDGER_PERIODS]
    assert tuple(int(item.values[period]) for period in dates) == EXPECTED_ANALYTICAL
    assert ident.key() == (
        f"concept={ANALYTICAL_CONCEPT}|label={ANALYTICAL_LABEL.casefold()}"
    )
    assert _snapshot_obs(retained["observations"]) == retained["obs_snapshot"]
    assert retained["live_std_bytes"] == (LIVE_DIR / "standardized.json").read_bytes()
    for row in result.periods:
        assert row.transformation == SIGN_TRANSFORMATION
        assert row.source_hashes
        assert set(row.source_hashes) <= set(BOUND_SOURCE_SHA256.values())
        assert row.physical_pages == EXPECTED_PHYSICAL_PAGES[row.period]
        assert row.printed_pages == EXPECTED_PRINTED_PAGES[row.period]
        assert set(row.row_identities) <= set(AUTHORIZED_IS_IDENTITIES)
        assert row.observation_fingerprints
        members = [
            obs
            for obs in retained["observations"]
            if obs.get("period") == row.period
            and obs.get("row_identity") in AUTHORIZED_IS_IDENTITIES
        ]
        expected_fps = {
            _independent_fingerprint(_locator_attached(obs, retained["page_lookup"]))
            for obs in members
        }
        assert set(row.observation_fingerprints) == expected_fps
    for selector in ORDINARY_SELECTORS:
        with pytest.raises(ValueError, match="matched no income-statement line"):
            resolve_income_statement_selector(reloaded, selector)
    periods = canonical_fiscal_periods(reloaded)
    cases_nr = normalization_cases(
        reloaded, periods, {"normalizationCandidates": [result.candidate_configuration]}
    )
    rec_cfg = dict(result.candidate_configuration)
    rec_cfg["referenceTreatment"] = "Recurring"
    rec_cfg["referenceRationale"] = "SYNTHETIC recurring probe; not adopted"
    rec_cfg["consequenceNote"] = "SYNTHETIC recurring probe; not adopted"
    cases_rec = normalization_cases(
        reloaded, periods, {"normalizationCandidates": [rec_cfg]}
    )
    anchor = _dummy_anchor(len(periods))
    series_nr = compute_normalization_series(
        reloaded, periods, anchor, cases_nr, treatments={cases_nr[0].id: "Non-recurring"}
    )
    series_rec = compute_normalization_series(
        reloaded, periods, anchor, cases_rec, treatments={cases_rec[0].id: "Recurring"}
    )
    assert tuple(int(v) for v in series_nr.pretax_adjustment) == EXPECTED_NONRECURRING_PRETAX
    assert tuple(int(v) for v in series_rec.pretax_adjustment) == EXPECTED_RECURRING_PRETAX
    assert series_nr.after_tax_adjustment[0] == 0.0
    assert series_nr.after_tax_adjustment[3] == 0.0
    assert series_nr.after_tax_adjustment[4] == 0.0
    assert series_nr.after_tax_adjustment[1] == UNDEFINED_RATIO
    assert series_nr.after_tax_adjustment[2] == UNDEFINED_RATIO
    blob = json.dumps(result.candidate_configuration)
    assert "28171" not in blob and "26085" not in blob
    assert NOTE_TAX_EFFECTS[0] not in series_nr.pretax_adjustment
    assert json.loads(ASSUMPTIONS.read_text(encoding="utf-8")).get("normalizationCandidates") == []


def test_repeated_admission_rejected_and_inputs_unchanged(retained):
    construction = construct_provisional_candidate(
        retained["observations"],
        bound_source_hashes=BOUND_SOURCE_SHA256,
        page_lookup=retained["page_lookup"],
    )
    first = _handoff(
        retained,
        adoption=_synthetic_adoption(construction),
        treatment=_synthetic_treatment(),
    )
    assert first.production_admitted is True
    isolated = first.constructed_financials
    assert isolated is not None
    original = standardized_to_payload(isolated)
    repeated = run_normalization_candidate_handoff(
        retained["observations"],
        isolated,
        bound_source_hashes=BOUND_SOURCE_SHA256,
        page_lookup=retained["page_lookup"],
        adoption=_synthetic_adoption(construction),
        treatment=_synthetic_treatment(),
    )
    assert repeated.blocked_reason == "repeated_admission"
    assert repeated.production_admitted is False
    assert repeated.candidate_configuration is None
    assert standardized_to_payload(isolated) == original


def test_ordinary_outputs_and_selectors_unchanged(retained):
    live = standardized_from_payload(copy.deepcopy(retained["live_payload"]), strict=True)
    ordinary = standardized_from_payload(copy.deepcopy(retained["ordinary_payload"]), strict=True)
    reconciled = standardized_from_payload(copy.deepcopy(retained["reconciled_payload"]), strict=True)
    for std in (live, ordinary):
        for selector in ORDINARY_SELECTORS + (ANALYTICAL_SELECTOR,):
            with pytest.raises(ValueError, match="matched no income-statement line"):
                resolve_income_statement_selector(std, selector)
    for std in (live, ordinary, reconciled):
        assert (
            normalization_cases(std, canonical_fiscal_periods(std), {"normalizationCandidates": []})
            == ()
        )
        assert not any(item.concept == ANALYTICAL_CONCEPT for item in std.income_statement)
    with pytest.raises(ValueError, match="matched no income-statement line"):
        resolve_income_statement_selector(reconciled, ANALYTICAL_SELECTOR)
    assert _sha256(LIVE_DIR / "standardized.json") == RETAINED_LIVE_STD
    assert retained["live_std_bytes"] == (LIVE_DIR / "standardized.json").read_bytes()
    assert retained["ordinary_std_bytes"] == ORDINARY_STD.read_bytes()
    assert retained["reconciled_std_bytes"] == RECONCILED_STD.read_bytes()
    assert json.loads(ASSUMPTIONS.read_text(encoding="utf-8")).get("normalizationCandidates") == []


def test_protected_artifacts_and_eight_extracts_unchanged():
    matches = 0
    for old, new in RELOCATED.items():
        wt = _git_out(["git", "hash-object", str(ROOT / new)])
        c1 = _git_out(["git", "rev-parse", f"{C1}:{old}"])
        c2 = _git_out(["git", "rev-parse", f"{C2}:{old}"])
        assert wt == c1 == c2, (old, new)
        matches += 1
    for rel in STAYED:
        wt = _git_out(["git", "hash-object", str(ROOT / rel)])
        c1 = _git_out(["git", "rev-parse", f"{C1}:{rel}"])
        c2 = _git_out(["git", "rev-parse", f"{C2}:{rel}"])
        assert wt == c1 == c2, rel
        matches += 1
    for rel in RETIRED:
        c1 = _git_out(["git", "rev-parse", f"{C1}:{rel}"])
        c2 = _git_out(["git", "rev-parse", f"{C2}:{rel}"])
        assert c1 == c2, rel
        assert not (ROOT / rel).is_file(), rel
        matches += 1
    assert matches == 50
    extract_matches = 0
    for old, new in EXTRACTED_EIGHT_RELOCATED.items():
        wt = _git_out(["git", "hash-object", str(ROOT / new)])
        at = _git_out(["git", "rev-parse", f"{EXTRACT_BLOB}:{old}"])
        assert wt == at, (old, new)
        extract_matches += 1
    assert extract_matches == 8


def _page_lookup_rows(page_lookup: dict) -> list[list[object]]:
    return [
        [source, page, info["printed_page"]]
        for (source, page), info in sorted(page_lookup.items())
    ]


def _independent_expected_provenance(observations: list[dict], page_lookup: dict) -> dict[str, dict]:
    """Source-derived expectations computed before any persist/reload."""
    expected: dict[str, dict] = {}
    for period in LEDGER_PERIODS:
        members = [
            _locator_attached(obs, page_lookup)
            for obs in observations
            if obs.get("period") == period and obs.get("row_identity") in AUTHORIZED_IS_IDENTITIES
        ]
        expected[period] = {
            "observation_fingerprints": tuple(
                _independent_fingerprint(obs) for obs in members
            ),
            "source_hashes": tuple(
                sorted({str(obs["source_sha256_declared"]) for obs in members})
            ),
            "physical_pages": EXPECTED_PHYSICAL_PAGES[period],
            "printed_pages": EXPECTED_PRINTED_PAGES[period],
            "row_identities": tuple(sorted({str(obs["row_identity"]) for obs in members})),
            "transformation": SIGN_TRANSFORMATION,
            "sign_conversions_applied": 1,
            "face_reported_usd_thousands": EXPECTED_FACE[LEDGER_PERIODS.index(period)],
        }
    return expected


def _documentary_needles() -> dict[str, bool]:
    return {
        ANALYTICAL_CONCEPT: False,
        ANALYTICAL_LABEL: False,
        SIGN_TRANSFORMATION: False,
        "observation_fingerprints": False,
        "sign_conversions_applied": False,
        "printed_page": False,
    }


def _documentary_hits(payload: object) -> dict[str, bool]:
    text = json.dumps(payload, default=str)
    return {needle: needle in text for needle in _documentary_needles()}


def _admission_persist_names() -> list[str]:
    import core.ingestion.normalization_candidate_admission as admission

    tokens = ("persist", "write_", "reload", "dump", "save_", "to_json", "from_json")
    return sorted(
        name
        for name in dir(admission)
        if any(token in name.lower() for token in tokens)
    )


def _materialize_git_tree(dest: Path, sha: str) -> None:
    archive = subprocess.check_output(
        ["git", "archive", sha, "core", "modeler", "extractor", "director"],
        cwd=ROOT,
    )
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as tar:
        tar.extractall(dest, filter="data")


def _run_isolated_compare(era: str, tree: Path, casebook: dict) -> dict:
    driver = ROOT / "core" / "tests" / "normalization_candidate_isolated_driver.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(tree)
    env["PYTHONNOUSERSITE"] = "1"
    result = subprocess.run(
        [sys.executable, str(driver), era],
        cwd=str(tree),
        input=json.dumps(casebook),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(f"isolated {era} compare failed: {result.stderr or result.stdout}")
    return json.loads(result.stdout)


def test_admission_provenance_persistence_reload(retained):
    expected = _independent_expected_provenance(
        retained["observations"], retained["page_lookup"]
    )
    construction = construct_provisional_candidate(
        retained["observations"],
        bound_source_hashes=BOUND_SOURCE_SHA256,
        page_lookup=retained["page_lookup"],
    )
    admitted = run_normalization_candidate_handoff(
        retained["observations"],
        copy.deepcopy(retained["live"]),
        bound_source_hashes=BOUND_SOURCE_SHA256,
        page_lookup=retained["page_lookup"],
        adoption=_synthetic_adoption(construction),
        treatment=_synthetic_treatment(),
    )
    assert admitted.production_admitted is True
    isolated = admitted.constructed_financials
    assert isolated is not None
    exported = standardized_to_payload(isolated)
    del admitted
    del isolated
    del construction

    with tempfile.TemporaryDirectory() as tmp:
        std_path = Path(tmp) / "standardized.json"
        std_path.write_text(json.dumps(exported), encoding="utf-8")
        del exported
        reloaded_payload = json.loads(std_path.read_text(encoding="utf-8"))
        reloaded = standardized_from_payload(reloaded_payload, strict=True)

    item = resolve_income_statement_selector(reloaded, ANALYTICAL_SELECTOR)
    ident = line_identity(item)
    dates = [date.fromisoformat(period) for period in LEDGER_PERIODS]
    recovered_line = next(
        row
        for row in reloaded_payload["income_statement"]
        if row.get("concept") == ANALYTICAL_CONCEPT
    )
    assert item.label == ANALYTICAL_LABEL
    assert item.concept == ANALYTICAL_CONCEPT
    assert tuple(int(item.values[period]) for period in dates) == EXPECTED_ANALYTICAL
    assert ident.key() == (
        f"concept={ANALYTICAL_CONCEPT}|label={ANALYTICAL_LABEL.casefold()}"
    )
    assert set(recovered_line) == {"label", "concept", "values"}
    assert item.source_doc == ""
    assert item.source_page == ""
    assert "provenance" not in reloaded_payload
    missing = [field for field in REQUIRED_PROVENANCE_FIELDS if field not in recovered_line]
    assert missing == list(REQUIRED_PROVENANCE_FIELDS)
    for period, expect in expected.items():
        assert expect["physical_pages"] == EXPECTED_PHYSICAL_PAGES[period]
        assert expect["printed_pages"] == EXPECTED_PRINTED_PAGES[period]
        assert expect["transformation"] == SIGN_TRANSFORMATION
        assert expect["sign_conversions_applied"] == 1
        assert expect["face_reported_usd_thousands"] == EXPECTED_FACE[
            LEDGER_PERIODS.index(period)
        ]
        assert expect["observation_fingerprints"]
        assert expect["source_hashes"]
        assert expect["row_identities"]
        recovered_period = recovered_line["values"].get(period)
        assert int(recovered_period) == EXPECTED_ANALYTICAL[LEDGER_PERIODS.index(period)]
        assert recovered_line.get("observation_fingerprints") != expect[
            "observation_fingerprints"
        ]
    assert EXPECTED_PRINTED_PAGES["2025-02-02"] == ()
    assert EXPECTED_PRINTED_PAGES["2026-02-01"] == ()
    assert _admission_persist_names() == []
    live_hits = _documentary_hits(_load_json(LIVE_DIR / "provenance.json"))
    ordinary_hits = _documentary_hits(_load_json(ORDINARY_DIR / "provenance.json"))
    assert live_hits == _documentary_needles()
    assert ordinary_hits == _documentary_needles()
    from modeler.ingestion.filing_standardizer import reconciliation_provenance_payload

    try:
        reconciliation_provenance_payload(reloaded)
        documentary_accepts = True
    except Exception as exc:
        documentary_accepts = False
        documentary_error = type(exc).__name__
    assert documentary_accepts is False
    assert documentary_error == "TypeError"
    assert _snapshot_obs(retained["observations"]) == retained["obs_snapshot"]
    assert retained["live_std_bytes"] == (LIVE_DIR / "standardized.json").read_bytes()


def test_b_and_current_isolated_agreement(retained):
    parent = _git_out(["git", "rev-parse", f"{REVIEWED_CHECKPOINT}^"])
    assert parent == COMPARISON_B
    reviewed_parent = _git_out(["git", "rev-parse", f"{REVIEWED_CHECKPOINT_1091}^"])
    assert reviewed_parent == REVIEWED_BASELINE_1091
    casebook = {
        "observations": retained["observations"],
        "live_payload": retained["live_payload"],
        "ordinary_payload": retained["ordinary_payload"],
        "bound_source_hashes": BOUND_SOURCE_SHA256,
        "page_lookup": _page_lookup_rows(retained["page_lookup"]),
        "ordinary_selectors": list(ORDINARY_SELECTORS),
        "expected_analytical": list(EXPECTED_ANALYTICAL),
        "required_provenance_fields": list(REQUIRED_PROVENANCE_FIELDS),
    }
    current = _run_isolated_compare("current", ROOT, casebook)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        pre_tree = root / "pre"
        auth_tree = root / "auth"
        pre_tree.mkdir()
        auth_tree.mkdir()
        _materialize_git_tree(pre_tree, COMPARISON_B)
        _materialize_git_tree(auth_tree, AUTHENTICATED_B)
        pre_admission = (pre_tree / "core/ingestion/normalization_candidate_admission.py").read_bytes()
        assert pre_admission == subprocess.check_output(
            ["git", "show", f"{COMPARISON_B}:core/ingestion/normalization_candidate_admission.py"],
            cwd=ROOT,
        )
        auth_admission = (auth_tree / "core/ingestion/normalization_candidate_admission.py").read_bytes()
        assert auth_admission == subprocess.check_output(
            ["git", "show", f"{AUTHENTICATED_B}:core/ingestion/normalization_candidate_admission.py"],
            cwd=ROOT,
        )
        baseline = _run_isolated_compare("b", pre_tree, casebook)
        authenticated = _run_isolated_compare("authenticated_b", auth_tree, casebook)
    assert current == baseline
    assert current == authenticated
    assert current["construction"]["face_series"] == list(EXPECTED_FACE)
    assert current["construction"]["analytical_series"] == list(EXPECTED_ANALYTICAL)
    assert current["absent_adoption"]["blocked_reason"] == "absent_adoption"
    assert current["absent_adoption"]["production_admitted"] is False
    assert current["synthetic_admission"]["production_admitted"] is True
    assert current["synthetic_admission"]["real_company_acceptance"] is False
    assert current["synthetic_admission"]["pretax"]["nonrecurring"] == list(EXPECTED_NONRECURRING_PRETAX)
    assert current["synthetic_admission"]["pretax"]["recurring"] == list(EXPECTED_RECURRING_PRETAX)
    assert current["repeated_admission"]["blocked_reason"] == "repeated_admission"
    assert current["ordinary_outputs"]["live"]["has_analytical"] is False
    assert current["ordinary_outputs"]["ordinary"]["empty_candidates"] is True
    persistence = current["persistence"]
    assert persistence["standardized_reload"]["recovered_values"] == list(EXPECTED_ANALYTICAL)
    assert persistence["standardized_reload"]["missing_required_fields"] == list(
        REQUIRED_PROVENANCE_FIELDS
    )
    assert persistence["standardized_reload"]["source_doc"] == ""
    assert persistence["standardized_reload"]["source_page"] == ""
    assert persistence["contract"]["admission_persist_names"] == []
    assert persistence["contract"]["documentary_accepts_standardized"] is False
    assert persistence["contract"]["documentary_error"] == "TypeError"
    assert persistence["contract"]["limitation"] == "no_admission_provenance_persist_reload"
    assert _snapshot_obs(retained["observations"]) == retained["obs_snapshot"]
    assert retained["live_std_bytes"] == (LIVE_DIR / "standardized.json").read_bytes()
