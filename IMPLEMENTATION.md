# Step 10.12 — Relocate CLI and company orchestration
AUTOCYCLE_PLAN: {"finding_key": "Relocate CLI and company orchestration", "kind": "work", "objective": "Relocate CLI and company orchestration", "plan_id": "7e4f1716a5944d429af75a2602fcca8e", "predecessor_review_sha256": "686d8daace7cd919ffae15c3f65fc137b9ee3041fe4eb7ec6941295496096bc0", "step_id": "10.12", "work_id": "889f7a7b0342467caa4faf6315b52b88"}

## Completion

Director owns CLI routing, company configuration and company build/check/publication orchestration, with mechanical build status owned by Modeler, while public interfaces and existing execution behavior remain preserved.

## Bounded work

Implement the remaining CLI/company dispositions in `director/docs/MIGRATION_INVENTORY.md` §4.2.

- Move `core/__main__.py` orchestration to `director/cli.py`; route `bav/__main__.py` directly to Director and preserve `python -m core` as a compatibility entry point.
- Move `core/current_build.py` to `director/current_build.py` and `core/project_companies.json` to `director/project_companies.json`. Preserve configuration bytes, aliases, admission settings, fixture references and repository-relative input/output resolution.
- Move `core/build_status.py` to `modeler/build_status.py`; update `modeler/build_bav.py` and company orchestration to consume that owner.
- Retain thin Python compatibility façades at displaced module paths, preserving public names, required private helpers and canonical object identity. Preserve existing patchable company configuration and failure-injection behavior without duplicate orchestration implementations.
- Update active callers, including `composer/research/document.py`, to canonical owners. Retarget lazy intra-orchestration imports, especially `build_company`’s output-validation call, without introducing import cycles.
- Keep existing Director build-contract policy and Modeler execution ownership intact. Retain canonical Legacy Trainer derivation and manual ingestion only on their existing explicit compatibility routes.
- Update affected inventory entries, build-contract documentation and touched package descriptions to reflect actual ownership and BAV Compiler identity.

## Preservation

Preserve command names, arguments, defaults, help, diagnostics, exit behavior, company aliases and explicit JSON/Excel output behavior.

Preserve strict standardized-only company preparation, protected-output checks, source immutability, staged verification, sidecar placement, atomic exchange, failure rollback and retirement only after successful replacement.

Preserve existing Modeler/Interpreter/Composer sequencing, analytical results, workbook formulas and presentation, publication contents, provenance, residual qualifications, dormant forecasting and zero-byte research placeholders. Ordinary company execution remains independent of Legacy; optional Trainer checks retain their existing conditional behavior.

Retain normalization fingerprint, adoption, treatment, authorization, persistence and once-only conversion gates, isolated baseline comparisons, lifecycle rejection fixtures and all 11-observation round trips. Admission remains default-off and independent of ordinary reconciliation and comparison.

Do not redesign CLI behavior, analytical algorithms, ingestion, reports or workbook architecture. Broader Legacy migration, Remove dispositions, repository-wide test relocation and final Session verification remain separate work.

## Verification and recording

- Authenticate implementation baseline B from populated `IMPLEMENT_BASE_SHA`, otherwise normal baseline and bound-attempt mechanisms; verify branch, ancestry and attempt bindings and fail closed if unavailable. Keep controller evidence read-only.
- Inspect historical Git blobs at B before comparing canonical destinations. Record preserved relocation bytes and intentional import/path changes; preserve normal provenance without retaining duplicate configuration.
- Extend existing CLI/company ownership coverage for canonical definitions, compatibility identities, patchable configuration, fresh-process import orders and both module entry points.
- Exercise company routes with Legacy imports rejected; separately retain explicit manual/Excel ingestion, JSON Trainer derivation and optional Trainer checks.
- Preserve tests covering protected inputs, ambiguous aliases, missing inputs, staged verification failure, atomic exchange failure and unchanged current output after failed builds.
- Run `/opt/anaconda3/bin/python -m pytest -q core/tests/test_build_cli.py core/tests/test_filing_cli.py core/tests/test_current_build.py core/tests/test_build_contract.py core/tests/test_publication.py core/tests/test_data_ingestion_ownership.py core/tests/test_engine_trainer_ownership.py core/tests/test_trainer.py core/tests/test_reference_integrity.py core/tests/test_cross_company_robustness.py core/tests/test_lululemon_benchmark.py core/tests/test_fast_retailing_benchmark.py`.
- Verify representative Lululemon and FastRetailing build/check/publication behavior through existing integration routes, comparing relevant outputs with B. Do not weaken, skip, deselect or xfail preserved gates.
- Apply SESSION’s Office Bridge requirements if workbook formulas/dependencies or presentation change; reuse prior verification only while dependencies remain applicable.
- Run `git diff --check` and the corresponding diff check against authenticated B.
- Append baseline bindings, ownership/path mappings, measured verification and unresolved defects to `RESULT.md`; preserve historical records and distinguish this Completion from Session acceptance.

Preserve ownership/recovery, provider retry, human adoption, interruption, candidate validation, protected-document, unrelated-dirty-work and Review-cache safeguards. Cursor must not modify TARGET.md, SESSION.md or IMPLEMENTATION.md.
