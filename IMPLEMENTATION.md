# Step 10.7 — Invert Engine and Trainer ownership
AUTOCYCLE_PLAN: {"finding_key": "Invert Engine and Trainer ownership", "kind": "work", "objective": "Invert Engine and Trainer ownership", "plan_id": "3ffdc544eb0f4dbabfe4e33a855a521e", "predecessor_review_sha256": "70ee9928e3667b73430dab12a703d45b9cbc18b64e6dd1a87d7aa9c16765be48", "step_id": "10.7", "work_id": "4ea4f5cca6b144b2b4361a06e030107f"}

## Completion

BAV workbook construction and reusable checking machinery execute under Modeler, build policy under Director and workbook opening presentation under Composer, with optional Trainer derivation and scoring preserved under Legacy and no required Legacy dependency in normal BAV build, check or publication.

## Bounded work

- Authenticate implementation baseline B through populated `IMPLEMENT_BASE_SHA` or normal baseline records, branch, ancestry and attempt/checkpoint bindings. Fail closed if unavailable. Use historical Git blobs at B for relocation comparisons.
- Apply `director/docs/MIGRATION_INVENTORY.md` §10 and the related §4.2 and §7.1 handoffs.
- Move `core/engine/reference_model.py` construction into `modeler/workbook.py`; move `component_catalog.py`, `semantic_map.py` and `map_embed.py` into `modeler/engine/`. Preserve workbook construction behavior and keep deferred forecasting disabled by default.
- Split `core/engine/build_contract.py`: Director owns `BUILD_MODULES` policy in `director/build_contract.py`; Modeler owns preparation, writer registration and execution in `modeler/engine/build_contract.py`. Preserve module ordering, required inputs and deferred statuses without introducing a registry framework.
- Extract `build_bav_workbook` and `TrainingWorkbookGenerator.finalize_bav` from `core/trainer/workbook.py` into `modeler/build_bav.py`. BAV finalization must not instantiate or depend on a Legacy Trainer generator.
- Move `_add_bav_opening` and its presentation helpers into `composer/workbook_opening.py`, preserving existing Overview prose, navigation, fallbacks and completed historical-strategy handoffs.
- Move reusable semantic-map/sidecar I/O into `modeler/semantic_io.py` and live formulas, source-payload embedding and reusable check-context machinery into `modeler/check_context.py`. Keep practice-only behavior with Legacy.
- Relocate Trainer derivation, practice blanking, scoring, chrome and Trainer-only helpers into `legacy/trainer/`. Preserve optional derivation from a completed BAV workbook; avoid substantial Legacy refactoring.
- Update `core/current_build.py`, `core/__main__.py`, affected verification code and other callers to use canonical owners. Normal company build/check/publish must work without loading Trainer implementation. Load Legacy lazily only for explicitly requested Trainer behavior or checking an existing Trainer file.
- Preserve explicit JSON `bav build … -o …` dual-output compatibility through the inventory-defined `legacy/trainer/derive.py` route, consuming Modeler construction.
- Retain only necessary thin compatibility exports at existing import paths; preserve existing callable interfaces and exports without duplicate implementations. Update affected tests and documentation references, and record executed ownership splits in the inventory.

## Verification

- Add focused coverage for canonical imports, retained compatibility exports and both import orders where façades remain.
- Verify normal BAV build/check/publication succeeds with Legacy and `core.trainer` imports unavailable; separately exercise explicit Trainer derivation and optional Trainer checking.
- Run `/opt/anaconda3/bin/python -m pytest -q core/tests/test_build_contract.py core/tests/test_reference_integrity.py core/tests/test_current_build.py core/tests/test_build_cli.py core/tests/test_historical_v1_exit_gate.py core/tests/test_trainer.py core/tests/test_learner_ready_presentation.py core/tests/test_lululemon_benchmark.py core/tests/test_fast_retailing_benchmark.py core/tests/test_publication.py`, following relocated tests where applicable. Run affected live-formula and opening-presentation coverage.
- Run representative `python -m bav build`, `check` and `publish` for both `Lululemon` and `FastRetailing`; confirm normal builds do not derive Trainers.
- Compare generated workbook formulas, dependency relationships, semantic maps, source/context embedding, sheet structure and opening presentation against authenticated baseline behavior. Preserve canonical filenames, sidecars and zero-byte research placeholders.
- Apply SESSION native verification when workbook formulas/dependencies or presentation change: Office Bridge recalculation and independent saved-cache verification for the former, relevant readability inspection for the latter. Reuse earlier evidence only while its dependencies remain applicable.
- Run `git diff --check`. Append measured results, relocation mappings, compatibility coverage and remaining migration scope to `RESULT.md`; preserve historical records.

## Constraints and remaining scope

Preserve public `bav` commands, company aliases, signatures, return types, output contracts, lazy loading and fail-closed behavior. Preserve canonical source evidence, accounting signs, fiscal distinctions, precision, provenance, admission/comparison independence and residual qualifications.

Preserve completed Driver handoffs, first-name-wins assessments, CFO classification, attribution amounts and locators, counterfactual scope, `supported_as_attribution`, `not independently verified` and `outside the accounting bridge`. Retain attribution appendices independently of principal selection; accompanying margin prose requires independently selected margin evidence.

Do not redesign algorithms, workbook architecture or reports, expand Trainer, repair unrelated inventory §16 defects or implement second-phase features. Remaining calculation/data relocations, unrelated Legacy/removal work and final repository-wide migration verification remain subsequent work.

Preserve ownership/recovery safeguards, protected documents and unrelated dirty work. Cursor must not modify TARGET.md, SESSION.md or IMPLEMENTATION.md.
