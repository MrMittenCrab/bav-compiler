"""Typed application dispatcher. Provider output cannot grant permissions."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from bav.director.runtime.contract import ALLOWED_OPERATIONS, ApprovedSnapshot, AttemptRecord
from bav.director.runtime.policy import (
    classify_operation,
    managed_source_name,
    source_contains_instructions,
    text_fingerprint,
    validate_approved_path,
)


class ApplicationDispatcher:
    def __init__(
        self,
        snapshot: ApprovedSnapshot,
        workspace,
        inventory: list[Mapping[str, Any]] | None = None,
    ) -> None:
        self.snapshot = snapshot
        self.workspace = workspace
        self._by_id = {source.source_id: source for source in snapshot.sources}
        self._managed = {
            source.source_id: managed_source_name(source.source_id)
            for source in snapshot.sources
        }
        for item in inventory or []:
            source_id = str(item.get("source_id") or "")
            managed = item.get("managed_name")
            if source_id and isinstance(managed, str):
                self._managed[source_id] = managed
        self._dispatch_count = 0

    @property
    def dispatch_count(self) -> int:
        return self._dispatch_count

    def handle(self, operation: str, arguments: Mapping[str, Any]) -> AttemptRecord:
        decision = self.decide(operation, arguments)
        if decision.decision != "allowed":
            return decision
        return self.execute(decision)

    def decide(self, operation: str, arguments: Mapping[str, Any]) -> AttemptRecord:
        if not isinstance(operation, str) or not operation.strip():
            return AttemptRecord(str(operation), {}, "denied", "invalid_operation_name", False)
        if not isinstance(arguments, Mapping):
            return AttemptRecord(operation, {}, "denied", "invalid_arguments", False)
        kind = classify_operation(operation)
        args = dict(arguments)
        if kind == "prohibited":
            reason = "prohibited_native_or_external_operation"
            if operation.lower() == "apply_source_policy" or self._cites_source_instruction(args):
                reason = "source_contained_instruction"
            return AttemptRecord(operation, args, "denied", reason, False)
        if kind == "unknown":
            return AttemptRecord(operation, args, "denied", "unknown_operation", False)
        if operation not in ALLOWED_OPERATIONS:
            return AttemptRecord(operation, args, "denied", "unknown_operation", False)
        if self._cites_source_instruction(args):
            return AttemptRecord(
                operation, args, "denied", "source_contained_instruction", False
            )
        if operation == "inspect_approved_source":
            return self._inspect_decision(args)
        return AttemptRecord(operation, args, "denied", "unknown_operation", False)

    def execute(self, decision: AttemptRecord) -> AttemptRecord:
        if decision.decision != "allowed" or decision.operation != "inspect_approved_source":
            return decision
        source_id = str(decision.arguments.get("source_id") or "")
        source = self._by_id.get(source_id)
        if source is None:
            return AttemptRecord(
                decision.operation,
                decision.arguments,
                "denied",
                "unapproved_source",
                False,
                source_binding=decision.source_binding,
            )
        self._dispatch_count += 1
        return AttemptRecord(
            decision.operation,
            decision.arguments,
            "allowed",
            decision.reason,
            True,
            {
                "source_id": source.source_id,
                "label": source.label,
                "fingerprint": source.fingerprint,
                "text": source.text,
                "origin": source.origin,
            },
            source_binding=decision.source_binding,
        )

    def _inspect_decision(self, args: Mapping[str, Any]) -> AttemptRecord:
        source_id = str(args.get("source_id") or "")
        source = self._by_id.get(source_id)
        if source is None:
            return AttemptRecord(
                "inspect_approved_source", args, "denied", "unapproved_source", False
            )
        managed = self._managed.get(source_id) or managed_source_name(source_id)
        binding = {
            "source_id": source.source_id,
            "managed_name": managed,
            "original_name": source.relative_name,
            "fingerprint": source.fingerprint,
        }
        raw_path = args.get("path")
        if raw_path:
            _target, error = validate_approved_path(
                str(raw_path),
                workspace=self.workspace,
                expected_relative=managed,
            )
            if error:
                return AttemptRecord(
                    "inspect_approved_source",
                    args,
                    "denied",
                    error,
                    False,
                    source_binding=binding,
                )
        staged = Path(self.workspace) / managed
        if staged.exists():
            try:
                if staged.is_symlink():
                    return AttemptRecord(
                        "inspect_approved_source",
                        args,
                        "denied",
                        "symlink_escape",
                        False,
                        source_binding=binding,
                    )
                observed = text_fingerprint(staged.read_text(encoding="utf-8"))
            except OSError:
                return AttemptRecord(
                    "inspect_approved_source",
                    args,
                    "denied",
                    "path_stat_failure",
                    False,
                    source_binding=binding,
                )
            if observed != source.fingerprint:
                return AttemptRecord(
                    "inspect_approved_source",
                    args,
                    "denied",
                    "staged_input_changed",
                    False,
                    source_binding={**binding, "staged_fingerprint": observed},
                )
        return AttemptRecord(
            "inspect_approved_source",
            args,
            "allowed",
            "approved_source_inspect",
            False,
            source_binding=binding,
        )

    def _cites_source_instruction(self, args: Mapping[str, Any]) -> bool:
        if args.get("follow_source_instructions") or args.get("apply_source_policy"):
            return True
        cited = str(args.get("source_id") or "")
        source = self._by_id.get(cited)
        if source and source_contains_instructions(source.text):
            if str(args.get("treat_as") or "") in {"policy", "instruction", "command"}:
                return True
        return False
