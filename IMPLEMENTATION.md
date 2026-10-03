# Step 10.16 — Verify representative company behavior and migration acceptance
AUTOCYCLE_PLAN: {"finding_key": "Verify representative company behavior and migration acceptance", "kind": "work", "objective": "Verify representative company behavior and migration acceptance", "plan_id": "fb9a605f00a6445e8d2fa4a6bd6f11fa", "predecessor_review_sha256": "c08e261a6d3ed4fea18d4d80222b098f9c8cbdfb5bd983c729054a982caa6464", "step_id": "10.16", "work_id": "cda6950237df44bfb093c96a57625e6a"}

## Completion

Representative Lululemon and Fast Retailing builds, checks and publications pass under canonical ownership with preserved useful behavior, and every Session migration acceptance criterion has an evidence-backed disposition in RESULT.md.

## Bounded work

- Authenticate execution baseline B from populated `IMPLEMENT_BASE_SHA`, otherwise through normal baseline and bound-attempt mechanisms. Verify branch, ancestry and checkpoint bindings; fail closed if authentication is unavailable.
- Inspect historical Git blobs at B, current canonical destinations and provenance continuity before evaluating current behavior. Reuse completed migration evidence only where its dependencies remain applicable.
- Run the following supported commands with the project interpreter, preserving their outputs and exit statuses:
  - `python -m bav build Lululemon`
  - `python -m bav check Lululemon`
  - `python -m bav publish Lululemon`
  - `python -m bav build FastRetailing`
  - `python -m bav check FastRetailing`
  - `python -m bav publish FastRetailing`
- Verify canonical lowercase output paths, workbook and supporting artifacts, nonempty Drivers Markdown, referenced figures, Word/PDF publication and zero-byte Forecast/Valuation/Overview placeholders.
- Establish that builds preserve canonical upstream inputs, checks validate the generated company outputs, and standalone publication preserves workbook and analytical inputs without requiring Trainer.
- Compare current results with applicable recorded representative evidence. Where regeneration is needed, materialize authenticated B through Git and use equivalent inputs in disposable locations; do not substitute a migration-specific baseline.
- Compare workbook formulas, dependencies, values, provenance and presentation semantically. Identify volatile archive/document metadata explicitly rather than demanding generated binary identity or ignoring unexplained differences.
- Verify public aliases, explicit JSON/Excel routes, atomic failure preservation, optional Trainer derivation/checking and ordinary company-route independence from Legacy using existing regression coverage.
- Assess each SESSION acceptance bullet against `director/docs/MIGRATION_INVENTORY.md`, canonical implementation and applicable verification: complete responsibility dispositions, mixed Driver decomposition, component boundaries, evidence qualifications, Legacy independence, removals, references, branding and preserved behavior.
- Record demonstrated migration defects and unresolved architectural ambiguities for Review. Keep deferred behavior issues separate; do not redesign production behavior during this verification step.

## Verification

- Run `director/tests/test_current_build.py`, `director/tests/test_build_cli.py`, `director/tests/test_engine_trainer_ownership.py`, `modeler/tests/test_build_contract.py`, `composer/tests/test_publication.py` and `legacy/tests/test_trainer.py` with the project interpreter.
- Reuse the reviewed 3548-test regression result only after checking dependency applicability; rerun affected existing suites when current evidence or changes invalidate reuse.
- Changed workbook formulas/dependencies require native recalculation and independent saved-cache verification. Changed presentation requires relevant readability inspection. Native Office work must use Office Bridge and existing access controls.
- Bind any reused native evidence to its actual artifact and dependencies. Later verification must not be represented as proof that an earlier gate ran.
- Use permitted temporary/cache locations. Record access or tooling failures separately from product failures without weakening checks or claiming unavailable evidence.

## Preservation and recording

Preserve source evidence, accounting signs, fiscal distinctions, precision, reconciliations, provenance, residual qualifications, admission/comparison independence, fail-closed controls and default-off normalization admission. Preserve ownership/recovery, provider retry, human adoption, interruption, candidate validation, protected-document, unrelated-dirty-work and Review-cache safeguards.

Git supplies tracked historical preservation; do not recreate obsolete paths, duplicate legacy copies or migration receipts. Do not invent missing source PDFs or revive stale exact-artifact requirements. Protect irreplaceable non-Git evidence through canonical continuity before any removal.

Append measured commands, artifact paths and hashes, comparison results, evidence-reuse justifications, native verification applicability and criterion-by-criterion Session assessment to `RESULT.md`. Preserve historical records and distinguish verified acceptance from unresolved requirements.

Update current verification status in `director/docs/MIGRATION_INVENTORY.md` and `README.md` only as supported by results. Do not introduce second-phase features, new verification infrastructure or unrelated cleanup.

Cursor must not modify TARGET.md, SESSION.md or IMPLEMENTATION.md.
