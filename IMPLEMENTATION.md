# Step 10.9.4 — Relocate data contracts and ingestion responsibilities — admission-bundle validation repair

AUTOCYCLE_PLAN: {"finding_key": "Relocate data contracts and ingestion responsibilities", "kind": "work", "minor": 4, "objective": "Relocate data contracts and ingestion responsibilities — admission-bundle validation repair", "plan_id": "87e752e51a824eb18dd099110324ab5b", "predecessor_review_sha256": "48a15c342f11dc47a4af3769fa3a28985569086e24196c70d8963025c0cec4af", "step_id": "10.9.4", "work_id": "59ab4fdc9ec144ffb2c2b3f0bb8adaeb"}

## Completion

The data contracts, admission/reconciliation implementations and ingestion orchestration listed below execute from their canonical Modeler and Director owners, with runtime callers using those owners and existing compatibility imports, source provenance, analytical behavior and public `bav` interfaces preserved.

## Bounded work

Repair admission-bundle validation so persisted evidence cannot bypass the existing adoption, treatment and authorization gates. Preserve successful production round trips.

- Resolve implementation B from populated `IMPLEMENT_BASE_SHA`, otherwise authenticated baseline and attempt/checkpoint records; authenticate branch, ancestry and binding, failing closed if unavailable. Review binds checkpoint `02d1f58e55a1823896f71e3090fd236d3448008c` to parent `a7e50356d5129066bad5a90ba8f54d801243f926`. Retain `eb65dc63845b940162c48e39ae9af7598d2a3078` as the separately bound pre-relocation comparator.
- Limit production changes to `modeler/ingestion/normalization_candidate_admission_io.py` and directly necessary admission evidence capture/integration. Keep broader admission relocation and decomposition subsequent.
- Validate recovered adoption against existing admission semantics: required decisions, adopted status, contradiction checks, company, fiscal axis, membership, analytical identity/scope and evidence fingerprints.
- Require complete, admissible treatment decisions. Validate candidate configuration, tax disposition and after-tax availability against those decisions without resolving supplied uncertainties.
- Validate authorization kinds and agreement between adoption and bundle metadata. Synthetic authorization must never imply real-company acceptance; preserve independent authorization and provisional grouping qualifications.
- Bind each persisted observation’s source file/hash, row, period, amount, currency, scale and locators to its adopted fingerprint. Existing fingerprints hash the full observation; persist sufficient original fingerprint inputs to recompute them and verify the stored evidence projection. Do not substitute a checksum of an unrelated subset or reconstruct missing inputs from analytical values.
- Reject missing, stale, inconsistent or ambiguously linked evidence with `AdmissionProvenanceError`. If the artifact schema changes, explicitly reject older evidence that cannot satisfy validation; do not fabricate missing provenance.
- Preserve company/statement/line/period/value bindings, reported face amounts, exact transformation identity and exactly-once sign conversion. Do not sum overlapping comparative observations or reapply conversion on reload.
- Preserve explicit unresolved/unavailable locator states; never infer printed pages from physical pages. Keep ordinary standardized-only loading supported without claiming recovered admission provenance.
- Keep the dedicated admission artifact and model-only standardized serializer separate. Preserve existing entry points, documentary reconciliation provenance and rejection of blocked/provisional handoffs before persistence.

## Verification

- Add independent mutations of a valid production-saved bundle for the four demonstrated bypasses: provisional `adoption.decision_status`, empty `treatment`, synthetic authorization with `real_company_acceptance=true`, and an altered observation `source_hash` with unchanged fingerprints. Each must fail through the production loader.
- Add focused cases for inconsistent adoption/bundle authorization, treatment/configuration disagreement and fingerprint/evidence disagreement. Preserve existing missing/stale evidence, ambiguous linkage and company/line/period/value rejection cases.
- Reuse source-derived fixtures and independent expectations. Verify successful save/load in a fresh process receiving only persisted paths, including admissible synthetic and independent authorization records without claiming actual company approval.
- Assert recovered observation associations, source hashes, rows, locators, unresolved states, face amounts, transformation and analytical values. Preserve input immutability, repeated-admission rejection, unresolved after-tax treatment and default-off admission.
- Retain all existing candidate scenarios and the standardized-only omission diagnostic. Compare authenticated B Git behavior with current behavior in isolated processes; allow only the intended validation/persistence differences and retain applicable pre-relocation comparisons.
- Run `/opt/anaconda3/bin/python -m pytest -q core/tests/test_normalization_candidate_admission.py` and `/opt/anaconda3/bin/python -m pytest -q core/tests/test_data_ingestion_ownership.py core/tests/test_normalization.py core/tests/test_filing_json.py`, plus any separate focused repair tests. Do not skip, deselect, xfail or weaken existing gates.
- Run `git diff --check`. Append measured results, baseline bindings, bypass rejection evidence and successful recovered linkage to `RESULT.md`; do not rewrite historical records or claim parent Completion or Session acceptance.

## Preserved ownership and remaining scope

Completed Modeler data ownership covers `interface`, `validators`, `standardized_io`, `line_identity`, `issuer_fiscal`, `historical_operating_kpis` and `historical_segments`; Director retains `data/schema`. Documentary types and historical-strategy contracts remain in Extractor.

Completed Modeler ingestion ownership covers `base`, `reconciler`, `filing_reconciler`, `filing_standardizer`, `management_kpi`, `management_kpi_identity`, `management_kpi_reconciliation`, `management_kpi_history`, `operating_kpi`, `geographic_segment`, `share_basis` and KPI validator admission. Director owns `filing_cli`, `note_handoff` and combined validation; Extractor retains documentary binding. Preserve issue ordering, façades, private exports, object identity and inventory mappings.

Preserve public `bav` commands, aliases, lazy loading, optional Trainer independence, dormant forecasting, accounting signs, fiscal distinctions, precision, reconciliations, source/transformation provenance, residual qualifications and admission/comparison independence. Do not rewrite canonical source or extracted/reconciled inputs.

Preserve completed Driver handoffs, first-name-wins assessments, CFO classification, attribution amounts/locators, counterfactual scope, `supported_as_attribution`, `not independently verified` and `outside the accounting bridge`. Attribution appendices remain independent of principal selection; margin prose requires independently selected margin evidence.

Classification/normalization interpretation splits, broader normalization-candidate separation, enrichment/Legacy decomposition, remaining orchestration relocation, unrelated removals, test ownership migration and final repository-wide verification remain subsequent scope. Keep the separate enrichment-sidecar defect visible. Do not add default admission activation, CLI expansion, a general provenance framework, algorithm/report redesign, Trainer expansion or second-phase features.

Preserve ownership/recovery safeguards, protected documents, unrelated dirty work and zero-byte research placeholders. Reuse prior verification only while dependencies remain applicable. SESSION native verification remains binding if formulas/dependencies or presentation change, through Office Bridge. Cursor must not modify TARGET.md, SESSION.md or IMPLEMENTATION.md.
