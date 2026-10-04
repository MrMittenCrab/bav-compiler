# Step 12.1.6 — Repair whole-stream provider error validation

## Completion

The replacement Debater specification is recorded, and a reproducible benchmark prerequisite record establishes the available company sources, conversion behavior and controlled runtime capabilities, distinguishing verified routes from exact missing dependencies or human decisions without claiming end-to-end Debater acceptance.

AUTOCYCLE_PLAN: {"finding_key": "Verify Debater benchmark sources and controlled runtime", "kind": "work", "minor": 6, "objective": "Repair whole-stream provider error validation", "plan_id": "820c80ac158942a1af12093f5d0daf9a", "predecessor_review_sha256": "6148b55b7910414c539be46c4beb6e7b6b338b0a4963041d881db31b154f4ef4", "step_id": "12.1.6", "work_id": "e35d5703ccc14627a150a29b9e900502"}

## Bounded work

Continue work `e35d5703ccc14627a150a29b9e900502`. Repair stream validation in `bav/director/runtime/adapter.py`, sharing error-indicator handling with `policy.py` where appropriate. Preserve the checkpoint's bounded capture, cumulative accounting, allowance restoration and installed-launch closure.

- Authenticate the implementation baseline, branch, ancestry and attempt binding through normal controller records before edits. Preserve unfinished work and ownership/recovery safeguards.
- Validate every provider event before selecting or accepting a final result. An error anywhere in the stream must defeat a success-shaped result, regardless of event order or process exit zero.
- Recognize provider error events and existing envelope failure indicators consistently. Inspect protocol envelopes and applicable output envelopes; quoted source content is not a provider control signal.
- Reject malformed, truncated and non-object stream records rather than silently dropping them. Preserve missing-result and unsuccessful-exit handling.
- Complete whole-stream validation before any application dispatch. Return no structured research result on failure; retain sanitized, call-bound diagnostics, failure accounting and no automatic retry.
- Preserve valid single-object and successful stream responses, approved typed dispatch and separate Planner/Reviewer contexts. Keep changes within the existing adapter contract.

## Regression coverage

Extend `bav/director/tests/fixtures/runtime/fake_provider.py` and `bav/director/tests/test_research_runtime.py` through actual `ResearchRuntime.invoke` subprocess, parsing, validation and dispatch paths.

- Reproduce an error event followed by a success-shaped result at exit zero; demonstrate failure before the repair.
- Cover errors before and after the result, an earlier error-bearing result followed by success, and separate events carrying existing failure indicators.
- Include otherwise valid operation requests in rejected streams. Assert zero dispatches, no accepted result, a sanitized call-bound failure, consumed call/failure allowance and no retry.
- Cover malformed/truncated records and non-object records alongside a valid result.
- Include successful stream and single-object controls with approved dispatch; exercise both Planner and Reviewer roles.
- Run `/opt/anaconda3/bin/python -m pytest -q bav/director/tests/test_research_runtime.py`.
- Run affected Director regressions: `test_current_build.py::test_public_namespace_and_compatibility`, `test_current_build.py::test_public_help_is_bav_first_and_check_is_diagnostic`, `test_readme.py`, and `test_research_handoff.py::test_modeler_import_boundary_excludes_downstream_owners`, all under `bav/director/tests/`.

## Constraints and remaining obligations

BAV owns research configuration, contexts, permissions, state, budgets, capture and lifecycle. Preserve the incorporated architecture clarification and full handbook in `bav/director/docs/DEBATER.md`. AutoCycle remains implementation infrastructure, with no product-runtime dependency or changes to its controls.

Installed launches remain closed. Caller verification flags, synthetic evidence, backend/model changes or company-context declarations cannot authorize them. Preserve Cursor preference and the separately selectable Codex obligation; Codex remains unimplemented.

No live provider calls, company transmission, Controller probe/authentication/ACP replay, credential-store access, global configuration changes, installations, upgrades, new billing or relaxed permissions. Historical Controller observations neither prove current enforcement nor prevent this BAV-owned repair.

Preserve completed source discovery/conversion, originals/assets, provenance and coverage limits. Fast Retailing publication date remains unknown and distinct from financial-statement approval. Preserve financial inputs, neutral assumptions, company commands and six-component ownership.

Controlled installed-runtime acceptance remains required through a later bounded authorized BAV demonstration. Extractor readers/preparation/retrieval, ordinary debate CLI and approvals, Planner/Reviewer research, durable cases, coherent JSON/Markdown exports, semantic checks and real evidence-addition/resumption remain outstanding Endpoint obligations.

## Evidence

Update `bav/director/docs/BENCHMARK.md` with measured whole-stream coverage and exact remaining runtime limitations. Record changes, commands and measured outcomes in `RESULT.md`, preserving historical records. Synthetic checks do not establish installed enforcement, parent Completion or Session acceptance.

Cursor must not modify `TARGET.md`, `SESSION.md` or `IMPLEMENTATION.md`. Do not repeat source preparation, workbook builds, Office verification or full certification for this repair.
