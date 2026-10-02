# Step 10.3 — Relocate Director specifications and update operational references
AUTOCYCLE_PLAN: {"finding_key": "Relocate Director specifications and update operational references", "kind": "work", "objective": "Relocate Director specifications and update operational references", "plan_id": "f8a7b9cf43b244d28a758423944d7a14", "predecessor_review_sha256": "608038b183f0e3a35fa2f914924fefc1276f0bf30b6c68adc80003fec206253c", "step_id": "10.3", "work_id": "1fa333611fee4d899f0896036f117f2a"}

## Completion

Director specifications occupy their inventory destinations, operational references resolve to those destinations, and the README presents BAV Compiler while preserving specification content and existing public behavior.

## Bounded work

Execute the documentation relocation in `director/docs/MIGRATION_INVENTORY.md` §§4.9 and 11.

- Authenticate implementation baseline B from populated `IMPLEMENT_BASE_SHA`, otherwise the normal baseline records, branch, ancestry and attempt/checkpoint bindings; fail closed if unavailable. Use historical Git blobs at B for content comparisons.
- Move `STYLE.md` to `director/docs/STYLE.md`, preserving its bytes and single-authority role for presentation and language.
- Move `DRIVER.md` to `director/docs/DRIVER.md`, preserving its requirements, evidence qualifications and source attributions while updating STYLE references.
- Move `docs/build-contract.md` to `director/docs/build-contract.md`, preserving the documented build policy and references to implementation that has not yet moved.
- Move `docs/FAST_RETAILING_BENCHMARK.md` to `director/docs/FAST_RETAILING_BENCHMARK.md`. Update obsolete operational source paths to `build/input/fast_retailing/source/`; distinguish historical baseline descriptions from current source availability without claiming unavailable PDFs are present.
- Update affected operational links, documentation paths, test file reads and `core/research/style.py` documentation. Resolve Markdown links relative to their containing documents. Preserve historical inventory mappings and RESULT records.
- Update the root README title and product description to BAV Compiler. Describe the five active components and Legacy according to current migration state; retain useful commands, supported companies and optional Trainer guidance. Replace the obsolete immediate Step 9 roadmap with the current structural-migration priority and retain deferred product capabilities.
- Correct the README’s company-build description to reflect consumption of `reconciled/standardized.json`, keeping explicit validate-source/reconcile workflows distinct.
- Update README identity and specification-path assertions together, retaining their substantive checks. Keep tests at their existing locations for this step.

## Verification

- Compare each relocated specification with its Git blob at B. Record exact preservation for unchanged moves and inspect intentional reference or operational-description edits for unchanged substantive policy.
- Search active consumers for stale document locations and resolve changed links. Historical paths in inventory mappings and prior RESULT entries remain historical evidence.
- Run affected specification and README checks in `core/tests/test_research_drivers.py` and `core/tests/test_learner_ready_presentation.py`, plus `core/tests/test_build_contract.py` and `core/tests/test_fast_retailing_benchmark.py`.
- Verify `python -m bav --help` and run `git diff --check`.
- Append measured verification, relocation mappings, intentional content changes and remaining migration scope to `RESULT.md`. Record unavailable verification explicitly.
- Apply SESSION native-verification requirements if workbook formulas/dependencies or presentation change; native work uses Office Bridge.

## Limits and remaining scope

Preserve canonical company inputs, source evidence, accounting signs, precision, provenance, fail-closed controls, optional Trainer behavior and zero-byte research placeholders. Preserve ownership, recovery, protected-document and unrelated-dirty-work safeguards.

Do not alter style rules, analytical behavior or generated publications. Do not restore source PDFs, rewrite source manifests or relocate runtime implementations for this documentation step.

Mixed Driver/assessment splits, remaining component relocation, Trainer inversion, justified removals and final representative build/check/publication verification remain subsequent migration work. No second-phase features.

Cursor must not modify TARGET.md, SESSION.md or IMPLEMENTATION.md or rewrite historical RESULT records.
