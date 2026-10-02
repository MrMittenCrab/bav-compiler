"""Thin shared Driver records. No calculations, judgments, or wording."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResearchClaim:
    identifier: str
    wording: str
    claim_type: str
    measurement_role: str
    evidence_refs: tuple[str, ...]
    transformation: str
    qualifiers: tuple[str, ...]
    dependencies: tuple[str, ...]
    mechanism_support: str
    counterevidence: str
    status: str


@dataclass(frozen=True)
class ResearchQuestion:
    identifier: str
    question: str
    entity: str
    population: str
    periods: tuple[str, ...]
    outcome: str
    materiality_rationale: str
    temporal_character: str
    magnitude: str
    mechanisms: tuple[str, ...]
    alternative: str
    discriminating_evidence: str
    claims: tuple[ResearchClaim, ...]
    strongest_conclusion: str
    unresolved_requirement: str
    reopening_condition: str
    publication: str
    publication_reason: str
    overlap: tuple[str, ...] = ()
    figure_purpose: str | None = None
    figure_question: str | None = None
    main_body_table_reason: str | None = None


@dataclass(frozen=True)
class SelectionDecision:
    identifier: str
    action: str
    reason: str


@dataclass(frozen=True)
class ResearchSelection:
    questions: tuple[ResearchQuestion, ...]
    decisions: tuple[SelectionDecision, ...]
    main_body_ids: tuple[str, ...]
    figure_ids: tuple[str, ...]
    principal_ids: tuple[str, ...] = ()
    secondary_ids: tuple[str, ...] = ()
    appendix_ids: tuple[str, ...] = ()
    main_body_table_reasons: tuple[str, ...] = ()

    def question(self, identifier: str) -> ResearchQuestion | None:
        for item in self.questions:
            if item.identifier == identifier:
                return item
        return None

    def selected(self, identifier: str) -> bool:
        return identifier in self.main_body_ids

    def is_principal(self, identifier: str) -> bool:
        return identifier in self.principal_ids

    def is_secondary(self, identifier: str) -> bool:
        return identifier in self.secondary_ids
