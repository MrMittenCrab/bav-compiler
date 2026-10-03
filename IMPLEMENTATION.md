# Step 10.9.4 — Relocate data contracts and ingestion responsibilities — complete admission-bundle validation repair
AUTOCYCLE_PLAN: {"finding_key": "Relocate data contracts and ingestion responsibilities", "kind": "work", "objective": "Relocate data contracts and ingestion responsibilities — complete admission-bundle validation repair", "plan_id": "57858697f3f94db58c9e344d7023d3bf", "predecessor_review_sha256": "5a28efe5ad868d0bbbc969c18962c95774da118c25027e4c1414b8c072e0e93e", "step_id": "10.9.4", "work_id": "59ab4fdc9ec144ffb2c2b3f0bb8adaeb"}

## Completion

The data contracts, admission/reconciliation implementations and ingestion orchestration listed below execute from their canonical Modeler and Director owners, with runtime callers using those owners and existing compatibility imports, source provenance, analytical behavior and public `bav` interfaces preserved.

## Bounded work

Finish the current validation repair: reject recovered period reassignment and false transformation metadata, and make baseline authentication valid at an authenticated checkpoint.

- Limit changes to `modeler/ingestion/normalization_candidate_admission_io.py`, `core/tests/test_normalization_candidate_admission.py` and directly necessary admission evidence integration. Broader relocation remains subsequent.
- In `observation_evidence_from_payload`, require the persisted observation period to equal the period in its original, fingerprint-validated `fingerprint_inputs`. Derive the expected projection from those inputs, never from the supplied recovered period. Reject missing or inconsistent period evidence with `AdmissionProvenanceError`; do not silently fill or rewrite it.
- In `load_admitted_bundle`, require the exact transformation identity `analytical_amount = -reported_face_expense`. Preserve face/analytical value agreement and `sign_conversions_applied == 1`; reload must not reapply conversion.
- Preserve full-observation fingerprint recomputation and source file/hash, row, amount, currency, scale and locator bindings. Reject stale or insufficient evidence without fabricating provenance.
- Preserve adopted-status, required-decision, contradiction, membership, analytical identity/scope, treatment/configuration, tax and authorization gates. Synthetic authorization must not imply real-company acceptance; independent authorization must retain grouping qualifications.
- Preserve company/statement/line/period/value bindings, unresolved after-tax treatment, unresolved/unavailable locators and rejection of ambiguous linkage. Never infer printed pages from physical pages or sum overlapping comparative observations.
- Keep the dedicated admission artifact separate from model-only standardized serialization and documentary reconciliation provenance. Preserve standardized-only loading and its omission diagnostic, default-off admission and rejection of blocked/provisional persistence.

## Baseline comparison repair

- Resolve implementation B from populated `IMPLEMENT_BASE_SHA` in `.git/autocycle/resume-state`; otherwise use authenticated baseline, bound attempt and latest-implementation records. Authenticate branch, ancestry and implementation/checkpoint binding; fail closed if unavailable.
- Review binds checkpoint `06a7184194cd9cb462eebf262790e88d3808a92a` to direct parent `d260153bbda7014d7069c2247f80db75890f61f9`. Preserve this historical binding without treating it as every future implementation’s B.
- Replace the unconditional HEAD-equals-B assertion in `test_b_and_current_isolated_agreement` with authentication that supports both implementation at B and its recorded checkpoint. An ancestry check alone must not authorize an unrelated checkpoint or mismatched attempt.
- Retain isolated current-versus-B execution using historical Git blobs, analytical/admission-gate comparisons and separately bound historical comparators, including pre-relocation `eb65dc63845b940162c48e39ae9af7598d2a3078`. Allow only intended validation/persistence differences.
- Use existing controller evidence read-only; do not create recovery machinery, substitute HEAD as B, or edit controller records to make tests pass.

## Verification

- Add independent mutations of a valid production-saved bundle: move an observation from `2025-02-02` to `2026-02-01` without changing its fingerprint inputs, and change transformation to `analytical_amount = reported_face_expense`. Each must fail through the production loader, including fresh-process loading from persisted paths only.
- Include missing-period evidence rejection and retain all four repaired bypass regressions: provisional adoption, empty treatment, synthetic real-company acceptance and altered source hash. Preserve existing authorization, treatment/configuration, fingerprint, stale-evidence and linkage rejection cases.
- Exercise baseline authentication for valid implementation and checkpoint states and rejection of inconsistent branch/attempt/checkpoint evidence. Ensure the isolated comparison runs at a bound checkpoint without weakening its behavioral assertions.
- Verify successful fresh-process round trips for synthetic and independently supplied authorization using source-derived fixtures and independent expectations: all 11 observations retain their original period associations, hashes, rows, locators, face amounts, exact transformation and analytical values.
- Preserve input immutability, repeated-admission rejection, unresolved states and all existing candidate scenarios.
- Run `/opt/anaconda3/bin/python -m pytest -q core/tests/test_normalization_candidate_admission.py`.
- Run `/opt/anaconda3/bin/python -m pytest -q core/tests/test_data_ingestion_ownership.py core/tests/test_normalization.py core/tests/test_filing_json.py`, plus any separate focused repair tests. Do not skip, deselect, xfail or weaken existing gates.
- Run `git diff --check`. Append measured results, authenticated baseline/checkpoint bindings, rejection evidence and recovered linkage to `RESULT.md`; preserve historical records and distinguish bounded repair from parent Completion and Session acceptance.

## Preserved ownership and remaining scope

Preserve completed Modeler data ownership of `interface`, `validators`, `standardized_io`, `line_identity`, `issuer_fiscal`, `historical_operating_kpis` and `historical_segments`; Director retains `data/schema`. Documentary types and historical-strategy contracts remain in Extractor.

Preserve completed Modeler ingestion ownership of `base`, `reconciler`, `filing_reconciler`, `filing_standardizer`, `management_kpi`, `management_kpi_identity`, `management_kpi_reconciliation`, `management_kpi_history`, `operating_kpi`, `geographic_segment`, `share_basis` and KPI validator admission. Director owns `filing_cli`, `note_handoff` and combined validation; Extractor retains documentary binding. Preserve issue ordering, façades, private exports, object identity and inventory mappings.

Preserve public `bav` commands, aliases, lazy loading, optional Trainer independence, dormant forecasting, accounting signs, fiscal distinctions, precision, reconciliations, source/transformation provenance, residual qualifications and admission/comparison independence. Do not rewrite canonical source or extracted/reconciled inputs.

Preserve completed Driver handoffs, first-name-wins assessments, CFO classification, attribution amounts/locators, counterfactual scope, `supported_as_attribution`, `not independently verified` and `outside the accounting bridge`. Attribution appendices remain independent of principal selection; margin prose requires independently selected margin evidence.

Classification/normalization interpretation splits, broader normalization-candidate separation, enrichment/Legacy decomposition, remaining orchestration relocation, unrelated removals, test ownership migration and final repository-wide verification remain subsequent scope. Keep the separate enrichment-sidecar defect visible. Do not add CLI expansion, a general provenance framework, algorithm/report redesign, Trainer expansion or second-phase features.

Preserve ownership/recovery safeguards, protected documents, unrelated dirty work and zero-byte research placeholders. Reuse prior verification only while dependencies remain applicable. SESSION native verification remains binding if formulas/dependencies or presentation change, through Office Bridge. Cursor must not modify TARGET.md, SESSION.md or IMPLEMENTATION.md.
