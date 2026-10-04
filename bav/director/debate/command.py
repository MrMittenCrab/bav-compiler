"""Noninteractive debate command. Local intake and approval only."""

from __future__ import annotations

import argparse
import json
from typing import Any, Mapping

from bav.debater.contracts import (
    DebateEnvelope,
    IntakeClassification,
    PendingItem,
    ProofPlan,
    ProposedMeaning,
)
from bav.debater.intake import (
    build_local_plan,
    classify_proposition,
    default_provider_boundary,
    load_intake_fixtures,
    meanings_pending_display,
    parse_exclude,
    pending_from_meanings,
    pending_from_plan,
    proof_plan_display,
)
from bav.director.debate.store import (
    CaseLocked,
    CaseRecord,
    CaseSelectionError,
    allocate_slug,
    allocate_title,
    allowance_fingerprint,
    cases_root,
    default_allowance,
    find_by_proposition,
    increment_intake,
    list_cases,
    load_case,
    locked_case,
    new_case_payload,
    pending_from_payload,
    select_case,
    write_case_atomically,
)
from bav.director.debate.terminal import format_terminal
from bav.director.research_corpus import inventory_approved_snapshot
from bav.extractor.research.contracts import SnapshotInventory
from bav.extractor.research.paths import sha256_text
from bav.extractor.research.snapshot import DEFAULT_SNAPSHOT_ID

PROVIDER_LAUNCHES = {"invoke": 0, "verify": 0, "company_transmission": 0}

_UNIMPLEMENTED = {
    "add": "File add is not implemented in this intake path.",
    "note": "Notes are not implemented in this intake path.",
    "backend": "Backend change is not implemented. Installed transmission stays closed.",
}


def run_debate_command(
    args: argparse.Namespace,
    *,
    cases_dir=None,
    inventory: SnapshotInventory | None = None,
    fixtures: Mapping[str, Any] | None = None,
) -> int:
    envelope = execute_debate(
        args,
        cases_dir=cases_dir,
        inventory=inventory,
        fixtures=fixtures,
    )
    text = format_terminal(envelope)
    if text:
        print(text, end="")
    return envelope.exit_code


def execute_debate(
    args: argparse.Namespace,
    *,
    cases_dir=None,
    inventory: SnapshotInventory | None = None,
    fixtures: Mapping[str, Any] | None = None,
) -> DebateEnvelope:
    root = cases_dir if cases_dir is not None else cases_root()
    table = fixtures if fixtures is not None else load_intake_fixtures()
    conflict = _validate_invocation(args)
    if conflict is not None:
        return conflict
    unimplemented = _unimplemented(args)
    if unimplemented is not None:
        return unimplemented
    if args.list:
        return _list_envelope(root)
    snapshot = inventory if inventory is not None else _load_inventory(table)
    if getattr(args, "proposition", None):
        return _submit(args, root, snapshot, table)
    if not args.case:
        return _error("Submit a proposition or select a case.")
    try:
        record = select_case(root, args.case)
    except CaseSelectionError as exc:
        return _selection_error(root, exc)
    if args.status:
        return _display_record(record, kind="status", mutated=False)
    if args.approve:
        return _approve(args, root, record, snapshot, table)
    if args.backend:
        return _envelope(
            next_lines=(_UNIMPLEMENTED["backend"], "The saved backend and allowance are unchanged."),
            case_title=record.title,
            case_slug=record.slug,
            kind="backend_rejected",
            exit_code=1,
        )
    return _resume(record, snapshot, table)


def _validate_invocation(args: argparse.Namespace) -> DebateEnvelope | None:
    proposition = getattr(args, "proposition", None)
    has_case = bool(getattr(args, "case", None))
    flags = [
        bool(getattr(args, "list", False)),
        bool(getattr(args, "status", False)),
        bool(getattr(args, "approve", False)),
        bool(getattr(args, "exclude", None)),
        bool(getattr(args, "add", None)),
        bool(getattr(args, "note", None)),
        bool(getattr(args, "backend", None)),
    ]
    if args.list and (proposition or has_case or any(flags[1:])):
        return _error("Conflicting options. List is read-only.")
    if args.status and (proposition or args.approve or args.exclude or args.add or args.note or args.backend):
        return _error("Conflicting options. Status is read-only.")
    if args.status and not has_case:
        return _error("Status requires a case.")
    if args.exclude and not args.approve:
        return _error("Exclusions require approval of the displayed meanings.")
    if args.approve and (args.add or args.note or args.backend):
        return _error("Conflicting options. Approve cannot combine with files, notes, or a backend change.")
    if args.approve and not has_case and not proposition:
        return _error("Approve requires a case.")
    if args.approve and proposition:
        return _error("Conflicting options. Approve a saved case rather than a new proposition.")
    if proposition and has_case:
        return _error("Conflicting options. Submit a proposition or select a case.")
    if args.backend and proposition:
        return _error("Conflicting options. Process a backend change on a saved case.")
    return None


def _unimplemented(args: argparse.Namespace) -> DebateEnvelope | None:
    if args.add:
        return _error(_UNIMPLEMENTED["add"], kind="unimplemented")
    if args.note:
        return _error(_UNIMPLEMENTED["note"], kind="unimplemented")
    return None


def _submit(
    args: argparse.Namespace,
    root,
    inventory: SnapshotInventory,
    fixtures: Mapping[str, Any],
) -> DebateEnvelope:
    classification = classify_proposition(args.proposition, fixtures=fixtures)
    if classification.clarity == "unclear":
        return _envelope(
            next_lines=("Resubmit with the acquirer and intended beneficiary.",),
            kind="rejected_proposition",
        )
    existing = find_by_proposition(root, classification.accepted)
    if existing is not None:
        return _resume(existing, inventory, fixtures)
    title = allocate_title(root, classification.title, classification.accepted)
    slug = allocate_slug(root, title, classification.accepted)
    directory = root / slug
    try:
        with locked_case(directory):
            if (directory / "case.json").is_file():
                return _resume(load_case(directory), inventory, fixtures)
            boundary = default_provider_boundary(fixtures)
            allowance = increment_intake(default_allowance(), planning=True)
            corpus = _corpus_payload(inventory)
            input_fp = _input_fingerprint(
                inventory,
                classification.accepted,
                boundary,
                _fingerprint_meanings(classification),
            )
            allow_fp = allowance_fingerprint(allowance)
            pending, lines, approved_scope, approved_plan = _opening_pending(
                classification,
                inventory,
                fixtures,
                input_fp,
                allow_fp,
                boundary,
                title,
            )
            display = {
                "case_title": title,
                "status": None,
                "next_lines": list(lines) + [_approve_command(title) if pending else _resume_command(title)],
            }
            payload = new_case_payload(
                title=title,
                slug=slug,
                classification=_classification_payload(classification),
                pending=pending,
                corpus=corpus,
                backend=boundary,
                allowance=allowance,
                last_display=display,
                approved_scope=approved_scope,
                approved_plan=approved_plan,
            )
            path = write_case_atomically(directory, payload)
            return _envelope(
                next_lines=tuple(display["next_lines"]),
                case_title=title,
                case_slug=slug,
                kind="submit",
                mutated=True,
                pending_kind=pending.kind if pending else None,
                details={"path": str(path), "revision": payload["revision"]},
            )
    except CaseLocked:
        return _error("The case is locked. Preserve the work and retry.", case_title=title)


def _opening_pending(
    classification: IntakeClassification,
    inventory: SnapshotInventory,
    fixtures: Mapping[str, Any],
    input_fp: str,
    allow_fp: str,
    boundary: Mapping[str, Any],
    title: str,
) -> tuple[PendingItem | None, tuple[str, ...], dict[str, Any] | None, dict[str, Any] | None]:
    if classification.clarity == "ambiguous":
        pending = pending_from_meanings(
            classification,
            input_fingerprint=input_fp,
            allowance_fingerprint=allow_fp,
            provider_boundary=boundary,
        )
        return pending, meanings_pending_display(classification), None, None
    if classification.kind == "simple_fact":
        scope = {
            "proposition": classification.accepted,
            "meanings": [classification.accepted],
            "kind": classification.kind,
        }
        lines = _runtime_blocker_lines(
            extra=("Simple fact scope needs no extra proof-plan approval.", classification.planning_limitation)
        )
        return None, lines, scope, None
    plan = build_local_plan(classification, inventory, fixtures=fixtures)
    display = proof_plan_display(plan, case_fragment=title)
    pending = pending_from_plan(
        plan,
        input_fingerprint=input_fp,
        allowance_fingerprint=allow_fp,
        provider_boundary=boundary,
        display_lines=display,
    )
    return pending, display, None, None


def _approve(
    args: argparse.Namespace,
    root,
    record: CaseRecord,
    inventory: SnapshotInventory,
    fixtures: Mapping[str, Any],
) -> DebateEnvelope:
    directory = record.path.parent
    try:
        with locked_case(directory):
            current = load_case(directory)
            pending = pending_from_payload(current.pending)
            if pending is None or pending.consumed:
                return _envelope(
                    next_lines=("No pending item. The saved case is unchanged.",),
                    case_title=current.title,
                    case_slug=current.slug,
                    kind="approve_absent",
                    exit_code=1,
                    details={"authority": current.authority},
                )
            if args.exclude and pending.kind != "meanings":
                return _envelope(
                    next_lines=("Exclusions apply only to displayed meanings.",),
                    case_title=current.title,
                    case_slug=current.slug,
                    kind="invalid_exclude",
                    exit_code=1,
                    details={"authority": current.authority},
                )
            live_fp = _live_fingerprints(current, inventory)
            if (
                live_fp["input"] != pending.input_fingerprint
                or live_fp["allowance"] != pending.allowance_fingerprint
                or live_fp["provider"] != dict(pending.provider_boundary)
            ):
                return _rebind_changed(current, inventory, fixtures, live_fp)
            payload = dict(current.payload)
            if pending.kind == "meanings":
                return _approve_meanings(args, payload, pending, inventory, fixtures, directory)
            return _approve_plan(payload, pending, directory)
    except CaseLocked:
        return _error("The case is locked. Preserve the work and retry.", case_title=record.title)


def _approve_meanings(
    args: argparse.Namespace,
    payload: dict[str, Any],
    pending: PendingItem,
    inventory: SnapshotInventory,
    fixtures: Mapping[str, Any],
    directory,
) -> DebateEnvelope:
    meanings = [
        ProposedMeaning(index=i + 1, statement=str(item))
        for i, item in enumerate(pending.displayed.get("meanings") or ())
    ]
    try:
        excluded = parse_exclude(args.exclude, len(meanings)) if args.exclude else ()
    except ValueError as exc:
        return _envelope(
            next_lines=(str(exc).rstrip(".") + ".",),
            case_title=payload["title"],
            case_slug=payload["slug"],
            kind="invalid_exclude",
            exit_code=1,
            details={"authority": sha256_text(_canonical(payload))},
        )
    retained = tuple(item for item in meanings if item.index not in excluded)
    classification = classify_proposition(payload["proposition"]["accepted"], fixtures=fixtures)
    if pending.displayed.get("incoherent_together") and len(retained) != 1:
        payload["pending"] = None
        payload["consumed_approvals"] = list(payload.get("consumed_approvals") or ()) + [pending.item_id]
        payload["proposition"] = dict(payload["proposition"])
        payload["proposition"]["meanings"] = [item.statement for item in retained]
        payload["allowance"] = increment_intake(payload["allowance"], planning=False)
        payload["revision"] = int(payload.get("revision") or 1) + 1
        lines = (
            "Resubmit narrower propositions. The retained meanings do not form one linked argument.",
        )
        payload["last_display"] = {
            "case_title": payload["title"],
            "status": None,
            "next_lines": list(lines),
        }
        write_case_atomically(directory, payload)
        return _envelope(
            next_lines=lines,
            case_title=payload["title"],
            case_slug=payload["slug"],
            kind="meanings_narrower",
            mutated=True,
        )
    selected = IntakeClassification(
        original=classification.original,
        accepted=classification.accepted,
        clarity="clear",
        kind=classification.kind,
        title=payload["title"],
        fixture_id=classification.fixture_id,
        plan_id=classification.plan_id,
        meanings=retained,
        incoherent_together=False,
        hypothetical=classification.hypothetical,
        planning_limitation=classification.planning_limitation,
    )
    plan = build_local_plan(selected, inventory, fixtures=fixtures, retained_meanings=retained)
    display = proof_plan_display(plan, case_fragment=payload["title"])
    boundary = dict(payload.get("backend") or default_provider_boundary(fixtures))
    allowance = increment_intake(payload["allowance"], planning=True)
    new_pending = pending_from_plan(
        plan,
        input_fingerprint=_input_fingerprint(inventory, selected.accepted, boundary, retained),
        allowance_fingerprint=allowance_fingerprint(allowance),
        provider_boundary=boundary,
        display_lines=display,
    )
    payload["pending"] = new_pending.to_payload()
    payload["consumed_approvals"] = list(payload.get("consumed_approvals") or ()) + [pending.item_id]
    payload["proposition"] = dict(payload["proposition"])
    payload["proposition"]["meanings"] = [item.statement for item in retained]
    payload["allowance"] = allowance
    payload["revision"] = int(payload.get("revision") or 1) + 1
    lines = display + (_approve_command(payload["title"]),)
    payload["last_display"] = {
        "case_title": payload["title"],
        "status": None,
        "next_lines": list(lines),
    }
    write_case_atomically(directory, payload)
    return _envelope(
        next_lines=lines,
        case_title=payload["title"],
        case_slug=payload["slug"],
        kind="meanings_approved",
        mutated=True,
        pending_kind="proof_plan",
        details={"consumed": pending.item_id, "new_pending": new_pending.item_id},
    )


def _approve_plan(payload: dict[str, Any], pending: PendingItem, directory) -> DebateEnvelope:
    plan = pending.displayed.get("plan") or {}
    payload["pending"] = None
    payload["consumed_approvals"] = list(payload.get("consumed_approvals") or ()) + [pending.item_id]
    payload["approved_scope"] = {
        "proposition": payload["proposition"]["accepted"],
        "meanings": list(payload["proposition"].get("meanings") or ()),
        "markets": list(plan.get("markets") or ()),
        "comparison": plan.get("comparison"),
        "growth_measure": plan.get("growth_measure"),
        "unresolved_parameters": list(plan.get("unresolved_parameters") or ()),
    }
    payload["approved_plan"] = plan
    payload["allowance"] = increment_intake(payload["allowance"], planning=False)
    payload["revision"] = int(payload.get("revision") or 1) + 1
    lines = _runtime_blocker_lines(
        extra=(
            "Approved scope and plan are saved locally.",
            "Approval is not transmission authorization and not evidence a premise is true.",
        )
    ) + (_resume_command(payload["title"]),)
    payload["last_display"] = {
        "case_title": payload["title"],
        "status": None,
        "next_lines": list(lines),
    }
    write_case_atomically(directory, payload)
    return _envelope(
        next_lines=lines,
        case_title=payload["title"],
        case_slug=payload["slug"],
        kind="plan_approved",
        mutated=True,
        details={"consumed": pending.item_id, "plan_revision": pending.revision},
    )


def _rebind_changed(
    record: CaseRecord,
    inventory: SnapshotInventory,
    fixtures: Mapping[str, Any],
    live_fp: Mapping[str, Any],
) -> DebateEnvelope:
    payload = dict(record.payload)
    pending = pending_from_payload(record.pending)
    if pending is None:
        return _display_record(record, kind="resume", mutated=False)
    classification = classify_proposition(payload["proposition"]["accepted"], fixtures=fixtures)
    if pending.kind == "meanings":
        classification = IntakeClassification(
            original=classification.original,
            accepted=classification.accepted,
            clarity="ambiguous",
            kind=classification.kind,
            title=payload["title"],
            fixture_id=classification.fixture_id,
            plan_id=classification.plan_id,
            meanings=tuple(
                ProposedMeaning(index=i + 1, statement=str(item))
                for i, item in enumerate(pending.displayed.get("meanings") or ())
            ),
            incoherent_together=bool(pending.displayed.get("incoherent_together")),
            hypothetical=classification.hypothetical,
            planning_limitation=classification.planning_limitation,
        )
        new_pending = pending_from_meanings(
            classification,
            input_fingerprint=str(live_fp["input"]),
            allowance_fingerprint=str(live_fp["allowance"]),
            provider_boundary=dict(live_fp["provider"]),
        )
        lines = meanings_pending_display(classification) + (_approve_command(payload["title"]),)
    else:
        retained = tuple(
            ProposedMeaning(index=i + 1, statement=str(item))
            for i, item in enumerate(payload["proposition"].get("meanings") or ())
        )
        plan = build_local_plan(classification, inventory, fixtures=fixtures, retained_meanings=retained)
        display = proof_plan_display(plan, case_fragment=payload["title"])
        new_pending = pending_from_plan(
            plan,
            input_fingerprint=str(live_fp["input"]),
            allowance_fingerprint=str(live_fp["allowance"]),
            provider_boundary=dict(live_fp["provider"]),
            display_lines=display,
        )
        lines = display + (_approve_command(payload["title"]),)
    payload["pending"] = new_pending.to_payload()
    payload["corpus"] = _corpus_payload(inventory)
    payload["revision"] = int(payload.get("revision") or 1) + 1
    payload["last_display"] = {
        "case_title": payload["title"],
        "status": None,
        "next_lines": list(lines),
    }
    write_case_atomically(record.path.parent, payload)
    return _envelope(
        next_lines=("The pending item changed. A subsequent approval is required.",) + lines[1:],
        case_title=payload["title"],
        case_slug=payload["slug"],
        kind="approval_rebound",
        mutated=True,
        pending_kind=new_pending.kind,
    )


def _resume(
    record: CaseRecord,
    inventory: SnapshotInventory,
    fixtures: Mapping[str, Any],
) -> DebateEnvelope:
    pending = pending_from_payload(record.pending)
    if pending is not None and not pending.consumed:
        live_fp = _live_fingerprints(record, inventory)
        if (
            live_fp["input"] != pending.input_fingerprint
            or live_fp["allowance"] != pending.allowance_fingerprint
            or live_fp["provider"] != dict(pending.provider_boundary)
        ):
            try:
                with locked_case(record.path.parent):
                    return _rebind_changed(load_case(record.path.parent), inventory, fixtures, live_fp)
            except CaseLocked:
                return _error("The case is locked. Preserve the work and retry.", case_title=record.title)
    return _display_record(record, kind="resume", mutated=False)


def _display_record(record: CaseRecord, *, kind: str, mutated: bool) -> DebateEnvelope:
    display = record.payload.get("last_display") or {}
    pending = pending_from_payload(record.pending)
    lines = tuple(display.get("next_lines") or ("Saved case.",))
    return _envelope(
        next_lines=lines,
        case_title=record.title,
        case_slug=record.slug,
        status=record.payload.get("status"),
        kind=kind,
        mutated=mutated,
        pending_kind=pending.kind if pending and not pending.consumed else None,
        details={"authority": record.authority, "revision": record.payload.get("revision")},
    )


def _list_envelope(root) -> DebateEnvelope:
    records = list_cases(root)
    if not records:
        return _envelope(next_lines=("No cases. Submit a proposition.",), kind="list")
    return _envelope(
        next_lines=("Cases", *(record.title for record in records)),
        kind="list",
    )


def _selection_error(root, exc: CaseSelectionError) -> DebateEnvelope:
    if str(exc) == "ambiguous":
        titles = tuple(record.title for record in list_cases(root))
        return _envelope(next_lines=("Multiple matching titles", *titles), kind="ambiguous_case")
    return _envelope(
        next_lines=("No matching case. python -m bav debate --list",),
        kind="missing_case",
    )


def _load_inventory(fixtures: Mapping[str, Any]) -> SnapshotInventory:
    snapshot_id = str(fixtures.get("snapshot_id") or DEFAULT_SNAPSHOT_ID)
    return inventory_approved_snapshot(snapshot_id)


def _corpus_payload(inventory: SnapshotInventory) -> dict[str, Any]:
    return {
        "snapshot_id": inventory.snapshot_id,
        "snapshot_fingerprint": inventory.snapshot_fingerprint,
        "source_candidates": [
            {
                "document_id": record.document_id,
                "company_slug": record.company_slug,
                "representation": record.representation,
                "original_filename": record.original_filename,
                "original_sha256": record.original_sha256,
                "prepared_sha256": record.prepared_sha256,
            }
            for record in inventory.records
        ],
        "coverage_limitations": list(inventory.coverage_gaps),
    }


def _classification_payload(classification: IntakeClassification) -> dict[str, Any]:
    return {
        "original": classification.original,
        "accepted": classification.accepted,
        "clarity": classification.clarity,
        "kind": classification.kind,
        "fixture_id": classification.fixture_id,
        "meanings": [item.statement for item in classification.meanings] or [classification.accepted],
    }


def _input_fingerprint(
    inventory: SnapshotInventory,
    proposition: str,
    boundary: Mapping[str, Any],
    meanings: tuple[ProposedMeaning, ...] | None = None,
) -> str:
    payload = {
        "snapshot": inventory.snapshot_fingerprint,
        "proposition": proposition,
        "meanings": [item.statement for item in meanings or ()],
        "provider": dict(boundary),
    }
    return sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def _fingerprint_meanings(classification: IntakeClassification) -> tuple[ProposedMeaning, ...]:
    if classification.meanings:
        return classification.meanings
    return (ProposedMeaning(index=1, statement=classification.accepted),)


def _live_fingerprints(record: CaseRecord, inventory: SnapshotInventory) -> dict[str, Any]:
    boundary = dict(record.payload.get("backend") or default_provider_boundary())
    meanings = tuple(
        ProposedMeaning(index=i + 1, statement=str(item))
        for i, item in enumerate(record.payload.get("proposition", {}).get("meanings") or ())
    )
    return {
        "input": _input_fingerprint(inventory, record.proposition, boundary, meanings),
        "allowance": allowance_fingerprint(record.payload.get("allowance") or {}),
        "provider": boundary,
    }


def _runtime_blocker_lines(*, extra: tuple[str, ...] = ()) -> tuple[str, ...]:
    return (
        "Installed launch is closed.",
        *extra,
        "No supported BAV verification path binds the backend, executable, version, policy, and launch boundary.",
        "Local intake is not a research verdict and does not transmit the company corpus.",
    )


def _approve_command(title: str) -> str:
    fragment = _fragment(title)
    return f'python -m bav debate --case "{fragment}" --approve'


def _resume_command(title: str) -> str:
    fragment = _fragment(title)
    return f'python -m bav debate --case "{fragment}"'


def _fragment(title: str) -> str:
    return title


def _canonical(payload: Mapping[str, Any]) -> str:
    from bav.director.debate.store import canonical_json

    return canonical_json(payload)


def _error(
    message: str,
    *,
    case_title: str | None = None,
    case_slug: str | None = None,
    kind: str = "invalid",
) -> DebateEnvelope:
    return _envelope(
        next_lines=(message,),
        case_title=case_title,
        case_slug=case_slug,
        kind=kind,
        exit_code=1,
    )


def _envelope(
    *,
    next_lines: tuple[str, ...],
    case_title: str | None = None,
    case_slug: str | None = None,
    status: str | None = None,
    kind: str,
    exit_code: int = 0,
    mutated: bool = False,
    pending_kind: str | None = None,
    details: Mapping[str, Any] | None = None,
) -> DebateEnvelope:
    return DebateEnvelope(
        exit_code=exit_code,
        case_title=case_title,
        case_slug=case_slug,
        status=status,
        next_lines=next_lines,
        kind=kind,
        mutated=mutated,
        provider_launched=False,
        company_transmitted=False,
        pending_kind=pending_kind,
        details=dict(details or {}),
    )


def assert_no_provider_use() -> None:
    if any(PROVIDER_LAUNCHES.values()):
        raise RuntimeError("intake launched a provider or transmitted company context")
