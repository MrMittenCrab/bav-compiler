# Step 10.9.3 — Relocate data contracts and ingestion responsibilities — admission provenance persistence repair

AUTOCYCLE_PLAN: {"finding_key": "Relocate data contracts and ingestion responsibilities", "kind": "work", "minor": 3, "objective": "Relocate data contracts and ingestion responsibilities — admission provenance persistence repair", "plan_id": "599e137086184011ae3ea0dbf34bb107", "predecessor_review_sha256": "bd8f4230127d31d892b312e675fe0d6f98e523293b5600c769812d3aacc0ef8b", "step_id": "10.9.3", "work_id": "59ab4fdc9ec144ffb2c2b3f0bb8adaeb"}

## Completion

The data contracts, admission/reconciliation implementations and ingestion orchestration listed below execute from their canonical Modeler and Director owners, with runtime callers using those owners and existing compatibility imports, source provenance, analytical behavior and public `bav` interfaces preserved.

## Bounded work

Implement a production persistence/reload boundary for explicitly admitted normalization candidates, retaining recoverable evidence linked to the persisted analytical line and fiscal periods.

- Resolve implementation B from populated `IMPLEMENT_BASE_SHA`, otherwise authenticated baseline and attempt/checkpoint records; authenticate branch, ancestry and binding, failing closed if unavailable. Reviewed checkpoint `7cf143f53036afcb981fb4118b830e73b4fa58b6` has authenticated parent B `95efb965cd896e462814459b843d9a992358c7a9`. Keep `eb65dc63845b940162c48e39ae9af7598d2a3078` as the separately bound pre-relocation comparator.
- Add a small Modeler-owned admission provenance writer/reader and the directly necessary handoff integration in `core/ingestion/normalization_candidate_admission.py`. Preserve existing signatures and compatibility behavior; defer broader admission decomposition.
- Persist admission evidence alongside standardized financials in a dedicated artifact. Keep `modeler/data/standardized_io.py` model-only and ordinary documentary reconciliation provenance unchanged.
- Capture evidence during construction/admission, before per-period aggregation loses observation associations. Retain each observation fingerprint with its source file/hash, row identity, physical page, printed-page value/status, period, reported amount, currency and scale.
- Preserve unresolved and unavailable locator states explicitly. Do not infer printed pages from physical pages or rebuild missing evidence from labels or analytical amounts.
- Bind the artifact to company, statement, canonical analytical line identity, fiscal periods and analytical values. Retain reported face amounts, transformation and exactly-once sign-conversion evidence without summing overlapping comparative observations.
- Persist the supplied adoption/treatment decisions and their authorization distinctions needed to interpret admission. Preserve provisional grouping qualifications, synthetic status, unresolved after-tax treatment and candidate configuration.
- Provide an explicit production save/load path using the existing standardized serializer plus the admission artifact. Loading must recover and validate the association without original observations or in-memory handoff objects, and must not reapply sign conversion.
- Reject missing, stale, inconsistent or ambiguously linked evidence when loading an admission bundle. Ordinary standardized-only loading remains supported without claiming recovered admission provenance. Blocked/provisional handoffs must not be persisted as admitted bundles.
- Limit production changes to this persistence contract and necessary evidence capture/integration, with focused tests and appended `RESULT.md` evidence. Do not add default admission activation, CLI expansion, a general provenance framework or unrelated repairs.

## Verification

- Reuse the completed source-derived fixtures, independently specified expectations and isolated driver. Exercise production save/load through temporary artifacts and a fresh process receiving only persisted paths.
- Assert recovered fingerprints, associated source hashes/rows/locators, unresolved locator states, face amounts and transformation evidence against independent expectations. Verify their linkage to the reloaded analytical identity and each fiscal period, unchanged values and exactly-once conversion.
- Cover mismatched company/line/period/value bindings, missing evidence and blocked admission; preserve input immutability and repeated-admission rejection after reload.
- Preserve all existing candidate scenarios. Retain the historical omission reproduction as diagnostic coverage; add positive assertions for the repaired production boundary. Update baseline/current comparisons only for the intentional persistence difference, retaining analytical and admission-gate parity.
- Compare authenticated B Git code with current behavior in isolated processes; retain the pre-relocation comparison without modifying historical production code. Equal historical omissions remain evidence of the original limitation, not successful preservation.
- Run `/opt/anaconda3/bin/python -m pytest -q core/tests/test_normalization_candidate_admission.py` and `/opt/anaconda3/bin/python -m pytest -q core/tests/test_data_ingestion_ownership.py core/tests/test_normalization.py core/tests/test_filing_json.py`, plus focused tests added for the repair. Do not skip, deselect, xfail or weaken existing gates.
- Run `git diff --check`. Append measured results, baseline bindings, production persistence entry points and recovered linkage evidence to `RESULT.md`; distinguish this repair from parent Completion and Session acceptance.

## Preserved relocation and constraints

Completed Modeler data ownership covers `interface`, `validators`, `standardized_io`, `line_identity`, `issuer_fiscal`, `historical_operating_kpis` and `historical_segments`; Director retains `data/schema`. Documentary types and historical-strategy contracts remain in Extractor.

Completed Modeler ingestion ownership covers `base`, `reconciler`, `filing_reconciler`, `filing_standardizer`, `management_kpi`, `management_kpi_identity`, `management_kpi_reconciliation`, `management_kpi_history`, `operating_kpi`, `geographic_segment`, `share_basis` and KPI validator admission. Director owns `filing_cli`, `note_handoff` and combined validation; Extractor retains documentary binding. Preserve issue ordering, façades, private exports, object identity and inventory mappings.

Preserve public commands, aliases, lazy loading, optional Trainer independence, dormant forecasting, accounting signs, fiscal distinctions, precision, reconciliations, source/transformation provenance, residual qualifications and admission/comparison independence. Do not rewrite canonical source or extracted/reconciled inputs.

Preserve completed Driver handoffs, first-name-wins assessments, CFO classification, attribution amounts/locators, counterfactual scope, `supported_as_attribution`, `not independently verified` and `outside the accounting bridge`. Attribution appendices remain independent of principal selection; margin prose requires independently selected margin evidence.

Classification/normalization interpretation splits, broader normalization-candidate separation, enrichment/Legacy decomposition, remaining orchestration relocation, unrelated removals, test ownership migration and final repository-wide verification remain subsequent scope. Keep the separate enrichment-sidecar defect visible without repairing it here. Do not redesign algorithms/reports, expand Trainer or implement second-phase features.

Preserve ownership/recovery safeguards, protected documents, unrelated dirty work and zero-byte research placeholders. Reuse prior verification only while dependencies remain applicable. SESSION native verification remains binding if formulas/dependencies or presentation change, through Office Bridge. Cursor must not modify TARGET.md, SESSION.md or IMPLEMENTATION.md.
