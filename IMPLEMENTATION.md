# Step 10.13 — Relocate remaining Legacy functionality and references
AUTOCYCLE_PLAN: {"finding_key": "Relocate remaining Legacy functionality and references", "kind": "work", "objective": "Relocate remaining Legacy functionality and references", "plan_id": "07c9bd93061c439fbe0a6046baf1520e", "predecessor_review_sha256": "fe1909d1f7584b501dc2ecd030c02fa97457b924f82e3b8ba31a8eabbba44fd6", "step_id": "10.13", "work_id": "01a325c7ed794dcbbcc0167a74c9d572"}

## Completion

Inventory-designated Legacy functionality and supporting assets reside under their assigned Legacy categories, with working references and preserved useful behavior, while ordinary BAV company execution remains independent of Legacy.

## Bounded work

Follow `director/docs/MIGRATION_INVENTORY.md` §§4.6–4.11, 10 and 13–14. Retain completed Trainer, ingestion and enrichment relocations; move only remaining Legacy material.

- Relocate coverage automation to `legacy/automation/` and `automation/autocycle-fixes/` to `legacy/autocycle-fixes/`. Preserve controller patches as historical assets; do not apply them or alter installed AutoCycle.
- Relocate repository skills and their fixtures/references to `legacy/skills/`, plugin metadata to `legacy/plugin/`, and the packaging script to `legacy/build_plugin_zip.sh`. Retain one existing archive at `legacy/bav-pipeline-plugin.zip`.
- Relocate retired release builders, benchmark/reference audit scripts and PDF text-cache extraction to `legacy/scripts/`; place `requirements-benchmark.txt` alongside its extraction helper.
- Relocate historical workbook verifiers and `docs/native-excel-*.json` to `legacy/verification/`. Preserve SHA bindings and independent expectations; relocation does not refresh native verification.
- Relocate the Trainer guide, GOOGL reference, historical Excel diagnosis/resume notes and `docs/superpowers/specs/` under `legacy/docs/`, preserving useful substructure.
- Relocate the five inventory-listed HK/GOOGL example JSON/workbook assets to `legacy/example/`, preserving their bytes.
- Update imports, repository-root discovery, resource paths, script defaults, packaging inputs, installation templates, test fixtures and current documentation links affected by these moves. Keep the packaged plugin’s expected internal layout.
- Update `legacy/README.md` and the migration inventory with actual destinations and retained entry points. Preserve historical RESULT records and distinguish historical commands from current instructions.

Keep existing compatibility interfaces where required by public behavior. Do not add forwarding layers for retired script paths without a demonstrated caller. Leave canonical company inputs, outputs and archived local evidence at their existing locations.

## Preservation

Authenticate execution baseline B using populated `IMPLEMENT_BASE_SHA`, otherwise the normal baseline and bound-attempt mechanisms. Verify branch, ancestry and checkpoint bindings; fail closed if authentication is unavailable.

Inspect historical Git blobs at B before comparing canonical destinations. Record old-to-new mappings, byte identity for unchanged assets and explicit path/import changes for modified files. Git preserves tracked history; no duplicate legacy copies or migration receipts are required.

Preserve non-Git irreplaceable evidence through verified canonical continuity before removing its old copy. Preserve source immutability, protected outputs, staged verification, sidecars, atomic replacement, rollback and provenance.

Preserve CLI aliases, patchable configuration, explicit JSON/Excel routes, optional Trainer behavior, analytical results, residual qualifications, dormant forecasting and zero-byte research placeholders. Retain normalization admission’s default-off behavior, fingerprint/adoption/treatment/authorization gates, once-only conversion, lifecycle rejection coverage and 11-observation round trips.

Remove dispositions, broader test ownership migration, product-wide branding and final Session verification remain subsequent scope. Do not redesign Legacy, expand features or alter active analytical algorithms.

## Verification and recording

- Run affected existing Trainer, ingestion, learner-presentation, cached-workbook verifier, reference-audit, CLI and company-orchestration tests. Update path assumptions without weakening assertions.
- Check relocated Python/shell entry points and plugin packaging in disposable locations; inspect archive members and resource resolution. Do not install automation, launch services or invoke external coverage workflows.
- Verify ordinary company build/check/publication routes still avoid Legacy imports. Reuse the reviewed representative comparison only while its dependencies remain unchanged; rerun affected representative paths if relocation changes their dependencies.
- Preserve binary workbook assets exactly. Apply SESSION’s Office Bridge requirements if formulas/dependencies or presentation change; historical SHA-bound records do not substitute for current native verification.
- Run `git diff --check` and the corresponding comparison against authenticated B.
- Append relocation mappings, intentional edits, measured verification and remaining Session scope to `RESULT.md`. Preserve ownership/recovery, provider retry, human adoption, interruption, candidate validation, protected-document, unrelated-dirty-work and Review-cache safeguards.

Cursor must not modify TARGET.md, SESSION.md or IMPLEMENTATION.md.
