# Step 12.1.13 — Make capture descriptor acquisition exception-safe

## Completion

The replacement Debater specification is recorded, and a reproducible benchmark prerequisite record establishes the available company sources, conversion behavior and controlled runtime capabilities, distinguishing verified routes from exact missing dependencies or human decisions without claiming end-to-end Debater acceptance.

AUTOCYCLE_PLAN: {"finding_key": "Verify Debater benchmark sources and controlled runtime", "kind": "work", "minor": 13, "objective": "Make capture descriptor acquisition exception-safe", "plan_id": "dc71182b35f74e3099f003a2358c5714", "predecessor_review_sha256": "30a643f88738b732bda71cd686f2f5b2fb8ca1e439045b439d27c76673348352", "step_id": "12.1.13", "work_id": "e35d5703ccc14627a150a29b9e900502"}

## Bounded work

Continue work `e35d5703ccc14627a150a29b9e900502`. Repair interruption cleanup in `bav/director/runtime/policy.py`, preserving descriptor-relative ancestor traversal and post-read metadata validation.

- Authenticate the implementation baseline, branch, ancestry and checkpoint binding through normal controller records before editing. Preserve unfinished work and recovery safeguards.
- Make `_open_trust_anchor` and `_open_owned_directory` close newly opened descriptors whenever validation raises, including `KeyboardInterrupt` and other `BaseException` subclasses. Transfer ownership only on successful return; preserve the original exception.
- Repair validation-before-registration gaps in `_walk_names_from_anchor`, including ordinary components and system-prefix components. Every acquired descriptor must have cleanup ownership before subsequent identity validation or other fallible work.
- Keep ownership explicit through successful root/parent handoff and probe acquisition. Do not mark acquisition successful before the returned acquisition object is safely constructed. Avoid leaked descriptors, duplicate closes and closing caller-owned handles.
- Ensure `_probe_identity_mismatch` and `_probe_walk_replaced` release temporary descriptors when acquisition or later validation is interrupted, while surrounding capture cleanup releases retained descriptors and scanners.
- Preserve existing ordinary-error behavior and interruption propagation. An interrupted capture must not become successful or complete evidence. Make lifecycle changes outside `policy.py` only if necessary for this cleanup contract.

## Verification

Extend `bav/director/tests/test_research_runtime.py` with deterministic synthetic tests that expose the current leak before repair.

- Inject `KeyboardInterrupt` into `_fd_identity` after trust-anchor open and before ownership transfer.
- Independently interrupt component validation inside `_open_owned_directory` and subsequent walk validation before registration. Cover intermediate, final-root and supported system-prefix acquisition, including cleanup of previously acquired ancestors.
- Interrupt both direct identity probing and ancestor re-walk probing, during acquisition and after successful acquisition. Verify temporary probes close and caller-owned descriptors survive until their designated cleanup.
- Instrument actual successful opens, closes and scanners. Assert every invocation-owned resource is released exactly once after unwinding, no unrelated descriptor is closed, and the original interruption propagates. Test cleanup must release any leaked test resources without hiding the failed assertion.
- Retain a successful nested-directory control and ordinary validation-failure controls. Clock exhaustion remains separate coverage and cannot substitute for exception interruption.
- Retain ancestor/root/queued-child substitution tests, outside-target access instrumentation, bounded capture accounting, failed post-read metadata checks, incomplete mutation comparison and adapter evidence preservation.
- Retain launch-binding, inventory, executable identity, environment, source-collision, instruction-named evidence, typed dispatch, cumulative allowance, checkpoint and whole-response validation checks. Synthetic success and forged verification must launch no installed provider or stage company context.
- Run `/opt/anaconda3/bin/python -m pytest -q bav/director/tests/test_research_runtime.py`.
- Run `/opt/anaconda3/bin/python -m pytest -q bav/director/tests/test_current_build.py::test_public_namespace_and_compatibility bav/director/tests/test_current_build.py::test_public_help_is_bav_first_and_check_is_diagnostic bav/director/tests/test_readme.py bav/director/tests/test_research_handoff.py::test_modeler_import_boundary_excludes_downstream_owners`.

## Preservation and remaining scope

Preserve descriptor-bound traversal, no unsafe pathname fallback, explicit incomplete coverage, finite capture limits, bounded diagnostics, sanitized call-bound evidence before cleanup and qualified mutation comparisons. Keep application prevention, provider reports and observed mutations separately attributed.

Keep installed launches closed, approved launch bindings, isolated workspace/HOME/configuration/data paths, backend/model/role bindings, separate Planner/Reviewer contexts, finite child cleanup and no automatic retry.

No live provider calls, company transmission, Controller probes, authentication/ACP replay, credential-store access, global configuration changes, installations, upgrades, new billing, relaxed permissions, new sandbox platform or AutoCycle modifications.

Preserve `DEBATER.md`, completed source discovery/conversion, originals, assets, provenance and coverage limitations. Fast Retailing publication date remains unknown and distinct from financial-statement approval. Preserve company commands, accepted financial inputs, neutral assumptions and six-component ownership. Do not repeat source preparation, workbook builds, Office verification or full certification.

Controlled installed-runtime acceptance, loaded-configuration binding, native-tool enforcement and Codex integration remain outstanding. A later bounded authorized BAV demonstration must establish effective restrictions before company transmission. Required Extractor readers/preparation/retrieval, ordinary debate CLI and approvals, Planner/Reviewer research, durable cases, coherent JSON/Markdown exports, semantic checks and the real two-company benchmark with evidence addition/resumption remain unfinished.

## Evidence

Update `bav/director/docs/BENCHMARK.md` to distinguish actual exception-interruption coverage from prior clock-exhaustion coverage and record measured cleanup guarantees and limitations.

Append measured commands and outcomes to `RESULT.md`; qualify the previous interruption claim without rewriting historical records. Synthetic cleanup success does not establish provider enforcement, parent Completion or Session acceptance.

Cursor must not modify `TARGET.md`, `SESSION.md` or `IMPLEMENTATION.md`.
