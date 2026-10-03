"""Shared adoption, treatment and authorization contracts for candidate handoff."""

from __future__ import annotations

from dataclasses import dataclass

AUTHORIZATION_SYNTHETIC = "synthetic"
AUTHORIZATION_INDEPENDENT = "independently_supplied"


@dataclass(frozen=True)
class AdoptionRecord:
    """Supplied grouping decision. Technical validation cannot establish it."""

    company: str
    axis: tuple[str, ...]
    member_identities: tuple[str, ...]
    analytical_concept: str
    analytical_label: str
    source_evidence_fingerprints: tuple[str, ...]
    mapping_decision: str
    decision_authority: str
    rationale: str
    analytical_scope: str
    decision_status: str
    authorization_kind: str
    approved: bool | None = None
    equivalent_by_concept: bool = False
    equivalent_by_agreeing_amounts: bool = False


@dataclass(frozen=True)
class TreatmentRecord:
    """Supplied treatment decision required before a candidate configuration."""

    scope: str
    reference_treatment: str
    rationale: str
    consequence_note: str
    aggregate_or_component: str
    cogs_boundary: str
    deductibility: str
    etr_disposition: str
    topic: str = "impairment_and_restructuring"
