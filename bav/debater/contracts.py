"""Proposition, meaning, and local proof-plan contracts owned by Debater."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Mapping

Clarity = Literal["clear", "ambiguous", "unclear"]
PropositionKind = Literal["causal_strategic", "simple_fact"]
PendingKind = Literal["meanings", "proof_plan"]
ClaimRole = Literal["proposed_obligation"]


@dataclass(frozen=True)
class ProposedMeaning:
    index: int
    statement: str


@dataclass(frozen=True)
class QuestionDraft:
    question_id: str
    inquiry: str
    why_it_matters: str
    minimum_useful_data: str


@dataclass(frozen=True)
class LinkedClaimDraft:
    claim_id: str
    statement: str
    role: ClaimRole
    questions: tuple[QuestionDraft, ...]
    assumptions: tuple[str, ...]
    failure_conditions: tuple[str, ...]


@dataclass(frozen=True)
class SourceCandidate:
    document_id: str
    company_slug: str | None
    representation: str
    original_filename: str
    original_sha256: str
    prepared_sha256: str
    publication_date_status: str
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class ProofPlan:
    plan_id: str
    revision: str
    proposition: str
    kind: PropositionKind
    hypothetical: bool
    markets: tuple[str, ...]
    markets_relation_to_asia: str
    comparison: str
    growth_measure: str
    unresolved_parameters: tuple[str, ...]
    mechanism: str
    transfer_bridge: str
    joint_inference: str
    claims: tuple[LinkedClaimDraft, ...]
    fallbacks: tuple[str, ...]
    permitted_local_actions: tuple[str, ...]
    excluded_obligations: tuple[str, ...]
    source_candidates: tuple[SourceCandidate, ...]
    coverage_limitations: tuple[str, ...]
    planning_limitation: str
    snapshot_id: str
    snapshot_fingerprint: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "revision": self.revision,
            "proposition": self.proposition,
            "kind": self.kind,
            "hypothetical": self.hypothetical,
            "markets": list(self.markets),
            "markets_relation_to_asia": self.markets_relation_to_asia,
            "comparison": self.comparison,
            "growth_measure": self.growth_measure,
            "unresolved_parameters": list(self.unresolved_parameters),
            "mechanism": self.mechanism,
            "transfer_bridge": self.transfer_bridge,
            "joint_inference": self.joint_inference,
            "claims": [
                {
                    "claim_id": claim.claim_id,
                    "statement": claim.statement,
                    "role": claim.role,
                    "questions": [
                        {
                            "question_id": question.question_id,
                            "inquiry": question.inquiry,
                            "why_it_matters": question.why_it_matters,
                            "minimum_useful_data": question.minimum_useful_data,
                        }
                        for question in claim.questions
                    ],
                    "assumptions": list(claim.assumptions),
                    "failure_conditions": list(claim.failure_conditions),
                }
                for claim in self.claims
            ],
            "fallbacks": list(self.fallbacks),
            "permitted_local_actions": list(self.permitted_local_actions),
            "excluded_obligations": list(self.excluded_obligations),
            "source_candidates": [
                {
                    "document_id": item.document_id,
                    "company_slug": item.company_slug,
                    "representation": item.representation,
                    "original_filename": item.original_filename,
                    "original_sha256": item.original_sha256,
                    "prepared_sha256": item.prepared_sha256,
                    "publication_date_status": item.publication_date_status,
                    "limitations": list(item.limitations),
                }
                for item in self.source_candidates
            ],
            "coverage_limitations": list(self.coverage_limitations),
            "planning_limitation": self.planning_limitation,
            "snapshot_id": self.snapshot_id,
            "snapshot_fingerprint": self.snapshot_fingerprint,
        }


@dataclass(frozen=True)
class IntakeClassification:
    original: str
    accepted: str
    clarity: Clarity
    kind: PropositionKind
    title: str
    fixture_id: str | None
    plan_id: str | None
    meanings: tuple[ProposedMeaning, ...]
    incoherent_together: bool
    hypothetical: bool
    planning_limitation: str = (
        "Local deterministic planning only. Not researched semantic judgment."
    )


@dataclass(frozen=True)
class PendingItem:
    item_id: str
    kind: PendingKind
    revision: str
    actions: tuple[str, ...]
    input_fingerprint: str
    provider_boundary: Mapping[str, Any]
    allowance_fingerprint: str
    displayed: Mapping[str, Any]
    consumed: bool = False
    approval_binding: str | None = None

    def to_payload(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "kind": self.kind,
            "revision": self.revision,
            "actions": list(self.actions),
            "input_fingerprint": self.input_fingerprint,
            "provider_boundary": dict(self.provider_boundary),
            "allowance_fingerprint": self.allowance_fingerprint,
            "displayed": dict(self.displayed),
            "consumed": self.consumed,
            "approval_binding": self.approval_binding,
        }


@dataclass(frozen=True)
class DebateEnvelope:
    exit_code: int
    case_title: str | None
    case_slug: str | None
    status: str | None
    next_lines: tuple[str, ...]
    kind: str
    mutated: bool
    provider_launched: bool
    company_transmitted: bool
    pending_kind: str | None
    details: Mapping[str, Any] = field(default_factory=dict)
