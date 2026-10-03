# Step 11.1 — Complete the six-package architectural migration

AUTOCYCLE_PLAN: {"finding_key": "Complete the six-package architectural migration", "inputs": [{"commitment": "Amend TARGET and Session 11 Endpoint/Priority to the six canonical bav packages; inventory every responsibility before movement, split Interpreter and Core by decision type, migrate implementation and references, preserve root Build/Legacy and required tooling, and verify representative behavior and architectural acceptance. This step covers the structural migration; sophisticated Inferer/Debater engines and other feature development remain excluded.", "id": "20261003-120058-000000026"}], "kind": "work", "objective": "Complete the six-package architectural migration", "plan_id": "7c19dc90f52d4ffc96c98e61733e9253", "predecessor_review_sha256": "0dc7f74858f929402997806574267473994059677e4b4a390b85ee3ad272a8e4", "step_id": "11.1", "work_id": "f84fa0b0a013403d9a029c060cec1ed9"}

## Completion

All active BAV implementation belongs to exactly one of the six canonical `bav` components, Core and Interpreter are dismantled without duplicate active implementations or hidden Legacy dependencies, and relevant regressions plus representative Lululemon and Fast Retailing builds, checks and publications pass with useful behavior preserved.

## Inventory and preservation

- Authenticate implementation baseline B from populated `IMPLEMENT_BASE_SHA`, otherwise through normal baseline and bound-attempt mechanisms; verify branch, ancestry and checkpoint binding, failing closed if authentication is unavailable.
- Inspect the complete repository, including tracked and untracked material, hidden tooling, `bav/`, `core/`, `interpreter/`, top-level components, Driver/research, root Markdown and Trainer remnants.
- Before moving code, update `director/docs/MIGRATION_INVENTORY.md` with responsibility-level dispositions: Director / Extractor / Modeler / Inferer / Debater / Composer / Legacy / Remove / Runtime-tooling. Record source paths, symbols for mixed files, canonical destinations, dependencies and ambiguities; retain applicable historical evidence without treating obsolete ownership as authoritative.
- Inspect AutoCycle path requirements before considering control-file relocation. Retain `TARGET.md`, `SESSION.md`, `IMPLEMENTATION.md` and `RESULT.md` at root; record why each other root file must remain.
- Compare tracked relocations with Git blobs at authenticated B and preserve provenance continuity. Git retains removed historical bytes; do not create migration backups or duplicate legacy copies. Verify surviving canonical content before removing irreplaceable non-Git evidence.

## Ownership and relocation

- Establish `bav/director/`, `bav/extractor/`, `bav/modeler/`, `bav/inferer/`, `bav/debater/` and `bav/composer/`. Keep package initialization and `python -m bav` entry wiring minimal, with routing owned by Director.
- Split each Interpreter responsibility rather than renaming the directory: neutral assumptions, plausibility and neutral uncertainty → Inferer; historical/forecast/scenario/valuation arithmetic and deterministic tests → Modeler; position-conditioned assumptions, thesis logic, evidence selection, counterarguments, rebuttals and weaknesses → Debater; prose and publication presentation → Composer; orchestration/policy → Director; obsolete work → Legacy or Remove.
- Inspect `interpreter/{selection,historical_strategy,revenue_driver,reported_margin,classification_judgment,normalization}.py` and mixed Composer/Driver code by actual decision type. Preserve evidence qualifications and useful behavior while separating analytical decisions from wording.
- Dissolve Core by the same ownership rules, including Extractor ownership of source/provenance handling. Remove obsolete façades and internal `core` routing after migrating callers; do not replace Core with another generic implementation layer or move it wholesale into Director.
- Relocate active top-level components, tests, scripts, fixtures and specifications into their canonical owners. Move the inventory, STYLE.md and other system-wide specifications into `bav/director/docs/`; remove duplicate active old paths.
- Keep Modeler responsible for the complete quantitative model and explicit-assumption consequences. Keep management guidance attributed evidence. Preserve distinctions among reported fact, management view, historical tendency, inferred assumption and uncertainty.
- Retain explicit origin and stance for assumption sets; prevent Debater paths from silently overwriting canonical neutral/base assumptions. Debater may consume Extractor/Modeler directly. Establish only minimal boundaries and safeguards needed by existing behavior; do not invent research workflows.
- Keep `build/` and `legacy/` at root. Inspect `requirements-trainer.txt`: retain active dependencies in justified packaging/tooling configuration, and move Trainer-only requirements to Legacy or remove unused remnants.
- Update imports, exports, CLI routing, resource and repository-root discovery, packaging if required, tests, documentation, build paths and publish paths. Keep a minimal root README documenting public use and linking canonical specifications.

## Verification and recording

- Verify no active Core, Interpreter, generic shared layer, parallel root implementation or hidden Legacy dependency remains. Audit dynamic imports, resource paths and tests as well as static imports.
- Run relevant migrated regression suites, including the successors of `director/tests/test_current_build.py`, `director/tests/test_build_cli.py`, `director/tests/test_engine_trainer_ownership.py`, `modeler/tests/test_build_contract.py`, `composer/tests/test_publication.py` and `legacy/tests/test_trainer.py`; retain behavioral assertions while replacing obsolete ownership expectations.
- Cover numerical and provenance preservation, neutral/stance separation, public aliases, explicit JSON/Excel routes, atomic failure preservation, optional Trainer behavior and ordinary company-route independence from Legacy.
- With the project interpreter, run `python -m bav build Lululemon`, `python -m bav check Lululemon`, `python -m bav publish Lululemon`, and the same three commands for `FastRetailing`.
- Verify canonical lowercase output paths, workbook/supporting artifacts, nonempty Drivers Markdown, referenced figures, Word/PDF publication and zero-byte Forecast/Valuation/Overview placeholders. Confirm builds preserve upstream inputs and publication preserves workbook and analytical inputs.
- Evaluate preservation from authenticated B, historical blobs, canonical destinations and provenance before current behavior. Compare generated outputs semantically; explain volatile metadata and reuse earlier evidence only where dependencies remain applicable.
- Changed workbook formulas/dependencies require native recalculation and independent saved-cache verification; changed presentation requires readability inspection. Native Office work uses Office Bridge and existing access controls. Do not claim unavailable evidence or that later verification proves an earlier gate ran.
- Append measured verification, responsibility mapping, Interpreter/Core splits, intentional root retention, removed functionality, preservation comparisons and unresolved ambiguities to `RESULT.md`; update the canonical inventory with current evidence.

Preserve accounting signs, fiscal distinctions, precision, reconciliations, provenance, residual qualifications, admission/comparison independence, default-off normalization admission, fail-closed controls and normal ownership/recovery safeguards. Do not rewrite working quantitative logic unnecessarily, add methods or LLM workflows, redesign Extractor/Composer, expand Trainer or cosmetically refactor Legacy. Stop after structural migration.

Cursor must not modify TARGET.md, SESSION.md or IMPLEMENTATION.md.
