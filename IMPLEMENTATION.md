# Step 12.1.10 — Repair bounded mutation capture and scan-error coverage

## Completion

The replacement Debater specification is recorded, and a reproducible benchmark prerequisite record establishes the available company sources, conversion behavior and controlled runtime capabilities, distinguishing verified routes from exact missing dependencies or human decisions without claiming end-to-end Debater acceptance.

AUTOCYCLE_PLAN: {"finding_key": "Verify Debater benchmark sources and controlled runtime", "kind": "work", "minor": 10, "objective": "Repair bounded mutation capture and scan-error coverage", "plan_id": "ab220dd4518348aab02838e6e7e903f5", "predecessor_review_sha256": "cc8a173d00ba02e7e5efb60bb2e07aa8324f477ae23556659d14318e608ccc54", "step_id": "12.1.10", "work_id": "e35d5703ccc14627a150a29b9e900502"}

## Bounded work

Continue work `e35d5703ccc14627a150a29b9e900502`. Repair capture in `bav/director/runtime/policy.py` and its existing adapter integration. Keep installed launches closed.

- Authenticate the implementation baseline, branch, ancestry and checkpoint ownership through normal controller records before edits. Preserve unfinished work and recovery safeguards.
- Replace whole-file `read_bytes()` in `_observe_owned_entry` with incremental reads bounded before each read by the remaining byte allowance and a finite chunk size. Check elapsed allowance between chunks. Bound bytes actually read, not merely bytes hashed or retained.
- Distinguish full-content fingerprints from partial observations. Record truncation, read failures and detected instability explicitly; partial fingerprints cannot establish complete content identity. Handle empty files and exact-boundary files without an unbudgeted lookahead read.
- Replace eager directory enumeration with bounded incremental traversal. Check entry, depth, elapsed and retained-output limits during enumeration, including directories and symlinks. Stop globally when the applicable allowance is exhausted; do not accumulate an unbounded directory queue or diagnostic list.
- Record directory-open and directory-iteration failures, including failures after some entries were returned. Missing, unreadable, omitted or unstable coverage must set `complete=false` and `unchanged_not_established=true`, with bounded safe root-relative diagnostics.
- Record directory and file-type observations needed to detect additions, removals and type changes. Do not follow symlink targets or read special files; prevent entry replacement between classification and opening from bypassing those restrictions.
- Preserve the existing capture contract where practical. Update `bav/director/runtime/contract.py` only if needed to express a finite traversal allowance.
- In `bav/director/runtime/adapter.py`, propagate incomplete before/after coverage through retained capture. Unobserved entries must not become definitive additions/removals or an unchanged-filesystem conclusion. Preserve observed changes with their coverage qualification.
- Retain sanitized, call-bound evidence before cleanup on success, denial, malformed output, timeout and interruption. Keep application prevention, provider reports and observed mutations separately attributed.

## Verification

Extend `bav/director/tests/test_research_runtime.py` and its existing synthetic provider fixture as needed.

- Reproduce the reviewed large-file defect with a 64-byte allowance and instrument actual read requests/returned bytes. Verify bounded memory/read behavior, shared byte accounting across files, empty/exact-boundary files, truncation and interrupted reads.
- Inject `PermissionError` at root and nested directory scans, plus a mid-iteration failure. Assert explicit incomplete coverage and no false unchanged conclusion, including when no records were obtained.
- Exercise wide directories containing only directories or symlinks, depth exhaustion, record exhaustion and a controlled clock expiring during enumeration or hashing. Measure consumed entries and read operations rather than relying only on returned record counts.
- Exercise symlink replacement, special files and detectable concurrent file changes without reading targets or blocking on special-file content.
- Verify adapter capture survives cleanup with incomplete before/after observations. Retain the unchanged synthetic control, existing overwrite/add/remove/type-change checks and launch-binding rejection tests.
- Retain snapshot-content, on-disk inventory, executable identity, environment, source-collision, instruction-named evidence, typed dispatch, cumulative allowance and checkpoint tests. Forged installed-verification flags or synthetic success must still launch no installed process and stage no company context.
- Run `/opt/anaconda3/bin/python -m pytest -q bav/director/tests/test_research_runtime.py`.
- Run `/opt/anaconda3/bin/python -m pytest -q bav/director/tests/test_current_build.py::test_public_namespace_and_compatibility bav/director/tests/test_current_build.py::test_public_help_is_bav_first_and_check_is_diagnostic bav/director/tests/test_readme.py bav/director/tests/test_research_handoff.py::test_modeler_import_boundary_excludes_downstream_owners`.

## Preservation and remaining scope

Preserve repaired full-content snapshot, disk-inventory and approved executable bindings; isolated workspace/HOME/configuration/data paths; backend/model/role bindings; separate Planner/Reviewer contexts; whole-response validation; finite child cleanup and no automatic retry.

No live provider calls, company transmission, Controller probe/authentication/ACP replay, credential-store access, global configuration changes, installations, upgrades, new billing, relaxed permissions, new sandbox platform or AutoCycle modifications. Historical Controller observations remain historical evidence, not prerequisites for this target-owned repair.

Preserve `DEBATER.md`, completed source discovery/conversion, original assets, provenance and coverage limitations. Fast Retailing publication date remains unknown and distinct from financial-statement approval. Preserve company commands, accepted financial inputs, neutral assumptions and six-component ownership. Do not repeat source preparation, workbook builds, Office verification or full certification.

Controlled installed-runtime acceptance and Codex integration remain outstanding. A later bounded authorized BAV demonstration must establish effective restrictions before company transmission. Extractor readers/preparation/retrieval, ordinary debate CLI and approvals, Planner/Reviewer research, durable cases, coherent JSON/Markdown exports, semantic checks and real evidence-addition/resumption remain required by the Session.

## Evidence

Update `bav/director/docs/BENCHMARK.md` to correct unsupported bounded/complete-capture claims and record measured repair behavior, coverage limits and remaining installed-acceptance mechanisms. Record commands and measured outcomes in `RESULT.md` without rewriting historical records. Synthetic tests do not establish provider enforcement, parent Completion or Session acceptance.

Cursor must not modify `TARGET.md`, `SESSION.md` or `IMPLEMENTATION.md`.
