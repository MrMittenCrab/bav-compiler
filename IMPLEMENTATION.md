# Step 10.11 — Isolate Legacy manual ingestion
AUTOCYCLE_PLAN: {"finding_key": "Isolate Legacy manual ingestion", "kind": "work", "objective": "Isolate Legacy manual ingestion", "plan_id": "7020abbb0a364d50b31f446b95d5cd64", "predecessor_review_sha256": "f8a74e923cceb7801c6b4720f711d8c842a712a3865846ca357c6c1142ba5f35", "step_id": "10.11", "work_id": "ac3a1ebfb5df43c3ac215cddb71437fb"}

## Completion

HK manual and Excel ingestion execute from Legacy with existing interfaces and behavior preserved, while ordinary company build, check, publication and canonical ingestion execute without loading or depending on those Legacy adapters.

## Bounded work

Implement the manual-ingestion disposition in `director/docs/MIGRATION_INVENTORY.md` §§4.2 and 7.3.

- Move `core/ingestion/manual_hk.py` and `core/ingestion/excel_import.py` implementations to `legacy/ingestion/`, retaining existing names and relative cooperation between the adapters.
- Keep shared documentary contracts in Extractor, standardized financial contracts and reconciliation in Modeler, and label policy in Director. Legacy adapters consume these canonical owners.
- Retain thin compatibility modules at the old paths, preserving public names, required private helpers and canonical object identity.
- Make adapter exports in `core/ingestion/__init__.py` lazy while preserving `__all__` and existing import interfaces. Importing ordinary ingestion compatibility modules must not initialize Legacy adapters.
- Remove the eager adapter import from `core/__main__.py`. Load the canonical Legacy adapter only when executing `ingest` or the explicit Excel-input compatibility build branch.
- Preserve strict standardized-JSON loading, company routing, optional Trainer derivation and all command arguments, output paths, messages and exit behavior.
- Update affected inventory entries and Legacy documentation to distinguish retained compatibility entry points from active company execution.

## Preservation

Preserve adapter date parsing, period order, label normalization, missing values, historical shares, concepts, source/page provenance, statement merging, checksums and failure behavior. Do not redesign ingestion or add extraction capabilities.

Preserve completed component ownership, classification/normalization calculations and qualifications, compatibility exports, protected-input immutability, standardized-only ordinary preparation, public `bav` interfaces, optional Trainer independence, dormant forecasting and zero-byte research placeholders.

Retain normalization fingerprint, adoption, treatment, authorization, persistence and once-only conversion gates; isolated baseline comparisons, lifecycle rejection fixtures and all 11-observation round trips remain intact. Admission remains default-off and independent of ordinary reconciliation and comparison.

Do not rewrite source, extracted/reconciled inputs, workbook formulas or presentation.

## Verification and recording

- Authenticate live implementation baseline B from populated `IMPLEMENT_BASE_SHA`, otherwise the normal baseline and bound-attempt mechanisms. Verify branch, ancestry and attempt bindings; fail closed if authentication is unavailable. Keep controller evidence read-only.
- Inspect historical adapter blobs at B and compare canonical destinations, recording relocation continuity and intentional import changes.
- Extend `core/tests/test_data_ingestion_ownership.py` for Legacy ownership, compatibility identity, private exports and fresh-process import orders. Verify ordinary ingestion imports do not load Legacy.
- Extend existing CLI and ownership tests to exercise normal company routes with Legacy imports rejected, while explicit ingest and Excel compatibility builds retain their behavior.
- Compare representative JSON and Excel adapter results with B, including historical shares, source provenance, merging and reconciliation failures.
- Run `/opt/anaconda3/bin/python -m pytest -q core/tests/test_build_cli.py core/tests/test_filing_cli.py core/tests/test_data_ingestion_ownership.py core/tests/test_engine_trainer_ownership.py core/tests/test_trainer.py core/tests/test_reference_integrity.py core/tests/test_current_build.py core/tests/test_publication.py core/tests/test_cross_company_robustness.py core/tests/test_lululemon_benchmark.py core/tests/test_fast_retailing_benchmark.py`.
- Run `git diff --check` and the corresponding diff check against authenticated B. Do not weaken, skip, deselect or xfail preserved gates.
- Append baseline bindings, ownership/path mappings, measured verification and unresolved defects to `RESULT.md`; preserve historical records.

## Remaining scope and constraints

Remaining Director relocation, other Legacy categories, Remove items, repository-wide test ownership migration and final migration verification remain separate Session work. This step does not establish Session acceptance.

Preserve ownership/recovery, provider retry, human adoption, interruption, candidate validation, protected-document, unrelated-dirty-work and Review-cache safeguards. Reuse verification only while its dependencies remain applicable; changed workbook formulas/dependencies or presentation retain SESSION’s Office Bridge requirements. Cursor must not modify TARGET.md, SESSION.md or IMPLEMENTATION.md.
