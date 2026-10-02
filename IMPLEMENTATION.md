# Step 10.5 — Split Driver research responsibilities and correct emphasis eligibility
AUTOCYCLE_PLAN: {"finding_key": "Split Driver research responsibilities and correct emphasis eligibility", "kind": "work", "objective": "Split Driver research responsibilities and correct emphasis eligibility", "plan_id": "d39ef10d44b34d40b7b2d9a35dc3cb63", "predecessor_review_sha256": "b8a4fec20aab39a4a9a784aa06cef2d4bf476d2ae95ab97c11ee030bcd6b0aae", "step_id": "10.5", "work_id": "116fc09cee884ccea734dfb368f42fa2"}

## Completion

Driver research executes through inventory-defined Modeler calculations, Interpreter judgments and Composer publication decisions under thin Director orchestration; management emphasis alone never establishes driver eligibility, and numerical support, provenance and evidence qualifications remain intact.

## Bounded work

Split `core/research/drivers.py` and `core/research/selection.py` according to `director/docs/MIGRATION_INVENTORY.md` §§5–6 and 9.

- Authenticate implementation baseline B through resume-state or normal baseline records, branch, ancestry and attempt/checkpoint bindings. Fail closed if unavailable; compare against historical Git blobs.
- Move CFO classification to `modeler/research/cfo.py`, numerical assembly to `modeler/research/drivers_view.py`, geographic conditions to `modeler/research/geo_conditions.py` and mechanical eligibility to `modeler/research/eligibility.py`.
- Make Modeler assembly return numerical observations without invoking selection, interpretation, Composer or Director. Obtain completed assessments through Director and supply them explicitly where needed; preserve first-name-wins assessment assembly.
- Move question judgments, claim classifications, mechanisms, alternatives, uncertainty, calendar limitations and economic eligibility gates to `interpreter/selection.py`. Preserve existing thresholds and independently evaluated geographic conditions.
- Move Driver wording, Markdown, figures and publication helpers to `composer/research/drivers.py`; place publication constants in `composer/research/selection_roles.py` and role/order selection in `composer/research/selection.py`.
- Separate mixed question builders by field ownership in inventory §6. Composer owns claim wording, display formatting, publication reasons and exhibit questions; Interpreter must not infer judgments from Composer prose or publication roles.
- Reuse `DriversView`, `ResearchClaim`, `ResearchQuestion`, `ResearchSelection` and `SelectionDecision`; keep their contracts thin and avoid a new reasoning schema. Locate shared records so their imports do not pull downstream implementation into Modeler.
- Add thin orchestration in `director/research.py`: obtain calculations and completed assessments, assemble the view, invoke Interpreter, invoke Composer selection, then attach the completed selection with `replace(view, selection=…)`.
- Require completed selection at Composer rendering and figure-selection boundaries. Remove fallback interpretation from rendering helpers; route existing public convenience calls through Director.
- Preserve margin → geography → footprint → cash ordering, independent eligibility gates, figure deduplication, report headings, appendix structure and source navigation.
- Stop assigning main-body eligibility merely because management attribution or comparable-sales observations exist. Keep attribution claims, amounts, locators, counterfactual scope, `supported_as_attribution`, `not independently verified` and `outside the accounting bridge`.
- Retain the attribution appendix table regardless of principal selection. Include attributed margin prose only beside an independently selected margin finding; attribution must not independently create a principal or figure. Comparable-sales observations remain auditable without automatic promotion.
- Consolidate duplicate reconstruction and component-direction helpers under their inventory-defined owners. Remove only the dead Driver symbols identified in §5.1 after confirming no callers.
- Update affected build, publication, verification and test imports. Any retained `core/research` façades must delegate without calculations, judgments or wording. Update the inventory and narrowly affected documentation to reflect actual ownership.

## Verification

- Add focused handoff tests proving Modeler assembly does not select arguments, Director sequences interpretation before publication selection, and Composer consumes completed judgments without recomputing them.
- Test qualitative and quantified attribution with missing, zero and nonzero margin movement: evidence survives, emphasis alone cannot promote eligibility, and accompanying prose requires independently selected margin evidence.
- Test comparable-sales presence without independent driver support, and independence of valid geographic/store/margin evidence from management disclosure presence.
- Compare numerical fields, judgments, qualifications, Markdown and figure selection with authenticated baseline behavior across Lululemon, Fast Retailing and existing missing/zero, partial-reconstruction, geographic-offset, calendar and cash fixtures. Isolate intentional emphasis-related differences.
- Preserve regression coverage while splitting research tests by responsibility. Check import boundaries, reconstruction gates, CFO classification, source locators, residuals, assessment ordering and zero-byte placeholders.
- Run `/opt/anaconda3/bin/python -m pytest -q` on the affected research tests and `core/tests/test_revenue_driver.py`, `core/tests/test_reported_margin.py`, `core/tests/test_current_build.py`, `core/tests/test_build_contract.py`, `core/tests/test_build_cli.py`, `core/tests/test_publication.py`, `core/tests/test_lululemon_benchmark.py`, `core/tests/test_fast_retailing_benchmark.py`, `core/tests/test_trainer.py` and `core/tests/test_learner_ready_presentation.py`.
- Verify `/opt/anaconda3/bin/python -m bav --help` and `git diff --check`.
- Apply SESSION native-verification requirements when presentation or workbook formulas/dependencies change. Use Office Bridge; record unavailable verification explicitly.
- Append actual ownership changes, intentional behavioral differences, measured verification and remaining migration scope to `RESULT.md`.

## Limits and remaining scope

Preserve canonical inputs, source evidence, accounting signs, fiscal distinctions, precision, admission/comparison independence, fail-closed controls, optional Trainer behavior and ownership/recovery safeguards. Protect unrelated dirty work and protected documents.

Remaining component relocation, Trainer inversion, broader removals and final representative build/check/publication verification remain subsequent work. Do not repair inventory §16 behavior defects, redesign reports or implement second-phase features.

Cursor must not modify TARGET.md, SESSION.md or IMPLEMENTATION.md.
