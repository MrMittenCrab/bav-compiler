# Step 12.1.7 — Unify provider event validation and failure accounting

## Completion

The replacement Debater specification is recorded, and a reproducible benchmark prerequisite record establishes the available company sources, conversion behavior and controlled runtime capabilities, distinguishing verified routes from exact missing dependencies or human decisions without claiming end-to-end Debater acceptance.

AUTOCYCLE_PLAN: {"finding_key": "Verify Debater benchmark sources and controlled runtime", "kind": "work", "minor": 7, "objective": "Unify provider event validation and failure accounting", "plan_id": "ced63d1a4b0748b4a1d008f4dc5aa71f", "predecessor_review_sha256": "419b1d41497570b1b5d41a8625fefc5734aad73dc80f38d0fff89a2b100ca5d2", "step_id": "12.1.7", "work_id": "e35d5703ccc14627a150a29b9e900502"}

## Bounded work

Continue work `e35d5703ccc14627a150a29b9e900502` with a bounded repair of the reviewed single-object bypass and malformed-discriminator crash.

- Authenticate baseline, branch, ancestry and attempt binding through normal controller records before edits. Preserve unfinished work and ownership/recovery safeguards.
- In `bav/director/runtime/adapter.py` and `policy.py`, apply shared provider-event validation to both single-object responses and every stream event before accepting output or dispatching operations.
- Reject single-object `type=error` or `subtype=error` envelopes even when they contain valid-looking `output.kind` and operation requests.
- Validate present `type` and `subtype` values before membership tests or result selection. Reject non-string values with a stable validation failure; do not stringify, ignore or allow them to raise `TypeError`. Preserve valid envelopes that omit optional discriminators.
- Retain existing protocol and applicable output-envelope error indicators, unsuccessful-exit handling, missing-result checks and malformed/truncated/non-object rejection. Inspect control envelopes without interpreting quoted evidence as provider instructions or error signals.
- Complete all event validation before dispatch. Failures return no accepted structured result and pass through normal sanitized, call-bound capture and cumulative failure accounting without automatic retry.
- Preserve valid single-object and stream responses, typed operations, separate Planner/Reviewer contexts, bounded capture, allowance restoration and installed-launch closure. Keep the existing adapter contract.

## Verification

Extend `bav/director/tests/fixtures/runtime/fake_provider.py` and `bav/director/tests/test_research_runtime.py`.

- Reproduce both reviewed defects through actual `ResearchRuntime.invoke` subprocess paths before repairing them.
- Cover single-object `type=error` and `subtype=error` with success-shaped output and otherwise valid approved operation requests at exit zero.
- Cover list, object, number, boolean and null discriminator values for both fields in single objects and stream events. Include malformed events before and after a valid result.
- Assert no uncaught exception, no accepted result, zero dispatches, one attempted call, one recorded backend failure, sanitized diagnostics bound to the call and no retry. Verify checkpoint/restoration retains consumed allowance after rejection.
- Retain whole-stream error-order, error-indicator, malformed-record and non-object regressions. Exercise valid single-object and stream controls for both Planner and Reviewer, including omitted optional discriminators and quoted error wording.
- Run `/opt/anaconda3/bin/python -m pytest -q bav/director/tests/test_research_runtime.py`.
- Run affected Director regressions under `bav/director/tests/`: `test_current_build.py::test_public_namespace_and_compatibility`, `test_current_build.py::test_public_help_is_bav_first_and_check_is_diagnostic`, `test_readme.py`, and `test_research_handoff.py::test_modeler_import_boundary_excludes_downstream_owners`.

## Constraints and remaining obligations

BAV owns research configuration, contexts, permissions, state, budgets, capture and lifecycle. Preserve the full handbook and incorporated architecture clarification in `bav/director/docs/DEBATER.md`; AutoCycle remains implementation infrastructure without a product-runtime dependency or control changes.

Installed launches remain closed. Caller verification flags, synthetic evidence, backend/model changes and company-context declarations cannot authorize them. Preserve Cursor preference and the separately selectable Codex obligation; Codex remains unimplemented.

No live provider calls, company transmission, Controller probe/authentication/ACP replay, credential-store access, global configuration changes, installations, upgrades, new billing or relaxed permissions. Historical Controller observations neither establish current enforcement nor block this target-owned repair.

Preserve completed source discovery/conversion, originals/assets, provenance and coverage limits. Fast Retailing publication date remains unknown and distinct from financial-statement approval. Preserve financial inputs, neutral assumptions, company commands and six-component ownership.

Controlled installed-runtime acceptance remains required through a later bounded authorized BAV demonstration. Extractor readers/preparation/retrieval, ordinary debate CLI and approvals, Planner/Reviewer research, durable cases, coherent JSON/Markdown exports, semantic checks and real evidence-addition/resumption remain outstanding Endpoint obligations.

## Evidence

Update `bav/director/docs/BENCHMARK.md` with measured validation coverage and exact remaining runtime limitations. Record changes, commands and measured outcomes in `RESULT.md`, preserving historical records. Synthetic checks do not establish installed enforcement, parent Completion or Session acceptance.

Cursor must not modify `TARGET.md`, `SESSION.md` or `IMPLEMENTATION.md`. Do not repeat source preparation, workbook builds, Office verification or full certification for this repair.
