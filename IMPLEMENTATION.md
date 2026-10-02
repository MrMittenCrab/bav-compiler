# Step 10.4.1 — Director-owned historical-strategy interpretation

AUTOCYCLE_PLAN: {"finding_key": "Split Driver assessment calculations, judgments and wording", "kind": "work", "minor": 1, "objective": "Director-owned historical-strategy interpretation", "plan_id": "2b3133c3ba5e4c4caae9c727c827e416", "predecessor_review_sha256": "b032a459ef13d5eb8abc3d0bc9bee0b921ee523c24556e945321e0b81e99cfc0", "step_id": "10.4.1", "work_id": "b0acea18798147eb824094bee2a60f09"}

## Completion

Revenue-driver analysis, reported-margin assessments and historical-strategy synthesis execute through their inventory-defined Modeler, Interpreter and Composer owners, preserving existing numerical results, judgments, evidence qualifications and rendered behavior through thin orchestration.

## Bounded work

Repair the historical-strategy handoff in `director/driver_assessment.py` and `composer/overview.py`, following `director/docs/MIGRATION_INVENTORY.md` §7.1.

- Authenticate implementation baseline B from populated `IMPLEMENT_BASE_SHA`, otherwise normal baseline records and branch, ancestry and attempt/checkpoint bindings. Fail closed if unavailable; use historical Git blobs for comparisons.
- Have `complete_historical_strategy_synthesis` obtain completed revenue-driver analysis when needed, invoke `interpret_historical_strategy`, then pass the completed `HistoricalStrategyJudgment` and analysis to Composer.
- Make Composer require completed judgments explicitly. Remove its interpretation invocation and any fallback that computes judgments or revenue analysis. Retain Interpreter-owned judgment types and constants where composition needs them.
- Keep applicability and empty-test failures consistent with existing entry-point behavior, including validation order and messages.
- Update affected callers and tests. Preserve the delegating `core/model/revenue_strategy_synthesis.py` façade, research consumers and workbook-opening behavior through Director.
- Preserve all synthesis fields, wording, source locators, qualifications, counterexamples, deferred-SPSF handling, theme order, navigation and fallback text. Keep judgment decisions in Interpreter and wording in Composer.
- Retain the completed revenue and margin splits, numeric consumer boundaries, assessment ordering and first-name-wins deduplication. Update only narrowly affected documentation.

## Verification

- Add focused regressions proving Director invokes historical-strategy interpretation before composition, passes its completed judgment unchanged, and avoids recomputing supplied analysis.
- Verify Composer can render supplied judgments without invoking Interpreter or Modeler computations; cover both supplied-analysis and omitted-analysis orchestration paths.
- Compare complete synthesis records and rendered output against authenticated baseline behavior, including supported, mixed, contradicted, insufficient, counterexample and deferred-evidence cases represented by existing fixtures.
- Retain checks that Modeler does not import Interpreter or Composer, Interpreter does not import Composer or parse its prose, and numeric workbook consumers do not invoke assessment wording.
- Run `/opt/anaconda3/bin/python -m pytest -q` on `core/tests/test_revenue_driver.py`, `core/tests/test_reported_margin.py`, `core/tests/test_research_drivers.py`, `core/tests/test_current_build.py`, `core/tests/test_build_contract.py`, `core/tests/test_build_cli.py`, `core/tests/test_publication.py`, `core/tests/test_lululemon_benchmark.py`, `core/tests/test_fast_retailing_benchmark.py`, `core/tests/test_trainer.py` and `core/tests/test_learner_ready_presentation.py`.
- Verify `python -m bav --help` and `git diff --check`.
- Apply SESSION native-verification requirements if workbook formulas/dependencies or presentation change; use Office Bridge and record unavailable verification explicitly.
- Append the repaired responsibility handoff, measured verification and remaining migration scope to `RESULT.md`. Preserve historical records.

## Limits and remaining scope

Preserve canonical inputs, source evidence, accounting signs, fiscal distinctions, precision, admission/comparison independence, residual qualifications, fail-closed controls, optional Trainer behavior and zero-byte research placeholders. Preserve ownership, recovery, protected-document and unrelated-dirty-work safeguards.

The broader `drivers.py`/`selection.py` split, management-emphasis eligibility correction, remaining component relocation, Trainer inversion, justified removals and final representative build/check/publication verification remain subsequent work. Do not repair inventory §16 behavior defects or implement second-phase features.

Cursor must not modify TARGET.md, SESSION.md or IMPLEMENTATION.md.
