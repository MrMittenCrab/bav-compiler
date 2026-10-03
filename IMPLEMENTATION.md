# Step 10.9.4 — Finish lifecycle-aware baseline authentication regression coverage
AUTOCYCLE_PLAN: {"finding_key": "Relocate data contracts and ingestion responsibilities", "kind": "work", "objective": "Finish lifecycle-aware baseline authentication regression coverage", "plan_id": "3c98231171454b838b1fb791241dc6a1", "predecessor_review_sha256": "4f9ef1735102065b4d6f299aa2060b15b5accd53b9936a45e8bf0cb5b1597850", "step_id": "10.9.4", "work_id": "59ab4fdc9ec144ffb2c2b3f0bb8adaeb"}

## Completion

The data contracts, admission/reconciliation implementations and ingestion orchestration listed below execute from their canonical Modeler and Director owners, with runtime callers using those owners and existing compatibility imports, source provenance, analytical behavior and public `bav` interfaces preserved.

## Bounded work

Finish the current authentication repair in `core/tests/test_normalization_candidate_admission.py`: correct lifecycle-dependent live assertions and copied controller fixtures so the regression succeeds during implementation and at the exact authenticated checkpoint. Preserve the completed authentication and production-loader repairs.

- Replace the live implementation-only assertion and its dependent HEAD/checkpoint assertions with strict assertions for the authenticated lifecycle. Implementation requires HEAD equal to B and the matching running attempt; checkpoint requires HEAD equal to that same attempt’s recorded checkpoint, with matching baseline, branch and Git parent/ancestry bindings. Merely accepting either state string is insufficient.
- Derive isolated implementation and checkpoint fixtures from existing controller record shapes. Set each fixture’s plan, allocation, work, attempt, phase, baseline, checkpoint and Git state consistently; do not inherit whichever lifecycle happens to be live.
- Repair every copied fixture that searches for a running attempt or changes only `git_head`. Select the bound attempt by identity and construct the intended lifecycle explicitly inside isolated records.
- Exercise `_authenticate_current_repository_baseline` through its record-reading and caller path for both valid states. Keep helper coverage; it does not replace caller-path coverage.
- Start negative cases from valid isolated fixtures, mutate observed ownership independently of expected ownership, and retain specific rejection assertions. Do not let an unrelated malformed lifecycle satisfy a rejection test.
- Resolve B from populated `IMPLEMENT_BASE_SHA` in `.git/autocycle/resume-state`; otherwise use authenticated implementation-baseline, bound attempt and latest-implementation records. Fail closed when required evidence is missing or inconsistent.
- Require nonempty matching work and attempt identities, plan/baseline bindings and branch ownership even at `HEAD == B`. Preserve exact recorded-checkpoint authorization; never restore direct-child or stale-review authorization.
- Read controller evidence only. Fixture changes must remain isolated; do not edit `.git/autocycle`, substitute HEAD as B, fabricate live bindings or introduce recovery infrastructure. Keep historical comparator tuples separate from live authorization.

## Verification

- Cover missing expected and observed work/attempt identities, mismatched identities, baseline/checkpoint bindings and branches in both lifecycle fixtures where applicable.
- Retain rejection of an unrecorded direct child, a child with a checkpoint belonging to an old B, and a different child of the correct B when an exact checkpoint is recorded.
- Verify the live caller against actual controller bindings. Demonstrate both lifecycle paths with deterministic fixtures regardless of the live phase; label fixture evidence separately from live execution.
- Retain isolated current-versus-B execution using historical Git blobs and analytical/admission-gate assertions, including separately bound pre-relocation comparator `eb65dc63845b940162c48e39ae9af7598d2a3078`. Allow only intended validation/persistence differences.
- Preserve fresh-process production-loader rejection of reassigned or missing periods, false transformation metadata, provisional adoption, empty treatment, synthetic real-company acceptance and altered source hashes.
- Retain synthetic and independently authorized round trips with all 11 observations’ original periods, hashes, rows, locators, face amounts, exact transformation and analytical values; preserve input immutability and repeated-admission rejection.
- Run `/opt/anaconda3/bin/python -m pytest -q core/tests/test_normalization_candidate_admission.py`.
- Run `/opt/anaconda3/bin/python -m pytest -q core/tests/test_data_ingestion_ownership.py core/tests/test_normalization.py core/tests/test_filing_json.py` and `git diff --check`. Do not skip, deselect, xfail or weaken gates.
- Append measured results, actual binding sources, lifecycle coverage and rejection evidence to `RESULT.md`. Preserve historical records. Earlier pre-checkpoint passes do not establish checkpoint-state success; distinguish this repair from parent Completion and Session acceptance.

## Preserved behavior and remaining scope

Preserve fingerprint recomputation and source file/hash, row, period, amount, currency, scale and locator bindings; adopted-status, required-decision, contradiction, membership, analytical identity/scope, treatment/configuration, tax and authorization gates. Preserve exact negative-face transformation, face/analytical agreement and once-only conversion.

Preserve independent authorization’s grouping qualifications, unresolved after-tax treatment, unresolved/unavailable locators and ambiguous-linkage rejection. Never infer printed pages from physical pages or sum overlapping comparative observations. Keep admission default-off, reject blocked/provisional persistence, and retain the separate admission artifact, model-only standardized serialization, standardized-only loading and omission diagnostic.

Preserve completed Modeler data ownership of `interface`, `validators`, `standardized_io`, `line_identity`, `issuer_fiscal`, `historical_operating_kpis` and `historical_segments`; Director retains `data/schema`. Documentary types and historical-strategy contracts remain in Extractor.

Preserve completed Modeler ingestion ownership of `base`, `reconciler`, `filing_reconciler`, `filing_standardizer`, `management_kpi`, `management_kpi_identity`, `management_kpi_reconciliation`, `management_kpi_history`, `operating_kpi`, `geographic_segment`, `share_basis` and KPI validator admission. Director owns `filing_cli`, `note_handoff` and combined validation; Extractor retains documentary binding. Preserve issue ordering, façades, private exports, object identity and inventory mappings.

Preserve public `bav` commands, aliases, lazy loading, optional Trainer independence, dormant forecasting, accounting signs, fiscal distinctions, precision, reconciliations, provenance, residual qualifications and admission/comparison independence. Do not rewrite canonical source or extracted/reconciled inputs.

Preserve completed Driver handoffs, first-name-wins assessments, CFO classification, attribution amounts/locators, counterfactual scope, `supported_as_attribution`, `not independently verified` and `outside the accounting bridge`. Attribution appendices remain independent of principal selection; margin prose requires independently selected margin evidence.

Classification/normalization interpretation splits, broader normalization-candidate separation, enrichment/Legacy decomposition, remaining orchestration relocation, unrelated removals, test ownership migration and final repository-wide verification remain subsequent scope. Keep the separate enrichment-sidecar defect visible. Do not add CLI expansion, a general provenance framework, algorithm/report redesign, Trainer expansion or second-phase features.

Preserve ownership/recovery, provider retry, human adoption, interruption, candidate validation, protected-document, unrelated-dirty-work and Review-cache safeguards and zero-byte research placeholders. Reuse verification only while dependencies remain applicable. SESSION native verification remains binding for changed formulas/dependencies or presentation, through Office Bridge. Cursor must not modify TARGET.md, SESSION.md or IMPLEMENTATION.md.
