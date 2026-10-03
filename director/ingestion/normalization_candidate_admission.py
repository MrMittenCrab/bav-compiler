"""Explicit normalization-candidate handoff sequencing and save/load coordination.

Delegates provisional construction, mechanical validation and persistence to
Modeler. Supplied grouping and treatment decisions remain supplied judgments.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from director.data.normalization_candidate import (
    AUTHORIZATION_INDEPENDENT,
    AUTHORIZATION_SYNTHETIC,
    AdoptionRecord,
    TreatmentRecord,
)
from interpreter.normalization import grouping_established_as_source_fact
from modeler.data.interface import LineItem, StandardizedFinancials
from modeler.ingestion.normalization_candidate_admission import (
    AUTHORIZED_IS_IDENTITIES,
    LEDGER_PERIODS,
    PeriodConstruction,
    _already_contains_analytical_line,
    _candidate_configuration,
    _insert_constructed_line,
    construct_provisional_candidate,
    evaluate_adoption,
    evaluate_treatment,
    persist_admitted_normalization_candidate,
)
from modeler.ingestion.normalization_candidate_admission_io import (
    AdmittedNormalizationBundle,
    AdmissionProvenanceError,
    ObservationEvidence,
    load_admitted_bundle,
)


@dataclass(frozen=True)
class HandoffResult:
    constructed: bool
    production_admitted: bool
    real_company_acceptance: bool
    mapping_status: str
    grouping_is_accepted_source_fact: bool
    blocked_reason: str | None
    gate: str | None
    face_series: tuple[int, ...]
    analytical_series: tuple[int, ...]
    periods: tuple[PeriodConstruction, ...]
    constructed_line: LineItem | None
    constructed_financials: StandardizedFinancials | None
    candidate_configuration: dict[str, str] | None
    after_tax_available: bool
    authorization_kind: str | None
    tax_disposition: str | None
    note_tax_effects_attributed: bool
    observation_evidence: tuple[ObservationEvidence, ...] = ()
    adoption: AdoptionRecord | None = None
    treatment: TreatmentRecord | None = None


def run_normalization_candidate_handoff(
    observations: Sequence[Mapping[str, Any]],
    financials: StandardizedFinancials,
    *,
    bound_source_hashes: Mapping[str, str],
    page_lookup: Mapping[tuple[str, int], Mapping[str, Any]] | None = None,
    member_identities: Sequence[str] = AUTHORIZED_IS_IDENTITIES,
    axis: Sequence[str] = LEDGER_PERIODS,
    sign_conversion: str = "once",
    allow_cf_members: bool = False,
    adoption: AdoptionRecord | None = None,
    treatment: TreatmentRecord | None = None,
) -> HandoffResult:
    """Explicit gated handoff. Mutates neither observations nor ``financials``."""
    original_n = len(financials.income_statement)
    construction = construct_provisional_candidate(
        observations,
        member_identities=member_identities,
        axis=axis,
        bound_source_hashes=bound_source_hashes,
        page_lookup=page_lookup,
        sign_conversion=sign_conversion,
        allow_cf_members=allow_cf_members,
    )
    if not construction.constructed or construction.line is None:
        assert len(financials.income_statement) == original_n
        return HandoffResult(
            constructed=False,
            production_admitted=False,
            real_company_acceptance=False,
            mapping_status="blocked",
            grouping_is_accepted_source_fact=grouping_established_as_source_fact(),
            blocked_reason=construction.reason,
            gate=construction.gate,
            face_series=(),
            analytical_series=(),
            periods=(),
            constructed_line=None,
            constructed_financials=None,
            candidate_configuration=None,
            after_tax_available=False,
            authorization_kind=None,
            tax_disposition=None,
            note_tax_effects_attributed=False,
        )

    if _already_contains_analytical_line(financials):
        assert len(financials.income_statement) == original_n
        return HandoffResult(
            constructed=True,
            production_admitted=False,
            real_company_acceptance=False,
            mapping_status="blocked",
            grouping_is_accepted_source_fact=grouping_established_as_source_fact(),
            blocked_reason="repeated_admission",
            gate="production",
            face_series=construction.face_series,
            analytical_series=construction.analytical_series,
            periods=construction.periods,
            constructed_line=construction.line,
            constructed_financials=None,
            candidate_configuration=None,
            after_tax_available=False,
            authorization_kind=None,
            tax_disposition=None,
            note_tax_effects_attributed=False,
        )

    isolated = _insert_constructed_line(financials, construction.line)
    assert len(financials.income_statement) == original_n

    adoption_block, adoption_gate = evaluate_adoption(adoption, construction, financials)
    if adoption_block is not None:
        return HandoffResult(
            constructed=True,
            production_admitted=False,
            real_company_acceptance=False,
            mapping_status=construction.mapping_status,
            grouping_is_accepted_source_fact=grouping_established_as_source_fact(
                getattr(adoption, "authorization_kind", None)
            ),
            blocked_reason=adoption_block,
            gate=adoption_gate,
            face_series=construction.face_series,
            analytical_series=construction.analytical_series,
            periods=construction.periods,
            constructed_line=construction.line,
            constructed_financials=isolated,
            candidate_configuration=None,
            after_tax_available=False,
            authorization_kind=getattr(adoption, "authorization_kind", None),
            tax_disposition=None,
            note_tax_effects_attributed=False,
        )

    assert adoption is not None
    treatment_block, treatment_gate, after_tax_available = evaluate_treatment(
        treatment, adoption
    )
    if treatment_block is not None:
        return HandoffResult(
            constructed=True,
            production_admitted=False,
            real_company_acceptance=False,
            mapping_status=construction.mapping_status,
            grouping_is_accepted_source_fact=grouping_established_as_source_fact(
                adoption.authorization_kind
            ),
            blocked_reason=treatment_block,
            gate=treatment_gate,
            face_series=construction.face_series,
            analytical_series=construction.analytical_series,
            periods=construction.periods,
            constructed_line=construction.line,
            constructed_financials=isolated,
            candidate_configuration=None,
            after_tax_available=False,
            authorization_kind=adoption.authorization_kind,
            tax_disposition=getattr(treatment, "etr_disposition", None),
            note_tax_effects_attributed=False,
        )

    assert treatment is not None
    real_acceptance = adoption.authorization_kind == AUTHORIZATION_INDEPENDENT
    mapping_status = (
        "synthetic_test_authorization"
        if adoption.authorization_kind == AUTHORIZATION_SYNTHETIC
        else "independently_supplied_decision"
    )
    return HandoffResult(
        constructed=True,
        production_admitted=True,
        real_company_acceptance=real_acceptance,
        mapping_status=mapping_status,
        grouping_is_accepted_source_fact=grouping_established_as_source_fact(
            adoption.authorization_kind
        ),
        blocked_reason=None,
        gate="production_admitted",
        face_series=construction.face_series,
        analytical_series=construction.analytical_series,
        periods=construction.periods,
        constructed_line=construction.line,
        constructed_financials=isolated,
        candidate_configuration=_candidate_configuration(treatment),
        after_tax_available=after_tax_available,
        authorization_kind=adoption.authorization_kind,
        tax_disposition=treatment.etr_disposition,
        note_tax_effects_attributed=False,
        observation_evidence=construction.observation_evidence,
        adoption=adoption,
        treatment=treatment,
    )


def save_admitted_normalization_candidate(
    result: HandoffResult,
    *,
    standardized_path: str | Path,
    admission_path: str | Path,
) -> None:
    """Persist admitted financials plus dedicated admission provenance."""
    if (
        not result.production_admitted
        or result.constructed_financials is None
        or result.constructed_line is None
        or result.candidate_configuration is None
        or result.adoption is None
        or result.treatment is None
        or not result.observation_evidence
        or result.mapping_status == "provisional_equivalence_unresolved"
        or result.grouping_is_accepted_source_fact
    ):
        raise AdmissionProvenanceError("blocked_or_provisional_handoff")
    persist_admitted_normalization_candidate(
        result.constructed_financials,
        result.constructed_line,
        observations=result.observation_evidence,
        periods=result.periods,
        adoption=result.adoption,
        treatment=result.treatment,
        candidate_configuration=result.candidate_configuration,
        mapping_status=result.mapping_status,
        grouping_is_accepted_source_fact=result.grouping_is_accepted_source_fact,
        authorization_kind=result.authorization_kind or result.adoption.authorization_kind,
        after_tax_available=result.after_tax_available,
        tax_disposition=result.tax_disposition,
        note_tax_effects_attributed=result.note_tax_effects_attributed,
        real_company_acceptance=result.real_company_acceptance,
        standardized_path=standardized_path,
        admission_path=admission_path,
    )


def load_admitted_normalization_candidate(
    standardized_path: str | Path,
    admission_path: str | Path,
) -> AdmittedNormalizationBundle:
    """Recover an admitted bundle from persisted paths only. No sign reconversion."""
    return load_admitted_bundle(standardized_path, admission_path)
