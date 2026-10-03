"""Gated opt-in normalization candidate handoff (Step 9M.2.4.1.1.1.68)."""

from __future__ import annotations

import pytest

from bav.director.tests.normalization_candidate_admission_support import (
    AUTHORIZATION_INDEPENDENT,
    BOUND_SOURCE_SHA256,
    EXPECTED_ANALYTICAL,
    EXPECTED_FACE,
    LIVE_DIR,
    Path,
    SIGN_TRANSFORMATION,
    _handoff,
    _independent_adoption,
    _independent_observation_evidence,
    _persist_admitted,
    _run_fresh_load,
    _snapshot_obs,
    _synthetic_adoption,
    _synthetic_treatment,
    construct_provisional_candidate,
    copy,
    load_admitted_normalization_candidate,
    retained,
    run_normalization_candidate_handoff,
    standardized_to_payload,
    tempfile,
)

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

def test_independent_authorization_bundle_save_load_fresh_process(retained):
    construction = construct_provisional_candidate(
        retained["observations"],
        bound_source_hashes=BOUND_SOURCE_SHA256,
        page_lookup=retained["page_lookup"],
    )
    financials = copy.deepcopy(retained["live"])
    original = standardized_to_payload(financials)
    admitted = run_normalization_candidate_handoff(
        retained["observations"],
        financials,
        bound_source_hashes=BOUND_SOURCE_SHA256,
        page_lookup=retained["page_lookup"],
        adoption=_independent_adoption(construction),
        treatment=_synthetic_treatment(),
    )
    assert standardized_to_payload(financials) == original
    assert admitted.production_admitted is True
    assert admitted.authorization_kind == AUTHORIZATION_INDEPENDENT
    assert admitted.real_company_acceptance is True
    assert admitted.mapping_status == "independently_supplied_decision"
    assert admitted.grouping_is_accepted_source_fact is False
    expected = _independent_observation_evidence(
        retained["observations"], retained["page_lookup"]
    )
    with tempfile.TemporaryDirectory() as tmp:
        std_path, adm_path = _persist_admitted(retained, admitted, Path(tmp))
        recovered = _run_fresh_load(std_path, adm_path)
        bundle = load_admitted_normalization_candidate(std_path, adm_path)
    assert recovered["authorization_kind"] == AUTHORIZATION_INDEPENDENT
    assert recovered["real_company_acceptance"] is True
    assert recovered["mapping_status"] == "independently_supplied_decision"
    assert recovered["grouping_is_accepted_source_fact"] is False
    assert recovered["values"] == list(EXPECTED_ANALYTICAL)
    assert recovered["face_values"] == list(EXPECTED_FACE)
    assert recovered["observations"] == expected
    assert bundle.authorization_kind == AUTHORIZATION_INDEPENDENT
    assert bundle.real_company_acceptance is True
    assert bundle.grouping_is_accepted_source_fact is False
    assert recovered["transformation"] == SIGN_TRANSFORMATION
    assert recovered["sign_conversions_applied"] == 1
    assert all(
        item["period"] == expect["period"]
        for item, expect in zip(recovered["observations"], expected, strict=True)
    )
    assert _snapshot_obs(retained["observations"]) == retained["obs_snapshot"]
    assert retained["live_std_bytes"] == (LIVE_DIR / "standardized.json").read_bytes()

