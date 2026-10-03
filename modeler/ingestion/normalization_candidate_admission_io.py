"""Modeler-owned persistence for admitted normalization-candidate provenance.

Dedicated admission artifact alongside model-only standardized financials.
Does not extend standardized_io or ordinary documentary reconciliation provenance.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Mapping, Sequence

from modeler.data.interface import LineItem, StandardizedFinancials
from modeler.data.line_identity import line_identity
from modeler.data.standardized_io import standardized_from_payload, standardized_to_payload

ARTIFACT_KIND = "normalization_candidate_admission"
ARTIFACT_SCHEMA = "normalization_candidate_admission/v2"
PRIOR_ARTIFACT_SCHEMAS = frozenset({"normalization_candidate_admission/v1"})
STATEMENT = "income_statement"
SIGN_CONVERSION_ONCE = 1
SIGN_TRANSFORMATION = "analytical_amount = -reported_face_expense"
AUTHORIZATION_SYNTHETIC = "synthetic"
AUTHORIZATION_INDEPENDENT = "independently_supplied"
SUPPORTED_NORMALIZATION_SCOPE = "operating_pretax_effective_tax"
NORMALIZATION_TREATMENTS = ("Recurring", "Non-recurring")
ANALYTICAL_CONCEPT = "analytical_is_impairment_restructuring_aggregate"
ANALYTICAL_LABEL = "Impairment and restructuring costs (provisional analytical aggregate)"
ANALYTICAL_SELECTOR = f"concept:{ANALYTICAL_CONCEPT}"
_TECHNICAL_EQUIVALENCE_MARKERS = (
    "matching concept",
    "same suggested_concept",
    "agreeing amounts",
    "agreeing overlapping",
    "boolean approval",
)


class AdmissionProvenanceError(ValueError):
    """Rejected admission-bundle persistence or reload."""

    def __init__(self, reason: str, **detail: Any) -> None:
        super().__init__(reason)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class ObservationEvidence:
    """One admitted observation, captured before period aggregation."""

    fingerprint: str
    source_file: str
    source_hash: str
    row_identity: str
    physical_page: int | None
    printed_page: Any
    printed_page_status: str
    period: str
    reported_amount: int
    currency: str
    unit_scale: str
    fingerprint_inputs: dict[str, Any]


@dataclass(frozen=True)
class AdmittedNormalizationBundle:
    """Recovered admitted financials plus validated admission provenance."""

    financials: StandardizedFinancials
    analytical_line: LineItem
    analytical_identity: str
    statement: str
    company: str
    fiscal_periods: tuple[str, ...]
    analytical_values: tuple[int, ...]
    face_values: tuple[int, ...]
    transformation: str
    sign_conversions_applied: int
    observations: tuple[ObservationEvidence, ...]
    adoption: dict[str, Any]
    treatment: dict[str, Any]
    candidate_configuration: dict[str, str]
    mapping_status: str
    grouping_is_accepted_source_fact: bool
    authorization_kind: str
    after_tax_available: bool
    tax_disposition: str | None
    note_tax_effects_attributed: bool
    real_company_acceptance: bool


def observation_fingerprint(obs: Mapping[str, Any]) -> str:
    """Hash the full original observation. Do not substitute a projected subset."""
    payload = json.dumps(dict(obs), sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def observation_evidence_payload(item: ObservationEvidence) -> dict[str, Any]:
    return {
        "fingerprint": item.fingerprint,
        "source_file": item.source_file,
        "source_hash": item.source_hash,
        "row_identity": item.row_identity,
        "physical_page": item.physical_page,
        "printed_page": item.printed_page,
        "printed_page_status": item.printed_page_status,
        "period": item.period,
        "reported_amount": int(item.reported_amount),
        "currency": item.currency,
        "unit_scale": item.unit_scale,
        "fingerprint_inputs": dict(item.fingerprint_inputs),
    }


def _locator_state(obs: Mapping[str, Any]) -> tuple[int | None, Any, str]:
    raw_physical = obs.get("physical_page", obs.get("pdf_page"))
    if raw_physical is None or raw_physical == "":
        physical = None
    else:
        physical = int(raw_physical)
        if physical == 0:
            physical = None
    printed = obs.get("printed_page")
    status = obs.get("printed_page_status")
    if isinstance(status, str) and status.strip():
        printed_status = status.strip()
    elif printed is not None:
        printed_status = "resolved"
    elif physical is None:
        printed_status = "unavailable"
    else:
        printed_status = "unresolved"
    return physical, printed, printed_status


def _face_amount(value: object) -> int:
    return int(value)


def observation_evidence_from_inputs(
    obs: Mapping[str, Any],
    *,
    period: str,
    fingerprint: str,
) -> ObservationEvidence:
    """Project stored evidence from original fingerprint inputs. Never invent locators."""
    if not isinstance(obs, Mapping) or not obs:
        raise AdmissionProvenanceError("missing_admission_evidence")
    physical, printed, printed_status = _locator_state(obs)
    try:
        reported_amount = _face_amount(obs["value"])
    except (KeyError, TypeError, ValueError) as exc:
        raise AdmissionProvenanceError("missing_admission_evidence") from exc
    return ObservationEvidence(
        fingerprint=fingerprint,
        source_file=str(obs.get("source_file") or ""),
        source_hash=str(obs.get("source_sha256_declared") or ""),
        row_identity=str(obs.get("row_identity") or ""),
        physical_page=physical,
        printed_page=printed,
        printed_page_status=printed_status,
        period=period,
        reported_amount=reported_amount,
        currency=str(obs.get("currency") or ""),
        unit_scale=str(obs.get("unit_scale") or ""),
        fingerprint_inputs=dict(obs),
    )


def observation_evidence_from_payload(payload: Mapping[str, Any]) -> ObservationEvidence:
    if not isinstance(payload, Mapping):
        raise AdmissionProvenanceError("missing_admission_evidence")
    inputs = payload.get("fingerprint_inputs")
    if not isinstance(inputs, Mapping) or not inputs:
        raise AdmissionProvenanceError("stale_admission_evidence")
    stored_fingerprint = str(payload.get("fingerprint") or "")
    recomputed = observation_fingerprint(inputs)
    if not stored_fingerprint or recomputed != stored_fingerprint:
        raise AdmissionProvenanceError(
            "stale_admission_evidence",
            fingerprint=stored_fingerprint,
            recomputed=recomputed,
        )
    input_period = inputs.get("period")
    stored_period = payload.get("period")
    if _blank(input_period) or stored_period is None or _blank(stored_period):
        raise AdmissionProvenanceError("missing_admission_evidence")
    input_period = str(input_period)
    stored_period = str(stored_period)
    if stored_period != input_period:
        raise AdmissionProvenanceError(
            "inconsistent_admission_binding",
            stored_period=stored_period,
            fingerprint_period=input_period,
        )
    projected = observation_evidence_from_inputs(
        inputs, period=input_period, fingerprint=stored_fingerprint
    )
    physical = payload.get("physical_page")
    if physical is not None:
        physical = int(physical)
    stored = ObservationEvidence(
        fingerprint=stored_fingerprint,
        source_file=str(payload.get("source_file") or ""),
        source_hash=str(payload.get("source_hash") or ""),
        row_identity=str(payload.get("row_identity") or ""),
        physical_page=physical,
        printed_page=payload.get("printed_page"),
        printed_page_status=str(payload.get("printed_page_status") or ""),
        period=stored_period,
        reported_amount=int(payload.get("reported_amount")),
        currency=str(payload.get("currency") or ""),
        unit_scale=str(payload.get("unit_scale") or ""),
        fingerprint_inputs=dict(inputs),
    )
    if (
        stored.source_file != projected.source_file
        or stored.source_hash != projected.source_hash
        or stored.row_identity != projected.row_identity
        or stored.physical_page != projected.physical_page
        or stored.printed_page != projected.printed_page
        or stored.printed_page_status != projected.printed_page_status
        or stored.period != projected.period
        or stored.reported_amount != projected.reported_amount
        or stored.currency != projected.currency
        or stored.unit_scale != projected.unit_scale
    ):
        raise AdmissionProvenanceError(
            "inconsistent_admission_binding",
            fingerprint=stored_fingerprint,
        )
    return stored


def build_admission_provenance_payload(
    financials: StandardizedFinancials,
    line: LineItem,
    *,
    observations: Sequence[ObservationEvidence],
    face_by_period: Mapping[str, int],
    analytical_by_period: Mapping[str, int],
    fiscal_periods: Sequence[str],
    transformation: str,
    sign_conversions_applied: int,
    adoption: Mapping[str, Any],
    treatment: Mapping[str, Any],
    candidate_configuration: Mapping[str, str],
    mapping_status: str,
    grouping_is_accepted_source_fact: bool,
    authorization_kind: str,
    after_tax_available: bool,
    tax_disposition: str | None,
    note_tax_effects_attributed: bool,
    real_company_acceptance: bool,
) -> dict[str, Any]:
    identity = line_identity(line).key()
    company = str(adoption.get("company") or financials.ticker or "")
    return {
        "kind": ARTIFACT_KIND,
        "schema": ARTIFACT_SCHEMA,
        "company": company,
        "ticker": financials.ticker,
        "company_name": financials.company_name,
        "statement": STATEMENT,
        "analytical_line": {
            "concept": line.concept,
            "label": line.label,
            "identity": identity,
        },
        "fiscal_periods": list(fiscal_periods),
        "analytical_values": {period: int(analytical_by_period[period]) for period in fiscal_periods},
        "face_values": {period: int(face_by_period[period]) for period in fiscal_periods},
        "transformation": transformation,
        "sign_conversions_applied": int(sign_conversions_applied),
        "observations": [observation_evidence_payload(item) for item in observations],
        "adoption": dict(adoption),
        "treatment": dict(treatment),
        "candidate_configuration": dict(candidate_configuration),
        "mapping_status": mapping_status,
        "grouping_is_accepted_source_fact": bool(grouping_is_accepted_source_fact),
        "authorization_kind": authorization_kind,
        "after_tax_available": bool(after_tax_available),
        "tax_disposition": tax_disposition,
        "note_tax_effects_attributed": bool(note_tax_effects_attributed),
        "real_company_acceptance": bool(real_company_acceptance),
        "production_admitted": True,
    }


def save_admitted_bundle(
    financials: StandardizedFinancials,
    payload: Mapping[str, Any],
    *,
    standardized_path: str | Path,
    admission_path: str | Path,
) -> None:
    Path(standardized_path).write_text(
        json.dumps(standardized_to_payload(financials), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    Path(admission_path).write_text(
        json.dumps(dict(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _require_mapping(payload: object, reason: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise AdmissionProvenanceError(reason)
    return payload


def _require_text(payload: Mapping[str, Any], key: str, reason: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise AdmissionProvenanceError(reason)
    return value


def _line_amount(line: LineItem, period: str) -> int:
    try:
        amount = line.values[date.fromisoformat(period)]
    except KeyError as exc:
        raise AdmissionProvenanceError("mismatched_period_binding", period=period) from exc
    if amount is None:
        raise AdmissionProvenanceError("mismatched_value_binding", period=period)
    return int(amount)


def _blank(value: object) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _cites_technical_equivalence(*parts: object) -> bool:
    blob = " ".join(str(part or "") for part in parts).casefold()
    return any(marker in blob for marker in _TECHNICAL_EQUIVALENCE_MARKERS)


def _as_text_tuple(value: object, reason: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise AdmissionProvenanceError(reason)
    items = tuple(str(item) for item in value)
    if any(_blank(item) for item in items):
        raise AdmissionProvenanceError(reason)
    return items


def _validate_recovered_adoption(
    adoption: Mapping[str, Any],
    *,
    company: str,
    concept: str,
    label: str,
    fiscal_periods: Sequence[str],
    fingerprints: Sequence[str],
    observations: Sequence[ObservationEvidence],
) -> None:
    required = (
        adoption.get("company"),
        adoption.get("mapping_decision"),
        adoption.get("decision_authority"),
        adoption.get("rationale"),
        adoption.get("decision_status"),
        adoption.get("authorization_kind"),
        adoption.get("analytical_scope"),
    )
    if any(_blank(item) for item in required):
        raise AdmissionProvenanceError("missing_admission_evidence")
    axis = _as_text_tuple(adoption.get("axis"), "mismatched_period_binding")
    members = _as_text_tuple(adoption.get("member_identities"), "mismatched_line_binding")
    if not adoption.get("source_evidence_fingerprints"):
        raise AdmissionProvenanceError("stale_admission_evidence")
    status = str(adoption.get("decision_status") or "")
    if status.casefold() == "provisional" or status.casefold() != "adopted":
        raise AdmissionProvenanceError("blocked_or_provisional_handoff")
    if adoption.get("approved") is not None:
        raise AdmissionProvenanceError("inconsistent_admission_binding")
    if adoption.get("equivalent_by_concept") or adoption.get("equivalent_by_agreeing_amounts"):
        raise AdmissionProvenanceError("inconsistent_admission_binding")
    if _cites_technical_equivalence(adoption.get("mapping_decision"), adoption.get("rationale")):
        raise AdmissionProvenanceError("inconsistent_admission_binding")
    if "provisional" in str(adoption.get("mapping_decision") or "").casefold():
        raise AdmissionProvenanceError("inconsistent_admission_binding")
    if str(adoption.get("company") or "") != company:
        raise AdmissionProvenanceError("mismatched_company_binding")
    if axis != tuple(fiscal_periods):
        raise AdmissionProvenanceError("mismatched_period_binding")
    observed_rows = {item.row_identity for item in observations}
    if not observed_rows or not observed_rows.issubset(set(members)):
        raise AdmissionProvenanceError("mismatched_line_binding")
    if str(adoption.get("analytical_concept") or "") != concept:
        raise AdmissionProvenanceError("mismatched_line_binding")
    if str(adoption.get("analytical_label") or "") != label:
        raise AdmissionProvenanceError("mismatched_line_binding")
    if concept != ANALYTICAL_CONCEPT or label != ANALYTICAL_LABEL:
        raise AdmissionProvenanceError("mismatched_line_binding")
    if str(adoption.get("analytical_scope") or "") != SUPPORTED_NORMALIZATION_SCOPE:
        raise AdmissionProvenanceError("inconsistent_admission_binding")
    if set(str(item) for item in adoption.get("source_evidence_fingerprints") or []) != set(
        fingerprints
    ):
        raise AdmissionProvenanceError("stale_admission_evidence")
    kind = str(adoption.get("authorization_kind") or "")
    if kind not in {AUTHORIZATION_SYNTHETIC, AUTHORIZATION_INDEPENDENT}:
        raise AdmissionProvenanceError("inconsistent_admission_binding")


def _validate_recovered_treatment(
    treatment: Mapping[str, Any],
    adoption: Mapping[str, Any],
    *,
    configuration: Mapping[str, Any],
    after_tax_available: bool,
    tax_disposition: object,
    concept: str,
) -> None:
    if not treatment:
        raise AdmissionProvenanceError("missing_admission_evidence")
    if _blank(treatment.get("rationale")):
        raise AdmissionProvenanceError("missing_admission_evidence")
    if _blank(treatment.get("consequence_note")):
        raise AdmissionProvenanceError("missing_admission_evidence")
    if _blank(treatment.get("scope")) or _blank(treatment.get("reference_treatment")):
        raise AdmissionProvenanceError("missing_admission_evidence")
    if _blank(treatment.get("aggregate_or_component")) or _blank(treatment.get("cogs_boundary")):
        raise AdmissionProvenanceError("missing_admission_evidence")
    if _blank(treatment.get("topic")):
        raise AdmissionProvenanceError("missing_admission_evidence")
    if str(treatment.get("scope") or "") != SUPPORTED_NORMALIZATION_SCOPE:
        raise AdmissionProvenanceError("inconsistent_admission_binding")
    if str(treatment.get("scope") or "") != str(adoption.get("analytical_scope") or ""):
        raise AdmissionProvenanceError("inconsistent_admission_binding")
    if str(treatment.get("reference_treatment") or "") not in NORMALIZATION_TREATMENTS:
        raise AdmissionProvenanceError("inconsistent_admission_binding")
    if str(treatment.get("aggregate_or_component") or "") != "aggregate":
        raise AdmissionProvenanceError("inconsistent_admission_binding")
    if str(treatment.get("cogs_boundary") or "") != "exclude_studio_cogs":
        raise AdmissionProvenanceError("inconsistent_admission_binding")
    expected_configuration = {
        "selector": ANALYTICAL_SELECTOR if concept == ANALYTICAL_CONCEPT else f"concept:{concept}",
        "referenceTreatment": str(treatment.get("reference_treatment") or ""),
        "scope": str(treatment.get("scope") or ""),
        "topic": str(treatment.get("topic") or ""),
        "referenceRationale": str(treatment.get("rationale") or ""),
        "consequenceNote": str(treatment.get("consequence_note") or ""),
    }
    recovered_configuration = {str(key): str(value) for key, value in configuration.items()}
    if recovered_configuration != expected_configuration:
        raise AdmissionProvenanceError("inconsistent_admission_binding")
    deductibility = treatment.get("deductibility")
    etr_disposition = treatment.get("etr_disposition")
    tax_resolved = (
        not _blank(deductibility)
        and not _blank(etr_disposition)
        and str(deductibility).casefold() != "unresolved"
        and str(etr_disposition).casefold() != "unresolved"
    )
    expected_after_tax = tax_resolved and etr_disposition == "operating_etr"
    if bool(after_tax_available) != expected_after_tax:
        raise AdmissionProvenanceError("inconsistent_admission_binding")
    if tax_disposition != etr_disposition:
        raise AdmissionProvenanceError("inconsistent_admission_binding")


def _validate_recovered_authorization(
    adoption: Mapping[str, Any],
    *,
    authorization_kind: str,
    mapping_status: str,
    real_company_acceptance: bool,
) -> None:
    adopted_kind = str(adoption.get("authorization_kind") or "")
    if adopted_kind != authorization_kind:
        raise AdmissionProvenanceError("inconsistent_admission_binding")
    if authorization_kind not in {AUTHORIZATION_SYNTHETIC, AUTHORIZATION_INDEPENDENT}:
        raise AdmissionProvenanceError("inconsistent_admission_binding")
    if authorization_kind == AUTHORIZATION_SYNTHETIC:
        if real_company_acceptance:
            raise AdmissionProvenanceError("inconsistent_admission_binding")
        if mapping_status != "synthetic_test_authorization":
            raise AdmissionProvenanceError("inconsistent_admission_binding")
        return
    if mapping_status != "independently_supplied_decision":
        raise AdmissionProvenanceError("inconsistent_admission_binding")


def _select_analytical_line(
    financials: StandardizedFinancials,
    concept: str,
    label: str,
    identity: str,
) -> LineItem:
    matches = [
        item
        for item in financials.income_statement
        if item.concept == concept
    ]
    if not matches:
        raise AdmissionProvenanceError("mismatched_line_binding", concept=concept)
    if len(matches) != 1:
        raise AdmissionProvenanceError(
            "ambiguous_admission_linkage",
            concept=concept,
            n_matches=len(matches),
        )
    line = matches[0]
    recovered = line_identity(line).key()
    if line.label != label or recovered != identity:
        raise AdmissionProvenanceError(
            "mismatched_line_binding",
            expected_identity=identity,
            recovered_identity=recovered,
        )
    return line


def load_admitted_bundle(
    standardized_path: str | Path,
    admission_path: str | Path,
) -> AdmittedNormalizationBundle:
    """Reload standardized financials plus admission evidence from persisted paths.

    Recovers stored analytical values as-is. Does not reapply sign conversion.
    """
    std_path = Path(standardized_path)
    adm_path = Path(admission_path)
    if not std_path.is_file() or not adm_path.is_file():
        raise AdmissionProvenanceError("missing_admission_evidence")
    try:
        standardized_payload = json.loads(std_path.read_text(encoding="utf-8"))
        artifact = json.loads(adm_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AdmissionProvenanceError("missing_admission_evidence") from exc
    artifact = _require_mapping(artifact, "missing_admission_evidence")
    if artifact.get("kind") != ARTIFACT_KIND:
        raise AdmissionProvenanceError("stale_admission_evidence")
    if artifact.get("schema") in PRIOR_ARTIFACT_SCHEMAS or artifact.get("schema") != ARTIFACT_SCHEMA:
        raise AdmissionProvenanceError("stale_admission_evidence")
    if artifact.get("production_admitted") is not True:
        raise AdmissionProvenanceError("blocked_or_provisional_handoff")
    financials = standardized_from_payload(
        _require_mapping(standardized_payload, "missing_admission_evidence"),
        strict=True,
    )
    company = _require_text(artifact, "company", "mismatched_company_binding")
    company_tokens = {
        str(financials.ticker or "").strip(),
        str(financials.company_name or "").strip(),
    }
    if company not in company_tokens:
        raise AdmissionProvenanceError("mismatched_company_binding", company=company)
    if artifact.get("statement") != STATEMENT:
        raise AdmissionProvenanceError("mismatched_line_binding")
    line_payload = _require_mapping(artifact.get("analytical_line"), "mismatched_line_binding")
    concept = _require_text(line_payload, "concept", "mismatched_line_binding")
    label = _require_text(line_payload, "label", "mismatched_line_binding")
    identity = _require_text(line_payload, "identity", "mismatched_line_binding")
    line = _select_analytical_line(financials, concept, label, identity)
    raw_periods = artifact.get("fiscal_periods")
    if not isinstance(raw_periods, list) or not raw_periods:
        raise AdmissionProvenanceError("mismatched_period_binding")
    fiscal_periods = tuple(str(period) for period in raw_periods)
    raw_analytical = _require_mapping(artifact.get("analytical_values"), "mismatched_value_binding")
    raw_face = _require_mapping(artifact.get("face_values"), "mismatched_value_binding")
    transformation = _require_text(artifact, "transformation", "missing_admission_evidence")
    if transformation != SIGN_TRANSFORMATION:
        raise AdmissionProvenanceError(
            "inconsistent_admission_binding",
            transformation=transformation,
        )
    sign_conversions = artifact.get("sign_conversions_applied")
    if sign_conversions != SIGN_CONVERSION_ONCE:
        raise AdmissionProvenanceError(
            "inconsistent_admission_binding",
            sign_conversions_applied=sign_conversions,
        )
    raw_observations = artifact.get("observations")
    if not isinstance(raw_observations, list) or not raw_observations:
        raise AdmissionProvenanceError("missing_admission_evidence")
    observations = tuple(observation_evidence_from_payload(item) for item in raw_observations)
    fingerprints = [item.fingerprint for item in observations]
    if any(not item for item in fingerprints) or len(set(fingerprints)) != len(fingerprints):
        raise AdmissionProvenanceError("ambiguous_admission_linkage")
    by_period: dict[str, list[ObservationEvidence]] = {period: [] for period in fiscal_periods}
    analytical_values: list[int] = []
    face_values: list[int] = []
    for period in fiscal_periods:
        if period not in raw_analytical or period not in raw_face:
            raise AdmissionProvenanceError("mismatched_period_binding", period=period)
        stored_analytical = int(raw_analytical[period])
        stored_face = int(raw_face[period])
        recovered = _line_amount(line, period)
        if recovered != stored_analytical:
            raise AdmissionProvenanceError(
                "mismatched_value_binding",
                period=period,
                stored=stored_analytical,
                recovered=recovered,
            )
        if stored_analytical != -stored_face:
            raise AdmissionProvenanceError(
                "inconsistent_admission_binding",
                period=period,
                face=stored_face,
                analytical=stored_analytical,
            )
        analytical_values.append(stored_analytical)
        face_values.append(stored_face)
    for item in observations:
        if item.period not in by_period:
            raise AdmissionProvenanceError("mismatched_period_binding", period=item.period)
        if item.printed_page_status not in {"resolved", "unresolved", "unavailable"}:
            raise AdmissionProvenanceError("missing_admission_evidence", fingerprint=item.fingerprint)
        if item.printed_page_status != "resolved" and item.printed_page is not None:
            raise AdmissionProvenanceError("inconsistent_admission_binding", fingerprint=item.fingerprint)
        if item.printed_page_status == "unavailable" and item.physical_page is not None:
            raise AdmissionProvenanceError("inconsistent_admission_binding", fingerprint=item.fingerprint)
        if not item.source_hash or not item.row_identity or not item.source_file:
            raise AdmissionProvenanceError("missing_admission_evidence", fingerprint=item.fingerprint)
        if item.period in raw_face and int(item.reported_amount) != int(raw_face[item.period]):
            raise AdmissionProvenanceError(
                "inconsistent_admission_binding",
                period=item.period,
                reported_amount=item.reported_amount,
            )
        by_period[item.period].append(item)
    for period, members in by_period.items():
        if not members:
            raise AdmissionProvenanceError("missing_admission_evidence", period=period)
    adoption = _require_mapping(artifact.get("adoption"), "missing_admission_evidence")
    treatment = _require_mapping(artifact.get("treatment"), "missing_admission_evidence")
    configuration = _require_mapping(
        artifact.get("candidate_configuration"), "missing_admission_evidence"
    )
    adoption_fps = adoption.get("source_evidence_fingerprints")
    if not isinstance(adoption_fps, list):
        raise AdmissionProvenanceError("stale_admission_evidence")
    if set(str(item) for item in adoption_fps) != set(fingerprints):
        raise AdmissionProvenanceError("stale_admission_evidence")
    if str(adoption.get("company") or "") != company:
        raise AdmissionProvenanceError("mismatched_company_binding")
    if str(adoption.get("analytical_concept") or "") != concept:
        raise AdmissionProvenanceError("mismatched_line_binding")
    mapping_status = _require_text(artifact, "mapping_status", "missing_admission_evidence")
    authorization_kind = _require_text(
        artifact, "authorization_kind", "missing_admission_evidence"
    )
    if artifact.get("grouping_is_accepted_source_fact") is True:
        raise AdmissionProvenanceError("blocked_or_provisional_handoff")
    after_tax_available = bool(artifact.get("after_tax_available"))
    tax_disposition = artifact.get("tax_disposition")
    real_company_acceptance = bool(artifact.get("real_company_acceptance"))
    _validate_recovered_adoption(
        adoption,
        company=company,
        concept=concept,
        label=label,
        fiscal_periods=fiscal_periods,
        fingerprints=fingerprints,
        observations=observations,
    )
    _validate_recovered_treatment(
        treatment,
        adoption,
        configuration=configuration,
        after_tax_available=after_tax_available,
        tax_disposition=tax_disposition,
        concept=concept,
    )
    _validate_recovered_authorization(
        adoption,
        authorization_kind=authorization_kind,
        mapping_status=mapping_status,
        real_company_acceptance=real_company_acceptance,
    )
    return AdmittedNormalizationBundle(
        financials=financials,
        analytical_line=line,
        analytical_identity=identity,
        statement=STATEMENT,
        company=company,
        fiscal_periods=fiscal_periods,
        analytical_values=tuple(analytical_values),
        face_values=tuple(face_values),
        transformation=transformation,
        sign_conversions_applied=SIGN_CONVERSION_ONCE,
        observations=observations,
        adoption=dict(adoption),
        treatment=dict(treatment),
        candidate_configuration={str(key): str(value) for key, value in configuration.items()},
        mapping_status=mapping_status,
        grouping_is_accepted_source_fact=False,
        authorization_kind=authorization_kind,
        after_tax_available=after_tax_available,
        tax_disposition=tax_disposition,
        note_tax_effects_attributed=bool(artifact.get("note_tax_effects_attributed")),
        real_company_acceptance=real_company_acceptance,
    )
