# Step 10.9.6 — Decompose management-KPI enrichment ownership
AUTOCYCLE_PLAN: {"finding_key": "Relocate data contracts and ingestion responsibilities", "kind": "work", "minor": 6, "objective": "Decompose management-KPI enrichment ownership", "plan_id": "cba07f8dbe9b432293a6def32e655add", "predecessor_review_sha256": "af85cb3cede68bc7aad5833de83b59184e5dd6a60e30f86b50b1ad6189f63c48", "step_id": "10.9.6", "work_id": "59ab4fdc9ec144ffb2c2b3f0bb8adaeb"}

## Completion

The data contracts, admission/reconciliation implementations and ingestion orchestration listed below execute from their canonical Modeler and Director owners, with runtime callers using those owners and existing compatibility imports, source provenance, analytical behavior and public `bav` interfaces preserved.

## Bounded work

Split `core/ingestion/management_kpi_enrichment.py` across canonical owners and resolve the enrichment-sidecar regression while preserving the canonical company-build input contract.

- Relocate existing source-faithful PDF inspection, decoding, passage extraction, documentary evidence records and printed/physical page binding into `extractor/ingestion/management_kpi_enrichment.py`. Separate these from analytical metric mappings and admission decisions; do not build a new extraction system.
- Put deterministic definition-equivalence checks, analytical enrichment transformations and `build_group_decisions` with their mechanical failure mappings in `modeler/ingestion/management_kpi_enrichment.py`. Consume Extractor evidence without duplicating documentary parsing. Keep source-faithful feature extraction with Extractor and reproducible comparison checks with Modeler.
- Put `enrich_management_working_copies` directory traversal, protected-path checks, sequencing and sidecar persistence in `director/ingestion/management_kpi_enrichment.py`, delegating substantive operations. Preserve signatures, defaults, sidecar schema, ordering and failure behavior.
- Keep shared workflow contracts under Director and documentary records under Extractor, with one definition per type. Separate actual meaning judgments into Interpreter only where existing executable responsibility requires it; do not invent judgment machinery or promote management emphasis into driver status.
- Replace the core module with a thin compatibility façade preserving public and required private exports. Update active callers in `modeler/ingestion/management_kpi.py`, `management_kpi_identity.py` and other direct consumers. Canonical implementations must not import the façade or Legacy.
- Update `director/docs/MIGRATION_INVENTORY.md` with responsibility-level destinations, replacing its blanket Legacy assignment for enrichment. Replace deferred enrichment-location assertions in `core/tests/test_data_ingestion_ownership.py` with canonical ownership, identity and dependency coverage.

## Sidecar regression

Reproduce `test_ordinary_prepare_writes_resolution_and_keeps_revenue_per_store` and compare its expectations with authenticated historical code and TARGET’s canonical-input contract. `core/current_build.py:prepare_company_input` currently loads accepted standardized data and ignores staging.

Preserve ordinary preparation’s canonical loading behavior. Exercise sidecar creation through the explicit Director working-copy enrichment workflow, followed by existing validation, reconciliation and admission. Transfer the sidecar, FY2024 date, printed-page 34 → physical-page 40, protected-input preservation and selected-admission assertions into that workflow’s integration coverage. Retain ordinary preparation coverage for management observations, independent store totals and revenue-per-store anchors, and verify it does not regenerate upstream working copies. Repair any demonstrated enrichment defect; do not restore implicit build-time enrichment or merely delete failing assertions.

## Preservation

Preserve source file/hash, row, period, amount, currency, scale, locator and individual passage bindings; unresolved/unavailable locators, ambiguous-linkage rejection, original values/labels, protected extracts and input immutability. Never infer printed pages from physical pages, infer metric exclusions from year length alone, or sum overlapping comparative observations.

Preserve fiscal labels versus dates, 52/53-week evidence, metric-specific exclusions, comparison windows, identity populations, definition distinctions, prior-period occurrences, peer-specific failures, issue ordering and level-admission/comparison independence. Missing presentation, assurance or revision evidence remains unresolved.

Preserve completed normalization-candidate ownership, fingerprint recomputation, adoption/treatment/authorization gates, exact negative-face transformation and once-only conversion. Admission remains default-off and outside ordinary reconciliation; retain blocked/provisional persistence rejection, separate admission artifacts, standardized-only loading, omission diagnostics and repeated-admission rejection. Independent authorization does not establish grouping as source fact or resolve after-tax treatment.

Preserve completed Driver handoffs, first-name-wins assessments, CFO classification, attribution amounts/locators, counterfactual scope and qualifications: `supported_as_attribution`, `not independently verified`, and `outside the accounting bridge`. Attribution appendices remain independent of principal selection; margin prose requires independently selected margin evidence.

Preserve completed canonical ownership and compatibility mappings, public `bav` commands/aliases/lazy loading, optional Trainer independence, dormant forecasting, accounting signs, precision, reconciliations and residual qualifications. Do not rewrite canonical source or extracted/reconciled inputs.

## Verification

- Authenticate implementation baseline B from populated `IMPLEMENT_BASE_SHA`, otherwise normal implementation-baseline, bound-attempt and latest-implementation mechanisms. Preserve branch, work, attempt, ancestry and exact-checkpoint bindings; fail closed. Controller evidence remains read-only.
- Compare historical Git blobs at B with canonical destinations for semantic and provenance continuity. Separate the intentional regression-test contract correction from behavior-preserving relocation.
- Retain isolated current-versus-B normalization comparisons, lifecycle fixtures and negative rejection cases, including synthetic and independently authorized round trips for all 11 observations. Retain pre-relocation comparator `eb65dc63845b940162c48e39ae9af7598d2a3078`; historical tuples never authorize the live attempt.
- Exercise enrichment through canonical and compatibility entry points, including fresh-process imports, protected-directory rejection, unsupported page bindings, complete passage attribution and repeated working-copy enrichment.
- Run `/opt/anaconda3/bin/python -m pytest -q core/tests/test_management_kpi_enrichment.py core/tests/test_management_kpi_reconciliation.py core/tests/test_normalization_candidate_admission.py core/tests/test_data_ingestion_ownership.py core/tests/test_normalization.py core/tests/test_filing_json.py core/tests/test_research_drivers.py` and `git diff --check`. Do not skip, deselect, xfail or weaken preserved gates.
- Append actual responsibility destinations, baseline bindings, regression diagnosis, measured verification and remaining defects to `RESULT.md`; preserve historical records and distinguish bounded completion from parent Completion and Session acceptance.

## Remaining scope and constraints

Broader classification/normalization interpretation splits, remaining ingestion and Legacy decomposition, unrelated removals, test ownership migration and final repository-wide verification remain unfinished commitments. No CLI expansion, general provenance framework, algorithm/report redesign, Trainer expansion or second-phase features.

Preserve ownership/recovery, provider retry, human adoption, interruption, candidate validation, protected-document, unrelated-dirty-work and Review-cache safeguards and zero-byte research placeholders. Reuse verification only while dependencies remain applicable; changed workbook formulas/dependencies or presentation retain SESSION’s Office Bridge verification requirements. Cursor must not modify TARGET.md, SESSION.md or IMPLEMENTATION.md.
