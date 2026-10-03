# Step 10.9.2 — Relocate data contracts and ingestion responsibilities — provenance persistence verification

AUTOCYCLE_PLAN: {"evidence_routes": [{"commands": [["rg", "-n", "normalization_candidate|reconciliation_provenance_payload|provenance.json", "core", "modeler", "director", "extractor"], ["/opt/anaconda3/bin/python", "-m", "pytest", "-q", "core/tests/test_normalization_candidate_admission.py"], ["/opt/anaconda3/bin/python", "-m", "pytest", "-q", "core/tests/test_data_ingestion_ownership.py", "core/tests/test_normalization.py", "core/tests/test_filing_json.py"]], "fact": "Whether observation fingerprints, source hashes, physical/printed locators, row identities and sign transformation remain recoverable through the applicable admission persistence/reload boundary under current canonical dependencies."}], "finding_key": "Relocate data contracts and ingestion responsibilities", "kind": "work", "minor": 2, "objective": "Relocate data contracts and ingestion responsibilities — provenance persistence verification", "plan_id": "6370c3e59e864abfa2257793d076b489", "predecessor_review_sha256": "d9df190fdab715f115dbbcfb8abe7aed69d58501b1e819c3ce052c1f07190bce", "step_id": "10.9.2", "work_id": "59ab4fdc9ec144ffb2c2b3f0bb8adaeb"}

## Completion

The data contracts, admission/reconciliation implementations and ingestion orchestration listed below execute from their canonical Modeler and Director owners, with runtime callers using those owners and existing compatibility imports, source provenance, analytical behavior and public `bav` interfaces preserved.

## Bounded work

Verify normalization-candidate provenance through its actual persistence/reload boundary against authenticated B. Reuse the completed reproducible fixtures and admission comparisons.

- Resolve B from populated `IMPLEMENT_BASE_SHA`, otherwise normal baseline and attempt/checkpoint records; authenticate branch, ancestry and binding, failing closed if unavailable. The reviewed checkpoint is `1a82323aac1309141f480e550277ffb2f56b35ca`, whose authenticated implementation baseline is `250d57178d4b32b3b12a13ba9a08677789d59183`. Retain `eb65dc63845b940162c48e39ae9af7598d2a3078` only as the separately bound pre-relocation comparator for checkpoint `38f5774170c577aa10eb5f03c4cbe99ed7cff789`.
- Inspect B Git blobs, current canonical implementations and admission callers to identify the applicable persisted provenance artifact, writer, reader and linkage to admitted financial identity. Establish whether documentary reconciliation provenance actually covers this opt-in admission path.
- Extend `core/tests/test_normalization_candidate_admission.py` and its isolated driver or directly necessary test helpers to exercise that existing contract. Persist to temporary storage, reload independently and assert against recovered data, without retaining original result objects as provenance evidence.
- Verify recovered observation fingerprints, source hashes, physical/printed locators, row identities and sign transformation against independently specified source-derived expectations. Preserve explicit unresolved printed-page states; do not invent locators.
- Establish that recovered provenance belongs to the reloaded analytical line and fiscal periods, with reported face values retained and sign conversion applied exactly once. Preserve financial identity/value round-trip checks.
- Run the same persistence cases against authenticated B and current dependencies in isolated processes; retain the pre-relocation comparison. Keep historical production code unchanged, allowing only necessary test import/path adaptations.
- If no applicable production persistence/reload contract exists, or required fields cannot be recovered, record the concrete missing path or field and B/current behavior with a minimal executable reproduction. Equal omissions do not establish preservation; distinguish an existing contract limitation from a migration regression.
- Do not substitute test-only serialization of `result.periods` for a production contract, reconstruct expected provenance from original observations after reload, or add provenance to the model-only standardized serializer.
- Limit changes to tests, directly necessary fixtures/helpers and appended `RESULT.md` evidence. Document production mismatches for Review without production repairs or architectural expansion.

## Verification

Whether observation fingerprints, source hashes, physical/printed locators, row identities and sign transformation remain recoverable through the applicable admission persistence/reload boundary under current canonical dependencies.

Criterion: IMPLEMENTATION.md explicitly requires provenance to survive round-trip, and the parent Completion preserves source provenance and analytical behavior.

- Execute the finite inspection and test routes above. Preserve all 23 existing candidate cases and the related regression checks; do not skip, deselect, xfail or weaken them.
- Preserve admission/rejection gates, independent analytical expectations, input immutability, repeated-admission rejection, default-off behavior, synthetic authorization distinctions and unresolved after-tax treatment.
- Run `git diff --check`. Append exact commands, measured results, persistence entry points, recovered field comparisons, baseline bindings and remaining limitations to `RESULT.md`; do not rewrite historical records.
- Keep the separate enrichment-sidecar failure visible. Reuse prior relocation/build/publication evidence only while its dependencies remain applicable; do not claim broader-suite or Session completion.

## Preserved relocation and constraints

Completed Modeler data ownership covers `interface`, `validators`, `standardized_io`, `line_identity`, `issuer_fiscal`, `historical_operating_kpis` and `historical_segments`; Director retains `data/schema`. Documentary types and historical-strategy contracts remain in Extractor.

Completed Modeler ingestion ownership covers `base`, `reconciler`, `filing_reconciler`, `filing_standardizer`, `management_kpi`, `management_kpi_identity`, `management_kpi_reconciliation`, `management_kpi_history`, `operating_kpi`, `geographic_segment`, `share_basis` and KPI validator admission. Director owns `filing_cli`, `note_handoff` and combined validation; Extractor retains documentary binding. Preserve issue ordering, façades, private exports, object identity and inventory mappings.

Preserve signatures, public commands, aliases, lazy loading, optional Trainer independence, dormant forecasting, accounting signs, fiscal distinctions, precision, reconciliations, source/transformation provenance, residual qualifications and admission/comparison independence. Do not rewrite canonical source or extracted/reconciled inputs.

Preserve completed Driver handoffs, first-name-wins assessments, CFO classification, attribution amounts/locators, counterfactual scope, `supported_as_attribution`, `not independently verified` and `outside the accounting bridge`. Attribution appendices remain independent of principal selection; margin prose requires independently selected margin evidence.

Classification/normalization interpretation splits, normalization-candidate separation, enrichment/Legacy decomposition, remaining orchestration relocation, unrelated removals, test ownership migration and final repository-wide verification remain subsequent scope. Do not repair the enrichment-sidecar defect, redesign algorithms/reports, expand Trainer or implement second-phase features.

Preserve ownership/recovery safeguards, protected documents, unrelated dirty work and zero-byte research placeholders. SESSION native verification remains binding if formulas/dependencies or presentation change, through Office Bridge. Cursor must not modify TARGET.md, SESSION.md or IMPLEMENTATION.md.
