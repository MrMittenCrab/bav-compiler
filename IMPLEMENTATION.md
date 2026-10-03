# Step 10.14 — Execute inventory-designated Remove dispositions
AUTOCYCLE_PLAN: {"finding_key": "Execute inventory-designated Remove dispositions", "kind": "work", "objective": "Execute inventory-designated Remove dispositions", "plan_id": "929ee92e950e43b5ae91c8a191dfbcdf", "predecessor_review_sha256": "da85d9a5559667dfac6635ff3251d93bf0fc6f141b49eaa7fd5ce04991ee222f", "step_id": "10.14", "work_id": "5aa7273b08304f909042b1d1efecd98e"}

## Completion

Inventory-designated Remove material is removed, with required source evidence, retained Legacy behavior and public BAV interfaces preserved, and affected references and regressions verified.

## Bounded work

Follow `director/docs/MIGRATION_INVENTORY.md` §§4.1, 4.6, 4.10, 4.12 and 13. Confirm current callers and contents before deleting each item.

- Delete `scripts/build_fast_retailing_source_facts.py` and `core/ingestion/future_adapters.py`; update current documentation that presents them as available functionality.
- Confirm `FIGURE_NAMES`, `FIGURE_PLOTTERS` and `_calendar_limit_block` are already removed; remove only remaining unused definitions, without changing live rendering.
- Remove empty `benchmark/`, `release/` and `build/input/lululemon/evidence/stale-benchmark-reconciled/` directories after checking their contents.
- Remove `build/input/fast_retailing/evidence/_extract/*.txt` after confirming they are regenerable caches and no retained workflow requires those copies.
- Remove leftover generated `example/rowmap.json`, `example/DEMO_HK_Answer_Key.assumptions.json` and `example/DEMO_HK_Answer_Key.component_map.json`. Do not generalize deletion to canonical assumptions or retained fixtures.
- Remove repository-owned `__pycache__/`, `.pytest_cache/` and `.DS_Store` artifacts within the inventoried areas. Exclude Git/controller state, environments and unrelated work; regenerated runtime caches need not remain absent after verification.
- Update the inventory and `legacy/README.md` to record actual removals and retained destinations. Correct affected current references without rewriting historical records.

Retain required compatibility façades, the Director `validate_standardized` contract, one `legacy/bav-pipeline-plugin.zip`, retained Legacy assets and historical verification records. Do not introduce replacement adapters, forwarding layers or a `remove/` directory.

Broader test ownership migration, remaining repository branding/alignment and final Session verification remain subsequent scope.

## Preservation

Authenticate execution baseline B from populated `IMPLEMENT_BASE_SHA`, otherwise through the normal baseline and bound-attempt mechanisms. Verify branch, ancestry and checkpoint bindings; fail closed if authentication is unavailable.

Inspect tracked removal candidates through Git blobs at B, then current consumers and canonical destinations. Git preserves tracked history; deletion of obsolete material requires no duplicate, backup or receipt.

Preserve local extracted/reconciled JSON, canonical company inputs and outputs, archived evidence, source manifests and required sidecars. Before removing any non-Git irreplaceable source copy, verify byte continuity and provenance at its intended canonical destination; otherwise block that removal. Do not remove restored source PDFs without verified canonical bytes.

Preserve public `bav` commands, aliases, patchable configuration, explicit JSON/Excel routes and optional Trainer behavior. Retain analytical results, source immutability, residual qualifications, dormant forecasting, zero-byte research placeholders and normalization admission’s existing gates and default-off behavior.

## Verification and recording

- Check retained active and Legacy consumers for broken imports, paths and resource discovery after removal.
- Run affected existing ingestion ownership, filing CLI, build CLI, current-build, build-contract, reference-integrity and optional Trainer regressions. Preserve assertions establishing public interfaces and source provenance.
- Reuse representative Lululemon/Fast Retailing verification only while its dependencies remain applicable; rerun affected build/check/publication paths if removal changes those dependencies.
- Apply SESSION’s Office Bridge requirements if workbook formulas/dependencies or presentation change.
- Run `git diff --check` and inspect the comparison against authenticated B.
- Append actual removals, absence-of-use findings, preservation evidence, measured verification and remaining Session scope to `RESULT.md`. Do not rewrite historical records or certify a prospective next ID.

Preserve ownership/recovery, provider retry, human adoption, interruption, candidate validation, protected-document, unrelated-dirty-work and Review-cache safeguards.

Cursor must not modify TARGET.md, SESSION.md or IMPLEMENTATION.md.
