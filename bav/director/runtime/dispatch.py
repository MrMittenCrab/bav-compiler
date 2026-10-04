"""Typed application dispatcher. Provider output cannot grant permissions."""

from __future__ import annotations

from typing import Any, Mapping

from bav.director.runtime.contract import ALLOWED_OPERATIONS, ApprovedSnapshot, AttemptRecord
from bav.director.runtime.policy import (
    classify_operation,
    source_contains_instructions,
    validate_approved_path,
)


class ApplicationDispatcher:
    def __init__(self, snapshot: ApprovedSnapshot, workspace) -> None:
        self.snapshot = snapshot
        self.workspace = workspace
        self._by_id = {source.source_id: source for source in snapshot.sources}
        self._approved_names = {source.relative_name for source in snapshot.sources}
        self._approved_names.update(source.source_id for source in snapshot.sources)
        self._dispatch_count = 0

    @property
    def dispatch_count(self) -> int:
        return self._dispatch_count

    def handle(self, operation: str, arguments: Mapping[str, Any]) -> AttemptRecord:
        kind = classify_operation(operation)
        args = dict(arguments or {})
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
            return self._inspect(args)
        return AttemptRecord(operation, args, "denied", "unknown_operation", False)

    def _inspect(self, args: Mapping[str, Any]) -> AttemptRecord:
        source_id = str(args.get("source_id") or "")
        source = self._by_id.get(source_id)
        if source is None:
            return AttemptRecord(
                "inspect_approved_source", args, "denied", "unapproved_source", False
            )
        raw_path = args.get("path")
        if raw_path:
            _target, error = validate_approved_path(
                str(raw_path),
                workspace=self.workspace,
                approved_names=self._approved_names,
            )
            if error:
                return AttemptRecord(
                    "inspect_approved_source", args, "denied", error, False
                )
        self._dispatch_count += 1
        return AttemptRecord(
            "inspect_approved_source",
            args,
            "allowed",
            "approved_source_inspect",
            True,
            {
                "source_id": source.source_id,
                "label": source.label,
                "fingerprint": source.fingerprint,
                "text": source.text,
                "origin": source.origin,
            },
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
