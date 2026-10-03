"""Gated opt-in normalization candidate handoff (Step 9M.2.4.1.1.1.68)."""

from __future__ import annotations

import pytest

from bav.director.tests.normalization_candidate_admission_support import (
    ANALYTICAL_CONCEPT,
    ANALYTICAL_LABEL,
    ANALYTICAL_SELECTOR,
    ASSUMPTIONS,
    AUTHORIZATION_INDEPENDENT,
    AUTHORIZATION_SYNTHETIC,
    AUTHORIZED_IS_IDENTITIES,
    AdmissionProvenanceError,
    BOUND_SOURCE_SHA256,
    CF_AUDIT_IDENTITIES,
    EXPECTED_ANALYTICAL,
    EXPECTED_FACE,
    EXPECTED_NONRECURRING_PRETAX,
    EXPECTED_PHYSICAL_PAGES,
    EXPECTED_PRINTED_PAGES,
    EXPECTED_RECURRING_PRETAX,
    LEDGER_PERIODS,
    LIVE_DIR,
    NOTE_TAX_EFFECTS,
    ORDINARY_DIR,
    ORDINARY_SELECTORS,
    Path,
    REQUIRED_PROVENANCE_FIELDS,
    SEGMENT_BRIDGE_TOLERANCE,
    SIGN_TRANSFORMATION,
    UNDEFINED_RATIO,
    _admission_persist_names,
    _admit,
    _documentary_hits,
    _documentary_needles,
    _dummy_anchor,
    _handoff,
    _independent_expected_provenance,
    _independent_fingerprint,
    _independent_observation_evidence,
    _load_json,
    _locator_attached,
    _persist_admitted,
    _run_fresh_load,
    _run_fresh_load_rejection,
    _snapshot_obs,
    _synthetic_adoption,
    _synthetic_treatment,
    _write_mutated_bundle,
    canonical_fiscal_periods,
    compute_normalization_series,
    construct_provisional_candidate,
    copy,
    date,
    json,
    line_identity,
    load_admitted_normalization_candidate,
    normalization_cases,
    pytest,
    resolve_income_statement_selector,
    retained,
    run_normalization_candidate_handoff,
    save_admitted_normalization_candidate,
    standardized_from_payload,
    standardized_to_payload,
    tempfile,
)

def test_segment_bridge_tolerance_unchanged():
    assert SEGMENT_BRIDGE_TOLERANCE == 0.0

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
    assert "persist_admitted_normalization_candidate" in _admission_persist_names()
    live_hits = _documentary_hits(_load_json(LIVE_DIR / "provenance.json"))
    ordinary_hits = _documentary_hits(_load_json(ORDINARY_DIR / "provenance.json"))
    assert live_hits == _documentary_needles()
    assert ordinary_hits == _documentary_needles()
    from bav.modeler.ingestion.filing_standardizer import reconciliation_provenance_payload

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

def test_production_admission_bundle_save_load_fresh_process(retained):
    expected = _independent_observation_evidence(
        retained["observations"], retained["page_lookup"]
    )
    admitted = _admit(retained)
    assert admitted.production_admitted is True
    original_obs = _snapshot_obs(retained["observations"])
    with tempfile.TemporaryDirectory() as tmp:
        std_path = Path(tmp) / "standardized.json"
        adm_path = Path(tmp) / "normalization_candidate_admission.json"
        save_admitted_normalization_candidate(
            admitted,
            standardized_path=std_path,
            admission_path=adm_path,
        )
        del admitted
        recovered = _run_fresh_load(std_path, adm_path)
        bundle = load_admitted_normalization_candidate(std_path, adm_path)
    assert recovered["concept"] == ANALYTICAL_CONCEPT
    assert recovered["label"] == ANALYTICAL_LABEL
    assert recovered["identity_key"] == (
        f"concept={ANALYTICAL_CONCEPT}|label={ANALYTICAL_LABEL.casefold()}"
    )
    assert recovered["values"] == list(EXPECTED_ANALYTICAL)
    assert recovered["face_values"] == list(EXPECTED_FACE)
    assert recovered["analytical_values"] == list(EXPECTED_ANALYTICAL)
    assert recovered["fiscal_periods"] == list(LEDGER_PERIODS)
    assert recovered["transformation"] == SIGN_TRANSFORMATION
    assert recovered["sign_conversions_applied"] == 1
    assert recovered["authorization_kind"] == AUTHORIZATION_SYNTHETIC
    assert recovered["mapping_status"] == "synthetic_test_authorization"
    assert recovered["after_tax_available"] is False
    assert recovered["tax_disposition"] == "unresolved"
    assert recovered["grouping_is_accepted_source_fact"] is False
    assert recovered["real_company_acceptance"] is False
    assert recovered["candidate_configuration"]["selector"] == ANALYTICAL_SELECTOR
    recovered_obs = recovered["observations"]
    assert recovered_obs == expected
    assert len(recovered_obs) == 11
    by_period = {period: [] for period in LEDGER_PERIODS}
    for item in recovered_obs:
        by_period[item["period"]].append(item)
        assert item["source_hash"] in BOUND_SOURCE_SHA256.values()
        assert item["row_identity"] in AUTHORIZED_IS_IDENTITIES
        assert item["currency"] == "USD"
        assert item["unit_scale"] == "thousands"
        assert item["printed_page_status"] in {"resolved", "unresolved", "unavailable"}
        if item["printed_page_status"] != "resolved":
            assert item["printed_page"] is None
        if item["printed_page_status"] == "unresolved":
            assert item["physical_page"] is not None
            assert item["printed_page"] != item["physical_page"]
    assert {item["printed_page_status"] for item in by_period["2025-02-02"]} == {"unresolved"}
    assert {item["printed_page_status"] for item in by_period["2026-02-01"]} == {"unresolved"}
    assert any(item["printed_page_status"] == "resolved" for item in recovered_obs)
    assert tuple(int(v) for v in bundle.analytical_values) == EXPECTED_ANALYTICAL
    assert tuple(int(v) for v in bundle.face_values) == EXPECTED_FACE
    assert bundle.sign_conversions_applied == 1
    for period, expect in _independent_expected_provenance(
        retained["observations"], retained["page_lookup"]
    ).items():
        members = [item for item in recovered_obs if item["period"] == period]
        assert {item["fingerprint"] for item in members} == set(expect["observation_fingerprints"])
        assert {item["source_hash"] for item in members} == set(expect["source_hashes"])
        assert {item["row_identity"] for item in members} == set(expect["row_identities"])
        assert {item["physical_page"] for item in members} == set(expect["physical_pages"])
        assert {item["printed_page"] for item in members if item["printed_page"] is not None} == set(
            expect["printed_pages"]
        )
        assert {item["reported_amount"] for item in members} == {expect["face_reported_usd_thousands"]}
    repeated = run_normalization_candidate_handoff(
        retained["observations"],
        bundle.financials,
        bound_source_hashes=BOUND_SOURCE_SHA256,
        page_lookup=retained["page_lookup"],
        adoption=_synthetic_adoption(
            construct_provisional_candidate(
                retained["observations"],
                bound_source_hashes=BOUND_SOURCE_SHA256,
                page_lookup=retained["page_lookup"],
            )
        ),
        treatment=_synthetic_treatment(),
    )
    assert repeated.blocked_reason == "repeated_admission"
    assert repeated.production_admitted is False
    assert _snapshot_obs(retained["observations"]) == original_obs
    assert retained["live_std_bytes"] == (LIVE_DIR / "standardized.json").read_bytes()

def test_admission_bundle_rejects_mismatched_missing_and_blocked(retained):
    admitted = _admit(retained)
    blocked = _handoff(retained)
    assert blocked.production_admitted is False
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        std_path = root / "standardized.json"
        adm_path = root / "normalization_candidate_admission.json"
        save_admitted_normalization_candidate(
            admitted, standardized_path=std_path, admission_path=adm_path
        )
        with pytest.raises(AdmissionProvenanceError, match="blocked_or_provisional_handoff"):
            save_admitted_normalization_candidate(
                blocked,
                standardized_path=root / "blocked.json",
                admission_path=root / "blocked_admission.json",
            )
        construction = construct_provisional_candidate(
            retained["observations"],
            bound_source_hashes=BOUND_SOURCE_SHA256,
            page_lookup=retained["page_lookup"],
        )
        provisional = _handoff(
            retained,
            adoption=_synthetic_adoption(construction).__class__(
                **{**_synthetic_adoption(construction).__dict__, "decision_status": "provisional"}
            ),
            treatment=_synthetic_treatment(),
        )
        assert provisional.blocked_reason == "provisional_adoption"
        with pytest.raises(AdmissionProvenanceError, match="blocked_or_provisional_handoff"):
            save_admitted_normalization_candidate(
                provisional,
                standardized_path=root / "provisional.json",
                admission_path=root / "provisional_admission.json",
            )
        assert not (root / "blocked.json").exists()
        assert not (root / "blocked_admission.json").exists()
        assert not (root / "provisional.json").exists()
        assert not (root / "provisional_admission.json").exists()

        missing_adm = root / "missing_admission.json"
        with pytest.raises(AdmissionProvenanceError, match="missing_admission_evidence"):
            load_admitted_normalization_candidate(std_path, missing_adm)

        company = json.loads(adm_path.read_text(encoding="utf-8"))
        company["company"] = "NOT_LULU"
        company_path = root / "company.json"
        company_path.write_text(json.dumps(company), encoding="utf-8")
        with pytest.raises(AdmissionProvenanceError, match="mismatched_company_binding"):
            load_admitted_normalization_candidate(std_path, company_path)

        line = json.loads(adm_path.read_text(encoding="utf-8"))
        line["analytical_line"]["concept"] = "impairment_and_restructuring"
        line["analytical_line"]["identity"] = "concept=impairment_and_restructuring|label=x"
        line_path = root / "line.json"
        line_path.write_text(json.dumps(line), encoding="utf-8")
        with pytest.raises(AdmissionProvenanceError, match="mismatched_line_binding"):
            load_admitted_normalization_candidate(std_path, line_path)

        period = json.loads(adm_path.read_text(encoding="utf-8"))
        period["fiscal_periods"] = list(LEDGER_PERIODS[1:])
        period_path = root / "period.json"
        period_path.write_text(json.dumps(period), encoding="utf-8")
        with pytest.raises(AdmissionProvenanceError, match="mismatched_period_binding"):
            load_admitted_normalization_candidate(std_path, period_path)

        value_std = json.loads(std_path.read_text(encoding="utf-8"))
        for item in value_std["income_statement"]:
            if item.get("concept") == ANALYTICAL_CONCEPT:
                item["values"][LEDGER_PERIODS[1]] = 1
        value_path = root / "value.json"
        value_path.write_text(json.dumps(value_std), encoding="utf-8")
        with pytest.raises(AdmissionProvenanceError, match="mismatched_value_binding"):
            load_admitted_normalization_candidate(value_path, adm_path)

        stale = json.loads(adm_path.read_text(encoding="utf-8"))
        stale["observations"][0]["fingerprint"] = "0" * 64
        stale_path = root / "stale.json"
        stale_path.write_text(json.dumps(stale), encoding="utf-8")
        with pytest.raises(AdmissionProvenanceError, match="stale_admission_evidence"):
            load_admitted_normalization_candidate(std_path, stale_path)

        missing_obs = json.loads(adm_path.read_text(encoding="utf-8"))
        missing_obs["observations"] = [
            item
            for item in missing_obs["observations"]
            if item["period"] != LEDGER_PERIODS[0]
        ]
        missing_path = root / "missing_obs.json"
        missing_path.write_text(json.dumps(missing_obs), encoding="utf-8")
        with pytest.raises(AdmissionProvenanceError, match="missing_admission_evidence"):
            load_admitted_normalization_candidate(std_path, missing_path)

        ambiguous_std = json.loads(std_path.read_text(encoding="utf-8"))
        analytical = next(
            item
            for item in ambiguous_std["income_statement"]
            if item.get("concept") == ANALYTICAL_CONCEPT
        )
        ambiguous_std["income_statement"].append(copy.deepcopy(analytical))
        ambiguous_path = root / "ambiguous.json"
        ambiguous_path.write_text(json.dumps(ambiguous_std), encoding="utf-8")
        with pytest.raises(AdmissionProvenanceError, match="ambiguous_admission_linkage"):
            load_admitted_normalization_candidate(ambiguous_path, adm_path)

    ordinary = standardized_from_payload(copy.deepcopy(retained["ordinary_payload"]), strict=True)
    assert not any(item.concept == ANALYTICAL_CONCEPT for item in ordinary.income_statement)
    assert _snapshot_obs(retained["observations"]) == retained["obs_snapshot"]

def test_production_loader_rejects_four_demonstrated_bypasses(retained):
    admitted = _admit(retained)
    original_obs = _snapshot_obs(retained["observations"])
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        std_path, adm_path = _persist_admitted(retained, admitted, root)
        valid = json.loads(adm_path.read_text(encoding="utf-8"))

        provisional = copy.deepcopy(valid)
        provisional["adoption"]["decision_status"] = "provisional"
        provisional_path = _write_mutated_bundle(root, provisional, "provisional.json")
        with pytest.raises(AdmissionProvenanceError, match="blocked_or_provisional_handoff"):
            load_admitted_normalization_candidate(std_path, provisional_path)
        rejected = _run_fresh_load_rejection(std_path, provisional_path)
        assert rejected["reason"] == "blocked_or_provisional_handoff"

        empty_treatment = copy.deepcopy(valid)
        empty_treatment["treatment"] = {}
        empty_path = _write_mutated_bundle(root, empty_treatment, "empty_treatment.json")
        with pytest.raises(AdmissionProvenanceError, match="missing_admission_evidence"):
            load_admitted_normalization_candidate(std_path, empty_path)
        rejected = _run_fresh_load_rejection(std_path, empty_path)
        assert rejected["reason"] == "missing_admission_evidence"

        synthetic_as_real = copy.deepcopy(valid)
        synthetic_as_real["real_company_acceptance"] = True
        synthetic_path = _write_mutated_bundle(root, synthetic_as_real, "synthetic_as_real.json")
        with pytest.raises(AdmissionProvenanceError, match="inconsistent_admission_binding"):
            load_admitted_normalization_candidate(std_path, synthetic_path)
        rejected = _run_fresh_load_rejection(std_path, synthetic_path)
        assert rejected["reason"] == "inconsistent_admission_binding"

        changed_hash = copy.deepcopy(valid)
        changed_hash["observations"][0]["source_hash"] = "0" * 64
        hash_path = _write_mutated_bundle(root, changed_hash, "changed_source_hash.json")
        with pytest.raises(AdmissionProvenanceError, match="inconsistent_admission_binding"):
            load_admitted_normalization_candidate(std_path, hash_path)
        rejected = _run_fresh_load_rejection(std_path, hash_path)
        assert rejected["reason"] == "inconsistent_admission_binding"

        recovered = _run_fresh_load(std_path, adm_path)
        assert recovered["real_company_acceptance"] is False
        assert recovered["authorization_kind"] == AUTHORIZATION_SYNTHETIC
    assert _snapshot_obs(retained["observations"]) == original_obs
    assert retained["live_std_bytes"] == (LIVE_DIR / "standardized.json").read_bytes()

def test_admission_bundle_rejects_authorization_treatment_and_fingerprint_disagreement(retained):
    admitted = _admit(retained)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        std_path, adm_path = _persist_admitted(retained, admitted, root)
        valid = json.loads(adm_path.read_text(encoding="utf-8"))

        auth_mismatch = copy.deepcopy(valid)
        auth_mismatch["authorization_kind"] = AUTHORIZATION_INDEPENDENT
        auth_path = _write_mutated_bundle(root, auth_mismatch, "auth_mismatch.json")
        with pytest.raises(AdmissionProvenanceError, match="inconsistent_admission_binding"):
            load_admitted_normalization_candidate(std_path, auth_path)
        assert _run_fresh_load_rejection(std_path, auth_path)["reason"] == (
            "inconsistent_admission_binding"
        )

        config_mismatch = copy.deepcopy(valid)
        config_mismatch["candidate_configuration"]["referenceTreatment"] = "Recurring"
        config_path = _write_mutated_bundle(root, config_mismatch, "config_mismatch.json")
        with pytest.raises(AdmissionProvenanceError, match="inconsistent_admission_binding"):
            load_admitted_normalization_candidate(std_path, config_path)
        assert _run_fresh_load_rejection(std_path, config_path)["reason"] == (
            "inconsistent_admission_binding"
        )

        fingerprint_mismatch = copy.deepcopy(valid)
        fingerprint_mismatch["observations"][0]["reported_amount"] = 1
        fp_path = _write_mutated_bundle(root, fingerprint_mismatch, "fingerprint_mismatch.json")
        with pytest.raises(AdmissionProvenanceError, match="inconsistent_admission_binding"):
            load_admitted_normalization_candidate(std_path, fp_path)
        assert _run_fresh_load_rejection(std_path, fp_path)["reason"] == (
            "inconsistent_admission_binding"
        )
        stale_inputs = copy.deepcopy(valid)
        stale_inputs["observations"][0]["fingerprint_inputs"]["value"] = 1
        stale_inputs_path = _write_mutated_bundle(root, stale_inputs, "stale_inputs.json")
        with pytest.raises(AdmissionProvenanceError, match="stale_admission_evidence"):
            load_admitted_normalization_candidate(std_path, stale_inputs_path)
        assert _run_fresh_load_rejection(std_path, stale_inputs_path)["reason"] == (
            "stale_admission_evidence"
        )

        missing_inputs = copy.deepcopy(valid)
        for item in missing_inputs["observations"]:
            item.pop("fingerprint_inputs", None)
        missing_path = _write_mutated_bundle(root, missing_inputs, "missing_inputs.json")
        with pytest.raises(AdmissionProvenanceError, match="stale_admission_evidence"):
            load_admitted_normalization_candidate(std_path, missing_path)
        assert _run_fresh_load_rejection(std_path, missing_path)["reason"] == (
            "stale_admission_evidence"
        )

        old_schema = copy.deepcopy(valid)
        old_schema["schema"] = "normalization_candidate_admission/v1"
        old_path = _write_mutated_bundle(root, old_schema, "old_schema.json")
        with pytest.raises(AdmissionProvenanceError, match="stale_admission_evidence"):
            load_admitted_normalization_candidate(std_path, old_path)
        assert _run_fresh_load_rejection(std_path, old_path)["reason"] == (
            "stale_admission_evidence"
        )

def test_production_loader_rejects_period_reassignment_and_false_transformation(retained):
    admitted = _admit(retained)
    original_obs = _snapshot_obs(retained["observations"])
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        std_path, adm_path = _persist_admitted(retained, admitted, root)
        valid = json.loads(adm_path.read_text(encoding="utf-8"))
        assert valid["transformation"] == SIGN_TRANSFORMATION
        source_period = "2025-02-02"
        reassigned_period = "2026-02-01"
        moved = copy.deepcopy(valid)
        target = next(item for item in moved["observations"] if item["period"] == source_period)
        assert target["fingerprint_inputs"]["period"] == source_period
        target["period"] = reassigned_period
        assert target["fingerprint_inputs"]["period"] == source_period
        moved_path = _write_mutated_bundle(root, moved, "period_reassigned.json")
        with pytest.raises(AdmissionProvenanceError, match="inconsistent_admission_binding"):
            load_admitted_normalization_candidate(std_path, moved_path)
        assert _run_fresh_load_rejection(std_path, moved_path)["reason"] == (
            "inconsistent_admission_binding"
        )

        false_transform = copy.deepcopy(valid)
        false_transform["transformation"] = "analytical_amount = reported_face_expense"
        transform_path = _write_mutated_bundle(root, false_transform, "false_transform.json")
        with pytest.raises(AdmissionProvenanceError, match="inconsistent_admission_binding"):
            load_admitted_normalization_candidate(std_path, transform_path)
        assert _run_fresh_load_rejection(std_path, transform_path)["reason"] == (
            "inconsistent_admission_binding"
        )

        missing_period = copy.deepcopy(valid)
        missing_period["observations"][0].pop("period", None)
        assert missing_period["observations"][0]["fingerprint_inputs"]["period"]
        missing_path = _write_mutated_bundle(root, missing_period, "missing_period.json")
        with pytest.raises(AdmissionProvenanceError, match="missing_admission_evidence"):
            load_admitted_normalization_candidate(std_path, missing_path)
        assert _run_fresh_load_rejection(std_path, missing_path)["reason"] == (
            "missing_admission_evidence"
        )

        recovered = _run_fresh_load(std_path, adm_path)
        assert recovered["transformation"] == SIGN_TRANSFORMATION
        assert any(item["period"] == source_period for item in recovered["observations"])
        assert any(item["period"] == reassigned_period for item in recovered["observations"])
    assert _snapshot_obs(retained["observations"]) == original_obs
    assert retained["live_std_bytes"] == (LIVE_DIR / "standardized.json").read_bytes()

