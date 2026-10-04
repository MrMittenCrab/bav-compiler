"""Local proposition intake and deterministic proof-plan construction.

Benchmark entities and plan templates live in fixtures. This module does not
call a provider and does not present local plans as researched judgment.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

from dataclasses import replace

from bav.debater.contracts import (
    IntakeClassification,
    LinkedClaimDraft,
    PendingItem,
    ProofPlan,
    ProposedMeaning,
    QuestionDraft,
    SourceCandidate,
)
from bav.extractor.research.contracts import SnapshotInventory
from bav.extractor.research.paths import sha256_text

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "intake.json"

_PREDICATE = re.compile(
    r"\b(would|will|might|may|could|can|is|are|was|were|has|have|had|"
    r"accelerate|accelerates|improve|improves|exceed|exceeds|reported|"
    r"cause|causes|caused|increase|increases|decrease|decreases|grew|"
    r"grow|versus|compared|equal|greater|less|fit|fits)\b",
    re.IGNORECASE,
)
_NEGATION = re.compile(r"\b(not|no|never|without)\b", re.IGNORECASE)
_STRENGTH = re.compile(r"\b(would|will|might|may|could|can)\b", re.IGNORECASE)


def load_intake_fixtures(*, path: Path | None = None) -> dict[str, Any]:
    target = path or FIXTURE_PATH
    payload = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or "propositions" not in payload:
        raise ValueError("intake fixture must be an object with propositions")
    return payload


def normalize_proposition(text: str) -> str:
    return " ".join((text or "").split())


def proposition_key(text: str) -> str:
    return normalize_proposition(text)


def classify_proposition(
    text: str,
    *,
    fixtures: Mapping[str, Any] | None = None,
) -> IntakeClassification:
    original = text if text is not None else ""
    accepted = normalize_proposition(original)
    table = fixtures if fixtures is not None else load_intake_fixtures()
    limitation = str(
        table.get("planning_limitation")
        or "Local deterministic planning only. Not researched semantic judgment."
    )
    if not accepted:
        return _unclear(original, accepted, limitation, "Resubmit a complete proposition.")
    for item in table.get("propositions") or ():
        if item.get("match") == "exact" and normalize_proposition(item.get("text") or "") == accepted:
            meanings = tuple(
                ProposedMeaning(index=i + 1, statement=str(statement))
                for i, statement in enumerate(item.get("meanings") or ())
            )
            return IntakeClassification(
                original=original,
                accepted=accepted,
                clarity=item["clarity"],
                kind=item["kind"],
                title=str(item["title"]),
                fixture_id=str(item["id"]),
                plan_id=item.get("plan_id"),
                meanings=meanings,
                incoherent_together=bool(item.get("incoherent_together")),
                hypothetical=bool(item.get("hypothetical")),
                planning_limitation=limitation,
            )
    tokens = accepted.split()
    if len(tokens) < 3 or _PREDICATE.search(accepted) is None:
        return _unclear(
            original,
            accepted,
            limitation,
            "Resubmit with the acquirer and intended beneficiary.",
        )
    kind: str = "causal_strategic" if _STRENGTH.search(accepted) else "simple_fact"
    return IntakeClassification(
        original=original,
        accepted=accepted,
        clarity="clear",
        kind=kind,
        title=_title_from_proposition(accepted),
        fixture_id=None,
        plan_id=None,
        meanings=(),
        incoherent_together=False,
        hypothetical="acquisition" in accepted.casefold(),
        planning_limitation=limitation,
    )


def conservative_proposition_match(left: str, right: str) -> bool:
    """Exact accepted wording only. Negation, strength and entities are not guessed."""
    return proposition_key(left) == proposition_key(right)


def same_claim_signature(text: str) -> tuple[str, bool, tuple[str, ...]]:
    key = proposition_key(text).casefold()
    return (
        key,
        _NEGATION.search(key) is not None,
        tuple(_STRENGTH.findall(key)),
    )


def build_local_plan(
    classification: IntakeClassification,
    inventory: SnapshotInventory,
    *,
    fixtures: Mapping[str, Any] | None = None,
    retained_meanings: tuple[ProposedMeaning, ...] = (),
) -> ProofPlan:
    table = fixtures if fixtures is not None else load_intake_fixtures()
    templates = table.get("plans") or {}
    template = templates.get(classification.plan_id or "") or _generic_template(classification)
    candidates = tuple(_candidate(record) for record in inventory.records)
    limitations = tuple(dict.fromkeys(inventory.coverage_gaps))
    claims = tuple(_claim(item) for item in template["claims"])
    body = {
        "plan_id": classification.plan_id or classification.kind,
        "proposition": classification.accepted,
        "kind": classification.kind,
        "hypothetical": bool(template.get("hypothetical", classification.hypothetical)),
        "markets": list(template.get("markets") or ()),
        "markets_relation_to_asia": template["markets_relation_to_asia"],
        "comparison": template["comparison"],
        "growth_measure": template["growth_measure"],
        "unresolved_parameters": list(template.get("unresolved_parameters") or ()),
        "mechanism": template["mechanism"],
        "transfer_bridge": template["transfer_bridge"],
        "joint_inference": template["joint_inference"],
        "claims": [
            {
                "claim_id": claim.claim_id,
                "statement": claim.statement,
                "questions": [question.inquiry for question in claim.questions],
            }
            for claim in claims
        ],
        "fallbacks": list(template.get("fallbacks") or ()),
        "permitted_local_actions": list(template.get("permitted_local_actions") or ()),
        "excluded_obligations": list(template.get("excluded_obligations") or ()),
        "meanings": [item.statement for item in retained_meanings],
        "snapshot_id": inventory.snapshot_id,
        "snapshot_fingerprint": inventory.snapshot_fingerprint,
        "planning_limitation": classification.planning_limitation,
    }
    revision = sha256_text(json.dumps(body, sort_keys=True, separators=(",", ":")))[:16]
    return ProofPlan(
        plan_id=str(body["plan_id"]),
        revision=revision,
        proposition=classification.accepted,
        kind=classification.kind,
        hypothetical=bool(body["hypothetical"]),
        markets=tuple(body["markets"]),
        markets_relation_to_asia=str(template["markets_relation_to_asia"]),
        comparison=str(template["comparison"]),
        growth_measure=str(template["growth_measure"]),
        unresolved_parameters=tuple(body["unresolved_parameters"]),
        mechanism=str(template["mechanism"]),
        transfer_bridge=str(template["transfer_bridge"]),
        joint_inference=str(template["joint_inference"]),
        claims=claims,
        fallbacks=tuple(body["fallbacks"]),
        permitted_local_actions=tuple(body["permitted_local_actions"]),
        excluded_obligations=tuple(body["excluded_obligations"]),
        source_candidates=candidates,
        coverage_limitations=limitations,
        planning_limitation=classification.planning_limitation,
        snapshot_id=inventory.snapshot_id,
        snapshot_fingerprint=inventory.snapshot_fingerprint,
    )


def meanings_pending_display(
    classification: IntakeClassification,
) -> tuple[str, ...]:
    lines = ["Confirm meanings", classification.planning_limitation]
    for meaning in classification.meanings:
        lines.append(f"{meaning.index}  {meaning.statement}")
    return tuple(lines)


def proof_plan_display(plan: ProofPlan, *, case_fragment: str) -> tuple[str, ...]:
    del case_fragment
    lines = [
        "Confirm proof plan",
        plan.planning_limitation,
        f"Plan revision {plan.revision}",
    ]
    if plan.hypothetical:
        lines.append(f"Hypothetical acquisition. {plan.proposition}")
    else:
        lines.append(plan.proposition)
    if "would" in plan.proposition.casefold():
        lines.append("Strength remains would, not might.")
    if plan.markets:
        joined = " and ".join(plan.markets)
        lines.append(
            f"Focus markets {joined} are assessed separately. {plan.markets_relation_to_asia}"
        )
    else:
        lines.append(plan.markets_relation_to_asia)
    lines.append(plan.comparison)
    lines.append(plan.growth_measure)
    if plan.unresolved_parameters:
        lines.append(
            "Unresolved parameters are "
            + ", ".join(plan.unresolved_parameters)
            + ". None were invented."
        )
    if plan.excluded_obligations:
        lines.append(
            "Excluded obligations are " + ", ".join(plan.excluded_obligations) + "."
        )
    lines.append(plan.mechanism)
    lines.append(plan.transfer_bridge)
    lines.append(plan.joint_inference)
    lines.append("Linked claims")
    for index, claim in enumerate(plan.claims, start=1):
        lines.append(
            f"{index} {claim.statement} Proposed obligation, not an established premise."
        )
        for question in claim.questions:
            lines.append(f"{index}{question.question_id[-1].lower()} {question.inquiry}")
    for fallback in plan.fallbacks:
        lines.append(fallback)
    if plan.permitted_local_actions:
        lines.append(
            "Permitted local actions are "
            + ", ".join(plan.permitted_local_actions)
            + ". No provider launch."
        )
    if plan.source_candidates:
        lines.append("Source candidates")
        for item in plan.source_candidates:
            lines.append(
                f"{item.document_id} {item.representation} {item.original_filename}"
            )
    if plan.coverage_limitations:
        lines.append("Coverage limitations")
        for item in plan.coverage_limitations:
            lines.append(colon_safe(item))
    return tuple(lines)


def colon_safe(text: str) -> str:
    return text.replace(":", " -")


def default_provider_boundary(fixtures: Mapping[str, Any] | None = None) -> dict[str, str]:
    table = fixtures if fixtures is not None else load_intake_fixtures()
    boundary = table.get("default_provider_boundary") or {
        "backend": "cursor",
        "transmission": "closed",
        "installed_launch": "closed",
    }
    return {
        "backend": str(boundary.get("backend") or "cursor"),
        "transmission": str(boundary.get("transmission") or "closed"),
        "installed_launch": str(boundary.get("installed_launch") or "closed"),
    }


def approval_binding_for(item: PendingItem) -> str:
    """Hash the complete displayed item. Ignore any stored binding or revision label."""
    material = {
        "actions": list(item.actions),
        "allowance_fingerprint": item.allowance_fingerprint,
        "displayed": dict(item.displayed),
        "input_fingerprint": item.input_fingerprint,
        "item_id": item.item_id,
        "kind": item.kind,
        "provider_boundary": dict(item.provider_boundary),
        "revision": item.revision,
    }
    return sha256_text(json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True))


def bind_pending_item(item: PendingItem) -> PendingItem:
    return replace(item, approval_binding=approval_binding_for(item))


def pending_binding_matches(item: PendingItem) -> bool:
    stored = item.approval_binding
    if not stored:
        return False
    return stored == approval_binding_for(item)


def pending_from_meanings(
    classification: IntakeClassification,
    *,
    input_fingerprint: str,
    allowance_fingerprint: str,
    provider_boundary: Mapping[str, Any],
) -> PendingItem:
    displayed = {
        "kind": "meanings",
        "title": classification.title,
        "proposition": classification.accepted,
        "meanings": [meaning.statement for meaning in classification.meanings],
        "incoherent_together": classification.incoherent_together,
    }
    revision = sha256_text(json.dumps(displayed, sort_keys=True, separators=(",", ":")))[:16]
    return bind_pending_item(
        PendingItem(
            item_id=f"meanings-{revision}",
            kind="meanings",
            revision=revision,
            actions=("accept_meanings",),
            input_fingerprint=input_fingerprint,
            provider_boundary=dict(provider_boundary),
            allowance_fingerprint=allowance_fingerprint,
            displayed=displayed,
        )
    )


def pending_from_plan(
    plan: ProofPlan,
    *,
    input_fingerprint: str,
    allowance_fingerprint: str,
    provider_boundary: Mapping[str, Any],
    display_lines: tuple[str, ...],
) -> PendingItem:
    displayed = {
        "kind": "proof_plan",
        "revision": plan.revision,
        "plan": plan.to_payload(),
        "lines": list(display_lines),
    }
    return bind_pending_item(
        PendingItem(
            item_id=f"proof_plan-{plan.revision}",
            kind="proof_plan",
            revision=plan.revision,
            actions=("accept_scope", "accept_local_plan", "halt_before_provider"),
            input_fingerprint=input_fingerprint,
            provider_boundary=dict(provider_boundary),
            allowance_fingerprint=allowance_fingerprint,
            displayed=displayed,
        )
    )


def parse_exclude(raw: str | None, count: int) -> tuple[int, ...]:
    if raw is None or not str(raw).strip():
        raise ValueError("exclusions are missing")
    values: list[int] = []
    for part in str(raw).split(","):
        token = part.strip()
        if not token or not token.isdigit():
            raise ValueError("exclusions must be displayed meaning numbers")
        index = int(token)
        if index < 1 or index > count:
            raise ValueError("exclusions must name a displayed meaning")
        if index not in values:
            values.append(index)
    if len(values) >= count:
        raise ValueError("exclusions cannot remove every displayed meaning")
    return tuple(values)


def _unclear(
    original: str,
    accepted: str,
    limitation: str,
    title: str,
) -> IntakeClassification:
    del title
    return IntakeClassification(
        original=original,
        accepted=accepted,
        clarity="unclear",
        kind="simple_fact",
        title="",
        fixture_id=None,
        plan_id=None,
        meanings=(),
        incoherent_together=False,
        hypothetical=False,
        planning_limitation=limitation,
    )


def _title_from_proposition(text: str) -> str:
    title = text[:-1] if text.endswith(".") else text
    if len(title) > 90:
        title = title[:87].rstrip() + "..."
    return title


def _candidate(record: Any) -> SourceCandidate:
    return SourceCandidate(
        document_id=record.document_id,
        company_slug=record.company_slug,
        representation=record.representation,
        original_filename=record.original_filename,
        original_sha256=record.original_sha256,
        prepared_sha256=record.prepared_sha256,
        publication_date_status=record.publication_date_status,
        limitations=tuple(record.limitations),
    )


def _claim(item: Mapping[str, Any]) -> LinkedClaimDraft:
    return LinkedClaimDraft(
        claim_id=str(item["claim_id"]),
        statement=str(item["statement"]),
        role="proposed_obligation",
        questions=tuple(
            QuestionDraft(
                question_id=str(question["question_id"]),
                inquiry=str(question["inquiry"]),
                why_it_matters=str(question["why_it_matters"]),
                minimum_useful_data=str(question["minimum_useful_data"]),
            )
            for question in item.get("questions") or ()
        ),
        assumptions=tuple(str(value) for value in item.get("assumptions") or ()),
        failure_conditions=tuple(str(value) for value in item.get("failure_conditions") or ()),
    )


def _generic_template(classification: IntakeClassification) -> dict[str, Any]:
    return {
        "hypothetical": classification.hypothetical,
        "markets": [],
        "markets_relation_to_asia": "No hidden Japan or Greater China scope is added.",
        "comparison": "Keep the submitted comparison. Do not enlarge it into acquisition value.",
        "growth_measure": "Use the submitted outcome. Do not substitute store count or invent uplift.",
        "unresolved_parameters": ["uplift", "closing date", "forecast"],
        "mechanism": "State the concrete mechanism named by the proposition.",
        "transfer_bridge": "A cross-company claim needs an explicit bridge. Two descriptions are not enough.",
        "joint_inference": "The submitted claim holds only if its mechanism and comparison both hold.",
        "excluded_obligations": ["acquisition valuation"],
        "fallbacks": [
            "If local sources lack a discriminating observation, request one specific file."
        ],
        "permitted_local_actions": [
            "inspect registered research-source inventory",
            "retrieve prepared passages already in the snapshot",
        ],
        "claims": [
            {
                "claim_id": "C1",
                "statement": classification.accepted,
                "questions": [
                    {
                        "question_id": "Q1a",
                        "inquiry": "What observation would confirm or undermine the submitted mechanism?",
                        "why_it_matters": "A claim without a discriminating test is not a linked argument.",
                        "minimum_useful_data": "A sourced fact that could change the claim, including contrary evidence.",
                    }
                ],
                "assumptions": [classification.planning_limitation],
                "failure_conditions": [
                    "The wording or strength of the proposition is silently changed."
                ],
            }
        ],
    }
