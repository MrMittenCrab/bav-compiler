"""Compatibility façade. Implementation is split across Modeler, Director and Interpreter."""

from director.data.normalization_candidate import (
    AUTHORIZATION_INDEPENDENT,
    AUTHORIZATION_SYNTHETIC,
    AdoptionRecord,
    TreatmentRecord,
)
from director.ingestion.normalization_candidate_admission import (
    HandoffResult,
    load_admitted_normalization_candidate,
    run_normalization_candidate_handoff,
    save_admitted_normalization_candidate,
)
from modeler.data.interface import LineItem, StandardizedFinancials
from modeler.ingestion.normalization_candidate_admission import (
    ANALYTICAL_CONCEPT,
    ANALYTICAL_LABEL,
    ANALYTICAL_SELECTOR,
    AUTHORIZED_IS_IDENTITIES,
    CF_AUDIT_IDENTITIES,
    GEO_AUDIT_IDENTITY,
    LEDGER_PERIODS,
    SIGN_TRANSFORMATION,
    ConstructionResult,
    GateFailure,
    PeriodConstruction,
    construct_provisional_candidate,
    evaluate_adoption,
    evaluate_treatment,
    observation_fingerprint,
    printed_page_lookup_from_evidence,
    _adoption_payload,
    _already_contains_analytical_line,
    _attach_pages,
    _blank,
    _candidate_configuration,
    _cites_technical_equivalence,
    _face_amount,
    _failure,
    _insert_constructed_line,
    _is_studio,
    _locator_state,
    _membership_set_rejection,
    _observation_evidence,
    _treatment_payload,
)
from modeler.ingestion.normalization_candidate_admission_io import (
    AdmittedNormalizationBundle,
    AdmissionProvenanceError,
    ObservationEvidence,
    build_admission_provenance_payload,
    load_admitted_bundle,
    observation_evidence_from_inputs,
    save_admitted_bundle,
)
