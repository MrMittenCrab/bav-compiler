# Step 10.9.7 — Restore management-KPI enrichment compatibility exports
AUTOCYCLE_PLAN: {"finding_key": "Relocate data contracts and ingestion responsibilities", "kind": "work", "minor": 7, "objective": "Restore management-KPI enrichment compatibility exports", "plan_id": "0d6df9da13994dad9013c7393a8d8d59", "predecessor_review_sha256": "50b9b5c24fb5af1170be62388803100b35dc91298ed17a98ee7b7b3605a051f7", "step_id": "10.9.7", "work_id": "59ab4fdc9ec144ffb2c2b3f0bb8adaeb"}

## Completion

The data contracts, admission/reconciliation implementations and ingestion orchestration listed below execute from their canonical Modeler and Director owners, with runtime callers using those owners and existing compatibility imports, source provenance, analytical behavior and public `bav` interfaces preserved.

## Bounded work

Repair the reviewed enrichment façade omissions and EOF whitespace without changing canonical function bodies or reopening completed relocation.

- In `core/ingestion/management_kpi_enrichment.py`, explicitly re-export `collect_calendar_corpus`, `collect_exclusion_corpus`, `extract_comparison_window` and `extract_spsf_prior_period_levels` from `extractor.ingestion.management_kpi_enrichment`. Preserve object identity, signatures and defaults; add no wrappers or duplicate implementations.
- Extend `core/tests/test_data_ingestion_ownership.py` with compatibility coverage for all four names. Assert direct imports succeed and are identical to their Extractor definitions, including fresh-process façade-first and canonical-first import orders. Confirm this coverage fails before the repair and passes afterward.
- Remove extra blank lines at EOF from `extractor/ingestion/management_kpi_enrichment.py`, `modeler/ingestion/management_kpi_enrichment.py` and `director/ingestion/management_kpi_enrichment.py`, retaining one terminating newline.

## Preservation

Retain Extractor documentary ownership, Modeler analytical ownership, Director working-copy orchestration, shared contracts, canonical caller routing, compatibility exports and responsibility inventory mappings. Canonical implementations must not import the façade or Legacy.

Keep ordinary company preparation standardized-only. Preserve explicit Director enrichment integration coverage for sidecars, FY2024 dates, printed-page 34 → physical-page 40 binding, protected inputs and selected admission; retain ordinary preparation coverage for management observations, independent store totals and revenue-per-store anchors without upstream regeneration.

Preserve source file/hash, row, period, amount, currency, scale, locator and individual passage bindings; original values/labels, protected extracts and input immutability. Retain unresolved locators, ambiguous-linkage rejection, fiscal labels versus dates, 52/53-week evidence, metric-specific exclusions, comparison windows, identity populations, definition distinctions, prior-period occurrences, peer-specific failures, issue ordering and admission/comparison independence. Do not infer printed pages from physical pages, infer exclusions from year length alone or sum overlapping observations. Missing presentation, assurance or revision evidence remains unresolved.

Preserve normalization ownership, fingerprint recomputation, adoption/treatment/authorization gates, exact negative-face transformation and once-only conversion. Admission remains default-off and outside ordinary reconciliation, with blocked/provisional persistence rejection, separate artifacts, omission diagnostics and repeated-admission rejection. Independent authorization establishes neither grouping as source fact nor after-tax treatment.

Preserve Driver handoffs, first-name-wins assessments, CFO classification, attribution amounts/locators, counterfactual scope and qualifications: `supported_as_attribution`, `not independently verified`, and `outside the accounting bridge`. Attribution appendices remain independent of principal selection; margin prose requires independently selected margin evidence.

Preserve public `bav` commands/aliases/lazy loading, optional Trainer independence, dormant forecasting, accounting signs, precision, reconciliations and residual qualifications. Do not rewrite canonical source or extracted/reconciled inputs.

## Verification and recording

- Authenticate live implementation baseline B from populated `IMPLEMENT_BASE_SHA`, otherwise normal implementation-baseline, bound-attempt and latest-implementation mechanisms. Preserve branch, work, attempt, ancestry and checkpoint bindings; fail closed. Controller evidence stays read-only.
- Retain reviewed relocation baseline `da53beb625d195794b947b98718a42f70a07bb53` and checkpoint `f902de4922c3c745afb35aacc1cd0c8c74655308` as historical comparators, not substitutes for live authentication. Verify the four historical definitions remain canonical and unchanged.
- Retain isolated current-versus-B normalization comparisons, lifecycle fixtures, negative rejection cases and synthetic/independently authorized round trips for all 11 observations, including pre-relocation comparator `eb65dc63845b940162c48e39ae9af7598d2a3078`.
- Retain canonical/compatibility enrichment coverage for protected-directory rejection, unsupported page bindings, complete passage attribution and repeated working-copy enrichment.
- Run `/opt/anaconda3/bin/python -m pytest -q core/tests/test_management_kpi_enrichment.py core/tests/test_management_kpi_reconciliation.py core/tests/test_normalization_candidate_admission.py core/tests/test_data_ingestion_ownership.py core/tests/test_normalization.py core/tests/test_filing_json.py core/tests/test_research_drivers.py`. Do not skip, deselect, xfail or weaken preserved gates.
- Run `git diff --check` and `git diff --check da53beb625d195794b947b98718a42f70a07bb53` against the repaired working tree so checkpoint-introduced EOF defects are included.
- Append baseline bindings, restored exports, canonical destinations, measured verification and remaining defects to `RESULT.md`. Preserve historical records; distinguish this repair from parent Completion and Session acceptance.

## Remaining scope and constraints

Broader classification/normalization interpretation splits, remaining ingestion and Legacy decomposition, unrelated removals, test ownership migration and final repository-wide verification remain unfinished commitments outside this repair. No CLI expansion, general provenance framework, algorithm/report redesign, Trainer expansion or second-phase features.

Preserve ownership/recovery, provider retry, human adoption, interruption, candidate validation, protected-document, unrelated-dirty-work and Review-cache safeguards and zero-byte research placeholders. Reuse verification only while dependencies remain applicable; changed workbook formulas/dependencies or presentation retain SESSION’s Office Bridge requirements. Cursor must not modify TARGET.md, SESSION.md or IMPLEMENTATION.md.
