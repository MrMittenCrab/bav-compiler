"""Local intake classification and proof-plan contracts. No provider calls."""

from __future__ import annotations

from pathlib import Path

from bav.debater.intake import (
    build_local_plan,
    classify_proposition,
    conservative_proposition_match,
    load_intake_fixtures,
    parse_exclude,
    proof_plan_display,
)
from bav.extractor.research.contracts import InventoryRecord, SnapshotInventory

BENCHMARK = (
    "Fast Retailing's acquisition of Lululemon would accelerate Lululemon's growth in Asia."
)


def _inventory() -> SnapshotInventory:
    record = InventoryRecord(
        document_id="fastretailing-cfs-2025",
        company_slug="fast_retailing",
        case_local=False,
        original_filename="Fastretailing_CFS2025.pdf",
        original_sha256="25" * 32,
        prepared_sha256="63" * 32,
        converter_profile_id="fixture",
        representation="converted_markdown",
        publication_date_status="unknown",
        issuer_status="assigned",
        limitations=("cfs_only",),
        bundle_dir=Path("."),
    )
    return SnapshotInventory(
        snapshot_id="fixture-snapshot",
        snapshot_fingerprint="fp-fixture",
        records=(record,),
        coverage_gaps=("lulu-fy2025-annual-report:garbled_text",),
    )


def test_benchmark_is_clear_and_preserves_wording():
    result = classify_proposition(BENCHMARK)
    assert result.clarity == "clear"
    assert result.accepted == BENCHMARK
    assert result.kind == "causal_strategic"
    assert result.plan_id == "asia-growth"
    assert result.hypothetical is True


def test_unclear_proposition_creates_no_meanings():
    result = classify_proposition("growth")
    assert result.clarity == "unclear"
    assert result.meanings == ()


def test_ambiguous_meanings_come_from_fixture():
    result = classify_proposition("Lululemon and Fast Retailing have product fit.")
    assert result.clarity == "ambiguous"
    assert [item.statement for item in result.meanings] == [
        "Complementary product categories.",
        "Distinct price tiers.",
        "Complementary customer segments.",
    ]


def test_negated_and_reworded_claims_are_not_the_benchmark():
    negated = (
        "Fast Retailing's acquisition of Lululemon would not accelerate "
        "Lululemon's growth in Asia."
    )
    reworded = (
        "An acquisition of Lululemon by Fast Retailing would speed "
        "Lululemon's Asian expansion."
    )
    assert classify_proposition(negated).plan_id is None
    assert classify_proposition(reworded).plan_id is None
    assert not conservative_proposition_match(BENCHMARK, negated)
    assert not conservative_proposition_match(BENCHMARK, reworded)


def test_benchmark_plan_keeps_markets_and_avoids_valuation():
    plan = build_local_plan(classify_proposition(BENCHMARK), _inventory())
    assert plan.markets == ("Japan", "Greater China")
    assert "would" in plan.proposition
    assert "might" not in plan.growth_measure.casefold()
    assert "store count is not the measure" in plan.growth_measure.casefold()
    assert "acquisition valuation" in plan.excluded_obligations
    assert plan.unresolved_parameters == ("uplift", "closing date", "forecast", "horizon")
    assert all(claim.role == "proposed_obligation" for claim in plan.claims)
    display = "\n".join(proof_plan_display(plan, case_fragment="growth in Asia"))
    assert "Hypothetical acquisition" in display
    assert "Japan and Greater China" in display
    assert "continued independence" in display
    assert "Not researched semantic judgment" in display
    assert "acquisition valuation" in display
    assert ":" not in display


def test_exclude_parser_rejects_invalid_values():
    assert parse_exclude("2,3", 3) == (2, 3)
    try:
        parse_exclude("0", 3)
        raise AssertionError("expected invalid exclude")
    except ValueError:
        pass
    try:
        parse_exclude("1,2,3", 3)
        raise AssertionError("expected exclusion of every meaning")
    except ValueError:
        pass


def test_fixture_is_labeled_configuration():
    payload = load_intake_fixtures()
    assert "not company evidence" in payload["label"]
