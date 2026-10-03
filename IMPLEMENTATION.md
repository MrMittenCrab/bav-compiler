# Step 10.10 — Split classification and normalization interpretation ownership
AUTOCYCLE_PLAN: {"finding_key": "Split classification and normalization interpretation ownership", "kind": "work", "objective": "Split classification and normalization interpretation ownership", "plan_id": "f3e25b8607b9495588b36e3549201fb9", "predecessor_review_sha256": "f3b098ef292664f9392f132fb388f574bb23764ce275d7163c3ad60038940e77", "step_id": "10.10", "work_id": "823b625d346943a6b3c6ee40c60a72ed"}

## Completion

Classification case selection and normalization calculations execute from Modeler, their interpretive rationales execute from Interpreter, and runtime callers use canonical owners while existing calculations, qualifications, compatibility imports and public interfaces remain preserved.

## Bounded work

Implement the classification/normalization split in `director/docs/MIGRATION_INVENTORY.md` §4.

- Move deterministic classification case selection, `JudgmentCase` and mechanical helpers from `core/model/judgment.py` to `modeler/judgment.py`.
- Move `ClassificationJudgmentTemplate`, `CLASSIFICATION_JUDGMENT_TEMPLATES` and their rationale, consequence and prompt content to `interpreter/classification_judgment.py`. Preserve registry keys, options, wording and validation behavior.
- Move normalization selectors, candidate validation, case identities, treatment selection, series arithmetic and associated data types from `core/model/normalization.py` to `modeler/normalization.py`.
- Place normalization rationale/consequence handling and interpretive prompt ownership in existing `interpreter/normalization.py`. Preserve supplied `referenceRationale` and `consequenceNote` verbatim, existing grouping qualifications and the distinction between supplied judgments and source facts. Use a minimal handoff; do not introduce new inference or treatment decisions.
- Replace both old modules with compatibility façades preserving existing names, signatures, defaults and canonical object identity, including required private helpers. Keep one canonical definition per symbol.
- Update runtime imports in workbook construction, check context, historical expectations, normalized per-share calculations, admission and other actual callers. Canonical implementations must not import these façades or Legacy.
- Update the inventory’s affected ownership and transitional-dependency notes.

## Preservation

Preserve case IDs, ordering, selectors, ambiguity/override filtering, zero-value filtering, alternatives, errors, treatment defaults, missing-value behavior, accounting signs, precision, tax handling and numerical series.

Preserve normalization fingerprint recomputation, adoption/treatment/authorization gates, original source and passage bindings, negative-face transformation and once-only conversion. Admission stays default-off, separate from ordinary reconciliation, with blocked/provisional persistence rejection and repeated-admission rejection. Independent authorization establishes neither grouping as source fact nor after-tax treatment.

Preserve completed ingestion/enrichment ownership, compatibility exports, standardized-only ordinary preparation, protected input immutability, admission/comparison independence, Driver qualifications, public `bav` commands and lazy loading, optional Trainer independence, dormant forecasting and zero-byte research placeholders. Do not rewrite source or extracted/reconciled inputs, workbook formulas or presentation.

## Verification and recording

- Resolve and authenticate live implementation baseline B through populated `IMPLEMENT_BASE_SHA`, otherwise normal baseline and bound-attempt mechanisms. Verify branch, ancestry and attempt/checkpoint bindings; fail closed if authentication is unavailable. Keep controller evidence read-only.
- Inspect historical Git blobs at B before comparing canonical destinations and provenance continuity. Demonstrate unchanged classification cases, normalization cases, rationale text and calculated series for representative existing fixtures.
- Extend existing ownership coverage for canonical definitions, compatibility identity, required private exports, fresh-process import orders and absence of runtime façade/Legacy dependencies.
- Run `/opt/anaconda3/bin/python -m pytest -q core/tests/test_classification.py core/tests/test_normalization.py core/tests/test_normalized_per_share.py core/tests/test_lease_liability.py core/tests/test_normalization_candidate_admission.py core/tests/test_modeler_calculation_ownership.py core/tests/test_data_ingestion_ownership.py core/tests/test_reference_integrity.py core/tests/test_current_build.py core/tests/test_cross_company_robustness.py core/tests/test_lululemon_benchmark.py core/tests/test_fast_retailing_benchmark.py`.
- Retain isolated current-versus-B admission comparisons, lifecycle rejection fixtures and synthetic/independently authorized round trips for all 11 observations. Do not weaken, skip, deselect or xfail preserved gates.
- Run `git diff --check` and the corresponding diff check against authenticated B.
- Append ownership mappings, baseline bindings, measured verification and unresolved defects to `RESULT.md`; preserve historical records. Do not claim Session acceptance from this split.

## Remaining scope and constraints

Remaining Legacy/ingestion dispositions, repository-wide test ownership migration, unrelated removals and final migration verification remain separate Session work. No algorithm/report redesign, general provenance framework, new Extractor, reasoning engine, Trainer expansion or second-phase features.

Preserve ownership/recovery, provider retry, human adoption, interruption, candidate validation, protected-document, unrelated-dirty-work and Review-cache safeguards. Reuse verification only while dependencies remain applicable; changed workbook formulas/dependencies or presentation retain SESSION’s Office Bridge requirements. Cursor must not modify TARGET.md, SESSION.md or IMPLEMENTATION.md.
