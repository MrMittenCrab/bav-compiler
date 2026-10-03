# Step 11.1.1 — Isolate nested assumption payloads

AUTOCYCLE_PLAN: {"finding_key": "Complete the six-package architectural migration", "kind": "work", "minor": 1, "objective": "Isolate nested assumption payloads", "plan_id": "e31cdb181777494c80abe5790ea80107", "predecessor_review_sha256": "ea5fd4354ced0fab705e5e27515dd3338e262fa0afbe118cfe1ce54a411ad07c", "step_id": "11.1.1", "work_id": "f84fa0b0a013403d9a029c060cec1ed9"}

## Completion

All active BAV implementation belongs to exactly one of the six canonical `bav` components, Core and Interpreter are dismantled without duplicate active implementations or hidden Legacy dependencies, and relevant regressions plus representative Lululemon and Fast Retailing builds, checks and publications pass with useful behavior preserved.

## Bounded repair

- Preserve completed migration work and the existing responsibility inventory. Finish the neutral/stance separation commitment through changes to `bav/inferer/assumptions.py`, `bav/debater/assumptions.py` and their existing assumption tests.
- Authenticate execution baseline B through populated `IMPLEMENT_BASE_SHA`, otherwise normal baseline and bound-attempt records; verify branch, ancestry and checkpoint binding. Fail closed if authentication is unavailable.
- Add failing regressions reproducing nested mutation through `classificationOverrides` and `normalizationCandidates`, including dictionaries and lists within candidate entries.
- Make `AssumptionSet` construction defensively copy nested mutable payload data before applying the existing outer read-only mapping. Cover direct construction and `canonical_neutral_assumptions`; subsequent changes to caller-owned inputs must not change constructed assumptions.
- Ensure `stance_conditioned_assumptions` independently owns nested payloads both when deriving from `base.payload` and when receiving an explicit payload. Mutations to one stance must leave the neutral base, sibling stances and caller-owned inputs unchanged; caller mutations must leave existing sets unchanged.
- Preserve public signatures, origin/stance metadata, neutral-stance rejection, overwrite guards, sidecar keys and existing payload value/container semantics. Keep this a minimal isolation repair without new assumption engines or generic infrastructure.

## Verification and recording

- Run `/opt/anaconda3/bin/python -m pytest -q bav/inferer/tests/test_assumptions.py bav/debater/tests/test_assumptions.py` before and after the repair. Record the reproduced failures and subsequent passes.
- Exercise default and explicit payload routes, direct construction, caller mutation, stance mutation and sibling isolation. Assert nested values remain unchanged across boundaries, alongside existing metadata and outer-mapping protections.
- Run `/opt/anaconda3/bin/python -m pytest -q bav/director/tests/test_current_build.py bav/director/tests/test_build_cli.py bav/director/tests/test_engine_trainer_ownership.py bav/modeler/tests/test_build_contract.py bav/composer/tests/test_publication.py legacy/tests/test_trainer.py`.
- Retain applicable migration, provenance and representative Lululemon/Fast Retailing build/check/publication evidence already reviewed. Confirm dependency applicability before reuse; rerun affected company commands if the repair changes their execution or output behavior.
- Preserve canonical lowercase outputs, analytical and upstream inputs, supporting artifacts, Drivers Markdown, referenced figures, Word/PDF publication and zero-byte research placeholders. Changed formulas/dependencies require native recalculation and independent saved-cache verification; changed presentation requires readability inspection through Office Bridge.
- Append measured regression results, baseline binding, isolation behavior and evidence-reuse justification to `RESULT.md`. Correct the earlier separation claim through a new record; do not rewrite historical records. Update the canonical inventory only where its boundary description needs correction.

Preserve six-package ownership, public interfaces, root `build/` and `legacy/`, optional Trainer independence, accounting signs, fiscal distinctions, precision, reconciliations, provenance, residual qualifications, admission/comparison independence, default-off normalization admission and fail-closed controls. Retain normal ownership/recovery, protected-document and unrelated-dirty-work safeguards. Sophisticated Inferer/Debater engines, new methods, LLM workflows and unrelated refactoring remain excluded.

Cursor must not modify TARGET.md, SESSION.md or IMPLEMENTATION.md.
