# Step 10.6.1 — Restore Composer publication compatibility exports

AUTOCYCLE_PLAN: {"finding_key": "Relocate research styling and publication into Composer", "kind": "work", "minor": 1, "objective": "Restore Composer publication compatibility exports", "plan_id": "13619243875e42cc8dcf8b926402cafd", "predecessor_review_sha256": "d97df35ef2dbe70bd3a8fb870ec8a6ab68bb10305db3d50456b6219bfa34cb03", "step_id": "10.6.1", "work_id": "9c134fea34e840dfbe25f98869e28acc"}

## Completion

Research styling, Word/PDF generation and publication execute from their inventory-defined Composer destinations, with updated callers and preserved public interfaces, artifact contracts and presentation behavior.

## Bounded work

- Authenticate implementation baseline B using populated `IMPLEMENT_BASE_SHA` or normal baseline records, branch, ancestry and attempt/checkpoint bindings. Fail closed if unavailable.
- Restore `CELL_INSET_MM`, `CHAR_WIDTH_PT`, `SHORT_IDENTIFIER_CHARS`, `DXA_PER_MM` and `Block` in `core/research/document.py` through explicit imports from `composer.research.document`, including all five names in `__all__`. Keep definitions and implementation solely in Composer.
- Extend `core/tests/test_publication.py` compatibility coverage to explicitly import all five names through the legacy path, assert identity with canonical exports and check their inclusion in `__all__`.
- Exercise the original `from core.research.document import CELL_INSET_MM` import in publication coverage; canonical implementation tests must not substitute for compatibility assertions.
- Extend existing isolated import-order coverage to exercise both façade-first and Composer-first imports, checking restored exports and lazy converter loading.

## Verification

- Run the new compatibility checks before and after repair, recording the missing-export failure and subsequent result.
- Run `/opt/anaconda3/bin/python -m pytest -q core/tests/test_publication.py core/tests/test_research_drivers.py core/tests/test_research_handoff.py core/tests/test_research_emphasis.py core/tests/test_drivers_numeric.py`.
- Confirm the diff is limited to the façade, compatibility tests and appended results; Composer rendering, styling and publication implementations remain unchanged.
- Reuse reviewed relocation, build/check/publish and broader regression evidence only while its dependencies remain applicable. Rerun affected checks if the repair expands beyond exports and tests.
- Apply SESSION native-verification requirements if presentation or workbook formulas/dependencies change; use Office Bridge. Export-only repair does not newly trigger native verification.
- Run `git diff --check`; historical RESULT Markdown hard-break whitespace remains advisory.
- Append restored-export coverage, actual commands/results, applicable reused evidence and remaining scope to `RESULT.md`. Preserve historical records.

## Constraints and remaining scope

Preserve callable signatures, return types, existing exports, company aliases, public `bav` commands, canonical paths, output filenames, lazy loading, publication validation and failure behavior, presentation, figure contracts and zero-byte research placeholders.

Preserve canonical source evidence, accounting signs, fiscal distinctions, precision, provenance, admission/comparison independence, residual qualifications, fail-closed controls, first-name-wins assessments, CFO classification, completed Driver handoffs and optional Trainer behavior.

Preserve attribution amounts, locators, counterfactual scope, `supported_as_attribution`, `not independently verified` and `outside the accounting bridge`. Retain attribution appendices independently of principal selection; accompanying margin prose requires independently selected margin evidence.

Preserve ownership/recovery safeguards, protected documents and unrelated dirty work. No compatibility framework, report redesign, inventory §16 behavior repair or second-phase features.

Engine/Trainer inversion, other component relocation, removals and final repository-wide migration verification remain subsequent work.

Cursor must not modify TARGET.md, SESSION.md or IMPLEMENTATION.md.
