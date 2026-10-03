# Step 10.15 — Align tests and current documentation with canonical ownership
AUTOCYCLE_PLAN: {"finding_key": "Align tests and current documentation with canonical ownership", "kind": "work", "objective": "Align tests and current documentation with canonical ownership", "plan_id": "739d224b4bfb41dd89fdfef8787451cd", "predecessor_review_sha256": "e9ee6c54f0cf3700cb47bd483ab6f5fc2a2147e1403842fe0264c93c9553a82c", "step_id": "10.15", "work_id": "97863636032d4cc68fa5872fcc3f895d"}

## Completion

Remaining tests reside under their canonical component owners with preserved coverage and working discovery, and current repository documentation, branding and executable references accurately describe the migrated architecture and supported interfaces.

## Bounded work

Use `director/docs/MIGRATION_INVENTORY.md` §§4.5, 11 and 14–15 to finish test ownership and current-reference alignment.

- Move homogeneous tests from `core/tests/` to their owning component’s `tests/`. Split mixed test modules by the responsibility asserted; place orchestration and cross-component integration tests under Director.
- Complete the ownership splits for research Drivers, revenue drivers, reported margin, ingestion/admission, benchmark policy versus numerical checks, publication, learner presentation and optional Trainer tests. Preserve already-completed splits.
- Use canonical imports for component behavior tests. Retain explicit compatibility-import, façade identity, public CLI, patchability and historical-baseline coverage.
- Update test helper imports, repository-root discovery, fixture paths and existing test commands after relocation. Preserve parameterization, assertions and independent negative cases; avoid duplicate collection or lost tests.
- Keep protected fixture bytes and externally referenced fixture locations stable, including fixtures used by `project_companies.json`. Record retained shared fixture locations and ownership in the inventory.
- Update `README.md` architecture and planned-work text to reflect completed Modeler relocation, Driver decomposition, Trainer inversion and removals. Describe five active components and retained Legacy behavior accurately.
- Align current package descriptions, component documentation, benchmark guidance and executable build/test references with canonical paths and BAV Compiler identity. Preserve public `bav`, compatibility names, supported commands and dependency-file names.
- Update the inventory’s test destinations and remaining-work descriptions. Preserve historical RESULT records, archived documentation and historical Git comparator paths.

Final representative Session verification remains subsequent scope; documentation must not claim Session completion.

## Preservation

Authenticate execution baseline B from populated `IMPLEMENT_BASE_SHA`, otherwise through the normal baseline and bound-attempt mechanisms. Verify branch, ancestry and checkpoint bindings; fail closed if authentication is unavailable.

Compare moved tests and fixtures against Git blobs at B, accounting for intentional splits and import/path edits. Preserve provenance and coverage continuity without duplicate legacy copies or migration receipts.

Preserve public interfaces, explicit JSON/Excel routes, optional Trainer behavior, source immutability, accounting signs, fiscal distinctions, precision, reconciliations, residual qualifications, admission/comparison independence, fail-closed gates and zero-byte research placeholders. Normalization admission remains default-off.

Do not redesign production algorithms, workbook architecture or publication presentation, activate deferred features, introduce test infrastructure, or modify controller authentication machinery. Preserve ownership/recovery, provider retry, human adoption, interruption, candidate validation, protected-document, unrelated-dirty-work and Review-cache safeguards.

## Verification and recording

- Compare test collection before and after relocation, mapping moved or split cases so missing or duplicate coverage is visible.
- Run the relocated suites and affected ownership, compatibility, CLI, build-contract, reference-integrity, publication and optional Trainer regressions using existing project tooling. Do not weaken assertions or add skips to obtain a pass.
- Check current documentation links, executable paths, canonical imports and fixture consumers. Distinguish intentional historical/compatibility references from stale active references.
- Reuse prior representative build/check/publication evidence only while its dependencies remain applicable; rerun affected routes when they change. Apply SESSION’s Office Bridge requirements if workbook formulas/dependencies or presentation change.
- Run `git diff --check` and inspect the diff against authenticated B.
- Add measured verification, test ownership mappings, preserved coverage, remaining failures and final Session verification scope to `RESULT.md` without rewriting historical records or certifying a prospective next ID.

Cursor must not modify TARGET.md, SESSION.md or IMPLEMENTATION.md.
