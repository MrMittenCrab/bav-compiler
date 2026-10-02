# Step 10.2 — Relocate Extractor contracts and loading
AUTOCYCLE_PLAN: {"finding_key": "Relocate Extractor contracts and loading", "kind": "work", "objective": "Relocate Extractor contracts and loading", "plan_id": "798b84b06ef64e51880c54d79da8d14a", "predecessor_review_sha256": "64e97042b43bdc8c655380f7d5c54e3aba038d1b129d83facadbd09a11f48dd4", "step_id": "10.2", "work_id": "5afa7df9522b4e74b6d033a577043e15"}

## Completion

Existing Extractor responsibilities reside at the inventory’s canonical destinations, consumers use those destinations, and relevant regressions demonstrate preserved loading, provenance, admission and public `bav` behavior.

## Bounded work

Execute the Extractor relocation in `director/docs/MIGRATION_INVENTORY.md` §§4.3, 7.2–7.3 and 12–14.

- Authenticate implementation baseline B from populated `IMPLEMENT_BASE_SHA`, otherwise the normal baseline records and branch, ancestry and attempt/checkpoint bindings; fail closed if unavailable. Compare migrated responsibilities against historical Git blobs at B.
- Establish the inventory’s visible component roots with minimal package scaffolding. Add `extractor/README.md` explaining the existing JSON-contract boundary and absence of production PDF extraction.
- Move `core/data/filing.py` and `core/ingestion/filing_json.py` to `extractor/data/filing.py` and `extractor/data/filing_json.py`, retaining contract types, symbol names, parsing and serialization behavior.
- Split `core/ingestion/management_kpi.py`: move schema classification and its helpers/constants to `extractor/data/extracted_kind.py`; move source-faithful document types, parsing/loading and their supporting helpers to `extractor/data/management_kpi_json.py`. Keep analytical admission, binding decisions and reconciliation with their existing Modeler-owned implementation pending its relocation.
- Move parse-time operating-KPI fact-type and label-shape helpers to `extractor/data/operating_kpi_contract.py`. Keep analytical identity validation and admission outside Extractor.
- Relocate provenance binding, source-row identity, validation contracts and documentary validation to `extractor/data/filing_validator.py`. Separate existing operating-KPI admission checks from documentary validation; preserve their execution, diagnostic ordering and aggregate report behavior through the calling orchestration.
- Move historical-strategy contracts, I/O, validation and locators to `extractor/data/historical_strategy.py`. Preserve attributed management statements as evidence without changing analytical driver selection.
- Split documentary `DocumentManifest`, its supporting document types and `DataSourceAdapter` into `extractor/data/interface.py`, preserving adapter signatures without pulling model payload implementation into Extractor or introducing runtime import cycles.
- Relocate `scripts/prepare_lululemon_operating_kpi_filings.py` to `extractor/scripts/prepare_lululemon_operating_kpi_filings.py`; adjust repository-root resolution and consumers while preserving destination-only writes and canonical source protection.
- Update affected production imports, package exports, tests, script references and relevant documentation. Use one canonical implementation per responsibility; retain only thin forwarding exports where an existing supported interface requires them.
- Preserve `filing_cli` classify → load → validate/admit sequencing. Company builds continue reading `reconciled/standardized.json`; do not route them through `load_extracted_filing`.

## Verification

- Run affected filing JSON, filing CLI, filing reconciliation, management-KPI admission/identity/reconciliation/history, operating-KPI fact and geographic-segment regressions, plus historical-strategy/revenue-driver, current-build and public CLI tests.
- Run `test_lululemon_benchmark.py` and `test_fast_retailing_benchmark.py` against relocated imports. Add focused coverage only where existing tests miss a changed handoff.
- Check round-trip payloads, schema rejection, missing versus zero values, fiscal distinctions, reported labels, source hashes/pages, portable paths, diagnostics and admission outcomes against baseline behavior.
- Verify fresh-process canonical imports and public `python -m bav --help`; inspect dependencies for cycles and accidental Extractor ownership of analytical decisions.
- Check relocation continuity against B, search for stale operational references and run `git diff --check`. Distinguish unchanged moves from intentional import and responsibility-split edits.
- Append measured commands, results, path mappings, preservation findings and remaining migration scope to `RESULT.md`. Record unavailable verification explicitly.
- Apply SESSION native-verification requirements if workbook formulas/dependencies or presentation change; use Office Bridge for native work.

## Limits and remaining scope

Preserve canonical source evidence, accounting signs, precision, provenance, fail-closed controls, optional Trainer behavior, zero-byte placeholders and ownership/recovery/protected-document safeguards. Do not modify canonical company inputs or regenerate publications merely to relocate code.

Director specification and STYLE.md relocation, mixed Driver/assessment splits, remaining component moves, Trainer inversion, justified removals and final representative build/check/publication verification remain subsequent migration work.

No new PDF extractor, reasoning system, analytical methods, Trainer expansion or second-phase features. Cursor must not modify TARGET.md, SESSION.md or IMPLEMENTATION.md or rewrite historical RESULT records.
