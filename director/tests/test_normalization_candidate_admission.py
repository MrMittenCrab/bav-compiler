"""Gated opt-in normalization candidate handoff (Step 9M.2.4.1.1.1.68)."""

from __future__ import annotations

import pytest

from director.tests.normalization_candidate_admission_support import (
    ANALYTICAL_CONCEPT,
    ANALYTICAL_SELECTOR,
    ASSUMPTIONS,
    AUTHENTICATED_B,
    AUTHORIZATION_SYNTHETIC,
    AUTHORIZED_IS_IDENTITIES,
    BOUND_SOURCE_SHA256,
    C1,
    C2,
    COMPARISON_B,
    EXPECTED_ANALYTICAL,
    EXPECTED_BRANCH,
    EXPECTED_FACE,
    EXPECTED_NONRECURRING_PRETAX,
    EXPECTED_RECURRING_PRETAX,
    EXTRACTED_EIGHT_RELOCATED,
    EXTRACT_BLOB,
    HISTORICAL_REVIEWED_ATTEMPT,
    HISTORICAL_REVIEWED_B,
    HISTORICAL_REVIEWED_CHECKPOINT,
    HISTORICAL_REVIEWED_PLAN,
    LEDGER_PERIODS,
    LIVE_DIR,
    ORDINARY_SELECTORS,
    ORDINARY_STD,
    ORDINARY_STD_SHA256,
    Path,
    RECONCILED_STD,
    RELOCATED,
    REQUIRED_PROVENANCE_FIELDS,
    RETAINED_LIVE_CONFLICTS,
    RETAINED_LIVE_PROV,
    RETAINED_LIVE_STD,
    RETIRED,
    REVIEWED_BASELINE_1091,
    REVIEWED_CHECKPOINT,
    REVIEWED_CHECKPOINT_1091,
    REVIEWED_CHECKPOINT_1092,
    REVIEWED_CHECKPOINT_1093,
    REVIEWED_CHECKPOINT_1094,
    REVIEWED_PARENT_1093,
    REVIEWED_PARENT_1094,
    ROOT,
    SIGN_TRANSFORMATION,
    STAYED,
    WORK_ID,
    _assert_authenticated_lifecycle,
    _authenticate_current_repository_baseline,
    _authorize_head_against_baseline,
    _axis_is_obs,
    _bound_attempt,
    _expected_live_lifecycle,
    _git_out,
    _handoff,
    _isolated_checkpoint_records,
    _isolated_implementation_records,
    _materialize_git_tree,
    _page_lookup_rows,
    _read_autocycle_plan,
    _read_resume_state,
    _reject_baseline_binding,
    _reject_ownership_mutations,
    _require_git_commit,
    _resolve_implement_base_sha,
    _run_isolated_compare,
    _sha256,
    _snapshot_obs,
    _synthetic_adoption,
    _synthetic_treatment,
    canonical_fiscal_periods,
    construct_provisional_candidate,
    copy,
    json,
    normalization_cases,
    pytest,
    resolve_income_statement_selector,
    retained,
    run_normalization_candidate_handoff,
    standardized_from_payload,
    standardized_to_payload,
    subprocess,
    tempfile,
)

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
    for old, new in STAYED.items():
        wt = _git_out(["git", "hash-object", str(ROOT / new)])
        c1 = _git_out(["git", "rev-parse", f"{C1}:{old}"])
        c2 = _git_out(["git", "rev-parse", f"{C2}:{old}"])
        assert wt == c1 == c2, (old, new)
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

def test_b_and_current_isolated_agreement(retained):
    parent = _git_out(["git", "rev-parse", f"{REVIEWED_CHECKPOINT}^"])
    assert parent == COMPARISON_B
    reviewed_parent = _git_out(["git", "rev-parse", f"{REVIEWED_CHECKPOINT_1091}^"])
    assert reviewed_parent == REVIEWED_BASELINE_1091
    reviewed_1092_parent = _git_out(["git", "rev-parse", f"{REVIEWED_CHECKPOINT_1092}^"])
    assert reviewed_1092_parent == AUTHENTICATED_B
    reviewed_1093_parent = _git_out(["git", "rev-parse", f"{REVIEWED_CHECKPOINT_1093}^"])
    assert reviewed_1093_parent == REVIEWED_PARENT_1093
    reviewed_1094_parent = _git_out(["git", "rev-parse", f"{REVIEWED_CHECKPOINT_1094}^"])
    assert reviewed_1094_parent == REVIEWED_PARENT_1094
    expected_live = _expected_live_lifecycle()
    binding = _authenticate_current_repository_baseline()
    _assert_authenticated_lifecycle(binding, expected_live)
    implement_base = binding["implement_base"]
    assert implement_base != REVIEWED_CHECKPOINT_1094
    assert binding["attempt_id"] != HISTORICAL_REVIEWED_ATTEMPT
    assert binding["recorded_checkpoint"] != HISTORICAL_REVIEWED_CHECKPOINT
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
        implement_tree = root / "implement_b"
        pre_tree.mkdir()
        auth_tree.mkdir()
        implement_tree.mkdir()
        _materialize_git_tree(pre_tree, COMPARISON_B)
        _materialize_git_tree(auth_tree, AUTHENTICATED_B)
        _materialize_git_tree(implement_tree, implement_base)
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
        implement_admission = (
            implement_tree / "core/ingestion/normalization_candidate_admission.py"
        ).read_bytes()
        assert implement_admission == subprocess.check_output(
            ["git", "show", f"{implement_base}:core/ingestion/normalization_candidate_admission.py"],
            cwd=ROOT,
        )
        baseline = _run_isolated_compare("b", pre_tree, casebook)
        authenticated = _run_isolated_compare("authenticated_b", auth_tree, casebook)
        implement_b = _run_isolated_compare("authenticated_b", implement_tree, casebook)
    current_gates = {
        key: value
        for key, value in current.items()
        if key not in {"persistence", "repaired_persistence"}
    }
    baseline_gates = {
        key: value
        for key, value in baseline.items()
        if key not in {"persistence", "repaired_persistence"}
    }
    authenticated_gates = {
        key: value
        for key, value in authenticated.items()
        if key not in {"persistence", "repaired_persistence"}
    }
    implement_b_gates = {
        key: value
        for key, value in implement_b.items()
        if key not in {"persistence", "repaired_persistence"}
    }
    assert current_gates == baseline_gates
    assert current_gates == authenticated_gates
    assert current_gates == implement_b_gates
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
    assert "save_admitted_normalization_candidate" in persistence["contract"]["admission_persist_names"]
    assert persistence["contract"]["documentary_accepts_standardized"] is False
    assert persistence["contract"]["documentary_error"] == "TypeError"
    assert persistence["contract"]["limitation"] == "no_admission_provenance_persist_reload"
    assert baseline["persistence"]["contract"]["admission_persist_names"] == []
    assert authenticated["persistence"]["contract"]["admission_persist_names"] == []
    assert baseline["persistence"]["contract"]["limitation"] == "no_admission_provenance_persist_reload"
    assert authenticated["persistence"]["contract"]["limitation"] == "no_admission_provenance_persist_reload"
    assert baseline["repaired_persistence"]["available"] is False
    assert authenticated["repaired_persistence"]["available"] is False
    assert implement_b["repaired_persistence"]["available"] is True
    assert implement_b["repaired_persistence"]["recovered_values"] == list(EXPECTED_ANALYTICAL)
    repaired = current["repaired_persistence"]
    assert repaired["available"] is True
    assert repaired["recovered_values"] == list(EXPECTED_ANALYTICAL)
    assert repaired["face_values"] == list(EXPECTED_FACE)
    assert repaired["transformation"] == SIGN_TRANSFORMATION
    assert repaired["sign_conversions_applied"] == 1
    assert repaired["authorization_kind"] == AUTHORIZATION_SYNTHETIC
    assert repaired["after_tax_available"] is False
    assert repaired["observations"]
    assert any(item["printed_page_status"] == "unresolved" for item in repaired["observations"])
    assert _snapshot_obs(retained["observations"]) == retained["obs_snapshot"]
    assert retained["live_std_bytes"] == (LIVE_DIR / "standardized.json").read_bytes()

def test_baseline_authentication_implementation_and_checkpoint_bindings():
    current_b = _resolve_implement_base_sha()
    resume = _read_resume_state()
    assert resume.get("IMPLEMENT_BASE_SHA") == current_b
    assert resume.get("STATE_BRANCH") == EXPECTED_BRANCH
    _require_git_commit(current_b)
    assert current_b != HISTORICAL_REVIEWED_B
    expected_live = _expected_live_lifecycle()
    current_attempt_id = expected_live["attempt_id"]
    current_plan_id = str(_read_autocycle_plan().get("plan_id") or "").strip()
    assert current_attempt_id
    assert current_plan_id
    assert current_attempt_id != HISTORICAL_REVIEWED_ATTEMPT
    assert current_plan_id != HISTORICAL_REVIEWED_PLAN

    shared = dict(
        branch=EXPECTED_BRANCH,
        work_id=WORK_ID,
        bound_work_id=WORK_ID,
        attempt_id=current_attempt_id,
        bound_attempt_id=current_attempt_id,
        attempt_baseline=current_b,
    )
    assert _authorize_head_against_baseline(
        head=current_b,
        implement_base=current_b,
        **shared,
    ) == "implementation"
    assert _authorize_head_against_baseline(
        head=HISTORICAL_REVIEWED_CHECKPOINT,
        branch=EXPECTED_BRANCH,
        implement_base=HISTORICAL_REVIEWED_B,
        recorded_checkpoint=HISTORICAL_REVIEWED_CHECKPOINT,
        recorded_checkpoint_parent=HISTORICAL_REVIEWED_B,
        work_id=WORK_ID,
        bound_work_id=WORK_ID,
        attempt_id=HISTORICAL_REVIEWED_ATTEMPT,
        bound_attempt_id=HISTORICAL_REVIEWED_ATTEMPT,
        attempt_baseline=HISTORICAL_REVIEWED_B,
    ) == "checkpoint"

    missing_identity_kwargs = dict(
        head=current_b,
        branch=EXPECTED_BRANCH,
        implement_base=current_b,
        attempt_baseline=current_b,
    )
    with pytest.raises(AssertionError, match="unavailable_ownership_binding"):
        _authorize_head_against_baseline(**missing_identity_kwargs)
    with pytest.raises(AssertionError, match="unavailable_ownership_binding"):
        _authorize_head_against_baseline(
            work_id=WORK_ID,
            bound_work_id="",
            attempt_id="present",
            bound_attempt_id="present",
            **missing_identity_kwargs,
        )
    with pytest.raises(AssertionError, match="unavailable_ownership_binding"):
        _authorize_head_against_baseline(
            work_id=WORK_ID,
            bound_work_id=WORK_ID,
            attempt_id="",
            bound_attempt_id="present",
            **missing_identity_kwargs,
        )
    with pytest.raises(AssertionError, match="mismatched_attempt"):
        _authorize_head_against_baseline(
            head=current_b,
            implement_base=current_b,
            work_id=WORK_ID,
            bound_work_id="unrelated-work",
            attempt_id="same",
            bound_attempt_id="same",
            attempt_baseline=current_b,
            branch=EXPECTED_BRANCH,
        )
    with pytest.raises(AssertionError, match="mismatched_attempt"):
        _authorize_head_against_baseline(
            head=current_b,
            implement_base=current_b,
            work_id=WORK_ID,
            bound_work_id=WORK_ID,
            attempt_id="expected-attempt",
            bound_attempt_id="observed-attempt",
            attempt_baseline=current_b,
            branch=EXPECTED_BRANCH,
        )
    with pytest.raises(AssertionError, match="mismatched_baseline"):
        _authorize_head_against_baseline(
            head=current_b,
            implement_base=current_b,
            work_id=WORK_ID,
            bound_work_id=WORK_ID,
            attempt_id="same",
            bound_attempt_id="same",
            attempt_baseline=HISTORICAL_REVIEWED_B,
            branch=EXPECTED_BRANCH,
        )
    with pytest.raises(AssertionError, match="unauthorized_checkpoint"):
        _authorize_head_against_baseline(
            head=HISTORICAL_REVIEWED_CHECKPOINT,
            implement_base=current_b,
            recorded_checkpoint="",
            recorded_checkpoint_parent="",
            head_parent=current_b,
            **shared,
        )
    with pytest.raises(AssertionError, match="unauthorized_checkpoint"):
        _authorize_head_against_baseline(
            head=HISTORICAL_REVIEWED_CHECKPOINT,
            implement_base=current_b,
            recorded_checkpoint=REVIEWED_CHECKPOINT_1094,
            recorded_checkpoint_parent=REVIEWED_PARENT_1094,
            head_parent=current_b,
            **shared,
        )
    with pytest.raises(AssertionError, match="unauthorized_checkpoint"):
        _authorize_head_against_baseline(
            head=current_b,
            implement_base=HISTORICAL_REVIEWED_B,
            recorded_checkpoint=HISTORICAL_REVIEWED_CHECKPOINT,
            recorded_checkpoint_parent=HISTORICAL_REVIEWED_B,
            work_id=WORK_ID,
            bound_work_id=WORK_ID,
            attempt_id=HISTORICAL_REVIEWED_ATTEMPT,
            bound_attempt_id=HISTORICAL_REVIEWED_ATTEMPT,
            attempt_baseline=HISTORICAL_REVIEWED_B,
            branch=EXPECTED_BRANCH,
        )
    with pytest.raises(AssertionError, match="inconsistent_branch"):
        _authorize_head_against_baseline(
            head=current_b,
            branch="main",
            implement_base=current_b,
            work_id=WORK_ID,
            bound_work_id=WORK_ID,
            attempt_id="same",
            bound_attempt_id="same",
            attempt_baseline=current_b,
        )

    # Live execution: authenticate against actual controller bindings.
    live = _authenticate_current_repository_baseline()
    _assert_authenticated_lifecycle(live, expected_live)
    assert live["work_id"] == WORK_ID
    assert live["attempt_id"] != HISTORICAL_REVIEWED_ATTEMPT
    assert live["recorded_checkpoint"] != HISTORICAL_REVIEWED_CHECKPOINT

    # Fixture evidence: implementation path, constructed independently of live phase.
    implementation_fixture = _isolated_implementation_records(
        implement_base=current_b,
        plan_id=current_plan_id,
        attempt_id=current_attempt_id,
    )
    implemented = _authenticate_current_repository_baseline(implementation_fixture)
    assert implemented["state"] == "implementation"
    assert implemented["head"] == current_b == implemented["implement_base"]
    assert implemented["attempt_id"] == implemented["bound_attempt_id"] == current_attempt_id
    assert implemented["work_id"] == implemented["bound_work_id"] == WORK_ID
    assert implemented["recorded_checkpoint"] == ""
    assert implemented["attempt_baseline"] == current_b
    assert implemented["branch"] == EXPECTED_BRANCH

    # Fixture evidence: exact-checkpoint path, historical comparator tuple only.
    checkpoint_fixture = _isolated_checkpoint_records(
        implement_base=HISTORICAL_REVIEWED_B,
        plan_id=HISTORICAL_REVIEWED_PLAN,
        attempt_id=HISTORICAL_REVIEWED_ATTEMPT,
        checkpoint_sha=HISTORICAL_REVIEWED_CHECKPOINT,
        checkpoint_parent=HISTORICAL_REVIEWED_B,
    )
    exact = _authenticate_current_repository_baseline(checkpoint_fixture)
    assert exact["state"] == "checkpoint"
    assert exact["head"] == HISTORICAL_REVIEWED_CHECKPOINT
    assert exact["attempt_id"] == exact["bound_attempt_id"] == HISTORICAL_REVIEWED_ATTEMPT
    assert exact["recorded_checkpoint"] == HISTORICAL_REVIEWED_CHECKPOINT
    assert exact["recorded_checkpoint_parent"] == HISTORICAL_REVIEWED_B
    assert exact["implement_base"] == HISTORICAL_REVIEWED_B
    assert exact["work_id"] == exact["bound_work_id"] == WORK_ID
    assert exact["attempt_baseline"] == HISTORICAL_REVIEWED_B
    assert exact["branch"] == EXPECTED_BRANCH

    _reject_ownership_mutations(implementation_fixture)
    _reject_ownership_mutations(checkpoint_fixture)
    _reject_baseline_binding(implementation_fixture, foreign_baseline=HISTORICAL_REVIEWED_B)
    _reject_baseline_binding(checkpoint_fixture, foreign_baseline=REVIEWED_PARENT_1094)

    wrong_checkpoint_parent = copy.deepcopy(checkpoint_fixture)
    wrong_checkpoint_parent["git_checkpoint_parent"] = REVIEWED_PARENT_1094
    with pytest.raises(AssertionError, match="unauthorized_checkpoint"):
        _authenticate_current_repository_baseline(wrong_checkpoint_parent)

    no_recorded_child = _isolated_implementation_records(
        implement_base=HISTORICAL_REVIEWED_B,
        plan_id=HISTORICAL_REVIEWED_PLAN,
        attempt_id=HISTORICAL_REVIEWED_ATTEMPT,
    )
    _bound_attempt(no_recorded_child)["checkpoint_sha"] = None
    no_recorded_child["git_head"] = HISTORICAL_REVIEWED_CHECKPOINT
    no_recorded_child["git_head_parent"] = HISTORICAL_REVIEWED_B
    with pytest.raises(AssertionError, match="unauthorized_checkpoint"):
        _authenticate_current_repository_baseline(no_recorded_child)

    stale_old_b = _isolated_implementation_records(
        implement_base=HISTORICAL_REVIEWED_B,
        plan_id=HISTORICAL_REVIEWED_PLAN,
        attempt_id=HISTORICAL_REVIEWED_ATTEMPT,
    )
    _bound_attempt(stale_old_b)["checkpoint_sha"] = REVIEWED_CHECKPOINT_1094
    stale_old_b["git_head"] = HISTORICAL_REVIEWED_CHECKPOINT
    stale_old_b["git_head_parent"] = HISTORICAL_REVIEWED_B
    stale_old_b["git_checkpoint_parent"] = REVIEWED_PARENT_1094
    with pytest.raises(AssertionError, match="unauthorized_checkpoint"):
        _authenticate_current_repository_baseline(stale_old_b)

    other_child = _isolated_checkpoint_records(
        implement_base=HISTORICAL_REVIEWED_B,
        plan_id=HISTORICAL_REVIEWED_PLAN,
        attempt_id=HISTORICAL_REVIEWED_ATTEMPT,
        checkpoint_sha=HISTORICAL_REVIEWED_CHECKPOINT,
        checkpoint_parent=HISTORICAL_REVIEWED_B,
    )
    _bound_attempt(other_child)["phase"] = "running"
    other_child["git_head"] = current_b
    other_child["git_head_parent"] = HISTORICAL_REVIEWED_B
    with pytest.raises(AssertionError, match="unauthorized_checkpoint"):
        _authenticate_current_repository_baseline(other_child)

