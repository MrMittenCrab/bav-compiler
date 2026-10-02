# Step 10.4 — Split Driver assessment calculations, judgments and wording
AUTOCYCLE_PLAN: {"finding_key": "Split Driver assessment calculations, judgments and wording", "kind": "work", "objective": "Split Driver assessment calculations, judgments and wording", "plan_id": "a32e38ca62b94e2b8e59edbf0170c54b", "predecessor_review_sha256": "51ad4a2f7115b3fd0c9e41bb34159cdca42c5946923906d221f56841cec074d1", "step_id": "10.4", "work_id": "b0acea18798147eb824094bee2a60f09"}

## Completion

Revenue-driver analysis, reported-margin assessments and historical-strategy synthesis execute through their inventory-defined Modeler, Interpreter and Composer owners, preserving existing numerical results, judgments, evidence qualifications and rendered behavior through thin orchestration.

## Bounded work

Implement `director/docs/MIGRATION_INVENTORY.md` §§7.0, 7.1 and 7.4, including their field producers, branch precedence and caller handoffs.

- Authenticate implementation baseline B using populated `IMPLEMENT_BASE_SHA`, otherwise normal baseline records, branch, ancestry and attempt/checkpoint bindings. Fail closed if unavailable; compare against historical Git blobs at B.
- Split `core/model/revenue_driver.py` into `modeler/revenue_driver.py`, `interpreter/revenue_driver.py` and `composer/revenue_driver.py`. Follow the inventory’s symbol map for observations, identities, verdicts, requirements, qualifications and wording.
- Split `core/model/reported_margin.py` into `modeler/reported_margin.py`, `interpreter/reported_margin.py` and `composer/reported_margin.py`. Keep the existing assessment contract and KIND constants with Modeler; preserve all six assessment branches and their guards.
- Keep identity `kind` and residual-based `established` decisions in Modeler. Preserve Modeler’s disclosure-presence and latest-pair availability flags; Interpreter owns claim typology, recurrence, contradiction classes and unsupported causal judgments. Composer copies these decisions unchanged into existing sentences.
- Split `core/model/revenue_strategy_synthesis.py` between `interpreter/historical_strategy.py` and `composer/overview.py`; move applicability beside Modeler’s revenue-driver applicability. Replace counterexample and deferred-SPSF prose scanning with the inventory-defined flags and codes.
- Preserve current wording, labels, formatting, source locators, hypothesis/mechanism content, fallback text and evidence qualifications. Keep semantic handoffs limited to existing needs; do not introduce a reasoning framework.
- Sequence numeric computation, interpretation and wording through thin Director-owned orchestration. Retain temporary delegating façades at existing entry points only where unmigrated callers require them; façades must not contain analytical decisions or wording implementations.
- Update affected consumers in `core/research/drivers.py`, `core/engine/reference_model.py`, `core/engine/historical_expected.py`, `core/engine/component_catalog.py` and `core/trainer/`. Numeric consumers use Modeler directly; narrative consumers receive completed records through orchestration.
- Supply completed analysis to historical-strategy composition and workbook opening; Composer must not initiate hidden analytical tests. Preserve existing entry-point behavior through orchestration where needed.
- Preserve revenue theme order, margin branch append order and first-name-wins assessment deduplication. Collection assembly must not become another judgment producer.
- Update affected imports and narrowly relevant documentation. Keep unmoved dependencies at their current paths and tests at existing locations for this step.

## Verification

- Compare split implementations against B for numerical algorithms, thresholds, branch decisions, exceptions, provenance and existing rendered strings.
- Add focused regressions for phase boundaries, unchanged decision flags through wording, structured counterexamples/deferred evidence, and assessment ordering where existing coverage is insufficient.
- Verify Modeler does not import Interpreter or Composer, Interpreter does not import Composer or parse its prose, and numeric workbook consumers do not invoke assessment wording.
- Run `/opt/anaconda3/bin/python -m pytest -q` on `core/tests/test_revenue_driver.py`, `core/tests/test_reported_margin.py`, `core/tests/test_research_drivers.py`, `core/tests/test_current_build.py`, `core/tests/test_build_contract.py`, `core/tests/test_build_cli.py`, `core/tests/test_publication.py`, `core/tests/test_lululemon_benchmark.py`, `core/tests/test_fast_retailing_benchmark.py`, `core/tests/test_trainer.py` and `core/tests/test_learner_ready_presentation.py`.
- Verify `python -m bav --help` and `git diff --check`.
- Apply SESSION native-verification requirements when workbook formulas/dependencies or presentation change; use Office Bridge. Record unavailable verification explicitly.
- Append responsibility mappings, retained façades, measured verification and remaining migration scope to `RESULT.md`.

## Limits and remaining scope

Preserve canonical inputs, source evidence, accounting signs, fiscal distinctions, precision, admission/comparison independence, residual qualifications, fail-closed controls, optional Trainer behavior and zero-byte research placeholders. Preserve ownership, recovery, protected-document and unrelated-dirty-work safeguards.

The broader `drivers.py`/`selection.py` split, management-emphasis eligibility correction, remaining component relocation, Trainer inversion, justified removals and final representative build/check/publication verification remain subsequent work. Do not repair inventory §16 behavior defects or implement second-phase features.

Cursor must not modify TARGET.md, SESSION.md or IMPLEMENTATION.md or rewrite historical RESULT records.
