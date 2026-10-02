# Step 10.9 — Relocate data contracts and ingestion responsibilities
AUTOCYCLE_PLAN: {"finding_key": "Relocate data contracts and ingestion responsibilities", "kind": "work", "objective": "Relocate data contracts and ingestion responsibilities", "plan_id": "0168b23846f641e185ae9fa4b4ef625f", "predecessor_review_sha256": "ac8fde580a8ce4845fb4f2f9d1f440221a9a8b15122edc0fe92ec24dd4419ee0", "step_id": "10.9", "work_id": "59ab4fdc9ec144ffb2c2b3f0bb8adaeb"}

## Completion

The data contracts, admission/reconciliation implementations and ingestion orchestration listed below execute from their canonical Modeler and Director owners, with runtime callers using those owners and existing compatibility imports, source provenance, analytical behavior and public `bav` interfaces preserved.

## Bounded work

- Authenticate implementation baseline B from populated `IMPLEMENT_BASE_SHA`, otherwise normal baseline and attempt/checkpoint records; verify branch, ancestry and ownership bindings. Fail closed if authentication is unavailable.
- Follow inventory §§4.3 and 7.2–7.3, preserving completed Extractor ownership and existing symbol names.
- Relocate these `core/data/` modules to `modeler/data/`, preserving basenames: `interface.py`, `validators.py`, `standardized_io.py`, `line_identity.py`, `issuer_fiscal.py`, `historical_operating_kpis.py`, `historical_segments.py`.
- Keep documentary types and historical-strategy contracts in `extractor/data/`. Preserve their existing compatibility exports from `core.data.interface`; update Extractor’s type-only references to canonical Modeler types.
- Relocate `core/data/schema.py`, including `StatementKind` and `validate_standardized`, to `director/data/schema.py`; retain the existing contract despite its lack of runtime callers.
- Relocate these `core/ingestion/` modules to `modeler/ingestion/`, preserving basenames: `base.py`, `reconciler.py`, `filing_reconciler.py`, `filing_standardizer.py`, `management_kpi.py`, `management_kpi_identity.py`, `management_kpi_reconciliation.py`, `management_kpi_history.py`, `operating_kpi.py`, `geographic_segment.py`, `share_basis.py`.
- Relocate `filing_cli.py` and `note_handoff.py` to `director/ingestion/`.
- Finish the existing `filing_validator.py` separation: documentary binding stays in Extractor; `operating_kpi_admission_issues` and its per-fact helper move to `modeler/ingestion/filing_validator.py`; combined `validate_extracted_filing` orchestration moves to `director/ingestion/filing_validator.py`. Preserve issue ordering, duplicate detection, source hashes and report types.
- Retain thin compatibility façades and package exports under `core.data` and `core.ingestion`, including existing explicit private imports and `__all__` contracts. Preserve canonical object identity without duplicating implementations or adding a compatibility framework.
- Update affected runtime consumers, lazy imports, scripts and tests to canonical owners. Update Extractor’s existing lazy metric-mapping reference without redesigning that dependency.
- Preserve transitional dependencies on `core.ingestion.management_kpi_enrichment` and `core.ingestion.normalization_candidate_admission`. Their mixed responsibilities are deferred; do not relocate enrichment wholesale into Legacy while active admission depends on it.
- Limit changes to relocation, the specified validator separation and necessary imports/path adjustments. Compare destinations and moved definitions with historical Git blobs at B.
- Update directly affected documentation and `director/docs/MIGRATION_INVENTORY.md`, recording actual destinations and remaining transitional dependencies.

## Verification

- Add focused ownership and compatibility regressions covering canonical definitions, retained exports/private imports, object identity and both import orders in fresh subprocesses.
- Verify canonical implementations do not route through their own façades and normal company build/check/publish retains its independence from Legacy.
- Run affected filing JSON/CLI/reconciliation, standardized round-trip, validators, issuer-fiscal, line-identity, share-basis, geographic/operating-KPI and management-KPI admission/identity/reconciliation/history regressions with `/opt/anaconda3/bin/python -m pytest -q`.
- Include validator issue-order/source-binding coverage, normalization-candidate compatibility, affected Driver and calculation tests, build/current-build/CLI contracts, Engine/Trainer compatibility and both company benchmarks.
- Compare B-derived and relocated admission, reconciliation, standardized payloads and provenance using existing fixtures, including rejection paths and deferred disagreements.
- Run `python -m bav` build/check/publish for Lululemon and FastRetailing. Verify canonical outputs, optional Trainer separation and zero-byte research placeholders.
- Compare representative analytical outputs, workbook formulas/dependencies and publication content with B-derived behavior. Reuse earlier evidence only where dependencies remain applicable.
- Apply SESSION native verification when formulas/dependencies or presentation change, using Office Bridge.
- Record the reviewed pre-existing enrichment-sidecar failure separately; do not suppress it, claim a fully passing suite or expand this relocation into its repair.
- Run `git diff --check`. Append measured verification, relocation/split mappings, differences from B and remaining scope to `RESULT.md`.

## Constraints and remaining scope

Preserve signatures, return types, company aliases, public commands, lazy loading, fail-closed behavior, optional JSON dual-output Trainer derivation, all restored compatibility exports and dormant/default-off forecasting.

Preserve canonical source evidence and paths, accounting signs, fiscal distinctions, precision, reconciliations, source and transformation provenance, admission/comparison independence, residual qualifications, filenames and sidecars. Do not rewrite local extracted/reconciled inputs for relocation verification.

Preserve completed Driver handoffs, first-name-wins assessments, CFO classification, attribution amounts and locators, counterfactual scope, `supported_as_attribution`, `not independently verified` and `outside the accounting bridge`. Attribution appendices remain independent of principal selection; accompanying margin prose requires independently selected margin evidence.

Classification/normalization interpretation splits, normalization-candidate separation, enrichment/Legacy decomposition, remaining Director CLI/company orchestration relocation, unrelated removals, test ownership migration and final repository-wide verification remain subsequent work. Do not repair unrelated inventory §16 defects, redesign algorithms or reports, expand Trainer or implement second-phase features.

Preserve ownership/recovery safeguards, protected documents and unrelated dirty work. Cursor must not modify TARGET.md, SESSION.md or IMPLEMENTATION.md.
