# Step 10.15.1 — Finish normalization-admission test ownership and executable references

AUTOCYCLE_PLAN: {"finding_key": "Align tests and current documentation with canonical ownership", "kind": "work", "minor": 1, "objective": "Finish normalization-admission test ownership and executable references", "plan_id": "684fda603868472a89ce50dad49aa1d1", "predecessor_review_sha256": "bab919f4f81ed0e500546901b7d0617ccb3e480f00a6612ab15aaed4cd4df1ed", "step_id": "10.15.1", "work_id": "97863636032d4cc68fa5872fcc3f895d"}

## Completion

Remaining tests reside under their canonical component owners with preserved coverage and working discovery, and current repository documentation, branding and executable references accurately describe the migrated architecture and supported interfaces.

## Bounded work

- Split `core/tests/test_normalization_candidate_admission.py` by asserted responsibility: construction, mechanical validation and persistence under `modeler/tests/`; handoff, cross-component integration, protected-artifact and baseline-authentication coverage under `director/tests/`; independently asserted interpretation qualifications under `interpreter/tests/`.
- Relocate `core/tests/normalization_candidate_isolated_driver.py` to Director’s test support and update its callers. Keep historical comparator imports valid for their materialized Git versions; use canonical imports for current behavior.
- Replace the behavior import from `core.model.normalization` with `modeler.normalization`. Preserve deliberate compatibility-import, façade-identity, patchability, public CLI and historical-baseline assertions.
- Share necessary fixture/helper code without importing collected test functions into another suite. Preserve test names, parameterization, assertions, negative cases, subprocess behavior and repository-root resolution.
- Keep protected fixture bytes and externally referenced fixture locations stable, including `core/tests/fixtures/` consumers in `director/project_companies.json`.
- Correct `director/docs/build-contract.md`: focused checks target `modeler/tests/test_build_contract.py`; regression discovery includes `director/tests extractor/tests modeler/tests interpreter/tests composer/tests legacy/tests core/tests`.
- Update `director/docs/MIGRATION_INVENTORY.md` §§4.5, 11 and 14–15 with actual admission-test and helper destinations, removing the active decision to retain mixed admission tests under Core.
- Check active documentation and executable references for other paths invalidated by completed relocation; repair direct stale references. Preserve completed ownership splits, branding updates, archived documentation and historical Git comparator paths.

## Preservation

Authenticate execution baseline B from populated `IMPLEMENT_BASE_SHA`, otherwise through the normal baseline and bound-attempt mechanisms. Verify branch, ancestry and checkpoint bindings; fail closed if authentication is unavailable.

Compare moved or split content against Git blobs at B, preserving provenance and semantic coverage without duplicate legacy copies or migration receipts. Preserve live authentication guards and historical comparator bindings when moving their tests.

Preserve public interfaces, explicit JSON/Excel routes, optional Trainer behavior, source immutability, accounting signs, fiscal distinctions, precision, reconciliations, residual qualifications, admission/comparison independence, fail-closed gates and zero-byte research placeholders. Normalization admission remains default-off.

Do not redesign production algorithms, workbook architecture or publication presentation, activate deferred features, introduce test infrastructure, or modify controller authentication machinery. Preserve ownership/recovery, provider retry, human adoption, interruption, candidate validation, protected-document, unrelated-dirty-work and Review-cache safeguards.

## Verification and recording

- Collect the seven test trees before and after the split using the project interpreter. Map relocated node IDs and parameterized cases; establish no missing or newly duplicated coverage rather than relying on equal counts alone.
- Run all split admission suites and isolated historical/current comparisons, plus affected normalization, ingestion ownership, compatibility, CLI, build-contract and reference-integrity regressions. Rerun publication and optional Trainer regressions where shared helpers or discovery changes affect them.
- Execute the corrected documented focused and regression commands. Use permitted writable temporary/cache locations when needed; record infrastructure failures separately from product failures without weakening assertions or adding skips.
- Check active documentation paths, canonical imports, helper references and fixture consumers. Run `git diff --check` and inspect the diff against authenticated B.
- Reuse prior representative build/check/publication evidence only while dependencies remain applicable. Apply SESSION’s Office Bridge requirements if workbook formulas/dependencies or presentation change.
- Append ownership mappings, measured collection and regression results, remaining failures and subsequent representative Session verification scope to `RESULT.md`. Preserve historical records; do not claim Session completion or certify a prospective next ID.

Cursor must not modify TARGET.md, SESSION.md or IMPLEMENTATION.md.
