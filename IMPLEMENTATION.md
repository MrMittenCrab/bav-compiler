# Step 10.7.1 — Restore Engine and Trainer compatibility exports

AUTOCYCLE_PLAN: {"finding_key": "Invert Engine and Trainer ownership", "kind": "work", "minor": 1, "objective": "Restore Engine and Trainer compatibility exports", "plan_id": "5d12a71992dd412e876fd43cc3cbafac", "predecessor_review_sha256": "29872ebc47530c07de1647cf9e95881733017e3b731c9802d4888258bbb1d256", "step_id": "10.7.1", "work_id": "4ea4f5cca6b144b2b4361a06e030107f"}

## Completion

BAV workbook construction and reusable checking machinery execute under Modeler, build policy under Director and workbook opening presentation under Composer, with optional Trainer derivation and scoring preserved under Legacy and no required Legacy dependency in normal BAV build, check or publication.

## Bounded work

- Authenticate implementation baseline B through populated `IMPLEMENT_BASE_SHA` or normal baseline records, branch, ancestry and attempt/checkpoint bindings. Fail closed if unavailable. Use historical Git blobs for export comparisons.
- Restore these exports in `core/engine/build_contract.py` directly from `modeler.engine.build_contract`: `SOURCE`, `CONDENSED`, `DUPONT`, `JUDGMENT`, `OWNERSHIP`, `NORMALIZATION_JUDGMENT`, `NORMALIZATION`, `QUALITY`, `WORKING_CAPITAL`, `PER_SHARE`, `GEOGRAPHIC`, `OPERATING_KPI`, `COMPARABLE_SALES`, `SALES_PER_SQUARE_FOOT`, `REVENUE_PER_STORE`, `REVENUE_DRIVER`.
- Restore `CLEAR_BORDER` in `core/trainer/workbook.py` directly from `modeler.build_bav`.
- Include the restored names in each façade’s `__all__`. Preserve existing exports and canonical object identity; keep definitions with their canonical owners.
- Extend `core/tests/test_engine_trainer_ownership.py` to exercise explicit imports of all 17 restored names through compatibility paths, assert identity with canonical exports and verify `__all__` membership.
- Cover both façade-first and canonical-first import orders in fresh subprocesses for both repaired modules.

## Verification

- Demonstrate that the new compatibility regressions fail before the repair and pass afterward.
- Run `/opt/anaconda3/bin/python -m pytest -q core/tests/test_engine_trainer_ownership.py core/tests/test_build_contract.py core/tests/test_trainer.py`.
- Retain the existing ownership tests covering normal build/check/publication with Legacy and `core.trainer` blocked, plus explicit Trainer derivation and checking.
- Reuse reviewed Step 10.7 relocation, broader regression and representative Lululemon/FastRetailing build/check/publication evidence only while its dependencies remain unchanged. Verify that this repair leaves canonical implementations and runtime callers unchanged.
- Apply SESSION native verification if workbook formulas/dependencies or presentation change: Office Bridge recalculation and independent saved-cache verification for the former, relevant readability inspection for the latter.
- Run `git diff --check`. Append measured results, restored-export coverage and applicable reused evidence to `RESULT.md`; preserve historical records.

## Constraints and remaining scope

Preserve public `bav` commands, company aliases, signatures, return types, output contracts, lazy loading, fail-closed behavior and optional JSON dual-output Trainer derivation. Keep deferred forecasting disabled by default.

Preserve canonical source evidence, accounting signs, fiscal distinctions, precision, provenance, admission/comparison independence, residual qualifications, canonical filenames, sidecars and zero-byte research placeholders.

Preserve completed Driver handoffs, first-name-wins assessments, CFO classification, attribution amounts and locators, counterfactual scope, `supported_as_attribution`, `not independently verified` and `outside the accounting bridge`. Retain attribution appendices independently of principal selection; accompanying margin prose requires independently selected margin evidence.

Keep this continuation limited to compatibility exports, regression coverage and measured result recording. Remaining calculation/data relocations, unrelated Legacy/removal work and final repository-wide migration verification remain subsequent work. Do not redesign algorithms, workbook architecture or reports, expand Trainer, repair unrelated inventory §16 defects or implement second-phase features.

Preserve ownership/recovery safeguards, protected documents and unrelated dirty work. Cursor must not modify TARGET.md, SESSION.md or IMPLEMENTATION.md.
