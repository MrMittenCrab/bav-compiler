"""Isolated B/current comparison driver for normalization-candidate admission.

Test helper only. B production modules are imported unchanged when ERA=b.
"""

from __future__ import annotations

import copy
import json
import sys
from datetime import date

ERA = sys.argv[1]
if ERA == "b":
    from core.data.line_identity import line_identity
    from core.data.standardized_io import standardized_from_payload, standardized_to_payload
    from core.ingestion.normalization_candidate_admission import (
        ANALYTICAL_CONCEPT,
        ANALYTICAL_LABEL,
        ANALYTICAL_SELECTOR,
        AUTHORIZED_IS_IDENTITIES,
        AUTHORIZATION_SYNTHETIC,
        CF_AUDIT_IDENTITIES,
        LEDGER_PERIODS,
        AdoptionRecord,
        TreatmentRecord,
        construct_provisional_candidate,
        run_normalization_candidate_handoff,
    )
    from core.model.normalization import (
        SUPPORTED_NORMALIZATION_SCOPE,
        compute_normalization_series,
        normalization_cases,
        resolve_income_statement_selector,
    )
    from modeler.financial_math import AnchorMetrics, HistoricalSeries
    from modeler.period_axis import canonical_fiscal_periods
    from modeler.ratio_values import UNDEFINED_RATIO
else:
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
        AdoptionRecord,
        TreatmentRecord,
        construct_provisional_candidate,
        run_normalization_candidate_handoff,
    )
    from core.model.normalization import (
        SUPPORTED_NORMALIZATION_SCOPE,
        compute_normalization_series,
        normalization_cases,
        resolve_income_statement_selector,
    )
    from modeler.financial_math import AnchorMetrics, HistoricalSeries
    from modeler.period_axis import canonical_fiscal_periods
    from modeler.ratio_values import UNDEFINED_RATIO


def _page_lookup(rows):
    return {
        (str(source), int(page)): {
            "printed_page": printed,
            "printed_status": "resolved",
        }
        for source, page, printed in rows
    }


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


def _summarize_handoff(result) -> dict:
    periods = [
        {
            "period": row.period,
            "n_is_observations": row.n_is_observations,
            "row_identities": list(row.row_identities),
            "source_hashes": list(row.source_hashes),
            "physical_pages": list(row.physical_pages),
            "printed_pages": list(row.printed_pages),
            "transformation": row.transformation,
            "sign_conversions_applied": row.sign_conversions_applied,
            "observation_fingerprints": list(row.observation_fingerprints),
        }
        for row in result.periods
    ]
    return {
        "constructed": result.constructed,
        "production_admitted": result.production_admitted,
        "real_company_acceptance": result.real_company_acceptance,
        "mapping_status": result.mapping_status,
        "blocked_reason": result.blocked_reason,
        "gate": result.gate,
        "face_series": list(result.face_series),
        "analytical_series": list(result.analytical_series),
        "candidate_configuration": result.candidate_configuration,
        "after_tax_available": result.after_tax_available,
        "authorization_kind": result.authorization_kind,
        "tax_disposition": result.tax_disposition,
        "note_tax_effects_attributed": result.note_tax_effects_attributed,
        "periods": periods,
        "has_constructed_financials": result.constructed_financials is not None,
    }


def _mutate(observations, bound, kwargs):
    observations = copy.deepcopy(observations)
    member_identities = AUTHORIZED_IS_IDENTITIES
    sign_conversion = kwargs.get("sign_conversion", "once")
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
                "source_sha256_declared": bound["LULU_FY2022_Annual_Report.pdf"],
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
                "source_sha256_declared": bound["LULU_FY2023_Annual_Report.pdf"],
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
                "source_sha256_declared": bound["LULU_FY2022_Annual_Report.pdf"],
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
    return observations, member_identities, sign_conversion


def main() -> None:
    book = json.loads(sys.stdin.read())
    observations = book["observations"]
    bound = book["bound_source_hashes"]
    lookup = _page_lookup(book["page_lookup"])
    live = standardized_from_payload(copy.deepcopy(book["live_payload"]), strict=True)
    results: dict[str, object] = {}

    construction = construct_provisional_candidate(
        observations, bound_source_hashes=bound, page_lookup=lookup
    )
    results["construction"] = {
        "constructed": construction.constructed,
        "face_series": list(construction.face_series),
        "analytical_series": list(construction.analytical_series),
        "mapping_status": construction.mapping_status,
        "grouping_is_accepted_source_fact": construction.grouping_is_accepted_source_fact,
        "production_activation_authorized": construction.production_activation_authorized,
        "used_fingerprints": list(construction.used_fingerprints),
        "periods": [
            {
                "period": row.period,
                "n_is_observations": row.n_is_observations,
                "row_identities": list(row.row_identities),
                "source_hashes": list(row.source_hashes),
                "physical_pages": list(row.physical_pages),
                "printed_pages": list(row.printed_pages),
                "transformation": row.transformation,
                "sign_conversions_applied": row.sign_conversions_applied,
                "observation_fingerprints": list(row.observation_fingerprints),
            }
            for row in construction.periods
        ],
    }

    absent = run_normalization_candidate_handoff(
        observations, copy.deepcopy(live), bound_source_hashes=bound, page_lookup=lookup
    )
    results["absent_adoption"] = _summarize_handoff(absent)

    probes = {
        "missing_period_evidence": {"drop_period": "2022-01-30"},
        "altered_or_unbound_source_hash": {"alter_binding": True},
        "conflicting_overlapping_observations": {"conflict_value": 999999},
        "unauthorized_identity_membership": {"unauthorized": True},
        "cash_flow_substitution_forbidden": {"cf_members": True},
        "studio_cogs_excluded": {"studio": True},
        "aggregate_and_component_double_count": {"component": True},
        "absent_sign_conversion": {"sign_conversion": "absent"},
        "repeated_sign_conversion": {"sign_conversion": "repeated"},
        "observation_used_more_than_once": {"duplicate": True},
    }
    probe_out = {}
    for name, kwargs in probes.items():
        mutated, members, sign_conversion = _mutate(observations, bound, kwargs)
        financials = copy.deepcopy(live)
        original = standardized_to_payload(financials)
        blocked = run_normalization_candidate_handoff(
            mutated,
            financials,
            bound_source_hashes=bound,
            page_lookup=lookup,
            member_identities=members,
            sign_conversion=sign_conversion,
        )
        probe_out[name] = {
            **_summarize_handoff(blocked),
            "inputs_unchanged": standardized_to_payload(financials) == original,
        }
    results["rejection_probes"] = probe_out

    isolated = copy.deepcopy(live)
    isolated.income_statement = list(isolated.income_statement)
    isolated.income_statement.append(construction.line)
    isolated.income_statement.append(
        type(construction.line)(
            label=ANALYTICAL_LABEL + " duplicate",
            concept=ANALYTICAL_CONCEPT,
            values=dict(construction.line.values),
        )
    )
    try:
        resolve_income_statement_selector(isolated, ANALYTICAL_SELECTOR)
        results["ambiguous_selector"] = "accepted"
    except ValueError as exc:
        results["ambiguous_selector"] = str(exc)

    base = _synthetic_adoption(construction)
    adoption_cases = {
        "provisional_adoption": base.__class__(**{**base.__dict__, "decision_status": "provisional"}),
        "boolean_approved": base.__class__(**{**base.__dict__, "approved": True}),
        "matching_concept": base.__class__(**{**base.__dict__, "equivalent_by_concept": True}),
        "agreeing_amounts": base.__class__(**{**base.__dict__, "equivalent_by_agreeing_amounts": True}),
        "rationale_matching_concept": base.__class__(
            **{**base.__dict__, "rationale": "matching concept across three labels"}
        ),
    }
    adoption_out = {}
    for name, record in adoption_cases.items():
        adoption_out[name] = _summarize_handoff(
            run_normalization_candidate_handoff(
                observations,
                copy.deepcopy(live),
                bound_source_hashes=bound,
                page_lookup=lookup,
                adoption=record,
            )
        )
    results["adoption_gates"] = adoption_out

    mismatched = [
        ("company", base.__class__(**{**base.__dict__, "company": "NOT_LULU"})),
        ("axis", base.__class__(**{**base.__dict__, "axis": LEDGER_PERIODS[1:]})),
        (
            "members",
            base.__class__(**{**base.__dict__, "member_identities": AUTHORIZED_IS_IDENTITIES[:2]}),
        ),
        (
            "concept",
            base.__class__(**{**base.__dict__, "analytical_concept": "impairment_and_restructuring"}),
        ),
    ]
    mismatch_out = {}
    for name, record in mismatched:
        mismatch_out[name] = _summarize_handoff(
            run_normalization_candidate_handoff(
                observations,
                copy.deepcopy(live),
                bound_source_hashes=bound,
                page_lookup=lookup,
                adoption=record,
                treatment=_synthetic_treatment(),
            )
        )
    stale = base.__class__(**{**base.__dict__, "source_evidence_fingerprints": ("0" * 64,)})
    mismatch_out["stale"] = _summarize_handoff(
        run_normalization_candidate_handoff(
            observations,
            copy.deepcopy(live),
            bound_source_hashes=bound,
            page_lookup=lookup,
            adoption=stale,
            treatment=_synthetic_treatment(),
        )
    )
    results["mismatched_stale"] = mismatch_out

    treatment_out = {
        "absent": _summarize_handoff(
            run_normalization_candidate_handoff(
                observations,
                copy.deepcopy(live),
                bound_source_hashes=bound,
                page_lookup=lookup,
                adoption=base,
            )
        ),
        "missing_rationale": _summarize_handoff(
            run_normalization_candidate_handoff(
                observations,
                copy.deepcopy(live),
                bound_source_hashes=bound,
                page_lookup=lookup,
                adoption=base,
                treatment=_synthetic_treatment(rationale=""),
            )
        ),
        "missing_consequence": _summarize_handoff(
            run_normalization_candidate_handoff(
                observations,
                copy.deepcopy(live),
                bound_source_hashes=bound,
                page_lookup=lookup,
                adoption=base,
                treatment=_synthetic_treatment(consequence_note=""),
            )
        ),
        "conflicting_scope": _summarize_handoff(
            run_normalization_candidate_handoff(
                observations,
                copy.deepcopy(live),
                bound_source_hashes=bound,
                page_lookup=lookup,
                adoption=base,
                treatment=_synthetic_treatment(scope="note_item_specific_tax"),
            )
        ),
        "unresolved_scope": _summarize_handoff(
            run_normalization_candidate_handoff(
                observations,
                copy.deepcopy(live),
                bound_source_hashes=bound,
                page_lookup=lookup,
                adoption=base,
                treatment=_synthetic_treatment(aggregate_or_component="component"),
            )
        ),
        "unresolved_treatment": _summarize_handoff(
            run_normalization_candidate_handoff(
                observations,
                copy.deepcopy(live),
                bound_source_hashes=bound,
                page_lookup=lookup,
                adoption=base,
                treatment=_synthetic_treatment(reference_treatment="Maybe"),
            )
        ),
    }
    results["treatment_gates"] = treatment_out

    admitted = run_normalization_candidate_handoff(
        observations,
        copy.deepcopy(live),
        bound_source_hashes=bound,
        page_lookup=lookup,
        adoption=base,
        treatment=_synthetic_treatment(),
    )
    export_reload = None
    pretax = None
    if admitted.constructed_financials is not None and admitted.candidate_configuration is not None:
        exported = standardized_to_payload(admitted.constructed_financials)
        reloaded = standardized_from_payload(exported, strict=True)
        item = resolve_income_statement_selector(reloaded, ANALYTICAL_SELECTOR)
        ident = line_identity(item)
        dates = [date.fromisoformat(period) for period in LEDGER_PERIODS]
        export_reload = {
            "label": item.label,
            "concept": item.concept,
            "values": [int(item.values[period]) for period in dates],
            "identity": ident.key(),
        }
        periods = canonical_fiscal_periods(reloaded)
        cases_nr = normalization_cases(
            reloaded, periods, {"normalizationCandidates": [admitted.candidate_configuration]}
        )
        rec_cfg = dict(admitted.candidate_configuration)
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
        pretax = {
            "nonrecurring": [int(value) for value in series_nr.pretax_adjustment],
            "recurring": [int(value) for value in series_rec.pretax_adjustment],
            "after_tax": [value for value in series_nr.after_tax_adjustment],
        }
        ordinary_hits = []
        for selector in book["ordinary_selectors"]:
            try:
                resolve_income_statement_selector(reloaded, selector)
                ordinary_hits.append(selector)
            except ValueError:
                pass
        export_reload["ordinary_hits"] = ordinary_hits
    results["synthetic_admission"] = {
        **_summarize_handoff(admitted),
        "export_reload": export_reload,
        "pretax": pretax,
    }

    repeated = run_normalization_candidate_handoff(
        observations,
        admitted.constructed_financials,
        bound_source_hashes=bound,
        page_lookup=lookup,
        adoption=base,
        treatment=_synthetic_treatment(),
    )
    results["repeated_admission"] = _summarize_handoff(repeated)

    ordinary_out = {}
    for name, payload in (("live", book["live_payload"]), ("ordinary", book["ordinary_payload"])):
        std = standardized_from_payload(copy.deepcopy(payload), strict=True)
        missing = []
        for selector in list(book["ordinary_selectors"]) + [ANALYTICAL_SELECTOR]:
            try:
                resolve_income_statement_selector(std, selector)
                missing.append(selector)
            except ValueError:
                pass
        ordinary_out[name] = {
            "unexpected_hits": missing,
            "empty_candidates": normalization_cases(
                std, canonical_fiscal_periods(std), {"normalizationCandidates": []}
            )
            == (),
            "has_analytical": any(item.concept == ANALYTICAL_CONCEPT for item in std.income_statement),
        }
    results["ordinary_outputs"] = ordinary_out
    json.dump(results, sys.stdout, sort_keys=True, default=str)


if __name__ == "__main__":
    main()
