# Step 10.8 — Relocate homogeneous Modeler calculations
AUTOCYCLE_PLAN: {"finding_key": "Relocate homogeneous Modeler calculations", "kind": "work", "objective": "Relocate homogeneous Modeler calculations", "plan_id": "fef73b2d9d2d4413a7fae6d94ff3e514", "predecessor_review_sha256": "6a61da1914dd8a4b2e6394dec00fdd4a4239e8e817e2afefb520ffc12d5a9247", "step_id": "10.8", "work_id": "8b681f97ea3e4c4eaab8fad32a8dc593"}

## Completion

The homogeneous calculation modules assigned by inventory §4.4 execute from canonical `modeler/` modules, with callers using those owners and existing compatibility imports, analytical behavior and public `bav` interfaces preserved.

## Bounded work

- Authenticate implementation baseline B from populated `IMPLEMENT_BASE_SHA`, otherwise normal baseline and attempt/checkpoint records; verify branch, ancestry and ownership bindings. Fail closed if authentication is unavailable.
- Relocate the following `core/model/` implementations to `modeler/`, preserving basenames:
  - `classification.py`, `financial_math.py`, `line_resolver.py`, `period_axis.py`, `ratio_values.py`, `source_values.py`, `source_availability.py`, `historical_expected.py`.
  - `normalized_per_share.py`, `revenue_per_store.py`, `geographic_segment.py`, `operating_kpi.py`, `operating_kpi_relationships.py`, `management_kpi.py`.
  - `earnings_quality.py`, `earnings_quality_change.py`, `working_capital.py`, `profitability_drivers.py`, `profitability_change.py`, `roe_attribution.py`, `per_share.py`, `per_share_attribution.py`.
  - `inventory_analysis.py`, `cash_rollforward.py`, `capex.py`, `fixed_asset.py`, `lease_liability.py`, `lease_rou.py`, `lease_repayment.py`, `deferred_tax.py`, `goodwill_intangibles.py`, `acquisition_cash.py`, `share_repurchase.py`, `ownership_attribution.py`.
  - `operating_forecast.py`, `ri_engine.py`; retain their existing dormant/default-off behavior.
- Limit implementation changes to relocation and necessary import/path adjustments. Compare each destination with its historical Git blob at B; record exact moves separately from import-adjusted moves.
- Update runtime consumers, lazy imports and affected tests to use canonical destinations, including Modeler workbook/checking, Driver handoffs and optional Legacy Trainer consumers.
- Retain thin `core.model` compatibility façades for moved modules. Preserve existing importable names, explicit private imports used by current callers/tests, existing `__all__` contracts and canonical object identity. Do not duplicate implementations or introduce a compatibility framework.
- Keep `judgment.py` and `normalization.py` at their current locations pending their inventory-defined Interpreter splits. Adjust imports into moved modules; retain necessary transitional dependencies on these modules and existing data/ingestion owners.
- Preserve the completed `revenue_driver.py`, `reported_margin.py` and `revenue_strategy_synthesis.py` splits; update only references affected by this relocation.
- Update directly affected documentation and `director/docs/MIGRATION_INVENTORY.md` with canonical destinations and remaining transitional dependencies.

## Verification

- Add focused ownership and compatibility regressions covering moved definitions, existing exports, canonical identity and both import orders in fresh subprocesses. Check that canonical calculation modules do not route through their own compatibility façades.
- Run corresponding analytical-family tests using `/opt/anaconda3/bin/python -m pytest -q`, including dormant forecasting and default-off scenario coverage.
- Run affected Driver, reported-margin, revenue-driver, build-contract, current-build, build-CLI, Engine/Trainer ownership and Trainer regressions, plus Lululemon and Fast Retailing benchmark tests.
- Run `build`, `check` and `publish` through `python -m bav` for Lululemon and FastRetailing. Verify canonical output contracts, optional Trainer separation and zero-byte research placeholders.
- Compare representative analytical outputs and workbook formulas/dependencies against B-derived behavior. Reuse prior verification only where its dependencies remain applicable.
- Apply SESSION native verification when workbook formulas/dependencies or presentation change: Office Bridge recalculation and independent saved-cache verification for the former, relevant readability inspection for the latter.
- Run `git diff --check`. Append measured verification, relocation mappings, import-only differences and remaining scope to `RESULT.md`; preserve historical records.

## Constraints and remaining scope

Preserve signatures, return types, company aliases, public commands, lazy loading, fail-closed behavior, optional JSON dual-output Trainer derivation and all 17 restored Engine/Trainer compatibility exports.

Preserve source evidence, accounting signs, fiscal distinctions, precision, reconciliations, provenance, admission/comparison independence, residual qualifications, canonical filenames and sidecars.

Preserve completed Driver handoffs, first-name-wins assessments, CFO classification, attribution amounts and locators, counterfactual scope, `supported_as_attribution`, `not independently verified` and `outside the accounting bridge`. Attribution appendices remain independent of principal selection; accompanying margin prose requires independently selected margin evidence.

Data/ingestion relocation, classification/normalization interpretation splits, unrelated Legacy/removal work, remaining test ownership migration and final repository-wide verification remain subsequent work. Do not repair unrelated inventory §16 defects, redesign algorithms, workbook architecture or reports, expand Trainer or implement second-phase features.

Preserve ownership/recovery safeguards, protected documents and unrelated dirty work. Cursor must not modify TARGET.md, SESSION.md or IMPLEMENTATION.md.
