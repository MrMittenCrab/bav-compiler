"""Modeler-owned persistence for admitted normalization-candidate provenance.

Dedicated admission artifact alongside model-only standardized financials.
Does not extend standardized_io or ordinary documentary reconciliation provenance.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Mapping, Sequence

from modeler.data.interface import LineItem, StandardizedFinancials
from modeler.data.line_identity import line_identity
from modeler.data.standardized_io import standardized_from_payload, standardized_to_payload

ARTIFACT_KIND = "normalization_candidate_admission"
ARTIFACT_SCHEMA = "normalization_candidate_admission/v1"
STATEMENT = "income_statement"
SIGN_CONVERSION_ONCE = 1


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
    }


def observation_evidence_from_payload(payload: Mapping[str, Any]) -> ObservationEvidence:
    if not isinstance(payload, Mapping):
        raise AdmissionProvenanceError("missing_admission_evidence")
    physical = payload.get("physical_page")
    if physical is not None:
        physical = int(physical)
    return ObservationEvidence(
        fingerprint=str(payload.get("fingerprint") or ""),
        source_file=str(payload.get("source_file") or ""),
        source_hash=str(payload.get("source_hash") or ""),
        row_identity=str(payload.get("row_identity") or ""),
        physical_page=physical,
        printed_page=payload.get("printed_page"),
        printed_page_status=str(payload.get("printed_page_status") or ""),
        period=str(payload.get("period") or ""),
        reported_amount=int(payload.get("reported_amount")),
        currency=str(payload.get("currency") or ""),
        unit_scale=str(payload.get("unit_scale") or ""),
    )


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
    if artifact.get("kind") != ARTIFACT_KIND or artifact.get("schema") != ARTIFACT_SCHEMA:
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
        after_tax_available=bool(artifact.get("after_tax_available")),
        tax_disposition=artifact.get("tax_disposition"),
        note_tax_effects_attributed=bool(artifact.get("note_tax_effects_attributed")),
        real_company_acceptance=bool(artifact.get("real_company_acceptance")),
    )
